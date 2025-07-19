import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import requests
import re
import os
import json
from PIL import Image, ImageTk
import io

class YouTube4KCheckerSimple:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 4K Video Checker (Service Account)")
        self.root.geometry("1200x900")
        
        # Dark theme colors
        self.colors = {
            'bg_primary': '#1e1e1e',
            'bg_secondary': '#2d2d2d',
            'bg_tertiary': '#3c3c3c',
            'text_primary': '#ffffff',
            'text_secondary': '#b3b3b3',
            'accent_blue': '#0078d4',
            'accent_green': '#107c10',
            'accent_orange': '#ff8c00',
            'accent_red': '#d13438',
            'accent_purple': '#8b5cf6',
            'border': '#404040'
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure ttk styles for dark theme
        self.setup_dark_theme()
        
        # API Key - Buraya kendi API key'inizi yazın
        self.API_KEY = 'AIzaSyA3hWhKJmy2_0A7cfbB46va3XWsq-SeV2E'
        self.youtube = build('youtube', 'v3', developerKey=self.API_KEY)
        
        # Service Account Authentication
        self.service_account_file = os.path.join(os.path.dirname(__file__), 'service_account.json')
        self.authenticated_youtube = None
        self.is_authenticated = False
        
        # Try to authenticate with service account
        self.try_service_account_auth()
        
        # İşlem durumu
        self.is_processing = False
        self.stop_requested = False
        self.found_4k_videos = []
        self.thumbnail_cache = {}
        self.thumbnail_refs = []
        
        self.create_widgets()
    
    def try_service_account_auth(self):
        """Service Account ile authentication dene"""
        try:
            if os.path.exists(self.service_account_file):
                credentials = Credentials.from_service_account_file(
                    self.service_account_file,
                    scopes=['https://www.googleapis.com/auth/youtube']
                )
                self.authenticated_youtube = build('youtube', 'v3', credentials=credentials)
                self.is_authenticated = True
                print("Service Account authentication successful!")
            else:
                print(f"Service account file not found: {self.service_account_file}")
        except Exception as e:
            print(f"Service Account authentication failed: {e}")
            self.is_authenticated = False

# Not: Bu simplified version OAuth2 user flow olmadan çalışır
# Sadece public playlist'leri okuyabilir, user'ın kendi playlist'lerini değiştiremez
