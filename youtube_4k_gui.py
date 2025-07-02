import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from googleapiclient.discovery import build
import requests
import re
import os
from PIL import Image, ImageTk
import io

class YouTube4KCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 4K Video Checker")
        self.root.geometry("1200x900")
        
        # Dark theme colors
        self.colors = {
            'bg_primary': '#1e1e1e',
            'bg_secondary': '#2d2d2d',
            'bg_tertiary': '#3c3c3c',
            'text_primary': '#ffffff',
            'text_secondary': '#b3b3b3',
            'accent_blue': '#0078d4',
            'accent_green': '#107c10',
            'accent_orange': '#ff8c00',
            'accent_red': '#d13438',
            'accent_purple': '#8b5cf6',
            'border': '#404040'
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure ttk styles for dark theme
        self.setup_dark_theme()
        
        # API Key - Buraya kendi API key'inizi yazın
        self.API_KEY = 'AIzaSyA3hWhKJmy2_0A7cfbB46va3XWsq-SeV2E'
        self.youtube = build('youtube', 'v3', developerKey=self.API_KEY)
        
        # İşlem durumu
        self.is_processing = False
        self.stop_requested = False  # İşlemi durdurma talebi
        self.found_4k_videos = []
        self.thumbnail_cache = {}  # Thumbnail önbelleği
        self.thumbnail_refs = []   # Thumbnail referanslarını korumak için
        
        self.create_widgets()

    def setup_dark_theme(self):
        """Configure dark theme for ttk widgets"""
        style = ttk.Style()
        
        # Configure treeview style
        style.theme_use('clam')
        
        # Configure styles for different widgets
        style.configure('Dark.Treeview',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       fieldbackground=self.colors['bg_secondary'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       rowheight=60)
        
        style.configure('Dark.Treeview.Heading',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'])
        
        style.map('Dark.Treeview',
                 background=[('selected', self.colors['accent_blue'])],
                 foreground=[('selected', self.colors['text_primary'])])
        
        style.configure('Dark.TFrame',
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        style.configure('Dark.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Dark.TEntry',
                       fieldbackground=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       bordercolor=self.colors['border'],
                       insertcolor=self.colors['text_primary'])
        
        style.configure('Dark.TButton',
                       background=self.colors['accent_blue'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Dark.TButton',
                 background=[('active', self.colors['accent_purple']),
                           ('pressed', self.colors['bg_tertiary'])])
        
        style.configure('Success.TButton',
                       background=self.colors['accent_green'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Success.TButton',
                 background=[('active', '#0e6e0e'),
                           ('pressed', self.colors['bg_tertiary'])])
        
        style.configure('Warning.TButton',
                       background=self.colors['accent_orange'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Warning.TButton',
                 background=[('active', '#e07600'),
                           ('pressed', self.colors['bg_tertiary'])])
        
        style.configure('Danger.TButton',
                       background=self.colors['accent_red'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Danger.TButton',
                 background=[('active', '#b42b2f'),
                           ('pressed', self.colors['bg_tertiary'])])
        
        style.configure('Dark.Horizontal.TProgressbar',
                       background=self.colors['accent_blue'],
                       troughcolor=self.colors['bg_tertiary'],
                       borderwidth=0,
                       lightcolor=self.colors['accent_blue'],
                       darkcolor=self.colors['accent_blue'])
    
    def create_widgets(self):
        # Ana frame container
        main_container = ttk.Frame(self.root, style='Dark.TFrame')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Ana başlık
        title_label = tk.Label(main_container, text="🎬 YouTube 4K Video Checker", 
                              font=('Segoe UI', 18, 'bold'), 
                              bg=self.colors['bg_primary'], 
                              fg=self.colors['text_primary'])
        title_label.pack(pady=(0, 20))
        
        # Playlist URL girişi
        url_frame = ttk.Frame(main_container, style='Dark.TFrame')
        url_frame.pack(pady=(0, 15), fill='x')
        
        ttk.Label(url_frame, text="Playlist URL:", font=('Segoe UI', 12, 'bold'), 
                 style='Dark.TLabel').pack(anchor='w', pady=(0, 5))
        
        url_input_frame = ttk.Frame(url_frame, style='Dark.TFrame')
        url_input_frame.pack(fill='x', pady=(0, 10))
        
        self.url_entry = ttk.Entry(url_input_frame, font=('Segoe UI', 11), 
                                  style='Dark.TEntry', width=60)
        self.url_entry.pack(side='left', fill='x', expand=True)
        
        paste_btn = ttk.Button(url_input_frame, text="📋 Paste", 
                              command=self.paste_url, style='Success.TButton')
        paste_btn.pack(side='right', padx=(10, 0))
        
        # Playlist bilgileri
        self.playlist_info_frame = ttk.Frame(url_frame, style='Dark.TFrame')
        self.playlist_info_frame.pack(fill='x', pady=(0, 10))
        
        self.playlist_info_label = tk.Label(self.playlist_info_frame, text="", 
                                          font=('Segoe UI', 10), 
                                          bg=self.colors['bg_primary'], 
                                          fg=self.colors['text_secondary'],
                                          wraplength=800, justify='left')
        self.playlist_info_label.pack(anchor='w')
        
        # URL değişikliklerini dinle
        self.url_entry.bind('<KeyRelease>', self.on_url_change)
        self.url_entry.bind('<FocusOut>', self.on_url_change)
        
        # Video sayısı sınırı
        limit_frame = ttk.Frame(main_container, style='Dark.TFrame')
        limit_frame.pack(pady=(0, 15), fill='x')
        
        ttk.Label(limit_frame, text="Maximum video count:", 
                 font=('Segoe UI', 12, 'bold'), style='Dark.TLabel').pack(anchor='w', pady=(0, 5))
        
        # Slider ve Entry beraber
        slider_frame = ttk.Frame(limit_frame, style='Dark.TFrame')
        slider_frame.pack(fill='x', pady=(0, 10))
        
        # Slider (0-1000 arası)
        self.video_limit_var = tk.IntVar(value=200)
        self.limit_slider = tk.Scale(slider_frame, from_=10, to=1000, 
                                    orient='horizontal', variable=self.video_limit_var,
                                    bg=self.colors['bg_secondary'],
                                    fg=self.colors['text_primary'],
                                    highlightbackground=self.colors['bg_primary'],
                                    troughcolor=self.colors['bg_tertiary'],
                                    activebackground=self.colors['accent_blue'],
                                    font=('Segoe UI', 9),
                                    command=self.on_slider_change)
        self.limit_slider.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Entry kutusu
        entry_frame = ttk.Frame(slider_frame, style='Dark.TFrame')
        entry_frame.pack(side='right')
        
        self.limit_entry = ttk.Entry(entry_frame, font=('Segoe UI', 11), width=8,
                                    textvariable=self.video_limit_var, style='Dark.TEntry')
        self.limit_entry.pack(side='left')
        
        # "All" checkbox
        self.all_videos_var = tk.BooleanVar(value=False)
        self.all_videos_check = tk.Checkbutton(entry_frame, text="All", 
                                              variable=self.all_videos_var,
                                              command=self.on_all_videos_toggle,
                                              bg=self.colors['bg_primary'],
                                              fg=self.colors['text_primary'],
                                              font=('Segoe UI', 10),
                                              activebackground=self.colors['bg_primary'],
                                              activeforeground=self.colors['text_primary'],
                                              selectcolor=self.colors['bg_secondary'])
        self.all_videos_check.pack(side='right', padx=(10, 0))
        
        # Butonlar
        button_frame = ttk.Frame(main_container, style='Dark.TFrame')
        button_frame.pack(pady=(0, 15))
        
        self.get_videos_btn = ttk.Button(button_frame, text="📥 Get Videos", 
                                        command=self.get_videos, style='Dark.TButton')
        self.get_videos_btn.pack(side='left', padx=(0, 10))
        
        self.check_4k_btn = ttk.Button(button_frame, text="🔍 Check 4K", 
                                      command=self.check_4k_videos, style='Warning.TButton',
                                      state='disabled')
        self.check_4k_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="⏹️ Stop", 
                                  command=self.stop_processing, style='Danger.TButton',
                                  state='disabled')
        self.stop_btn.pack(side='left', padx=(0, 10))
        
        # Copy and Clear buttons
        self.copy_btn = ttk.Button(button_frame, text="📋 Copy Checked", 
                                  command=self.copy_checked_urls, style='Success.TButton',
                                  state='disabled')
        self.copy_btn.pack(side='left', padx=(0, 10))
        
        # Check management buttons
        self.check_all_btn = ttk.Button(button_frame, text="☑️ Check All", 
                                       command=self.check_all_videos, style='Dark.TButton',
                                       state='disabled')
        self.check_all_btn.pack(side='left', padx=(0, 10))
        
        self.uncheck_all_btn = ttk.Button(button_frame, text="☐ Uncheck All", 
                                         command=self.uncheck_all_videos, style='Dark.TButton',
                                         state='disabled')
        self.uncheck_all_btn.pack(side='left', padx=(0, 10))
        
        self.check_4k_only_btn = ttk.Button(button_frame, text="✅ Check 4K Only", 
                                           command=self.check_4k_only, style='Success.TButton',
                                           state='disabled')
        self.check_4k_only_btn.pack(side='left', padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="🗑️ Clear", 
                                   command=self.clear_all, style='Dark.TButton')
        self.clear_btn.pack(side='left')
        
        # Progress bar and status
        progress_frame = ttk.Frame(main_container, style='Dark.TFrame')
        progress_frame.pack(fill='x', pady=(0, 15))
        
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate', 
                                       style='Dark.Horizontal.TProgressbar')
        self.progress.pack(fill='x', pady=(0, 5))
        
        # Durum etiketi
        self.status_label = tk.Label(progress_frame, text="Enter playlist URL and click 'Get Videos'", 
                                    font=('Segoe UI', 10), 
                                    bg=self.colors['bg_primary'], 
                                    fg=self.colors['text_secondary'])
        self.status_label.pack()
        
        # Video listesi
        list_frame = ttk.Frame(main_container, style='Dark.TFrame')
        list_frame.pack(fill='both', expand=True)
        
        ttk.Label(list_frame, text="📹 Videos Found:", font=('Segoe UI', 12, 'bold'), 
                 style='Dark.TLabel').pack(anchor='w', pady=(0, 10))
        
        # Treeview ile video listesi
        tree_frame = ttk.Frame(list_frame, style='Dark.TFrame')
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('Check', 'No', 'Thumbnail', 'Title', 'Quality', 'Status')
        self.video_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                      height=15, style='Dark.Treeview')
        
        # Sütun başlıkları
        self.video_tree.heading('Check', text='☑️')
        self.video_tree.heading('No', text='#')
        self.video_tree.heading('Thumbnail', text='🖼️')
        self.video_tree.heading('Title', text='Video Title')
        self.video_tree.heading('Quality', text='Quality')
        self.video_tree.heading('Status', text='4K Status')
        
        # Sütun genişlikleri
        self.video_tree.column('Check', width=40, minwidth=40)
        self.video_tree.column('No', width=50, minwidth=50)
        self.video_tree.column('Thumbnail', width=80, minwidth=80)
        self.video_tree.column('Title', width=400, minwidth=200)
        self.video_tree.column('Quality', width=100, minwidth=100)
        self.video_tree.column('Status', width=120, minwidth=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.video_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Right-click context menu
        self.create_context_menu()
        self.video_tree.bind('<Button-3>', self.show_context_menu)  # Right-click
        self.video_tree.bind('<Button-1>', self.on_tree_click)  # Left-click for checkbox toggle
        
        # Bind events
        self.limit_entry.bind('<KeyRelease>', self.on_entry_change)

    def create_context_menu(self):
        """Create right-click context menu for video list"""
        self.context_menu = tk.Menu(self.root, tearoff=0,
                                   bg=self.colors['bg_secondary'],
                                   fg=self.colors['text_primary'],
                                   activebackground=self.colors['accent_blue'],
                                   activeforeground=self.colors['text_primary'],
                                   borderwidth=0)
        
        self.context_menu.add_command(label="📋 Copy Video URL", command=self.copy_selected_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Remove Video", command=self.remove_selected_video)
        
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Select the item under cursor
        item = self.video_tree.identify('item', event.x, event.y)
        if item:
            self.video_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
        
    def copy_selected_url(self):
        """Copy the URL of the selected video to clipboard"""
        selection = self.video_tree.selection()
        if selection:
            item = selection[0]
            video_id = self.video_tree.item(item)['tags'][0] if self.video_tree.item(item)['tags'] else None
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
                self.root.clipboard_clear()
                self.root.clipboard_append(url)
                self.status_label.config(text=f"Copied video URL to clipboard")
                
    def remove_selected_video(self):
        """Remove the selected video from the list"""
        selection = self.video_tree.selection()
        if selection:
            item = selection[0]
            video_id = self.video_tree.item(item)['tags'][0] if self.video_tree.item(item)['tags'] else None
            
            # Remove from treeview
            self.video_tree.delete(item)
            
            # Remove from found_4k_videos if it exists there
            if video_id:
                self.found_4k_videos = [v for v in self.found_4k_videos if v != f"https://www.youtube.com/watch?v={video_id}"]
                
                # Update copy button state
                if self.found_4k_videos:
                    self.copy_btn.config(state='normal')
                else:
                    self.copy_btn.config(state='disabled')
            
            self.status_label.config(text="Video removed from list")
    
    def on_tree_click(self, event):
        """Handle left-click on treeview to toggle checkboxes"""
        item = self.video_tree.identify('item', event.x, event.y)
        column = self.video_tree.identify('column', event.x, event.y)
        
        # If clicked on the checkbox column
        if item and column == '#1':  # First column (Check)
            self.toggle_checkbox(item)
    
    def toggle_checkbox(self, item):
        """Toggle checkbox state for an item"""
        if not self.video_tree.exists(item):
            return
            
        values = list(self.video_tree.item(item, 'values'))
        current_check = values[0]
        
        # Toggle between checked and unchecked
        if current_check == '☑️':
            values[0] = '☐'
        else:
            values[0] = '☑️'
        
        self.video_tree.item(item, values=values)
        self.update_copy_button_state()
    
    def update_copy_button_state(self):
        """Update copy button state based on checked items"""
        has_checked = any(self.video_tree.item(item, 'values')[0] == '☑️' 
                         for item in self.video_tree.get_children())
        
        if has_checked:
            self.copy_btn.config(state='normal')
        else:
            self.copy_btn.config(state='disabled')
    
    def check_all_videos(self):
        """Check all videos in the list"""
        for item in self.video_tree.get_children():
            values = list(self.video_tree.item(item, 'values'))
            values[0] = '☑️'
            self.video_tree.item(item, values=values)
        self.update_copy_button_state()
    
    def uncheck_all_videos(self):
        """Uncheck all videos in the list"""
        for item in self.video_tree.get_children():
            values = list(self.video_tree.item(item, 'values'))
            values[0] = '☐'
            self.video_tree.item(item, values=values)
        self.update_copy_button_state()
    
    def check_4k_only(self):
        """Check only videos that have 4K available"""
        for item in self.video_tree.get_children():
            values = list(self.video_tree.item(item, 'values'))
            status = values[5]  # Status column
            if '✅ 4K Available!' in status:
                values[0] = '☑️'
            else:
                values[0] = '☐'
            self.video_tree.item(item, values=values)
        self.update_copy_button_state()
    
    def copy_checked_urls(self):
        """Copy URLs of checked videos to clipboard"""
        checked_urls = []
        
        for item in self.video_tree.get_children():
            values = self.video_tree.item(item, 'values')
            is_checked = values[0] == '☑️'
            
            if is_checked:
                # Get video ID from tags
                video_id = self.video_tree.item(item)['tags'][0] if self.video_tree.item(item)['tags'] else None
                if video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    checked_urls.append(url)
        
        if not checked_urls:
            messagebox.showwarning("Warning", "No videos are checked!")
            return
        
        # Join URLs with newlines
        urls_text = '\n'.join(checked_urls)
        
        try:
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(urls_text)
            self.root.update()
            
            messagebox.showinfo("Success", f"✅ {len(checked_urls)} video URLs copied to clipboard!\n\nYou can now paste them anywhere.")
        except Exception as e:
            messagebox.showerror("Error", f"URLs could not be copied: {str(e)}")
    
    def on_entry_change(self, event=None):
        """Entry değeri değiştiğinde slider'ı güncelle"""
        try:
            value = int(self.limit_entry.get())
            if 10 <= value <= 1000:
                self.limit_slider.set(value)
        except ValueError:
            pass
    
    def on_slider_change(self, value):
        """Slider değeri değiştiğinde entry'yi güncelle"""
        if not self.all_videos_var.get():
            # Entry'yi slider değeri ile güncelle (sadece hepsi seçili değilse)
            pass  # textvariable otomatik güncelliyor
    
    def on_all_videos_toggle(self):
        """All checkbox'ı değiştiğinde"""
        if self.all_videos_var.get():
            # All seçiliyse slider ve entry'yi devre dışı bırak
            self.limit_slider.config(state='disabled')
            self.limit_entry.config(state='disabled')
        else:
            # All seçili değilse slider ve entry'yi etkinleştir
            self.limit_slider.config(state='normal')
            self.limit_entry.config(state='normal')
    
    def stop_processing(self):
        """İşlemi durdurmak için flag'i ayarla"""
        self.stop_requested = True
        self.status_label.config(text="⏹️ Process stopping...")
        # Check 4K Only butonunu aktif et (eğer 4K video bulunduysa)
        if self.found_4k_videos:
            self.check_4k_only_btn.config(state='normal')
    
    def get_playlist_info(self, playlist_id):
        """Playlist bilgilerini al"""
        try:
            # Playlist detaylarını al
            playlist_request = self.youtube.playlists().list(
                part='snippet,contentDetails',
                id=playlist_id
            )
            playlist_response = playlist_request.execute()
            
            if playlist_response['items']:
                playlist = playlist_response['items'][0]
                title = playlist['snippet']['title']
                video_count = playlist['contentDetails']['itemCount']
                channel_title = playlist['snippet']['channelTitle']
                
                return {
                    'title': title,
                    'video_count': video_count,
                    'channel': channel_title
                }
        except:
            pass
        
        return None
    
    def on_url_change(self, event=None):
        """URL değiştiğinde playlist bilgilerini güncelle"""
        url = self.url_entry.get().strip()
        
        if not url:
            self.playlist_info_label.config(text="")
            return
        
        # Playlist ID'yi çıkarmaya çalış
        try:
            playlist_id = self.extract_playlist_id(url)
            if len(playlist_id) > 10:  # Geçerli bir ID gibi görünüyor
                # Thread'de playlist bilgilerini al
                thread = threading.Thread(target=self._update_playlist_info_thread, args=(playlist_id,))
                thread.daemon = True
                thread.start()
            else:
                self.playlist_info_label.config(text="")
        except:
            self.playlist_info_label.config(text="")
    
    def _update_playlist_info_thread(self, playlist_id):
        """Playlist bilgilerini thread'de al ve güncelle"""
        try:
            playlist_info = self.get_playlist_info(playlist_id)
            if playlist_info:
                info_text = f"📂 {playlist_info['title']}\n👤 {playlist_info['channel']} • 🎬 {playlist_info['video_count']} video"
                self.root.after(0, lambda: self.playlist_info_label.config(text=info_text, fg=self.colors['accent_green']))
            else:
                self.root.after(0, lambda: self.playlist_info_label.config(text="❌ Playlist not found or accessible", fg=self.colors['accent_red']))
        except:
            self.root.after(0, lambda: self.playlist_info_label.config(text="❌ Failed to get playlist info", fg=self.colors['accent_red']))
    
    def paste_url(self):
        """Panodaki URL'yi yapıştır"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_content)
            # URL yapıştırıldığında playlist bilgilerini güncelle
            self.on_url_change()
        except:
            messagebox.showwarning("Warning", "No text found in clipboard!")
    
    def load_thumbnail(self, video_id, thumbnail_url):
        """Video thumbnail'ini yükle ve önbelleğe al"""
        try:
            if video_id in self.thumbnail_cache:
                return self.thumbnail_cache[video_id]
            
            response = requests.get(thumbnail_url, timeout=5)
            if response.status_code == 200:
                # PIL ile resmi yükle ve yeniden boyutlandır
                image = Image.open(io.BytesIO(response.content))
                image = image.resize((60, 40), Image.Resampling.LANCZOS)
                
                # Tkinter uyumlu hale getir
                photo = ImageTk.PhotoImage(image)
                
                # Önbelleğe al - referansı korumak için
                self.thumbnail_cache[video_id] = photo
                self.thumbnail_refs.append(photo)  # Referansı koru
                return photo
        except Exception as e:
            print(f"Thumbnail could not be loaded ({video_id}): {e}")
        
        return None
    
    def extract_playlist_id(self, playlist_url):
        """Playlist URL'sinden ID'yi çıkar"""
        if 'list=' in playlist_url:
            return playlist_url.split('list=')[1].split('&')[0]
        else:
            return playlist_url
    
    def get_videos(self):
        """Playlist'ten videoları getir"""
        if self.is_processing:
            return
            
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter playlist URL!")
            return
        
        # Video sayısı sınırını al
        if self.all_videos_var.get():
            max_videos = None  # All
        else:
            max_videos = self.video_limit_var.get()
        
        # Thread'de çalıştır
        thread = threading.Thread(target=self._get_videos_thread, args=(url, max_videos))
        thread.daemon = True
        thread.start()
    
    def _get_videos_thread(self, url, max_videos):
        """Video getirme işlemini thread'de yap"""
        self.is_processing = True
        self.progress.start()
        self.get_videos_btn.config(state='disabled')
        self.check_4k_btn.config(state='disabled')
        
        try:
            self.status_label.config(text="Analyzing playlist...")
            
            # Playlist ID'yi çıkar
            playlist_id = self.extract_playlist_id(url)
            
            # Video ID'lerini al
            video_ids = self.get_video_ids_from_playlist(playlist_id, max_videos)
            
            self.status_label.config(text=f"{len(video_ids)} videos found, getting details...")
            
            # Video detaylarını al
            self.video_details = self.get_video_details(video_ids)
            
            # GUI'yi güncelle
            self.root.after(0, self._update_video_list)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error getting videos: {str(e)}"))
        finally:
            self.is_processing = False
            self.progress.stop()
            self.get_videos_btn.config(state='normal')
            if hasattr(self, 'video_details') and self.video_details:
                self.check_4k_btn.config(state='normal')
    
    def _update_video_list(self):
        """Video listesini güncelle"""
        # Listeyi temizle
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        
        # Videoları ekle
        for i, video in enumerate(self.video_details, 1):
            quality = "HD" if video['definition'] == 'hd' else "SD"
            
            # Item'ı ekle video_id'yi tag olarak ekle, checkbox unchecked olarak başla
            item_id = self.video_tree.insert('', 'end', values=(
                '☐',  # Checkbox - unchecked by default
                i, 
                "🖼️",  # Placeholder thumbnail için
                video['title'][:50] + "..." if len(video['title']) > 50 else video['title'],
                quality,
                "Waiting..."
            ), tags=(video['id'],))
            
            # Thumbnail'i thread'de yükle
            thread = threading.Thread(target=self._load_thumbnail_async, args=(item_id, video['id'], video['thumbnail_url']))
            thread.daemon = True
            thread.start()
        
        # Check management buttons'ı aktif et
        self.check_all_btn.config(state='normal')
        self.uncheck_all_btn.config(state='normal')
        
        self.status_label.config(text=f"{len(self.video_details)} videos listed. Press button to check 4K.")
    
    def _load_thumbnail_async(self, item_id, video_id, thumbnail_url):
        """Thumbnail'i asenkron olarak yükle"""
        try:
            thumbnail = self.load_thumbnail(video_id, thumbnail_url)
            if thumbnail:
                # Ana thread'de GUI'yi güncelle
                self.root.after(0, lambda: self._update_thumbnail(item_id, thumbnail))
            else:
                # Hata durumunda ❌ işareti göster
                self.root.after(0, lambda: self._update_thumbnail_text(item_id, "❌"))
        except:
            self.root.after(0, lambda: self._update_thumbnail_text(item_id, "❌"))
    
    def _update_thumbnail(self, item_id, photo):
        """Thumbnail'i TreeView'da güncelle"""
        try:
            # TreeView item'ını güncelle
            if self.video_tree.exists(item_id):
                # Thumbnail'i image olarak ayarla
                self.video_tree.item(item_id, image=photo)
                # Thumbnail sütununu boş bırak (görsel image ile gösterilir)
                values = list(self.video_tree.item(item_id, 'values'))
                values[2] = ""  # Thumbnail sütunu (index 2 now)
                self.video_tree.item(item_id, values=values)
        except Exception as e:
            print(f"Thumbnail could not be updated: {e}")
    
    def _update_thumbnail_text(self, item_id, text):
        """Thumbnail yerine metin göster"""
        try:
            if self.video_tree.exists(item_id):
                values = list(self.video_tree.item(item_id, 'values'))
                values[2] = text  # Thumbnail sütunu (index 2 now)
                self.video_tree.item(item_id, values=values)
        except Exception as e:
            print(f"Thumbnail text could not be updated: {e}")
    
    def get_video_ids_from_playlist(self, playlist_id, max_videos=None):
        """Playlist'ten video ID'lerini al"""
        video_ids = []
        next_page_token = None
        
        while True:
            pl_request = self.youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            pl_response = pl_request.execute()
            
            for item in pl_response['items']:
                video_ids.append(item['contentDetails']['videoId'])
                if max_videos and len(video_ids) >= max_videos:
                    return video_ids[:max_videos]
            
            next_page_token = pl_response.get('nextPageToken')
            if not next_page_token:
                break
        
        return video_ids
    
    def get_video_details(self, video_ids):
        """Video detaylarını al"""
        video_details = []
        
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(batch_ids)
            )
            response = request.execute()
            
            for item in response['items']:
                video_info = {
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'url': f"https://www.youtube.com/watch?v={item['id']}",
                    'definition': item['contentDetails']['definition'],
                    'dimension': item['contentDetails']['dimension'],
                    'thumbnail_url': item['snippet']['thumbnails']['medium']['url']  # Thumbnail URL ekle
                }
                video_details.append(video_info)
        
        return video_details
    
    def check_4k_videos(self):
        """4K videoları kontrol et"""
        if self.is_processing or not hasattr(self, 'video_details'):
            return
        
        thread = threading.Thread(target=self._check_4k_thread)
        thread.daemon = True
        thread.start()
    
    def _check_4k_thread(self):
        """4K kontrol işlemini thread'de yap"""
        self.is_processing = True
        self.stop_requested = False
        self.progress.start()
        self.check_4k_btn.config(state='disabled')
        self.stop_btn.config(state='normal')  # Stop butonunu aktif et
        self.copy_btn.config(state='disabled')  # Copy butonunu deaktif et
        self.found_4k_videos = []
        
        try:
            hd_videos = [v for v in self.video_details if v['definition'] == 'hd']
            
            for i, video in enumerate(hd_videos):
                # Durduruluyor mu kontrol et
                if self.stop_requested:
                    self.root.after(0, lambda: self.status_label.config(text="❌ Process stopped by user."))
                    break
                
                # GUI'yi güncelle
                self.root.after(0, lambda v=video, idx=i: self._update_video_status(v, f"Checking... ({idx+1}/{len(hd_videos)})"))
                
                # 4K kontrolü yap
                is_4k = self.check_4k_availability(video['url'])
                
                # Tekrar durduruluyor mu kontrol et (HTTP isteği sonrası)
                if self.stop_requested:
                    self.root.after(0, lambda: self.status_label.config(text="❌ Process stopped by user."))
                    break
                
                if is_4k:
                    self.found_4k_videos.append(video['url'])
                    self.root.after(0, lambda v=video: self._update_video_status(v, "✅ 4K Available!"))
                else:
                    self.root.after(0, lambda v=video: self._update_video_status(v, "❌ No 4K"))
            
            # SD videoları için durum güncelle
            if not self.stop_requested:
                sd_videos = [v for v in self.video_details if v['definition'] == 'sd']
                for video in sd_videos:
                    self.root.after(0, lambda v=video: self._update_video_status(v, "📱 SD Quality"))
                
                # Sonuçları göster
                self.root.after(0, self._show_results)
            else:
                # Durduruldu ama kısmi sonuçlar var
                if self.found_4k_videos:
                    self.root.after(0, lambda: self.check_4k_only_btn.config(state='normal'))
                    self.root.after(0, lambda: self.status_label.config(text=f"❌ Stopped. {len(self.found_4k_videos)} 4K videos found so far."))
                else:
                    self.root.after(0, lambda: self.status_label.config(text="❌ Process stopped by user."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"4K check error: {str(e)}"))
        finally:
            self.is_processing = False
            self.stop_requested = False
            self.progress.stop()
            self.check_4k_btn.config(state='normal')
            self.stop_btn.config(state='disabled')  # Stop butonunu deaktif et
    
    def _update_video_status(self, video, status):
        """Video durumunu güncelle"""
        for item in self.video_tree.get_children():
            values = self.video_tree.item(item, 'values')
            if video['title'][:50] in values[3]:  # Title sütunu (index 3 now)
                new_values = list(values)
                new_values[5] = status  # Status sütunu (index 5 now)
                self.video_tree.item(item, values=new_values)
                break
    
    def _show_results(self):
        """Sonuçları göster"""
        total_videos = len(self.video_details)
        found_count = len(self.found_4k_videos)
        
        self.status_label.config(text=f"✅ Scan completed! {total_videos} videos scanned, {found_count} 4K videos found.")
        
        # Check 4K Only butonunu aktif et
        self.check_4k_only_btn.config(state='normal')
        
        if self.found_4k_videos:
            messagebox.showinfo("Result", f"🎉 {found_count} 4K videos found!\n\nUse checkboxes to select videos and copy URLs.")
        else:
            messagebox.showinfo("Result", "😔 No 4K videos found.\n\nThis playlist doesn't have 4K quality videos.")
    
    def check_4k_availability(self, video_url):
        """4K kalite kontrolü"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(video_url, headers=headers, timeout=10)
            
            if '2160p' in response.text or '"quality":"hd2160"' in response.text:
                return True
            
            if '"qualityLabel":"2160p"' in response.text:
                return True
                
        except:
            pass
        
        return False
    
    def clear_all(self):
        """Tüm verileri temizle"""
        self.url_entry.delete(0, tk.END)
        self.playlist_info_label.config(text="")  # Playlist bilgilerini temizle
        
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        
        self.status_label.config(text="Enter playlist URL and click 'Get Videos'")
        self.check_4k_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
        self.copy_btn.config(state='disabled')
        self.check_all_btn.config(state='disabled')
        self.uncheck_all_btn.config(state='disabled')
        self.check_4k_only_btn.config(state='disabled')
        self.found_4k_videos = []
        self.stop_requested = False
        self.thumbnail_cache.clear()  # Thumbnail önbelleğini temizle
        self.thumbnail_refs.clear()   # Thumbnail referanslarını temizle
        
        if hasattr(self, 'video_details'):
            delattr(self, 'video_details')

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTube4KCheckerGUI(root)
    root.mainloop()
