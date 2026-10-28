import os
import sys
import pytest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import core.database as db_mod
from core.database import init_db
from core.exceptions import TubeChainException, ImageGenerationError, ImageRefusalError
from core.contracts import AssetSceneJSON, AssetJSON, SceneJSON, ScriptJSON, IdeaJSON
from core.database import (
    save_idea, save_script, save_asset, get_or_create_project,
    get_ready_to_render_projects_with_audio
)
from modules.scene_illustrator.engine import SceneIllustratorEngine
from modules.scene_illustrator.placeholder import create_placeholder_image
from modules.idea_engine.adapter import is_refusal_text


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    test_db = str(tmp_path / "test.db")
    db_mod.DB_PATH = test_db
    init_db()
    yield test_db


def test_image_refusal_error_hierarchy():
    err = ImageRefusalError(
        message="Gemini tu choi ve anh",
        reason="Nha cung cap ben thu ba",
        prompt="Steve Jobs presenting iPhone"
    )
    assert isinstance(err, ImageGenerationError)
    assert isinstance(err, TubeChainException)
    assert err.reason == "Nha cung cap ben thu ba"
    assert err.prompt == "Steve Jobs presenting iPhone"
    assert "Gemini tu choi ve anh" in str(err)


@pytest.mark.parametrize("text,expected", [
    ("Hiện tôi không tạo được hình ảnh bạn yêu cầu do lợi ích của các nhà cung cấp nội dung bên thứ ba. Vui lòng chỉnh sửa câu lệnh rồi thử lại", True),
    ("Tôi không thể tạo hình ảnh này do chính sách nội dung bên thứ ba.", True),
    ("I cannot generate images due to third-party content provider policies.", True),
    ("Can't generate image: safety guidelines violation.", True),
    ("Đây là bức ảnh tuyệt đẹp của một chú mèo trong công viên.", False),
    ("", False),
])
def test_is_refusal_text(text, expected):
    assert is_refusal_text(text) == expected


def test_create_placeholder_image(tmp_path):
    img_path = str(tmp_path / "scene_1.jpg")
    success = create_placeholder_image(img_path, scene_number=1, reason="AI Refusal")
    assert success is True
    assert os.path.isfile(img_path)
    assert os.path.getsize(img_path) > 0


def test_scene_illustrator_retries_on_refusal_and_succeeds(tmp_path):
    adapter = Mock()
    adapter.generate_text.side_effect = [
        "Cinematic 3D animation",  # develop_art_direction
        "Detailed Disney style Mickey",  # optimize_prompt scene 1
        "Cute cartoon rabbit inventor with magical crystal",  # sanitize_prompt_via_ai
    ]

    target_dir = tmp_path / "data" / "projects" / "101"
    target_dir.mkdir(parents=True, exist_ok=True)
    real_img = target_dir / "scene_1.jpg"

    def fake_generate_image(prompt, save_path=None):
        if "Mickey" in prompt:
            raise ImageRefusalError(
                message="Refused by third party",
                reason="nhà cung cấp nội dung bên thứ ba",
                prompt=prompt
            )
        # Success on sanitized prompt
        with open(save_path, "wb") as f:
            f.write(b"fake_jpeg_content_12345")
        return "saved_successfully"

    adapter.generate_image.side_effect = fake_generate_image
    engine = SceneIllustratorEngine(adapter=adapter)

    script_dict = {
        "scenes": [{"scene_number": 1, "visual_concept": "Mickey Mouse walking", "duration_seconds": 10}]
    }

    with patch("modules.scene_illustrator.engine.os.path.abspath") as mock_abs:
        mock_abs.return_value = str(target_dir)
        assets = engine.generate_assets(101, script_dict)

    assert len(assets.assets) == 1
    scene_asset = assets.assets[0]
    assert scene_asset.scene_number == 1
    assert scene_asset.image_path == "data/projects/101/scene_1.jpg"
    assert scene_asset.is_placeholder is False
    assert adapter.generate_image.call_count == 2


def test_scene_illustrator_falls_back_to_placeholder_when_all_retries_fail(tmp_path):
    adapter = Mock()
    adapter.generate_text.side_effect = [
        "Original Art Style",
        "Original Prompt",
        "Sanitized AI Prompt",
    ]

    target_dir = tmp_path / "data" / "projects" / "102"
    target_dir.mkdir(parents=True, exist_ok=True)

    def always_refuse(prompt, save_path=None):
        raise ImageRefusalError(
            message="Refused",
            reason="Lợi ích nhà cung cấp nội dung bên thứ ba",
            prompt=prompt
        )

    adapter.generate_image.side_effect = always_refuse
    engine = SceneIllustratorEngine(adapter=adapter)

    script_dict = {
        "scenes": [{"scene_number": 1, "visual_concept": "Iron Man flying", "duration_seconds": 10}]
    }

    with patch("modules.scene_illustrator.engine.os.path.abspath") as mock_abs:
        mock_abs.return_value = str(target_dir)
        assets = engine.generate_assets(102, script_dict)

    assert len(assets.assets) == 1
    scene_asset = assets.assets[0]
    assert scene_asset.is_placeholder is True
    assert "bên thứ ba" in scene_asset.refusal_reason
    assert os.path.isfile(str(target_dir / "scene_1.jpg"))
    assert os.path.getsize(str(target_dir / "scene_1.jpg")) > 0


