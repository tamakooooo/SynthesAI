# Bilibili Login QR Code

Get Bilibili (B站) login QR code for video download authentication.

## Usage

```bash
la auth login --platform bilibili
```

## QR Code Generation Process

### 1. API Endpoints

```
Generate QR: GET https://passport.bilibili.com/x/passport-login/web/qrcode/generate
Poll Status: GET https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={key}
```

### 2. Generate QR Code

```python
import requests

# Generate QR code
response = requests.get(
    "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com/",
    }
)

data = response.json()["data"]
qr_url = data["url"]  # QR code URL to encode
qrcode_key = data["qrcode_key"]  # Session key for polling
```

### 3. Convert QR to Image (for agents that can send images)

```python
import qrcode
from pathlib import Path

# Create QR code image
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

qr.add_data(qr_url)
qr.make(fit=True)

# Generate PNG image
img = qr.make_image(fill_color="black", back_color="white")

# Save to file
output_path = Path("bilibili_qr.png")
img.save(output_path)

print(f"QR image saved to: {output_path}")
```

### 4. Poll for Scan Status

```python
import time

timeout = 180  # seconds
start_time = time.time()

while time.time() - start_time < timeout:
    response = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
        params={"qrcode_key": qrcode_key}
    )
    
    status = response.json()["data"]["code"]
    
    if status == 0:
        # Login successful - extract cookies
        cookies = extract_cookies_from_response(response.json())
        print("Login successful!")
        break
    elif status == 86038:
        print("QR expired")
        break
    elif status == 86090:
        print("Scanned, waiting for confirmation...")
    elif status == 86101:
        print("Waiting for scan...")
    
    time.sleep(2)
```

## Status Codes

| Code | Meaning |
|------|---------|
| 0 | Scanned and confirmed (success) |
| 86038 | QR code expired |
| 86090 | Scanned but not confirmed |
| 86101 | Not scanned yet |

## Complete Example: Get QR as Image

```python
#!/usr/bin/env python3
"""Generate Bilibili login QR code as PNG image."""

import qrcode
import requests
from pathlib import Path

def get_bilibili_qr_image() -> Path:
    """Generate Bilibili login QR and save as PNG."""
    
    # 1. Get QR URL from Bilibili API
    response = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com/",
        }
    )
    
    data = response.json()["data"]
    qr_url = data["url"]
    qrcode_key = data["qrcode_key"]
    
    print(f"QR Session Key: {qrcode_key}")
    print(f"QR URL: {qr_url}")
    
    # 2. Generate QR image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 3. Save to file
    output_path = Path("bilibili_login_qr.png")
    img.save(output_path)
    
    print(f"\n✅ QR image saved to: {output_path}")
    print("   Send this image to user for scanning with Bilibili App")
    
    return output_path

if __name__ == "__main__":
    path = get_bilibili_qr_image()
    print(f"\nImage path: {path}")
```

## Dependencies

```bash
pip install qrcode[pil] requests
```

## Cookie Storage Location

After successful login, cookies are saved to:
```
config/cookies/bilibili_cookies.txt
```

Format: Netscape HTTP Cookie File (yt-dlp compatible)

## For Agent Integration

When integrating with messaging agents (Feishu, Discord, etc.):

1. Generate QR image using the code above
2. Send the image file to user via agent's image upload capability
3. Poll for scan status
4. On success, save cookies and notify user

Example agent flow:
```
User: 帮我登录B站
Agent: [Generates QR] → [Sends QR image] → "请用B站App扫码登录"
User: [Scans QR]
Agent: [Polls status] → "登录成功！现在可以下载视频了"
```