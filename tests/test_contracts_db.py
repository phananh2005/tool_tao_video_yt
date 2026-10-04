import pytest
import sys
import os
import json
import sqlite3
import shutil
import tempfile
from dataclasses import asdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import core.database as db_mod
from core.database import (
    init_db, get_or_create_project, get_project_ideas, save_idea,
    get_idea_by_id, save_script, get_script_by_id, save_voiceover,
    save_asset, save_seo_metadata, get_ready_to_render_projects_with_audio,
    delete_project_media, get_ideas_without_script, get_scripts_without_voiceover,
    get_scripts_without_assets, get_rendered_projects_without_seo,
)
from core.contracts import (
    IdeaJSON, ScriptJSON, SceneJSON, VoiceoverJSON, VoiceoverSceneJSON,
    AssetJSON, AssetSceneJSON,
)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    test_db = str(tmp_path / "test.db")
    db_mod.DB_PATH = test_db
    init_db()
    yield test_db


# ---------- get_or_create_project ----------

def test_create_project():
    pid = get_or_create_project("My Project")
    assert isinstance(pid, int) and pid > 0


def test_get_or_create_project_idempotent():
    pid1 = get_or_create_project("Same Name")
    pid2 = get_or_create_project("Same Name")
    assert pid1 == pid2


# ---------- save / get ideas ----------

def _make_idea():
    return IdeaJSON(
        title="Test Idea",
        topics=["python", "testing"],
        rabbit_hole_series=False,
        part_number=1,
        summary="A test idea",
    )


def test_save_and_get_idea():
    pid = get_or_create_project("P1")
    idea = _make_idea()
    save_idea(pid, idea, 0.1, "pass")
    ideas = get_project_ideas(pid)
    assert len(ideas) == 1
    assert ideas[0].title == "Test Idea"
    assert ideas[0].topics == ["python", "testing"]


def test_get_idea_by_id():
    pid = get_or_create_project("P2")
    idea = _make_idea()
    save_idea(pid, idea, 0.0, "pass")
    retrieved = get_idea_by_id(1)
    assert retrieved is not None
    assert retrieved.title == "Test Idea"


# ---------- save / get scripts ----------

def _make_script(idea_id=1):
    scene = SceneJSON(
        chapter_number=1, scene_number=1,
        visual_concept="A cat", duration_seconds=10,
        narration_outline=["Hello world"],
    )
    return ScriptJSON(idea_id=idea_id, estimated_total_duration=10, scenes=[scene])


def test_save_and_get_script():
    pid = get_or_create_project("P3")
    idea = _make_idea()
    save_idea(pid, idea, 0.0, "pass")
    script = _make_script(idea_id=1)
    save_script(1, script)
    loaded = get_script_by_id(1)
    assert loaded is not None
    assert "scenes" in loaded
    assert loaded["scenes"][0]["visual_concept"] == "A cat"


def test_script_unique_idea_id():
    pid = get_or_create_project("P4")
    save_idea(pid, _make_idea(), 0.0, "pass")
    script = _make_script(idea_id=1)
    save_script(1, script)
    with pytest.raises(Exception):
        save_script(1, script)


# ---------- save / get voiceovers ----------

def _make_voiceover(script_id=1):
    vs = VoiceoverSceneJSON(scene_number=1, spoken_text="Hello from TTS")
    return VoiceoverJSON(script_id=script_id, voiceover_scenes=[vs])


def test_save_voiceover():
    pid = get_or_create_project("P5")
    save_idea(pid, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    vo = _make_voiceover(script_id=1)
    save_voiceover(1, vo)
    conn = sqlite3.connect(db_mod.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM voiceovers WHERE script_id = 1")
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    data = json.loads(row[0])
    assert data["voiceover_scenes"][0]["spoken_text"] == "Hello from TTS"


# ---------- save / get assets ----------

def _make_asset(script_id=1):
    asc = AssetSceneJSON(scene_number=1, image_prompt="cat", image_path="data/projects/1/scene_1.jpg")
    return AssetJSON(script_id=script_id, assets=[asc])


def test_save_asset():
    pid = get_or_create_project("P6")
    save_idea(pid, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    asset = _make_asset(script_id=1)
    save_asset(1, asset)
    conn = sqlite3.connect(db_mod.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM assets WHERE script_id = 1")
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    data = json.loads(row[0])
    assert data["assets"][0]["image_prompt"] == "cat"


# ---------- save seo ----------

def test_save_seo_metadata():
    pid = get_or_create_project("P7")
    save_idea(pid, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    seo = {"title": "SEO Title", "description": "desc", "tags": "t1,t2"}
    save_seo_metadata(1, seo)
    conn = sqlite3.connect(db_mod.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM seo_metadata WHERE script_id = 1")
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    data = json.loads(row[0])
    assert data["title"] == "SEO Title"


# ---------- get_ready_to_render_projects_with_audio ----------

def test_ready_to_render_needs_audio():
    pid = get_or_create_project("P8")
    save_idea(pid, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    asset_no_audio = AssetJSON(
        script_id=1,
        assets=[AssetSceneJSON(scene_number=1, image_prompt="x", image_path="x.jpg")],
    )
    save_asset(1, asset_no_audio)
    projects = get_ready_to_render_projects_with_audio()
    assert len(projects) == 0


def test_ready_to_render_with_audio():
    pid = get_or_create_project("P9")
    save_idea(pid, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    asset_data = {
        "script_id": 1,
        "assets": [{
            "scene_number": 1,
            "image_prompt": "x",
            "image_path": "x.jpg",
            "audio_path": "voice_1.mp3",
            "duration_seconds": 10,
        }],
    }
    conn = sqlite3.connect(db_mod.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO assets (script_id, content) VALUES (?, ?)", (1, json.dumps(asset_data)))
    conn.commit()
    conn.close()
    projects = get_ready_to_render_projects_with_audio()
    assert len(projects) == 1
    assert projects[0]["timeline"][0]["audio_path"] == "voice_1.mp3"


# ---------- delete_project_media ----------

def test_delete_project_media_removes_folder_keeps_db(tmp_path):
    pid = get_or_create_project("P10")
    save_idea(pid, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))

    fake_dir = os.path.join(os.path.dirname(db_mod.DB_PATH), '..', 'data', 'projects', '1')
    os.makedirs(fake_dir, exist_ok=True)
    with open(os.path.join(fake_dir, "dummy.txt"), "w") as f:
        f.write("hello")

    delete_project_media(pid)
    assert not os.path.exists(fake_dir)

    conn = sqlite3.connect(db_mod.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM scripts WHERE idea_id = 1")
    assert cursor.fetchone() is not None
    conn.close()
