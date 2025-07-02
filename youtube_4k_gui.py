import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from googleapiclient.discovery import build
import requests
import re
import os

class YouTube4KCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 4K Video Checker")
        self.root.geometry("800x700")
        self.root.configure(bg='#f0f0f0')
        
        # API Key - Buraya kendi API key'inizi yazın
        self.API_KEY = 'AIzaSyA3hWhKJmy2_0A7cfbB46va3XWsq-SeV2E'
        self.youtube = build('youtube', 'v3', developerKey=self.API_KEY)
        
        # İşlem durumu
        self.is_processing = False
        self.found_4k_videos = []
        
        self.create_widgets()
    
    def create_widgets(self):
        # Ana başlık
        title_label = tk.Label(self.root, text="🎬 YouTube 4K Video Checker", 
                              font=('Arial', 16, 'bold'), bg='#f0f0f0', fg='#333')
        title_label.pack(pady=10)
        
        # Playlist URL girişi
        url_frame = tk.Frame(self.root, bg='#f0f0f0')
        url_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(url_frame, text="Playlist URL:", font=('Arial', 12), 
                bg='#f0f0f0').pack(anchor='w')
        
        url_input_frame = tk.Frame(url_frame, bg='#f0f0f0')
        url_input_frame.pack(fill='x', pady=5)
        
        self.url_entry = tk.Entry(url_input_frame, font=('Arial', 11), width=60)
        self.url_entry.pack(side='left', fill='x', expand=True)
        
        paste_btn = tk.Button(url_input_frame, text="📋 Yapıştır", 
                             command=self.paste_url, bg='#4CAF50', fg='white',
                             font=('Arial', 10))
        paste_btn.pack(side='right', padx=(5, 0))
        
        # Video sayısı sınırı
        limit_frame = tk.Frame(self.root, bg='#f0f0f0')
        limit_frame.pack(pady=5, padx=20, fill='x')
        
        tk.Label(limit_frame, text="Maksimum video sayısı (boş = hepsi):", 
                font=('Arial', 10), bg='#f0f0f0').pack(anchor='w')
        
        self.limit_entry = tk.Entry(limit_frame, font=('Arial', 11), width=20)
        self.limit_entry.pack(anchor='w', pady=2)
        self.limit_entry.insert(0, "200")  # Varsayılan değer
        
        # Butonlar
        button_frame = tk.Frame(self.root, bg='#f0f0f0')
        button_frame.pack(pady=15)
        
        self.get_videos_btn = tk.Button(button_frame, text="📥 Videoları Getir", 
                                       command=self.get_videos, bg='#2196F3', 
                                       fg='white', font=('Arial', 12, 'bold'),
                                       padx=20, pady=10)
        self.get_videos_btn.pack(side='left', padx=5)
        
        self.check_4k_btn = tk.Button(button_frame, text="🔍 4K Kontrol Et", 
                                     command=self.check_4k_videos, bg='#FF5722', 
                                     fg='white', font=('Arial', 12, 'bold'),
                                     padx=20, pady=10, state='disabled')
        self.check_4k_btn.pack(side='left', padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill='x')
        
        # Durum etiketi
        self.status_label = tk.Label(self.root, text="Playlist URL'si girin ve 'Videoları Getir' butonuna basın", 
                                    font=('Arial', 10), bg='#f0f0f0', fg='#666')
        self.status_label.pack(pady=5)
        
        # Video listesi
        list_frame = tk.Frame(self.root, bg='#f0f0f0')
        list_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        tk.Label(list_frame, text="📹 Bulunan Videolar:", font=('Arial', 12, 'bold'), 
                bg='#f0f0f0').pack(anchor='w')
        
        # Treeview ile video listesi
        columns = ('No', 'Başlık', 'Kalite', 'Durum')
        self.video_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Sütun başlıkları
        self.video_tree.heading('No', text='#')
        self.video_tree.heading('Başlık', text='Video Başlığı')
        self.video_tree.heading('Kalite', text='Kalite')
        self.video_tree.heading('Durum', text='4K Durumu')
        
        # Sütun genişlikleri
        self.video_tree.column('No', width=50)
        self.video_tree.column('Başlık', width=400)
        self.video_tree.column('Kalite', width=80)
        self.video_tree.column('Durum', width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        
        self.video_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Alt butonlar
        bottom_frame = tk.Frame(self.root, bg='#f0f0f0')
        bottom_frame.pack(pady=10, fill='x')
        
        self.save_btn = tk.Button(bottom_frame, text="💾 4K Videoları Kaydet", 
                                 command=self.save_4k_videos, bg='#9C27B0', 
                                 fg='white', font=('Arial', 11, 'bold'),
                                 state='disabled')
        self.save_btn.pack(side='left', padx=20)
        
        self.clear_btn = tk.Button(bottom_frame, text="🗑️ Temizle", 
                                  command=self.clear_all, bg='#607D8B', 
                                  fg='white', font=('Arial', 11))
        self.clear_btn.pack(side='right', padx=20)
    
    def paste_url(self):
        """Panodaki URL'yi yapıştır"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_content)
        except:
            messagebox.showwarning("Uyarı", "Panoda metin bulunamadı!")
    
    def extract_playlist_id(self, playlist_url):
        """Playlist URL'sinden ID'yi çıkar"""
        if 'list=' in playlist_url:
            return playlist_url.split('list=')[1].split('&')[0]
        else:
            return playlist_url
    
    def get_videos(self):
        """Playlist'ten videoları getir"""
        if self.is_processing:
            return
            
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Hata", "Lütfen playlist URL'si girin!")
            return
        
        try:
            limit_text = self.limit_entry.get().strip()
            max_videos = int(limit_text) if limit_text else None
        except ValueError:
            max_videos = None
        
        # Thread'de çalıştır
        thread = threading.Thread(target=self._get_videos_thread, args=(url, max_videos))
        thread.daemon = True
        thread.start()
    
    def _get_videos_thread(self, url, max_videos):
        """Video getirme işlemini thread'de yap"""
        self.is_processing = True
        self.progress.start()
        self.get_videos_btn.config(state='disabled')
        self.check_4k_btn.config(state='disabled')
        
        try:
            self.status_label.config(text="Playlist analiz ediliyor...")
            
            # Playlist ID'yi çıkar
            playlist_id = self.extract_playlist_id(url)
            
            # Video ID'lerini al
            video_ids = self.get_video_ids_from_playlist(playlist_id, max_videos)
            
            self.status_label.config(text=f"{len(video_ids)} video bulundu, detaylar alınıyor...")
            
            # Video detaylarını al
            self.video_details = self.get_video_details(video_ids)
            
            # GUI'yi güncelle
            self.root.after(0, self._update_video_list)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"Video alınırken hata: {str(e)}"))
        finally:
            self.is_processing = False
            self.progress.stop()
            self.get_videos_btn.config(state='normal')
            if hasattr(self, 'video_details') and self.video_details:
                self.check_4k_btn.config(state='normal')
    
    def _update_video_list(self):
        """Video listesini güncelle"""
        # Listeyi temizle
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        
        # Videoları ekle
        for i, video in enumerate(self.video_details, 1):
            quality = "HD" if video['definition'] == 'hd' else "SD"
            self.video_tree.insert('', 'end', values=(
                i, 
                video['title'][:50] + "..." if len(video['title']) > 50 else video['title'],
                quality,
                "Bekliyor..."
            ))
        
        self.status_label.config(text=f"{len(self.video_details)} video listelendi. 4K kontrol için butona basın.")
    
    def get_video_ids_from_playlist(self, playlist_id, max_videos=None):
        """Playlist'ten video ID'lerini al"""
        video_ids = []
        next_page_token = None
        
        while True:
            pl_request = self.youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            pl_response = pl_request.execute()
            
            for item in pl_response['items']:
                video_ids.append(item['contentDetails']['videoId'])
                if max_videos and len(video_ids) >= max_videos:
                    return video_ids[:max_videos]
            
            next_page_token = pl_response.get('nextPageToken')
            if not next_page_token:
                break
        
        return video_ids
    
    def get_video_details(self, video_ids):
        """Video detaylarını al"""
        video_details = []
        
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(batch_ids)
            )
            response = request.execute()
            
            for item in response['items']:
                video_info = {
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'url': f"https://www.youtube.com/watch?v={item['id']}",
                    'definition': item['contentDetails']['definition'],
                    'dimension': item['contentDetails']['dimension']
                }
                video_details.append(video_info)
        
        return video_details
    
    def check_4k_videos(self):
        """4K videoları kontrol et"""
        if self.is_processing or not hasattr(self, 'video_details'):
            return
        
        thread = threading.Thread(target=self._check_4k_thread)
        thread.daemon = True
        thread.start()
    
    def _check_4k_thread(self):
        """4K kontrol işlemini thread'de yap"""
        self.is_processing = True
        self.progress.start()
        self.check_4k_btn.config(state='disabled')
        self.found_4k_videos = []
        
        try:
            hd_videos = [v for v in self.video_details if v['definition'] == 'hd']
            
            for i, video in enumerate(hd_videos):
                # GUI'yi güncelle
                self.root.after(0, lambda v=video, idx=i: self._update_video_status(v, f"Kontrol ediliyor... ({idx+1}/{len(hd_videos)})"))
                
                # 4K kontrolü yap
                is_4k = self.check_4k_availability(video['url'])
                
                if is_4k:
                    self.found_4k_videos.append(video)
                    self.root.after(0, lambda v=video: self._update_video_status(v, "✅ 4K Mevcut!"))
                else:
                    self.root.after(0, lambda v=video: self._update_video_status(v, "❌ 4K Yok"))
            
            # SD videoları için durum güncelle
            sd_videos = [v for v in self.video_details if v['definition'] == 'sd']
            for video in sd_videos:
                self.root.after(0, lambda v=video: self._update_video_status(v, "📱 SD Kalite"))
            
            # Sonuçları göster
            self.root.after(0, self._show_results)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"4K kontrol hatası: {str(e)}"))
        finally:
            self.is_processing = False
            self.progress.stop()
            self.check_4k_btn.config(state='normal')
    
    def _update_video_status(self, video, status):
        """Video durumunu güncelle"""
        for item in self.video_tree.get_children():
            values = self.video_tree.item(item, 'values')
            if video['title'][:50] in values[1]:
                self.video_tree.item(item, values=(values[0], values[1], values[2], status))
                break
    
    def _show_results(self):
        """Sonuçları göster"""
        total_videos = len(self.video_details)
        found_count = len(self.found_4k_videos)
        
        self.status_label.config(text=f"✅ Tarama tamamlandı! {total_videos} video tarandı, {found_count} adet 4K video bulundu.")
        
        if self.found_4k_videos:
            self.save_btn.config(state='normal')
            messagebox.showinfo("Sonuç", f"🎉 {found_count} adet 4K video bulundu!\n\nSonuçları kaydetmek için 'Kaydet' butonunu kullanın.")
        else:
            messagebox.showinfo("Sonuç", "😔 4K video bulunamadı.\n\nBu playlist'te 4K kalitede video bulunmuyor.")
    
    def check_4k_availability(self, video_url):
        """4K kalite kontrolü"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(video_url, headers=headers, timeout=10)
            
            if '2160p' in response.text or '"quality":"hd2160"' in response.text:
                return True
            
            if '"qualityLabel":"2160p"' in response.text:
                return True
                
        except:
            pass
        
        return False
    
    def save_4k_videos(self):
        """4K videoları dosyaya kaydet"""
        if not self.found_4k_videos:
            messagebox.showwarning("Uyarı", "Kaydedilecek 4K video bulunamadı!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="4K Videoları Kaydet"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for video in self.found_4k_videos:
                        f.write(f"{video['url']}\n")
                
                messagebox.showinfo("Başarılı", f"✅ {len(self.found_4k_videos)} adet 4K video URL'si kaydedildi!\n\nDosya: {filename}")
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya kaydedilemedi: {str(e)}")
    
    def clear_all(self):
        """Tüm verileri temizle"""
        self.url_entry.delete(0, tk.END)
        
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        
        self.status_label.config(text="Playlist URL'si girin ve 'Videoları Getir' butonuna basın")
        self.check_4k_btn.config(state='disabled')
        self.save_btn.config(state='disabled')
        self.found_4k_videos = []
        
        if hasattr(self, 'video_details'):
            delattr(self, 'video_details')

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTube4KCheckerGUI(root)
    root.mainloop()
