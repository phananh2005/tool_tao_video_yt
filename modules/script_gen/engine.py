import json
import re
from typing import List
from core.contracts import IdeaJSON, ChapterJSON, SceneJSON, ScriptJSON, AIProviderContract

class ScriptGeneratorEngine:
    def __init__(self, adapter: AIProviderContract):
        self.adapter = adapter

    def _extract_json_array(self, text: str) -> list:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            text = match.group(0)
            
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print("[LỖI PARSE JSON]:", e)
            print("Nội dung gốc:", text)
            return []

    def generate_outline(self, idea: IdeaJSON) -> List[ChapterJSON]:
        prompt = f"""
        Nhiệm vụ: Lập dàn ý cho một video YouTube có thời lượng TỪ 10 ĐẾN 15 PHÚT.
        - Chủ đề: {idea.title}
        - Tóm tắt: {idea.summary}
        
        Yêu cầu: 
        - Để video đạt chuẩn thời lượng 10-15 phút, hãy chia nội dung thành 4 đến 6 Chương (Chapters) vừa phải.
        - Mỗi chương phải có mục tiêu rõ ràng và đóng góp vào mạch truyện chung.
        - TRẢ VỀ DUY NHẤT MỘT MẢNG JSON HỢP LỆ. KHÔNG BAO GỒM GIẢI THÍCH.
        
        Định dạng bắt buộc:
        [
            {{ "chapter_number": 1, "title": "Tên chương", "summary": "Tóm tắt chi tiết chương này sẽ nói về cái gì" }}
        ]
        """
        result = self.adapter.generate_text(prompt, expected_format='json')
        data = self._extract_json_array(result)
        
        chapters = []
        for item in data:
            if 'chapter_number' in item and 'title' in item and 'summary' in item:
                chapters.append(ChapterJSON(**item))
        return chapters

    def generate_chapter_scenes(self, idea: IdeaJSON, outline: List[ChapterJSON], chapter: ChapterJSON) -> List[SceneJSON]:
        outline_str = "\n".join([f"Chương {c.chapter_number}: {c.title} ({c.summary})" for c in outline])
        prompt = f"""
        Nhiệm vụ: Viết kịch bản phân cảnh (Scene) cho MỘT CHƯƠNG trong video YouTube dài 10-15 phút.
        - Chủ đề chung: {idea.title}
        - Dàn ý toàn bài:\n{outline_str}
        
        YÊU CẦU CHÍNH CHO CHƯƠNG {chapter.chapter_number} ({chapter.title}):
        - Phải chia chương này thành 6 đến 8 phân cảnh (Scenes).
        - Mỗi cảnh kéo dài khoảng 15-20 giây.
        - `narration_outline` (dàn ý lời bình) cung cấp từ 2-4 gạch đầu dòng ngắn gọn nhưng đủ thông tin để viết lời thoại.
        - TRẢ VỀ DUY NHẤT MỘT MẢNG JSON HỢP LỆ. KHÔNG BAO GỒM GIẢI THÍCH.
        
        Định dạng bắt buộc:
        [
            {{
                "chapter_number": {chapter.chapter_number},
                "scene_number": 0,
                "visual_concept": "Mô tả hình ảnh B-roll",
                "duration_seconds": 15,
                "narration_outline": ["Dữ kiện 1", "Dữ kiện 2"]
            }}
        ]
        Lưu ý: Luôn để scene_number = 0.
        """
        result = self.adapter.generate_text(prompt, expected_format='json')
        data = self._extract_json_array(result)
        
        scenes = []
        for item in data:
            scenes.append(SceneJSON(
                chapter_number=item.get('chapter_number', chapter.chapter_number),
                scene_number=0,
                visual_concept=item.get('visual_concept', ''),
                duration_seconds=int(item.get('duration_seconds', 15)),
                narration_outline=item.get('narration_outline', [])
            ))
        return scenes

    def generate_full_script(self, idea_id: int, idea: IdeaJSON) -> ScriptJSON:
        print("\n[Engine] BƯỚC 1: Đang yêu cầu AI lập Dàn ý (Yêu cầu 4-6 Chương để video đạt 10-15 phút)...")
        chapters = self.generate_outline(idea)
        
        if not chapters:
            print("[Engine] Lỗi: Không thể sinh dàn ý. Vui lòng thử lại.")
            return ScriptJSON(idea_id=idea_id, estimated_total_duration=0, scenes=[])
            
        print(f"[Engine] -> Đã tạo được {len(chapters)} Chương. Chuẩn bị sinh chi tiết...")
        
        all_scenes = []
        global_scene_idx = 1
        total_duration = 0
        
        print("\n[Engine] BƯỚC 2: Gọi AI viết chi tiết từng Chương (Yêu cầu 6-8 phân cảnh/chương)...")
        for chap in chapters:
            print(f"  -> Đang viết kịch bản cho Chương {chap.chapter_number}: {chap.title}")
            scenes = self.generate_chapter_scenes(idea, chapters, chap)
            
            for sc in scenes:
                sc.scene_number = global_scene_idx
                global_scene_idx += 1
                total_duration += sc.duration_seconds
                all_scenes.append(sc)
                
        return ScriptJSON(
            idea_id=idea_id,
            estimated_total_duration=total_duration,
            scenes=all_scenes
        )
