import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.auth.exceptions
import requests
import re
import os
import json
import pickle
from PIL import Image, ImageTk
import io
import webbrowser
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# SSL uyarılarını devre dışı bırak
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class YouTube4KCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 4K Video Checker")
        self.root.geometry("1200x900")
        
        # Modern professional dark theme with sophisticated colors
        self.colors = {
            'bg_primary': '#1a1a1a',      # Rich dark gray
            'bg_secondary': '#242424',    # Medium dark gray  
            'bg_tertiary': '#2d2d2d',     # Lighter dark gray
            'bg_hover': '#383838',        # Hover state
            'text_primary': '#f5f5f5',    # Soft white
            'text_secondary': '#b8b8b8',  # Muted gray
            'text_accent': '#6366f1',     # Professional indigo
            'accent_blue': '#3b82f6',     # Clean blue
            'accent_green': '#10b981',    # Professional emerald
            'accent_orange': '#f59e0b',   # Warm amber
            'accent_red': '#ef4444',      # Clean red
            'accent_purple': '#8b5cf6',   # Sophisticated violet
            'accent_pink': '#ec4899',     # Refined pink
            'accent_yellow': '#eab308',   # Professional yellow
            'accent_cyan': '#06b6d4',     # Modern cyan
            'border': '#404040',          # Subtle border
            'gradient_start': '#4f46e5',  # Indigo gradient
            'gradient_end': '#7c3aed'     # Purple gradient
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure ttk styles for dark theme
        self.setup_dark_theme()
        
        # API Key - Buraya kendi API key'inizi yazın
        self.API_KEY = 'AIzaSyA3hWhKJmy2_0A7cfbB46va3XWsq-SeV2E'
        self.api_key = self.API_KEY  # Eski uyumluluk için
        self.setup_youtube_api()
        
        # OAuth2 için değişkenler
        self.authenticated_youtube = None
        self.credentials = None
        self.flow = None
        self.is_authenticated = False
        self.oauth_scopes = ['https://www.googleapis.com/auth/youtube']
        self.oauth_redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'  # Out-of-band mode
        
        # OAuth2 credentials dosyası
        self.client_secrets_file = os.path.join(os.path.dirname(__file__), 'client_secret.json')
        self.token_file = os.path.join(os.path.dirname(__file__), 'token.pickle')
        
        # OAuth2 durumunu kontrol et
        self.check_existing_authentication()
        
        # İşlem durumu
        self.is_processing = False
        self.stop_requested = False  # İşlemi durdurma talebi
        self.found_4k_videos = []
        self.thumbnail_cache = {}  # Thumbnail önbelleği
        self.thumbnail_refs = []   # Thumbnail referanslarını korumak için
        
        self.create_widgets()
    
    def setup_youtube_api(self):
        """YouTube API'yi başlat"""
        try:
            if not hasattr(self, 'youtube') or self.youtube is None:
                self.youtube = build('youtube', 'v3', developerKey=self.API_KEY)
                print("YouTube API initialized successfully")
        except Exception as e:
            print(f"YouTube API setup error: {e}")
            # API başarısız olursa None olarak bırak, video getirirken tekrar deneriz
            self.youtube = None

    def check_existing_authentication(self):
        """Mevcut authentication durumunu kontrol et"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
                
                if self.credentials and self.credentials.valid:
                    self.authenticated_youtube = build('youtube', 'v3', credentials=self.credentials)
                    self.is_authenticated = True
                elif self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    try:
                        self.credentials.refresh(Request())
                        self.authenticated_youtube = build('youtube', 'v3', credentials=self.credentials)
                        self.is_authenticated = True
                        # Güncellenmiş token'ı kaydet
                        with open(self.token_file, 'wb') as token:
                            pickle.dump(self.credentials, token)
                    except:
                        self.is_authenticated = False
                else:
                    self.is_authenticated = False
        except:
            self.is_authenticated = False

    def start_oauth_flow(self):
        """OAuth2 flow'unu başlat"""
        try:
            if not os.path.exists(self.client_secrets_file):
                messagebox.showerror("Error", f"OAuth2 credentials file not found: {self.client_secrets_file}")
                return
            
            self.flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=self.oauth_scopes,
                redirect_uri=self.oauth_redirect_uri
            )
            
            auth_url, _ = self.flow.authorization_url(prompt='consent')
            
            # Browser'da URL'yi aç
            webbrowser.open(auth_url)
            
            # Kullanıcıdan authorization code iste
            self.show_oauth_dialog(auth_url)
            
        except Exception as e:
            messagebox.showerror("Error", f"OAuth flow could not be started: {str(e)}")

    def show_oauth_dialog(self, auth_url):
        """OAuth2 authorization dialog göster"""
        dialog = tk.Toplevel(self.root)
        dialog.title("YouTube Authentication")
        dialog.geometry("700x500")
        dialog.configure(bg=self.colors['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Dialog içeriği
        tk.Label(dialog, text="🔐 YouTube Authentication Required", 
                font=('Segoe UI', 16, 'bold'),
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_primary']).pack(pady=20)
        
        tk.Label(dialog, text="To remove videos from your YouTube playlist, you need to authenticate:",
                font=('Segoe UI', 11),
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_secondary']).pack(pady=10)
        
        # Instructions
        instructions_frame = ttk.Frame(dialog, style='Dark.TFrame')
        instructions_frame.pack(pady=10, padx=20, fill='x')
        
        instructions_text = """📋 Instructions:
1. Click the 'Open Browser' button below
2. Sign in with your Google account
3. Click 'Allow' to grant permissions
4. You'll see a page with an authorization code
5. Copy that code and paste it in the field below"""
        
        tk.Label(instructions_frame, text=instructions_text,
                font=('Segoe UI', 10),
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_secondary'],
                justify='left').pack(anchor='w')
        
        # Browser button
        ttk.Button(dialog, text="🌐 Open Browser for Authentication", 
                  command=lambda: webbrowser.open(auth_url),
                  style='Success.TButton').pack(pady=15)
        
        # URL display (for copy-paste if browser doesn't open)
        url_frame = ttk.Frame(dialog, style='Dark.TFrame')
        url_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(url_frame, text="If browser doesn't open, copy this URL:",
                font=('Segoe UI', 9),
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_secondary']).pack(anchor='w')
        
        url_entry = tk.Text(url_frame, height=3, wrap='word',
                           bg=self.colors['bg_secondary'],
                           fg=self.colors['text_primary'],
                           font=('Segoe UI', 9))
        url_entry.insert('1.0', auth_url)
        url_entry.config(state='disabled')
        url_entry.pack(fill='x', pady=5)
        
        tk.Label(dialog, text="After authentication, paste the authorization code below:",
                font=('Segoe UI', 11, 'bold'),
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_primary']).pack(pady=(20, 5))
        
        # Authorization code entry
        code_entry = ttk.Entry(dialog, font=('Segoe UI', 11), width=60, style='Dark.TEntry')
        code_entry.pack(pady=5)
        
        # Buttons frame
        btn_frame = ttk.Frame(dialog, style='Dark.TFrame')
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="✅ Complete Authentication", 
                  command=lambda: self.complete_oauth(code_entry.get(), dialog),
                  style='Success.TButton').pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="❌ Cancel", 
                  command=dialog.destroy,
                  style='Danger.TButton').pack(side='left', padx=5)

    def complete_oauth(self, authorization_code, dialog):
        """OAuth2 authentication'ı tamamla"""
        try:
            if not authorization_code.strip():
                messagebox.showerror("Error", "Please enter the authorization code!")
                return
            
            # Remove any extra whitespace and potential URL fragments
            clean_code = authorization_code.strip()
            
            # If user pasted the full URL instead of just the code, extract the code
            if 'code=' in clean_code:
                try:
                    clean_code = clean_code.split('code=')[1].split('&')[0]
                except:
                    pass
            
            # Token'ı al
            self.flow.fetch_token(code=clean_code)
            self.credentials = self.flow.credentials
            
            # Authenticated YouTube service oluştur
            self.authenticated_youtube = build('youtube', 'v3', credentials=self.credentials)
            self.is_authenticated = True
            
            # Token'ı kaydet
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            
            dialog.destroy()
            messagebox.showinfo("Success", "✅ Authentication successful!\n\nYou can now remove videos from your YouTube playlists.")
            
            # Authentication status'unu güncelle
            self.update_auth_status()
            
        except Exception as e:
            error_msg = str(e)
            if "invalid_grant" in error_msg.lower():
                messagebox.showerror("Error", "Invalid authorization code. Please try again.\n\nMake sure you copied the entire code correctly.")
            elif "access_denied" in error_msg.lower():
                messagebox.showerror("Error", "Access was denied. Please make sure you:\n1. Are logged in as m.islam0422@gmail.com\n2. Click 'Allow' when prompted\n3. Are added as a test user in Google Cloud Console")
            else:
                messagebox.showerror("Error", f"Authentication failed: {error_msg}\n\nPlease try again or check your internet connection.")

    def logout_oauth(self):
        """OAuth2 logout"""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
            
            self.credentials = None
            self.authenticated_youtube = None
            self.is_authenticated = False
            
            self.update_auth_status()
            messagebox.showinfo("Success", "Successfully logged out!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Logout failed: {str(e)}")

    def update_auth_status(self):
        """Authentication status'unu güncelle"""
        if hasattr(self, 'auth_status_label'):
            if self.is_authenticated:
                self.auth_status_label.config(text="✨ 🔐 Authenticated & Ready! ✨", fg=self.colors['accent_green'],
                                             font=('Segoe UI', 12, 'bold'))
                self.auth_btn.config(text="🚪 Logout", command=self.logout_oauth, style='Warning.TButton')
                # YouTube removal butonunu aktif et
                if hasattr(self, 'remove_from_youtube_btn'):
                    self.remove_from_youtube_btn.config(state='normal')
            else:
                self.auth_status_label.config(text="⚠️ Authentication Required", fg=self.colors['accent_orange'],
                                             font=('Segoe UI', 12, 'bold'))
                self.auth_btn.config(text="🔐 Login", command=self.start_oauth_flow, style='Success.TButton')
                # YouTube removal butonunu deaktif et
                if hasattr(self, 'remove_from_youtube_btn'):
                    self.remove_from_youtube_btn.config(state='disabled')

    def create_auth_widget(self, parent):
        """Create Authentication Widget (Modern Widget Approach)"""
        # Main frame
        auth_frame = ttk.Frame(parent, style='Dark.TFrame')
        
        # Left side - status
        auth_left_frame = ttk.Frame(auth_frame, style='Dark.TFrame')
        auth_left_frame.pack(side='left')
        
        self.auth_status_label = tk.Label(
            auth_left_frame, 
            text="⚠️ Authentication Required",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_orange']
        )
        self.auth_status_label.pack(side='left')
        
        # Right side - button  
        auth_right_frame = ttk.Frame(auth_frame, style='Dark.TFrame')
        auth_right_frame.pack(side='right')
        
        self.auth_btn = ttk.Button(
            auth_right_frame,
            text="🔐 Login",
            command=self.start_oauth_flow,
            style='Success.TButton'
        )
        self.auth_btn.pack(side='right')
        
        # Update status
        self.update_auth_status()
        
        return auth_frame
    
    def create_playlist_input_widget(self, parent):
        """Create Playlist Input Widget (Modern Widget Approach)"""
        # Main frame
        url_frame = ttk.Frame(parent, style='Dark.TFrame')
        
        # Title with modern styling
        title_label = tk.Label(
            url_frame,
            text="🎵 Playlist URL",
            font=('Segoe UI', 13, 'bold'),
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_cyan']
        )
        title_label.pack(anchor='w', pady=(0, 8))
        
        # Input container with modern border
        input_container = tk.Frame(
            url_frame,
            bg=self.colors['accent_cyan'],
            bd=1,
            relief='solid'
        )
        input_container.pack(fill='x', pady=(0, 10))
        
        # Input frame inside container
        url_input_frame = ttk.Frame(input_container, style='Dark.TFrame')
        url_input_frame.pack(fill='x', padx=2, pady=2)
        
        # URL Entry with enhanced styling
        self.url_entry = ttk.Entry(
            url_input_frame,
            font=('Segoe UI', 11),
            style='Dark.TEntry',
            width=60
        )
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(5, 0), pady=3)
        
        # Modern paste button
        paste_btn = ttk.Button(
            url_input_frame,
            text="📋 Paste",
            command=self.paste_url,
            style='Neon.TButton'
        )
        paste_btn.pack(side='right', padx=(10, 5), pady=3)
        
        # Playlist info with enhanced styling
        info_container = tk.Frame(
            url_frame,
            bg=self.colors['bg_tertiary'],
            bd=1,
            relief='solid'
        )
        info_container.pack(fill='x', pady=(0, 10))
        
        self.playlist_info_frame = ttk.Frame(info_container, style='Dark.TFrame')
        self.playlist_info_frame.pack(fill='x', padx=10, pady=8)
        
        self.playlist_info_label = tk.Label(
            self.playlist_info_frame,
            text="💡 Enter a YouTube playlist URL above to get started...",
            font=('Segoe UI', 10, 'italic'),
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_secondary'],
            wraplength=800,
            justify='left'
        )
        self.playlist_info_label.pack(anchor='w')
        
        # Bind events
        self.url_entry.bind('<KeyRelease>', self.on_url_change)
        self.url_entry.bind('<FocusOut>', self.on_url_change)
        
        return url_frame
    
    def create_main_button_group(self, parent):
        """Create Main Action Button Group - Modern Professional Design"""
        # Container with modern minimalist styling
        container = tk.Frame(
            parent,
            bg=self.colors['bg_secondary'],
            bd=0,
            relief='flat'
        )
        
        # Title with refined styling
        title = tk.Label(
            container,
            text="Primary Actions",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        title.pack(pady=(12, 8))
        
        # Button frame with improved spacing
        button_frame = ttk.Frame(container, style='Dark.TFrame')
        button_frame.pack(pady=(0, 12), padx=12, fill='x')
        
        # Main action button - larger and more prominent
        self.get_videos_btn = ttk.Button(
            button_frame, 
            text="Get Videos & Check 4K",
            command=self.get_videos, 
            style='Success.TButton'
        )
        self.get_videos_btn.grid(row=0, column=0, columnspan=2, padx=0, pady=(0, 8), sticky='ew')
        
        # Secondary control buttons
        self.stop_btn = ttk.Button(
            button_frame, 
            text="Stop",
            command=self.stop_processing, 
            style='Danger.TButton',
            state='disabled'
        )
        self.stop_btn.grid(row=1, column=0, padx=(0, 4), pady=0, sticky='ew')
        
        self.clear_btn = ttk.Button(
            button_frame, 
            text="Clear All",
            command=self.clear_all, 
            style='Dark.TButton'
        )
        self.clear_btn.grid(row=1, column=1, padx=(4, 0), pady=0, sticky='ew')
        
        # Configure grid weights for equal distribution
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        return container
    
    def create_action_button_group(self, parent):
        """Create Video Action Button Group - Modern Professional Design"""
        # Container with modern minimalist styling
        container = tk.Frame(
            parent,
            bg=self.colors['bg_secondary'],
            bd=0,
            relief='flat'
        )
        
        # Title with refined styling
        title = tk.Label(
            container,
            text="Video Actions",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        title.pack(pady=(12, 8))
        
        # Button frame with improved spacing
        button_frame = ttk.Frame(container, style='Dark.TFrame')
        button_frame.pack(pady=(0, 12), padx=12, fill='x')
        
        # Row 1: Selection management
        self.check_all_btn = ttk.Button(
            button_frame, 
            text="Select All",
            command=self.check_all_videos, 
            style='Neon.TButton',
            state='disabled'
        )
        self.check_all_btn.grid(row=0, column=0, padx=(0, 4), pady=(0, 6), sticky='ew')
        
        self.uncheck_all_btn = ttk.Button(
            button_frame, 
            text="Select None",
            command=self.uncheck_all_videos, 
            style='Dark.TButton',
            state='disabled'
        )
        self.uncheck_all_btn.grid(row=0, column=1, padx=(4, 0), pady=(0, 6), sticky='ew')
        
        # Row 2: Smart selection
        self.check_4k_only_btn = ttk.Button(
            button_frame, 
            text="Select 4K Only",
            command=self.check_4k_only, 
            style='Gradient.TButton',
            state='disabled'
        )
        self.check_4k_only_btn.grid(row=1, column=0, columnspan=2, padx=0, pady=(0, 6), sticky='ew')
        
        # Row 3: Actions
        self.copy_btn = ttk.Button(
            button_frame, 
            text="Copy URLs",
            command=self.copy_checked_urls, 
            style='Neon.TButton',
            state='disabled'
        )
        self.copy_btn.grid(row=2, column=0, padx=(0, 4), pady=0, sticky='ew')
        
        # YouTube removal button
        self.remove_from_youtube_btn = ttk.Button(
            button_frame, 
            text="Remove from YouTube",
            command=self.remove_checked_from_youtube, 
            style='Warning.TButton',
            state='disabled'
        )
        self.remove_from_youtube_btn.grid(row=2, column=1, padx=(4, 0), pady=0, sticky='ew')
        
        # Configure grid weights for equal distribution
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        return container
    
    def create_video_list_widget(self, parent):
        """Create Modern Video List Widget"""
        # Main container with gradient border
        container = tk.Frame(
            parent,
            bg=self.colors['accent_purple'],
            bd=3,
            relief='solid'
        )
        
        # Inner frame
        list_frame = ttk.Frame(container, style='Dark.TFrame')
        list_frame.pack(fill='both', expand=True, padx=3, pady=3)
        
        # Header with modern styling
        header_frame = tk.Frame(
            list_frame,
            bg=self.colors['bg_tertiary'],
            height=50
        )
        header_frame.pack(fill='x', pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Video count and header
        self.video_count_label = tk.Label(
            header_frame,
            text="🎬✨ Videos Found: 0 ✨🎬",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_tertiary'],
            fg=self.colors['accent_cyan']
        )
        self.video_count_label.pack(expand=True)
        
        # Tree container with enhanced styling
        tree_container = tk.Frame(
            list_frame,
            bg=self.colors['accent_cyan'],
            bd=2,
            relief='solid'
        )
        tree_container.pack(fill='both', expand=True)
        
        # Treeview frame
        tree_frame = ttk.Frame(tree_container, style='Dark.TFrame')
        tree_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Enhanced TreeView
        columns = ('Check', 'No', 'Thumbnail', 'Title', 'Quality', 'Status')
        self.video_tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show='headings',
            height=15, 
            style='Dark.Treeview'
        )
        
        # Modern column headers with enhanced styling
        headers = {
            'Check': '☑️ Select',
            'No': '#️⃣ No',
            'Thumbnail': '🖼️ Preview',
            'Title': '🎬 Video Title',
            'Quality': '📺 Quality',
            'Status': '✨ 4K Status'
        }
        
        for col, header_text in headers.items():
            self.video_tree.heading(col, text=header_text)
        
        # Enhanced column widths
        widths = {
            'Check': (60, 60),
            'No': (50, 50),
            'Thumbnail': (90, 90),
            'Title': (420, 200),
            'Quality': (100, 100),
            'Status': (140, 140)
        }
        
        for col, (width, minwidth) in widths.items():
            self.video_tree.column(col, width=width, minwidth=minwidth)
        
        # Modern scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient='vertical',
            command=self.video_tree.yview
        )
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack with enhanced layout
        self.video_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind events
        self.video_tree.bind('<Button-3>', self.show_context_menu)  # Right-click
        self.video_tree.bind('<Button-1>', self.on_tree_click)  # Left-click
        
        # Create context menu
        self.create_context_menu()
        
        # Bind limit entry event
        self.limit_entry.bind('<KeyRelease>', self.on_entry_change)
        
        return container
    
    def create_status_widget(self, parent):
        """Create Modern Status Widget - Ultra Dark"""
        # Container with ultra-dark styling
        container = tk.Frame(
            parent,
            bg=self.colors['bg_tertiary'],
            bd=1,
            relief='solid',
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        
        # Inner frame
        progress_frame = ttk.Frame(container, style='Dark.TFrame')
        progress_frame.pack(fill='x', padx=3, pady=3)
        
        # Enhanced progress bar
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            style='Dark.Horizontal.TProgressbar'
        )
        self.progress.pack(fill='x', pady=(0, 8))
        
        # Status message with ultra-dark styling
        status_container = tk.Frame(
            progress_frame,
            bg=self.colors['bg_primary'],
            bd=1,
            relief='solid',
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        status_container.pack(fill='x')
        
        self.status_label = tk.Label(
            status_container,
            text="Enter playlist URL and click 'Get Videos' to start",
            font=('Segoe UI', 11, 'normal'),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_secondary'],
            pady=8
        )
        self.status_label.pack()
        
        return container
    
    def update_status(self, message, color=None):
        """Update status message with optional color"""
        if color is None:
            color = self.colors['text_accent']
        self.status_label.config(text=message, fg=color)
    
    def update_video_count(self, count):
        """Update video count in the header"""
        if hasattr(self, 'video_count_label'):
            self.video_count_label.config(text=f"{count} videos found")
    
    def setup_dark_theme(self):
        """Configure ultra-dark theme for ttk widgets"""
        style = ttk.Style()
        
        # Configure treeview style
        style.theme_use('clam')
        
        # Configure styles for different widgets with ultra-dark theme
        style.configure('Dark.Treeview',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       fieldbackground=self.colors['bg_primary'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       rowheight=65,
                       font=('Segoe UI', 10))
        
        style.configure('Dark.Treeview.Heading',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_accent'],
                       borderwidth=1,
                       relief='flat',
                       bordercolor=self.colors['border'],
                       font=('Segoe UI', 11, 'bold'))
        
        style.map('Dark.Treeview',
                 background=[('selected', self.colors['bg_hover'])],
                 foreground=[('selected', self.colors['text_primary'])])
        
        # Özel tag stilleri - seçili satırları vurgulamak için
        style.configure('Dark.Treeview.selected',
                       background=self.colors['accent_green'],
                       foreground='#ffffff')
        
        style.configure('Dark.Treeview.normal',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Dark.TFrame',
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        style.configure('Dark.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10))
        
        style.configure('Dark.TEntry',
                       fieldbackground=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       bordercolor=self.colors['border'],
                       borderwidth=1,
                       insertcolor=self.colors['accent_cyan'],
                       relief='solid',
                       font=('Segoe UI', 11))
        
        style.configure('Dark.TButton',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none',
                       font=('Segoe UI', 10, 'normal'))
        
        style.map('Dark.TButton',
                 background=[('active', self.colors['bg_hover']),
                           ('pressed', '#4a4a4a')])
        
        style.configure('Success.TButton',
                       background=self.colors['accent_green'],
                       foreground='#ffffff',
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'))
        
        style.map('Success.TButton',
                 background=[('active', '#059669'),
                           ('pressed', '#047857')])
        
        style.configure('Warning.TButton',
                       background=self.colors['accent_orange'],
                       foreground='#ffffff',
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'))
        
        style.map('Warning.TButton',
                 background=[('active', '#d97706'),
                           ('pressed', '#b45309')])
        
        style.configure('Danger.TButton',
                       background=self.colors['accent_red'],
                       foreground='#ffffff',
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'))
        
        style.map('Danger.TButton',
                 background=[('active', '#dc2626'),
                           ('pressed', '#b91c1c')])
        
        # Modern button styles with professional appearance
        style.configure('Gradient.TButton',
                       background=self.colors['accent_purple'],
                       foreground='#ffffff',
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'))
        
        style.map('Gradient.TButton',
                 background=[('active', '#7c3aed'),
                           ('pressed', '#6d28d9')])
        
        style.configure('Neon.TButton',
                       background=self.colors['accent_cyan'],
                       foreground='#ffffff',
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'))
        
        style.map('Neon.TButton',
                 background=[('active', '#0891b2'),
                           ('pressed', '#0e7490')])
        
        style.configure('Dark.Horizontal.TProgressbar',
                       background=self.colors['accent_green'],
                       troughcolor=self.colors['bg_secondary'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       lightcolor=self.colors['accent_green'],
                       darkcolor=self.colors['accent_green'])
    
    def create_widgets(self):
        # Ana frame container
        main_container = ttk.Frame(self.root, style='Dark.TFrame')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Ana başlık - clean and professional
        title_label = tk.Label(main_container, text="YouTube 4K Video Checker", 
                              font=('Segoe UI', 24, 'normal'), 
                              bg=self.colors['bg_primary'], 
                              fg=self.colors['text_primary'])
        title_label.pack(pady=(0, 20))
        
        # Main layout container - split into left and right
        layout_container = ttk.Frame(main_container, style='Dark.TFrame')
        layout_container.pack(fill='both', expand=True)
        
        # ========== LEFT PANEL (Controls) ==========
        left_panel = tk.Frame(
            layout_container,
            bg=self.colors['bg_secondary'],
            bd=0,
            relief='flat',
            width=450  # Fixed width for left panel
        )
        left_panel.pack(side='left', fill='y', padx=(0, 12))
        left_panel.pack_propagate(False)  # Maintain fixed width
        
        # Left panel content with improved padding
        left_content = ttk.Frame(left_panel, style='Dark.TFrame')
        left_content.pack(fill='both', expand=True, padx=16, pady=16)
        
        # Authentication Section
        auth_section = tk.Label(
            left_content,
            text="Authentication",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        auth_section.pack(anchor='w', pady=(0, 8))
        
        self.auth_widget = self.create_auth_widget(left_content)
        self.auth_widget.pack(pady=(0, 24), fill='x')
        
        # Playlist Section
        playlist_section = tk.Label(
            left_content,
            text="Playlist Settings",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        playlist_section.pack(anchor='w', pady=(0, 8))
        
        self.playlist_widget = self.create_playlist_input_widget(left_content)
        self.playlist_widget.pack(pady=(0, 24), fill='x')
        
        # Video Limit Section
        limit_section = tk.Label(
            left_content,
            text="Video Limit",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        limit_section.pack(anchor='w', pady=(0, 8))
        
        # Video sayısı sınırı
        limit_frame = ttk.Frame(left_content, style='Dark.TFrame')
        limit_frame.pack(pady=(0, 8), fill='x')
        
        ttk.Label(limit_frame, text="Maximum video count:", 
                 font=('Segoe UI', 11, 'bold'), style='Dark.TLabel').pack(anchor='w', pady=(0, 5))
        
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
                                              bg=self.colors['bg_secondary'],
                                              fg=self.colors['text_primary'],
                                              font=('Segoe UI', 10),
                                              activebackground=self.colors['bg_secondary'],
                                              activeforeground=self.colors['text_primary'],
                                              selectcolor=self.colors['bg_tertiary'])
        self.all_videos_check.pack(side='right', padx=(10, 0))
        
        # Show only 4K filter - Modern switch design
        filter_frame = ttk.Frame(limit_frame, style='Dark.TFrame')
        filter_frame.pack(fill='x', pady=(10, 0))
        
        # Filter container with modern styling
        filter_container = tk.Frame(
            filter_frame,
            bg=self.colors['bg_tertiary'],
            bd=2,
            relief='solid'
        )
        filter_container.pack(fill='x', pady=(0, 5))
        
        # Filter inner frame
        filter_inner = ttk.Frame(filter_container, style='Dark.TFrame')
        filter_inner.pack(fill='x', padx=10, pady=8)
        
        # 4K filter switch with enhanced styling
        self.show_4k_only_var = tk.BooleanVar(value=True)  # Automatically active
        
        # Left side - icon and label
        filter_left = ttk.Frame(filter_inner, style='Dark.TFrame')
        filter_left.pack(side='left')
        
        filter_icon = tk.Label(
            filter_left,
            text="✨ 4K Filter:",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['bg_tertiary'],
            fg=self.colors['accent_cyan']
        )
        filter_icon.pack(side='left')
        
        # Right side - switch
        filter_right = ttk.Frame(filter_inner, style='Dark.TFrame')
        filter_right.pack(side='right')
        
        # Modern switch-style checkbox
        self.show_4k_only_check = tk.Checkbutton(
            filter_right, 
            text="Show Only 4K Videos",
            variable=self.show_4k_only_var,
            command=self.on_4k_filter_toggle,
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 10, 'bold'),
            activebackground=self.colors['bg_tertiary'],
            activeforeground=self.colors['accent_green'],
            selectcolor=self.colors['accent_green'],
            relief='flat',
            bd=0
        )
        self.show_4k_only_check.pack(side='right')
        
        # Status indicator
        self.filter_status_label = tk.Label(
            filter_right,
            text="🟢 Active",
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['bg_tertiary'],
            fg=self.colors['accent_green']
        )
        self.filter_status_label.pack(side='right', padx=(0, 10))
        
        # Actions Section
        actions_section = tk.Label(
            left_content,
            text="Actions",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        actions_section.pack(anchor='w', pady=(24, 8))
        
        # Modern Button Groups
        self.main_buttons = self.create_main_button_group(left_content)
        self.main_buttons.pack(pady=(0, 12), fill='x')
        
        self.action_buttons = self.create_action_button_group(left_content)
        self.action_buttons.pack(pady=(0, 24), fill='x')
        
        # Status Section
        status_section = tk.Label(
            left_content,
            text="Status",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        status_section.pack(anchor='w', pady=(0, 8))
        
        self.status_widget = self.create_status_widget(left_content)
        self.status_widget.pack(fill='x', pady=(0, 0))
        
        # ========== RIGHT PANEL (Video List) ==========
        right_panel = tk.Frame(
            layout_container,
            bg=self.colors['bg_secondary'],
            bd=0,
            relief='flat'
        )
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Right panel header
        right_header = tk.Frame(
            right_panel,
            bg=self.colors['bg_secondary'],
            height=60
        )
        right_header.pack(fill='x', padx=16, pady=(16, 0))
        right_header.pack_propagate(False)
        
        list_title = tk.Label(
            right_header,
            text="Video List",
            font=('Segoe UI', 18, 'normal'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        list_title.pack(side='left', pady=20)
        
        # Video count in header - cleaner styling
        self.video_count_label = tk.Label(
            right_header,
            text="No videos loaded",
            font=('Segoe UI', 12, 'normal'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary']
        )
        self.video_count_label.pack(side='right', pady=20)
        
        # Modern Video List Widget
        self.video_list_widget = self.create_video_list_widget_no_header(right_panel)
        self.video_list_widget.pack(fill='both', expand=True, padx=16, pady=(0, 16))
    
    def create_video_list_widget_no_header(self, parent):
        """Create Modern Video List Widget without header (for right panel) - Ultra Dark"""
        # Tree container with ultra-dark styling
        tree_container = tk.Frame(
            parent,
            bg=self.colors['bg_primary'],
            bd=1,
            relief='solid',
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        
        # Treeview frame
        tree_frame = ttk.Frame(tree_container, style='Dark.TFrame')
        tree_frame.pack(fill='both', expand=True, padx=1, pady=1)
        
        # Enhanced TreeView
        columns = ('Check', 'No', 'Thumbnail', 'Title', 'Quality', 'Status')
        self.video_tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show='headings',
            height=20,  # Taller since we have more space
            style='Dark.Treeview'
        )
        
        # Modern column headers with enhanced styling
        headers = {
            'Check': '☑️ Select',
            'No': '#️⃣ No',
            'Thumbnail': '🖼️ Preview',
            'Title': '🎬 Video Title',
            'Quality': '📺 Quality',
            'Status': '✨ 4K Status'
        }
        
        for col, header_text in headers.items():
            self.video_tree.heading(col, text=header_text)
        
        # Enhanced column widths - adjusted for right panel
        widths = {
            'Check': (60, 60),
            'No': (50, 50),
            'Thumbnail': (90, 90),
            'Title': (450, 200),  # Wider title for more space
            'Quality': (100, 100),
            'Status': (140, 140)
        }
        
        for col, (width, minwidth) in widths.items():
            self.video_tree.column(col, width=width, minwidth=minwidth)
        
        # Modern scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient='vertical',
            command=self.video_tree.yview
        )
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack with enhanced layout
        self.video_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind events
        self.video_tree.bind('<Button-3>', self.show_context_menu)  # Right-click
        self.video_tree.bind('<Button-1>', self.on_tree_click)  # Left-click
        
        # Create context menu
        self.create_context_menu()
        
        # Bind limit entry event
        self.limit_entry.bind('<KeyRelease>', self.on_entry_change)
        
        return tree_container

    def create_context_menu(self):
        """Create ultra-dark right-click context menu for video list"""
        self.context_menu = tk.Menu(self.root, tearoff=0,
                                   bg=self.colors['bg_primary'],
                                   fg=self.colors['text_primary'],
                                   activebackground=self.colors['accent_cyan'],
                                   activeforeground=self.colors['bg_primary'],
                                   borderwidth=1,
                                   relief='solid',
                                   bd=1,
                                   font=('Segoe UI', 10))
        
        # Ultra-dark menu items with colorful icons and better spacing
        self.context_menu.add_command(
            label="  📋  Copy Video URL", 
            command=self.copy_selected_url,
            background=self.colors['bg_primary'],
            activebackground=self.colors['accent_green'],
            foreground=self.colors['text_primary'],
            activeforeground=self.colors['bg_primary'],
            font=('Segoe UI', 10, 'normal')
        )
        
        # Styled separator
        self.context_menu.add_separator(background=self.colors['bg_hover'])
        
        self.context_menu.add_command(
            label="  🗑️  Remove from Local List", 
            command=self.remove_selected_video,
            background=self.colors['bg_primary'],
            activebackground=self.colors['accent_orange'],
            foreground=self.colors['text_primary'],
            activeforeground=self.colors['bg_primary'],
            font=('Segoe UI', 10, 'normal')
        )
        
        # Add YouTube playlist removal if authenticated
        if self.is_authenticated:
            self.context_menu.add_separator(background=self.colors['bg_hover'])
            self.context_menu.add_command(
                label="  ❌  Remove from YouTube Playlist", 
                command=self.remove_selected_from_youtube,
                background=self.colors['bg_primary'],
                activebackground=self.colors['accent_red'],
                foreground=self.colors['text_primary'],
                activeforeground=self.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')
            )
        
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Select the item under cursor
        item = self.video_tree.identify('item', event.x, event.y)
        if item:
            self.video_tree.selection_set(item)
            # Recreate context menu to update authentication status
            self.create_context_menu()
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
    
    def remove_selected_from_youtube(self):
        """Remove the selected video from YouTube playlist"""
        if not self.is_authenticated:
            messagebox.showerror("Error", "Authentication required for this operation!")
            return
            
        selection = self.video_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "No video selected!")
            return
            
        item = selection[0]
        video_id = self.video_tree.item(item)['tags'][0] if self.video_tree.item(item)['tags'] else None
        
        if not video_id:
            messagebox.showerror("Error", "Could not find video ID!")
            return
        
        video_title = self.video_tree.item(item, 'values')[3]  # Title column
        
        # Confirmation
        confirm = messagebox.askyesno("Confirm Removal", 
                                     f"⚠️ WARNING: This will permanently remove this video from your YouTube playlist:\n\n"
                                     f"'{video_title[:50]}...'\n\n"
                                     "This action cannot be undone. Are you sure?")
        
        if not confirm:
            return
        
        # Create video data for removal
        video_data = [{
            'video_id': video_id,
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'title': video_title,
            'tree_item': item
        }]
        
        # Start removal
        self.progress.start()
        self.status_label.config(text=f"🗑️ Removing '{video_title[:30]}...' from YouTube playlist...")
        
        thread = threading.Thread(target=self._remove_from_playlist_thread, args=(video_data,))
        thread.daemon = True
        thread.start()
    
    def remove_checked_from_youtube(self):
        """Remove checked videos from YouTube playlist"""
        if not self.is_authenticated:
            messagebox.showerror("Error", "Authentication required for this operation!")
            return
        
        # Get checked videos
        checked_video_data = []
        
        for item in self.video_tree.get_children():
            values = self.video_tree.item(item, 'values')
            is_checked = values[0] == '☑️'
            
            if is_checked:
                # Get video ID from tags
                video_id = self.video_tree.item(item)['tags'][0] if self.video_tree.item(item)['tags'] else None
                if video_id:
                    checked_video_data.append({
                        'video_id': video_id,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'title': values[3],  # Title column
                        'tree_item': item
                    })
        
        if not checked_video_data:
            messagebox.showwarning("Warning", "No videos are checked!")
            return
        
        # Confirmation dialog
        confirm = messagebox.askyesno("Confirm Bulk Removal", 
                                     f"⚠️ WARNING: This will permanently remove {len(checked_video_data)} checked videos from your YouTube playlist!\n\n"
                                     "This action cannot be undone. Are you sure?")
        
        if not confirm:
            return
        
        # Start removal
        self.progress.start()
        self.status_label.config(text=f"🗑️ Removing {len(checked_video_data)} videos from YouTube playlist...")
        
        thread = threading.Thread(target=self._remove_from_playlist_thread, args=(checked_video_data,))
        thread.daemon = True
        thread.start()
    
    def on_tree_click(self, event):
        """Handle left-click on treeview to toggle checkboxes"""
        item = self.video_tree.identify('item', event.x, event.y)
        column = self.video_tree.identify('column', event.x, event.y)
        
        # If clicked on the checkbox column
        if item and column == '#1':  # First column (Check)
            self.toggle_checkbox(item)
    
    def toggle_checkbox(self, item):
        """Toggle checkbox state for an item - Geliştirilmiş görsel feedback"""
        if not self.video_tree.exists(item):
            return
            
        values = list(self.video_tree.item(item, 'values'))
        current_check = values[0]
        
        # Toggle between checked and unchecked with better visual indicators
        if current_check == '✅':
            values[0] = '⬜'  # Daha belirgin unchecked
            # Satır rengini normal yap
            self.video_tree.set(item, 'Check', '⬜')
        else:
            values[0] = '✅'  # Daha belirgin checked
            # Satır rengini vurgulu yap
            self.video_tree.set(item, 'Check', '✅')
        
        self.video_tree.item(item, values=values)
        
        # Satır rengini değiştir (seçili olanları vurgula)
        if values[0] == '✅':
            # Seçili satırı yeşil tonuyla vurgula
            self.video_tree.item(item, tags=('selected',))
        else:
            # Seçili değilse normal
            self.video_tree.item(item, tags=('normal',))
        
        self.update_copy_button_state()
    
    def update_copy_button_state(self):
        """Update copy button state based on checked items - Yeni checkbox formatı"""
        has_checked = any(self.video_tree.item(item, 'values')[0] == '✅' 
                         for item in self.video_tree.get_children())
        
        if has_checked:
            self.copy_btn.config(state='normal')
            # YouTube removal butonunu da kontrol et (authentication gerekli)
            if self.is_authenticated and hasattr(self, 'remove_from_youtube_btn'):
                self.remove_from_youtube_btn.config(state='normal')
        else:
            self.copy_btn.config(state='disabled')
            # YouTube removal butonunu deaktif et
            if hasattr(self, 'remove_from_youtube_btn'):
                self.remove_from_youtube_btn.config(state='disabled')
    
    def check_all_videos(self):
        """Check all videos in the list - Geliştirilmiş görsel feedback ile"""
        for item in self.video_tree.get_children():
            values = list(self.video_tree.item(item, 'values'))
            values[0] = '✅'
            self.video_tree.item(item, values=values, tags=('selected',))
        self.update_copy_button_state()
    
    def uncheck_all_videos(self):
        """Uncheck all videos in the list - Geliştirilmiş görsel feedback ile"""
        for item in self.video_tree.get_children():
            values = list(self.video_tree.item(item, 'values'))
            values[0] = '⬜'
            self.video_tree.item(item, values=values, tags=('normal',))
        self.update_copy_button_state()
    
    def check_4k_only(self):
        """Check only videos that have 4K available - Geliştirilmiş görsel feedback ile"""
        for item in self.video_tree.get_children():
            values = list(self.video_tree.item(item, 'values'))
            status = values[5]  # Status column
            if '✅ 4K Available!' in status:
                values[0] = '✅'
                self.video_tree.item(item, values=values, tags=('selected',))
            else:
                values[0] = '⬜'
                self.video_tree.item(item, values=values, tags=('normal',))
        self.update_copy_button_state()
    
    def copy_checked_urls(self):
        """Copy URLs of checked videos to clipboard"""
        checked_urls = []
        checked_video_data = []
        
        for item in self.video_tree.get_children():
            values = self.video_tree.item(item, 'values')
            is_checked = values[0] == '☑️'
            
            if is_checked:
                # Get video ID from tags
                video_id = self.video_tree.item(item)['tags'][0] if self.video_tree.item(item)['tags'] else None
                if video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    checked_urls.append(url)
                    checked_video_data.append({
                        'video_id': video_id,
                        'url': url,
                        'title': values[3],  # Title column
                        'tree_item': item
                    })
        
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
            
            # Show options dialog
            self.show_copy_options_dialog(checked_video_data, len(checked_urls))
            
        except Exception as e:
            messagebox.showerror("Error", f"URLs could not be copied: {str(e)}")
    
    def show_copy_options_dialog(self, checked_video_data, count):
        """Show options after copying URLs"""
        dialog = tk.Toplevel(self.root)
        dialog.title("URLs Copied - What's Next?")
        dialog.geometry("500x350")
        dialog.configure(bg=self.colors['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Dialog içeriği
        tk.Label(dialog, text="✅ URLs Copied to Clipboard!", 
                font=('Segoe UI', 16, 'bold'),
                bg=self.colors['bg_primary'], 
                fg=self.colors['accent_green']).pack(pady=20)
        
        tk.Label(dialog, text=f"{count} video URLs have been copied to your clipboard.",
                font=('Segoe UI', 11),
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_secondary']).pack(pady=10)
        
        tk.Label(dialog, text="What would you like to do next?",
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_primary']).pack(pady=(20, 10))
        
        # Options frame
        options_frame = ttk.Frame(dialog, style='Dark.TFrame')
        options_frame.pack(pady=10, fill='x', padx=40)
        
        # Option 1: Just close
        ttk.Button(options_frame, text="📋 Just Copy (Done)", 
                  command=dialog.destroy,
                  style='Dark.TButton').pack(fill='x', pady=5)
        
        # Option 2: Remove from local list
        ttk.Button(options_frame, text="🗑️ Remove from Local List", 
                  command=lambda: self.remove_from_local_list(checked_video_data, dialog),
                  style='Warning.TButton').pack(fill='x', pady=5)
        
        # Option 3: Remove from YouTube playlist (if authenticated)
        if self.is_authenticated:
            ttk.Button(options_frame, text="❌ Remove from YouTube Playlist", 
                      command=lambda: self.remove_from_youtube_playlist(checked_video_data, dialog),
                      style='Danger.TButton').pack(fill='x', pady=5)
        else:
            # Show authentication required
            auth_frame = ttk.Frame(options_frame, style='Dark.TFrame')
            auth_frame.pack(fill='x', pady=5)
            
            ttk.Button(auth_frame, text="❌ Remove from YouTube Playlist", 
                      state='disabled',
                      style='Danger.TButton').pack(fill='x')
            
            tk.Label(auth_frame, text="(Requires authentication)",
                    font=('Segoe UI', 9),
                    bg=self.colors['bg_primary'], 
                    fg=self.colors['text_secondary']).pack()
    
    def remove_from_local_list(self, video_data, dialog):
        """Remove videos from local list only"""
        for video in video_data:
            if self.video_tree.exists(video['tree_item']):
                self.video_tree.delete(video['tree_item'])
        
        # Update found_4k_videos list
        for video in video_data:
            if video['url'] in self.found_4k_videos:
                self.found_4k_videos.remove(video['url'])
        
        dialog.destroy()
        self.status_label.config(text=f"✅ {len(video_data)} videos removed from local list")
        self.update_copy_button_state()
    
    def remove_from_youtube_playlist(self, video_data, dialog):
        """Remove videos from actual YouTube playlist"""
        if not self.is_authenticated:
            messagebox.showerror("Error", "Authentication required for this operation!")
            return
        
        # Confirmation dialog
        confirm = messagebox.askyesno("Confirm Removal", 
                                     f"⚠️ WARNING: This will permanently remove {len(video_data)} videos from your YouTube playlist!\n\n"
                                     "This action cannot be undone. Are you sure?")
        
        if not confirm:
            return
        
        dialog.destroy()
        
        # Show progress and start removal in thread
        self.progress.start()
        self.status_label.config(text="🗑️ Removing videos from YouTube playlist...")
        
        thread = threading.Thread(target=self._remove_from_playlist_thread, args=(video_data,))
        thread.daemon = True
        thread.start()
    
    def _remove_from_playlist_thread(self, video_data):
        """Remove videos from YouTube playlist in thread"""
        try:
            playlist_url = self.url_entry.get().strip()
            playlist_id = self.extract_playlist_id(playlist_url)
            
            removed_count = 0
            failed_count = 0
            
            for i, video in enumerate(video_data):
                try:
                    self.root.after(0, lambda v=video, idx=i: 
                                   self.status_label.config(text=f"🗑️ Removing {v['title'][:30]}... ({idx+1}/{len(video_data)})"))
                    
                    # Find playlist item ID
                    playlist_item_id = self.find_playlist_item_id(playlist_id, video['video_id'])
                    
                    if playlist_item_id:
                        # Remove from playlist
                        self.authenticated_youtube.playlistItems().delete(id=playlist_item_id).execute()
                        
                        # Remove from local list
                        self.root.after(0, lambda item=video['tree_item']: 
                                       self.video_tree.delete(item) if self.video_tree.exists(item) else None)
                        
                        # Remove from found_4k_videos
                        if video['url'] in self.found_4k_videos:
                            self.found_4k_videos.remove(video['url'])
                        
                        removed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    print(f"Failed to remove video {video['video_id']}: {e}")
                    failed_count += 1
            
            # Update UI
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.update_copy_button_state())
            
            if removed_count > 0:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"✅ {removed_count} videos removed from YouTube playlist" + 
                         (f", {failed_count} failed" if failed_count > 0 else "")))
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                                                               f"✅ Successfully removed {removed_count} videos from your YouTube playlist!" +
                                                               (f"\n\n⚠️ {failed_count} videos could not be removed." if failed_count > 0 else "")))
            else:
                self.root.after(0, lambda: self.status_label.config(text="❌ No videos could be removed from playlist"))
                self.root.after(0, lambda: messagebox.showerror("Error", "No videos could be removed from the playlist. Check your permissions."))
                
        except Exception as e:
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to remove videos: {str(e)}"))
    
    def find_playlist_item_id(self, playlist_id, video_id):
        """Find the playlist item ID for a specific video in a playlist"""
        try:
            next_page_token = None
            
            while True:
                request = self.authenticated_youtube.playlistItems().list(
                    part='id,contentDetails',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response['items']:
                    if item['contentDetails']['videoId'] == video_id:
                        return item['id']
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
        except Exception as e:
            print(f"Error finding playlist item ID: {e}")
        
        return None
    
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
    
    def on_4k_filter_toggle(self):
        """4K filter toggle değiştiğinde"""
        if self.show_4k_only_var.get():
            # 4K filter aktif
            self.filter_status_label.config(text="🟢 Active", fg=self.colors['accent_green'])
            self.show_4k_only_check.config(fg=self.colors['accent_green'])
        else:
            # 4K filter pasif
            self.filter_status_label.config(text="🔴 Inactive", fg=self.colors['accent_red'])
            self.show_4k_only_check.config(fg=self.colors['text_secondary'])
        
        # Video listesini filtrele
        self.apply_4k_filter()
    
    def apply_4k_filter(self):
        """4K filtresini video listesine uygula - Waiting videoları da göster"""
        if not hasattr(self, 'video_tree'):
            return
        
        # Initialize detached items storage if not exists
        if not hasattr(self, 'detached_items'):
            self.detached_items = []
            
        if self.show_4k_only_var.get():
            # Clear any previously detached items
            self.detached_items = []
            
            # Get all items (including detached ones)
            all_items = list(self.video_tree.get_children())
            
            # Also get any items that might be detached
            for item in getattr(self, '_all_tree_items', []):
                if item not in all_items and self.video_tree.exists(item):
                    all_items.append(item)
            
            visible_count = 0
            for item in all_items:
                if not self.video_tree.exists(item):
                    continue
                    
                values = self.video_tree.item(item, 'values')
                if len(values) > 5:  # Status column exists
                    status = values[5]  # Status column
                    # 4K video veya henüz kontrol edilmemiş (Waiting) ise göster
                    # Ancak eğer işlem stop edilmişse, sadece 4K Available olanları göster
                    if hasattr(self, 'stop_requested') and self.stop_requested:
                        # Stop edilmişse sadece 4K available olanları göster
                        if '✅ 4K Available!' in status:
                            # 4K video - görünür yap (eğer gizliyse)
                            try:
                                parent = self.video_tree.parent(item)
                                if parent == '':  # Already attached to root
                                    visible_count += 1
                                else:  # Need to reattach
                                    self.video_tree.reattach(item, '', 'end')
                                    visible_count += 1
                            except:
                                try:
                                    self.video_tree.reattach(item, '', 'end')
                                    visible_count += 1
                                except:
                                    pass
                        else:
                            # Waiting veya No 4K - gizle
                            try:
                                parent = self.video_tree.parent(item)
                                if parent == '':  # Currently attached to root
                                    self.video_tree.detach(item)
                                    self.detached_items.append(item)
                            except:
                                pass
                    else:
                        # Normal durum: 4K video veya henüz kontrol edilmemiş (Waiting) ise göster
                        if '✅ 4K Available!' in status or 'Waiting...' in status:
                            # 4K video veya waiting - görünür yap (eğer gizliyse)
                            try:
                                parent = self.video_tree.parent(item)
                                if parent == '':  # Already attached to root
                                    visible_count += 1
                                else:  # Need to reattach
                                    self.video_tree.reattach(item, '', 'end')
                                    visible_count += 1
                            except:
                                try:
                                    self.video_tree.reattach(item, '', 'end')
                                    visible_count += 1
                                except:
                                    pass
                        else:
                            # 4K değil ve waiting de değil - gizle
                            try:
                                parent = self.video_tree.parent(item)
                                if parent == '':  # Currently attached to root
                                    self.video_tree.detach(item)
                                    self.detached_items.append(item)
                            except:
                                pass
            
            # Video sayısını güncelle
            if hasattr(self, 'video_count_label'):
                total_count = len(getattr(self, '_all_tree_items', all_items))
                # Kaç tane 4K ve kaç tane waiting olduğunu say
                k4_count = 0
                waiting_count = 0
                for item in self.video_tree.get_children():
                    try:
                        values = self.video_tree.item(item, 'values')
                        if len(values) > 5:
                            status = values[5]
                            if '✅ 4K Available!' in status:
                                k4_count += 1
                            elif 'Waiting...' in status:
                                waiting_count += 1
                    except:
                        pass
                
                # Stop edilmişse farklı mesaj göster
                if hasattr(self, 'stop_requested') and self.stop_requested:
                    self.video_count_label.config(
                        text=f"🎬✨ Showing 4K Only: {visible_count}/{total_count} (stopped) ✨🎬"
                    )
                else:
                    self.video_count_label.config(
                        text=f"🎬✨ Showing 4K + Pending: {visible_count}/{total_count} (4K: {k4_count}, Pending: {waiting_count}) ✨🎬"
                    )
        else:
            # Tüm videoları göster - including detached ones
            # First reattach any detached items
            for item in self.detached_items:
                try:
                    if self.video_tree.exists(item):
                        self.video_tree.reattach(item, '', 'end')
                except:
                    pass
            
            # Clear detached items list
            self.detached_items = []
            
            # Ensure all items are visible
            if hasattr(self, '_all_tree_items'):
                for item in self._all_tree_items:
                    try:
                        if self.video_tree.exists(item):
                            parent = self.video_tree.parent(item)
                            if parent != '':  # Not attached to root
                                self.video_tree.reattach(item, '', 'end')
                    except:
                        pass
            
            # Video sayısını güncelle
            if hasattr(self, 'video_count_label'):
                total_count = len(self.video_tree.get_children())
                self.video_count_label.config(text=f"🎬✨ Videos Found: {total_count} ✨🎬")
    
    def stop_processing(self):
        """İşlemi durdurmak için flag'i ayarla ve filtreyi güncelle"""
        self.stop_requested = True
        self.status_label.config(text="⏹️ Process stopping...")
        
        # Eğer 4K filter aktifse, waiting videoları gizlemek için filtreyi yeniden uygula
        if hasattr(self, 'show_4k_only_var') and self.show_4k_only_var.get():
            # Kısa bir delay ile filter'ı güncelle (thread'lerin durması için)
            self.root.after(1000, self.apply_4k_filter)
    
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
        """Video thumbnail'ini yükle - Basitleştirilmiş ve güvenilir yaklaşım"""
        try:
            if video_id in self.thumbnail_cache:
                return self.thumbnail_cache[video_id]
            
            # Basit emoji thumbnail kullan (yükleme sorunları için)
            # Bu SSL/network sorunlarını önler
            return None  # Thumbnail yüklemek yerine emoji kullanacağız
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
        
        # Önceki verileri temizle
        self.clear_video_data()
        
        # Video sayısı sınırını al
        if self.all_videos_var.get():
            max_videos = None  # All
        else:
            max_videos = self.video_limit_var.get()
        
        # Thread'de çalıştır
        thread = threading.Thread(target=self._get_videos_thread, args=(url, max_videos))
        thread.daemon = True
        thread.start()
    
    def clear_video_data(self):
        """Video verilerini temizle (authentication hariç)"""
        # Video listesini temizle
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        
        # İç verileri temizle
        self.found_4k_videos = []
        self.stop_requested = False
        
        # Thumbnail önbelleğini temizle
        self.thumbnail_cache.clear()
        self.thumbnail_refs.clear()
        
        # Detached items'ı temizle
        if hasattr(self, 'detached_items'):
            self.detached_items = []
        
        if hasattr(self, '_all_tree_items'):
            self._all_tree_items = []
        
        if hasattr(self, 'video_details'):
            delattr(self, 'video_details')
        
        # Button durumlarını resetle
        self.copy_btn.config(state='disabled')
        self.check_all_btn.config(state='disabled')
        self.uncheck_all_btn.config(state='disabled')
        self.check_4k_only_btn.config(state='disabled')
        self.remove_from_youtube_btn.config(state='disabled')
        
        # Video count'u güncelle
        self.update_video_count(0)
    
    def _get_videos_thread(self, url, max_videos):
        """Video getirme işlemini thread'de yap ve otomatik 4K kontrolü başlat"""
        self.is_processing = True
        self.progress.start()
        self.get_videos_btn.config(state='disabled')
        
        try:
            self.root.after(0, lambda: self.status_label.config(text="🔍 Analyzing playlist..."))
            
            # YouTube API'nin hazır olduğundan emin ol
            if not hasattr(self, 'youtube') or self.youtube is None:
                self.root.after(0, lambda: self.status_label.config(text="🔧 Initializing YouTube API..."))
                self.setup_youtube_api()
                time.sleep(1)  # API'nin hazır olması için kısa bekleme
            
            # Playlist ID'yi çıkar
            playlist_id = self.extract_playlist_id(url)
            
            # Video ID'lerini al
            self.root.after(0, lambda: self.status_label.config(text="📋 Getting video list..."))
            video_ids = self.get_video_ids_from_playlist(playlist_id, max_videos)
            
            if not video_ids:
                self.root.after(0, lambda: messagebox.showerror("Error", "No videos found in playlist or playlist is private!"))
                return
            
            self.root.after(0, lambda: self.status_label.config(text=f"📥 {len(video_ids)} videos found, getting details..."))
            
            # Video detaylarını al
            self.video_details = self.get_video_details(video_ids)
            
            if not self.video_details:
                self.root.after(0, lambda: messagebox.showerror("Error", "Could not get video details!"))
                return
            
            # GUI'yi güncelle
            self.root.after(0, self._update_video_list)
            
            # Video yükleme işlemi tamamlandı - is_processing'i false yap
            self.is_processing = False
            self.progress.stop()
            self.get_videos_btn.config(state='normal')
            
            # Videos successfully loaded, now automatically start 4K checking
            if hasattr(self, 'video_details') and self.video_details:
                self.root.after(0, lambda: self.status_label.config(text="✨ Videos loaded successfully! Starting 4K check..."))
                # Start 4K checking automatically
                self.root.after(1000, self._start_4k_check_automatically)  # Small delay for UI update
            
        except Exception as e:
            error_msg = f"Error getting videos: {str(e)}"
            print(f"_get_videos_thread error: {error_msg}")
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.status_label.config(text="❌ Failed to get videos"))
        finally:
            self.is_processing = False
            self.progress.stop()
            self.get_videos_btn.config(state='normal')
    
    def _start_4k_check_automatically(self):
        """Otomatik olarak 4K kontrolünü başlat"""
        if hasattr(self, 'video_details') and self.video_details and not self.is_processing:
            self.root.after(0, lambda: self.status_label.config(text="🔍 Starting automatic 4K check..."))
            # Start 4K checking thread
            thread = threading.Thread(target=self._check_4k_thread)
            thread.daemon = True
            thread.start()
        else:
            # Eğer hala processing ise, biraz daha bekle
            if hasattr(self, 'video_details') and self.video_details:
                self.root.after(500, self._start_4k_check_automatically)
    
    def _update_video_list(self):
        """Video listesini güncelle"""
        # Listeyi temizle
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        
        # Store all tree items for filter management
        self._all_tree_items = []
        
        # Videoları ekle
        for i, video in enumerate(self.video_details, 1):
            quality = "HD" if video['definition'] == 'hd' else "SD"
            
            # Kaliteye göre emoji seç
            if video['definition'] == 'hd':
                thumbnail_emoji = "🎬"  # HD için film emoji
            else:
                thumbnail_emoji = "📱"  # SD için mobil emoji
            
            # Item'ı ekle video_id'yi tag olarak ekle, checkbox unchecked olarak başla
            item_id = self.video_tree.insert('', 'end', values=(
                '⬜',  # Checkbox - unchecked by default (daha belirgin)
                i, 
                thumbnail_emoji,  # Emoji thumbnail (güvenilir)
                video['title'][:50] + "..." if len(video['title']) > 50 else video['title'],
                quality,
                "Waiting..."
            ), tags=(video['id'], 'normal'))  # normal tag ekle
            
            # Store item ID for filter management
            self._all_tree_items.append(item_id)
        
        # Initialize detached items list
        self.detached_items = []
        
        # Apply current filter if active
        if hasattr(self, 'show_4k_only_var') and self.show_4k_only_var.get():
            self.apply_4k_filter()
        
        # Check management buttons'ı aktif et
        self.check_all_btn.config(state='normal')
        self.uncheck_all_btn.config(state='normal')
        
        # Update video count
        self.update_video_count(len(self.video_details))
        
        self.status_label.config(text=f"📺 {len(self.video_details)} videos listed. 4K check will start automatically...")
    
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
        """4K kontrol işlemini thread'de yap - Paralel işleme ile hızlandırılmış"""
        self.is_processing = True
        self.stop_requested = False
        self.progress.start()
        self.stop_btn.config(state='normal')  # Stop butonunu aktif et
        self.copy_btn.config(state='disabled')  # Copy butonunu deaktif et
        self.found_4k_videos = []
        
        try:
            hd_videos = [v for v in self.video_details if v['definition'] == 'hd']
            
            if not hd_videos:
                # SD videoları için durum güncelle
                sd_videos = [v for v in self.video_details if v['definition'] == 'sd']
                for video in sd_videos:
                    self.root.after(0, lambda v=video: self._update_video_status(v, "📱 SD Quality"))
                
                self.root.after(0, self._show_results)
                return
            
            # Paralel işleme için ThreadPoolExecutor kullan - daha az thread, daha güvenilir
            max_workers = min(6, len(hd_videos))  # Maksimum 6 thread (daha stabil)
            completed_count = 0
            failed_count = 0
            
            self.root.after(0, lambda: self.status_label.config(text=f"🚀 Smart 4K scanning with {max_workers} threads..."))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Tüm videoları submit et
                future_to_video = {
                    executor.submit(self.check_4k_availability, video['url']): video 
                    for video in hd_videos
                }
                
                # Sonuçları al
                for future in as_completed(future_to_video, timeout=120):  # 2 dakika toplam timeout
                    # Durduruluyor mu kontrol et
                    if self.stop_requested:
                        # Tüm futures'ı iptal et
                        for f in future_to_video:
                            if not f.done():
                                f.cancel()
                        break
                    
                    video = future_to_video[future]
                    completed_count += 1
                    
                    try:
                        is_4k = future.result(timeout=3)  # 3 saniye timeout per video
                        
                        if is_4k:
                            self.found_4k_videos.append(video['url'])
                            self.root.after(0, lambda v=video: self._update_video_status(v, "✅ 4K Available!"))
                        else:
                            self.root.after(0, lambda v=video: self._update_video_status(v, "❌ No 4K"))
                    
                    except Exception as e:
                        print(f"Error checking video {video['id']}: {e}")
                        failed_count += 1
                        self.root.after(0, lambda v=video: self._update_video_status(v, "⚠️ Check Failed"))
                    
                    # Progress güncelle
                    progress_text = f"🔍 Scanning: {completed_count}/{len(hd_videos)} ({len(self.found_4k_videos)} 4K found)"
                    if failed_count > 0:
                        progress_text += f" [{failed_count} failed]"
                    self.root.after(0, lambda text=progress_text: self.status_label.config(text=text))
            
            # Timeout olan videoları kontrol et
            remaining_videos = []
            for future, video in future_to_video.items():
                if not future.done() and not self.stop_requested:
                    remaining_videos.append(video)
                    self.root.after(0, lambda v=video: self._update_video_status(v, "⏰ Timeout"))
            
            if remaining_videos and not self.stop_requested:
                timeout_text = f"⚠️ {len(remaining_videos)} videos timed out"
                self.root.after(0, lambda text=timeout_text: self.status_label.config(text=text))
            
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
                
                # Stop edildiğinde 4K filter aktifse, waiting videoları gizlemek için filtreyi güncelle
                if hasattr(self, 'show_4k_only_var') and self.show_4k_only_var.get():
                    self.root.after(500, self.apply_4k_filter)  # Kısa delay ile filter güncelle
                    
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"4K check error: {str(e)}"))
        finally:
            self.is_processing = False
            self.stop_requested = False
            self.progress.stop()
            self.stop_btn.config(state='disabled')  # Stop butonunu deaktif et
    
    def _update_video_status(self, video, status):
        """Video durumunu güncelle"""
        for item in getattr(self, '_all_tree_items', self.video_tree.get_children()):
            if not self.video_tree.exists(item):
                continue
                
            values = self.video_tree.item(item, 'values')
            if video['title'][:50] in values[3]:  # Title sütunu (index 3 now)
                new_values = list(values)
                new_values[5] = status  # Status sütunu (index 5 now)
                self.video_tree.item(item, values=new_values)
                
                # 4K filter aktifse kontrol et
                if hasattr(self, 'show_4k_only_var') and self.show_4k_only_var.get():
                    # Eğer işlem stop edilmişse, sadece 4K Available olanları göster
                    if hasattr(self, 'stop_requested') and self.stop_requested:
                        if '✅ 4K Available!' not in status:
                            try:
                                # Check if currently visible
                                parent = self.video_tree.parent(item)
                                if parent == '':  # Currently attached to root
                                    self.video_tree.detach(item)
                                    if not hasattr(self, 'detached_items'):
                                        self.detached_items = []
                                    if item not in self.detached_items:
                                        self.detached_items.append(item)
                            except:
                                pass
                        else:
                            # 4K ise görünür yap (eğer gizliyse)
                            try:
                                parent = self.video_tree.parent(item)
                                if parent != '':  # Currently detached
                                    self.video_tree.reattach(item, '', 'end')
                                    if hasattr(self, 'detached_items') and item in self.detached_items:
                                        self.detached_items.remove(item)
                            except:
                                pass
                    else:
                        # Normal durum: Sadece 4K olmayan VE waiting olmayan videoları gizle
                        if '✅ 4K Available!' not in status and 'Waiting...' not in status:
                            try:
                                # Check if currently visible
                                parent = self.video_tree.parent(item)
                                if parent == '':  # Currently attached to root
                                    self.video_tree.detach(item)
                                    if not hasattr(self, 'detached_items'):
                                        self.detached_items = []
                                    if item not in self.detached_items:
                                        self.detached_items.append(item)
                            except:
                                pass
                        else:
                            # 4K veya waiting ise görünür yap (eğer gizliyse)
                            try:
                                parent = self.video_tree.parent(item)
                                if parent != '':  # Currently detached
                                    self.video_tree.reattach(item, '', 'end')
                                    if hasattr(self, 'detached_items') and item in self.detached_items:
                                        self.detached_items.remove(item)
                            except:
                                pass
                
                break
        
        # Video sayısını güncelle
        if hasattr(self, 'show_4k_only_var') and self.show_4k_only_var.get():
            # Update filtered count
            visible_count = len(self.video_tree.get_children())
            total_count = len(getattr(self, '_all_tree_items', []))
            
            k4_count = 0
            waiting_count = 0
            for item in self.video_tree.get_children():
                try:
                    values = self.video_tree.item(item, 'values')
                    if len(values) > 5:
                        item_status = values[5]
                        if '✅ 4K Available!' in item_status:
                            k4_count += 1
                        elif 'Waiting...' in item_status:
                            waiting_count += 1
                except:
                    pass
            
            if hasattr(self, 'video_count_label'):
                self.video_count_label.config(
                    text=f"🎬✨ Showing 4K + Pending: {visible_count}/{total_count} (4K: {k4_count}, Pending: {waiting_count}) ✨🎬"
                )
    
    def update_filtered_video_count(self):
        """Filtrelenmiş video sayısını güncelle"""
        if not hasattr(self, 'video_tree') or not hasattr(self, 'video_count_label'):
            return
            
        all_items = list(self.video_tree.get_children())
        # Detached items'ı da say
        detached_items = []
        
        # Tüm video sayısını bul (attached + detached)
        total_count = len(self.video_details) if hasattr(self, 'video_details') else len(all_items)
        
        if hasattr(self, 'show_4k_only_var') and self.show_4k_only_var.get():
            # Sadece görünür 4K videoları say
            visible_4k_count = 0
            for item in all_items:
                values = self.video_tree.item(item, 'values')
                if len(values) > 5:  # Status column exists
                    status = values[5]  # Status column
                    if '✅ 4K Available!' in status:
                        visible_4k_count += 1
            
            self.video_count_label.config(text=f"🎬✨ 4K Videos: {visible_4k_count}/{total_count} ✨🎬")
        else:
            self.video_count_label.config(text=f"🎬✨ Videos Found: {total_count} ✨🎬")
    
    def _show_results(self):
        """Sonuçları göster"""
        total_videos = len(self.video_details)
        found_count = len(self.found_4k_videos)
        
        # 4K filtresini uygula (eğer aktifse)
        if hasattr(self, 'show_4k_only_var') and self.show_4k_only_var.get():
            self.apply_4k_filter()
        
        self.status_label.config(text=f"✅ Scan completed! {total_videos} videos scanned, {found_count} 4K videos found.")
        
        # Check 4K Only butonunu aktif et
        self.check_4k_only_btn.config(state='normal')
        
        if self.found_4k_videos:
            if hasattr(self, 'show_4k_only_var') and self.show_4k_only_var.get():
                messagebox.showinfo("Result", f"🎉 {found_count} 4K videos found!\n\n✨ 4K Filter is active - showing only 4K videos.\nUse checkboxes to select videos and copy URLs.")
            else:
                messagebox.showinfo("Result", f"🎉 {found_count} 4K videos found!\n\nUse checkboxes to select videos and copy URLs.")
        else:
            messagebox.showinfo("Result", "😔 No 4K videos found.\n\nThis playlist doesn't have 4K quality videos.")
    
    def check_4k_availability(self, video_url):
        """4K kalite kontrolü - Güvenilir ve hızlı yöntem"""
        try:
            # Video ID'yi çıkar
            video_id = None
            if 'watch?v=' in video_url:
                video_id = video_url.split('watch?v=')[1].split('&')[0]
            elif '/embed/' in video_url:
                video_id = video_url.split('/embed/')[1].split('?')[0]
            
            if not video_id:
                return False
            
            # Önce hızlı format kontrolü yap
            result = self.quick_format_check(video_id)
            if result is not None:  # Başarılı oldu
                return result
            
            # Fallback: YouTube API kontrolü (daha yavaş ama güvenilir)
            try:
                if hasattr(self, 'youtube') and self.youtube:
                    request = self.youtube.videos().list(
                        part='contentDetails',
                        id=video_id
                    )
                    response = request.execute()
                    
                    if response['items']:
                        video_info = response['items'][0]
                        content_details = video_info.get('contentDetails', {})
                        
                        # Definition HD ise muhtemelen 4K var (basit kontrol)
                        definition = content_details.get('definition', 'sd')
                        if definition == 'hd':
                            # HD ise basit sayfa kontrolü yap
                            return self.simple_4k_check(video_id)
                        else:
                            return False
                
            except Exception as api_error:
                print(f"API error for {video_id}: {api_error}")
                # API hatası durumunda basit kontrol
                pass
            
            # Son çare: Basit kontrol
            return self.simple_4k_check(video_id)
                
        except Exception as e:
            print(f"4K check error for {video_url}: {e}")
            return False
    
    def quick_format_check(self, video_id):
        """Hızlı 4K format kontrolü - None döner başarısız olursa"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
            }
            
            # YouTube'un internal API endpoint'i
            info_url = "https://www.youtube.com/youtubei/v1/player"
            
            payload = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20240101.00.00"
                    }
                },
                "videoId": video_id
            }
            
            response = requests.post(
                info_url, 
                json=payload,
                headers=headers,
                timeout=6,  # Kısa timeout
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Streaming data'yı kontrol et
                streaming_data = data.get('streamingData', {})
                adaptive_formats = streaming_data.get('adaptiveFormats', [])
                
                # 4K formatları ara
                for fmt in adaptive_formats:
                    height = fmt.get('height', 0)
                    quality_label = fmt.get('qualityLabel', '')
                    itag = fmt.get('itag', 0)
                    
                    # 4K formatlarını kontrol et
                    if (height >= 2160 or 
                        '2160p' in quality_label or 
                        '4K' in quality_label or
                        itag in [313, 315, 337, 401, 571]):
                        return True
                
                return False
            else:
                # HTTP hatası - None döner
                return None
                
        except Exception as e:
            print(f"Quick format check error for {video_id}: {e}")
            return None  # Hata durumunda None döner
    
    def simple_4k_check(self, video_id):
        """En basit 4K kontrolü - video sayfasından"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = f"https://www.youtube.com/watch?v={video_id}"
            response = requests.get(url, headers=headers, timeout=5, verify=False)
            
            if response.status_code == 200:
                content = response.text
                # 4K işaretlerini ara
                indicators = [
                    '"2160p"', '"qualityLabel":"2160p"', 'itag":313', 'itag":315',
                    'height":2160', '"4K"', '2160p60'
                ]
                
                for indicator in indicators:
                    if indicator in content:
                        return True
            
            return False
            
        except Exception as e:
            print(f"Simple 4K check error for {video_id}: {e}")
            return False
    
    def clear_all(self):
        """Tüm verileri temizle (authentication hariç)"""
        self.url_entry.delete(0, tk.END)
        self.playlist_info_label.config(text="💡 Enter a YouTube playlist URL above to get started...")  # Playlist bilgilerini temizle
        
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        
        self.status_label.config(text="Enter playlist URL and click 'Get Videos' to start")
        self.stop_btn.config(state='disabled')
        self.copy_btn.config(state='disabled')
        self.check_all_btn.config(state='disabled')
        self.uncheck_all_btn.config(state='disabled')
        self.check_4k_only_btn.config(state='disabled')
        self.remove_from_youtube_btn.config(state='disabled')
        self.found_4k_videos = []
        self.stop_requested = False
        
        # Update video count
        self.update_video_count(0)
        self.thumbnail_cache.clear()  # Thumbnail önbelleğini temizle
        self.thumbnail_refs.clear()   # Thumbnail referanslarını temizle
        
        if hasattr(self, 'video_details'):
            delattr(self, 'video_details')
        
        # Authentication durumunu koru - sadece UI'yi güncelle
        self.update_auth_status()

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTube4KCheckerGUI(root)
    root.mainloop()
