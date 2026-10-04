import json
import re
import os
from typing import Dict
from core.contracts import AIProviderContract

class SEOOptimizerEngine:
    def __init__(self, adapter: AIProviderContract):
        self.adapter = adapter

    def calculate_timestamps(self, script_dict: dict, asset_dict: dict) -> list:
        # Mapping thời gian thực tế từ Asset
        actual_durations = {}
        for a_sc in asset_dict.get('assets', []):
            actual_durations[a_sc['scene_number']] = a_sc.get('duration_seconds', 10)
            
        timestamps = []
        current_time_seconds = 0
        
        # Duyệt qua các scenes, nhóm theo chapter
        current_chapter = None
        
        for sc in script_dict.get('scenes', []):
            c_num = sc.get('chapter_number', 1)
            s_num = sc['scene_number']
            duration = actual_durations.get(s_num, 10)
            
            # Ghi nhận thời gian mỗi khi chuyển qua chương mới
            if current_chapter != c_num:
                mins, secs = divmod(int(current_time_seconds), 60)
                time_str = f"{mins:02d}:{secs:02d}"
                
                timestamps.append({
                    'chapter_number': c_num,
                    'time_str': time_str,
                    'seconds': int(current_time_seconds)
                })
                current_chapter = c_num
                
            current_time_seconds += duration
            
        return timestamps

    def generate_seo_metadata(self, title: str, summary: str) -> dict:
        prompt = f"""
        Nhiệm vụ: Viết bộ thông tin chuẩn SEO cho video YouTube.
        Chủ đề: {title}
        Nội dung chính: {summary}
        
        YÊU CẦU:
        1. Tiêu đề (title): Dài dưới 60 ký tự, giật tít, khơi gợi tò mò.
        2. Mô tả (description): 2-3 đoạn ngắn, cuốn hút. Có lời kêu gọi Like/Subscribe.
        3. Tags: 15-20 từ khóa thịnh hành cách nhau bằng dấu phẩy.
        4. Thumbnail Concept: Gợi ý cách thiết kế ảnh bìa (Yếu tố hình ảnh chính, text đập vào mắt người xem).
        
        TRẢ VỀ DUY NHẤT ĐỊNH DẠNG JSON. KHÔNG MARKDOWN.
        {{
            "title": "...",
            "description": "...",
            "tags": "...",
            "thumbnail_concept": "..."
        }}
        """
        result = self.adapter.generate_text(prompt, expected_format='json')
        
        # Trích xuất JSON
        text = result.strip()
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        match = re.search(r'\{.*\}', text.strip(), re.DOTALL)
        if match: text = match.group(0)
            
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"[Engine] Lỗi Parse JSON SEO: {e}")
            return {}

    def format_upload_info(self, script_id: int, title: str, script_dict: dict, asset_dict: dict):
        print("\n[Engine] Bước 1: Tính toán Timestamps Youtube...")
        timestamps = self.calculate_timestamps(script_dict, asset_dict)
        
        print(f"[Engine] Bước 2: Gọi Gemini viết Tiêu đề và Mô tả chuẩn SEO...")
        # Tìm tóm tắt tổng thể
        summary = "Video về chủ đề " + title
        
        seo_data = self.generate_seo_metadata(title, summary)
        if not seo_data:
            return False
            
        # Ghép Timestamps với Tên Chương
        print("[Engine] Bước 3: Ghép nối dữ liệu và xuất file Text...")
        
        # Lấy tên chapter từ script (giả lập bằng cách moi trong scenes)
        chapter_names = {}
        for ts in timestamps:
            c_num = ts['chapter_number']
            chapter_names[c_num] = f"Chương {c_num}" # Đặt mặc định
            
        timestamp_str = "NỘI DUNG VIDEO:\n"
        for ts in timestamps:
            timestamp_str += f"{ts['time_str']} - {chapter_names[ts['chapter_number']]}\n"
            
        seo_data['timestamps_text'] = timestamp_str
        
        # Lưu ra File
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        file_path = os.path.join(project_dir, 'YouTube_Upload_Info.txt')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=== YOUTUBE UPLOAD METADATA ===\n\n")
            f.write(f"📌 TIÊU ĐỀ (Title):\n{seo_data.get('title', title)}\n\n")
            f.write(f"📝 MÔ TẢ (Description):\n{seo_data.get('description', '')}\n\n")
            f.write(f"⏱️ CHỈ MỤC THỜI GIAN (Chapters):\n{timestamp_str}\n")
            f.write(f"🏷️ TỪ KHÓA (Tags):\n{seo_data.get('tags', '')}\n\n")
            f.write("-" * 40 + "\n")
            f.write(f"🎨 GỢI Ý LÀM ẢNH BÌA (Thumbnail):\n{seo_data.get('thumbnail_concept', '')}\n")
            
        # ==========================================
        # BƯỚC 4: TỰ ĐỘNG VẼ THUMBNAIL LUÔN
        # ==========================================
        print(f"\n[Engine] Bước 4: Yêu cầu AI vẽ luôn Thumbnail dựa trên Concept...")
        thumbnail_prompt = seo_data.get('thumbnail_concept', '')
        if thumbnail_prompt:
            # Gửi lệnh cho Gemini Adapter để vẽ ảnh Thumbnail
            thumb_path = os.path.join(project_dir, 'thumbnail_youtube.jpg')
            
            # Cấu trúc lại prompt cho việc vẽ Thumbnail
            full_thumb_prompt = f"Hãy tạo 1 bức ảnh TỶ LỆ 16:9 sắc nét, thiết kế chuyên biệt để làm Thumbnail Youtube. Nội dung: {thumbnail_prompt}. Tuyệt đối KHÔNG CHÈN CHỮ (TEXT) vào trong ảnh vì tôi sẽ tự ghép chữ sau."
            
            # Hàm sinh ảnh đã được code ở Adapter Phase 4
            self.adapter.generate_image(full_thumb_prompt, save_path=thumb_path)
            
            if os.path.exists(thumb_path):
                print(f"[Engine] => Thumbnail AI vẽ đã được lưu tại: thumbnail_youtube.jpg")
                seo_data['thumbnail_path'] = thumb_path
        
        return seo_data, file_path
