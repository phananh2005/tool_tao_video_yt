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


def test_save_script_updates_existing_script_for_idea():
    pid = get_or_create_project("P4")
    save_idea(pid, _make_idea(), 0.0, "pass")
    script = _make_script(idea_id=1)
    save_script(1, script)

    updated_script = _make_script(idea_id=1)
    updated_script.scenes[0].visual_concept = "An updated cat scene"
    save_script(1, updated_script)

    loaded = get_script_by_id(1)
    assert loaded["scenes"][0]["visual_concept"] == "An updated cat scene"


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


def test_ready_to_render_ignores_empty_audio_paths():
    pid = get_or_create_project("P8 empty audio")
    save_idea(pid, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    assets = {
        "script_id": 1,
        "assets": [
            {"scene_number": 1, "image_path": "x.jpg", "audio_path": None},
            {"scene_number": 2, "image_path": "y.jpg", "audio_path": "  "},
        ],
    }
    conn = sqlite3.connect(db_mod.DB_PATH)
    conn.execute("INSERT INTO assets (script_id, content) VALUES (?, ?)", (1, json.dumps(assets)))
    conn.commit()
    conn.close()

    assert get_ready_to_render_projects_with_audio() == []


def _save_render_assets(script_id, assets):
    conn = sqlite3.connect(db_mod.DB_PATH)
    conn.execute(
        "INSERT INTO assets (script_id, content) VALUES (?, ?)",
        (script_id, json.dumps({"script_id": script_id, "assets": assets})),
    )
    conn.commit()
    conn.close()


def _valid_render_asset(scene_number=1, **overrides):
    asset = {
        "scene_number": scene_number,
        "image_prompt": "x",
        "image_path": f"scene_{scene_number}.jpg",
        "audio_path": f"voice_{scene_number}.mp3",
        "duration_seconds": 10,
    }
    asset.update(overrides)
    return asset


def _create_project_media_files(script_id, assets):
    project_dir = os.path.join(os.path.dirname(db_mod.DB_PATH), "projects", str(script_id))
    os.makedirs(project_dir, exist_ok=True)
    for asset in assets:
        for key in ("image_path", "audio_path"):
            path = asset.get(key)
            if isinstance(path, str) and path.strip():
                with open(os.path.join(project_dir, os.path.basename(path)), "wb") as media_file:
                    media_file.write(b"media")


def test_ready_to_render_with_audio():
    pid = get_or_create_project("P9")
    save_idea(pid, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    assets = [_valid_render_asset()]
    _create_project_media_files(1, assets)
    _save_render_assets(1, assets)

    projects = get_ready_to_render_projects_with_audio()

    assert len(projects) == 1
    assert projects[0]["timeline"] == [{
        "scene_number": 1,
        "duration": 10,
        "image_path": "scene_1.jpg",
        "audio_path": "voice_1.mp3",
    }]


@pytest.mark.parametrize("asset_overrides", [
    {"audio_path": None},
    {"audio_path": "  "},
    {"audio_path": 42},
    {"image_path": None},
    {"image_path": ""},
    {"image_path": "  "},
    {"image_path": 42},
    {"duration_seconds": None},
    {"duration_seconds": 0},
    {"duration_seconds": -1},
    {"duration_seconds": "10"},
    {"duration_seconds": float("nan")},
    {"duration_seconds": float("inf")},
    {"duration_seconds": 10 ** 1000},
    {"duration_seconds": 1e308},
])
def test_ready_to_render_rejects_invalid_scene_inputs(asset_overrides):
    get_or_create_project("Invalid render input")
    save_idea(1, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    assets = [_valid_render_asset(**asset_overrides)]
    _create_project_media_files(1, assets)
    _save_render_assets(1, assets)

    assert get_ready_to_render_projects_with_audio() == []


def test_ready_to_render_requires_all_script_scenes():
    get_or_create_project("Partial render inputs")
    save_idea(1, _make_idea(), 0.0, "pass")
    script = _make_script(idea_id=1)
    script.scenes.append(SceneJSON(
        chapter_number=1, scene_number=2, visual_concept="Another scene",
        duration_seconds=10, narration_outline=["More"],
    ))
    save_script(1, script)
    assets = [_valid_render_asset(scene_number=1)]
    _create_project_media_files(1, assets)
    _save_render_assets(1, assets)

    assert get_ready_to_render_projects_with_audio() == []


@pytest.mark.parametrize("assets", [
    [_valid_render_asset(), _valid_render_asset()],
    [_valid_render_asset(), _valid_render_asset(scene_number=2)],
])
def test_ready_to_render_rejects_duplicate_or_unexpected_scenes(assets):
    get_or_create_project("Invalid scene coverage")
    save_idea(1, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    _create_project_media_files(1, assets)
    _save_render_assets(1, assets)

    assert get_ready_to_render_projects_with_audio() == []


def test_ready_to_render_rejects_boolean_scene_number():
    get_or_create_project("Boolean scene number")
    save_idea(1, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    assets = [_valid_render_asset(scene_number=True)]
    _create_project_media_files(1, assets)
    _save_render_assets(1, assets)

    assert get_ready_to_render_projects_with_audio() == []


def test_ready_to_render_requires_non_empty_image_path():
    get_or_create_project("Missing image")
    save_idea(1, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    assets = [{"scene_number": 1, "audio_path": "voice_1.mp3", "duration_seconds": 10}]
    _create_project_media_files(1, assets)
    _save_render_assets(1, assets)

    assert get_ready_to_render_projects_with_audio() == []


@pytest.mark.parametrize("asset_overrides", [
    {"image_path": "missing.jpg"},
    {"audio_path": "missing.mp3"},
])
def test_ready_to_render_rejects_missing_media_files(asset_overrides):
    get_or_create_project("Missing media files")
    save_idea(1, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    assets = [_valid_render_asset(**asset_overrides)]
    _create_project_media_files(1, assets)
    missing_path = asset_overrides.get("image_path") or asset_overrides.get("audio_path")
    os.remove(os.path.join(os.path.dirname(db_mod.DB_PATH), "projects", "1", os.path.basename(missing_path)))
    _save_render_assets(1, assets)

    assert get_ready_to_render_projects_with_audio() == []


def test_ready_to_render_rejects_empty_media_files():
    get_or_create_project("Empty media files")
    save_idea(1, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    assets = [_valid_render_asset()]
    project_dir = os.path.join(os.path.dirname(db_mod.DB_PATH), "projects", "1")
    os.makedirs(project_dir, exist_ok=True)
    for key in ("image_path", "audio_path"):
        path = os.path.join(project_dir, os.path.basename(assets[0][key]))
        with open(path, "wb"):
            pass
    _save_render_assets(1, assets)

    assert get_ready_to_render_projects_with_audio() == []


def test_ready_to_render_uses_default_duration_for_legacy_asset():
    get_or_create_project("Legacy duration")
    save_idea(1, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    assets = [_valid_render_asset()]
    assets[0].pop("duration_seconds")
    _create_project_media_files(1, assets)
    _save_render_assets(1, assets)

    projects = get_ready_to_render_projects_with_audio()

    assert projects[0]["timeline"][0]["duration"] == 10


def test_ready_to_render_ignores_malformed_asset_payloads():
    get_or_create_project("Malformed assets")
    save_idea(1, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))
    conn = sqlite3.connect(db_mod.DB_PATH)
    conn.execute("INSERT INTO assets (script_id, content) VALUES (?, ?)", (1, json.dumps([])))
    conn.commit()
    conn.close()

    assert get_ready_to_render_projects_with_audio() == []


# ---------- delete_project_media ----------

def test_delete_project_media_removes_folder_keeps_db(tmp_path):
    pid = get_or_create_project("P10")
    save_idea(pid, _make_idea(), 0.0, "pass")
    save_script(1, _make_script(idea_id=1))

    save_seo_metadata(1, {"title": "Completed video"})
    fake_dir = os.path.join(os.path.dirname(db_mod.DB_PATH), 'projects', '1')
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
