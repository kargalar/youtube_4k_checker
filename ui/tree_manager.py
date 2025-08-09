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
            text="📺",
            bg=colors['bg_secondary'],
            fg=colors['text_primary'],
            font=('Segoe UI', 14)
        )
        icon_label.pack(side='left', padx=(5, 8))
        
        title_label = tk.Label(
            header_frame,
            text="Video List",
            bg=colors['bg_secondary'],
            fg=colors['text_primary'],
            font=('Segoe UI', 11, 'bold')
        )
        title_label.pack(side='left')
        
        # Tree container
        tree_container = tk.Frame(tree_frame, bg=colors['bg_primary'])
        tree_container.pack(fill='both', expand=True)
        
        # Configure tree with columns
        columns = ('checkbox', 'title', 'channel', 'status', 'definition', 'published')
        tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show='tree headings',
            style='Modern.Treeview'
        )
        
        # Configure columns
        tree.column('#0', width=60, minwidth=60, stretch=False)  # Thumbnail column
        tree.column('checkbox', width=30, minwidth=30, stretch=False, anchor='center')
        tree.column('title', width=350, minwidth=200, stretch=True)
        tree.column('channel', width=150, minwidth=100, stretch=False)
        tree.column('status', width=120, minwidth=100, stretch=False, anchor='center')
        tree.column('definition', width=60, minwidth=60, stretch=False, anchor='center')
        tree.column('published', width=100, minwidth=80, stretch=False, anchor='center')
        
        # Configure headings
        tree.heading('#0', text='📷', anchor='center')
        tree.heading('checkbox', text='☐', anchor='center')
        tree.heading('title', text='📺 Title', anchor='w')
        tree.heading('channel', text='📺 Channel', anchor='w')
        tree.heading('status', text='🔍 4K Status', anchor='center')
        tree.heading('definition', text='📺 Quality', anchor='center')
        tree.heading('published', text='📅 Date', anchor='center')
        
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
        
        # Register with UI manager
        self.ui_manager.register_element('video_tree', tree)
        self.ui_manager.register_element('tree_scrollbar', scrollbar)
        
        return tree
    
    def add_video_to_tree(self, tree, video_data):
        """Add a video to the tree"""
        try:
            # Format date
            published_date = video_data.get('published_at', '')
            if published_date:
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                except:
                    formatted_date = published_date[:10]  # Fallback
            else:
                formatted_date = ''
            
            # Add to tree
            item_id = tree.insert('', 'end',
                image='',  # Thumbnail will be loaded later
                values=(
                    '☐',  # checkbox
                    video_data.get('title', 'Unknown Title')[:50] + ('...' if len(video_data.get('title', '')) > 50 else ''),
                    video_data.get('channel_title', 'Unknown Channel')[:25],
                    '⏳ Pending',  # status
                    video_data.get('definition', 'hd').upper(),
                    formatted_date
                )
            )
            
            # Store video data
            self.video_data[item_id] = {
                **video_data,
                'tree_item_id': item_id,
                'checked': False
            }
            
            # Set additional data in tree
            tree.set(item_id, 'id', video_data.get('id', ''))
            tree.set(item_id, 'url', video_data.get('url', ''))
            tree.set(item_id, 'playlist_item_id', video_data.get('playlist_item_id', ''))
            
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
                            video_id, thumbnail_url, (45, 30)
                        )
                        
                        if photo:
                            def update_tree():
                                if tree.exists(item_id):
                                    tree.set(item_id, '#0', image=photo)
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
    
    def update_video_status(self, tree, item_id, status):
        """Update video 4K status in tree"""
        try:
            if tree.exists(item_id):
                tree.set(item_id, 'status', status)
                
                # Update stored data
                if item_id in self.video_data:
                    self.video_data[item_id]['4k_status'] = status
                    
        except Exception as e:
            print(f"Error updating video status: {e}")
    
    def toggle_checkbox(self, tree, item):
        """Toggle checkbox for tree item"""
        try:
            current_value = tree.set(item, 'checkbox')
            new_value = '☑' if current_value == '☐' else '☐'
            tree.set(item, 'checkbox', new_value)
            
            # Update stored data
            if item in self.video_data:
                self.video_data[item]['checked'] = (new_value == '☑')
            
            return new_value == '☑'
            
        except Exception as e:
            print(f"Error toggling checkbox: {e}")
            return False
    
    def on_tree_click(self, event):
        """Handle tree click events"""
        try:
            tree = event.widget
            region = tree.identify_region(event.x, event.y)
            
            if region == "cell":
                column = tree.identify_column(event.x, event.y)
                item = tree.identify_row(event.y)
                
                # Handle checkbox column clicks
                if column == '#2' and item:  # Checkbox column
                    self.toggle_checkbox(tree, item)
                    
                    # Update UI state
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
                url = tree.set(item, 'url')
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
                    command=lambda: self.on_double_click(event)
                )
                
                context_menu.add_separator()
                
                context_menu.add_command(
                    label="📋 Copy URL",
                    command=lambda: self.copy_item_url(tree, item)
                )
                
                context_menu.add_separator()
                
                context_menu.add_command(
                    label="🗑️ Remove from List",
                    command=lambda: self.remove_tree_item(tree, item)
                )
                
                # Show menu
                context_menu.tk_popup(event.x_root, event.y_root)
                
        except Exception as e:
            print(f"Error showing context menu: {e}")
    
    def copy_item_url(self, tree, item):
        """Copy item URL to clipboard"""
        try:
            url = tree.set(item, 'url')
            if url:
                tree.clipboard_clear()
                tree.clipboard_append(url)
                self.ui_manager.update_status("📋 URL copied to clipboard")
                
        except Exception as e:
            print(f"Error copying item URL: {e}")
    
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
                    del self.video_data[item]
                
                # Remove from tree
                tree.delete(item)
                self.ui_manager.update_status("🗑️ Video removed from list")
                
        except Exception as e:
            print(f"Error removing tree item: {e}")
    
    def clear_tree(self, tree):
        """Clear all items from tree"""
        try:
            # Clear stored data
            self.video_data.clear()
            
            # Clear tree
            for item in tree.get_children():
                tree.delete(item)
                
            # Clear image references
            if hasattr(tree, 'image'):
                tree.image.clear()
                
        except Exception as e:
            print(f"Error clearing tree: {e}")
    
    def get_checked_videos(self, tree):
        """Get all checked videos"""
        try:
            checked = []
            
            for item in tree.get_children():
                if tree.set(item, 'checkbox') == '☑':
                    video_data = self.video_data.get(item, {})
                    if video_data:
                        checked.append(video_data)
            
            return checked
            
        except Exception as e:
            print(f"Error getting checked videos: {e}")
            return []
    
    def check_all_videos(self, tree):
        """Check all videos in tree"""
        try:
            for item in tree.get_children():
                tree.set(item, 'checkbox', '☑')
                if item in self.video_data:
                    self.video_data[item]['checked'] = True
                    
        except Exception as e:
            print(f"Error checking all videos: {e}")
    
    def uncheck_all_videos(self, tree):
        """Uncheck all videos in tree"""
        try:
            for item in tree.get_children():
                tree.set(item, 'checkbox', '☐')
                if item in self.video_data:
                    self.video_data[item]['checked'] = False
                    
        except Exception as e:
            print(f"Error unchecking all videos: {e}")
    
    def check_4k_only(self, tree):
        """Check only videos with 4K availability"""
        try:
            for item in tree.get_children():
                status = tree.set(item, 'status')
                
                if '✅' in status or '4K Available' in status:
                    tree.set(item, 'checkbox', '☑')
                    if item in self.video_data:
                        self.video_data[item]['checked'] = True
                else:
                    tree.set(item, 'checkbox', '☐')
                    if item in self.video_data:
                        self.video_data[item]['checked'] = False
                        
        except Exception as e:
            print(f"Error checking 4K videos: {e}")
