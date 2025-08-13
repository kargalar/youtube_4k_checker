"""
UI Widget Factory
Creates and manages UI components
"""
import tkinter as tk
from tkinter import ttk

class WidgetFactory:
    """Factory class for creating UI widgets with consistent styling"""
    
    def __init__(self, theme_config):
        self.theme = theme_config
        self.colors = theme_config.COLORS
    
    def create_auth_widget(self, parent):
        """Create authentication widget"""
        # Ana frame
        auth_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        auth_frame.pack(fill='x', padx=10, pady=5)
        
        # Header frame
        header_frame = tk.Frame(auth_frame, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(0, 5))
        
        # Auth icon and title
        auth_icon = tk.Label(
            header_frame, 
            text="🔐",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 14)
        )
        auth_icon.pack(side='left', padx=(5, 10))
        
        title_label = tk.Label(
            header_frame,
            text="YouTube Authentication",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 11, 'bold')
        )
        title_label.pack(side='left')
        
        # Status frame
        status_frame = tk.Frame(auth_frame, bg=self.colors['bg_secondary'])
        status_frame.pack(fill='x', pady=2)
        
        # Status label
        status_label = tk.Label(
            status_frame,
            text="Not authenticated",
            bg=self.colors['bg_secondary'],
            fg=self.colors['accent_orange'],
            font=('Segoe UI', 9)
        )
        status_label.pack(side='left', padx=(25, 10))
        
        # Button frame
        button_frame = tk.Frame(auth_frame, bg=self.colors['bg_secondary'])
        button_frame.pack(fill='x', pady=(5, 0))
        
        # Login button
        login_button = ttk.Button(
            button_frame,
            text="🔑 Login with Google",
            style='Accent.TButton'
        )
        login_button.pack(side='left', padx=(25, 5))
        
        # Logout button
        logout_button = ttk.Button(
            button_frame,
            text="🚪 Logout",
            style='Secondary.TButton'
        )
        logout_button.pack(side='left', padx=5)
        
        return {
            'frame': auth_frame,
            'status_label': status_label,
            'login_button': login_button,
            'logout_button': logout_button
        }
    
    def create_playlist_input_widget(self, parent):
        """Create playlist URL input widget"""
        # Ana frame
        input_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        input_frame.pack(fill='x', padx=10, pady=5)
        
        # Header
        header_frame = tk.Frame(input_frame, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(0, 8))
        
        # Title with icon
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        title_frame.pack(side='left')
        
        icon_label = tk.Label(
            title_frame,
            text="📋",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 14)
        )
        icon_label.pack(side='left', padx=(5, 8))
        
        title_label = tk.Label(
            title_frame,
            text="Playlist URL",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 11, 'bold')
        )
        title_label.pack(side='left')
        
        # Playlist info
        info_label = tk.Label(
            header_frame,
            text="No playlist loaded",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary'],
            font=('Segoe UI', 9)
        )
        info_label.pack(side='right', padx=(0, 5))
        
        # URL input frame
        url_frame = tk.Frame(input_frame, bg=self.colors['bg_secondary'])
        url_frame.pack(fill='x', pady=(0, 5))
        
        # URL entry
        url_entry = ttk.Entry(
            url_frame,
            font=('Segoe UI', 10),
            style='Modern.TEntry'
        )
        url_entry.pack(side='left', fill='x', expand=True, padx=(5, 5))
        
        # Paste button
        paste_button = ttk.Button(
            url_frame,
            text="📋",
            width=3,
            style='Tool.TButton'
        )
        paste_button.pack(side='right', padx=(0, 5))
        
        # Load button
        load_button = ttk.Button(
            url_frame,
            text="🚀 Load Playlist",
            style='Accent.TButton'
        )
        load_button.pack(side='right', padx=(0, 5))

        # Options row
        options_frame = tk.Frame(input_frame, bg=self.colors['bg_secondary'])
        options_frame.pack(fill='x', pady=(2, 0))

        auto_check_4k = tk.BooleanVar(value=True)
        auto_check_4k_check = ttk.Checkbutton(
            options_frame,
            text="Auto check 4K on load",
            variable=auto_check_4k,
            style='Modern.TCheckbutton'
        )
        auto_check_4k_check.pack(side='left', padx=(5, 5))
        
        return {
            'frame': input_frame,
            'url_entry': url_entry,
            'paste_button': paste_button,
            'load_button': load_button,
            'info_label': info_label,
            'auto_check_4k': auto_check_4k,
            'auto_check_4k_check': auto_check_4k_check
        }
    
    def create_main_button_group(self, parent):
        """Create main control buttons"""
        # Ana frame
        button_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        button_frame.pack(fill='x', padx=10, pady=5)
        
        # Header
        header_frame = tk.Frame(button_frame, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(0, 8))
        
        icon_label = tk.Label(
            header_frame,
            text="⚡",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 14)
        )
        icon_label.pack(side='left', padx=(5, 8))
        
        title_label = tk.Label(
            header_frame,
            text="4K Checker Controls",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 11, 'bold')
        )
        title_label.pack(side='left')
        
        # Button container
        controls_frame = tk.Frame(button_frame, bg=self.colors['bg_secondary'])
        controls_frame.pack(fill='x', padx=5)
        
        # Check 4K button
        check_button = ttk.Button(
            controls_frame,
            text="🔍 Check 4K Quality",
            style='Success.TButton'
        )
        check_button.pack(side='left', padx=(0, 10))
        
        # Stop button
        stop_button = ttk.Button(
            controls_frame,
            text="⏹️ Stop",
            style='Danger.TButton',
            state='disabled'
        )
        stop_button.pack(side='left', padx=(0, 15))
        
        # Progress frame (hidden initially)
        progress_frame = tk.Frame(controls_frame, bg=self.colors['bg_secondary'])
        
        progress_label = tk.Label(
            progress_frame,
            text="0/0",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary'],
            font=('Segoe UI', 9)
        )
        progress_label.pack(side='left', padx=(0, 8))
        
        progress_bar = ttk.Progressbar(
            progress_frame,
            length=200,
            mode='determinate',
            style='Modern.Horizontal.TProgressbar'
        )
        progress_bar.pack(side='left')
        
        return {
            'frame': button_frame,
            'check_button': check_button,
            'stop_button': stop_button,
            'progress_frame': progress_frame,
            'progress_label': progress_label,
            'progress_bar': progress_bar
        }
    
    def create_action_button_group(self, parent):
        """Create action buttons for video operations"""
        # Ana frame
        action_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        action_frame.pack(fill='x', padx=10, pady=5)
        
        # Header
        header_frame = tk.Frame(action_frame, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(0, 8))
        
        icon_label = tk.Label(
            header_frame,
            text="🎬",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 14)
        )
        icon_label.pack(side='left', padx=(5, 8))
        
        title_label = tk.Label(
            header_frame,
            text="Video Actions",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 11, 'bold')
        )
        title_label.pack(side='left')
        
        # Selection controls frame
        selection_frame = tk.Frame(action_frame, bg=self.colors['bg_secondary'])
        selection_frame.pack(fill='x', padx=5, pady=(0, 5))
        
        # Check all button
        check_all_button = ttk.Button(
            selection_frame,
            text="☑️ Check All",
            style='Tool.TButton'
        )
        check_all_button.pack(side='left', padx=(0, 5))
        
        # Uncheck all button
        uncheck_all_button = ttk.Button(
            selection_frame,
            text="☐ Uncheck All",
            style='Tool.TButton'
        )
        uncheck_all_button.pack(side='left', padx=(0, 5))
        
        # Check 4K only button
        check_4k_button = ttk.Button(
            selection_frame,
            text="✅ 4K Only",
            style='Tool.TButton'
        )
        check_4k_button.pack(side='left', padx=(0, 15))
        
        # Copy URLs button
        copy_button = ttk.Button(
            selection_frame,
            text="📋 Copy URLs",
            style='Info.TButton',
            state='disabled'
        )
        copy_button.pack(side='left', padx=(0, 10))
        
        # Remove buttons frame
        remove_frame = tk.Frame(action_frame, bg=self.colors['bg_secondary'])
        remove_frame.pack(fill='x', padx=5)
        
        # Remove from list button
        remove_list_button = ttk.Button(
            remove_frame,
            text="🗑️ Remove from List",
            style='Warning.TButton',
            state='disabled'
        )
        remove_list_button.pack(side='left', padx=(0, 5))
        
        # Remove from YouTube button
        remove_youtube_button = ttk.Button(
            remove_frame,
            text="❌ Remove from YouTube",
            style='Danger.TButton',
            state='disabled'
        )
        remove_youtube_button.pack(side='left')
        
        return {
            'frame': action_frame,
            'check_all_button': check_all_button,
            'uncheck_all_button': uncheck_all_button,
            'check_4k_button': check_4k_button,
            'copy_button': copy_button,
            'remove_list_button': remove_list_button,
            'remove_youtube_button': remove_youtube_button
        }
    
    def create_status_bar(self, parent):
        """Create status bar widget"""
        # Status frame
        status_frame = tk.Frame(parent, bg=self.colors['bg_tertiary'], height=30)
        status_frame.pack(fill='x', side='bottom')
        status_frame.pack_propagate(False)
        
        # Status content frame
        content_frame = tk.Frame(status_frame, bg=self.colors['bg_tertiary'])
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Status label
        status_label = tk.Label(
            content_frame,
            text="Ready",
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_secondary'],
            font=('Segoe UI', 9),
            anchor='w'
        )
        status_label.pack(side='left', fill='x', expand=True)
        
        # Video count label
        count_label = tk.Label(
            content_frame,
            text="0 videos",
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_secondary'],
            font=('Segoe UI', 9)
        )
        count_label.pack(side='right')
        
        return {
            'frame': status_frame,
            'status_label': status_label,
            'count_label': count_label
        }
    
    def create_filter_controls(self, parent):
        """Create filter and control widgets"""
        # Filter frame
        filter_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        # Header
        header_frame = tk.Frame(filter_frame, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(0, 8))
        
        icon_label = tk.Label(
            header_frame,
            text="🔧",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 14)
        )
        icon_label.pack(side='left', padx=(5, 8))
        
        title_label = tk.Label(
            header_frame,
            text="Filters & Settings",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 11, 'bold')
        )
        title_label.pack(side='left')
        
        # Controls frame
        controls_frame = tk.Frame(filter_frame, bg=self.colors['bg_secondary'])
        controls_frame.pack(fill='x', padx=5)
        
        # Max results frame
        max_frame = tk.Frame(controls_frame, bg=self.colors['bg_secondary'])
        max_frame.pack(side='left', padx=(0, 20))
        
        max_label = tk.Label(
            max_frame,
            text="Max Videos:",
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 9)
        )
        max_label.pack(side='left', padx=(0, 5))
        
        max_entry = ttk.Entry(
            max_frame,
            width=5,
            font=('Segoe UI', 9),
            style='Modern.TEntry'
        )
        max_entry.pack(side='left', padx=(0, 5))
        max_entry.insert(0, "50")
        
        max_slider = ttk.Scale(
            max_frame,
            from_=10,
            to=500,
            orient='horizontal',
            length=100,
            style='Modern.Horizontal.TScale'
        )
        max_slider.pack(side='left')
        max_slider.set(50)
        
        # Toggle frame
        toggle_frame = tk.Frame(controls_frame, bg=self.colors['bg_secondary'])
        toggle_frame.pack(side='left')
        
        # All videos toggle
        all_videos_var = tk.BooleanVar(value=True)
        all_videos_check = ttk.Checkbutton(
            toggle_frame,
            text="Show all videos",
            variable=all_videos_var,
            style='Modern.TCheckbutton'
        )
        all_videos_check.pack(side='left', padx=(0, 10))
        
        # 4K filter toggle
        filter_4k_var = tk.BooleanVar(value=False)
        filter_4k_check = ttk.Checkbutton(
            toggle_frame,
            text="Show only 4K",
            variable=filter_4k_var,
            style='Accent.TCheckbutton'
        )
        filter_4k_check.pack(side='left')
        
        return {
            'frame': filter_frame,
            'max_entry': max_entry,
            'max_slider': max_slider,
            'all_videos_var': all_videos_var,
            'all_videos_check': all_videos_check,
            'filter_4k_var': filter_4k_var,
            'filter_4k_check': filter_4k_check
        }
