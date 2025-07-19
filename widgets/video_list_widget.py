import tkinter as tk
from tkinter import ttk

class VideoListWidget:
    """Video List Widget with TreeView"""
    
    def __init__(self, parent, colors, on_tree_click_callback, on_context_menu_callback):
        self.colors = colors
        self.on_tree_click = on_tree_click_callback
        self.on_context_menu = on_context_menu_callback
        
        # Main frame
        self.frame = ttk.Frame(parent, style='Dark.TFrame')
        self.create_widgets()
    
    def create_widgets(self):
        """Create video list widgets"""
        # Header
        header = tk.Label(
            self.frame,
            text="🎬✨ Videos Found ✨🎬",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_cyan']
        )
        header.pack(anchor='w', pady=(0, 10))
        
        # Tree frame
        tree_frame = ttk.Frame(self.frame, style='Dark.TFrame')
        tree_frame.pack(fill='both', expand=True)
        
        # TreeView
        columns = ('Check', 'No', 'Thumbnail', 'Title', 'Quality', 'Status')
        self.video_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=15,
            style='Dark.Treeview'
        )
        
        # Column headers
        headers = {
            'Check': '☑️',
            'No': '#',
            'Thumbnail': '🖼️',
            'Title': 'Video Title',
            'Quality': 'Quality',
            'Status': '4K Status'
        }
        
        for col, header_text in headers.items():
            self.video_tree.heading(col, text=header_text)
        
        # Column widths
        widths = {
            'Check': (40, 40),
            'No': (50, 50),
            'Thumbnail': (80, 80),
            'Title': (400, 200),
            'Quality': (100, 100),
            'Status': (120, 120)
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
        
        # Bind events
        self.video_tree.bind('<Button-1>', self.on_tree_click)
        self.video_tree.bind('<Button-3>', self.on_context_menu)
    
    def pack(self, **kwargs):
        """Pack the main frame"""
        self.frame.pack(**kwargs)
    
    def clear(self):
        """Clear all items"""
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
    
    def add_video(self, video_data):
        """Add a video to the list"""
        item_id = self.video_tree.insert('', 'end', 
                                        values=video_data['values'],
                                        tags=video_data.get('tags', ()))
        return item_id
    
    def get_all_items(self):
        """Get all tree items"""
        return self.video_tree.get_children()
    
    def get_item_values(self, item):
        """Get values of an item"""
        return self.video_tree.item(item, 'values')
    
    def set_item_values(self, item, values):
        """Set values of an item"""
        self.video_tree.item(item, values=values)
    
    def get_selection(self):
        """Get selected items"""
        return self.video_tree.selection()
    
    def set_selection(self, item):
        """Set selection"""
        self.video_tree.selection_set(item)
    
    def delete_item(self, item):
        """Delete an item"""
        if self.video_tree.exists(item):
            self.video_tree.delete(item)
    
    def item_exists(self, item):
        """Check if item exists"""
        return self.video_tree.exists(item)
