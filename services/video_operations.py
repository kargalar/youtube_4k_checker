"""
Video operations service
Handles video-related operations like copying, removing, etc.
"""
import tkinter as tk
from tkinter import messagebox
import threading
import webbrowser

class VideoOperations:
    """Service for video operations and management"""
    
    def __init__(self, ui_manager, playlist_service, theme_config=None):
        self.ui_manager = ui_manager
        self.playlist_service = playlist_service
        self.theme_config = theme_config
        self.checked_videos = []
        # Tree manager is set later by main_app after creation
        self.tree_manager = None
    
    def copy_selected_url(self, tree):
        """Copy selected video URL to clipboard"""
        try:
            selection = tree.selection()
            if not selection:
                self.ui_manager.show_message_dialog(
                    "Selection Required",
                    "Please select a video to copy its URL.",
                    'warning'
                )
                return
            
            item = selection[0]
            url = self._get_video_meta(item).get('url')
            
            if url:
                tree.clipboard_clear()
                tree.clipboard_append(url)
                
                # Get theme colors (fallback to defaults)
                if self.theme_config:
                    accent_green = self.theme_config.COLORS['accent_green']
                else:
                    accent_green = '#10b981'
                
                self.ui_manager.update_status(f"URL copied to clipboard", accent_green)
            
        except Exception as e:
            print(f"Error copying URL: {e}")
            self.ui_manager.show_message_dialog(
                "Copy Error",
                f"Error copying URL: {str(e)}",
                'error'
            )
    
    def copy_checked_urls(self, tree):
        """Copy all checked video URLs to clipboard"""
        try:
            checked_video_data = []
            
            # Collect checked videos
            for item in tree.get_children():
                checkbox_value = tree.set(item, 'checkbox')
                if checkbox_value == '☑':
                    # Merge tree visible fields with stored meta
                    meta = self._get_video_meta(item)
                    video_data = {
                        'title': tree.set(item, 'title'),
                        'url': meta.get('url'),
                        'status': tree.set(item, 'status'),
                        'id': meta.get('id'),
                        'playlist_item_id': meta.get('playlist_item_id')
                    }
                    checked_video_data.append(video_data)
            
            if not checked_video_data:
                self.ui_manager.show_message_dialog(
                    "No Videos Selected",
                    "Please check at least one video to copy URLs.",
                    'warning'
                )
                return
            
            self.show_copy_options_dialog(checked_video_data, len(checked_video_data))
            
        except Exception as e:
            print(f"Error copying checked URLs: {e}")
            self.ui_manager.show_message_dialog(
                "Copy Error",
                f"Error copying URLs: {str(e)}",
                'error'
            )
    
    def show_copy_options_dialog(self, checked_video_data, count):
        """Show dialog with copy and remove options"""
        try:
            # Get theme colors (fallback to defaults)
            if self.theme_config:
                colors = self.theme_config.COLORS
            else:
                colors = {
                    'bg_primary': '#1a1a1a',
                    'bg_secondary': '#242424',
                    'bg_tertiary': '#2d2d2d',
                    'text_primary': '#f5f5f5',
                    'accent_blue': '#3b82f6',
                    'accent_green': '#10b981',
                    'accent_orange': '#f59e0b',
                    'accent_red': '#ef4444'
                }
            
            dialog = tk.Toplevel()
            dialog.title("Copy & Actions")
            dialog.geometry("500x400")
            dialog.configure(bg=colors['bg_primary'])
            dialog.transient(self.ui_manager.root)
            dialog.grab_set()
            
            # Center dialog
            dialog.geometry("+%d+%d" % (
                dialog.master.winfo_rootx() + 50,
                dialog.master.winfo_rooty() + 50
            ))
            
            # Title
            title_label = tk.Label(
                dialog,
                text=f"📋 {count} Videos Selected",
                bg=colors['bg_primary'],
                fg=colors['text_primary'],
                font=('Segoe UI', 14, 'bold')
            )
            title_label.pack(pady=(20, 10))
            
            # Copy section
            copy_frame = tk.Frame(dialog, bg=colors['bg_secondary'])
            copy_frame.pack(fill='x', padx=20, pady=10)
            
            copy_label = tk.Label(
                copy_frame,
                text="📄 Copy Options:",
                bg=colors['bg_secondary'],
                fg=colors['text_primary'],
                font=('Segoe UI', 11, 'bold')
            )
            copy_label.pack(anchor='w', padx=10, pady=(10, 5))
            
            # Copy buttons
            button_frame = tk.Frame(copy_frame, bg=colors['bg_secondary'])
            button_frame.pack(fill='x', padx=10, pady=(0, 10))
            
            def copy_urls_only():
                urls = [video['url'] for video in checked_video_data]
                text = '\n'.join(urls)
                dialog.clipboard_clear()
                dialog.clipboard_append(text)
                self.ui_manager.update_status(f"📋 {len(urls)} URLs copied to clipboard")
                dialog.destroy()
            
            def copy_with_titles():
                lines = []
                for video in checked_video_data:
                    lines.append(f"{video['title']}\n{video['url']}\n")
                text = '\n'.join(lines)
                dialog.clipboard_clear()
                dialog.clipboard_append(text)
                self.ui_manager.update_status(f"📋 {len(checked_video_data)} videos with titles copied")
                dialog.destroy()
            
            copy_urls_btn = tk.Button(
                button_frame,
                text="📋 URLs Only",
                command=copy_urls_only,
                bg=colors['accent_blue'],
                fg='white',
                font=('Segoe UI', 9),
                relief='flat',
                padx=15,
                pady=5
            )
            copy_urls_btn.pack(side='left', padx=(0, 10))
            
            copy_titles_btn = tk.Button(
                button_frame,
                text="📄 With Titles",
                command=copy_with_titles,
                bg=colors['accent_green'],
                fg='white',
                font=('Segoe UI', 9),
                relief='flat',
                padx=15,
                pady=5
            )
            copy_titles_btn.pack(side='left')
            
            # Remove section
            remove_frame = tk.Frame(dialog, bg=colors['bg_secondary'])
            remove_frame.pack(fill='x', padx=20, pady=10)
            
            remove_label = tk.Label(
                remove_frame,
                text="🗑️ Remove Options:",
                bg=colors['bg_secondary'],
                fg=colors['text_primary'],
                font=('Segoe UI', 11, 'bold')
            )
            remove_label.pack(anchor='w', padx=10, pady=(10, 5))
            
            # Remove buttons
            remove_button_frame = tk.Frame(remove_frame, bg=colors['bg_secondary'])
            remove_button_frame.pack(fill='x', padx=10, pady=(0, 10))
            
            remove_list_btn = tk.Button(
                remove_button_frame,
                text="📝 Remove from List",
                command=lambda: self.remove_from_local_list(checked_video_data, dialog),
                bg=colors['accent_orange'],
                fg='white',
                font=('Segoe UI', 9),
                relief='flat',
                padx=15,
                pady=5
            )
            remove_list_btn.pack(side='left', padx=(0, 10))
            
            remove_youtube_btn = tk.Button(
                remove_button_frame,
                text="❌ Remove from YouTube",
                command=lambda: self.remove_from_youtube_playlist(checked_video_data, dialog),
                bg=colors['accent_red'],
                fg='white',
                font=('Segoe UI', 9),
                relief='flat',
                padx=15,
                pady=5
            )
            remove_youtube_btn.pack(side='left')
            
            # Close button
            close_btn = tk.Button(
                dialog,
                text="❌ Close",
                command=dialog.destroy,
                bg=colors['bg_tertiary'],
                fg=colors['text_primary'],
                font=('Segoe UI', 9),
                relief='flat',
                padx=20,
                pady=8
            )
            close_btn.pack(pady=20)
            
        except Exception as e:
            print(f"Error showing copy dialog: {e}")
    
    def remove_from_local_list(self, video_data, dialog):
        """Remove videos from local list only"""
        try:
            tree = self.ui_manager.get_element('video_tree')
            if not tree:
                return
            
            removed_count = 0
            
            # Remove from tree
            for item in tree.get_children():
                checkbox_value = tree.set(item, 'checkbox')
                if checkbox_value == '☑':
                    tree.delete(item)
                    removed_count += 1
            
            self.ui_manager.update_status(f"🗑️ {removed_count} videos removed from list")
            self.update_video_count()
            dialog.destroy()
            
        except Exception as e:
            print(f"Error removing from list: {e}")
            messagebox.showerror("Remove Error", f"Error removing videos: {str(e)}")
    
    def remove_from_youtube_playlist(self, video_data, dialog):
        """Remove videos from YouTube playlist"""
        try:
            if not self.playlist_service.youtube_service:
                self.ui_manager.show_message_dialog(
                    "Authentication Required",
                    "Please authenticate with YouTube to remove videos from playlist.",
                    'warning'
                )
                return
            
            dialog.destroy()
            
            # Confirm removal
            result = messagebox.askyesno(
                "Confirm Removal",
                f"Are you sure you want to remove {len(video_data)} videos from the YouTube playlist?\n\nThis action cannot be undone!"
            )
            
            if result:
                self.ui_manager.update_status("🔄 Removing videos from YouTube playlist...")
                self.ui_manager.set_checking_state(True)
                
                # Start removal in background thread
                thread = threading.Thread(
                    target=self._remove_from_playlist_thread,
                    args=(video_data,),
                    daemon=True
                )
                thread.start()
            
        except Exception as e:
            print(f"Error removing from YouTube: {e}")
            self.ui_manager.show_message_dialog(
                "Remove Error",
                f"Error removing videos from YouTube: {str(e)}",
                'error'
            )
    
    def _remove_from_playlist_thread(self, video_data):
        """Background thread for playlist removal"""
        try:
            def progress_callback(current, total, removed, failed):
                self.ui_manager.update_status(
                    f"🔄 Removing from YouTube: {current}/{total} (✅{removed} ❌{failed})"
                )
                self.ui_manager.update_progress(current, total, "Removing")
            
            # Remove videos
            result = self.playlist_service.remove_videos_batch(video_data, progress_callback)
            
            # Update UI
            def update_ui():
                self.ui_manager.set_checking_state(False)
                
                if result['removed'] > 0:
                    # Remove successful removals from tree
                    tree = self.ui_manager.get_element('video_tree')
                    if tree:
                        items_to_remove = []
                        for item in tree.get_children():
                            checkbox_value = tree.set(item, 'checkbox')
                            if checkbox_value == '☑':
                                items_to_remove.append(item)
                        
                        for item in items_to_remove:
                            tree.delete(item)
                        
                        self.update_video_count()
                
                # Show result
                message = f"✅ Removed {result['removed']} videos"
                if result['failed'] > 0:
                    message += f"\n❌ Failed to remove {result['failed']} videos"
                
                self.ui_manager.update_status(message)
                self.ui_manager.show_message_dialog("Removal Complete", message, 'info')
            
            self.ui_manager.safe_update(update_ui)
            
        except Exception as e:
            print(f"Error in removal thread: {e}")
            def error_update():
                self.ui_manager.set_checking_state(False)
                self.ui_manager.update_status(f"❌ Removal error: {str(e)}")
                self.ui_manager.show_message_dialog(
                    "Removal Error",
                    f"Error removing videos: {str(e)}",
                    'error'
                )
            
            self.ui_manager.safe_update(error_update)
    
    def remove_selected_video(self, tree):
        """Remove selected video from list"""
        try:
            selection = tree.selection()
            if not selection:
                self.ui_manager.show_message_dialog(
                    "Selection Required",
                    "Please select a video to remove.",
                    'warning'
                )
                return
            
            # Confirm removal
            item = selection[0]
            title = tree.set(item, 'title')
            
            result = messagebox.askyesno(
                "Confirm Removal",
                f"Remove '{title}' from the list?"
            )
            
            if result:
                tree.delete(item)
                self.ui_manager.update_status("🗑️ Video removed from list")
                self.update_video_count()
        
        except Exception as e:
            print(f"Error removing video: {e}")
            self.ui_manager.show_message_dialog(
                "Remove Error",
                f"Error removing video: {str(e)}",
                'error'
            )
    
    def open_video_in_browser(self, tree):
        """Open selected video in web browser"""
        try:
            selection = tree.selection()
            if not selection:
                return
            
            item = selection[0]
            url = self._get_video_meta(item).get('url')
            
            if url:
                webbrowser.open(url)
                self.ui_manager.update_status(f"🌐 Opened video in browser")
        
        except Exception as e:
            print(f"Error opening video: {e}")
    
    def update_video_count(self):
        """Update video count display"""
        try:
            tree = self.ui_manager.get_element('video_tree')
            count_label = self.ui_manager.get_element('count_label')
            
            if tree and count_label:
                count = len(tree.get_children())
                def update():
                    count_label.config(text=f"{count} videos")
                
                self.ui_manager.safe_update(update)
                
        except Exception as e:
            print(f"Error updating video count: {e}")
    
    def update_copy_button_state(self, tree):
        """Update copy button state based on selections"""
        try:
            copy_button = self.ui_manager.get_element('copy_button')
            if not copy_button:
                return
            
            # Check if any videos are checked
            has_checked = False
            for item in tree.get_children():
                if tree.set(item, 'checkbox') == '☑':
                    has_checked = True
                    break
            
            def update():
                copy_button.config(state='normal' if has_checked else 'disabled')
            
            self.ui_manager.safe_update(update)
            
        except Exception as e:
            print(f"Error updating copy button: {e}")

    def _get_video_meta(self, item):
        """Helper to get full stored metadata for a tree item."""
        try:
            # Prefer the injected reference
            tree_manager = getattr(self, 'tree_manager', None)
            if tree_manager and hasattr(tree_manager, 'video_data'):
                return tree_manager.video_data.get(item, {})
            # Fallback to UIManager registry
            tree_manager = getattr(self.ui_manager, '_ui_elements', {}).get('tree_manager_instance')
            if tree_manager and hasattr(tree_manager, 'video_data'):
                return tree_manager.video_data.get(item, {})
        except Exception:
            pass
        return {}
