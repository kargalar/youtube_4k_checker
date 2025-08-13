"""
Tree widget manager
Handles video list tree operations and interactions
"""
import tkinter as tk
from tkinter import ttk

class TreeManager:
    """Manager for video list tree widget operations"""
    
    def __init__(self, ui_manager, thumbnail_manager, theme_config=None):
        self.ui_manager = ui_manager
        self.thumbnail_manager = thumbnail_manager
        self.theme_config = theme_config
        self.video_data = {}  # Store video data by item ID
        self.video_id_index = {}  # Map video_id -> tree item_id
    
    def create_video_tree(self, parent):
        """Create and configure video list tree"""
        # Get theme colors (fallback to defaults if not available)
        if self.theme_config:
            colors = self.theme_config.COLORS
        else:
            colors = {
                'bg_primary': '#1a1a1a',
                'bg_secondary': '#242424',
                'text_primary': '#f5f5f5'
            }

        # Tree frame
        tree_frame = tk.Frame(parent, bg=colors['bg_primary'])
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Header
        header_frame = tk.Frame(tree_frame, bg=colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(0, 5))

        icon_label = tk.Label(
            header_frame,
            text='📺',
            bg=colors['bg_secondary'],
            fg=colors['text_primary'],
            font=('Segoe UI', 14),
        )
        icon_label.pack(side='left', padx=(5, 8))

        title_label = tk.Label(
            header_frame,
            text='Video List',
            bg=colors['bg_secondary'],
            fg=colors['text_primary'],
            font=('Segoe UI', 11, 'bold'),
        )
        title_label.pack(side='left')

        # Tree container
        tree_container = tk.Frame(tree_frame, bg=colors['bg_primary'])
        tree_container.pack(fill='both', expand=True)

        # Configure tree with columns (no date column; selection-based actions)
        columns = ('title', 'channel', 'status')
        tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show='tree headings',
            style='Modern.Treeview',
        )

        # Configure columns
        tree.column('#0', width=130, minwidth=100, stretch=False)  # Thumbnail column wider for bigger thumbs
        tree.column('title', width=380, minwidth=220, stretch=True)
        tree.column('channel', width=150, minwidth=100, stretch=False)
        tree.column('status', width=120, minwidth=100, stretch=False, anchor='center')

        # Configure headings
        tree.heading('#0', text='📷', anchor='center')
        tree.heading('title', text='📺 Title', anchor='w')
        tree.heading('channel', text='📺 Channel', anchor='w')
        tree.heading('status', text='📺 Quality', anchor='center')

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Bind events
        tree.bind('<Button-1>', self.on_tree_click)
        tree.bind('<Button-3>', self.show_context_menu)
        tree.bind('<Double-1>', self.on_double_click)
        tree.bind('<Delete>', self.on_delete_key)
        tree.bind('<<TreeviewSelect>>', self.on_select_changed)
        tree.bind('<Control-a>', self.on_ctrl_a)

        # Register with UI manager
        self.ui_manager.register_element('video_tree', tree)
        self.ui_manager.register_element('tree_scrollbar', scrollbar)

        return tree
    
    def add_video_to_tree(self, tree, video_data):
        """Add a video to the tree"""
        try:
            # Date removed from UI

            # Prepare title (prefix with [EN] if detected via API)
            raw_title = video_data.get('title', 'Unknown Title')
            title_prefix = '[EN] ' if video_data.get('is_english') else ''
            display_title_full = f"{title_prefix}{raw_title}".strip()
            # Prefix indicator if previously copied
            if self._is_previously_copied(video_data.get('id')):
                display_title_full = f"📋 {display_title_full}"
            display_title = display_title_full[:50] + ('...' if len(display_title_full) > 50 else '')

            # Add to tree
            item_id = tree.insert(
                '',
                'end',
                image='',  # Thumbnail will be loaded later
                values=(
                    display_title,
                    video_data.get('channel_title', 'Unknown Channel')[:25],
                    self._format_quality_initial(video_data.get('definition', 'hd')),
                ),
            )
            
            # Store video data
            self.video_data[item_id] = {
                **video_data,
                'tree_item_id': item_id,
                'checked': False
            }
            # Index by video id for quick status updates
            vid = video_data.get('id')
            if vid:
                self.video_id_index[vid] = item_id
            
            # Additional metadata is stored in self.video_data and video_id_index
            
            # Load thumbnail asynchronously
            if video_data.get('thumbnail'):
                self.load_video_thumbnail(tree, item_id, video_data)
            
            return item_id
            
        except Exception as e:
            print(f"Error adding video to tree: {e}")
            return None
    
    def load_video_thumbnail(self, tree, item_id, video_data):
        """Load thumbnail for video item"""
        try:
            video_id = video_data.get('id')
            thumbnail_url = video_data.get('thumbnail')
            
            if video_id and thumbnail_url:
                # Load thumbnail in background
                import threading
                
                def load_thumbnail():
                    try:
                        photo = self.thumbnail_manager.get_thumbnail_image(
                            video_id, thumbnail_url, (120, 68)
                        )
                        
                        if photo:
                            def update_tree():
                                if tree.exists(item_id):
                                    # Use correct API to set image on tree item
                                    tree.item(item_id, image=photo)
                                    # Keep reference to prevent garbage collection
                                    tree.image = getattr(tree, 'image', [])
                                    tree.image.append(photo)
                            
                            self.ui_manager.safe_update(update_tree)
                            
                    except Exception as e:
                        print(f"Error loading thumbnail for {video_id}: {e}")
                
                thread = threading.Thread(target=load_thumbnail, daemon=True)
                thread.start()
                
        except Exception as e:
            print(f"Error in thumbnail loading setup: {e}")

    def on_select_changed(self, event):
        """Update action buttons when selection changes"""
        try:
            tree = event.widget
            if hasattr(self, 'video_operations') and self.video_operations:
                # Prefer new unified updater if available
                updater = getattr(self.video_operations, 'update_action_buttons_state', None)
                if callable(updater):
                    updater(tree)
                else:
                    self.video_operations.update_copy_button_state(tree)
        except Exception as e:
            print(f"Error handling selection change: {e}")

    def on_ctrl_a(self, event):
        """Ctrl+A to select all items"""
        try:
            tree = event.widget
            items = tree.get_children()
            tree.selection_set(items)
            # Prevent text selection beep
            return 'break'
        except Exception as e:
            print(f"Error handling Ctrl+A: {e}")
    
    def update_video_status(self, tree, item_id, status):
        """Update video 4K status in tree"""
        try:
            if tree.exists(item_id):
                # Map 4K status strings to Quality label
                mapped = self._map_status_to_quality(status)
                tree.set(item_id, 'status', mapped)
                
                # Update stored data
                if item_id in self.video_data:
                    self.video_data[item_id]['4k_status'] = status
                    
        except Exception as e:
            print(f"Error updating video status: {e}")

    def _get_config_manager(self):
        try:
            return self.ui_manager.get_element('config_manager')
        except Exception:
            return None

    def _is_previously_copied(self, video_id):
        try:
            if not video_id:
                return False
            cfg = self._get_config_manager()
            if not cfg:
                return False
            copied = cfg.get('history.copied_video_ids', []) or []
            return video_id in copied
        except Exception:
            return False

    def set_copied_icon(self, tree, item, copied=True):
        """Toggle the copied indicator on the title cell for a tree item."""
        try:
            title = tree.set(item, 'title')
            has_icon = title.startswith('📋 ')
            if copied and not has_icon:
                tree.set(item, 'title', f"📋 {title}")
            elif not copied and has_icon:
                tree.set(item, 'title', title[2:].lstrip())
        except Exception as e:
            print(f"Error setting copied icon: {e}")

    def select_previously_copied(self, tree):
        """Select all items that were previously copied."""
        try:
            copied_ids = set(self._get_config_manager().get('history.copied_video_ids', []) or []) if self._get_config_manager() else set()
            if not copied_ids:
                return
            to_select = []
            for item in tree.get_children():
                meta = self.video_data.get(item, {})
                vid = meta.get('id')
                if vid and vid in copied_ids:
                    to_select.append(item)
            if to_select:
                tree.selection_set(to_select)
        except Exception as e:
            print(f"Error selecting previously copied: {e}")

    def _format_quality_initial(self, definition):
        """Return initial quality label based on definition (sd/hd)."""
        try:
            if str(definition).lower() == 'sd':
                return 'SD'
            return 'HD'
        except Exception:
            return 'HD'

    def _map_status_to_quality(self, status):
        """Normalize various status strings into SD/HD/4K quality labels."""
        try:
            s = str(status).lower().strip()
            # Handle negatives first to avoid 'no 4k' matching as 4K
            if 'no 4k' in s or '❌' in s:
                return 'HD'
            # Explicit SD labels
            if s.startswith('📱') or s == 'sd':
                return 'SD'
            # Explicit 4K labels only
            if '✅' in s or s == '4k' or '2160' in s:
                return '4K'
            if 'pending' in s or '⏳' in s:
                return '⏳ Pending'
            if 'timeout' in s:
                return '⚠️ Timeout'
            if 'failed' in s:
                return '⚠️ Failed'
            # Default: keep original if unknown
            return status
        except Exception:
            return status
    
    def on_tree_click(self, event):
        """Handle tree click events"""
        try:
            tree = event.widget
            # Left-click: no special handling needed now; keep for future hooks
            _ = tree.identify_region(event.x, event.y)
            if hasattr(self, 'video_operations'):
                self.video_operations.update_copy_button_state(tree)
                        
        except Exception as e:
            print(f"Error in tree click handler: {e}")
    
    def on_double_click(self, event):
        """Handle double-click to open video"""
        try:
            tree = event.widget
            item = tree.identify_row(event.y)
            
            if item:
                url = self.video_data.get(item, {}).get('url')
                if url:
                    import webbrowser
                    webbrowser.open(url)
                    self.ui_manager.update_status("🌐 Opened video in browser")
                    
        except Exception as e:
            print(f"Error in double-click handler: {e}")
    
    def show_context_menu(self, event):
        """Show context menu for tree items"""
        try:
            tree = event.widget
            item = tree.identify_row(event.y)
            
            if item:
                # Preserve existing selection; if nothing selected, select the item under cursor
                if not tree.selection() or item in ('', None):
                    if item:
                        tree.selection_set(item)
                
                # Get theme colors (fallback to defaults)
                if self.theme_config:
                    colors = self.theme_config.COLORS
                else:
                    colors = {
                        'bg_tertiary': '#2d2d2d',
                        'text_primary': '#f5f5f5',
                        'accent_blue': '#3b82f6'
                    }
                
                # Create context menu
                context_menu = tk.Menu(tree, tearoff=0)
                context_menu.configure(
                    bg=colors['bg_tertiary'],
                    fg=colors['text_primary'],
                    activebackground=colors['accent_blue'],
                    activeforeground='white',
                    relief='flat',
                    bd=1
                )
                
                context_menu.add_command(
                    label="🌐 Open in Browser",
                    command=lambda: self.open_selected_in_browser(tree)
                )
                
                context_menu.add_separator()
                
                context_menu.add_command(
                    label="📋 Copy URL(s)",
                    command=lambda: self.copy_selected_urls(tree)
                )
                
                context_menu.add_separator()
                
                context_menu.add_command(
                    label="🗑️ Remove from List",
                    command=lambda: self.remove_selected_items(tree)
                )
                context_menu.add_command(
                    label="❌ Remove from YouTube Playlist",
                    command=lambda: self.remove_selected_from_youtube(tree)
                )
                
                # Show menu
                context_menu.tk_popup(event.x_root, event.y_root)
                
        except Exception as e:
            print(f"Error showing context menu: {e}")
    
    def copy_item_url(self, tree, item):
        """Copy item URL to clipboard"""
        try:
            url = self.video_data.get(item, {}).get('url')
            if url:
                tree.clipboard_clear()
                tree.clipboard_append(url)
                self.ui_manager.update_status("📋 URL copied to clipboard")
                
        except Exception as e:
            print(f"Error copying item URL: {e}")

    def copy_selected_urls(self, tree):
        """Copy all selected items' URLs to clipboard (each on new line)"""
        try:
            selection = tree.selection()
            urls = []
            for item in selection:
                url = self.video_data.get(item, {}).get('url')
                if url:
                    urls.append(url)
            if urls:
                text = '\n'.join(urls)
                tree.clipboard_clear()
                tree.clipboard_append(text)
                self.ui_manager.update_status(f"📋 Copied {len(urls)} URL(s)")
        except Exception as e:
            print(f"Error copying selected URLs: {e}")
    
    def remove_tree_item(self, tree, item):
        """Remove item from tree"""
        try:
            from tkinter import messagebox
            
            title = tree.set(item, 'title')
            result = messagebox.askyesno(
                "Confirm Removal",
                f"Remove '{title}' from the list?"
            )
            
            if result:
                # Remove from stored data
                if item in self.video_data:
                    vid = self.video_data[item].get('id')
                    if vid and vid in self.video_id_index:
                        del self.video_id_index[vid]
                    del self.video_data[item]
                
                # Remove from tree
                tree.delete(item)
                self.ui_manager.update_status("🗑️ Video removed from list")
                
        except Exception as e:
            print(f"Error removing tree item: {e}")

    def remove_selected_items(self, tree):
        """Remove all selected items from the list (no confirmation)."""
        try:
            selection = list(tree.selection())
            if not selection:
                return
            for item in selection:
                # Clean stored indices
                if item in self.video_data:
                    vid = self.video_data[item].get('id')
                    if vid and vid in self.video_id_index:
                        del self.video_id_index[vid]
                    del self.video_data[item]
                # Remove from tree
                if tree.exists(item):
                    tree.delete(item)
            self.ui_manager.update_status(f"🗑️ Removed {len(selection)} item(s) from list")
        except Exception as e:
            print(f"Error removing selected items: {e}")

    def on_delete_key(self, event):
        """Handle Delete key to remove selected items."""
        try:
            tree = event.widget
            self.remove_selected_items(tree)
        except Exception as e:
            print(f"Error handling Delete key: {e}")

    def open_selected_in_browser(self, tree):
        """Open all selected videos in browser (or focused one if none)."""
        try:
            selection = tree.selection()
            if not selection:
                focused = tree.focus()
                selection = [focused] if focused else []
            count = 0
            for item in selection:
                url = self.video_data.get(item, {}).get('url')
                if url:
                    import webbrowser
                    webbrowser.open(url)
                    count += 1
            if count:
                self.ui_manager.update_status(f"🌐 Opened {count} video(s) in browser")
        except Exception as e:
            print(f"Error opening selected in browser: {e}")

    def remove_selected_from_youtube(self, tree):
        """Trigger removal of selected items from YouTube playlist via VideoOperations."""
        try:
            if hasattr(self, 'video_operations') and self.video_operations:
                self.video_operations.remove_selected_from_youtube(tree)
        except Exception as e:
            print(f"Error removing selected from YouTube: {e}")
    
    def clear_tree(self, tree):
        """Clear all items from tree"""
        try:
            # Clear stored data
            self.video_data.clear()
            self.video_id_index.clear()
            
            # Clear tree
            for item in tree.get_children():
                tree.delete(item)
                
            # Clear image references
            if hasattr(tree, 'image'):
                tree.image.clear()
                
        except Exception as e:
            print(f"Error clearing tree: {e}")

    def get_item_id_by_video_id(self, video_id):
        """Get tree item id by video id"""
        try:
            return self.video_id_index.get(video_id)
        except Exception:
            return None
    
    def get_checked_videos(self, tree):
        """Compatibility: return selected videos instead of 'checked'."""
        try:
            result = []
            selection = tree.selection()
            for item in selection:
                video_data = self.video_data.get(item, {})
                if video_data:
                    result.append(video_data)
            return result
        except Exception as e:
            print(f"Error getting selected videos: {e}")
            return []
    
    def check_all_videos(self, tree):
        """Select all videos in tree"""
        try:
            items = tree.get_children()
            tree.selection_set(items)
        except Exception as e:
            print(f"Error selecting all videos: {e}")
    
    def uncheck_all_videos(self, tree):
        """Clear selection for all videos in tree"""
        try:
            tree.selection_remove(tree.selection())
        except Exception as e:
            print(f"Error clearing selection: {e}")
    
    def check_4k_only(self, tree):
        """Select only videos with 4K availability"""
        try:
            select_items = []
            for item in tree.get_children():
                status = tree.set(item, 'status')
                if '✅' in status or '4K' in status:
                    select_items.append(item)
            tree.selection_set(select_items)
        except Exception as e:
            print(f"Error selecting 4K videos: {e}")
