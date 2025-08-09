import tkinter as tk
from tkinter import ttk


class InlineVideoListWidget:
    """Video List with inline thumbnails using Treeview #0 column."""

    def __init__(self, parent, colors):
        self.colors = colors
        # Container
        self.frame = tk.Frame(
            parent,
            bg=self.colors['bg_primary'],
            bd=1,
            relief='solid',
            highlightbackground=self.colors['border'],
            highlightthickness=1,
        )
        self._build()

    def _build(self):
        tree_frame = ttk.Frame(self.frame, style='Dark.TFrame')
        tree_frame.pack(fill='both', expand=True, padx=1, pady=1)

        columns = ('Check', 'No', 'Title', 'Quality', 'Status')
        self.video_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='tree headings',
            height=20,
            style='Dark.Treeview',
        )
        # Headers
        self.video_tree.heading('#0', text='🖼️')
        headers = {
            'Check': '☑️ Select',
            'No': '#️⃣ No',
            'Title': '🎬 Video Title',
            'Quality': '📺 Quality',
            'Status': '✨ 4K Status',
        }
        for col, text in headers.items():
            self.video_tree.heading(col, text=text)
        # Widths
        self.video_tree.column('#0', width=90, minwidth=90, anchor='center')
        widths = {
            'Check': (60, 60),
            'No': (50, 50),
            'Title': (450, 200),
            'Quality': (100, 100),
            'Status': (140, 140),
        }
        for col, (w, m) in widths.items():
            self.video_tree.column(col, width=w, minwidth=m)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        self.video_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
