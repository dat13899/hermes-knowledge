#!/usr/bin/env python3
"""Insert images into Google Doc at section positions."""
import sys, json, time
SCRIPT_DIR = r"C:\Users\datel\AppData\Local\hermes\skills\productivity\google-workspace\scripts"
sys.path.insert(0, SCRIPT_DIR)
from google_api import build_service

DOC_ID = "1BqLjMDIP1xUM_6zcgNApBZNndMWR_SEtceFR7ImxaBs"

# Image file IDs uploaded to Drive (need to be publicly viewable)
images = [
    ("Bánh Phu Thê", "1WhOWdQg0a3nA-Nb7BXYjZ-oyQ-IyqI7s"),
    ("Nem Bùi", "1oxYSgbDUmZtBMud6kKYAkxZi9HXXbb3G"),
    ("Bánh Tẻ", "1CvcogBmFyJEGJhmNAZ379MEN64At8fZq"),
    ("Rượu Nếp", "1QJSZq_Ul3-RgaO48_oa-YnurCR3x1iE_"),
    ("Phở", "1PbCN-yr3ZBRT11X64Ixtee3Uz_6hoVfm"),
    ("Tương", "1kcZEilYe1NC5otQrxaSwgi-CvR0KcQsU"),
    # Bánh Khúc - use pho image as fallback
]

# Map each image to the section heading text it belongs to
section_image_map = {
    "1. Bánh Phu Thê": ("Bánh Phu Thê", "1WhOWdQg0a3nA-Nb7BXYjZ-oyQ-IyqI7s"),
    "2. Nem Bùi": ("Nem Bùi", "1oxYSgbDUmZtBMud6kKYAkxZi9HXXbb3G"),
    "3. Bánh Tẻ": ("Bánh Tẻ", "1CvcogBmFyJEGJhmNAZ379MEN64At8fZq"),
    "4. Bánh Khúc": ("Bánh Khúc", None),  # No image found
    "5. Rượu Nếp": ("Rượu Nếp", "1QJSZq_Ul3-RgaO48_oa-YnurCR3x1iE_"),
    "6. Tương": ("Tương", "1kcZEilYe1NC5otQrxaSwgi-CvR0KcQsU"),
    "7. Phở Gan": ("Phở", "1PbCN-yr3ZBRT11X64Ixtee3Uz_6hoVfm"),
}

def share_file(drive_service, file_id):
    """Make a Drive file publicly viewable."""
    permission = {"type": "anyone", "role": "reader"}
    try:
        drive_service.permissions().create(
            fileId=file_id, body=permission
        ).execute()
        return True
    except Exception as e:
        print(f"  Share error for {file_id}: {e}")
        return False

def get_image_uri(file_id):
    """Get the image URI for Docs API."""
    return f"https://lh3.googleusercontent.com/d/{file_id}"

def main():
    docs_service = build_service("docs", "v1")
    drive_service = build_service("drive", "v3")
    
    # Step 1: Share all image files publicly
    print("Sharing image files...")
    for name, fid in images:
        if fid:
            share_file(drive_service, fid)
            print(f"  Shared: {name}")
    
    # Step 2: Get current doc structure
    doc = docs_service.documents().get(documentId=DOC_ID).execute()
    content = doc["body"]["content"]
    
    # Step 3: Find insertion indices for each section
    # Strategy: find each section heading's endIndex, insert image right after
    insertions = []  # (index, file_id, label) - index BEFORE any insertions
    
    for element in content:
        text = ""
        for pe in element.get("paragraph", {}).get("elements", []):
            text += pe.get("textRun", {}).get("content", "")
        text = text.strip()
        
        # Match section headings
        for section_key, (label, file_id) in section_image_map.items():
            if text.startswith(section_key) and file_id:
                # Insert after the paragraph that contains this heading
                # The heading paragraph endIndex is where we insert
                ei = element.get("endIndex")
                if ei:
                    insertions.append((ei - 1, file_id, label))
                    break  # Only match once
                else:
                    insertions.append((element.get("startIndex", 1) + len(text) + 1, file_id, label))
                    break
    
    if not insertions:
        # Fallback: find by position
        print("No sections matched by text. Using positional fallback...")
        # From doc structure: headings at indices 366, 817, 1232, 1519, 1907, 2192, 2638
        fallback_indices = [
            (366, "1WhOWdQg0a3nA-Nb7BXYjZ-oyQ-IyqI7s", "Bánh Phu Thê"),   # after "1. Bánh Phu Thê..."
            (817, "1oxYSgbDUmZtBMud6kKYAkxZi9HXXbb3G", "Nem Bùi"),        # after "2. Nem Bùi..."
            (1232, "1CvcogBmFyJEGJhmNAZ379MEN64At8fZq", "Bánh Tẻ"),       # after "3. Bánh Tẻ..."
            # Index 1519 = Bánh Khúc, skip (no image)
            (1907, "1QJSZq_Ul3-RgaO48_oa-YnurCR3x1iE_", "Rượu Nếp"),     # after "5. Rượu Nếp..."
            (2192, "1kcZEilYe1NC5otQrxaSwgi-CvR0KcQsU", "Tương"),         # after "6. Tương..."
            (2638, "1PbCN-yr3ZBRT11X64Ixtee3Uz_6hoVfm", "Phở"),           # after "7. Phở Gan..."
        ]
        insertions = fallback_indices
    
    print(f"\nInsertions found: {len(insertions)}")
    for idx, fid, label in insertions:
        print(f"  Index {idx}: {label} ({fid})")
    
    # Step 4: Insert images from bottom to top (to preserve indices)
    insertions.sort(key=lambda x: x[0], reverse=True)
    
    for idx, file_id, label in insertions:
        uri = get_image_uri(file_id)
        print(f"\nInserting {label} at index {idx}...")
        
        request = {
            "insertInlineImage": {
                "location": {"index": idx},
                "uri": uri,
                "objectSize": {
                    "height": {"magnitude": 180, "unit": "PT"},  # ~2.5 inches
                    "width": {"magnitude": 324, "unit": "PT"},   # ~4.5 inches (landscape)
                }
            }
        }
        
        try:
            docs_service.documents().batchUpdate(
                documentId=DOC_ID,
                body={"requests": [request]}
            ).execute()
            print(f"  OK")
        except Exception as e:
            print(f"  ERROR: {e}")
            # Try alternative URI format
            alt_uri = f"https://drive.google.com/uc?export=view&id={file_id}"
            try:
                docs_service.documents().batchUpdate(
                    documentId=DOC_ID,
                    body={"requests": [{
                        "insertInlineImage": {
                            "location": {"index": idx},
                            "uri": alt_uri,
                            "objectSize": {
                                "height": {"magnitude": 180, "unit": "PT"},
                                "width": {"magnitude": 324, "unit": "PT"},
                            }
                        }
                    }]}
                ).execute()
                print(f"  OK (alt URI)")
            except Exception as e2:
                print(f"  ERROR (alt): {e2}")
        
        time.sleep(1)
    
    print(f"\nDone! Image insertion complete.")
    print(f"URL: https://docs.google.com/document/d/{DOC_ID}/edit")

if __name__ == "__main__":
    main()
