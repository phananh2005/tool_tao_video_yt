import pytest
import sys
import os
import json
import sqlite3
from unittest.mock import Mock, patch, mock_open
from dataclasses import asdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import core.database as db_mod
from core.database import (
    init_db, get_or_create_project, save_idea, save_script,
    save_voiceover, save_asset, save_seo_metadata,
    get_project_ideas, get_script_by_id,
)
from core.contracts import (
    IdeaJSON, ScriptJSON, SceneJSON, ChapterJSON,
    VoiceoverJSON, VoiceoverSceneJSON,
    AssetJSON, AssetSceneJSON, AIProviderContract,
)
from modules.idea_engine.engine import IdeaEngine
from modules.script_gen.engine import ScriptGeneratorEngine
from modules.voiceover.engine import VoiceoverEngine
from modules.scene_illustrator.engine import SceneIllustratorEngine
from modules.video_assembler.engine import VideoAssemblerEngine
from modules.seo_optimizer.engine import SEOOptimizerEngine


class FakeAdapter(AIProviderContract):
    def __init__(self):
        self.call_count = 0

    def generate_text(self, prompt, expected_format='json'):
        self.call_count += 1
        lower = prompt.lower()
        if "voiceover" in lower or "lời thoại" in lower or "spoken" in lower or "lời bình" in lower:
            return '[{"scene_number": 1, "spoken_text": "Hello from golden path"}]'
        if "seo" in lower or "thumbnail" in lower:
            return '{"title":"Golden SEO","description":"desc","tags":"t1","thumbnail_concept":"thumb"}'
        # Default: idea generation (prompt contains "ý tưởng" / idea keywords)
        return '[{"title":"Golden Idea","topics":["ai","test"],"rabbit_hole_series":false,"part_number":1,"summary":"Golden summary"}]'

    def generate_image(self, prompt, **kwargs):
        return "http://fake.img/1.jpg"


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    test_db = str(tmp_path / "test.db")
    db_mod.DB_PATH = test_db
    init_db()
    yield test_db


def test_golden_path_phase1_to_phase6():
    adapter = FakeAdapter()

    # --- Phase 1: Idea Engine ---
    idea_engine = IdeaEngine(adapter=adapter)
    ideas = idea_engine.generate_ideas("Golden Theme")
    assert len(ideas) >= 1
    idea = ideas[0]
    assert idea.title == "Golden Idea"

    project_id = get_or_create_project("Golden Theme")
    save_idea(project_id, idea, 0.0, "pass")
    saved_ideas = get_project_ideas(project_id)
    assert len(saved_ideas) == 1
    idea_id = 1

    # --- Phase 2: Script Generator ---
    script_engine = ScriptGeneratorEngine(adapter=adapter)
    script_engine.generate_outline = Mock(return_value=[
        ChapterJSON(chapter_number=1, title="Chapter 1", summary="Summary"),
    ])
    scene = SceneJSON(chapter_number=1, scene_number=0, visual_concept="Robot waving",
                      duration_seconds=15, narration_outline=["Hello"])
    script_engine.generate_chapter_scenes = Mock(return_value=[scene])

    script = script_engine.generate_full_script(idea_id, idea)
    assert isinstance(script, ScriptJSON)
    assert len(script.scenes) == 1
    save_script(idea_id, script)

    loaded_script = get_script_by_id(1)
    assert loaded_script is not None
    assert loaded_script["scenes"][0]["visual_concept"] == "Robot waving"
    script_id = 1

    # --- Phase 3: Voiceover Engine ---
    vo_engine = VoiceoverEngine(adapter=adapter)
    vo = vo_engine.generate_full_voiceover(script_id, asdict(script), idea.title)
    assert isinstance(vo, VoiceoverJSON)
    assert len(vo.voiceover_scenes) >= 1
    save_voiceover(script_id, vo)

    conn = sqlite3.connect(db_mod.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM voiceovers WHERE script_id = ?", (script_id,))
    assert cursor.fetchone() is not None
    conn.close()

    # --- Phase 4: Scene Illustrator ---
    illustrator = SceneIllustratorEngine(adapter=adapter)
    with patch("os.path.exists", return_value=False), \
         patch("os.path.getsize", return_value=0), \
         patch("os.makedirs"), \
         patch("time.sleep"):
        assets = illustrator.generate_assets(script_id, asdict(script))
    assert isinstance(assets, AssetJSON)
    save_asset(script_id, assets)

    conn = sqlite3.connect(db_mod.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM assets WHERE script_id = ?", (script_id,))
    row = cursor.fetchone()
    conn.close()
    assert row is not None

    # --- Phase 5: Video Assembler (mock FFmpeg) ---
    assembler = VideoAssemblerEngine()
    mock_process = Mock()
    mock_process.stdout.__iter__ = Mock(return_value=iter(["frame=1", ""]))
    mock_process.stdout.readline = Mock(side_effect=["frame=1", ""])
    mock_process.stdout.close = Mock()
    mock_process.wait.return_value = 0

    timeline = [{"image_path": "img.jpg", "audio_path": "voice.mp3", "duration": 15}]
    with patch.object(assembler, "generate_concat_files", return_value=("v.txt", "a.txt")), \
         patch("subprocess.Popen", return_value=mock_process), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove"):
        chunks = list(assembler.render_video_stream(script_id, timeline))
    assert any("[DONE]" in c for c in chunks)

    # --- Phase 6: SEO Optimizer ---
    seo_engine = SEOOptimizerEngine(adapter=adapter)
    asset_dict = asdict(assets)
    with patch("os.path.exists", return_value=True), \
         patch("os.makedirs"), \
         patch("builtins.open", mock_open()):
        seo_data, file_path = seo_engine.format_upload_info(script_id, idea.title, asdict(script), asset_dict)
    assert seo_data["title"] == "Golden SEO"
    save_seo_metadata(script_id, seo_data)

    # --- Final DB verification ---
    conn = sqlite3.connect(db_mod.DB_PATH)
    cursor = conn.cursor()
    for table in ["projects", "ideas", "scripts", "voiceovers", "assets", "seo_metadata"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        assert count >= 1, f"Table {table} should have at least 1 row but has {count}"
    conn.close()
