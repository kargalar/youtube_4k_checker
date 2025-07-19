# YouTube 4K Video Checker - OAuth2 Setup

## ✅ YouTube Playlist Modification Feature Ready!

OAuth2 credentials are already configured! You can now use all features including removing videos from YouTube playlists.

## How to Use

### 1. **Authentication (First Time)**
1. Click the "🔐 Login" button in the top-right corner
2. A dialog will open - click "🌐 Open Browser for Authentication"
3. Sign in with your Google account and authorize the app
4. Copy the authorization code from the browser
5. Paste it in the app and click "✅ Complete Authentication"
6. Status will change to "🔐 Authenticated" (green)

### 2. **Check 4K Videos**
1. Enter a YouTube playlist URL
2. Click "Get Videos" to fetch video list
3. Click "Check 4K" to scan for 4K availability
4. Use "Check 4K Only" to select only 4K videos

### 3. **Copy and Remove Videos**
1. Check the videos you want to copy/remove (use checkboxes)
2. Click "Copy Checked" - this opens an options dialog:
   - **📋 Just Copy (Done)** - Only copy URLs to clipboard
   - **🗑️ Remove from Local List** - Remove from app view only
   - **❌ Remove from YouTube Playlist** - Permanently remove from your YouTube playlist

### 4. **Right-Click Options**
- Right-click any video for quick actions:
  - Copy single video URL
  - Remove from local list
  - Remove from YouTube playlist (if authenticated)

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
- Batch removal operations

## Important Notes

### **Security & Privacy**
- ✅ OAuth2 credentials are already configured
- 🔐 Your authentication is stored securely locally
- 🚪 Use "Logout" to clear authentication
- ⚠️ Only you can access your playlists

### **Removal Operations**
- ❌ **PERMANENT**: YouTube playlist removals cannot be undone
- ✅ **CONFIRMATION**: App always asks for confirmation before removing
- 🔄 **BATCH**: You can remove multiple videos at once
- 📱 **SAFE**: Local list operations don't affect YouTube

### **Troubleshooting**
- If authentication fails, try logging out and in again
- Make sure the playlist is owned by your account for removal
- Some playlists may be read-only (like "Watch Later")

## New Features Added

### 🆕 **Google OAuth2 Integration**
- Secure authentication with your Google account
- Persistent login (stays logged in between sessions)
- Easy logout option

### 🆕 **YouTube Playlist Management**
- Remove individual videos from playlists
- Batch remove multiple selected videos
- Confirmation dialogs prevent accidental deletions
- Progress tracking for batch operations

### 🆕 **Enhanced User Interface**
- Authentication status indicator
- Post-copy action options
- Right-click context menus
- Improved error handling and user feedback
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
