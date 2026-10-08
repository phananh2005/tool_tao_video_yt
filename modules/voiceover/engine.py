import json
import re
from typing import List
from core.contracts import AIProviderContract, VoiceoverSceneJSON, VoiceoverJSON

class VoiceoverEngine:
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

    def generate_chapter_voiceover(self, title: str, chapter_number: int, chapter_scenes: list, all_scenes_context: list) -> List[VoiceoverSceneJSON]:
        # Trích xuất context để AI hiểu mạch truyện
        context_str = "Tóm tắt các mạch truyện chính trong toàn bộ video:\n"
        for sc in all_scenes_context:
            context_str += f"- Chương {sc['chapter_number']} | Scene {sc['scene_number']}: {', '.join(sc['narration_outline'])}\n"
            
        # Nhiệm vụ cụ thể
        task_str = f"=== BẠN CHỈ ĐƯỢC VIẾT LỜI THOẠI CHO CÁC PHÂN CẢNH THUỘC CHƯƠNG {chapter_number} ===\n"
        for sc in chapter_scenes:
            task_str += f"- Scene {sc['scene_number']}:\n"
            task_str += f"  + Hình ảnh (Visual): {sc['visual_concept']}\n"
            task_str += f"  + Ý chính cần nói (Gợi ý): {', '.join(sc['narration_outline'])}\n\n"

        prompt = f"""
        Nhiệm vụ: Viết LỜI BÌNH (Voiceover) chi tiết, lôi cuốn cho một video YouTube.
        - Chủ đề: {title}
        
        {context_str}
        
        YÊU CẦU DÀNH CHO BẠN:
        {task_str}
        
        Phong cách (Tone):
        - Gần gũi, cuốn hút, bí ẩn hoặc tạo động lực tùy theo bối cảnh.
        - Xưng "mình" / "chúng ta" và gọi khán giả là "các bạn".
        - Viết câu văn hoàn chỉnh, mượt mà để thu âm. Đừng chỉ copy lại dàn ý. Mỗi scene nên viết khoảng 3-5 câu văn dài.
        - QUAN TRỌNG VỀ PHÁT ÂM (TTS): TUYỆT ĐỐI KHÔNG dùng ký tự đặc biệt, ký hiệu toán học, hoặc số dạng phân số/phần trăm (ví dụ: 1/3, 50%, +, &). Bắt buộc phải viết mọi con số, phần trăm, phân số và ký hiệu thành CHỮ hoàn toàn bằng tiếng Việt (ví dụ: "một phần ba" thay vì "1/3", "năm mươi phần trăm" thay vì "50%", "và" thay vì "&") để công cụ AI phát âm chuẩn xác ý nghĩa nhất.
        
        Định dạng bắt buộc: Trả về DUY NHẤT một mảng JSON hợp lệ, KHÔNG giải thích, KHÔNG markdown.
        [
            {{
                "scene_number": [Số của scene tương ứng],
                "spoken_text": "[Lời thoại chi tiết]"
            }}
        ]
        """
        result = self.adapter.generate_text(prompt, expected_format='json')
        data = self._extract_json_array(result)
        
        vo_scenes = []
        for item in data:
            if 'scene_number' in item and 'spoken_text' in item:
                vo_scenes.append(VoiceoverSceneJSON(
                    scene_number=item['scene_number'],
                    spoken_text=item['spoken_text']
                ))
        return vo_scenes

    def generate_full_voiceover(self, script_id: int, script_dict: dict, title: str) -> VoiceoverJSON:
        all_scenes = script_dict['scenes']
        
        # Gom nhóm scene theo chapter
        chapters_map = {}
        for sc in all_scenes:
            c_num = sc['chapter_number']
            if c_num not in chapters_map:
                chapters_map[c_num] = []
            chapters_map[c_num].append(sc)
            
        print(f"\n[Engine] Bắt đầu sinh Voiceover cho {len(chapters_map)} Chương...")
        
        final_vo_scenes = []
        
        for c_num, scenes_in_chapter in chapters_map.items():
            print(f"  -> Đang viết lời thoại cho Chương {c_num} ({len(scenes_in_chapter)} phân cảnh)...")
            vo_scenes = self.generate_chapter_voiceover(title, c_num, scenes_in_chapter, all_scenes)
            
            # Gộp kết quả
            for vo in vo_scenes:
                final_vo_scenes.append(vo)
                
        return VoiceoverJSON(
            script_id=script_id,
            voiceover_scenes=final_vo_scenes
        )
