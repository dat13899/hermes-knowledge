#!/usr/bin/env python3
"""Tạo bài báo đặc sản Bắc Ninh trên Google Docs với định dạng Times New Roman."""

import sys
import os
import json

# Add google_api.py to path
SCRIPT_DIR = r"C:\Users\datel\AppData\Local\hermes\skills\productivity\google-workspace\scripts"
sys.path.insert(0, SCRIPT_DIR)
from google_api import get_credentials, build_service

DOC_ID = "1BqLjMDIP1xUM_6zcgNApBZNndMWR_SEtceFR7ImxaBs"

def build_content():
    """Build article content as list of (text, is_heading_bool, font_size)."""
    items = []
    
    # Title
    items.append(("Đặc Sản Tỉnh Bắc Ninh – Tinh Hoa Ẩm Thực Kinh Bắc", True, 16))
    
    # Intro
    items.append((
        "Bắc Ninh là vùng đất Kinh Bắc cổ kính, nơi có nền văn hóa ẩm thực phong phú và "
        "đa dạng. Nằm ở cửa ngõ phía Bắc thủ đô Hà Nội, Bắc Ninh từ lâu đã nổi tiếng với "
        "những làn điệu Quan họ du dương và những món ăn dân dã đậm đà hương vị quê hương. "
        "Dưới đây là những đặc sản nổi bật làm nên tên tuổi ẩm thực xứ Kinh Bắc.",
        False, 14
    ))
    
    # Section 1: Bánh Phu Thê
    items.append(("1. Bánh Phu Thê Đình Bảng", True, 14))
    items.append((
        "Bánh Phu Thê hay còn gọi là bánh Su Sê, có xuất xứ từ làng Đình Bảng, thành phố "
        "Từ Sơn, Bắc Ninh. Tên gọi \"Phu Thê\" mang ý nghĩa vợ chồng – tượng trưng cho sự "
        "gắn kết, thủy chung. Bánh được làm từ bột nếp, đỗ xanh, cùi dừa, đường kính và "
        "nước hoa bưởi, gói trong lá chuối tạo thành hình chữ nhật xinh xắn. Bánh có vị "
        "ngọt thanh, thơm mùi lá chuối và nước hoa bưởi, là món không thể thiếu trong các "
        "dịp lễ cưới hỏi, hội hè.",
        False, 14
    ))
    
    # Section 2: Nem Bùi
    items.append(("2. Nem Bùi (Ninh Xá)", True, 14))
    items.append((
        "Nem Bùi là đặc sản nổi tiếng của làng Ninh Xá, nay thuộc thành phố Bắc Ninh. "
        "Điểm đặc biệt của nem Bùi là phần nhân được làm từ thịt lợn nạc xay nhuyễn, trộn "
        "với mộc nhĩ, hành khô, tiêu bột và nước mắm ngon. Nem được gói trong lá đinh lăng, "
        "tạo nên hương vị thơm ngon khó cưỡng. Khi thưởng thức, nem Bùi có vị chua dịu, "
        "ngọt thanh của thịt, hòa quyện với mùi thơm đặc trưng của lá đinh lăng.",
        False, 14
    ))
    
    # Section 3: Bánh Tẻ
    items.append(("3. Bánh Tẻ Làng Chờ", True, 14))
    items.append((
        "Bánh tẻ làng Chờ (phường Yên Phong) là một trong những đặc sản lâu đời của Bắc "
        "Ninh. Bánh được làm từ bột gạo tẻ pha loãng, hấp chín trong khuôn lá dong. Bánh "
        "tẻ có vị mềm, dẻo, thơm mùi lá dong, thường được chấm với nước mắm pha chua ngọt "
        "hoặc ăn kèm với chả lụa.",
        False, 14
    ))
    
    # Section 4: Bánh Khúc
    items.append(("4. Bánh Khúc Làng Diềm", True, 14))
    items.append((
        "Bánh khúc làng Diềm (xã Viêm Xá, thành phố Bắc Ninh) được làm từ rau khúc – một "
        "loại rau mọc hoang trên đồng ruộng. Rau khúc được giã nhuyễn trộn với bột nếp, "
        "tạo nên màu xanh đặc trưng. Bánh có nhân đỗ xanh, hành phi và thịt ba chỉ, gói "
        "trong lá chuối rồi hấp chín. Bánh khúc có hương vị bùi bùi, thơm thơm của rau "
        "khúc hòa quyện với vị béo của thịt và nhân đỗ.",
        False, 14
    ))
    
    # Section 5: Rượu Nếp
    items.append(("5. Rượu Nếp Làng Cẩm", True, 14))
    items.append((
        "Rượu nếp làng Cẩm (xã Cẩm Giang, huyện Gia Bình) là đặc sản nức tiếng xứ Kinh "
        "Bắc. Rượu được nấu từ gạo nếp cái hoa vàng, bằng men lá truyền thống và nước "
        "giếng cổ trong làng. Rượu nếp làng Cẩm có vị ngọt, thơm nồng nàn, uống vào ấm "
        "bụng, để lại dư vị khó quên.",
        False, 14
    ))
    
    # Section 6: Tương & Bánh Tro
    items.append(("6. Tương Đình Tổ & Bánh Tro", True, 14))
    items.append((
        "Tương Đình Tổ (Thuận Thành) là loại tương được làm từ gạo nếp, đỗ tương và muối, "
        "ủ lên men tự nhiên. Tương có màu vàng óng, vị mặn ngọt hài hòa, dùng làm nước "
        "chấm rau luộc, thịt luộc hoặc ăn với bánh tro. Bánh tro (hay bánh gio) là loại "
        "bánh được làm từ gạo nếp ngâm trong nước tro (nước than thực vật), gói trong lá "
        "dong và luộc chín. Bánh tro có vị thanh, mát, thường chấm với mật mía hoặc ăn "
        "cùng tương Đình Tổ.",
        False, 14
    ))
    
    # Section 7: Phở Gan Cháy
    items.append(("7. Phở Gan Cháy Đáp Cầu", True, 14))
    items.append((
        "Phở gan cháy Đáp Cầu (thành phố Bắc Ninh) là món ăn đặc biệt không thể bỏ qua "
        "khi đến xứ Kinh Bắc. Điểm đặc biệt của món phở này là gan lợn được chiên cháy "
        "cạnh, ăn giòn rụm, kết hợp với nước dùng ngọt thanh từ xương hầm, bánh phở mềm "
        "thơm.",
        False, 14
    ))
    
    # Conclusion
    items.append(("Kết Luận", True, 14))
    items.append((
        "Ẩm thực Bắc Ninh là sự hòa quyện giữa truyền thống và tinh tế, giữa hương vị "
        "dân dã và những nét văn hóa độc đáo của vùng đất Kinh Bắc. Mỗi món ăn không chỉ "
        "là sự kết hợp hài hòa của nguyên liệu mà còn là cả một câu chuyện lịch sử, văn "
        "hóa được gìn giữ qua nhiều thế hệ.",
        False, 14
    ))
    
    return items


