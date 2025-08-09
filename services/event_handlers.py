"""
Event handler service
Handles UI events and user interactions
"""
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import re

class EventHandlers:
    """Service for handling UI events and user interactions"""
    
    def __init__(self, ui_manager, playlist_service, youtube_service, video_checker, tree_manager):
        self.ui_manager = ui_manager
        self.playlist_service = playlist_service
        self.youtube_service = youtube_service
        self.video_checker = video_checker
        self.tree_manager = tree_manager
        
        self.stop_requested = False
        self.is_processing = False
    
    def on_url_change(self, event=None):
        """Handle URL entry changes"""
        try:
            url_entry = self.ui_manager.get_element('url_entry')
            info_label = self.ui_manager.get_element('info_label')
            
            if not url_entry or not info_label:
                return
            
            url = url_entry.get().strip()
            
            if not url:
                def update():
                    info_label.config(text="No playlist loaded")
                self.ui_manager.safe_update(update)
                return
            
            if self.playlist_service.is_valid_playlist_url(url):
                playlist_id = self.playlist_service.extract_playlist_id(url)
                if playlist_id:
                    def update():
                        info_label.config(text="🔄 Loading playlist info...")
                    self.ui_manager.safe_update(update)
                    
                    # Update playlist info in background
                    self.playlist_service.update_playlist_info_async(
                        playlist_id, 
                        self.on_playlist_info_updated
                    )
                else:
                    def update():
                        info_label.config(text="❌ Invalid playlist URL")
                    self.ui_manager.safe_update(update)
            else:
                def update():
                    info_label.config(text="⚠️ Not a playlist URL")
                self.ui_manager.safe_update(update)
                
        except Exception as e:
            print(f"Error in URL change handler: {e}")
    
    def on_playlist_info_updated(self, playlist_info):
        """Handle playlist info update"""
        try:
            info_label = self.ui_manager.get_element('info_label')
            
            if not info_label:
                return
            
            if playlist_info:
                text = f"📋 {playlist_info['title']} ({playlist_info['video_count']} videos)"
                def update():
                    info_label.config(text=text[:60] + ('...' if len(text) > 60 else ''))
            else:
                def update():
                    info_label.config(text="❌ Playlist not found")
            
            self.ui_manager.safe_update(update)
            
        except Exception as e:
            print(f"Error updating playlist info: {e}")
    
    def paste_url(self):
        """Paste URL from clipboard"""
        try:
            url_entry = self.ui_manager.get_element('url_entry')
            
            if url_entry:
                try:
                    clipboard_text = self.ui_manager.root.clipboard_get()
                    url_entry.delete(0, tk.END)
                    url_entry.insert(0, clipboard_text.strip())
                    
                    # Trigger URL change event
                    self.on_url_change()
                    
                    self.ui_manager.update_status("📋 URL pasted from clipboard")
                    
                except tk.TclError:
                    self.ui_manager.update_status("❌ No text in clipboard")
                    
        except Exception as e:
            print(f"Error pasting URL: {e}")
    
    def load_playlist(self):
        """Load playlist videos"""
        try:
            if self.is_processing:
                self.ui_manager.update_status("⚠️ Already processing, please wait...")
                return
            
            url_entry = self.ui_manager.get_element('url_entry')
            max_entry = self.ui_manager.get_element('max_entry')
            
            if not url_entry:
                return
            
            url = url_entry.get().strip()
            
            if not url:
                self.ui_manager.show_message_dialog(
                    "URL Required",
                    "Please enter a YouTube playlist URL.",
                    'warning'
                )
                return
            
            if not self.playlist_service.is_valid_playlist_url(url):
                self.ui_manager.show_message_dialog(
                    "Invalid URL",
                    "Please enter a valid YouTube playlist URL.",
                    'warning'
                )
                return
            
            playlist_id = self.playlist_service.extract_playlist_id(url)
            if not playlist_id:
                self.ui_manager.show_message_dialog(
                    "Invalid Playlist",
                    "Could not extract playlist ID from URL.",
                    'error'
                )
                return
            
            # Get max results
            max_results = 50
            if max_entry:
                try:
                    max_results = int(max_entry.get())
                    max_results = max(10, min(500, max_results))  # Clamp between 10-500
                except ValueError:
                    max_results = 50
            
            # Start loading in background thread
            self.ui_manager.update_status("🚀 Loading playlist videos...")
            self.ui_manager.set_loading_state(True)
            
            thread = threading.Thread(
                target=self._load_playlist_thread,
                args=(playlist_id, max_results),
                daemon=True
            )
            thread.start()
            
        except Exception as e:
            print(f"Error loading playlist: {e}")
            self.ui_manager.show_message_dialog(
                "Load Error",
                f"Error loading playlist: {str(e)}",
                'error'
            )
    
    def _load_playlist_thread(self, playlist_id, max_results):
        """Background thread for loading playlist"""
        try:
            self.is_processing = True
            
            # Ensure YouTube service is ready (with retry)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Verify service is available
                    if not self.playlist_service.youtube_service:
                        if not self.youtube_service.youtube:
                            self.youtube_service.setup_youtube_api()
                        self.playlist_service.youtube_service = self.youtube_service.youtube
                    
                    # Test API connection with a simple call
                    test_request = self.playlist_service.youtube_service.playlists().list(
                        part='snippet',
                        id=playlist_id,
                        maxResults=1
                    )
                    test_response = test_request.execute()
                    
                    if not test_response.get('items'):
                        def update():
                            self.ui_manager.set_loading_state(False)
                            self.ui_manager.update_status("❌ Playlist not found or private")
                            self.ui_manager.show_message_dialog(
                                "Playlist Not Found",
                                "The playlist was not found or is private. Please check the URL and try again.",
                                'warning'
                            )
                        
                        self.ui_manager.safe_update(update)
                        return
                    
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    print(f"API setup attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        def retry_update():
                            self.ui_manager.update_status(f"🔄 API connection failed, retrying... ({attempt + 1}/{max_retries})")
                        self.ui_manager.safe_update(retry_update)
                        
                        import time
                        time.sleep(2)  # Wait before retry
                        continue
                    else:
                        # Final attempt failed
                        def error_update():
                            self.ui_manager.set_loading_state(False)
                            self.ui_manager.update_status("❌ YouTube API connection failed")
                            self.ui_manager.show_message_dialog(
                                "API Connection Error",
                                f"Failed to connect to YouTube API after {max_retries} attempts.\n\nError: {str(e)}\n\nPlease check your internet connection and API credentials.",
                                'error'
                            )
                        
                        self.ui_manager.safe_update(error_update)
                        return
            
            # Update status
            def status_update():
                self.ui_manager.update_status("📡 Loading playlist videos...")
            self.ui_manager.safe_update(status_update)
            
            # Get videos from playlist
            videos = self.playlist_service.get_playlist_videos(playlist_id, max_results)
            
            if not videos:
                def update():
                    self.ui_manager.set_loading_state(False)
                    self.ui_manager.update_status("❌ No videos found in playlist")
                    self.ui_manager.show_message_dialog(
                        "No Videos",
                        "No videos found in the playlist or playlist is private.",
                        'warning'
                    )
                
                self.ui_manager.safe_update(update)
                return
            
            # Update status with count
            def count_update():
                self.ui_manager.update_status(f"📊 Getting video details for {len(videos)} videos...")
            self.ui_manager.safe_update(count_update)
            
            # Get video details (quality info) with retry
            video_details = {}
            for retry_attempt in range(2):  # Max 2 attempts for video details
                try:
                    video_ids = [video['id'] for video in videos]
                    video_details = self.youtube_service.get_video_details(video_ids)
                    break
                except Exception as e:
                    print(f"Video details attempt {retry_attempt + 1} failed: {e}")
                    if retry_attempt == 0:
                        def retry_update():
                            self.ui_manager.update_status("🔄 Retrying video details...")
                        self.ui_manager.safe_update(retry_update)
                        
                        import time
                        time.sleep(1)
                    else:
                        print("Using basic video info without quality details")
                        # Continue with basic info only
                        for video in videos:
                            video_details[video['id']] = {'definition': 'hd'}  # Default
            
            # Merge details with playlist info
            for video in videos:
                details = video_details.get(video['id'], {'definition': 'hd'})
                video.update(details)
            
            # Update UI
            def update_ui():
                self.ui_manager.set_loading_state(False)
                
                # Clear existing videos
                tree = self.ui_manager.get_element('video_tree')
                if tree:
                    self.tree_manager.clear_tree(tree)
                
                # Add videos to tree
                for video in videos:
                    if tree:
                        self.tree_manager.add_video_to_tree(tree, video)
                
                # Update counts
                count_label = self.ui_manager.get_element('count_label')
                if count_label:
                    count_label.config(text=f"{len(videos)} videos")
                
                self.ui_manager.update_status(f"✅ Loaded {len(videos)} videos from playlist")
                
                # Auto-start 4K checking if enabled
                auto_check = self.ui_manager.get_element('auto_check_4k')
                if auto_check and getattr(auto_check, 'get', lambda: True)():
                    self.ui_manager.root.after(1000, self.check_4k_quality)
            
            self.ui_manager.safe_update(update_ui)
            
        except Exception as e:
            print(f"Error in playlist loading thread: {e}")
            
            def error_update():
                self.ui_manager.set_loading_state(False)
                self.ui_manager.update_status(f"❌ Error loading playlist: {str(e)}")
                self.ui_manager.show_message_dialog(
                    "Load Error",
                    f"Error loading playlist: {str(e)}",
                    'error'
                )
            
            self.ui_manager.safe_update(error_update)
        
        finally:
            self.is_processing = False
    
    def check_4k_quality(self):
        """Start 4K quality checking"""
        try:
            if self.is_processing:
                self.ui_manager.update_status("⚠️ Already processing, please wait...")
                return
            
            tree = self.ui_manager.get_element('video_tree')
            if not tree or len(tree.get_children()) == 0:
                self.ui_manager.show_message_dialog(
                    "No Videos",
                    "Please load a playlist first.",
                    'warning'
                )
                return
            
            # Collect video data
            video_details = []
            for item in tree.get_children():
                video_data = self.tree_manager.video_data.get(item, {})
                if video_data:
                    video_details.append(video_data)
            
            if not video_details:
                self.ui_manager.update_status("❌ No video data available")
                return
            
            self.stop_requested = False
            self.ui_manager.update_status("🚀 Starting 4K quality check...")
            self.ui_manager.set_checking_state(True)
            
            # Start checking in background thread
            thread = threading.Thread(
                target=self._check_4k_thread,
                args=(video_details,),
                daemon=True
            )
            thread.start()
            
        except Exception as e:
            print(f"Error starting 4K check: {e}")
            self.ui_manager.show_message_dialog(
                "Check Error",
                f"Error starting 4K check: {str(e)}",
                'error'
            )
    
    def _check_4k_thread(self, video_details):
        """Background thread for 4K checking"""
        try:
            self.is_processing = True
            
            def progress_callback(video, status):
                """Update individual video status"""
                try:
                    tree = self.ui_manager.get_element('video_tree')
                    if not tree:
                        return
                    
                    # Find the tree item for this video
                    video_id = video.get('id')
                    for item in tree.get_children():
                        if tree.set(item, 'id') == video_id:
                            def update():
                                self.tree_manager.update_video_status(tree, item, status)
                            self.ui_manager.safe_update(update)
                            break
                            
                except Exception as e:
                    print(f"Error in progress callback: {e}")
            
            def status_callback(message):
                """Update overall status"""
                self.ui_manager.update_status(message)
            
            def stop_check():
                """Check if stop was requested"""
                return self.stop_requested
            
            # Start parallel 4K checking
            found_4k = self.video_checker.check_videos_parallel(
                video_details,
                progress_callback,
                status_callback,
                stop_check
            )
            
            # Update final status
            def final_update():
                self.ui_manager.set_checking_state(False)
                
                if self.stop_requested:
                    self.ui_manager.update_status("⏹️ 4K check stopped by user")
                else:
                    message = f"✅ 4K check complete! Found {len(found_4k)} videos with 4K quality"
                    self.ui_manager.update_status(message)
                    
                    if len(found_4k) > 0:
                        self.ui_manager.show_message_dialog(
                            "4K Check Complete",
                            f"Found {len(found_4k)} videos with 4K quality available!",
                            'info'
                        )
            
            self.ui_manager.safe_update(final_update)
            
        except Exception as e:
            print(f"Error in 4K check thread: {e}")
            
            def error_update():
                self.ui_manager.set_checking_state(False)
                self.ui_manager.update_status(f"❌ 4K check error: {str(e)}")
                self.ui_manager.show_message_dialog(
                    "Check Error",
                    f"Error during 4K check: {str(e)}",
                    'error'
                )
            
            self.ui_manager.safe_update(error_update)
        
        finally:
            self.is_processing = False
    
    def stop_processing(self):
        """Stop current processing"""
        try:
            self.stop_requested = True
            self.video_checker.stop_checking()
            self.ui_manager.update_status("🛑 Stopping process...")
            
        except Exception as e:
            print(f"Error stopping process: {e}")
    
    def on_entry_change(self, event=None):
        """Handle max results entry changes"""
        try:
            max_entry = self.ui_manager.get_element('max_entry')
            max_slider = self.ui_manager.get_element('max_slider')
            
            if not max_entry or not max_slider:
                return
            
            try:
                value = int(max_entry.get())
                value = max(10, min(500, value))  # Clamp
                max_slider.set(value)
            except ValueError:
                # Invalid number, reset to slider value
                max_entry.delete(0, tk.END)
                max_entry.insert(0, str(int(max_slider.get())))
                
        except Exception as e:
            print(f"Error in entry change handler: {e}")
    
    def on_slider_change(self, value):
        """Handle slider value changes"""
        try:
            max_entry = self.ui_manager.get_element('max_entry')
            
            if max_entry:
                max_entry.delete(0, tk.END)
                max_entry.insert(0, str(int(float(value))))
                
        except Exception as e:
            print(f"Error in slider change handler: {e}")
    
    def on_filter_toggle(self):
        """Handle filter toggles"""
        try:
            filter_4k_var = self.ui_manager.get_element('filter_4k_var')
            
            if filter_4k_var and filter_4k_var.get():
                self.apply_4k_filter()
            else:
                self.show_all_videos()
                
        except Exception as e:
            print(f"Error in filter toggle: {e}")
    
    def apply_4k_filter(self):
        """Show only 4K videos"""
        try:
            tree = self.ui_manager.get_element('video_tree')
            if not tree:
                return
            
            # Hide non-4K videos
            for item in tree.get_children():
                status = tree.set(item, 'status')
                if '✅' in status or '4K Available' in status:
                    tree.reattach(item, '', 'end')
                else:
                    tree.detach(item)
            
            self.ui_manager.update_status("🔍 Showing only 4K videos")
            
        except Exception as e:
            print(f"Error applying 4K filter: {e}")
    
    def show_all_videos(self):
        """Show all videos"""
        try:
            tree = self.ui_manager.get_element('video_tree')
            if not tree:
                return
            
            # Show all videos
            for item in tree.get_children():
                tree.reattach(item, '', 'end')
            
            self.ui_manager.update_status("📺 Showing all videos")
            
        except Exception as e:
            print(f"Error showing all videos: {e}")
