import tkinter as tk
from tkinter import ttk

class LimitFilterWidget:
    """Encapsulates Video Limit controls and the 4K filter block.
    Exposes attributes for backward-compatibility:
      - video_limit_var, limit_slider, limit_entry, all_videos_var, all_videos_check
      - show_4k_only_var, show_4k_only_check, filter_status_label
    """

    def __init__(self, parent, colors,
                 on_slider_change=None,
                 on_entry_change=None,
                 on_all_videos_toggle=None,
                 on_4k_filter_toggle=None):
        self.colors = colors
        self.on_slider_change = on_slider_change
        self.on_entry_change = on_entry_change
        self.on_all_videos_toggle = on_all_videos_toggle
        self.on_4k_filter_toggle = on_4k_filter_toggle

        self.frame = ttk.Frame(parent, style='Dark.TFrame')

        # Section title
        limit_section = tk.Label(
            self.frame,
            text="Video Limit",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        limit_section.pack(anchor='w', pady=(0, 8))

        # Video count limit container
        limit_frame = ttk.Frame(self.frame, style='Dark.TFrame')
        limit_frame.pack(pady=(0, 8), fill='x')

        ttk.Label(limit_frame, text="Maximum video count:",
                  font=('Segoe UI', 11, 'bold'), style='Dark.TLabel').pack(anchor='w', pady=(0, 5))

        # Slider + Entry row
        slider_frame = ttk.Frame(limit_frame, style='Dark.TFrame')
        slider_frame.pack(fill='x', pady=(0, 10))

        # Slider (10-1000)
        self.video_limit_var = tk.IntVar(value=200)
        self.limit_slider = tk.Scale(slider_frame, from_=10, to=1000,
                                     orient='horizontal', variable=self.video_limit_var,
                                     bg=self.colors['bg_secondary'],
                                     fg=self.colors['text_primary'],
                                     highlightbackground=self.colors['bg_primary'],
                                     troughcolor=self.colors['bg_tertiary'],
                                     activebackground=self.colors['accent_blue'],
                                     font=('Segoe UI', 9),
                                     command=self._on_slider_change)
        self.limit_slider.pack(side='left', fill='x', expand=True, padx=(0, 10))

        # Entry box
        entry_frame = ttk.Frame(slider_frame, style='Dark.TFrame')
        entry_frame.pack(side='right')

        self.limit_entry = ttk.Entry(entry_frame, font=('Segoe UI', 11), width=8,
                                     textvariable=self.video_limit_var, style='Dark.TEntry')
        self.limit_entry.pack(side='left')
        if self.on_entry_change:
            self.limit_entry.bind('<KeyRelease>', self.on_entry_change)

        # "All" checkbox
        self.all_videos_var = tk.BooleanVar(value=False)
        self.all_videos_check = tk.Checkbutton(entry_frame, text="All",
                                               variable=self.all_videos_var,
                                               command=self._on_all_videos_toggle,
                                               bg=self.colors['bg_secondary'],
                                               fg=self.colors['text_primary'],
                                               font=('Segoe UI', 10),
                                               activebackground=self.colors['bg_secondary'],
                                               activeforeground=self.colors['text_primary'],
                                               selectcolor=self.colors['bg_tertiary'])
        self.all_videos_check.pack(side='right', padx=(10, 0))

        # Filter block
        filter_frame = ttk.Frame(limit_frame, style='Dark.TFrame')
        filter_frame.pack(fill='x', pady=(10, 0))

        filter_container = tk.Frame(
            filter_frame,
            bg=self.colors['bg_tertiary'],
            bd=2,
            relief='solid'
        )
        filter_container.pack(fill='x', pady=(0, 5))

        filter_inner = ttk.Frame(filter_container, style='Dark.TFrame')
        filter_inner.pack(fill='x', padx=10, pady=8)

        # Left side icon/label
        filter_left = ttk.Frame(filter_inner, style='Dark.TFrame')
        filter_left.pack(side='left')
        tk.Label(
            filter_left,
            text="✨ 4K Filter:",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['bg_tertiary'],
            fg=self.colors['accent_cyan']
        ).pack(side='left')

        # Right side switch + status
        filter_right = ttk.Frame(filter_inner, style='Dark.TFrame')
        filter_right.pack(side='right')

        self.show_4k_only_var = tk.BooleanVar(value=True)
        self.show_4k_only_check = tk.Checkbutton(
            filter_right,
            text="Show Only 4K Videos",
            variable=self.show_4k_only_var,
            command=self._on_4k_filter_toggle,
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            font=('Segoe UI', 10, 'bold'),
            activebackground=self.colors['bg_tertiary'],
            activeforeground=self.colors['accent_green'],
            selectcolor=self.colors['accent_green'],
            relief='flat',
            bd=0
        )
        self.show_4k_only_check.pack(side='right')

        self.filter_status_label = tk.Label(
            filter_right,
            text="🟢 Active",
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['bg_tertiary'],
            fg=self.colors['accent_green']
        )
        self.filter_status_label.pack(side='right', padx=(0, 10))

    # Internal adapters to call host callbacks
    def _on_slider_change(self, value):
        if self.on_slider_change:
            self.on_slider_change(value)

    def _on_all_videos_toggle(self):
        if self.on_all_videos_toggle:
            self.on_all_videos_toggle()

    def _on_4k_filter_toggle(self):
        """Handle 4K filter toggle: update status label/colors and notify host callback."""
        try:
            is_active = bool(self.show_4k_only_var.get())
            # Update status label and checkbox color
            if is_active:
                self.filter_status_label.config(text="🟢 Active", fg=self.colors['accent_green'])
                try:
                    self.show_4k_only_check.config(fg=self.colors['accent_green'])
                except Exception:
                    pass
            else:
                self.filter_status_label.config(text="🔴 Inactive", fg=self.colors['accent_red'])
                try:
                    self.show_4k_only_check.config(fg=self.colors['text_secondary'])
                except Exception:
                    pass
        except Exception:
            # Silent fail; still propagate callback
            pass

        if self.on_4k_filter_toggle:
            self.on_4k_filter_toggle()

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
