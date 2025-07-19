import tkinter as tk
from tkinter import ttk

class PlaylistInputWidget:
    """Playlist URL Input Widget"""
    
    def __init__(self, parent, colors, on_url_change_callback, on_paste_callback):
        self.colors = colors
        self.on_url_change = on_url_change_callback
        self.on_paste = on_paste_callback
        
        # Main frame
        self.frame = ttk.Frame(parent, style='Dark.TFrame')
        self.create_widgets()
    
    def create_widgets(self):
        """Create playlist input widgets"""
        # Title
        title_label = ttk.Label(
            self.frame,
            text="Playlist URL:",
            font=('Segoe UI', 12, 'bold'),
            style='Dark.TLabel'
        )
        title_label.pack(anchor='w', pady=(0, 5))
        
        # Input frame
        input_frame = ttk.Frame(self.frame, style='Dark.TFrame')
        input_frame.pack(fill='x', pady=(0, 10))
        
        # URL Entry
        self.url_entry = ttk.Entry(
            input_frame,
            font=('Segoe UI', 11),
            style='Dark.TEntry',
            width=60
        )
        self.url_entry.pack(side='left', fill='x', expand=True)
        self.url_entry.bind('<KeyRelease>', self.on_url_change)
        self.url_entry.bind('<FocusOut>', self.on_url_change)
        
        # Paste button
        paste_btn = ttk.Button(
            input_frame,
            text="📋 Paste",
            command=self.on_paste,
            style='Success.TButton'
        )
        paste_btn.pack(side='right', padx=(10, 0))
        
        # Playlist info
        self.info_frame = ttk.Frame(self.frame, style='Dark.TFrame')
        self.info_frame.pack(fill='x', pady=(0, 10))
        
        self.info_label = tk.Label(
            self.info_frame,
            text="",
            font=('Segoe UI', 10),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_secondary'],
            wraplength=800,
            justify='left'
        )
        self.info_label.pack(anchor='w')
    
    def pack(self, **kwargs):
        """Pack the main frame"""
        self.frame.pack(**kwargs)
    
    def get_url(self):
        """Get the current URL"""
        return self.url_entry.get().strip()
    
    def set_url(self, url):
        """Set the URL"""
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
    
    def update_info(self, info_text, color=None):
        """Update playlist info"""
        if color is None:
            color = self.colors['text_secondary']
        self.info_label.config(text=info_text, fg=color)
