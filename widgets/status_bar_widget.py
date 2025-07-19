import tkinter as tk
from tkinter import ttk

class StatusBarWidget:
    """Status Bar with Progress and Message"""
    
    def __init__(self, parent, colors):
        self.colors = colors
        
        # Main frame
        self.frame = ttk.Frame(parent, style='Dark.TFrame')
        self.create_widgets()
    
    def create_widgets(self):
        """Create status bar widgets"""
        # Progress bar
        self.progress = ttk.Progressbar(
            self.frame,
            mode='indeterminate',
            style='Dark.Horizontal.TProgressbar'
        )
        self.progress.pack(fill='x', pady=(0, 5))
        
        # Status label
        self.status_label = tk.Label(
            self.frame,
            text="💫 Enter playlist URL and click 'Get Videos' to start! 💫",
            font=('Segoe UI', 11, 'italic'),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_accent']
        )
        self.status_label.pack()
    
    def pack(self, **kwargs):
        """Pack the main frame"""
        self.frame.pack(**kwargs)
    
    def start_progress(self):
        """Start progress animation"""
        self.progress.start()
    
    def stop_progress(self):
        """Stop progress animation"""
        self.progress.stop()
    
    def set_message(self, message, color=None):
        """Set status message"""
        if color is None:
            color = self.colors['text_accent']
        self.status_label.config(text=message, fg=color)
    
    def set_success_message(self, message):
        """Set success message"""
        self.set_message(f"✅ {message}", self.colors['accent_green'])
    
    def set_error_message(self, message):
        """Set error message"""
        self.set_message(f"❌ {message}", self.colors['accent_red'])
    
    def set_warning_message(self, message):
        """Set warning message"""
        self.set_message(f"⚠️ {message}", self.colors['accent_orange'])
    
    def set_info_message(self, message):
        """Set info message"""
        self.set_message(f"💫 {message}", self.colors['text_accent'])
