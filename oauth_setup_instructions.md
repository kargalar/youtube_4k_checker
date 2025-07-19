# Google OAuth2 Setup Instructions

## ⚠️ Error 403: access_denied Çözümü

Google OAuth2 uygulamanız henüz doğrulanmamış. İki çözüm seçeneğiniz var:

### 🎯 Çözüm 1: Test Kullanıcıları Ekleme (Önerilen - Hızlı)

1. **Google Cloud Console'a gidin:**
   - https://console.cloud.google.com/

2. **Projenizi seçin ve OAuth consent screen'e gidin:**
   - Sol menüden "APIs & Services" > "OAuth consent screen"

3. **Test users ekleyin:**
   - "Test users" bölümüne gidin
   - "ADD USERS" butonuna tıklayın
   - Email adresinizi ekleyin: `m.islam0422@gmail.com`
   - "SAVE" yapın

4. **Publishing status'u kontrol edin:**
   - Status "Testing" olmalı
   - "MAKE EXTERNAL" varsa tıklayın

5. **Authorized redirect URIs kontrol edin:**
   - APIs & Services > Credentials > OAuth 2.0 Client IDs
   - Edit butonuna tıklayın
   - "Authorized redirect URIs" bölümüne ekleyin: `urn:ietf:wg:oauth:2.0:oob`
   - SAVE yapın

### 🔐 Çözüm 2: Service Account Kullanma (Alternatif)

OAuth2 yerine Service Account kullanarak authentication yapmayı da deneyebiliriz.

## 📋 Adım Adım Test User Ekleme:

1. Google Cloud Console → Projeniz
2. APIs & Services → OAuth consent screen
3. Aşağı kaydırın → "Test users" bölümü
4. "ADD USERS" → Email adresinizi yazın
5. SAVE

## 📋 Redirect URI Ekleme:

1. Google Cloud Console → Projeniz
2. APIs & Services → Credentials
3. OAuth 2.0 Client IDs'den projenizi seçin
4. "Edit" butonuna tıklayın
5. "Authorized redirect URIs" bölümüne ekleyin:
   - `urn:ietf:wg:oauth:2.0:oob`
6. SAVE

## ✅ Test Sonrası:

Test kullanıcısı ve redirect URI ekledikten sonra:
- Uygulamayı tekrar çalıştırın
- Login butonuna tıklayın
- Browser'da warning göreceksiniz ama "Advanced" → "Go to YouTube 4K Checker (unsafe)" diyebilirsiniz
- Authorization code sayfasında kodu kopyalayıp uygulamaya yapıştırın

## 🔧 Troubleshooting:

### "Error 400: redirect_uri_mismatch"
- Redirect URI'yi `urn:ietf:wg:oauth:2.0:oob` olarak eklediğinizden emin olun

### "Error 403: access_denied"
- Email adresinizin test users listesinde olduğundan emin olun
- OAuth consent screen'in "Testing" modunda olduğunu kontrol edin

### "Invalid authorization code"
- Kod'u tamamen kopyaladığınızdan emin olun
- Kod'un süresinin dolmamış olduğunu kontrol edin (birkaç dakika içinde kullanın)
