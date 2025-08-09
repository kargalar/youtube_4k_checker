import tkinter as tk
from tkinter import ttk

class MainActionsWidget:
    """Encapsulates the primary action buttons: Get Videos, Stop, Clear.
    Exposes button attributes for compatibility: get_videos_btn, stop_btn, clear_btn.
    """
    def __init__(self, parent, colors, callbacks):
        self.colors = colors
        self.callbacks = callbacks or {}
        self.frame = tk.Frame(
            parent,
            bg=self.colors['bg_secondary'],
            bd=0,
            relief='flat'
        )

        # Title
        title = tk.Label(
            self.frame,
            text="Primary Actions",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        title.pack(pady=(12, 8))

        # Buttons area
        button_frame = ttk.Frame(self.frame, style='Dark.TFrame')
        button_frame.pack(pady=(0, 12), padx=12, fill='x')

        # Get Videos (prominent)
        self.get_videos_btn = ttk.Button(
            button_frame,
            text="Get Videos & Check 4K",
            command=self.callbacks.get('get_videos'),
            style='Success.TButton'
        )
        self.get_videos_btn.grid(row=0, column=0, columnspan=2, padx=0, pady=(0, 8), sticky='ew')

        # Stop button
        self.stop_btn = ttk.Button(
            button_frame,
            text="Stop",
            command=self.callbacks.get('stop'),
            style='Danger.TButton',
            state='disabled'
        )
        self.stop_btn.grid(row=1, column=0, padx=(0, 4), pady=0, sticky='ew')

        # Clear button
        self.clear_btn = ttk.Button(
            button_frame,
            text="Clear All",
            command=self.callbacks.get('clear'),
            style='Dark.TButton'
        )
        self.clear_btn.grid(row=1, column=1, padx=(4, 0), pady=0, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
