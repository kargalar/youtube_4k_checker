"""
UI coordination and state management service
Handles UI state synchronization and thread-safe updates
"""
import tkinter as tk
from tkinter import ttk
import threading
from datetime import datetime

class UIManager:
    """Manages UI state and provides thread-safe update methods"""
    
    def __init__(self, root):
        self.root = root
        self.ui_lock = threading.Lock()
        self._ui_elements = {}
        self._state = {
            'is_checking': False,
            'is_loading': False,
            'current_operation': None,
            'last_update': None
        }
    
    def register_element(self, name, element):
        """Register a UI element for managed updates"""
        self._ui_elements[name] = element
    
    def get_element(self, name):
        """Get a registered UI element"""
        return self._ui_elements.get(name)
    
    def safe_update(self, update_func, *args, **kwargs):
        """Execute UI update safely on main thread"""
        def wrapper():
            try:
                with self.ui_lock:
                    update_func(*args, **kwargs)
            except Exception as e:
                print(f"UI update error: {e}")
        
        self.root.after(0, wrapper)
    
    def update_status(self, message, color=None):
        """Update status bar message"""
        def do_update():
            status_label = self._ui_elements.get('status_label')
            if status_label:
                status_label.config(text=message)
                if color:
                    status_label.config(foreground=color)
                self._state['last_update'] = datetime.now()
        
        self.safe_update(do_update)
    
    def update_progress(self, current, total, operation=None):
        """Update progress bar and related UI"""
        def do_update():
            progress_bar = self._ui_elements.get('progress_bar')
            progress_label = self._ui_elements.get('progress_label')
            
            if progress_bar:
                if total > 0:
                    percentage = (current / total) * 100
                    progress_bar.config(value=percentage)
                else:
                    progress_bar.config(value=0)
            
            if progress_label:
                text = f"{current}/{total}"
                if operation:
                    text = f"{operation}: {text}"
                progress_label.config(text=text)
        
        self.safe_update(do_update)
    
    def set_checking_state(self, is_checking):
        """Update UI elements based on checking state"""
        def do_update():
            self._state['is_checking'] = is_checking
            
            # Update buttons
            check_button = self._ui_elements.get('check_button')
            stop_button = self._ui_elements.get('stop_button')
            
            if check_button:
                check_button.config(state='disabled' if is_checking else 'normal')
            
            if stop_button:
                stop_button.config(state='normal' if is_checking else 'disabled')
            
            # Update progress bar visibility
            progress_frame = self._ui_elements.get('progress_frame')
            if progress_frame:
                if is_checking:
                    progress_frame.pack(fill='x', padx=5, pady=2)
                else:
                    progress_frame.pack_forget()
        
        self.safe_update(do_update)
    
    def set_loading_state(self, is_loading):
        """Update UI for loading state"""
        def do_update():
            self._state['is_loading'] = is_loading
            
            # Update input controls
            url_entry = self._ui_elements.get('url_entry')
            load_button = self._ui_elements.get('load_button')
            
            if url_entry:
                url_entry.config(state='disabled' if is_loading else 'normal')
            
            if load_button:
                load_button.config(state='disabled' if is_loading else 'normal')
        
        self.safe_update(do_update)
    
    def update_video_item(self, tree, item_id, column, value):
        """Update a specific tree item column"""
        def do_update():
            try:
                if tree.exists(item_id):
                    tree.set(item_id, column, value)
            except Exception as e:
                print(f"Error updating tree item: {e}")
        
        self.safe_update(do_update)
    
    def clear_tree(self, tree):
        """Clear all items from tree"""
        def do_update():
            try:
                for item in tree.get_children():
                    tree.delete(item)
            except Exception as e:
                print(f"Error clearing tree: {e}")
        
        self.safe_update(do_update)
    
    def add_tree_item(self, tree, parent, **kwargs):
        """Add item to tree safely"""
        item_id = None
        
        def do_update():
            nonlocal item_id
            try:
                item_id = tree.insert(parent, 'end', **kwargs)
            except Exception as e:
                print(f"Error adding tree item: {e}")
        
        # Execute and wait for completion
        event = threading.Event()
        
        def wrapper():
            do_update()
            event.set()
        
        self.root.after(0, wrapper)
        event.wait(timeout=1.0)  # Wait max 1 second
        
        return item_id
    
    def batch_update_tree(self, tree, updates):
        """Perform multiple tree updates in batch"""
        def do_update():
            try:
                for update in updates:
                    action = update.get('action')
                    
                    if action == 'insert':
                        tree.insert(
                            update['parent'], 
                            update.get('index', 'end'), 
                            **update.get('kwargs', {})
                        )
                    elif action == 'set':
                        item_id = update['item']
                        column = update['column']
                        value = update['value']
                        if tree.exists(item_id):
                            tree.set(item_id, column, value)
                    elif action == 'delete':
                        item_id = update['item']
                        if tree.exists(item_id):
                            tree.delete(item_id)
                            
            except Exception as e:
                print(f"Error in batch tree update: {e}")
        
        self.safe_update(do_update)
    
    def show_message_dialog(self, title, message, msg_type='info'):
        """Show message dialog safely"""
        def do_update():
            try:
                from tkinter import messagebox
                
                if msg_type == 'info':
                    messagebox.showinfo(title, message)
                elif msg_type == 'warning':
                    messagebox.showwarning(title, message)
                elif msg_type == 'error':
                    messagebox.showerror(title, message)
                else:
                    messagebox.showinfo(title, message)
                    
            except Exception as e:
                print(f"Error showing dialog: {e}")
        
        self.safe_update(do_update)
    
    def get_state(self):
        """Get current UI state"""
        return self._state.copy()
    
    def reset_state(self):
        """Reset UI state to defaults"""
        self._state = {
            'is_checking': False,
            'is_loading': False,
            'current_operation': None,
            'last_update': None
        }
        
        # Reset UI elements
        self.set_checking_state(False)
        self.set_loading_state(False)
        self.update_status("Ready")
    
    def configure_scrollbar(self, scrollbar, widget):
        """Configure scrollbar for widget safely"""
        def do_update():
            try:
                scrollbar.config(command=widget.yview)
                widget.config(yscrollcommand=scrollbar.set)
            except Exception as e:
                print(f"Error configuring scrollbar: {e}")
        
        self.safe_update(do_update)
