from dataclasses import dataclass
from typing import List, Optional
from abc import ABC, abstractmethod

@dataclass
class IdeaJSON:
    title: str
    topics: List[str]
    rabbit_hole_series: bool
    part_number: int
    summary: str

class AIProviderContract(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, expected_format: str = 'json') -> str:
        pass
    
    @abstractmethod
    def generate_image(self, prompt: str) -> str:
        pass

@dataclass
class ChapterJSON:
    chapter_number: int
    title: str
    summary: str

@dataclass
class SceneJSON:
    chapter_number: int
    scene_number: int
    visual_concept: str
    duration_seconds: int
    narration_outline: List[str]

@dataclass
class ScriptJSON:
    idea_id: int
    estimated_total_duration: int
    scenes: List[SceneJSON]
