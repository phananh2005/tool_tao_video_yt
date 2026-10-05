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

    def generate_seo_metadata(self, title: str, summary: str, chapter_summaries: str = "") -> dict:
        prompt = f"""
        Nhiệm vụ: Viết bộ thông tin chuẩn SEO cho video YouTube.
        Chủ đề: {title}
        Nội dung chính: {summary}
        Nội dung từng chương (tham khảo để đặt tên chương):
        {chapter_summaries}
        
        YÊU CẦU:
        1. Options (options): Trả về một mảng chứa ĐÚNG 3 LỰA CHỌN (3 option). Mỗi option là 1 bộ bao gồm:
           - "title": Tiêu đề (dưới 60 ký tự, giật tít, khơi gợi tò mò).
           - "thumbnail_concept": Gợi ý bối cảnh, nhân vật hoặc đồ vật chính cho ảnh bìa phù hợp với tiêu đề này.
           - "thumbnail_text": Một dòng chữ RẤT NGẮN (2-5 từ) và CỰC KỲ TÒ MÒ, giật gân, hoặc câu hỏi để chèn thật to lên ảnh bìa này.
        2. Mô tả (description): 2-3 đoạn ngắn, cuốn hút. Có lời kêu gọi Like/Subscribe.
        3. Tags: 15-20 từ khóa thịnh hành cách nhau bằng dấu phẩy.
        4. Chapter Titles (chapter_titles): Mảng các chuỗi, mỗi chuỗi là tên của một chương (tương ứng với số chương truyền vào). Tên chương KHÔNG ĐƯỢC để là "Chương 1", "Chương 2". Phải dùng nội dung cụ thể của chương đó hoặc đặt một câu hỏi gây tò mò, kích thích người xem click vào (vd: "Bí mật được hé lộ?").
        
        TRẢ VỀ DUY NHẤT ĐỊNH DẠNG JSON. KHÔNG MARKDOWN.
        {{
            "options": [
                {{
                    "title": "Tiêu đề 1",
                    "thumbnail_concept": "Concept 1",
                    "thumbnail_text": "Text 1"
                }},
                {{
                    "title": "Tiêu đề 2",
                    "thumbnail_concept": "Concept 2",
                    "thumbnail_text": "Text 2"
                }},
                {{
                    "title": "Tiêu đề 3",
                    "thumbnail_concept": "Concept 3",
                    "thumbnail_text": "Text 3"
                }}
            ],
            "description": "...",
            "tags": "...",
            "chapter_titles": ["Tên chương 1", "Tên chương 2", "..."]
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
        
        # Gom nhóm nội dung từng chương để đặt tên
        chapter_content_map = {}
        for sc in script_dict.get('scenes', []):
            c_num = sc.get('chapter_number', 1)
            if c_num not in chapter_content_map:
                chapter_content_map[c_num] = []
            if 'narration_outline' in sc:
                chapter_content_map[c_num].extend(sc['narration_outline'])
                
        chapter_summaries_str = ""
        for c_num, lines in chapter_content_map.items():
            lines_str = " ".join(lines[:3]) # lấy 3 ý đầu để AI nắm nội dung
            chapter_summaries_str += f"- Chương {c_num}: {lines_str}...\n"
            
        print(f"[Engine] Bước 2: Gọi Gemini viết Tiêu đề, Mô tả và Tên Chương chuẩn SEO...")
        summary = "Video về chủ đề " + title
        
        seo_data = self.generate_seo_metadata(title, summary, chapter_summaries_str)
        if not seo_data:
            return False
            
        # Gộp mảng 3 option lại thành 1 chuỗi tiêu đề để hiển thị trên frontend
        options = seo_data.get('options', [])
        if isinstance(options, list) and len(options) > 0:
            formatted_title = "\n".join([f"{i+1}. {opt.get('title', '')}" for i, opt in enumerate(options)])
        else:
            formatted_title = title
            
        seo_data['title'] = formatted_title
            
        print("[Engine] Bước 3: Ghép nối dữ liệu và xuất file Text...")
        
        ai_titles = seo_data.get('chapter_titles', [])
        chapter_names = {}
        for i, ts in enumerate(timestamps):
            c_num = ts['chapter_number']
            if i < len(ai_titles) and ai_titles[i]:
                chapter_names[c_num] = ai_titles[i]
            else:
                chapter_names[c_num] = f"Chương {c_num}"
            
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
            f.write(f"🎨 GỢI Ý ẢNH BÌA (Thumbnails):\n")
            for i, opt in enumerate(options):
                f.write(f" [Option {i+1}]: {opt.get('title', '')}\n")
                f.write(f"   - Hình ảnh: {opt.get('thumbnail_concept', '')}\n")
                f.write(f"   - Chữ chèn trên ảnh (Text): \"{opt.get('thumbnail_text', '')}\"\n\n")
            
        # ==========================================
        # BƯỚC 4: TỰ ĐỘNG VẼ THUMBNAIL LUÔN (3 ẢNH)
        # ==========================================
        print(f"\n[Engine] Bước 4: Yêu cầu AI vẽ {len(options)} Thumbnail dựa trên Concept...")
        thumbnail_paths = []
        for i, opt in enumerate(options):
            thumbnail_prompt = opt.get('thumbnail_concept', '')
            thumbnail_text = opt.get('thumbnail_text', '')
            
            if thumbnail_prompt:
                thumb_path = os.path.join(project_dir, f'thumbnail_youtube_{i+1}.jpg')
                
                # Cấu trúc lại prompt cho việc vẽ Thumbnail
                if thumbnail_text:
                    full_thumb_prompt = f"Hãy tạo 1 bức ảnh TỶ LỆ 16:9 sắc nét, thiết kế chuyên biệt để làm Thumbnail Youtube. Nội dung: {thumbnail_prompt}. BẮT BUỘC chèn thật to, rõ ràng dòng chữ này (có thể là tiếng Việt) lên vị trí nổi bật nhất của ảnh: \"{thumbnail_text}\"."
                else:
                    full_thumb_prompt = f"Hãy tạo 1 bức ảnh TỶ LỆ 16:9 sắc nét, thiết kế chuyên biệt để làm Thumbnail Youtube. Nội dung: {thumbnail_prompt}."
                
                print(f"[Engine] Đang vẽ Thumbnail {i+1}/{len(options)}...")
                self.adapter.generate_image(full_thumb_prompt, save_path=thumb_path)
                
                if os.path.exists(thumb_path):
                    print(f"[Engine] => Thumbnail {i+1} đã được lưu tại: thumbnail_youtube_{i+1}.jpg")
                    thumbnail_paths.append(f"data/projects/{script_id}/thumbnail_youtube_{i+1}.jpg")
        
        seo_data['thumbnail_paths'] = thumbnail_paths
        
        return seo_data, file_path
