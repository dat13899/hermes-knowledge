#!/usr/bin/env python3
"""Re-align images in Google Doc - center them in their own paragraphs."""
import sys, json, time
SCRIPT_DIR = r"C:\Users\datel\AppData\Local\hermes\skills\productivity\google-workspace\scripts"
sys.path.insert(0, SCRIPT_DIR)
from google_api import build_service

DOC_ID = "1BqLjMDIP1xUM_6zcgNApBZNndMWR_SEtceFR7ImxaBs"
service = build_service("docs", "v1")

# Step 1: Read current doc to find image positions
doc = service.documents().get(documentId=DOC_ID).execute()
content = doc["body"]["content"]

# Find all images with their parent paragraph info
images = []
for i, e in enumerate(content):
    for pe in e.get("paragraph", {}).get("elements", []):
        if "inlineObjectElement" in pe:
            images.append({
                "item_index": i,
                "start_index": pe.get("startIndex"),
                "end_index": pe.get("endIndex"),
                "obj_id": pe["inlineObjectElement"].get("inlineObjectId"),
                "para_start": e.get("startIndex"),
                "para_end": e.get("endIndex"),
                # Get any text in this same paragraph
                "para_text": "".join(
                    pe2.get("textRun", {}).get("content", "")
                    for pe2 in e.get("paragraph", {}).get("elements", [])
                    if "textRun" in pe2
                ).strip()
            })

print(f"Found {len(images)} images:")
for img in images:
    print(f"  idx={img['start_index']} obj={img['obj_id']} "
          f"para=[{img['para_start']}→{img['para_end']}] "
          f"text='{img['para_text'][:50]}'")

# Step 2: Insert a paragraph break (newline) right before each image
# so the image moves to its own paragraph
# Work from bottom up to preserve indices
images_sorted = sorted(images, key=lambda x: x["start_index"], reverse=True)

print("\n--- Inserting paragraph breaks before images ---")
for img in images_sorted:
    insert_idx = img["start_index"]
    print(f"  Inserting \\n at index {insert_idx} ...")
    try:
        service.documents().batchUpdate(
            documentId=DOC_ID,
            body={"requests": [{
                "insertText": {
                    "location": {"index": insert_idx},
                    "text": "\n"
                }
            }]}
        ).execute()
        print(f"    OK")
    except Exception as e:
        print(f"    ERROR: {e}")
    time.sleep(0.5)

# Step 3: Read doc again and center image paragraphs
print("\n--- Centering image paragraphs ---")
doc2 = service.documents().get(documentId=DOC_ID).execute()
content2 = doc2["body"]["content"]

# Find all paragraphs that now contain ONLY an image (no visible text)
for i, e in enumerate(content2):
    has_image = False
    has_text = False
    for pe in e.get("paragraph", {}).get("elements", []):
        if "inlineObjectElement" in pe:
            has_image = True
        if "textRun" in pe and pe.get("textRun", {}).get("content", "").strip():
            has_text = True
    
    if has_image and not has_text:
        # This paragraph is an image-only paragraph - center it!
        ps = e.get("startIndex", 1)
        pe = e.get("endIndex", 2)
        print(f"  Centering image-only para [{ps}→{pe}] (item {i})")
        try:
            service.documents().batchUpdate(
                documentId=DOC_ID,
                body={"requests": [{
                    "updateParagraphStyle": {
                        "range": {"startIndex": ps, "endIndex": pe},
                        "paragraphStyle": {
                            "alignment": "CENTER",
                            "spaceAbove": {"magnitude": 6, "unit": "PT"},
                            "spaceBelow": {"magnitude": 6, "unit": "PT"},
                            "lineSpacing": 100
                        },
                        "fields": "alignment,spaceAbove,spaceBelow,lineSpacing"
                    }
                }]}
            ).execute()
            print(f"    OK")
        except Exception as e:
            print(f"    ERROR: {e}")
        time.sleep(0.5)
    elif has_image and has_text:
        ps = e.get("startIndex", 1)
        pe = e.get("endIndex", 2)
        text_sample = ""
        for pe2 in e.get("paragraph", {}).get("elements", []):
            if "textRun" in pe2:
                text_sample = pe2.get("textRun", {}).get("content", "").strip()[:30]
                break
        print(f"  SKIP mixed para [{ps}→{pe}] (item {i}) - has both image and text '{text_sample}'")

print(f"\nDone! All images realigned.")
print(f"https://docs.google.com/document/d/{DOC_ID}/edit")
