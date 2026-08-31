#!/usr/bin/env python3
"""Read Google Doc structure to find image insertion positions."""
import sys, json
SCRIPT_DIR = r"C:\Users\datel\AppData\Local\hermes\skills\productivity\google-workspace\scripts"
sys.path.insert(0, SCRIPT_DIR)
from google_api import build_service

DOC_ID = "1BqLjMDIP1xUM_6zcgNApBZNndMWR_SEtceFR7ImxaBs"
service = build_service("docs", "v1")
doc = service.documents().get(documentId=DOC_ID).execute()

print(json.dumps({"title": doc.get("title"), "content": [{
    "startIndex": e.get("startIndex"),
    "endIndex": e.get("endIndex"),
    "text": "".join(
        pe.get("textRun", {}).get("content", "")
        for pe in e.get("paragraph", {}).get("elements", [])
    )[:100]
} for e in doc["body"]["content"]]}, ensure_ascii=False, indent=2))
