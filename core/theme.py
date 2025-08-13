"""
Theme configuration module for YouTube 4K Checker
Handles colors, styles, and visual appearance settings
"""
from tkinter import ttk

class ThemeConfig:
    """Modern professional dark theme configuration"""
    
    # Color palette
    COLORS = {
        'bg_primary': '#1a1a1a',      # Rich dark gray
        'bg_secondary': '#242424',    # Medium dark gray  
        'bg_tertiary': '#2d2d2d',     # Lighter dark gray
        'bg_hover': '#383838',        # Hover state
        'text_primary': '#f5f5f5',    # Soft white
        'text_secondary': '#b8b8b8',  # Muted gray
        'text_accent': '#6366f1',     # Professional indigo
        'accent_blue': '#3b82f6',     # Clean blue
        'accent_green': '#10b981',    # Professional emerald
        'accent_orange': '#f59e0b',   # Warm amber
        'accent_red': '#ef4444',      # Clean red
        'accent_purple': '#8b5cf6',   # Sophisticated violet
        'accent_pink': '#ec4899',     # Refined pink
        'accent_yellow': '#eab308',   # Professional yellow
        'accent_cyan': '#06b6d4',     # Modern cyan
        'border': '#404040',          # Subtle border
        'gradient_start': '#4f46e5',  # Indigo gradient
        'gradient_end': '#7c3aed'     # Purple gradient
    }
    
    # Font configurations
    FONTS = {
        'main': ('Segoe UI', 10),
        'heading': ('Segoe UI', 12, 'bold'),
        'small': ('Segoe UI', 9),
        'large': ('Segoe UI', 14, 'bold')
    }
    
    # Widget styles
    BUTTON_STYLE = {
        'relief': 'flat',
        'borderwidth': 0,
        'padx': 15,
        'pady': 8,
        'font': FONTS['main']
    }
    
    ENTRY_STYLE = {
        'relief': 'flat',
        'borderwidth': 1,
        'insertwidth': 2,
        'font': FONTS['main']
    }
    
    @classmethod
    def configure_ttk_styles(cls, root):
        """Configure TTK styles for consistent theming"""
        style = ttk.Style(root)
        
        # Configure Treeview style
        style.theme_use('clam')
        
        # Dark Treeview
        style.configure(
            "Dark.Treeview",
            background=cls.COLORS['bg_secondary'],
            foreground=cls.COLORS['text_primary'],
            fieldbackground=cls.COLORS['bg_secondary'],
            borderwidth=0,
            font=cls.FONTS['main'],
            rowheight=96
        )
        
        style.configure(
            "Dark.Treeview.Heading",
            background=cls.COLORS['bg_tertiary'],
            foreground=cls.COLORS['text_primary'],
            borderwidth=1,
            relief='flat',
            font=cls.FONTS['heading']
        )
        
        # Selected item colors
        style.map("Dark.Treeview",
                  background=[('selected', cls.COLORS['accent_blue'])],
                  foreground=[('selected', cls.COLORS['text_primary'])])
        
        style.map("Dark.Treeview.Heading",
                  background=[('active', cls.COLORS['bg_hover'])])

        # Provide equivalent "Modern" styles used by widgets
        style.configure(
            "Modern.Treeview",
            background=cls.COLORS['bg_secondary'],
            foreground=cls.COLORS['text_primary'],
            fieldbackground=cls.COLORS['bg_secondary'],
            borderwidth=0,
            font=cls.FONTS['main'],
            rowheight=96
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=cls.COLORS['bg_tertiary'],
            foreground=cls.COLORS['text_primary'],
            borderwidth=1,
            relief='flat',
            font=cls.FONTS['heading']
        )
        style.map("Modern.Treeview",
                  background=[('selected', cls.COLORS['accent_blue'])],
                  foreground=[('selected', cls.COLORS['text_primary'])])
        style.map("Modern.Treeview.Heading",
                  background=[('active', cls.COLORS['bg_hover'])])
        
        # Progress bar
        style.configure(
            "Dark.Horizontal.TProgressbar",
            background=cls.COLORS['accent_green'],
            troughcolor=cls.COLORS['bg_tertiary'],
            borderwidth=0,
            lightcolor=cls.COLORS['accent_green'],
            darkcolor=cls.COLORS['accent_green']
        )
        # Alias for Modern progressbar
        style.configure(
            "Modern.Horizontal.TProgressbar",
            background=cls.COLORS['accent_green'],
            troughcolor=cls.COLORS['bg_tertiary'],
            borderwidth=0,
            lightcolor=cls.COLORS['accent_green'],
            darkcolor=cls.COLORS['accent_green']
        )
        
        # Frame styles
        style.configure("Dark.TFrame", background=cls.COLORS['bg_primary'])
        
        return style
