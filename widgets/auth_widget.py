import tkinter as tk
from tkinter import ttk

class AuthenticationWidget:
    """OAuth2 Authentication Widget"""
    
    def __init__(self, parent, colors, on_login_callback, on_logout_callback):
        self.colors = colors
        self.on_login = on_login_callback
        self.on_logout = on_logout_callback
        self.is_authenticated = False
        
        # Main frame
        self.frame = ttk.Frame(parent, style='Dark.TFrame')
        self.create_widgets()
    
    def create_widgets(self):
        """Create authentication widgets"""
        # Left side - status
        left_frame = ttk.Frame(self.frame, style='Dark.TFrame')
        left_frame.pack(side='left')
        
        self.status_label = tk.Label(
            left_frame, 
            text="⚠️ Authentication Required",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_orange']
        )
        self.status_label.pack(side='left')
        
        # Right side - button
        right_frame = ttk.Frame(self.frame, style='Dark.TFrame')
        right_frame.pack(side='right')
        
        self.auth_btn = ttk.Button(
            right_frame,
            text="🔐 Login",
            command=self.on_login,
            style='Success.TButton'
        )
        self.auth_btn.pack(side='right')
    
    def pack(self, **kwargs):
        """Pack the main frame"""
        self.frame.pack(**kwargs)
    
    def update_status(self, is_authenticated):
        """Update authentication status"""
        self.is_authenticated = is_authenticated
        
        if is_authenticated:
            self.status_label.config(
                text="✨ 🔐 Authenticated & Ready! ✨",
                fg=self.colors['accent_green']
            )
            self.auth_btn.config(
                text="🚪 Logout",
                command=self.on_logout,
                style='Warning.TButton'
            )
        else:
            self.status_label.config(
                text="⚠️ Authentication Required",
                fg=self.colors['accent_orange']
            )
            self.auth_btn.config(
                text="🔐 Login",
                command=self.on_login,
                style='Success.TButton'
            )
