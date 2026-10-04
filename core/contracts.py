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
