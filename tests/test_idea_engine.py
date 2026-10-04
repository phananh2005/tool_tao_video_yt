import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.contracts import IdeaJSON, AIProviderContract
from modules.idea_engine.engine import IdeaEngine

class MockAdapter(AIProviderContract):
    def generate_text(self, prompt: str, expected_format: str = 'json') -> str:
        return '[{"title": "Test Video", "topics": ["test", "mock"], "rabbit_hole_series": true, "part_number": 1, "summary": "Test summary"}]'
        
    def generate_image(self, prompt: str) -> str:
        return ""

@pytest.fixture
def engine():
    return IdeaEngine(adapter=MockAdapter())

def test_dedup_drop(engine):
    old_idea = IdeaJSON(title="Old", topics=["python", "coding", "tutorial"], rabbit_hole_series=False, part_number=1, summary="")
    new_idea = IdeaJSON(title="New", topics=["python", "coding", "tutorial"], rabbit_hole_series=False, part_number=1, summary="")
    assert engine.dedup_filter(new_idea, [old_idea]) == "drop"

def test_dedup_warn(engine):
    old_idea = IdeaJSON(title="Old", topics=["python", "coding", "tutorial"], rabbit_hole_series=False, part_number=1, summary="")
    new_idea = IdeaJSON(title="New", topics=["python", "coding", "oop"], rabbit_hole_series=False, part_number=1, summary="")
    assert engine.dedup_filter(new_idea, [old_idea]) == "warn"

def test_dedup_pass(engine):
    old_idea = IdeaJSON(title="Old", topics=["python", "coding"], rabbit_hole_series=False, part_number=1, summary="")
    new_idea = IdeaJSON(title="New", topics=["java", "oop"], rabbit_hole_series=False, part_number=1, summary="")
    assert engine.dedup_filter(new_idea, [old_idea]) == "pass"

def test_rabbit_hole_limit(engine):
    ideas = [
        IdeaJSON(title="P1", topics=["t"], rabbit_hole_series=True, part_number=1, summary=""),
        IdeaJSON(title="P2", topics=["t"], rabbit_hole_series=True, part_number=2, summary=""),
        IdeaJSON(title="P3", topics=["t"], rabbit_hole_series=True, part_number=3, summary=""),
        IdeaJSON(title="P4", topics=["t"], rabbit_hole_series=True, part_number=4, summary=""),
        IdeaJSON(title="Normal", topics=["t2"], rabbit_hole_series=False, part_number=1, summary=""),
    ]
    result = engine.enforce_rabbit_hole(ideas)
    assert len(result) == 3
    assert result[0].part_number == 1
    assert result[2].part_number == 3

def test_generate_ideas(engine):
    ideas = engine.generate_ideas("test")
    assert len(ideas) == 1
    assert ideas[0].title == "Test Video"
