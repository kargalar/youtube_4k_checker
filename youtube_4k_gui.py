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
from dotenv import load_dotenv
import json
import pickle
from PIL import Image, ImageTk
import io
import webbrowser
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from widgets.video_actions_widget import VideoActionsWidget
import httplib2

# SSL uyarılarını devre dışı bırak
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class YouTube4KCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 4K Video Checker")
        self.root.geometry("1200x900")

        # Modern professional dark theme with sophisticated colors
        self.colors = {
            'bg_primary': '#1a1a1a',
            'bg_secondary': '#242424',
            'bg_tertiary': '#2d2d2d',
            'bg_hover': '#383838',
            'text_primary': '#f5f5f5',
            'text_secondary': '#b8b8b8',
            'text_accent': '#6366f1',
            'accent_blue': '#3b82f6',
            'accent_green': '#10b981',
            'accent_orange': '#f59e0b',
            'accent_red': '#ef4444',
            'accent_purple': '#8b5cf6',
            'accent_pink': '#ec4899',
            'accent_yellow': '#eab308',
            'accent_cyan': '#06b6d4',
            'border': '#404040',
            'gradient_start': '#4f46e5',
            'gradient_end': '#7c3aed'
        }

        self.root.configure(bg=self.colors['bg_primary'])

        # Configure ttk styles for dark theme
        self.setup_dark_theme()

        # Load environment variables (.env support)
        try:
            load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
            load_dotenv()
        except Exception:
            pass

        # API Key
        self.API_KEY = os.getenv('YOUTUBE_API_KEY', '')
        self.api_key = self.API_KEY
        self.setup_youtube_api()

        # OAuth2 state
        self.authenticated_youtube = None
        self.credentials = None
        self.flow = None
        self.is_authenticated = False
        self.oauth_scopes = ['https://www.googleapis.com/auth/youtube']
        self.oauth_redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        # Guards to prevent double-open
        self.oauth_dialog = None
        self.oauth_dialog_open = False
        self.oauth_browser_opened = False
        self.oauth_flow_active = False

        # OAuth2 files
        self.client_secrets_file = os.getenv(
            'CLIENT_SECRETS_FILE',
            os.path.join(os.path.dirname(__file__), 'client_secret.json')
        )
        self.token_file = os.getenv(
            'TOKEN_FILE',
            os.path.join(os.path.dirname(__file__), 'token.pickle')
        )

        # Check existing auth
        self.check_existing_authentication()

        # Processing state
        self.is_processing = False
        self.stop_requested = False
        self.found_4k_videos = []
        self.thumbnail_cache = {}
        self.thumbnail_refs = []

        self.create_widgets()
    
    def setup_youtube_api(self):
        """YouTube API'yi başlat"""
        try:
            if not hasattr(self, 'youtube') or self.youtube is None:
                if not self.API_KEY:
                    raise ValueError("YOUTUBE_API_KEY ortam değişkeni tanımlı değil.")

                # Use an HTTP client with a strict timeout to avoid long hangs on discovery
                http = httplib2.Http(timeout=10)

                # Small retry loop in case of transient network hiccups
                last_err = None
                for attempt in range(1, 4):
                    try:
                        self.youtube = build(
                            'youtube', 'v3',
                            developerKey=self.API_KEY,
                            http=http,
                            cache_discovery=False
                        )
                        print(f"YouTube API initialized successfully (attempt {attempt})")
                        break
                    except Exception as e:
                        last_err = e
                        print(f"YouTube API init attempt {attempt} failed: {e}")
                        time.sleep(min(1.5 * attempt, 4))

                if self.youtube is None and last_err:
                    raise last_err
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
            # Global guard for re-entrancy (e.g., double-clicks)
            if getattr(self, 'oauth_flow_active', False):
                return
            self.oauth_flow_active = True
            # Prevent re-entrancy / double clicks opening multiple dialogs/tabs
            if getattr(self, 'oauth_dialog_open', False) and self.oauth_dialog:
                try:
                    self.oauth_dialog.lift()
                    self.oauth_dialog.focus_force()
                except Exception:
                    pass
                self.oauth_flow_active = False
                return
            if not os.path.exists(self.client_secrets_file):
                messagebox.showerror("Error", f"OAuth2 credentials file not found: {self.client_secrets_file}")
                self.oauth_flow_active = False
                return
            
            self.flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=self.oauth_scopes,
                redirect_uri=self.oauth_redirect_uri
            )
            
            auth_url, _ = self.flow.authorization_url(prompt='consent')
            
            # Browser'da URL'yi aç
            # Ensure we only auto-open once per flow
            if not getattr(self, 'oauth_browser_opened', False):
                webbrowser.open(auth_url)
                self.oauth_browser_opened = True
            
            # Kullanıcıdan authorization code iste
            self.show_oauth_dialog(auth_url)
            
        except Exception as e:
            messagebox.showerror("Error", f"OAuth flow could not be started: {str(e)}")
            self.oauth_flow_active = False

    def show_oauth_dialog(self, auth_url):
        """OAuth2 authorization dialog göster"""
        dialog = tk.Toplevel(self.root)
        dialog.title("YouTube Authentication")
        dialog.geometry("700x500")
        dialog.configure(bg=self.colors['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()
        # Mark dialog as open and keep a reference
        self.oauth_dialog = dialog
        self.oauth_dialog_open = True
        
        def on_close():
            # Reset guards when dialog closes
            self.oauth_dialog_open = False
            self.oauth_dialog = None
            self.oauth_flow_active = False
            self.oauth_browser_opened = False
            # Do not reset oauth_browser_opened here to avoid double-open if user re-opens quickly
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", on_close)
        
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
        
        def on_cancel():
            # User-cancelled auth; reset dialog state guards
            self.oauth_dialog_open = False
            self.oauth_dialog = None
            self.oauth_flow_active = False
            self.oauth_browser_opened = False
            dialog.destroy()
        ttk.Button(btn_frame, text="❌ Cancel", 
                  command=on_cancel,
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
            # Reset dialog/browser guards after successful auth
            self.oauth_dialog_open = False
            self.oauth_dialog = None
            self.oauth_browser_opened = False
            self.oauth_flow_active = False
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
            # On any error, allow another attempt
            try:
                dialog.destroy()
            except Exception:
                pass
            self.oauth_dialog_open = False
            self.oauth_dialog = None
            self.oauth_flow_active = False

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
    
    # Removed: create_playlist_input_widget (replaced by widgets.playlist_input_widget.PlaylistInputWidget)
    
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
        """Deprecated: Kept for compatibility; now replaced by VideoActionsWidget."""
        placeholder = tk.Frame(parent, bg=self.colors['bg_secondary'])
        return placeholder
    
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
        columns = ('No', 'Thumbnail', 'Title', 'Quality', 'Status')
        self.video_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=15,
            style='Dark.Treeview'
        )
        # Column headers
        headers = {
            'No': '#',
            'Thumbnail': '🖼️ Preview',
            'Title': '🎬 Video Title',
            'Quality': '📺 Quality',
            'Status': '✨ 4K Status'
        }
        for col, header_text in headers.items():
            self.video_tree.heading(col, text=header_text)
        # Column widths
        widths = {
            'No': (36, 30),
            'Thumbnail': (90, 90),
            'Title': (420, 200),
            'Quality': (100, 100),
            'Status': (140, 140)
        }
        for col, (width, minwidth) in widths.items():
            self.video_tree.column(col, width=width, minwidth=minwidth)
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient='vertical',
            command=self.video_tree.yview
        )
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        # Pack
        self.video_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        # Events
        self.video_tree.bind('<Button-3>', self.show_context_menu)
        self.video_tree.bind('<Button-1>', self.on_tree_click)
        self.video_tree.bind('<Delete>', lambda e: self.remove_checked_from_list())
        # Context menu
        self.create_context_menu()
        # Limit entry event
        self.limit_entry.bind('<KeyRelease>', self.on_entry_change)
        return container
    
    # Removed: create_status_widget (replaced by widgets.status_bar_widget.StatusBarWidget)
    
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

        # Base theme
        style.theme_use('clam')

        # Treeview
        style.configure('Dark.Treeview',
                        background=self.colors['bg_primary'],
                        foreground=self.colors['text_primary'],
                        fieldbackground=self.colors['bg_primary'],
                        borderwidth=1,
                        relief='solid',
                        bordercolor=self.colors['border'],
                        rowheight=110,
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

        # Treeview row tags
        style.configure('Dark.Treeview.selected',
                        background=self.colors['accent_green'],
                        foreground='#ffffff')

        style.configure('Dark.Treeview.normal',
                        background=self.colors['bg_primary'],
                        foreground=self.colors['text_primary'])

        # Frames/Labels/Entries
        style.configure('Dark.TFrame', background=self.colors['bg_primary'], borderwidth=0)
        style.configure('Dark.TLabel', background=self.colors['bg_primary'],
                        foreground=self.colors['text_primary'], font=('Segoe UI', 10))
        style.configure('Dark.TEntry', fieldbackground=self.colors['bg_secondary'],
                        foreground=self.colors['text_primary'], bordercolor=self.colors['border'],
                        borderwidth=1, insertcolor=self.colors['accent_cyan'], relief='solid',
                        font=('Segoe UI', 11))

        # Buttons
        style.configure('Dark.TButton', background=self.colors['bg_tertiary'],
                        foreground=self.colors['text_primary'], borderwidth=0,
                        relief='flat', focuscolor='none', font=('Segoe UI', 10, 'normal'))
        style.map('Dark.TButton',
                  background=[('active', self.colors['bg_hover']),
                              ('pressed', '#4a4a4a'),
                              ('disabled', self.colors['bg_tertiary'])],
                  foreground=[('disabled', self.colors['text_secondary'])])

        style.configure('Success.TButton', background=self.colors['accent_green'],
                        foreground='#ffffff', borderwidth=0, relief='flat',
                        focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Success.TButton',
                  background=[('active', '#059669'), ('pressed', '#047857'), ('disabled', self.colors['accent_green'])],
                  foreground=[('disabled', self.colors['text_secondary'])])

        style.configure('Warning.TButton', background=self.colors['accent_orange'],
                        foreground='#ffffff', borderwidth=0, relief='flat',
                        focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Warning.TButton',
                  background=[('active', '#d97706'), ('pressed', '#b45309'), ('disabled', self.colors['accent_orange'])],
                  foreground=[('disabled', self.colors['text_secondary'])])

        style.configure('Danger.TButton', background=self.colors['accent_red'],
                        foreground='#ffffff', borderwidth=0, relief='flat',
                        focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Danger.TButton',
                  background=[('active', '#dc2626'), ('pressed', '#b91c1c'), ('disabled', self.colors['accent_red'])],
                  foreground=[('disabled', self.colors['text_secondary'])])

        style.configure('Gradient.TButton', background=self.colors['accent_purple'],
                        foreground='#ffffff', borderwidth=0, relief='flat',
                        focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Gradient.TButton',
                  background=[('active', '#7c3aed'), ('pressed', '#6d28d9'), ('disabled', self.colors['accent_purple'])],
                  foreground=[('disabled', self.colors['text_secondary'])])

        style.configure('Neon.TButton', background=self.colors['accent_cyan'],
                        foreground='#ffffff', borderwidth=0, relief='flat',
                        focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Neon.TButton',
                  background=[('active', '#0891b2'), ('pressed', '#0e7490'), ('disabled', self.colors['accent_cyan'])],
                  foreground=[('disabled', self.colors['text_secondary'])])

        # Progressbar
        style.configure('Dark.Horizontal.TProgressbar', background=self.colors['accent_green'],
                        troughcolor=self.colors['bg_secondary'], borderwidth=1, relief='solid',
                        bordercolor=self.colors['border'], lightcolor=self.colors['accent_green'],
                        darkcolor=self.colors['accent_green'])
    
    def create_widgets(self):
        # Ana frame container
        main_container = ttk.Frame(self.root, style='Dark.TFrame')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title_label = tk.Label(
            main_container,
            text="YouTube 4K Video Checker",
            font=('Segoe UI', 24, 'normal'),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
        )
        title_label.pack(pady=(0, 20))

        # Main layout container
        layout_container = ttk.Frame(main_container, style='Dark.TFrame')
        layout_container.pack(fill='both', expand=True)

        # LEFT PANEL
        left_panel = tk.Frame(
            layout_container,
            bg=self.colors['bg_secondary'],
            bd=0,
            relief='flat',
            width=450,
        )
        left_panel.pack(side='left', fill='y', padx=(0, 12))
        left_panel.pack_propagate(False)

        left_content = ttk.Frame(left_panel, style='Dark.TFrame')
        left_content.pack(fill='both', expand=True, padx=16, pady=16)

        # Authentication
        auth_section = tk.Label(
            left_content,
            text="Authentication",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
        )
        auth_section.pack(anchor='w', pady=(0, 8))

        from widgets.auth_widget import AuthenticationWidget
        self.auth_widget = AuthenticationWidget(
            left_content, self.colors, self.start_oauth_flow, self.logout_oauth
        )
        self.auth_widget.pack(pady=(0, 24), fill='x')
        self.auth_status_label = self.auth_widget.status_label
        self.auth_btn = self.auth_widget.auth_btn
        self.update_auth_status()

        # Playlist settings
        playlist_section = tk.Label(
            left_content,
            text="Playlist Settings",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
        )
        playlist_section.pack(anchor='w', pady=(0, 8))

        from widgets.playlist_input_widget import PlaylistInputWidget
        self.playlist_input = PlaylistInputWidget(
            left_content, self.colors, self.on_url_change, self.paste_url
        )
        self.playlist_input.pack(pady=(0, 24), fill='x')
        self.url_entry = self.playlist_input.url_entry
        self.playlist_info_label = self.playlist_input.info_label

        # Video Limit + 4K Filter
        from widgets.limit_filter_widget import LimitFilterWidget
        self.limit_filter = LimitFilterWidget(
            left_content,
            self.colors,
            on_slider_change=self.on_slider_change,
            on_entry_change=self.on_entry_change,
            on_all_videos_toggle=self.on_all_videos_toggle,
            on_4k_filter_toggle=self.on_4k_filter_toggle,
        )
        self.limit_filter.pack(fill='x', pady=(0, 12))
        self.video_limit_var = self.limit_filter.video_limit_var
        self.limit_slider = self.limit_filter.limit_slider
        self.limit_entry = self.limit_filter.limit_entry
        self.all_videos_var = self.limit_filter.all_videos_var
        self.all_videos_check = self.limit_filter.all_videos_check
        self.show_4k_only_var = self.limit_filter.show_4k_only_var
        self.show_4k_only_check = self.limit_filter.show_4k_only_check
        self.filter_status_label = self.limit_filter.filter_status_label

        # Actions
        actions_section = tk.Label(
            left_content,
            text="Actions",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
        )
        actions_section.pack(anchor='w', pady=(24, 8))

        from widgets.main_actions_widget import MainActionsWidget
        self.main_actions = MainActionsWidget(
            left_content,
            self.colors,
            callbacks={
                'get_videos': self.get_videos,
                'stop': self.stop_processing,
                'clear': self.clear_all,
            },
        )
        self.main_actions.pack(pady=(0, 12), fill='x')
        self.get_videos_btn = self.main_actions.get_videos_btn
        self.stop_btn = self.main_actions.stop_btn
        self.clear_btn = self.main_actions.clear_btn

        self.video_actions = VideoActionsWidget(
            left_content,
            self.colors,
            commands={
                'check_all': self.check_all_videos,
                'uncheck_all': self.uncheck_all_videos,
                'check_4k_only': self.check_4k_only,
                'copy_urls': self.copy_checked_urls,
                'remove_from_list': self.remove_checked_from_list,
                'remove_from_youtube': self.remove_checked_from_youtube,
            },
        )
        self.video_actions.pack(pady=(0, 24), fill='x')
        self.check_all_btn = self.video_actions.check_all_btn
        self.uncheck_all_btn = self.video_actions.uncheck_all_btn
        self.check_4k_only_btn = self.video_actions.check_4k_only_btn
        self.copy_btn = self.video_actions.copy_btn
        self.remove_from_list_btn = self.video_actions.remove_from_list_btn
        self.remove_from_youtube_btn = self.video_actions.remove_from_youtube_btn

        # Status
        status_section = tk.Label(
            left_content,
            text="Status",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
        )
        status_section.pack(anchor='w', pady=(0, 8))

        from widgets.status_bar_widget import StatusBarWidget
        self.status_bar = StatusBarWidget(left_content, self.colors)
        self.status_bar.pack(fill='x', pady=(0, 0))
        self.progress = self.status_bar.progress
        self.status_label = self.status_bar.status_label

        # RIGHT PANEL
        right_panel = tk.Frame(
            layout_container,
            bg=self.colors['bg_secondary'],
            bd=0,
            relief='flat',
        )
        right_panel.pack(side='right', fill='both', expand=True)

        right_header = tk.Frame(
            right_panel,
            bg=self.colors['bg_secondary'],
            height=60,
        )
        right_header.pack(fill='x', padx=16, pady=(16, 0))
        right_header.pack_propagate(False)

        list_title = tk.Label(
            right_header,
            text="Video List",
            font=('Segoe UI', 18, 'normal'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
        )
        list_title.pack(side='left', pady=20)

        self.video_count_label = tk.Label(
            right_header,
            text="No videos loaded",
            font=('Segoe UI', 12, 'normal'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary'],
        )
        self.video_count_label.pack(side='right', pady=20)

        from widgets.inline_video_list_widget import InlineVideoListWidget
        inline_list = InlineVideoListWidget(right_panel, self.colors)
        inline_list.pack(fill='both', expand=True, padx=16, pady=(0, 16))
        self.video_list_widget = inline_list.frame
        self.video_tree = inline_list.video_tree
        self.video_tree.bind('<Button-3>', self.show_context_menu)  # Right-click
        self.video_tree.bind('<Button-1>', self.on_tree_click)  # Left-click
        self.video_tree.bind('<Delete>', lambda e: self.remove_checked_from_list())
        self.create_context_menu()
        self.limit_entry.bind('<KeyRelease>', self.on_entry_change)
        
    
    
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

        # Enhanced TreeView (use #0 tree column for thumbnails)
        # Remove Select column; use Treeview selection and row highlight
        columns = ('No', 'Title', 'Quality', 'Status')
        self.video_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='tree headings',
            height=20,
            style='Dark.Treeview'
        )

        # Tree column header (thumbnail)
        self.video_tree.heading('#0', text='🖼️')
        headers = {
            'No': '#',
            'Title': '🎬 Video Title',
            'Quality': '📺 Quality',
            'Status': '✨ 4K Status'
        }
        for col, header_text in headers.items():
            self.video_tree.heading(col, text=header_text)

        # Column widths (configure tree column #0 for thumbnails)
        self.video_tree.column('#0', width=180, minwidth=160, anchor='center')
        widths = {
            'No': (36, 30),
            'Title': (450, 200),
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

    # (Preview selection handler removed)

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
        # Preserve existing selection; add the item under cursor if not already selected
        item = self.video_tree.identify('item', event.x, event.y)
        if item and item not in self.video_tree.selection():
            # Add to current selection without clearing others
            current = self.video_tree.selection()
            self.video_tree.selection_set((*current, item))
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

        # Title is now at index 1 (No, Title, Quality, Status)
        video_title = self.video_tree.item(item, 'values')[1]
        
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
    
    def remove_checked_from_list(self):
        """Remove selected videos from the local list (checkbox removed)"""
        removed_count = 0
        items_to_remove = list(self.video_tree.selection())

        for item in items_to_remove:
            # Track URL for 4K list cleanup
            tags = self.video_tree.item(item)['tags']
            video_id = tags[0] if tags else None
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
                if url in self.found_4k_videos:
                    try:
                        self.found_4k_videos.remove(url)
                    except ValueError:
                        pass
            self.video_tree.delete(item)
            removed_count += 1

        if removed_count == 0:
            messagebox.showwarning("Warning", "No videos are selected!")
            return

        # Update UI state and counters
        self.update_copy_button_state()
        self.update_filtered_video_count()
        self.status_label.config(text=f"🗑️ Removed {removed_count} videos from local list")

    def remove_checked_from_youtube(self):
        """Remove selected videos from YouTube playlist (checkbox removed)"""
        if not self.is_authenticated:
            messagebox.showerror("Error", "Authentication required for this operation!")
            return
        
        # Get selected videos
        checked_video_data = []
        for item in self.video_tree.selection():
            values = self.video_tree.item(item, 'values')
            video_id = self.video_tree.item(item)['tags'][0] if self.video_tree.item(item)['tags'] else None
            if video_id:
                checked_video_data.append({
                    'video_id': video_id,
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'title': values[1],  # Title column index updated
                    'tree_item': item
                })
        
        if not checked_video_data:
            messagebox.showwarning("Warning", "No videos are selected!")
            return
        
        # Confirmation dialog
        confirm = messagebox.askyesno("Confirm Bulk Removal", 
                                     f"⚠️ WARNING: This will permanently remove {len(checked_video_data)} checked videos from your YouTube playlist!\n\n"
                                     "This action cannot be undone. Are you sure?")
        
        if not confirm:
            return
        
        # Start removal
        self.progress.start()
        self.status_label.config(text=f"🗑️ Removing {len(checked_video_data)} selected videos from YouTube playlist...")
        
        thread = threading.Thread(target=self._remove_from_playlist_thread, args=(checked_video_data,))
        thread.daemon = True
        thread.start()
    
    def on_tree_click(self, event):
        """Handle left-click: update button states based on selection (no checkboxes)."""
        # Allow default selection behavior, then update buttons shortly after
        self.root.after(10, self.update_copy_button_state)
    
    def toggle_checkbox(self, item):
        """Deprecated: checkboxes removed. Kept for backward compatibility."""
        pass
    
    def update_copy_button_state(self):
        """Enable/disable actions based on current selection (checkboxes removed)."""
        has_selection = len(self.video_tree.selection()) > 0
        
        if has_selection:
            self.copy_btn.config(state='normal')
            # YouTube removal butonunu da kontrol et (authentication gerekli)
            if self.is_authenticated and hasattr(self, 'remove_from_youtube_btn'):
                self.remove_from_youtube_btn.config(state='normal')
            if hasattr(self, 'remove_from_list_btn'):
                self.remove_from_list_btn.config(state='normal')
        else:
            self.copy_btn.config(state='disabled')
            # YouTube removal butonunu deaktif et
            if hasattr(self, 'remove_from_youtube_btn'):
                self.remove_from_youtube_btn.config(state='disabled')
            if hasattr(self, 'remove_from_list_btn'):
                self.remove_from_list_btn.config(state='disabled')
    
    def check_all_videos(self):
        """Select all videos in the list."""
        items = self.video_tree.get_children()
        if items:
            self.video_tree.selection_set(items)
        self.update_copy_button_state()
    
    def uncheck_all_videos(self):
        """Clear selection for all videos in the list."""
        self.video_tree.selection_remove(self.video_tree.selection())
        self.update_copy_button_state()
    
    def check_4k_only(self):
        """Select only videos that have 4K available."""
        self.video_tree.selection_remove(self.video_tree.selection())
        to_select = []
        for item in self.video_tree.get_children():
            values = list(self.video_tree.item(item, 'values'))
            status = values[3]  # Status column index updated
            if '✅ 4K Available!' in status:
                to_select.append(item)
        if to_select:
            self.video_tree.selection_set(to_select)
        self.update_copy_button_state()
    
    def copy_checked_urls(self):
        """Copy URLs of selected videos to clipboard (no dialog)"""
        checked_urls = []
        checked_video_data = []

        for item in self.video_tree.selection():
            values = self.video_tree.item(item, 'values')
            video_id = self.video_tree.item(item)['tags'][0] if self.video_tree.item(item)['tags'] else None
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
                checked_urls.append(url)
                checked_video_data.append({
                    'video_id': video_id,
                    'url': url,
                    'title': values[1],  # Title column index updated
                    'tree_item': item
                })
        
        if not checked_urls:
            messagebox.showwarning("Warning", "No videos are selected!")
            return
        
        # Join URLs with newlines
        urls_text = '\n'.join(checked_urls)
        
        try:
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(urls_text)
            self.root.update()
            # Brief status update only
            self.status_label.config(text=f"✅ Copied {len(checked_urls)} URLs to clipboard")
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
                if len(values) >= 4:  # Status column exists (No, Title, Quality, Status)
                    status = values[3]  # Status column
                    # 4K video veya henüz kontrol edilmemiş (Waiting) ise göster
                    # Ancak eğer işlem stop edilmişse, sadece 4K Available olanları göster
                    if hasattr(self, 'stop_requested') and self.stop_requested:
                        # Stop edilmişse sadece 4K available olanları göster
                        if '✅ 4K Available!' in status:
                            # 4K video - görünür yap (unconditionally reattach)
                            try:
                                self.video_tree.reattach(item, '', 'end')
                                visible_count += 1
                            except:
                                pass
                        else:
                            # Waiting veya No 4K - gizle
                            try:
                                self.video_tree.detach(item)
                                self.detached_items.append(item)
                            except:
                                pass
                    else:
                        # Normal durum: 4K video veya henüz kontrol edilmemiş (Waiting) ise göster
                        if '✅ 4K Available!' in status or 'Waiting...' in status:
                            # 4K video veya waiting - görünür yap (unconditionally reattach)
                            try:
                                self.video_tree.reattach(item, '', 'end')
                                visible_count += 1
                            except:
                                pass
                        else:
                            # 4K değil ve waiting de değil - gizle
                            try:
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
                        if len(values) >= 4:
                            status = values[3]
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
                            # Reattach unconditionally to show all items again
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
            # Mevcut okunabilir YouTube servisini kullan (API anahtarı yoksa OAuth'a düş)
            service = self.get_youtube_service_for_read()
            if service is None:
                return None

            # Playlist detaylarını al
            playlist_request = service.playlists().list(
                part='snippet,contentDetails',
                id=playlist_id
            )
            playlist_response = playlist_request.execute(num_retries=1)
            
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
        """Video thumbnail'ini yükle - Akıllı retry sistemi ile"""
        try:
            if video_id in self.thumbnail_cache:
                return self.thumbnail_cache[video_id]
            
            # Multiple URL endpoints to try
            thumbnail_urls = [
                thumbnail_url,  # Original URL
                f"https://img.youtube.com/vi/{video_id}/default.jpg",  # Alternative 1
                f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",  # Alternative 2
                f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",  # Alternative 3
                f"https://i.ytimg.com/vi/{video_id}/default.jpg",  # Alternative 4
            ]
            
            # Try each URL with different configurations
            for i, url in enumerate(thumbnail_urls):
                try:
                    # Different headers for each attempt
                    headers_options = [
                        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                        {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1)'},
                        {'User-Agent': 'curl/7.68.0'},
                        {}  # No headers
                    ]
                    
                    headers = headers_options[min(i, len(headers_options)-1)]
                    
                    # Try with different SSL settings
                    ssl_configs = [
                        {'verify': False, 'timeout': 10},
                        {'verify': False, 'timeout': 5},
                        {'timeout': 3}  # No SSL verification specified
                    ]
                    
                    config = ssl_configs[min(i, len(ssl_configs)-1)]
                    
                    print(f"Trying thumbnail URL {i+1}: {url[:50]}...")
                    response = requests.get(url, headers=headers, **config)
                    
                    if response.status_code == 200 and len(response.content) > 1000:  # Ensure it's a real image
                        # PIL ile resmi yükle ve daha büyük boyuta yeniden boyutlandır (160x90)
                        image = Image.open(io.BytesIO(response.content))
                        image = image.resize((160, 90), Image.Resampling.LANCZOS)
                        
                        # Tkinter uyumlu hale getir
                        photo = ImageTk.PhotoImage(image)
                        
                        # Önbelleğe al - referansı korumak için
                        self.thumbnail_cache[video_id] = photo
                        self.thumbnail_refs.append(photo)  # Referansı koru
                        print(f"✅ Thumbnail loaded successfully for {video_id}")
                        return photo
                
                except Exception as url_error:
                    print(f"❌ URL {i+1} failed: {str(url_error)[:100]}")
                    continue
            
            print(f"⚠️ All thumbnail URLs failed for {video_id}")
            return None
            
        except Exception as e:
            print(f"💥 Thumbnail loading crashed for {video_id}: {e}")
            return None
    
    def extract_playlist_id(self, playlist_url):
        """Playlist URL'sinden ID'yi çıkar"""
        if 'list=' in playlist_url:
            return playlist_url.split('list=')[1].split('&')[0]
        else:
            return playlist_url
    
    def is_valid_playlist_url(self, url: str) -> bool:
        """Girilen metnin bir playlist URL'si olduğuna dair basit doğrulama"""
        if not url:
            return False
        # En yaygın biçimler ?list= veya /playlist?list=
        if 'list=' in url:
            return True
        # Sadece ID yapıştırılmış olabilir (PL, LL, UU, OL ile başlayabilir ve uzunluğu > 10)
        pid = url.strip()
        return pid.startswith(('PL', 'LL', 'UU', 'OL')) and len(pid) > 10

    def get_youtube_service_for_read(self):
        """Okuma işlemleri için kullanılacak YouTube servisini döndür.
        Önce API anahtarlı istemci, yoksa OAuth ile kimliği doğrulanmış istemci."""
        try:
            if hasattr(self, 'youtube') and self.youtube:
                return self.youtube
        except Exception:
            pass
        if self.is_authenticated and self.authenticated_youtube is not None:
            return self.authenticated_youtube
        return None

    def get_videos(self):
        """Playlist'ten videoları getir"""
        if self.is_processing:
            return
            
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter playlist URL!")
            return

        # Playlist URL doğrulaması (tek video linkine basılınca sessiz kalmasın)
        if not self.is_valid_playlist_url(url):
            messagebox.showwarning(
                "Invalid URL",
                "Lütfen bir playlist bağlantısı girin (URL '?list=' içermeli) veya geçerli bir playlist ID yapıştırın."
            )
            self.update_status("❌ Geçersiz playlist URL", color=self.colors['accent_red'])
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
        if hasattr(self, 'remove_from_list_btn'):
            self.remove_from_list_btn.config(state='disabled')
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
            
            # Okuma servisini belirle (API anahtarı yoksa OAuth'a düş)
            service = self.get_youtube_service_for_read()
            if service is None:
                self.root.after(0, lambda: self.status_label.config(text="❌ API anahtarı yok ve giriş yapılmamış"))
                self.root.after(0, lambda: messagebox.showerror(
                    "YouTube API not configured",
                    "Playlist videolarını almak için ya .env dosyanıza YOUTUBE_API_KEY ekleyin ya da önce 'Login' ile giriş yapın."
                ))
                return
            
            # Playlist ID'yi çıkar
            playlist_id = self.extract_playlist_id(url)
            
            # Playlist bilgilerini sol tarafta asenkron güncelle
            try:
                thread = threading.Thread(target=self._update_playlist_info_thread, args=(playlist_id,))
                thread.daemon = True
                thread.start()
            except Exception:
                pass
            
            # Video ID'lerini al
            import time as _t
            step_t0 = _t.perf_counter()
            self.root.after(0, lambda: self.status_label.config(text="📋 Getting video list..."))
            video_ids = self.get_video_ids_from_playlist(playlist_id, max_videos, service)
            step_t1 = _t.perf_counter()
            print(f"[Perf] playlistItems.list fetched {len(video_ids)} IDs in {step_t1 - step_t0:.2f}s")
            
            if not video_ids:
                self.root.after(0, lambda: messagebox.showerror("Error", "No videos found in playlist or playlist is private!"))
                return
            
            self.root.after(0, lambda: self.status_label.config(text=f"📥 {len(video_ids)} videos found, getting details..."))
            
            # Video detaylarını al
            step_t2 = _t.perf_counter()
            self.video_details = self.get_video_details(video_ids, service)
            step_t3 = _t.perf_counter()
            print(f"[Perf] videos.list fetched details in {step_t3 - step_t2:.2f}s")
            
            if not self.video_details:
                self.root.after(0, lambda: messagebox.showerror("Error", "Could not get video details!"))
                return
            
            # GUI'yi güncelle
            self.root.after(0, self._update_video_list)
            
            # Video yükleme işlemi tamamlandı - is_processing'i false yap
            self.is_processing = False
            self.progress.stop()
            self.get_videos_btn.config(state='normal')
            
            # Videos successfully loaded, inform user; 4K check will start after list is rendered
            if hasattr(self, 'video_details') and self.video_details:
                self.root.after(0, lambda: self.status_label.config(text="✨ Videos loaded! Preparing 4K check..."))
            
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

            # Kısa başlık
            short_title = video['title'][:50] + "..." if len(video['title']) > 50 else video['title']

            # Item'ı ekle: #0 sütunu (tree) text boş; image daha sonra yüklenecek
            item_id = self.video_tree.insert(
                '',
                'end',
                text=' ',
                values=(
                    i,             # No
                    short_title,   # Title
                    quality,       # Quality
                    "Waiting..."   # Status
                ),
                tags=(video['id'], 'normal')
            )

            # Store item ID for filter management
            self._all_tree_items.append(item_id)

            # Thumbnail'i thread'de yükle - Akıllı retry sistemi ile
            thread = threading.Thread(target=self._load_thumbnail_async, args=(item_id, video['id'], video['thumbnail_url']))
            thread.daemon = True
            thread.start()

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

        # Inform and start 4K scanning now that the list is rendered
        self.status_label.config(text=f"📺 {len(self.video_details)} videos listed. Starting sequential 4K check...")
        self.root.after(0, self.check_4k_videos)

    def _load_thumbnail_async(self, item_id, video_id, thumbnail_url):
        """Thumbnail'i asenkron olarak yükle - Akıllı retry sistemi"""
        try:
            thumbnail = self.load_thumbnail(video_id, thumbnail_url)
            if thumbnail:
                # Ana thread'de GUI'yi güncelle
                self.root.after(0, lambda: self._update_thumbnail(item_id, thumbnail))
            else:
                # Hata durumunda kaliteye göre emoji göster
                self.root.after(0, lambda: self._update_thumbnail_text(item_id, "🎬"))
        except Exception as e:
            print(f"Async thumbnail loading failed for {video_id}: {e}")
            self.root.after(0, lambda: self._update_thumbnail_text(item_id, "❌"))
    
    def _update_thumbnail(self, item_id, photo):
        """Thumbnail'i TreeView'da güncelle"""
        try:
            # TreeView item'ını güncelle
            if self.video_tree.exists(item_id):
                # Thumbnail'i #0 sütununda image olarak ayarla
                self.video_tree.item(item_id, image=photo)
        except Exception as e:
            print(f"Thumbnail could not be updated: {e}")
    
    def _update_thumbnail_text(self, item_id, text):
        """Thumbnail yerine metin göster"""
        try:
            if self.video_tree.exists(item_id):
                # #0 sütununda text göster
                self.video_tree.item(item_id, text=text)
        except Exception as e:
            print(f"Thumbnail text could not be updated: {e}")
    
    def get_video_ids_from_playlist(self, playlist_id, max_videos=None, service=None):
        """Playlist'ten video ID'lerini al"""
        video_ids = []
        next_page_token = None
        svc = service or getattr(self, 'youtube', None)
        if svc is None:
            raise RuntimeError("YouTube service is not initialized")
        
        while True:
            pl_request = svc.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            # Keep retries low; our client http has a timeout already
            pl_response = pl_request.execute(num_retries=2)
            
            for item in pl_response['items']:
                video_ids.append(item['contentDetails']['videoId'])
                if max_videos and len(video_ids) >= max_videos:
                    return video_ids[:max_videos]
            
            next_page_token = pl_response.get('nextPageToken')
            if not next_page_token:
                break
        
        return video_ids
    
    def get_video_details(self, video_ids, service=None):
        """Video detaylarını al"""
        video_details = []
        svc = service or getattr(self, 'youtube', None)
        if svc is None:
            raise RuntimeError("YouTube service is not initialized")
        
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            request = svc.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(batch_ids)
            )
            response = request.execute(num_retries=2)
            
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
        """4K kontrol işlemini thread'de yap - Sıra sıra (sequential) ve görünür ilerleme ile"""
        self.is_processing = True
        self.stop_requested = False
        # UI updates must be done on the main thread
        self.root.after(0, self.progress.start)
        self.root.after(0, lambda: self.stop_btn.config(state='normal'))
        self.root.after(0, lambda: self.copy_btn.config(state='disabled'))
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

            total = len(hd_videos)
            completed_count = 0
            failed_count = 0
            self.root.after(0, lambda: self.status_label.config(text=f"🚶‍♂️ Sequential 4K scanning: 0/{total}"))

            for video in hd_videos:
                if self.stop_requested:
                    break

                # Videoyu kontrol etmeden önce durumunu güncelle
                self.root.after(0, lambda v=video: self._update_video_status(v, "🔎 Checking..."))

                try:
                    is_4k = self.check_4k_availability(video['url'])
                    if is_4k:
                        self.found_4k_videos.append(video['url'])
                        self.root.after(0, lambda v=video: self._update_video_status(v, "✅ 4K Available!"))
                    else:
                        self.root.after(0, lambda v=video: self._update_video_status(v, "❌ No 4K"))
                except Exception as e:
                    print(f"Error checking video {video['id']}: {e}")
                    failed_count += 1
                    self.root.after(0, lambda v=video: self._update_video_status(v, "⚠️ Check Failed"))

                completed_count += 1
                progress_text = f"🔍 Scanning: {completed_count}/{total} ({len(self.found_4k_videos)} 4K found)"
                if failed_count > 0:
                    progress_text += f" [{failed_count} failed]"
                self.root.after(0, lambda text=progress_text: self.status_label.config(text=text))

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
                    self.root.after(500, self.apply_4k_filter)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"4K check error: {str(e)}"))
        finally:
            self.is_processing = False
            self.stop_requested = False
            # Ensure UI teardown happens on the main thread
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.stop_btn.config(state='disabled'))
    
    def _update_video_status(self, video, status):
        """Video durumunu güncelle"""
        for item in getattr(self, '_all_tree_items', self.video_tree.get_children()):
            if not self.video_tree.exists(item):
                continue
                
            values = self.video_tree.item(item, 'values')
            if len(values) >= 4 and video['title'][:50] in values[1]:  # Title sütunu (index 1 now)
                new_values = list(values)
                new_values[3] = status  # Status sütunu (index 3 now)
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
                    if len(values) >= 4:
                        item_status = values[3]
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
                if len(values) >= 4:  # Status column exists
                    status = values[3]  # Status column
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
                messagebox.showinfo("Result", f"🎉 {found_count} 4K videos found!\n\n✨ 4K Filter is active - showing only 4K videos.\nSelect rows to copy URLs or remove.")
            else:
                messagebox.showinfo("Result", f"🎉 {found_count} 4K videos found!\n\nSelect rows to copy URLs or remove.")
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
        if hasattr(self, 'remove_from_list_btn'):
            self.remove_from_list_btn.config(state='disabled')
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
