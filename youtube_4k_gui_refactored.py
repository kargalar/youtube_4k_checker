import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
import os
import pickle
import requests
import io
from PIL import Image, ImageTk

# Google API imports
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

# Import our custom widgets
from widgets.auth_widget import AuthenticationWidget
from widgets.playlist_input_widget import PlaylistInputWidget
from widgets.button_bar_widget import ModernButtonBar
from widgets.video_list_widget import VideoListWidget
from widgets.status_bar_widget import StatusBarWidget

class YouTube4KCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 4K Video Checker")
        self.root.geometry("1200x900")
        
        # Modern dark theme colors with vibrant accents
        self.colors = {
            'bg_primary': '#0f0f23',      # Deep dark blue
            'bg_secondary': '#1a1a2e',    # Dark blue-gray
            'bg_tertiary': '#16213e',     # Medium blue
            'bg_hover': '#0e3460',        # Hover blue
            'text_primary': '#eee6ff',    # Light purple-white
            'text_secondary': '#a8a8a8',  # Medium gray
            'text_accent': '#00d4ff',     # Bright cyan
            'accent_blue': '#0078d4',     # Microsoft blue
            'accent_green': '#00ff87',    # Neon green
            'accent_orange': '#ff6b35',   # Vibrant orange
            'accent_red': '#ff2d55',      # Bright red
            'accent_purple': '#8b5cf6',   # Modern purple
            'accent_pink': '#ff3b82',     # Hot pink
            'accent_yellow': '#ffd60a',   # Golden yellow
            'accent_cyan': '#00d4ff',     # Electric cyan
            'border': '#404040',
            'gradient_start': '#667eea',  # Blue gradient start
            'gradient_end': '#764ba2'     # Purple gradient end
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure ttk styles for dark theme
        self.setup_dark_theme()
        
        # Initialize API and OAuth
        self.init_youtube_api()
        
        # Initialize widgets
        self.init_widgets()
        
        # Create the UI
        self.create_ui()
    
    def init_youtube_api(self):
        """Initialize YouTube API and OAuth"""
        # API Key
        self.API_KEY = 'AIzaSyA3hWhKJmy2_0A7cfbB46va3XWsq-SeV2E'
        self.youtube = build('youtube', 'v3', developerKey=self.API_KEY)
        
        # OAuth2 variables
        self.authenticated_youtube = None
        self.credentials = None
        self.flow = None
        self.is_authenticated = False
        self.oauth_scopes = ['https://www.googleapis.com/auth/youtube']
        self.oauth_redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        # OAuth2 files
        self.client_secrets_file = os.path.join(os.path.dirname(__file__), 'client_secret.json')
        self.token_file = os.path.join(os.path.dirname(__file__), 'token.pickle')
        
        # Check existing authentication
        self.check_existing_authentication()
        
        # Processing state
        self.is_processing = False
        self.stop_requested = False
        self.found_4k_videos = []
        self.thumbnail_cache = {}
        self.thumbnail_refs = []
    
    def init_widgets(self):
        """Initialize all custom widgets"""
        # This will be called after create_ui
        pass
    
    def create_ui(self):
        """Create the main UI using widgets"""
        # Main container
        main_container = ttk.Frame(self.root, style='Dark.TFrame')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_container,
            text="🎬✨ YouTube 4K Video Checker ✨🎬",
            font=('Segoe UI', 20, 'bold'),
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_cyan']
        )
        title_label.pack(pady=(0, 10))
        
        # Authentication Widget
        self.auth_widget = AuthenticationWidget(
            main_container,
            self.colors,
            self.start_oauth_flow,
            self.logout_oauth
        )
        self.auth_widget.pack(pady=(0, 20), fill='x')
        self.auth_widget.update_status(self.is_authenticated)
        
        # Playlist Input Widget
        self.playlist_widget = PlaylistInputWidget(
            main_container,
            self.colors,
            self.on_url_change,
            self.paste_url
        )
        self.playlist_widget.pack(pady=(0, 15), fill='x')
        
        # Video limit controls (keep existing implementation)
        self.create_limit_controls(main_container)
        
        # Button Bar Widget
        button_callbacks = {
            'get_videos': self.get_videos,
            'check_4k': self.check_4k_videos,
            'stop': self.stop_processing,
            'copy': self.copy_checked_urls,
            'check_all': self.check_all_videos,
            'uncheck_all': self.uncheck_all_videos,
            'check_4k_only': self.check_4k_only,
            'remove_youtube': self.remove_checked_from_youtube,
            'clear': self.clear_all
        }
        
        self.button_bar = ModernButtonBar(
            main_container,
            self.colors,
            button_callbacks
        )
        self.button_bar.pack(pady=(0, 15))
        
        # Status Bar Widget
        self.status_bar = StatusBarWidget(main_container, self.colors)
        self.status_bar.pack(fill='x', pady=(0, 15))
        
        # Video List Widget
        self.video_list = VideoListWidget(
            main_container,
            self.colors,
            self.on_tree_click,
            self.show_context_menu
        )
        self.video_list.pack(fill='both', expand=True)
        
        # Create context menu
        self.create_context_menu()
    
    def create_limit_controls(self, parent):
        """Create video limit controls (keeping existing implementation)"""
        limit_frame = ttk.Frame(parent, style='Dark.TFrame')
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
        self.limit_entry.bind('<KeyRelease>', self.on_entry_change)
        
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
    
    # Widget callback methods
    def start_oauth_flow(self):
        """Start OAuth2 flow"""
        # Implementation stays the same
        pass
    
    def logout_oauth(self):
        """Logout OAuth2"""
        # Implementation stays the same
        pass
    
    def on_url_change(self, event=None):
        """Handle URL change"""
        # Implementation stays the same
        pass
    
    def paste_url(self):
        """Paste URL from clipboard"""
        # Implementation stays the same
        pass
    
    def get_videos(self):
        """Get videos from playlist"""
        # Implementation stays the same but uses widgets
        if self.is_processing:
            return
            
        url = self.playlist_widget.get_url()
        if not url:
            messagebox.showerror("Error", "Please enter playlist URL!")
            return
        
        # Update status
        self.status_bar.set_info_message("Getting playlist videos...")
        self.status_bar.start_progress()
        
        # Disable buttons
        self.button_bar.disable_button('get_videos')
        self.button_bar.disable_button('check_4k')
        
        # Continue with existing implementation...
    
    # Keep all other existing methods but update them to use widgets
    # For example:
    
    def update_copy_button_state(self):
        """Update copy button state based on checked items"""
        has_checked = any(self.video_list.get_item_values(item)[0] == '☑️' 
                         for item in self.video_list.get_all_items())
        
        if has_checked:
            self.button_bar.enable_button('copy')
            if self.is_authenticated:
                self.button_bar.enable_button('remove_youtube')
        else:
            self.button_bar.disable_button('copy')
            self.button_bar.disable_button('remove_youtube')
    
    def clear_all(self):
        """Clear all videos"""
        self.video_list.clear()
        self.found_4k_videos = []
        self.status_bar.set_info_message("💫 Enter playlist URL and click 'Get Videos' to start! 💫")
        
        # Disable buttons
        for btn_name in ['copy', 'check_all', 'uncheck_all', 'check_4k_only', 'remove_youtube']:
            self.button_bar.disable_button(btn_name)
    
    # Include setup_dark_theme and other necessary methods from original
    def setup_dark_theme(self):
        """Configure dark theme for ttk widgets"""
        # Keep the existing implementation
        pass
    
    # ... (include all other necessary methods from the original file)

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTube4KCheckerGUI(root)
    root.mainloop()
