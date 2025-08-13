"""
YouTube API service module
Handles YouTube API authentication and data fetching
"""
import os
import re
import pickle
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from google.auth.transport.requests import Request
import google.auth.exceptions
import sys
import glob

# Load environment variables
load_dotenv()

class YouTubeAPIService:
    """Handles YouTube API operations and authentication"""

    def __init__(self):
        self.youtube = None  # Active service (API key or OAuth)
        self.credentials = None
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        # Compatibility fields expected by main_app
        self.client_secrets_file = 'client_secret.json'
        self.token_file = 'token.pickle'
        self.is_authenticated = False
        self.authenticated_youtube = None  # Service built with OAuth credentials
        self.last_auth_url = None
        # Ensure paths are resolved for frozen apps
        try:
            self._resolve_paths()
        except Exception:
            pass

    def _resolve_paths(self):
        """Resolve client_secrets and token paths for dev and PyInstaller (frozen) builds."""
        # Resolve client_secret.json search order:
        # 1) Existing set path if absolute and exists
        # 2) Current working directory
        # 3) Executable directory (for frozen exe)
        # 4) sys._MEIPASS extracted bundle dir (for onefile)
        # 5) Module directory (dev mode)
        candidates = []
        exe_dir = None
        bundle_dir = None
        module_dir = None
        try:
            if self.client_secrets_file and os.path.isabs(self.client_secrets_file):
                candidates.append(self.client_secrets_file)
        except Exception:
            pass
        try:
            candidates.append(os.path.join(os.getcwd(), 'client_secret.json'))
        except Exception:
            pass
        try:
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                candidates.append(os.path.join(exe_dir, 'client_secret.json'))
                bundle_dir = getattr(sys, '_MEIPASS', None)
                if bundle_dir:
                    candidates.append(os.path.join(bundle_dir, 'client_secret.json'))
        except Exception:
            pass
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            candidates.append(os.path.join(module_dir, 'client_secret.json'))
        except Exception:
            pass

        # Also search for typical Google file names like client_secret_*.json in these dirs
        try:
            variant_dirs = set(filter(None, [os.getcwd(), exe_dir, bundle_dir, module_dir]))
            for d in variant_dirs:
                for p in glob.glob(os.path.join(d, 'client_secret*.json')):
                    candidates.append(p)
        except Exception:
            pass

        for p in candidates:
            try:
                if p and os.path.exists(p):
                    self.client_secrets_file = p
                    break
            except Exception:
                continue

        # Resolve token storage path to a writable user directory
        try:
            base_dir = None
            if os.name == 'nt':
                base_dir = os.getenv('LOCALAPPDATA')
                if not base_dir:
                    base_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
            else:
                base_dir = os.path.join(os.path.expanduser('~'), '.config')
            app_dir = os.path.join(base_dir, 'youtube_4k_checker') if base_dir else os.path.expanduser('~')
            os.makedirs(app_dir, exist_ok=True)
            self.token_file = os.path.join(app_dir, 'token.pickle')
        except Exception:
            # Fallback to current working directory
            self.token_file = os.path.join(os.getcwd(), 'token.pickle')
        
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
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
                
                if self.credentials and self.credentials.valid:
                    self.authenticated_youtube = build('youtube', 'v3', credentials=self.credentials)
                    self.youtube = self.authenticated_youtube
                    self.is_authenticated = True
                    return self.youtube
                elif self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    with open(self.token_file, 'wb') as token:
                        pickle.dump(self.credentials, token)
                    self.authenticated_youtube = build('youtube', 'v3', credentials=self.credentials)
                    self.youtube = self.authenticated_youtube
                    self.is_authenticated = True
                    return self.youtube
            except Exception as e:
                print(f"OAuth credential error: {e}")
        
        return None
    
    def authenticate_oauth(self, callback=None):
        """Perform OAuth authentication"""
        try:
            # Ensure paths are ready (works for frozen exe)
            try:
                self._resolve_paths()
            except Exception:
                pass
            if not os.path.exists(self.client_secrets_file):
                if callback:
                    callback("❌ client_secret.json not found! Place it next to the app or set CLIENT_SECRETS_FILE.")
                return False
            
            # OAuth 2.0 flow
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=['https://www.googleapis.com/auth/youtube.readonly']
            )
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            if callback:
                callback(f"🔐 Please visit this URL to authorize the application: {auth_url}")
            self.last_auth_url = auth_url
            
            return auth_url
            
        except Exception as e:
            error_msg = f"OAuth error: {str(e)}"
            if callback:
                callback(f"❌ {error_msg}")
            return False
    
    def complete_oauth(self, auth_code, callback=None):
        """Complete OAuth flow with authorization code"""
        try:
            try:
                self._resolve_paths()
            except Exception:
                pass
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=['https://www.googleapis.com/auth/youtube.readonly']
            )
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            flow.fetch_token(code=auth_code)
            self.credentials = flow.credentials
            
            # Save credentials
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            
            # Build service
            self.authenticated_youtube = build('youtube', 'v3', credentials=self.credentials)
            self.youtube = self.authenticated_youtube
            self.is_authenticated = True
            
            if callback:
                callback("✅ Successfully authenticated! You can now access private playlists.")
            
            return True
            
        except Exception as e:
            error_msg = f"OAuth completion error: {str(e)}"
            if callback:
                callback(f"❌ {error_msg}")
            return False

    # --- Compatibility helpers expected by main_app.py ---
    def start_oauth_flow(self, callback=None):
        """Start OAuth; prefer local server flow (auto browser), fallback to manual URL."""
        # Try local server flow first (recommended by Google)
        try:
            try:
                self._resolve_paths()
            except Exception:
                pass
            if not os.path.exists(self.client_secrets_file):
                if callback:
                    callback("❌ client_secret.json not found! Place it next to the app or set CLIENT_SECRETS_FILE.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=['https://www.googleapis.com/auth/youtube.readonly']
            )
            creds = flow.run_local_server(open_browser=True, prompt='consent')
            self.credentials = creds
            # Persist token
            try:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
            except Exception:
                pass
            # Build OAuth service
            self.authenticated_youtube = build('youtube', 'v3', credentials=self.credentials)
            self.youtube = self.authenticated_youtube
            self.is_authenticated = True
            if callback:
                callback("✅ Logged in with Google")
            return True
        except Exception as e:
            # Fallback to manual (OOB-like) flow: provide URL and try to open browser
            try:
                url = self.authenticate_oauth(callback)
                if isinstance(url, str) and url:
                    opened = False
                    try:
                        import webbrowser
                        opened = webbrowser.open(url, new=2)
                        if not opened:
                            opened = webbrowser.open_new_tab(url)
                        if not opened and os.name == 'nt':
                            os.startfile(url)
                            opened = True
                    except Exception:
                        opened = False
                    if callback:
                        if opened:
                            callback("🔐 Browser opened for Google authorization.")
                        else:
                            callback(f"🔗 Open this URL to authorize: {url}")
                    return url
            except Exception as inner:
                pass
            if callback:
                callback(f"❌ OAuth flow error: {str(e)}")
            return None

    def logout_oauth(self):
        """Logout: remove stored token and reset OAuth service."""
        try:
            if os.path.exists(self.token_file):
                try:
                    os.remove(self.token_file)
                except Exception:
                    pass
            self.credentials = None
            self.is_authenticated = False
            self.authenticated_youtube = None
            # Keep API-key youtube if set via setup_youtube_api
            print("🚪 Logged out from Google account.")
        except Exception as e:
            print(f"Logout error: {e}")

    def check_existing_authentication(self):
        """Check and load existing OAuth credentials if available."""
        try:
            try:
                self._resolve_paths()
            except Exception:
                pass
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
                if self.credentials and (self.credentials.valid or self.credentials.refresh_token):
                    if not self.credentials.valid:
                        self.credentials.refresh(Request())
                        with open(self.token_file, 'wb') as token:
                            pickle.dump(self.credentials, token)
                    self.authenticated_youtube = build('youtube', 'v3', credentials=self.credentials)
                    self.youtube = self.authenticated_youtube
                    self.is_authenticated = True
                    print("✅ Loaded existing OAuth credentials.")
                    return True
        except Exception as e:
            print(f"Existing auth check failed: {e}")
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
        
        def _is_english_code(code: str) -> bool:
            try:
                if not code:
                    return False
                c = code.lower()
                return c == 'en' or c.startswith('en-') or c.startswith('en_')
            except Exception:
                return False

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
                        snippet = item.get('snippet', {})
                        content_details = item.get('contentDetails', {})

                        default_audio_lang = snippet.get('defaultAudioLanguage')
                        default_lang = snippet.get('defaultLanguage')
                        is_english = _is_english_code(default_audio_lang) or _is_english_code(default_lang)
                        video_details[video_id] = {
                            'id': video_id,
                            'title': snippet.get('title', ''),
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'definition': content_details.get('definition', 'hd'),
                            'dimension': content_details.get('dimension', '2d'),
                            'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                            'channel_title': snippet.get('channelTitle', ''),
                            'published_at': snippet.get('publishedAt', ''),
                            # Language signals from API
                            'default_audio_language': default_audio_lang or '',
                            'default_language': default_lang or '',
                            'is_english': is_english
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
                                    'published_at': '',
                                    'default_audio_language': '',
                                    'default_language': '',
                                    'is_english': False
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
