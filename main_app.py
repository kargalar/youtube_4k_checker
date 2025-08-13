"""
Main modular application for YouTube 4K Checker
Clean, organized, and maintainable version
"""
import tkinter as tk
from tkinter import ttk
import os
from dotenv import load_dotenv

# Import modular components
from core import (
    ThemeConfig, YouTubeAPIService, Video4KChecker,
    ThumbnailManager, UIManager, ConfigManager
)
from ui import WidgetFactory, TreeManager
from services import PlaylistService, VideoOperations
from services.event_handlers import EventHandlers
from widgets.video_actions_widget import VideoActionsWidget

class YouTube4KCheckerApp:
    """
    Main application class - now clean and modular!
    Orchestrates all the services and components
    """
    
    def __init__(self, root):
        self.root = root
        self.setup_window()
        
        # Load environment variables
        self.load_env_config()
        
        # Initialize core services
        self.config_manager = ConfigManager()
        self.theme_config = ThemeConfig()
        self.ui_manager = UIManager(root)
        # Configure thumbnails from config
        thumb_cfg = {}
        try:
            thumb_cfg = self.config_manager.get('thumbnails', {}) or {}
        except Exception:
            pass
        self.thumbnail_manager = ThumbnailManager(
            cache_dir=thumb_cfg.get('cache_dir', 'thumbnails'),
            max_cache_size=thumb_cfg.get('max_cache_size', 100),
            use_disk_cache=thumb_cfg.get('use_disk_cache', True)
        )
        self.youtube_service = YouTubeAPIService()
        self.video_checker = Video4KChecker()
        # Apply API key from config (UI-managed)
        try:
            self.youtube_service.api_key = self.config_manager.get('youtube.api_key', '')
        except Exception:
            pass
        
        # Initialize UI services
        self.widget_factory = WidgetFactory(self.theme_config)
        self.tree_manager = TreeManager(self.ui_manager, self.thumbnail_manager, self.theme_config)
        
        # Initialize business services
        self.playlist_service = PlaylistService(self.youtube_service.youtube)
        self.video_operations = VideoOperations(self.ui_manager, self.playlist_service, self.theme_config)
        # Wire references for cross-service helpers
        try:
            self.tree_manager.video_operations = self.video_operations
            self.video_operations.tree_manager = self.tree_manager
            # Expose tree_manager via UIManager for lookup helpers
            self.ui_manager.register_element('tree_manager_instance', self.tree_manager)
        except Exception:
            pass
        
        # Initialize event handlers
        self.event_handlers = EventHandlers(
            self.ui_manager, self.playlist_service, self.youtube_service,
            self.video_checker, self.tree_manager
        )
        
        # Setup UI and theme
        self.setup_theme()
        self.create_ui()
        self.bind_events()
        
        # Initialize authentication
        self.setup_authentication()
    
    def setup_window(self):
        """Configure main window"""
        self.root.title("YouTube 4K Video Checker - Modular Edition")
        self.root.geometry("1200x900")
        self.root.minsize(800, 600)
    
    def load_env_config(self):
        """Load environment configuration"""
        try:
            load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
            load_dotenv()  # Fallback
        except Exception as e:
            print(f"Environment config load warning: {e}")
    
    def setup_theme(self):
        """Apply theme configuration"""
        self.root.configure(bg=self.theme_config.COLORS['bg_primary'])
        self.theme_config.configure_ttk_styles(self.root)
    
    def create_ui(self):
        """Create the user interface using modular widgets"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.theme_config.COLORS['bg_primary'])
        main_frame.pack(fill='both', expand=True)

        # Paned layout: left controls, right video list
        paned = tk.PanedWindow(
            main_frame,
            orient='horizontal',
            sashwidth=6,
            bg=self.theme_config.COLORS['bg_primary'],
            bd=0,
            relief='flat'
        )
        paned.pack(fill='both', expand=True)

        left_pane = tk.Frame(paned, bg=self.theme_config.COLORS['bg_primary'], width=380)
        right_pane = tk.Frame(paned, bg=self.theme_config.COLORS['bg_primary'])
        paned.add(left_pane, minsize=320)
        paned.add(right_pane)

        # Create widgets in left pane
        self.auth_widgets = self.widget_factory.create_auth_widget(left_pane)
        self.playlist_widgets = self.widget_factory.create_playlist_input_widget(left_pane)
        self.filter_widgets = self.widget_factory.create_filter_controls(left_pane)
        self.main_button_widgets = self.widget_factory.create_main_button_group(left_pane)
        self.action_widgets = self.widget_factory.create_action_button_group(left_pane)

        # Create video tree in right pane
        self.video_tree = self.tree_manager.create_video_tree(right_pane)

        # Create status bar in left pane (under controls)
        self.status_widgets = self.widget_factory.create_status_bar(left_pane)

        # Optional: set initial sash position
        try:
            self.root.update_idletasks()
            paned.sash_place(0, 380, 1)
        except Exception:
            pass
        
        # Register UI elements with manager
        self.register_ui_elements()
    
    def register_ui_elements(self):
        """Register UI elements with UI manager for controlled access"""
        # Auth widgets
        self.ui_manager.register_element('auth_status_label', self.auth_widgets['status_label'])
        self.ui_manager.register_element('api_key_entry', self.auth_widgets['api_key_entry'])
        self.ui_manager.register_element('save_api_key_button', self.auth_widgets['save_api_key_button'])
        self.ui_manager.register_element('login_button', self.auth_widgets['login_button'])
        self.ui_manager.register_element('logout_button', self.auth_widgets['logout_button'])

        # Playlist widgets
        self.ui_manager.register_element('url_entry', self.playlist_widgets['url_entry'])
        self.ui_manager.register_element('paste_button', self.playlist_widgets['paste_button'])
        self.ui_manager.register_element('info_label', self.playlist_widgets['info_label'])

        # Filter widgets
        self.ui_manager.register_element('max_entry', self.filter_widgets['max_entry'])
        self.ui_manager.register_element('max_slider', self.filter_widgets['max_slider'])
        self.ui_manager.register_element('filter_4k_var', self.filter_widgets['filter_4k_var'])
        self.ui_manager.register_element('filter_copied_var', self.filter_widgets.get('filter_copied_var'))
        # Also expose the checkbox widgets if present
        if 'filter_4k_check' in self.filter_widgets:
            self.ui_manager.register_element('filter_4k_check', self.filter_widgets['filter_4k_check'])
        if 'filter_copied_check' in self.filter_widgets:
            self.ui_manager.register_element('filter_copied_check', self.filter_widgets['filter_copied_check'])

        # Main buttons
        self.ui_manager.register_element('check_button', self.main_button_widgets['check_button'])
        self.ui_manager.register_element('stop_button', self.main_button_widgets['stop_button'])
        self.ui_manager.register_element('progress_frame', self.main_button_widgets['progress_frame'])
        self.ui_manager.register_element('progress_label', self.main_button_widgets['progress_label'])
        self.ui_manager.register_element('progress_bar', self.main_button_widgets['progress_bar'])

        # Action buttons
        self.ui_manager.register_element('check_all_button', self.action_widgets['check_all_button'])
        self.ui_manager.register_element('uncheck_all_button', self.action_widgets['uncheck_all_button'])
        self.ui_manager.register_element('check_4k_button', self.action_widgets['check_4k_button'])
        self.ui_manager.register_element('select_copied_button', self.action_widgets['select_copied_button'])
        self.ui_manager.register_element('copy_button', self.action_widgets['copy_button'])
        self.ui_manager.register_element('remove_list_button', self.action_widgets['remove_list_button'])
        self.ui_manager.register_element('remove_youtube_button', self.action_widgets['remove_youtube_button'])

        # Status bar
        self.ui_manager.register_element('status_label', self.status_widgets['status_label'])
        # Copy icon inside status bar for error messages
        if 'copy_button' in self.status_widgets:
            self.ui_manager.register_element('status_copy_button', self.status_widgets['copy_button'])
        self.ui_manager.register_element('count_label', self.status_widgets['count_label'])

        # Tree and services
        self.ui_manager.register_element('video_tree', self.video_tree)
        self.ui_manager.register_element('theme', self.theme_config)
        # Expose config manager for components that read/write persistent settings
        self.ui_manager.register_element('config_manager', self.config_manager)
        # Expose youtube service for checking OAuth vs API key where needed
        self.ui_manager.register_element('youtube_service', self.youtube_service)
    
    def bind_events(self):
        """Bind UI events to handlers"""
        # Auth events
        # Prefill API key
        try:
            key = self.config_manager.get('youtube.api_key', '')
            if key:
                self.auth_widgets['api_key_entry'].delete(0, tk.END)
                self.auth_widgets['api_key_entry'].insert(0, key)
        except Exception:
            pass

        def _save_api_key():
            try:
                key = self.auth_widgets['api_key_entry'].get().strip()
                self.config_manager.set('youtube.api_key', key)
                self.config_manager.save_config()
                # Re-init API with new key
                self.youtube_service.api_key = key
                if self.youtube_service.setup_youtube_api():
                    self.playlist_service.youtube_service = self.youtube_service.youtube
                    self.ui_manager.update_status("✅ API key saved and initialized")
                else:
                    self.ui_manager.update_status("⚠️ API key saved, but initialization failed")
            except Exception as e:
                print(e)
                self.ui_manager.update_status("❌ Failed to save API key")

        self.auth_widgets['save_api_key_button'].configure(command=_save_api_key)

        def _login():
            import threading
            def _worker():
                # Show initial status
                try:
                    self.ui_manager.update_status("🔐 Starting Google login...")
                except Exception:
                    pass
                self.youtube_service.start_oauth_flow(callback=self.ui_manager.update_status)
                # After login, refresh auth status on UI thread
                try:
                    self.ui_manager.safe_update(self.update_auth_status)
                except Exception:
                    pass
            threading.Thread(target=_worker, daemon=True).start()
        self.auth_widgets['login_button'].configure(command=_login)
        self.auth_widgets['logout_button'].configure(
            command=self.youtube_service.logout_oauth
        )
        
        # Playlist events
        self.playlist_widgets['url_entry'].bind('<KeyRelease>', self.event_handlers.on_url_change)
        self.playlist_widgets['paste_button'].configure(command=self.event_handlers.paste_url)
        
        # Filter events
        self.filter_widgets['max_entry'].bind('<KeyRelease>', self.event_handlers.on_entry_change)
        self.filter_widgets['max_slider'].configure(command=self.event_handlers.on_slider_change)
        self.filter_widgets['filter_4k_check'].configure(command=self.event_handlers.on_filter_toggle)
        # Copied filter
        if 'filter_copied_check' in self.filter_widgets:
            self.filter_widgets['filter_copied_check'].configure(command=self.event_handlers.on_filter_toggle)
        
        # Main control events
        self.main_button_widgets['check_button'].configure(command=self.event_handlers.check_4k_quality)
        self.main_button_widgets['stop_button'].configure(command=self.event_handlers.stop_processing)
        
        # Action button events
        self.action_widgets['check_all_button'].configure(
            command=lambda: self.tree_manager.check_all_videos(self.video_tree)
        )
        self.action_widgets['uncheck_all_button'].configure(
            command=lambda: self.tree_manager.uncheck_all_videos(self.video_tree)
        )
        self.action_widgets['check_4k_button'].configure(
            command=lambda: self.tree_manager.check_4k_only(self.video_tree)
        )
        self.action_widgets['select_copied_button'].configure(
            command=lambda: self.tree_manager.select_previously_copied(self.video_tree)
        )
        self.action_widgets['copy_button'].configure(
            command=lambda: self.video_operations.copy_checked_urls(self.video_tree)
        )
        # Selection-based remove actions
        self.action_widgets['remove_list_button'].configure(
            command=lambda: self.tree_manager.remove_selected_items(self.video_tree)
        )
        self.action_widgets['remove_youtube_button'].configure(
            command=lambda: self.video_operations.remove_selected_from_youtube(self.video_tree)
        )
    
    def setup_authentication(self):
        """Setup YouTube authentication with better error handling"""
        try:
            # Setup API key from config (required)
            api_key = self.config_manager.get('youtube.api_key', '')
            self.youtube_service.api_key = api_key or ''
            if not api_key:
                self.ui_manager.update_status("⚠️ Enter your YouTube API key to enable loading videos.")
            else:
                if self.youtube_service.setup_youtube_api():
                    try:
                        self.playlist_service.youtube_service = self.youtube_service.youtube
                    except Exception:
                        pass
            
            # Setup OAuth credentials
            self.youtube_service.client_secrets_file = os.getenv(
                'CLIENT_SECRETS_FILE',
                os.path.join(os.path.dirname(__file__), 'client_secret.json')
            )
            self.youtube_service.token_file = os.getenv(
                'TOKEN_FILE', 
                os.path.join(os.path.dirname(__file__), 'token.pickle')
            )
            
            print(f"🔐 Client secrets file: {self.youtube_service.client_secrets_file}")
            print(f"🎟️ Token file: {self.youtube_service.token_file}")
            
            # API ready is based on presence of key and setup attempt above
            api_ready = bool(api_key and self.youtube_service.youtube)
            if not api_ready:
                print("⚠️ API not initialized yet. Waiting for API key from UI.")
            
            # Check existing authentication
            try:
                self.youtube_service.check_existing_authentication()
            except Exception as e:
                print(f"⚠️ Authentication check warning: {e}")
            
            # Update auth status (OAuth is optional and only needed for playlist removal)
            try:
                self.update_auth_status()
            except Exception as e:
                print(f"⚠️ Auth status update warning: {e}")
                
        except Exception as e:
            print(f"❌ Authentication setup error: {e}")
            self.ui_manager.update_status(f"⚠️ Authentication setup error: {str(e)}")
            # Continue anyway - app can still work with limited functionality
    
    def update_auth_status(self):
        """Update authentication status display"""
        try:
            status_label = self.auth_widgets['status_label']
            login_button = self.auth_widgets['login_button'] 
            logout_button = self.auth_widgets['logout_button']
            
            if self.youtube_service.is_authenticated:
                status_label.config(
                    text="✅ Authenticated with Google",
                    fg=self.theme_config.COLORS['accent_green']
                )
                login_button.config(state='disabled')
                logout_button.config(state='normal')
                
                # Update playlist service
                self.playlist_service.youtube_service = self.youtube_service.authenticated_youtube
                
            else:
                status_label.config(
                    text="❌ Not authenticated",
                    fg=self.theme_config.COLORS['accent_orange']
                )
                login_button.config(state='normal')
                logout_button.config(state='disabled')
                
        except Exception as e:
            print(f"Error updating auth status: {e}")
    
    def run(self):
        """Start the application"""
        try:
            self.ui_manager.update_status("🚀 YouTube 4K Checker ready!")
            self.root.mainloop()
            
        except Exception as e:
            print(f"Application runtime error: {e}")
        finally:
            # Cleanup
            try:
                self.thumbnail_manager.clear_cache()
            except:
                pass

def main():
    """Application entry point"""
    root = tk.Tk()
    app = YouTube4KCheckerApp(root)
    app.run()

if __name__ == "__main__":
    main()
