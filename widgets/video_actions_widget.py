import tkinter as tk
from tkinter import ttk


class VideoActionsWidget:
    """Encapsulates the 'Video Actions' button group as a reusable widget."""

    def __init__(self, parent, colors, commands):
        self.colors = colors
        self.commands = commands or {}

        # Outer container
        self.frame = tk.Frame(
            parent,
            bg=self.colors['bg_secondary'],
            bd=0,
            relief='flat'
        )

        # Title
        title = tk.Label(
            self.frame,
            text="Video Actions",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        title.pack(pady=(12, 8))

        # Button frame
        button_frame = ttk.Frame(self.frame, style='Dark.TFrame')
        button_frame.pack(pady=(0, 12), padx=12, fill='x')

        # Row 1 — Selection
        self.check_all_btn = ttk.Button(
            button_frame,
            text="Select All",
            command=self.commands.get('check_all'),
            style='Neon.TButton',
            state='disabled'
        )
        self.check_all_btn.grid(row=0, column=0, padx=(0, 4), pady=(0, 6), sticky='ew')

        self.uncheck_all_btn = ttk.Button(
            button_frame,
            text="Select None",
            command=self.commands.get('uncheck_all'),
            style='Dark.TButton',
            state='disabled'
        )
        self.uncheck_all_btn.grid(row=0, column=1, padx=(4, 0), pady=(0, 6), sticky='ew')

        # Row 2 — Smart selection
        self.check_4k_only_btn = ttk.Button(
            button_frame,
            text="Select 4K Only",
            command=self.commands.get('check_4k_only'),
            style='Gradient.TButton',
            state='disabled'
        )
        self.check_4k_only_btn.grid(row=1, column=0, columnspan=2, padx=0, pady=(0, 6), sticky='ew')

        # Row 3 — Actions (Copy + Remove from List)
        self.copy_btn = ttk.Button(
            button_frame,
            text="Copy URLs",
            command=self.commands.get('copy_urls'),
            style='Neon.TButton',
            state='disabled'
        )
        self.copy_btn.grid(row=2, column=0, padx=(0, 4), pady=0, sticky='ew')

        self.remove_from_list_btn = ttk.Button(
            button_frame,
            text="Remove from List",
            command=self.commands.get('remove_from_list'),
            style='Warning.TButton',
            state='disabled'
        )
        self.remove_from_list_btn.grid(row=2, column=1, padx=(4, 0), pady=0, sticky='ew')

        # Row 4 — YouTube removal (red)
        self.remove_from_youtube_btn = ttk.Button(
            button_frame,
            text="Remove from YouTube",
            command=self.commands.get('remove_from_youtube'),
            style='Danger.TButton',
            state='disabled'
        )
        self.remove_from_youtube_btn.grid(row=3, column=0, columnspan=2, padx=0, pady=(6, 0), sticky='ew')

        # Equal columns
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
