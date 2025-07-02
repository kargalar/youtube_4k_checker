from googleapiclient.discovery import build
import requests
import re

API_KEY = 'AIzaSyA3hWhKJmy2_0A7cfbB46va3XWsq-SeV2E'
# Playlist URL'si verebilirsiniz (ID otomatik çıkarılacak)
PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PLjgqfB3WxfkF-I1_jW6sowSWvQ4a-80U7'
MAX_VIDEOS = 200  # Maksimum kaç video taranacak (None = hepsi)

youtube = build('youtube', 'v3', developerKey=API_KEY)

def extract_playlist_id(playlist_url):
    """Playlist URL'sinden ID'yi çıkar"""
    if 'list=' in playlist_url:
        return playlist_url.split('list=')[1].split('&')[0]
    else:
        # Eğer direkt ID verilmişse
        return playlist_url

def get_video_ids_from_playlist(playlist_id, max_videos=None):
    video_ids = []
    next_page_token = None
    while True:
        pl_request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        pl_response = pl_request.execute()
        for item in pl_response['items']:
            video_ids.append(item['contentDetails']['videoId'])
            
            # Maksimum video sayısına ulaştıysak dur
            if max_videos and len(video_ids) >= max_videos:
                return video_ids[:max_videos]

        next_page_token = pl_response.get('nextPageToken')

        if not next_page_token:
            break
    
    return video_ids

def get_video_details(video_ids):
    """YouTube Data API kullanarak video detaylarını al"""
    video_details = []
    
    # Video ID'leri 50'şer gruplara böl (API limiti)
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        
        request = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=','.join(batch_ids)
        )
        response = request.execute()
        
        for item in response['items']:
            video_info = {
                'id': item['id'],
                'title': item['snippet']['title'],
                'url': f"https://www.youtube.com/watch?v={item['id']}",
                'definition': item['contentDetails']['definition'],  # 'hd' veya 'sd'
                'dimension': item['contentDetails']['dimension']     # '2d' veya '3d'
            }
            video_details.append(video_info)
    
    return video_details

def check_4k_availability(video_url):
    """Alternatif yöntem: Video sayfasını kontrol et"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(video_url, headers=headers)
        
        # 4K kalite seçeneklerini ara
        if '2160p' in response.text or '"quality":"hd2160"' in response.text:
            return True
        
        # Adaptive formats kontrol et
        if '"qualityLabel":"2160p"' in response.text:
            return True
            
    except Exception as e:
        print(f"Hata (web scraping): {e}")
    
    return False

# Ana program
print("Playlist URL'sinden ID cikartiliyor...")
playlist_id = extract_playlist_id(PLAYLIST_URL)
print(f"Playlist ID: {playlist_id}")

if MAX_VIDEOS:
    print(f"Maksimum {MAX_VIDEOS} video taranacak...")
else:
    print("Tum videolar taranacak...")

print("Playlist'ten video ID'leri aliniyor...")
video_ids = get_video_ids_from_playlist(playlist_id, MAX_VIDEOS)
print(f"Toplam {len(video_ids)} video bulundu.\n")

print("Video detaylari aliniyor...")
video_details = get_video_details(video_ids)

print("4K videolar kontrol ediliyor...\n")
print("=" * 100)

hd_videos = []
potentially_4k_videos = []

for i, video in enumerate(video_details, 1):
    print(f"[{i}/{len(video_details)}] {video['title'][:60]}...")
    print(f"URL: {video['url']}")
    print(f"Definition: {video['definition']}")
    
    if video['definition'] == 'hd':
        hd_videos.append(video)
        print("📹 HD kalitede (potansiyel 4K adayi)")
        
        # HD olan videolar için web scraping ile 4K kontrolü yap
        print("   🔍 4K kontrolu yapiliyor...")
        if check_4k_availability(video['url']):
            potentially_4k_videos.append(video)
            print("   ✅ 4K kalite mevcut!")
        else:
            print("   ❌ 4K kalite bulunamadi")
    else:
        print("📱 SD kalitede")
    
    print("-" * 100)

print(f"\n📊 SONUCLAR:")
print(f"Toplam video: {len(video_details)}")
print(f"HD kalitedeki videolar: {len(hd_videos)}")
print(f"4K kalite tespit edilen videolar: {len(potentially_4k_videos)}")

if potentially_4k_videos:
    print(f"\n🎬 4K VIDEOLAR:")
    
    # 4K videoları txt dosyasına kaydet
    with open('4k_videolar.txt', 'w', encoding='utf-8') as f:
        for video in potentially_4k_videos:
            print(f"• {video['title']}")
            print(f"  {video['url']}")
            print()
            
            # Dosyaya sadece URL yaz
            f.write(f"{video['url']}\n")
    
    print(f"✅ 4K videolar '4k_videolar.txt' dosyasina kaydedildi!")
    
else:
    print("\n❌ 4K video bulunamadi.")
    
    # Boş dosya oluştur
    with open('4k_videolar.txt', 'w', encoding='utf-8') as f:
        f.write("")  # Boş dosya
    
    print("📄 Bos '4k_videolar.txt' dosyasi olusturuldu.")
    print("\n💡 Olasi nedenler:")
    print("1. Playlist'teki videolarda gercekten 4K kalite yok")
    print("2. YouTube 4K kaliteyi sadece premium kullanicilara sunuyor olabilir")
    print("3. Video sahipleri 4K upload yapmamis olabilir")
