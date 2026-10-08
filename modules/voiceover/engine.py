import json
from core.logger import get_logger
logger = get_logger(__name__)
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
            logger.error(f"[LỖI PARSE JSON]: {e}")
            logger.info(f"Nội dung gốc: {text}")
            return []

    def develop_voiceover_strategy(self, title: str, all_scenes_context: list) -> str:
        context_str = "Tóm tắt các mạch truyện chính:\n"
        for sc in all_scenes_context:
            context_str += f"- Chương {sc['chapter_number']} | Scene {sc['scene_number']}: {', '.join(sc['narration_outline'])}\n"

        prompt = f"""
        Nhiệm vụ: Xây dựng CHIẾN LƯỢC LỜI THOẠI (Voiceover Strategy) ĐỈNH CAO cho video YouTube.
        Chủ đề: {title}
        Kịch bản tổng thể:
        {context_str}

        Yêu cầu:
        Đóng vai một Đạo diễn Âm thanh và Chuyên gia Ngôn từ (Copywriter) hàng đầu. Hãy phân tích và đưa ra chiến lược lồng tiếng để giữ chân khán giả:
        1. Giọng điệu (Tone of Voice): Cần thay đổi như thế nào qua từng chương (Ví dụ: Bí ẩn ở Hook -> Quyết liệt ở Body -> Truyền cảm hứng ở Outro).
        2. Kỹ thuật viết (Copywriting techniques): Cấu trúc câu ngắn dài xen kẽ, sử dụng động từ mạnh, và các từ khóa đánh vào cảm xúc.
        3. Quy tắc Đọc bằng AI (TTS rules): Cách nhả chữ, cách ngắt câu để AI đọc tự nhiên nhất (tuyệt đối phải viết số, ký hiệu thành chữ tiếng Việt).

        Chỉ trả về nội dung chiến lược chi tiết, sâu sắc (văn bản thuần túy).
        """
        return self.adapter.generate_text(prompt, expected_format='text')

    def generate_chapter_voiceover_draft(self, title: str, chapter_number: int, chapter_scenes: list, strategy: str, previous_chapter_ending: str = "") -> List[VoiceoverSceneJSON]:
        prev_context_str = ""
        if previous_chapter_ending:
            prev_context_str = f"LƯU Ý QUAN TRỌNG VỀ LIÊN KẾT: Lời thoại cuối cùng của chương trước là: \"{previous_chapter_ending}\". Lời thoại mở đầu chương {chapter_number} phải nối tiếp hoàn hảo, trơn tru.\n\n"

        task_str = f"=== VIẾT LỜI THOẠI CHO CHƯƠNG {chapter_number} ===\n"
        for sc in chapter_scenes:
            task_str += f"- Scene {sc['scene_number']}:\n  + Hình ảnh: {sc['visual_concept']}\n  + Gợi ý: {', '.join(sc['narration_outline'])}\n\n"

        prompt = f"""
        Nhiệm vụ: Viết LỜI BÌNH (Voiceover) NHÁP cho Chương {chapter_number} của video YouTube.
        Chủ đề: {title}

        CHIẾN LƯỢC LỜI THOẠI:
        {strategy}

        {prev_context_str}YÊU CẦU DÀNH CHO BẠN:
        {task_str}

        - Lời thoại phải có tính chất "Hội thoại" (Conversational), xưng "mình/chúng ta" - "bạn/các bạn".
        - Lời thoại giữa các scene phải có TỪ NỐI, chuyển ý mượt mà. Đừng viết những câu văn khô khan như đọc sách.
        - TTS RULE: Cấm dùng số (1, 2, 3) hay ký hiệu (%, +, /). Phải viết chữ: "một", "phần trăm", "và".

        Định dạng bắt buộc (JSON):
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

    def refine_chapter_voiceover(self, title: str, chapter_number: int, draft_vo: List[VoiceoverSceneJSON], strategy: str) -> List[VoiceoverSceneJSON]:
        draft_str = ""
        for vo in draft_vo:
            draft_str += f"- Scene {vo.scene_number}: {vo.spoken_text}\n"

        prompt = f"""
        Nhiệm vụ: CHUỐT LẠI (Refine) LỜI THOẠI CHƯƠNG {chapter_number} ĐỂ ĐẠT MỨC HOÀN HẢO.
        Chủ đề: {title}

        Chiến lược:
        {strategy}

        Bản nháp hiện tại:
        {draft_str}

        YÊU CẦU:
        Đóng vai một Biên tập viên Âm thanh (Audio Editor) cực kỳ khắt khe.
        Hãy đọc lại bản nháp và SỬA LẠI toàn bộ để:
        1. Trôi chảy hơn: Xóa bỏ các từ ngữ thừa, rườm rà. Câu văn phải có nhịp điệu (ngắn, dài xen kẽ) để dễ thu âm.
        2. Kịch tính hơn: Đổi các động từ yếu thành động từ mạnh. Thêm cảm xúc.
        3. Kiểm tra TTS: Tuyệt đối KHÔNG CÒN MỘT CON SỐ HAY KÝ HIỆU NÀO DẠNG TOÁN HỌC (chuyển hết thành chữ: "một trăm", "phần trăm", v.v.).

        TRẢ VỀ DUY NHẤT MẢNG JSON ĐÃ CHUỐT LẠI.
        [
            {{
                "scene_number": [Số của scene],
                "spoken_text": "[Lời thoại đã hoàn thiện 100%]"
            }}
        ]
        """
        result = self.adapter.generate_text(prompt, expected_format='json')
        data = self._extract_json_array(result)
        if not data:
            return draft_vo

        vo_scenes = []
        for item in data:
            if 'scene_number' in item and 'spoken_text' in item:
                vo_scenes.append(VoiceoverSceneJSON(
                    scene_number=item['scene_number'],
                    spoken_text=item['spoken_text']
                ))
        return vo_scenes if vo_scenes else draft_vo

    def generate_full_voiceover(self, script_id: int, script_dict: dict, title: str) -> VoiceoverJSON:
        all_scenes = script_dict['scenes']

        # Gom nhóm scene theo chapter
        chapters_map = {}
        for sc in all_scenes:
            c_num = sc['chapter_number']
            if c_num not in chapters_map:
                chapters_map[c_num] = []
            chapters_map[c_num].append(sc)

        logger.info(f"\n[Engine] BƯỚC 1: Xây dựng Chiến lược Lời thoại (Voiceover Strategy) cho {len(chapters_map)} Chương...")
        strategy = self.develop_voiceover_strategy(title, all_scenes)

        final_vo_scenes = []
        previous_chapter_ending = ""

        logger.info(f"\n[Engine] BƯỚC 2: Gọi AI viết và chuốt lời thoại từng Chương...")
        for c_num, scenes_in_chapter in chapters_map.items():
            logger.info(f"  -> [Chương {c_num}] Đang viết nháp...")
            draft_vo = self.generate_chapter_voiceover_draft(title, c_num, scenes_in_chapter, strategy, previous_chapter_ending)

            logger.info(f"  -> [Chương {c_num}] Đang chuốt lại (Critique Mode)...")
            vo_scenes = self.refine_chapter_voiceover(title, c_num, draft_vo, strategy)

            # Gộp kết quả
            for vo in vo_scenes:
                final_vo_scenes.append(vo)

            # Lưu lại câu cuối của chương này để làm context chuyển ý cho chương sau
            if vo_scenes:
                last_spoken_text = vo_scenes[-1].spoken_text
                words = last_spoken_text.split()
                if len(words) > 20:
                    previous_chapter_ending = "..." + " ".join(words[-20:])
                else:
                    previous_chapter_ending = last_spoken_text

        return VoiceoverJSON(
            script_id=script_id,
            voiceover_scenes=final_vo_scenes
        )
