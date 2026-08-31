#!/usr/bin/env python3
"""Search Wikimedia Commons for Bac Ninh food images, download & upload to Drive."""
import json, urllib.request, urllib.parse, os, sys, io

HEADERS = {"User-Agent": "Mozilla/5.0"}
SCRIPT_DIR = r"C:\Users\datel\AppData\Local\hermes\skills\productivity\google-workspace\scripts"
sys.path.insert(0, SCRIPT_DIR)
from google_api import build_service

def wikimedia_search(query, limit=3):
    """Search Wikimedia Commons and return list of (title, pageid)"""
    params = urllib.parse.urlencode({
        "action": "query", "list": "search",
        "srsearch": query, "srnamespace": "6",
        "format": "json", "srlimit": limit
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return [(p["title"], p["pageid"]) for p in data.get("query", {}).get("search", [])]

def get_image_url(title):
    """Get the direct image URL from a File page title."""
    params = urllib.parse.urlencode({
        "action": "query", "titles": title,
        "prop": "imageinfo", "iiprop": "url|mime",
        "format": "json", "iiurlwidth": 800
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        iinfo = page.get("imageinfo", [])
        if iinfo:
            return iinfo[0].get("url")
    return None

def upload_to_drive(drive_service, image_url, filename):
    """Upload an image from URL to Google Drive and return file ID."""
    # Download image bytes
    req = urllib.request.Request(image_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        image_data = resp.read()
    
    # Upload to Drive
    from googleapiclient.http import MediaIoBaseUpload
    mime = resp.headers.get("Content-Type", "image/jpeg")
    media = MediaIoBaseUpload(io.BytesIO(image_data), mime, resumable=True)
    
    file_meta = {"name": filename, "mimeType": mime}
    file = drive_service.files().create(
        body=file_meta, media_body=media, fields="id,webContentLink"
    ).execute()
    
    return file["id"], file.get("webContentLink", "")

def main():
    searches = [
        ("Bánh Phu Thê", "banh phu the Vietnamese cake"),
        ("Bánh Tẻ", "banh te Vietnamese cake"),
        ("Bánh Khúc", "banh khuc Vietnamese cake"),
        ("Nem Bùi", "nem Vietnamese spring roll"),
        ("Rượu Nếp", "Vietnamese sticky rice wine"),
        ("Phở Gan Cháy", "Vietnamese noodle soup pho"),
        ("Tương Bần", "Vietnamese soybean paste tuong"),
    ]
    
    drive_service = build_service("drive", "v3")
    
    results = {}
    for label, query in searches:
        pages = wikimedia_search(query, limit=2)
        if pages:
            title, pageid = pages[0]
            img_url = get_image_url(title)
            if img_url:
                safe_name = label.replace(" ", "_").replace("/", "_") + ".jpg"
                try:
                    file_id, web_link = upload_to_drive(drive_service, img_url, safe_name)
                    results[label] = {
                        "file_id": file_id,
                        "web_link": web_link,
                        "image_url": img_url
                    }
                    print(f"OK: {label} -> {file_id}")
                except Exception as e:
                    print(f"UPLOAD FAIL: {label}: {e}")
            else:
                print(f"NO URL: {label}")
        else:
            print(f"NO RESULTS: {label}")
    
    print(f"\nSUMMARY: {json.dumps(results, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    main()
