"""
4K video quality checking service
Handles 4K availability detection for YouTube videos
"""
import requests
import urllib3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# SSL uyarılarını devre dışı bırak
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Video4KChecker:
    """Service for checking 4K availability of YouTube videos"""
    
    def __init__(self):
        self.found_4k_videos = []
        self.stop_requested = False
    
    def check_4k_availability(self, video_url):
        """Check if a video has 4K quality available"""
        try:
            # Extract video ID
            video_id = None
            if 'watch?v=' in video_url:
                video_id = video_url.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in video_url:
                video_id = video_url.split('youtu.be/')[1].split('?')[0]
            
            if not video_id:
                return False
            
            # Try different methods for 4K detection
            try:
                # Method 1: Check via yt-dlp style format detection
                result = self._advanced_4k_check(video_id)
                if result is not None:
                    return result
            except:
                pass
            
            # Method 2: Simple page-based check
            return self._simple_4k_check(video_id)
            
        except Exception as e:
            print(f"4K check error for {video_url}: {e}")
            return False
    
    def _advanced_4k_check(self, video_id):
        """Advanced 4K format check using video info"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Check video info page
            info_url = f"https://www.youtube.com/get_video_info?video_id={video_id}"
            response = requests.get(info_url, headers=headers, timeout=10, verify=False)
            
            if response.status_code == 200:
                content = response.text

                # Look for 4K indicators in the response (precise markers only)
                formats_data = content

                # Known itags and explicit quality markers for 2160p (strict)
                k4_indicators = [
                    'itag=313',  # VP9 4K
                    'itag=315',  # VP9 4K 60fps
                    'itag=401',  # AV1 4K
                    'itag=337',  # VP9 4K
                    'height=2160',
                    'quality=hd2160',
                    'quality_label=2160p',
                    '"qualityLabel":"2160p"'
                ]

                for indicator in k4_indicators:
                    if indicator in formats_data:
                        return True

                # No reliable 4K markers found
                return False
                
        except Exception as e:
            print(f"Advanced 4K check error for {video_id}: {e}")
            return None
    
    def _simple_4k_check(self, video_id):
        """Simple 4K check via video page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            url = f"https://www.youtube.com/watch?v={video_id}"
            response = requests.get(url, headers=headers, timeout=5, verify=False)
            
            if response.status_code == 200:
                content = response.text

                # Only rely on structured quality markers, not free text like titles/descriptions
                precise_markers = [
                    '"qualityLabel":"2160p"',
                    '"quality":"hd2160"',
                    '"height":2160',
                    'quality=hd2160'
                ]

                for marker in precise_markers:
                    if marker in content:
                        return True

                return False
            
            return False
            
        except Exception as e:
            print(f"Simple 4K check error for {video_id}: {e}")
            return False
    
    def check_videos_parallel(self, video_details, progress_callback=None, status_callback=None, stop_check=None):
        """
        Check multiple videos for 4K availability in parallel
        
        Args:
            video_details: List of video dictionaries
            progress_callback: Function to call with progress updates (video, status)
            status_callback: Function to call with overall status updates
            stop_check: Function that returns True if process should stop
        """
        self.found_4k_videos = []
        self.stop_requested = False
        
        try:
            # Filter HD videos for checking
            hd_videos = [v for v in video_details if v['definition'] == 'hd']
            
            if not hd_videos:
                # Mark SD videos
                sd_videos = [v for v in video_details if v['definition'] == 'sd']
                for video in sd_videos:
                    if progress_callback:
                        progress_callback(video, "📱 SD Quality")
                return self.found_4k_videos
            
            # Parallel processing setup
            max_workers = min(6, len(hd_videos))
            completed_count = 0
            failed_count = 0
            
            if status_callback:
                status_callback(f"🚀 Smart 4K scanning with {max_workers} threads...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all videos for checking
                future_to_video = {
                    executor.submit(self.check_4k_availability, video['url']): video
                    for video in hd_videos
                }
                
                # Process results as they complete
                for future in as_completed(future_to_video, timeout=120):
                    # Check if stop was requested
                    if stop_check and stop_check():
                        self.stop_requested = True
                        # Cancel remaining futures
                        for f in future_to_video:
                            if not f.done():
                                f.cancel()
                        break
                    
                    video = future_to_video[future]
                    completed_count += 1
                    
                    try:
                        is_4k = future.result(timeout=3)
                        
                        if is_4k:
                            self.found_4k_videos.append(video['url'])
                            if progress_callback:
                                progress_callback(video, "✅ 4K Available!")
                        else:
                            if progress_callback:
                                progress_callback(video, "❌ No 4K")
                    
                    except Exception as e:
                        print(f"Error checking video {video['id']}: {e}")
                        failed_count += 1
                        if progress_callback:
                            progress_callback(video, "⚠️ Check Failed")
                    
                    # Update overall progress
                    if status_callback:
                        progress_text = f"🔍 Scanning: {completed_count}/{len(hd_videos)} ({len(self.found_4k_videos)} 4K found)"
                        if failed_count > 0:
                            progress_text += f" [{failed_count} failed]"
                        status_callback(progress_text)
            
            # Handle timeouts
            remaining_videos = []
            for future, video in future_to_video.items():
                if not future.done() and not self.stop_requested:
                    remaining_videos.append(video)
                    if progress_callback:
                        progress_callback(video, "⏰ Timeout")
            
            if remaining_videos and not self.stop_requested and status_callback:
                timeout_text = f"⚠️ {len(remaining_videos)} videos timed out"
                status_callback(timeout_text)
            
            # Mark SD videos
            if not self.stop_requested:
                sd_videos = [v for v in video_details if v['definition'] == 'sd']
                for video in sd_videos:
                    if progress_callback:
                        progress_callback(video, "📱 SD Quality")
        
        except Exception as e:
            if status_callback:
                status_callback(f"❌ 4K check error: {str(e)}")
        
        return self.found_4k_videos
    
    def stop_checking(self):
        """Stop the current checking process"""
        self.stop_requested = True
