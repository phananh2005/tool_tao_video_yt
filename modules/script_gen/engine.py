from core.logger import get_logger
logger = get_logger(__name__)
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
            logger.error(f"[LỖI PARSE JSON]: {e}")
            logger.info(f"Nội dung gốc: {text}")
            return []

    def develop_strategy(self, idea: IdeaJSON) -> str:
        prompt = f"""
        Nhiệm vụ: Phân tích và xây dựng CHIẾN LƯỢC KỂ CHUYỆN (Storytelling Strategy) ĐỈNH CAO cho video YouTube.
        Chủ đề: {idea.title}
        Tóm tắt: {idea.summary}

        Yêu cầu:
        Đóng vai một đạo diễn nội dung và chuyên gia giữ chân khán giả (Audience Retention Expert) hàng đầu thế giới.
        Hãy phân tích và đưa ra chiến lược chi tiết để video này cuốn hút từ giây đầu đến giây cuối. Chiến lược phải bao gồm:
        1. Tâm lý khán giả mục tiêu & Insight cốt lõi (Họ sợ gì, khát khao gì?).
        2. Khung kể chuyện (Story framework) tối ưu nhất (ví dụ: Problem-Agitate-Solve, Hero's Journey, Bí ẩn chưa lời giải).
        3. Chiến thuật "Open Loops" (Mở vòng lặp bí ẩn ở đầu và giải đáp ở cuối) để giữ chân người xem.
        4. Nhịp điệu cảm xúc (Emotional pacing) và các "Pattern Interrupts" (thay đổi nhịp độ bất ngờ) qua các giai đoạn của video.

        Chỉ trả về nội dung chiến lược chi tiết, sâu sắc (văn bản thuần túy, không cần JSON).
        """
        return self.adapter.generate_text(prompt, expected_format='text')

    def generate_outline(self, idea: IdeaJSON, strategy: str) -> List[ChapterJSON]:
        prompt = f"""
        Nhiệm vụ: Lập dàn ý cho một video YouTube có thời lượng TỪ 10 ĐẾN 15 PHÚT.
        Chủ đề: {idea.title}
        Tóm tắt: {idea.summary}

        CHIẾN LƯỢC KỂ CHUYỆN ĐÃ ĐƯỢC CHUYÊN GIA PHÊ DUYỆT:
        {strategy}

        Yêu cầu:
        - Dựa trên chiến lược trên, hãy chia nội dung thành 4 đến 6 Chương (Chapters).
        - Chương 1 BẮT BUỘC là "Hook & Intro" - Phải tung ra ngay Open Loop (vòng lặp bí ẩn) và đánh trúng insight khán giả trong 15 giây đầu.
        - Chương cuối BẮT BUỘC là "CTA & Outro" - Giải quyết triệt để Open Loop và kêu gọi hành động mạnh mẽ.
        - Bố cục phải tạo thành một mạch truyện (narrative arc) hoặc mạch lập luận xuất sắc, có cao trào, có nút thắt. Mỗi chương phải là một bước đệm bắt buộc cho chương sau.
        - TRẢ VỀ DUY NHẤT MỘT MẢNG JSON HỢP LỆ. KHÔNG BAO GỒM GIẢI THÍCH.

        Định dạng bắt buộc:
        [
            {{ "chapter_number": 1, "title": "Tên chương", "summary": "Tóm tắt chi tiết chương này sẽ nói về cái gì, mục đích cảm xúc và cách nó liên kết/mở đường cho chương sau" }}
        ]
        """
        result = self.adapter.generate_text(prompt, expected_format='json')
        data = self._extract_json_array(result)

        chapters = []
        for item in data:
            if 'chapter_number' in item and 'title' in item and 'summary' in item:
                chapters.append(ChapterJSON(**item))
        return chapters

    def refine_outline(self, idea: IdeaJSON, strategy: str, initial_outline: List[ChapterJSON]) -> List[ChapterJSON]:
        outline_str = "\n".join([f"Chương {c.chapter_number}: {c.title} ({c.summary})" for c in initial_outline])
        prompt = f"""
        Nhiệm vụ: NÂNG CẤP DÀN Ý VIDEO YOUTUBE LÊN MỨC ĐỘ HOÀN HẢO.
        Chủ đề: {idea.title}
        Chiến lược: {strategy}

        Dàn ý bản nháp hiện tại:
        {outline_str}

        Yêu cầu:
        Đóng vai một Editor khó tính nhất của YouTube. Hãy phân tích dàn ý nháp này xem có chỗ nào bị chán, lê thê, hay thiếu móc nối không.
        Sau đó, VIẾT LẠI DÀN Ý NÀY cho thật sắc bén, kịch tính hơn, và có tính tò mò cao hơn. Đảm bảo vẫn giữ từ 4 đến 6 chương.
        - TRẢ VỀ DUY NHẤT MỘT MẢNG JSON HỢP LỆ CHỨA DÀN Ý ĐÃ NÂNG CẤP. KHÔNG BAO GỒM GIẢI THÍCH.

        Định dạng bắt buộc:
        [
            {{ "chapter_number": 1, "title": "Tên chương đã tối ưu", "summary": "Tóm tắt chương sắc bén, kịch tính, kết nối chặt chẽ" }}
        ]
        """
        result = self.adapter.generate_text(prompt, expected_format='json')
        data = self._extract_json_array(result)
        if not data:
            return initial_outline # Fallback

        chapters = []
        for item in data:
            if 'chapter_number' in item and 'title' in item and 'summary' in item:
                chapters.append(ChapterJSON(**item))
        return chapters if chapters else initial_outline

    def generate_chapter_scenes(self, idea: IdeaJSON, outline: List[ChapterJSON], chapter: ChapterJSON, strategy: str) -> List[SceneJSON]:
        outline_str = "\n".join([f"Chương {c.chapter_number}: {c.title} ({c.summary})" for c in outline])
        prompt = f"""
        Nhiệm vụ: Viết kịch bản phân cảnh (Scene) CỰC KỲ CUỐN HÚT cho MỘT CHƯƠNG trong video YouTube dài 10-15 phút.
        Chủ đề chung: {idea.title}
        Chiến lược tổng thể:\n{strategy}
        Dàn ý toàn bài:\n{outline_str}

        YÊU CẦU CHÍNH CHO CHƯƠNG {chapter.chapter_number} ({chapter.title}):
        - Phải chia chương này thành 10 đến 15 phân cảnh (Scenes) ngắn.
        - Mỗi cảnh CHỈ KÉO DÀI khoảng 5 đến 8 giây. Tốc độ này tạo ra sự bùng nổ về mặt thị giác (Pattern Interrupts).
        - LIÊN KẾT CHẶT CHẼ: Các scene phải chảy như một thước phim điện ảnh. Ý của cảnh sau nối tiếp tự nhiên, đẩy cao trào lên từ cảnh trước.
        - Visual Concept: Không chỉ mô tả hình ảnh, hãy dùng hình ảnh ẩn dụ (visual metaphor) sắc bén để minh họa cho ý tưởng.
        - Narration Outline (Dàn ý lời bình): Cực kỳ súc tích (1-2 ý ngắn). Chứa đựng móc câu (hook) hoặc điểm nhấn cảm xúc. Không lan man.
        - Nếu là Chương 1, phân cảnh 1 phải "tát thẳng vào mặt" khán giả bằng một hình ảnh và thông tin cực sốc/tò mò. KHÔNG yêu cầu logo kênh cụ thể.
        - Nếu là Chương cuối, phân cảnh cuối phải kết thúc gọn gàng, để lại dư âm và kêu gọi hành động. KHÔNG yêu cầu logo kênh.
        - TRẢ VỀ DUY NHẤT MỘT MẢNG JSON HỢP LỆ. KHÔNG BAO GỒM GIẢI THÍCH.

        Định dạng bắt buộc:
        [
            {{
                "chapter_number": {chapter.chapter_number},
                "scene_number": 0,
                "visual_concept": "Mô tả hình ảnh B-roll/metaphor mạnh mẽ, phù hợp logic",
                "duration_seconds": 6,
                "narration_outline": ["Dữ kiện 1 sắc bén, nối tiếp tự nhiên"]
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
        logger.info("\n[Engine] BƯỚC 1: AI (Deep Thinking) đang xây dựng CHIẾN LƯỢC KỂ CHUYỆN đỉnh cao...")
        strategy = self.develop_strategy(idea)

        logger.info("\n[Engine] BƯỚC 2: Đang yêu cầu AI lập Dàn ý dựa trên chiến lược...")
        initial_chapters = self.generate_outline(idea, strategy)

        if not initial_chapters:
            logger.error("[Engine] Lỗi: Không thể sinh dàn ý. Vui lòng thử lại.")
            return ScriptJSON(idea_id=idea_id, estimated_total_duration=0, scenes=[])

        logger.info("\n[Engine] BƯỚC 3: AI (Critique Mode) đang đánh giá và NÂNG CẤP Dàn ý cho kịch tính hơn...")
        chapters = self.refine_outline(idea, strategy, initial_chapters)

        logger.info(f"[Engine] -> Đã chốt được {len(chapters)} Chương xuất sắc. Chuẩn bị sinh chi tiết...")

        all_scenes = []
        global_scene_idx = 1
        total_duration = 0

        logger.info("\n[Engine] BƯỚC 4: Gọi AI viết chi tiết từng Chương (Áp dụng thủ thuật giữ chân khán giả)...")
        for chap in chapters:
            logger.info(f"  -> Đang viết kịch bản cho Chương {chap.chapter_number}: {chap.title}")
            scenes = self.generate_chapter_scenes(idea, chapters, chap, strategy)

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
