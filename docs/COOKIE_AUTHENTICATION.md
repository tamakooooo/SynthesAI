# Cookie Authentication Guide - Bilibili & Douyin

## Overview

Video platforms like Bilibili and Douyin require authentication cookies to download videos, especially when:
- Videos are region-restricted
- High-quality downloads are needed
- Rate limiting needs to be bypassed
- Premium content access is required

## Bilibili (B站) - Automatic QR Login

### Quick Start

```bash
# 1. Login with QR code
la auth login --platform bilibili

# 2. Scan the QR code with Bilibili App
# 3. Cookies are automatically saved to config/cookies/bilibili_cookies.txt

# 4. Download videos with authentication
la video https://www.bilibili.com/video/BV123
```

### How It Works

1. **Generate QR Code**: System calls Bilibili API to generate a login QR
2. **Display in Terminal**: QR code shown as ASCII art in your terminal
3. **Scan & Confirm**: You scan with Bilibili App and confirm login
4. **Auto Save**: System extracts cookies and saves to `config/cookies/bilibili_cookies.txt`
5. **Auto Use**: Video downloads automatically use saved cookies

### Commands

```bash
# Login
la auth login --platform bilibili

# Check status
la auth status --platform bilibili

# Logout
la auth logout --platform bilibili
```

### Troubleshooting

**QR Code Not Displaying**
- Ensure terminal supports Unicode characters
- Try Windows Terminal, iTerm2, or modern Linux terminals
- If using legacy terminal, upgrade or use different terminal

**Login Timeout**
- Default timeout: 180 seconds
- Increase with: `la auth login --platform bilibili --timeout 300`

**Cookies Not Working**
- Check cookie file: `cat config/cookies/bilibili_cookies.txt`
- Re-login: `la auth logout --platform bilibili && la auth login --platform bilibili`

## Douyin (抖音) - Manual Cookie Import

Douyin requires OAuth app registration for automated login (complex setup). We provide manual cookie import instead.

### Step-by-Step Guide

#### Step 1: Get Cookies from Browser

**Method 1: Network Tab (Recommended)**

1. Open https://www.douyin.com in Chrome/Edge
2. Login to your Douyin account (scan QR or phone number)
3. Press **F12** to open Developer Tools
4. Go to **Network** tab
5. Check **Preserve log**
6. Refresh page (F5)
7. Click any request in the list
8. Find **Request Headers** → **cookie:**
9. Copy the entire cookie value (long string)

**Method 2: Console (Quick)**

1. Open https://www.douyin.com
2. Login to your account
3. Press **F12** → **Console** tab
4. Type: `document.cookie`
5. Press Enter
6. Copy the output string

#### Step 2: Import Cookies

```bash
la auth import --platform douyin --cookies "your_cookie_string_here"
```

Example:
```bash
la auth import --platform douyin --cookies "odin_tt=abc123; ttwid=xyz789; passport_csrf_token=def456; s_v_web_id=ghi012"
```

#### Step 3: Verify

```bash
la auth status --platform douyin
```

Should show: `[OK] Authenticated`

#### Step 4: Download Videos

```bash
la video https://v.douyin.com/xxx
```

### Essential Cookies

Douyin requires these cookies:
- `odin_tt` - Device tracking
- `ttwid` - User tracking
- `passport_csrf_token` - Security token
- `s_v_web_id` - Session ID

If any are missing, authentication will fail.

### Cookie Expiration

Douyin cookies typically expire after:
- **7-30 days** for logged-in sessions
- **1 day** for anonymous sessions

**Re-import when expired**:
```bash
# Get fresh cookies from browser
la auth import --platform douyin --cookies "new_cookie_string"
```

## Cookie Management

### View Cookie Files

```bash
# Bilibili
cat config/cookies/bilibili_cookies.txt

# Douyin
cat config/cookies/douyin_cookies.txt
```

### Delete Cookies

```bash
# Delete specific platform
la auth logout --platform bilibili
la auth logout --platform douyin

# Manual deletion
rm config/cookies/bilibili_cookies.txt
rm config/cookies/douyin_cookies.txt
```

### Cookie File Format

Cookies are stored in **Netscape format** (yt-dlp compatible):

```
# Netscape HTTP Cookie File
.bilibili.com	TRUE	/	FALSE	0	SESSDATA	your_sessdata_value
.bilibili.com	TRUE	/	FALSE	0	DedeUserID	your_user_id
```

## Security & Privacy

### ⚠️ Important Security Notes

1. **Never share cookie files** - They contain your login credentials
2. **Never commit to git** - Cookie files are in `.gitignore`
3. **Cookie files are sensitive** - Treat like passwords
4. **Rotate cookies periodically** - Re-login every few weeks
5. **Use trusted devices** - Only extract cookies from your own devices

### File Permissions

```bash
# Restrict access to cookie files
chmod 600 config/cookies/*.txt
```

## Troubleshooting

### Bilibili Issues

**Error: "QR code scan timeout"**
- Scan faster within 180 seconds
- Or increase timeout: `--timeout 300`

**Error: "Cookies not working for download"**
- Cookies may have expired
- Re-login: `la auth logout --platform bilibili && la auth login --platform bilibili`

**Error: "SSL/Network error during download"**
- This is B站 CDN issue, not cookie issue
- Try with cookies: `la auth login --platform bilibili` first
- Then download: `la video <url>`

### Douyin Issues

**Error: "Invalid cookie format"**
- Ensure you copied the complete cookie string
- Should contain multiple `name=value` pairs separated by `;`
- Example: `name1=value1; name2=value2; name3=value3`

**Error: "Essential cookies missing"**
- Re-check you copied the full cookie string
- Must include: `odin_tt`, `ttwid`, `passport_csrf_token`, `s_v_web_id`

**Error: "Cookies expired"**
- Douyin cookies expire frequently
- Extract fresh cookies from browser
- Re-import: `la auth import --platform douyin --cookies "..."`

## Advanced Usage

### Multiple Accounts

```bash
# Login with account 1
la auth login --platform bilibili
# Download video
la video <url1>

# Switch to account 2
la auth logout --platform bilibili
la auth login --platform bilibili
# Download another video
la video <url2>
```

### Cookie Backup

```bash
# Backup cookies
cp config/cookies/bilibili_cookies.txt backup/bilibili_$(date +%Y%m%d).txt
cp config/cookies/douyin_cookies.txt backup/douyin_$(date +%Y%m%d).txt

# Restore cookies
cp backup/bilibili_20250101.txt config/cookies/bilibili_cookies.txt
```

### Manual Cookie Editing

You can manually edit cookie files in Netscape format:

```bash
# Open in editor
nano config/cookies/bilibili_cookies.txt

# Format:
# domain	flag	path	secure	expiration	name	value
.bilibili.com	TRUE	/	FALSE	0	SESSDATA	your_value_here
```

## Summary

| Platform | Method | Command | Automatic |
|----------|--------|---------|-----------|
| Bilibili | QR Login | `la auth login --platform bilibili` | ✅ Yes |
| Douyin | Manual Import | `la auth import --platform douyin --cookies "..."` | ❌ No |

**Bilibili**: Use automatic QR login (easiest)

**Douyin**: Import cookies manually from browser (one-time setup, periodic refresh)

Both platforms will automatically use saved cookies for video downloads!