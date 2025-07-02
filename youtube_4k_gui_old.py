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
                       bordercolor=self.colors['border'])
        
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
        
        style.configure('Dark.TScale',
                       background=self.colors['bg_primary'],
                       troughcolor=self.colors['bg_tertiary'],
                       borderwidth=0,
                       sliderthickness=20,
                       sliderrelief='flat',
                       slidercolor=self.colors['accent_blue'])
        
        style.configure('Dark.TCheckbutton',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       focuscolor='none')
        
        style.map('Dark.TCheckbutton',
                 background=[('active', self.colors['bg_primary'])])
    
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
        self.limit_slider = ttk.Scale(slider_frame, from_=10, to=1000, 
                                     orient='horizontal', variable=self.video_limit_var,
                                     style='Dark.TScale',
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
        self.all_videos_check = ttk.Checkbutton(entry_frame, text="All", 
                                               variable=self.all_videos_var,
                                               command=self.on_all_videos_toggle,
                                               style='Dark.TCheckbutton')
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
        self.copy_btn = ttk.Button(button_frame, text="📋 Copy 4K URLs", 
                                  command=self.copy_4k_urls, style='Success.TButton',
                                  state='disabled')
        self.copy_btn.pack(side='left', padx=(0, 10))
        
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
        
        columns = ('No', 'Thumbnail', 'Title', 'Quality', 'Status')
        self.video_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                      height=15, style='Dark.Treeview')
        
        # Sütun başlıkları
        self.video_tree.heading('No', text='#')
        self.video_tree.heading('Thumbnail', text='🖼️')
        self.video_tree.heading('Title', text='Video Title')
        self.video_tree.heading('Quality', text='Quality')
        self.video_tree.heading('Status', text='4K Status')
        
        # Sütun genişlikleri
        self.video_tree.column('No', width=50, minwidth=50)
        self.video_tree.column('Thumbnail', width=80, minwidth=80)
        self.video_tree.column('Title', width=450, minwidth=200)
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
        
        # Bind events
        self.limit_entry.bind('<KeyRelease>', self.on_entry_change)
        
        # Satır yüksekliği
        style = ttk.Style()
        style.configure("Treeview", rowheight=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        
        self.video_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Alt butonlar
        bottom_frame = tk.Frame(self.root, bg='#f0f0f0')
        bottom_frame.pack(pady=10, fill='x')
        
        self.copy_btn = tk.Button(bottom_frame, text="� 4K URL'leri Kopyala", 
                                 command=self.copy_4k_urls, bg='#9C27B0', 
                                 fg='white', font=('Arial', 11, 'bold'),
                                 state='disabled')
        self.copy_btn.pack(side='left', padx=20)
        
        self.clear_btn = tk.Button(bottom_frame, text="🗑️ Temizle", 
                                  command=self.clear_all, bg='#607D8B', 
                                  fg='white', font=('Arial', 11))
        self.clear_btn.pack(side='right', padx=20)
    
    def on_slider_change(self, value):
        """Slider değeri değiştiğinde entry'yi güncelle"""
        if not self.all_videos_var.get():
            # Entry'yi slider değeri ile güncelle (sadece hepsi seçili değilse)
            pass  # textvariable otomatik güncelliyor
    
    def on_all_videos_toggle(self):
        """Hepsi checkbox'ı değiştiğinde"""
        if self.all_videos_var.get():
            # Hepsi seçiliyse slider ve entry'yi devre dışı bırak
            self.limit_slider.config(state='disabled')
            self.limit_entry.config(state='disabled')
        else:
            # Hepsi seçili değilse slider ve entry'yi etkinleştir
            self.limit_slider.config(state='normal')
            self.limit_entry.config(state='normal')
    
    def stop_processing(self):
        """İşlemi durdurmak için flag'i ayarla"""
        self.stop_requested = True
        self.status_label.config(text="⏹️ İşlem durduruluyor...")
    
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
                self.root.after(0, lambda: self.playlist_info_label.config(text=info_text, fg='#2E7D32'))
            else:
                self.root.after(0, lambda: self.playlist_info_label.config(text="❌ Playlist bulunamadı veya erişilemiyor", fg='#D32F2F'))
        except:
            self.root.after(0, lambda: self.playlist_info_label.config(text="❌ Playlist bilgileri alınamadı", fg='#D32F2F'))
    
    def paste_url(self):
        """Panodaki URL'yi yapıştır"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_content)
            # URL yapıştırıldığında playlist bilgilerini güncelle
            self.on_url_change()
        except:
            messagebox.showwarning("Uyarı", "Panoda metin bulunamadı!")
    
    def load_thumbnail(self, video_id, thumbnail_url):
        """Video thumbnail'ini yükle ve önbelleğe al"""
        try:
            if video_id in self.thumbnail_cache:
                return self.thumbnail_cache[video_id]
            
            response = requests.get(thumbnail_url, timeout=5)
            if response.status_code == 200:
                # PIL ile resmi yükle ve yeniden boyutlandır
                image = Image.open(io.BytesIO(response.content))
                image = image.resize((100, 60), Image.Resampling.LANCZOS)
                
                # Tkinter uyumlu hale getir
                photo = ImageTk.PhotoImage(image)
                
                # Önbelleğe al - referansı korumak için
                self.thumbnail_cache[video_id] = photo
                self.thumbnail_refs.append(photo)  # Referansı koru
                return photo
        except Exception as e:
            print(f"Thumbnail yüklenemedi ({video_id}): {e}")
            # Hata durumunda kırmızı X işareti oluştur
            error_image = Image.new('RGB', (100, 60), color='#ffcccc')
            try:
                # Basit bir X işareti çiz (PIL'in drawing özelliği olmadan)
                photo = ImageTk.PhotoImage(error_image)
                self.thumbnail_cache[video_id] = photo
                return photo
            except:
                pass
        
        return None
    
    def create_error_thumbnail(self):
        """Hata durumu için basit bir thumbnail oluştur"""
        try:
            # Açık kırmızı arka plan
            image = Image.new('RGB', (100, 60), color='#ffcccc')
            photo = ImageTk.PhotoImage(image)
            return photo
        except:
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
            messagebox.showerror("Hata", "Lütfen playlist URL'si girin!")
            return
        
        # Video sayısı sınırını al
        if self.all_videos_var.get():
            max_videos = None  # Hepsi
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
            self.status_label.config(text="Playlist analiz ediliyor...")
            
            # Playlist ID'yi çıkar
            playlist_id = self.extract_playlist_id(url)
            
            # Video ID'lerini al
            video_ids = self.get_video_ids_from_playlist(playlist_id, max_videos)
            
            self.status_label.config(text=f"{len(video_ids)} video bulundu, detaylar alınıyor...")
            
            # Video detaylarını al
            self.video_details = self.get_video_details(video_ids)
            
            # GUI'yi güncelle
            self.root.after(0, self._update_video_list)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"Video alınırken hata: {str(e)}"))
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
            
            # Önce item'ı ekle
            item_id = self.video_tree.insert('', 'end', values=(
                "📷",  # Placeholder thumbnail için
                i, 
                video['title'][:40] + "..." if len(video['title']) > 40 else video['title'],
                quality,
                "Bekliyor..."
            ))
            
            # Thumbnail'i thread'de yükle
            thread = threading.Thread(target=self._load_thumbnail_async, args=(item_id, video['id'], video['thumbnail_url']))
            thread.daemon = True
            thread.start()
        
        self.status_label.config(text=f"{len(self.video_details)} video listelendi. 4K kontrol için butona basın.")
    
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
                self.video_tree.item(item_id, image=photo)
                # Thumbnail sütununu güncelle
                values = list(self.video_tree.item(item_id, 'values'))
                values[0] = ""  # Thumbnail sütunu
                self.video_tree.item(item_id, values=values)
        except Exception as e:
            print(f"Thumbnail güncellenemedi: {e}")
    
    def _update_thumbnail_text(self, item_id, text):
        """Thumbnail yerine metin göster"""
        try:
            if self.video_tree.exists(item_id):
                values = list(self.video_tree.item(item_id, 'values'))
                values[0] = text
                self.video_tree.item(item_id, values=values)
        except Exception as e:
            print(f"Thumbnail metni güncellenemedi: {e}")
    
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
        self.stop_btn.config(state='normal')  # Durdur butonunu aktif et
        self.found_4k_videos = []
        
        try:
            hd_videos = [v for v in self.video_details if v['definition'] == 'hd']
            
            for i, video in enumerate(hd_videos):
                # Durduruluyor mu kontrol et
                if self.stop_requested:
                    self.root.after(0, lambda: self.status_label.config(text="❌ İşlem kullanıcı tarafından durduruldu."))
                    break
                
                # GUI'yi güncelle
                self.root.after(0, lambda v=video, idx=i: self._update_video_status(v, f"Kontrol ediliyor... ({idx+1}/{len(hd_videos)})"))
                
                # 4K kontrolü yap
                is_4k = self.check_4k_availability(video['url'])
                
                # Tekrar durduruluyor mu kontrol et (HTTP isteği sonrası)
                if self.stop_requested:
                    self.root.after(0, lambda: self.status_label.config(text="❌ İşlem kullanıcı tarafından durduruldu."))
                    break
                
                if is_4k:
                    self.found_4k_videos.append(video)
                    self.root.after(0, lambda v=video: self._update_video_status(v, "✅ 4K Mevcut!"))
                else:
                    self.root.after(0, lambda v=video: self._update_video_status(v, "❌ 4K Yok"))
            
            # İşlem durdurulmadıysa SD videoları için durum güncelle
            if not self.stop_requested:
                sd_videos = [v for v in self.video_details if v['definition'] == 'sd']
                for video in sd_videos:
                    self.root.after(0, lambda v=video: self._update_video_status(v, "📱 SD Kalite"))
                
                # Sonuçları göster
                self.root.after(0, self._show_results)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"4K kontrol hatası: {str(e)}"))
        finally:
            self.is_processing = False
            self.stop_requested = False
            self.progress.stop()
            self.check_4k_btn.config(state='normal')
            self.stop_btn.config(state='disabled')  # Durdur butonunu deaktif et
    
    def _update_video_status(self, video, status):
        """Video durumunu güncelle"""
        for item in self.video_tree.get_children():
            values = self.video_tree.item(item, 'values')
            if video['title'][:40] in values[2]:  # Başlık sütunu artık index 2
                self.video_tree.item(item, values=(values[0], values[1], values[2], values[3], status))
                break
    
    def _show_results(self):
        """Sonuçları göster"""
        total_videos = len(self.video_details)
        found_count = len(self.found_4k_videos)
        
        self.status_label.config(text=f"✅ Tarama tamamlandı! {total_videos} video tarandı, {found_count} adet 4K video bulundu.")
        
        if self.found_4k_videos:
            self.copy_btn.config(state='normal')
            messagebox.showinfo("Sonuç", f"🎉 {found_count} adet 4K video bulundu!\n\nURL'leri kopyalamak için 'Kopyala' butonunu kullanın.")
        else:
            messagebox.showinfo("Sonuç", "😔 4K video bulunamadı.\n\nBu playlist'te 4K kalitede video bulunmuyor.")
    
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
    
    def copy_4k_urls(self):
        """4K video URL'lerini panoya kopyala"""
        if not self.found_4k_videos:
            messagebox.showwarning("Uyarı", "Kopyalanacak 4K video bulunamadı!")
            return
        
        # URL'leri birleştir
        urls = '\n'.join([video['url'] for video in self.found_4k_videos])
        
        try:
            # Panoya kopyala
            self.root.clipboard_clear()
            self.root.clipboard_append(urls)
            self.root.update()  # Clipboard'u güncelle
            
            messagebox.showinfo("Başarılı", f"✅ {len(self.found_4k_videos)} adet 4K video URL'si panoya kopyalandı!\n\nArtık istediğiniz yere yapıştırabilirsiniz.")
        except Exception as e:
            messagebox.showerror("Hata", f"URL'ler kopyalanamadı: {str(e)}")
    
    def clear_all(self):
        """Tüm verileri temizle"""
        self.url_entry.delete(0, tk.END)
        self.playlist_info_label.config(text="")  # Playlist bilgilerini temizle
        
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        
        self.status_label.config(text="Playlist URL'si girin ve 'Videoları Getir' butonuna basın")
        self.check_4k_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
        self.copy_btn.config(state='disabled')
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
