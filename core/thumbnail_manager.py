"""
Thumbnail management service
Handles downloading, caching and processing of video thumbnails
"""
import os
import requests
import threading
from PIL import Image, ImageTk
from io import BytesIO
import time

class ThumbnailManager:
    """Service for managing video thumbnails"""
    
    def __init__(self, cache_dir="thumbnails", max_cache_size=100):
        self.cache_dir = cache_dir
        self.max_cache_size = max_cache_size
        self.thumbnail_cache = {}
        self.cache_lock = threading.Lock()
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure thumbnail cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_cache_path(self, video_id):
        """Get cache file path for video thumbnail"""
        return os.path.join(self.cache_dir, f"{video_id}.jpg")
    
    def download_thumbnail(self, video_id, thumbnail_url):
        """Download thumbnail image for video"""
        try:
            cache_path = self.get_cache_path(video_id)
            
            # Check if already cached
            if os.path.exists(cache_path):
                return cache_path
            
            # Download thumbnail
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(thumbnail_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Save to cache
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                
                return cache_path
            
            return None
            
        except Exception as e:
            print(f"Error downloading thumbnail for {video_id}: {e}")
            return None
    
    def get_thumbnail_image(self, video_id, thumbnail_url, size=(50, 50)):
        """Get processed thumbnail image for display"""
        try:
            with self.cache_lock:
                # Check memory cache first
                cache_key = f"{video_id}_{size[0]}x{size[1]}"
                if cache_key in self.thumbnail_cache:
                    return self.thumbnail_cache[cache_key]
            
            # Download or get from disk cache
            cache_path = self.download_thumbnail(video_id, thumbnail_url)
            
            if cache_path and os.path.exists(cache_path):
                # Load and process image
                image = Image.open(cache_path)
                
                # Resize to fit
                image.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Convert for Tkinter
                photo = ImageTk.PhotoImage(image)
                
                # Cache in memory
                with self.cache_lock:
                    # Manage cache size
                    if len(self.thumbnail_cache) >= self.max_cache_size:
                        # Remove oldest entry
                        oldest_key = next(iter(self.thumbnail_cache))
                        del self.thumbnail_cache[oldest_key]
                    
                    self.thumbnail_cache[cache_key] = photo
                
                return photo
            
            return None
            
        except Exception as e:
            print(f"Error processing thumbnail for {video_id}: {e}")
            return None
    
    def download_thumbnails_batch(self, videos, progress_callback=None):
        """Download thumbnails for multiple videos"""
        downloaded = 0
        total = len(videos)
        
        for video in videos:
            try:
                video_id = video['id']
                thumbnail_url = video.get('thumbnail', '')
                
                if thumbnail_url:
                    cache_path = self.download_thumbnail(video_id, thumbnail_url)
                    if cache_path:
                        downloaded += 1
                
                if progress_callback:
                    progress_callback(downloaded, total)
                    
            except Exception as e:
                print(f"Error in batch thumbnail download: {e}")
        
        return downloaded
    
    def clear_cache(self):
        """Clear thumbnail cache"""
        try:
            # Clear memory cache
            with self.cache_lock:
                self.thumbnail_cache.clear()
            
            # Clear disk cache
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    file_path = os.path.join(self.cache_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            
            print("Thumbnail cache cleared")
            
        except Exception as e:
            print(f"Error clearing cache: {e}")
    
    def get_cache_stats(self):
        """Get cache statistics"""
        memory_count = len(self.thumbnail_cache)
        
        disk_count = 0
        disk_size = 0
        
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    disk_count += 1
                    disk_size += os.path.getsize(file_path)
        
        return {
            'memory_cached': memory_count,
            'disk_cached': disk_count,
            'disk_size_mb': disk_size / (1024 * 1024),
            'cache_dir': self.cache_dir
        }
    
    def preload_thumbnails(self, videos, callback=None):
        """Preload thumbnails in background thread"""
        def preload_worker():
            try:
                for i, video in enumerate(videos):
                    video_id = video['id']
                    thumbnail_url = video.get('thumbnail', '')
                    
                    if thumbnail_url:
                        # Download thumbnail
                        self.download_thumbnail(video_id, thumbnail_url)
                        
                        # Prepare display image
                        self.get_thumbnail_image(video_id, thumbnail_url)
                    
                    if callback:
                        callback(i + 1, len(videos))
                        
                    # Small delay to avoid overwhelming
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Error in thumbnail preload: {e}")
        
        thread = threading.Thread(target=preload_worker, daemon=True)
        thread.start()
        return thread
