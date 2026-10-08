import uuid
import json
import re
from typing import List
from core.contracts import IdeaJSON, AIProviderContract

class IdeaEngine:
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

    def develop_idea_strategy(self, topic: str) -> str:
        prompt = f"""
        Nhiệm vụ: Phân tích thị trường và tìm ra GÓC NHÌN ĐỘT PHÁ (Viral Angles) cho kênh YouTube chủ đề: '{topic}'.

        Yêu cầu:
        Đóng vai một chuyên gia chiến lược YouTube hàng đầu. Trước khi nghĩ ra ý tưởng video cụ thể, hãy phân tích:
        1. Cạm bẫy nội dung (Content Traps): Những video rập khuôn, nhàm chán mà ai cũng làm trong chủ đề này là gì?
        2. Góc nhìn đi ngược số đông (Contrarian Angles) hoặc Bí ẩn tột đỉnh (Ultimate Curiosities) có thể khai thác.
        3. Công thức Tiêu đề/Thumbnail giật gân nhưng không clickbait (hứa hẹn giá trị thực nhưng tạo tò mò cực độ).

        Trả về phân tích chiến lược này (dạng văn bản) để làm cơ sở cho bước sinh ý tưởng.
        """
        return self.adapter.generate_text(prompt, expected_format='text')

    def generate_ideas(self, topic: str, count: int = 5, is_rabbit_hole: bool = False) -> List[IdeaJSON]:
        print("\n[IdeaEngine] BƯỚC 1: Phân tích thị trường & Tìm góc nhìn Viral...")
        strategy = self.develop_idea_strategy(topic)

        print("\n[IdeaEngine] BƯỚC 2: Sinh ý tưởng dựa trên Chiến lược đột phá...")
        if is_rabbit_hole:
            prompt = f"""
            Chủ đề: '{topic}'
            Chiến lược đột phá:
            {strategy}

            Nhiệm vụ: Dựa trên chiến lược trên, hãy sinh ra CHÍNH XÁC 3 ý tưởng video YouTube nối tiếp nhau thành 1 series (Rabbit Hole).
            Video 1 phải gieo mầm tò mò khổng lồ để người xem buộc phải xem Video 2, và Video 3 là cú twist giải quyết toàn bộ.

            Trả về JSON list theo format:
            [
                {{"title": "Tiêu đề cực sốc/tò mò", "topics": ["từ khóa 1", "từ khóa 2"], "rabbit_hole_series": true, "part_number": 1, "summary": "Tóm tắt ngắn gọn sự hấp dẫn của video này"}}
            ]
            (Sinh đủ 3 phần)
            """
        else:
            prompt = f"""
            Chủ đề: '{topic}'
            Chiến lược đột phá:
            {strategy}

            Nhiệm vụ: Dựa trên chiến lược trên, hãy sinh ra {count} ý tưởng video YouTube ĐỘC LẬP xuất sắc nhất.
            Mỗi ý tưởng phải KHÁC BIỆT HOÀN TOÀN với nhau, tránh các lối mòn nhàm chán đã phân tích. Tiêu đề phải tạo cảm giác "không click vào xem không chịu được".

            Trả về JSON list theo format:
            [
                {{"title": "Tiêu đề tò mò/ngược đời", "topics": ["từ khóa", "từ khóa 2"], "rabbit_hole_series": false, "part_number": 1, "summary": "Tóm tắt giá trị và góc nhìn độc lạ của video"}}
            ]
            """

        response_text = self.adapter.generate_text(prompt, expected_format='json')
        data = self._extract_json_array(response_text)

        series_id = str(uuid.uuid4()) if is_rabbit_hole else None
        ideas = []
        for item in data:
            if 'title' in item and 'summary' in item:
                item.pop('series_id', None)
                if not item.get('topics'):
                    item['topics'] = []
                ideas.append(IdeaJSON(
                    title=item['title'],
                    topics=item['topics'],
                    rabbit_hole_series=item.get('rabbit_hole_series', is_rabbit_hole),
                    part_number=item.get('part_number', 1),
                    summary=item['summary'],
                    series_id=series_id
                ))

        if is_rabbit_hole:
            ideas = ideas[:3]

        return ideas

    def calculate_similarity(self, topics1: List[str], topics2: List[str]) -> float:
        set1 = set([t.lower() for t in topics1])
        set2 = set([t.lower() for t in topics2])
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        return intersection / float(max(len(set1), len(set2)))

    def dedup_filter(self, new_idea: IdeaJSON, history_ideas: List[IdeaJSON]) -> str:
        max_sim = 0.0
        for old in history_ideas:
            sim = self.calculate_similarity(new_idea.topics, old.topics)
            if sim > max_sim:
                max_sim = sim

        if max_sim > 0.85:
            return 'drop'
        elif max_sim >= 0.60:
            return 'warn'
        return 'pass'

    def enforce_rabbit_hole(self, ideas: List[IdeaJSON]) -> List[IdeaJSON]:
        rabbit_holes = [i for i in ideas if i.rabbit_hole_series]
        return rabbit_holes[:3]

