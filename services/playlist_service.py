"""
Playlist service operations
Handles all playlist-related functionality
"""
import re
import requests
import threading
from googleapiclient.discovery import build
import google.auth.exceptions

class PlaylistService:
    """Service for handling YouTube playlist operations"""
    
    def __init__(self, youtube_service=None):
        self.youtube_service = youtube_service
        self.current_playlist_info = None
    
    def extract_playlist_id(self, playlist_url):
        """Extract playlist ID from YouTube URL"""
        try:
            # Various YouTube playlist URL formats
            patterns = [
                r'[?&]list=([a-zA-Z0-9_-]+)',
                r'playlist\?list=([a-zA-Z0-9_-]+)',
                r'/playlist/([a-zA-Z0-9_-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, playlist_url)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"Error extracting playlist ID: {e}")
            return None
    
    def is_valid_playlist_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube playlist URL"""
        try:
            playlist_patterns = [
                r'youtube\.com/playlist\?list=',
                r'youtube\.com/watch\?.*list=',
                r'youtu\.be/.*list='
            ]
            
            for pattern in playlist_patterns:
                if re.search(pattern, url):
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error validating playlist URL: {e}")
            return False
    
    def get_playlist_info(self, playlist_id):
        """Get playlist information from YouTube API"""
        try:
            if not self.youtube_service:
                return None
            
            request = self.youtube_service.playlists().list(
                part='snippet,contentDetails',
                id=playlist_id
            )
            response = request.execute()
            
            if response.get('items'):
                playlist = response['items'][0]
                snippet = playlist['snippet']
                content_details = playlist['contentDetails']
                
                return {
                    'id': playlist_id,
                    'title': snippet['title'],
                    'description': snippet.get('description', ''),
                    'channel_title': snippet['channelTitle'],
                    'published_at': snippet['publishedAt'],
                    'video_count': content_details['itemCount'],
                    'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                }
            
            return None
            
        except google.auth.exceptions.RefreshError:
            print("Authentication expired. Please re-authenticate.")
            return None
        except Exception as e:
            print(f"Error getting playlist info: {e}")
            return None
    
    def update_playlist_info_async(self, playlist_id, callback=None):
        """Update playlist info in background thread"""
        def update_worker():
            try:
                info = self.get_playlist_info(playlist_id)
                self.current_playlist_info = info
                
                if callback and info:
                    callback(info)
                    
            except Exception as e:
                print(f"Error in playlist info update: {e}")
                if callback:
                    callback(None)
        
        thread = threading.Thread(target=update_worker, daemon=True)
        thread.start()
        return thread
    
    def get_playlist_videos(self, playlist_id, max_results=50):
        """Get videos from playlist"""
        try:
            if not self.youtube_service:
                return []
            
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                request = self.youtube_service.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                # Process videos
                for item in response.get('items', []):
                    snippet = item['snippet']
                    video_id = snippet['resourceId']['videoId']
                    
                    video_info = {
                        'id': video_id,
                        'title': snippet['title'],
                        'channel_title': snippet['channelTitle'],
                        'published_at': snippet['publishedAt'],
                        'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'playlist_item_id': item['id']
                    }
                    
                    videos.append(video_info)
                
                # Check for next page
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return videos
            
        except google.auth.exceptions.RefreshError:
            print("Authentication expired. Please re-authenticate.")
            return []
        except Exception as e:
            print(f"Error getting playlist videos: {e}")
            return []
    
    def find_playlist_item_id(self, playlist_id, video_id):
        """Find playlist item ID for a specific video in playlist"""
        try:
            if not self.youtube_service:
                return None
            
            next_page_token = None
            
            while True:
                request = self.youtube_service.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                for item in response.get('items', []):
                    if item['snippet']['resourceId']['videoId'] == video_id:
                        return item['id']
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return None
            
        except Exception as e:
            print(f"Error finding playlist item ID: {e}")
            return None
    
    def remove_video_from_playlist(self, playlist_item_id):
        """Remove video from playlist using playlist item ID"""
        try:
            if not self.youtube_service:
                return False
            
            request = self.youtube_service.playlistItems().delete(id=playlist_item_id)
            request.execute()
            
            return True
            
        except Exception as e:
            print(f"Error removing video from playlist: {e}")
            return False
    
    def remove_videos_batch(self, video_data_list, progress_callback=None):
        """Remove multiple videos from playlist"""
        removed_count = 0
        failed_count = 0
        
        for i, video_data in enumerate(video_data_list):
            try:
                playlist_item_id = video_data.get('playlist_item_id')
                
                if playlist_item_id:
                    success = self.remove_video_from_playlist(playlist_item_id)
                    if success:
                        removed_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                
                if progress_callback:
                    progress_callback(i + 1, len(video_data_list), removed_count, failed_count)
                    
            except Exception as e:
                print(f"Error in batch removal: {e}")
                failed_count += 1
        
        return {
            'removed': removed_count,
            'failed': failed_count,
            'total': len(video_data_list)
        }