def test_ready_to_render_accepts_placeholder_assets(tmp_path):
    project_id = get_or_create_project("Placeholder Test Project")
    idea = IdeaJSON(
        title="Test Idea", topics=["tech"], rabbit_hole_series=False,
        part_number=1, summary="Test summary"
    )
    save_idea(project_id, idea, 0.0, "pass")

    script = ScriptJSON(
        idea_id=1, estimated_total_duration=10,
        scenes=[SceneJSON(chapter_number=1, scene_number=1, visual_concept="A robot", duration_seconds=10, narration_outline=["hi"])]
    )
    save_script(1, script)

    proj_dir = tmp_path / "projects" / "1"
    proj_dir.mkdir(parents=True, exist_ok=True)
    img_file = proj_dir / "scene_1.jpg"
    img_file.write_bytes(b"placeholder_img_content")
    audio_file = proj_dir / "scene_1.mp3"
    audio_file.write_bytes(b"audio_content")

    asset_scene = AssetSceneJSON(
        scene_number=1,
        image_prompt="A generic robot",
        image_path=f"data/projects/1/{img_file.name}",
        audio_path=f"data/projects/1/{audio_file.name}",
        duration_seconds=10.0,
        is_placeholder=True,
        refusal_reason="Lợi ích nhà cung cấp nội dung bên thứ ba"
    )
    save_asset(1, AssetJSON(script_id=1, assets=[asset_scene]))

    ready = get_ready_to_render_projects_with_audio()
    assert len(ready) == 1
    assert ready[0]['script_id'] == 1
    assert ready[0]['timeline'][0]['scene_number'] == 1


def test_gemini_adapter_reraises_image_refusal_error():
    from modules.idea_engine.adapter import GeminiWebAdapter
    adapter = GeminiWebAdapter()

    mock_page = Mock()
    mock_eval = Mock()
    mock_eval.json_value.return_value = {
        "status": "refusal",
        "reason": "Hiện tôi không tạo được hình ảnh do lợi ích của bên thứ ba"
    }
    mock_page.wait_for_function.return_value = mock_eval

    mock_context = Mock()
    mock_context.pages = [mock_page]

    mock_p = Mock()
    mock_p.chromium.launch_persistent_context.return_value = mock_context

    with patch("modules.idea_engine.adapter.sync_playwright") as mock_sp:
        mock_sp.return_value.__enter__.return_value = mock_p
        with pytest.raises(ImageRefusalError) as exc_info:
            adapter.generate_image("Iron Man prompt", save_path="scene_1.jpg")

    assert "bên thứ ba" in exc_info.value.reason
    assert exc_info.value.prompt == "Iron Man prompt"


def test_scene_illustrator_does_not_skip_cached_placeholder(tmp_path):
    adapter = Mock()
    adapter.generate_text.return_value = "Style"
    adapter.generate_image.return_value = "saved"
    engine = SceneIllustratorEngine(adapter=adapter)

    existing_prompt = "Style\n\nGlobal Style: Style\n\nIMPORTANT: No text, no words, no letters, no logos, no watermarks."
    engine._get_existing_assets = Mock(return_value={
        1: {
            "image_prompt": existing_prompt,
            "image_path": "data/projects/99/scene_1.jpg",
            "is_placeholder": True
        }
    })

    script_dict = {"scenes": [{"scene_number": 1, "visual_concept": "A lighthouse", "duration_seconds": 10}]}
    target_dir = tmp_path / "data" / "projects" / "99"
    target_dir.mkdir(parents=True, exist_ok=True)
    real_img = target_dir / "scene_1.jpg"
    real_img.write_bytes(b"content")

    with patch("modules.scene_illustrator.engine.os.path.abspath", return_value=str(target_dir)):
        assets = engine.generate_assets(99, script_dict)

    assert adapter.generate_image.call_count == 1
    assert assets.assets[0].is_placeholder is False


def test_generate_single_image_returns_tuple_and_placeholder_state(tmp_path):
    adapter = Mock()
    adapter.generate_image.side_effect = ImageRefusalError("Refused", reason="bên thứ ba", prompt="prompt")
    engine = SceneIllustratorEngine(adapter=adapter)

    target_dir = tmp_path / "data" / "projects" / "55"
    target_dir.mkdir(parents=True, exist_ok=True)

    with patch("modules.scene_illustrator.engine.os.path.abspath", return_value=str(target_dir)):
        img_path, is_placeholder, refusal_reason = engine.generate_single_image(55, 1, "sensitive prompt")

    assert img_path == "data/projects/55/scene_1.jpg"
    assert is_placeholder is True
    assert refusal_reason == "bên thứ ba"
    assert os.path.isfile(str(target_dir / "scene_1.jpg"))


def test_api_generate_single_asset_saves_and_returns_placeholder_flag(tmp_path):
    import json
    from app import generate_single_asset, GenerateSingleAssetRequest, get_conn

    conn = get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS assets (id INTEGER PRIMARY KEY, script_id INTEGER UNIQUE, content TEXT)")
    initial_content = json.dumps({"script_id": 77, "assets": [{"scene_number": 1, "image_path": "", "image_prompt": "old"}]})
    conn.execute("INSERT OR REPLACE INTO assets (script_id, content) VALUES (77, ?)", (initial_content,))
    conn.commit()
    conn.close()

    with patch("modules.scene_illustrator.engine.SceneIllustratorEngine.generate_single_image", return_value=("data/projects/77/scene_1.jpg", True, "bên thứ ba")):
        res = generate_single_asset(77, 1, GenerateSingleAssetRequest(image_prompt="new prompt"))

    assert res["status"] == "success"
    assert res["image_path"] == "data/projects/77/scene_1.jpg"
    assert res["is_placeholder"] is True
    assert res["refusal_reason"] == "bên thứ ba"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT content FROM assets WHERE script_id = 77")
    row = cur.fetchone()
    conn.close()
    data = json.loads(row[0])
    assert data["assets"][0]["is_placeholder"] is True
    assert data["assets"][0]["refusal_reason"] == "bên thứ ba"


