import uuid

import json

from typing import List

from core.contracts import IdeaJSON, AIProviderContract



class IdeaEngine:

    def __init__(self, adapter: AIProviderContract):

        self.adapter = adapter

        

    def generate_ideas(self, topic: str, count: int = 5, is_rabbit_hole: bool = False) -> List[IdeaJSON]:

        if is_rabbit_hole:

            prompt = f"Sinh ra CHÍNH XÁC 3 ý tưởng video YouTube nối tiếp nhau thành 1 series (Rabbit Hole) về chủ đề '{topic}'. Trả về JSON list theo format: [{{'title': '...', 'topics': ['...'], 'rabbit_hole_series': True, 'part_number': 1, 'summary': '...'}}, {{... part_number: 2}}, {{... part_number: 3}}]"

        else:

            prompt = f"Sinh ra {count} ý tưởng video YouTube ĐỘC LẬP về chủ đề '{topic}'. Trả về JSON list theo format: [{{'title': '...', 'topics': ['...'], 'rabbit_hole_series': False, 'part_number': 1, 'summary': '...'}}]"

        

        response_text = self.adapter.generate_text(prompt, expected_format='json')

        try:

            import json

            data = json.loads(response_text)

            series_id = str(uuid.uuid4()) if is_rabbit_hole else None

            ideas = []

            for item in data:

                item.pop('series_id', None)

                ideas.append(IdeaJSON(**item, series_id=series_id))

            return ideas

        except Exception as e:

            print("Lỗi parse ý tưởng:", e)

            return []

            

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

