import tkinter as tk
from tkinter import ttk

class ButtonBarWidget:
    """Modern Button Bar Widget"""
    
    def __init__(self, parent, colors):
        self.colors = colors
        self.buttons = {}
        
        # Main frame
        self.frame = ttk.Frame(parent, style='Dark.TFrame')
    
    def add_button(self, name, text, command, style='Dark.TButton', state='normal'):
        """Add a button to the bar"""
        button = ttk.Button(
            self.frame,
            text=text,
            command=command,
            style=style,
            state=state
        )
        button.pack(side='left', padx=(0, 10))
        self.buttons[name] = button
        return button
    
    def get_button(self, name):
        """Get a button by name"""
        return self.buttons.get(name)
    
    def enable_button(self, name):
        """Enable a button"""
        if name in self.buttons:
            self.buttons[name].config(state='normal')
    
    def disable_button(self, name):
        """Disable a button"""
        if name in self.buttons:
            self.buttons[name].config(state='disabled')
    
    def pack(self, **kwargs):
        """Pack the main frame"""
        self.frame.pack(**kwargs)

class ModernButtonBar(ButtonBarWidget):
    """Pre-configured modern button bar for YouTube 4K Checker"""
    
    def __init__(self, parent, colors, callbacks):
        super().__init__(parent, colors)
        self.callbacks = callbacks
        self.create_buttons()
    
    def create_buttons(self):
        """Create all buttons"""
        # Main action buttons
        self.add_button('get_videos', '📥 Get Videos', 
                       self.callbacks.get('get_videos'), 'Dark.TButton')
        
        self.add_button('check_4k', '🔍 Check 4K', 
                       self.callbacks.get('check_4k'), 'Warning.TButton', 'disabled')
        
        self.add_button('stop', '⏹️ Stop', 
                       self.callbacks.get('stop'), 'Danger.TButton', 'disabled')
        
        # Management buttons
        self.add_button('copy', '📋 Copy Checked', 
                       self.callbacks.get('copy'), 'Neon.TButton', 'disabled')
        
        self.add_button('check_all', '☑️ Check All', 
                       self.callbacks.get('check_all'), 'Dark.TButton', 'disabled')
        
        self.add_button('uncheck_all', '☐ Uncheck All', 
                       self.callbacks.get('uncheck_all'), 'Dark.TButton', 'disabled')
        
        self.add_button('check_4k_only', '✨ Check 4K Only', 
                       self.callbacks.get('check_4k_only'), 'Neon.TButton', 'disabled')
        
        # YouTube action
        self.add_button('remove_youtube', '🚀 Remove from YouTube', 
                       self.callbacks.get('remove_youtube'), 'Gradient.TButton', 'disabled')
        
        # Clear button
        self.add_button('clear', '🗑️ Clear', 
                       self.callbacks.get('clear'), 'Dark.TButton')
