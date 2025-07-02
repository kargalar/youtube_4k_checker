# YouTube 4K Video Checker - OAuth2 Setup

## ✅ YouTube Playlist Modification Feature Ready!

OAuth2 credentials are already configured! You can now use all features including removing videos from YouTube playlists.

## How to Use

### 1. **Check 4K Videos**
1. Enter a YouTube playlist URL
2. Click "Get Videos" to fetch video list
3. Click "Check 4K" to scan for 4K availability
4. Use "Check 4K Only" to select only 4K videos

### 2. **Copy Video URLs**
1. Check the videos you want to copy (use checkboxes)
2. Click "Copy Checked" to copy URLs to clipboard
3. You'll get options to remove videos after copying

### 3. **Remove Videos from Playlist**
1. After copying URLs, choose "Remove from YouTube Playlist"
2. **First time**: Authentication dialog will appear
3. Click "Open Browser for Authentication"
4. Sign in with your Google account and authorize the app
5. Copy the authorization code and paste it in the app
6. Click "Complete Authentication"
7. Confirm removal - videos will be permanently removed from your playlist

## Authentication Status

- **🔐 Green**: Authenticated - Full features available
- **⚠️ Orange**: Not authenticated - Limited to local operations

## Features Available

### ✅ **Without Authentication** (Read-only):
- Get playlist videos
- Check 4K availability  
- Copy video URLs
- Remove from local list only

### 🔐 **With Authentication** (Full access):
- Everything above, plus:
- **Remove videos from actual YouTube playlists**
- Permanent playlist modification

## Important Notes

### **Security & Privacy**
- ✅ OAuth2 credentials are already configured
- ✅ Authentication is secure via Google's OAuth2 system
- ✅ Only YouTube scope - no access to other Google services
- ✅ Credentials are stored locally and encrypted

### **Limitations**
- You can only modify **your own playlists**
- You must be the playlist owner or have edit permissions
- Removed videos cannot be restored (permanent action)
- Authentication expires and needs renewal periodically

### **Troubleshooting**

**"Authentication Error":**
- Make sure you're connected to the internet
- Try clearing browser cookies for Google
- Ensure you're using the correct Google account

**"403 Forbidden" when removing videos:**
- You don't own the playlist
- The playlist is private/restricted
- Videos may have already been removed

**Authentication dialog doesn't open:**
- Check if your browser blocks popups
- Copy the URL manually if browser doesn't open automatically

## Data Storage

- **`token.pickle`**: Your authentication tokens (auto-created)
- **`client_secret.json`**: OAuth2 configuration (already set up)
- **Thumbnails**: Cached locally for performance

## Advanced Usage

### Bulk Operations
1. Use "Check All" to select all videos
2. Use "Check 4K Only" to select only 4K videos  
3. Copy and remove in batches for efficiency

### Playlist Management
- Remove videos you've already downloaded
- Clean up playlists by removing non-4K content
- Backup video URLs before removing

**Ready to use! No additional setup required.** 🚀
