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
        self.thumbnail_manager = ThumbnailManager()
        self.youtube_service = YouTubeAPIService()
        self.video_checker = Video4KChecker()
        
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
        
        # Create widgets using factory
        self.auth_widgets = self.widget_factory.create_auth_widget(main_frame)
        self.playlist_widgets = self.widget_factory.create_playlist_input_widget(main_frame)
        self.filter_widgets = self.widget_factory.create_filter_controls(main_frame)
        self.main_button_widgets = self.widget_factory.create_main_button_group(main_frame)
        self.action_widgets = self.widget_factory.create_action_button_group(main_frame)
        
        # Create video tree
        self.video_tree = self.tree_manager.create_video_tree(main_frame)
        
        # Create status bar
        self.status_widgets = self.widget_factory.create_status_bar(main_frame)
        
        # Register UI elements with manager
        self.register_ui_elements()
    
    def register_ui_elements(self):
        """Register UI elements with UI manager for controlled access"""
        # Auth widgets
        self.ui_manager.register_element('auth_status_label', self.auth_widgets['status_label'])
        self.ui_manager.register_element('login_button', self.auth_widgets['login_button'])
        self.ui_manager.register_element('logout_button', self.auth_widgets['logout_button'])
        
        # Playlist widgets
        self.ui_manager.register_element('url_entry', self.playlist_widgets['url_entry'])
        self.ui_manager.register_element('paste_button', self.playlist_widgets['paste_button'])
        self.ui_manager.register_element('load_button', self.playlist_widgets['load_button'])
        self.ui_manager.register_element('info_label', self.playlist_widgets['info_label'])
        # Auto-check toggle
        if 'auto_check_4k' in self.playlist_widgets:
            self.ui_manager.register_element('auto_check_4k', self.playlist_widgets['auto_check_4k'])
        if 'auto_check_4k_check' in self.playlist_widgets:
            self.ui_manager.register_element('auto_check_4k_check', self.playlist_widgets['auto_check_4k_check'])
        
        # Filter widgets
        self.ui_manager.register_element('max_entry', self.filter_widgets['max_entry'])
        self.ui_manager.register_element('max_slider', self.filter_widgets['max_slider'])
        self.ui_manager.register_element('all_videos_var', self.filter_widgets['all_videos_var'])
        self.ui_manager.register_element('filter_4k_var', self.filter_widgets['filter_4k_var'])
        
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
        self.ui_manager.register_element('copy_button', self.action_widgets['copy_button'])
        self.ui_manager.register_element('remove_list_button', self.action_widgets['remove_list_button'])
        self.ui_manager.register_element('remove_youtube_button', self.action_widgets['remove_youtube_button'])
        
        # Status bar
        self.ui_manager.register_element('status_label', self.status_widgets['status_label'])
        self.ui_manager.register_element('count_label', self.status_widgets['count_label'])
        
        # Tree and services
        self.ui_manager.register_element('video_tree', self.video_tree)
        self.ui_manager.register_element('theme', self.theme_config)
    
    def bind_events(self):
        """Bind UI events to handlers"""
        # Auth events
        self.auth_widgets['login_button'].configure(
            command=self.youtube_service.start_oauth_flow
        )
        self.auth_widgets['logout_button'].configure(
            command=self.youtube_service.logout_oauth
        )
        
        # Playlist events
        self.playlist_widgets['url_entry'].bind('<KeyRelease>', self.event_handlers.on_url_change)
        self.playlist_widgets['paste_button'].configure(command=self.event_handlers.paste_url)
        self.playlist_widgets['load_button'].configure(command=self.event_handlers.load_playlist)
        
        # Filter events
        self.filter_widgets['max_entry'].bind('<KeyRelease>', self.event_handlers.on_entry_change)
        self.filter_widgets['max_slider'].configure(command=self.event_handlers.on_slider_change)
        self.filter_widgets['filter_4k_check'].configure(command=self.event_handlers.on_filter_toggle)
        
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
        self.action_widgets['copy_button'].configure(
            command=lambda: self.video_operations.copy_checked_urls(self.video_tree)
        )
    
    def setup_authentication(self):
        """Setup YouTube authentication with better error handling"""
        try:
            # Setup API key
            api_key = os.getenv('YOUTUBE_API_KEY', '')
            if api_key:
                self.config_manager.set('youtube.api_key', api_key)
                print(f"✅ API key loaded: {api_key[:10]}...")
            else:
                print("⚠️ No YOUTUBE_API_KEY found in environment")
            
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
            
            # Initialize API with retry
            api_ready = False
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    if self.youtube_service.setup_youtube_api():
                        api_ready = True
                        # Wire the playlist service to use the API-key YouTube client
                        try:
                            self.playlist_service.youtube_service = self.youtube_service.youtube
                        except Exception:
                            pass
                        break
                    else:
                        print(f"⚠️ API setup attempt {attempt + 1} returned False")
                        
                except Exception as e:
                    print(f"❌ API setup attempt {attempt + 1} failed: {e}")
                    
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying API setup in 2 seconds...")
                    import time
                    time.sleep(2)
            
            if not api_ready:
                self.ui_manager.update_status("⚠️ YouTube API setup failed - some features may not work")
                print("⚠️ Continuing without full API access")
            
            # Check existing authentication
            try:
                self.youtube_service.check_existing_authentication()
            except Exception as e:
                print(f"⚠️ Authentication check warning: {e}")
            
            # Update auth status
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
