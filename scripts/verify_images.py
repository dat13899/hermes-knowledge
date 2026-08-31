#!/usr/bin/env python3
"""Verify images in Google Doc."""
import sys
SCRIPT_DIR = r"C:\Users\datel\AppData\Local\hermes\skills\productivity\google-workspace\scripts"
sys.path.insert(0, SCRIPT_DIR)
from google_api import build_service

DOC_ID = "1BqLjMDIP1xUM_6zcgNApBZNndMWR_SEtceFR7ImxaBs"
service = build_service("docs", "v1")
doc = service.documents().get(documentId=DOC_ID).execute()

print("=== DOC STRUCTURE ===")
img_count = 0
for i, e in enumerate(doc["body"]["content"]):
    for pe in e.get("paragraph", {}).get("elements", []):
        if "inlineObjectElement" in pe:
            obj_id = pe["inlineObjectElement"].get("inlineObjectId", "")
            img_count += 1
            print(f"[ITEM {i}] IMAGE #{img_count} (objId={obj_id}) idx={pe.get('startIndex')}")
        text = pe.get("textRun", {}).get("content", "")
        if text.strip():
            t = text.strip()[:80]
            print(f"[ITEM {i}] TEXT: {t}")

print(f"\n=== SUMMARY ===")
print(f"Images found: {img_count}")
print(f"Total structural elements: {len(doc['body']['content'])}")

# Check inlineObjects
inline_objects = doc.get("inlineObjects", {})
print(f"Inline object resources: {len(inline_objects)}")
for obj_id, obj_data in inline_objects.items():
    print(f"  {obj_id}: {obj_data.get('inlineObjectProperties', {}).get('embeddedObject', {}).get('imageProperties', {}).get('contentUri', '')[:80]}")