def main():
    service = build_service("docs", "v1")
    
    # Step 1: Get current doc state
    doc = service.documents().get(documentId=DOC_ID).execute()
    existing_text = ""
    for element in doc.get("body", {}).get("content", []):
        for pe in element.get("paragraph", {}).get("elements", []):
            tr = pe.get("textRun", {})
            if tr.get("content"):
                existing_text += tr["content"]
    
    print(f"Doc title: {doc.get('title')}")
    print(f"Existing text length: {len(existing_text.strip())}")
    
    if existing_text.strip():
        print("Doc already has content. Clearing it first...")
        # Get end index
        end_idx = 1
        for element in doc.get("body", {}).get("content", []):
            ei = element.get("endIndex")
            if isinstance(ei, int) and ei > end_idx:
                end_idx = ei
        # Delete existing content (keep trailing newline)
        if end_idx > 2:
            service.documents().batchUpdate(
                documentId=DOC_ID,
                body={"requests": [{
                    "deleteContentRange": {
                        "range": {"startIndex": 1, "endIndex": end_idx - 1}
                    }
                }]}
            ).execute()
            print("Cleared existing content.")
    
    # Step 2: Build content
    items = build_content()
    
    # Build full text and track character offsets
    full_text = ""
    offsets = []  # list of (start, end, is_heading, font_size)
    
    for text, is_heading, font_size in items:
        start = len(full_text)
        # Add a newline before sections (not before title and intro)
        if offsets:  # not the first item
            full_text += "\n"
            start += 1
        
        segment = text + "\n"
        full_text += segment
        end = len(full_text)
        offsets.append((start, end, is_heading, font_size))
    
    # Step 3: Insert all text in one batch
    print(f"Inserting {len(full_text)} characters...")
    insert_requests = [{
        "insertText": {
            "location": {"index": 1},
            "text": full_text
        }
    }]
    result = service.documents().batchUpdate(
        documentId=DOC_ID,
        body={"requests": insert_requests}
    ).execute()
    print("Text inserted successfully.")
    
    # Step 4: Apply formatting via batchUpdate
    print("Applying formatting...")
    style_requests = []
    
    for start, end, is_heading, font_size in offsets:
        # Docs indices: our text starts at index 1 (after the implicit newline)
        # So start_offset = start + 1, end_offset = end + 1
        si = start + 1
        ei = end + 1
        style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": si, "endIndex": ei},
                "textStyle": {
                    "weightedFontFamily": {
                        "fontFamily": "Times New Roman",
                        "weight": 700 if is_heading else 400
                    },
                    "fontSize": {"magnitude": font_size, "unit": "PT"},
                    "foregroundColor": {
                        "color": {"rgbColor": {"red": 0.0, "green": 0.0, "blue": 0.0}}
                    },
                    "bold": is_heading,
                },
                "fields": "weightedFontFamily,fontSize,foregroundColor,bold"
            }
        })
    
    # Also set line spacing to 1.15 for readability
    for start, end, is_heading, font_size in offsets:
        si = start + 1
        ei = end + 1
        style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": si, "endIndex": ei},
                "paragraphStyle": {
                    "lineSpacing": 115,  # 1.15 line spacing
                    "spaceAbove": {"magnitude": 0, "unit": "PT"},
                    "spaceBelow": {"magnitude": 6 if not is_heading else 12, "unit": "PT"},
                },
                "fields": "lineSpacing,spaceAbove,spaceBelow"
            }
        })
    
    if style_requests:
        # Google Docs API limits batch size - split if needed
        batch_size = 50
        for i in range(0, len(style_requests), batch_size):
            batch = style_requests[i:i+batch_size]
            service.documents().batchUpdate(
                documentId=DOC_ID,
                body={"requests": batch}
            ).execute()
            print(f"  Formatted batch {i//batch_size + 1}/{(len(style_requests)-1)//batch_size + 1}")
    
    print("Formatting applied successfully!")
    
    # Step 5: Update title
    service.documents().batchUpdate(
        documentId=DOC_ID,
        body={"requests": [{
            "updateDocumentStyle": {
                "documentStyle": {
                    "background": {"color": {"color": {"rgbColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}}}
                },
                "fields": "background"
            }
        }]}
    ).execute()
    
    url = f"https://docs.google.com/document/d/{DOC_ID}/edit"
    print(f"\nArticle created successfully!")
    print(f"URL: {url}")
    
    # Return JSON for consumption
    result = {
        "url": url,
        "documentId": DOC_ID,
        "characters": len(full_text),
        "sections": len(items)
    }
    print(f"JSON_OUTPUT:{json.dumps(result, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
