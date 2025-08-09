"""
YouTube API service module
Handles YouTube API authentication and data fetching
"""
import os
import re
import pickle
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.auth.exceptions

# Load environment variables
load_dotenv()

class YouTubeAPIService:
    """Handles YouTube API operations and authentication"""
    
    def __init__(self):
        self.youtube = None
        self.credentials = None
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        
    def setup_youtube_api(self):
        """Initialize YouTube API service with retry mechanism"""
        try:
            if self.api_key:
                # Use API key for read-only operations
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                        
                        # Test the API connection
                        test_request = self.youtube.search().list(
                            part='snippet',
                            q='test',
                            maxResults=1
                        )
                        test_response = test_request.execute()
                        
                        print("✅ YouTube API initialized and tested with API key")
                        return True
                        
                    except Exception as e:
                        print(f"API key test attempt {attempt + 1} failed: {e}")
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(1)
                            continue
                        else:
                            print(f"❌ API key failed after {max_retries} attempts")
                            
            else:
                print("⚠️ No API key found. OAuth will be required for playlist access.")
                
            return False
            
        except Exception as e:
            print(f"❌ YouTube API setup error: {e}")
            return False
    
    def get_youtube_service_for_read(self):
        """Get YouTube service for read operations (API key or OAuth)"""
        if self.youtube:
            return self.youtube
        
        # Try to load existing OAuth credentials
        if os.path.exists('token.pickle'):
            try:
                with open('token.pickle', 'rb') as token:
                    self.credentials = pickle.load(token)
                
                if self.credentials and self.credentials.valid:
                    self.youtube = build('youtube', 'v3', credentials=self.credentials)
                    return self.youtube
                elif self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    with open('token.pickle', 'wb') as token:
                        pickle.dump(self.credentials, token)
                    self.youtube = build('youtube', 'v3', credentials=self.credentials)
                    return self.youtube
            except Exception as e:
                print(f"OAuth credential error: {e}")
        
        return None
    
    def authenticate_oauth(self, callback=None):
        """Perform OAuth authentication"""
        try:
            if not os.path.exists('client_secret.json'):
                if callback:
                    callback("❌ client_secret.json not found! Please add your OAuth credentials.")
                return False
            
            # OAuth 2.0 flow
            flow = Flow.from_client_secrets_file(
                'client_secret.json',
                scopes=['https://www.googleapis.com/auth/youtube.readonly']
            )
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            if callback:
                callback(f"🔐 Please visit this URL to authorize the application: {auth_url}")
            
            return auth_url
            
        except Exception as e:
            error_msg = f"OAuth error: {str(e)}"
            if callback:
                callback(f"❌ {error_msg}")
            return False
    
    def complete_oauth(self, auth_code, callback=None):
        """Complete OAuth flow with authorization code"""
        try:
            flow = Flow.from_client_secrets_file(
                'client_secret.json',
                scopes=['https://www.googleapis.com/auth/youtube.readonly']
            )
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            flow.fetch_token(code=auth_code)
            self.credentials = flow.credentials
            
            # Save credentials
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.credentials, token)
            
            # Build service
            self.youtube = build('youtube', 'v3', credentials=self.credentials)
            
            if callback:
                callback("✅ Successfully authenticated! You can now access private playlists.")
            
            return True
            
        except Exception as e:
            error_msg = f"OAuth completion error: {str(e)}"
            if callback:
                callback(f"❌ {error_msg}")
            return False
    
    def extract_playlist_id(self, playlist_url):
        """Extract playlist ID from YouTube URL"""
        patterns = [
            r'[?&]list=([a-zA-Z0-9_-]+)',
            r'/playlist\?list=([a-zA-Z0-9_-]+)',
            r'youtube\.com/.*[?&]list=([a-zA-Z0-9_-]+)',
            r'youtu\.be/.*[?&]list=([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, playlist_url)
            if match:
                return match.group(1)
        
        # If no pattern matches, assume the input is already a playlist ID
        return playlist_url.strip()
    
    def get_video_ids_from_playlist(self, playlist_id, max_videos=None, service=None):
        """Get video IDs from a playlist"""
        video_ids = []
        svc = service or self.youtube
        
        if svc is None:
            raise RuntimeError("YouTube service is not initialized")
        
        next_page_token = None
        
        while True:
            request = svc.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=min(50, max_videos - len(video_ids) if max_videos else 50),
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])
                if max_videos and len(video_ids) >= max_videos:
                    break
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token or (max_videos and len(video_ids) >= max_videos):
                break
        
        return video_ids
    
    def get_video_details(self, video_ids, service=None):
        """Get video details from video IDs with retry mechanism"""
        video_details = {}
        svc = service or self.youtube
        
        if svc is None:
            print("❌ YouTube service is not initialized")
            return video_details
        
        max_retries = 3
        
        # Process in batches of 50 (API limit)
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            # Retry mechanism for each batch
            for attempt in range(max_retries):
                try:
                    request = svc.videos().list(
                        part='snippet,contentDetails,statistics',
                        id=','.join(batch_ids)
                    )
                    response = request.execute()
                    
                    # Process response
                    for item in response['items']:
                        video_id = item['id']
                        video_details[video_id] = {
                            'id': video_id,
                            'title': item['snippet']['title'],
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'definition': item['contentDetails'].get('definition', 'hd'),
                            'dimension': item['contentDetails'].get('dimension', '2d'),
                            'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                            'channel_title': item['snippet']['channelTitle'],
                            'published_at': item['snippet']['publishedAt']
                        }
                    
                    print(f"✅ Batch {i//50 + 1}: Got details for {len(response['items'])} videos")
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    print(f"❌ Batch {i//50 + 1} attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1 * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        print(f"❌ Failed to get details for batch {i//50 + 1} after {max_retries} attempts")
                        # Add basic info for failed videos
                        for video_id in batch_ids:
                            if video_id not in video_details:
                                video_details[video_id] = {
                                    'id': video_id,
                                    'title': f'Video {video_id}',
                                    'url': f"https://www.youtube.com/watch?v={video_id}",
                                    'definition': 'hd',  # Default
                                    'dimension': '2d',
                                    'thumbnail': '',
                                    'channel_title': 'Unknown',
                                    'published_at': ''
                                }
        
        return video_details
    
    def get_playlist_info(self, playlist_id, service=None):
        """Get playlist information"""
        svc = service or self.youtube
        
        if svc is None:
            return None
        
        try:
            request = svc.playlists().list(
                part='snippet,contentDetails',
                id=playlist_id
            )
            response = request.execute()
            
            if response['items']:
                item = response['items'][0]
                return {
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'video_count': item['contentDetails']['itemCount'],
                    'channel_title': item['snippet']['channelTitle']
                }
        except Exception as e:
            print(f"Error getting playlist info: {e}")
        
        return None
