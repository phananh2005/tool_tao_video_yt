import os
import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from modules.voiceover.synthesizer import (
    _generate_audio,
    _mask_credentials,
    _normalize_tts_text,
    get_audio_duration,
    VoiceSynthesizer
)

def test_mask_credentials():
    url = "http://myuser:secret123@proxy.domain.com:8080"
    masked = _mask_credentials(f"Error connecting to {url}")
    assert "secret123" not in masked
    assert "http://myuser:***@proxy.domain.com:8080" in masked

    url_token_only = "http://:my_api_token@proxy:8080"
    masked_token = _mask_credentials(f"Error {url_token_only}")
    assert "my_api_token" not in masked_token
    assert "http://:***@proxy:8080" in masked_token
    assert _mask_credentials("") == ""

def test_generate_audio_success():
    with patch.dict(os.environ, {}, clear=True), \
         patch("edge_tts.Communicate") as mock_comm:
        instance = MagicMock()
        instance.save = AsyncMock()
        mock_comm.return_value = instance

        asyncio.run(_generate_audio("Xin chào", "fake_out.mp3"))
        mock_comm.assert_called_once_with("Xin chào", "vi-VN-HoaiMyNeural")
        instance.save.assert_awaited_once_with("fake_out.mp3")

def test_generate_audio_with_proxy():
    with patch.dict(os.environ, {"EDGE_TTS_PROXY": "http://127.0.0.1:8888"}, clear=True), \
         patch("edge_tts.Communicate") as mock_comm:
        instance = MagicMock()
        instance.save = AsyncMock()
        mock_comm.return_value = instance

        asyncio.run(_generate_audio("Xin chào", "fake_out.mp3"))
        mock_comm.assert_called_once_with("Xin chào", "vi-VN-HoaiMyNeural", proxy="http://127.0.0.1:8888")

def test_generate_audio_empty_or_whitespace_skips():
    with patch("edge_tts.Communicate") as mock_comm:
        asyncio.run(_generate_audio("", "fake_out.mp3"))
        asyncio.run(_generate_audio("   ", "fake_out.mp3"))
        mock_comm.assert_not_called()

def test_generate_audio_403_raises_with_guidance(caplog):
    with patch.dict(os.environ, {}, clear=True), \
         patch("edge_tts.Communicate") as mock_comm, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        instance = MagicMock()
        instance.save = AsyncMock(side_effect=Exception("403, message='Invalid response status'"))
        mock_comm.return_value = instance

        with pytest.raises(Exception) as exc_info:
            asyncio.run(_generate_audio("Xin chào", "fake_out.mp3"))

        assert "403" in str(exc_info.value)
        log_text = caplog.text
        assert "pip install --upgrade edge-tts>=7.3.1" in log_text
        assert log_text.count("pip install --upgrade edge-tts>=7.3.1") == 1

def test_generate_audio_masks_proxy_in_log(caplog):
    with patch.dict(os.environ, {"EDGE_TTS_PROXY": "http://user:mypassword@proxy:8080"}, clear=True), \
         patch("edge_tts.Communicate") as mock_comm, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        instance = MagicMock()
        instance.save = AsyncMock(side_effect=Exception("Cannot connect http://user:mypassword@proxy:8080"))
        mock_comm.return_value = instance

        with pytest.raises(Exception):
            asyncio.run(_generate_audio("Xin chào", "fake_out.mp3"))

        assert "mypassword" not in caplog.text
        assert "http://user:***@proxy:8080" in caplog.text

def test_get_audio_duration_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="12.34\n")
        duration = get_audio_duration("real.mp3")
        assert duration == 12.34

def test_get_audio_duration_fallback():
    with patch("subprocess.run", side_effect=Exception("ffprobe failed")):
        duration = get_audio_duration("non_existent.mp3")
        assert duration == 10.0

def test_synthesize_voiceover_unready():
    synthesizer = VoiceSynthesizer()
    with patch("sqlite3.connect") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.cursor.return_value = mock_cursor

        result = synthesizer.synthesize_voiceover(script_id=999999)
        assert result is False

def test_synthesize_single_scene():
    synthesizer = VoiceSynthesizer()
    with patch.object(synthesizer, "_update_asset_duration") as mock_update, \
         patch("modules.voiceover.synthesizer._generate_audio") as mock_gen, \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=5.5), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.getsize", return_value=1234), \
         patch("os.makedirs"):
        ret = synthesizer.synthesize_single_scene(script_id=42, scene_number=1, text="Nội dung scene")
        assert ret == "/data/projects/42/voice_1.mp3"
        mock_update.assert_called_once_with(42, 1, 5.5, "voice_1.mp3")

def test_synthesize_single_scene_empty_raises_value_error():
    synthesizer = VoiceSynthesizer()
    with pytest.raises(ValueError):
        synthesizer.synthesize_single_scene(script_id=42, scene_number=1, text="")
    with pytest.raises(ValueError):
        synthesizer.synthesize_single_scene(script_id=42, scene_number=1, text="   ")
    with pytest.raises(ValueError):
        synthesizer.synthesize_single_scene(script_id=42, scene_number=1, text=None)

def test_synthesize_single_scene_invalid_scene_number():
    synthesizer = VoiceSynthesizer()
    with pytest.raises(ValueError, match="scene_number không hợp lệ"):
        synthesizer.synthesize_single_scene(script_id=42, scene_number=0, text="valid text")
    with pytest.raises(ValueError, match="scene_number không hợp lệ"):
        synthesizer.synthesize_single_scene(script_id=42, scene_number=True, text="valid text")
    with pytest.raises(ValueError, match="scene_number không hợp lệ"):
        synthesizer.synthesize_single_scene(script_id=42, scene_number="1", text="valid text")

def test_synthesize_single_scene_file_not_found_raises_runtime_error():
    synthesizer = VoiceSynthesizer()
    with patch("modules.voiceover.synthesizer._generate_audio"), \
         patch("os.path.isfile", return_value=False), \
         patch("os.makedirs"):
        with pytest.raises(RuntimeError, match="Không tạo được file âm thanh"):
            synthesize_ret = synthesizer.synthesize_single_scene(script_id=42, scene_number=1, text="Xin chào")

def test_synthesize_voiceover_invalid_or_null_scenes():
    synthesizer = VoiceSynthesizer()
    with patch("sqlite3.connect") as mock_conn:
        mock_cursor = MagicMock()
        # Test khi voiceover_scenes là None
        mock_cursor.fetchone.return_value = (json.dumps({"voiceover_scenes": None}),)
        mock_conn.return_value.cursor.return_value = mock_cursor

        res = synthesizer.synthesize_voiceover(script_id=300)
        assert res is False

    # Test khi scene_number không hợp lệ (None hoặc <= 0)
    vo_json = json.dumps({
        "voiceover_scenes": [
            {"scene_number": None, "spoken_text": "Bad scene number"},
            {"scene_number": 0, "spoken_text": "Zero scene number"},
            {"scene_number": True, "spoken_text": "Bool scene number"}
        ]
    })
    with patch("sqlite3.connect") as mock_conn, \
         patch("os.makedirs"):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (vo_json,)
        mock_conn.return_value.cursor.return_value = mock_cursor

        res = synthesizer.synthesize_voiceover(script_id=301)
        assert res == []

def test_update_asset_duration_sqlite_success_and_null_guard(tmp_path):
    import sqlite3
    db_file = str(tmp_path / "test_assets.db")
    with sqlite3.connect(db_file) as conn:
        conn.execute("CREATE TABLE assets (id INTEGER PRIMARY KEY, script_id INTEGER UNIQUE, content TEXT)")
        conn.execute("INSERT INTO assets (script_id, content) VALUES (1, ?)", (json.dumps({"assets": None}),))
        conn.execute("INSERT INTO assets (script_id, content) VALUES (3, NULL)")
        conn.execute("INSERT INTO assets (script_id, content) VALUES (4, '')")
        conn.commit()

    synthesizer = VoiceSynthesizer()
    with patch("modules.voiceover.synthesizer.DB_PATH", db_file):
        synthesizer._update_asset_duration(script_id=1, scene_number=1, duration=6.5, audio_name="voice_1.mp3")
        synthesizer._update_asset_duration(script_id=3, scene_number=1, duration=7.0, audio_name="voice_3.mp3")
        synthesizer._update_asset_duration(script_id=4, scene_number=1, duration=8.0, audio_name="voice_4.mp3")

        with sqlite3.connect(db_file) as conn:
            cur = conn.cursor()
            cur.execute("SELECT content FROM assets WHERE script_id = 1")
            content = json.loads(cur.fetchone()[0])
            assert content["assets"][0]["scene_number"] == 1

            cur.execute("SELECT content FROM assets WHERE script_id = 3")
            content3 = json.loads(cur.fetchone()[0])
            assert content3["assets"][0]["scene_number"] == 1

            cur.execute("SELECT content FROM assets WHERE script_id = 4")
            content4 = json.loads(cur.fetchone()[0])
            assert content4["assets"][0]["scene_number"] == 1

        synthesizer._update_asset_duration(script_id=2, scene_number=2, duration=8.0, audio_name="voice_2.mp3")
        with sqlite3.connect(db_file) as conn:
            cur = conn.cursor()
            cur.execute("SELECT content FROM assets WHERE script_id = 2")
            content2 = json.loads(cur.fetchone()[0])
            assert content2["script_id"] == 2

def test_synthesize_voiceover_with_scenes_cache_hit():
    synthesizer = VoiceSynthesizer()
    vo_json = json.dumps({
        "voiceover_scenes": [
            {"scene_number": 1, "spoken_text": "Scene mot"}
        ]
    })
    asset_json = json.dumps({"script_id": 100, "voice": "vi-VN-HoaiMyNeural", "assets": []})
    with patch("sqlite3.connect") as mock_conn, \
         patch.object(synthesizer, "_batch_update_asset_durations") as mock_batch, \
         patch("modules.voiceover.synthesizer._generate_audio") as mock_gen, \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=4.0), \
         patch("os.path.exists", return_value=True), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.getsize", return_value=100), \
         patch("os.makedirs"):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [(vo_json,), (asset_json,)]
        mock_conn.return_value.cursor.return_value = mock_cursor

        res = synthesizer.synthesize_voiceover(script_id=100)
        assert res == ["/data/projects/100/voice_1.mp3"]
        mock_batch.assert_called_once()
        mock_gen.assert_not_called()

def test_synthesize_voiceover_cache_miss_and_none_text():
    synthesizer = VoiceSynthesizer()
    vo_json = json.dumps({
        "voiceover_scenes": [
            {"scene_number": 1, "spoken_text": None},
            {"scene_number": 2, "spoken_text": ""},
            {"scene_number": 3, "spoken_text": "Scene 3 sinh moi"}
        ]
    })
    asset_json = json.dumps({"script_id": 200, "voice": "vi-VN-HoaiMyNeural", "assets": []})
    with patch("sqlite3.connect") as mock_conn, \
         patch.object(synthesizer, "_batch_update_asset_durations") as mock_batch, \
         patch("modules.voiceover.synthesizer._generate_audio") as mock_gen, \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=3.2), \
         patch("time.sleep") as mock_sleep, \
         patch("os.path.exists", return_value=False), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.getsize", return_value=200), \
         patch("os.makedirs"):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [(vo_json,), (asset_json,)]
        mock_conn.return_value.cursor.return_value = mock_cursor

        res = synthesizer.synthesize_voiceover(script_id=200)
        # Cả 3 scene đều có audio (scene 1, 2 sinh silence, scene 3 gọi TTS)
        assert res == ["/data/projects/200/voice_1.mp3", "/data/projects/200/voice_2.mp3", "/data/projects/200/voice_3.mp3"]
        mock_batch.assert_called_once()
        mock_gen.assert_called_once()
        mock_sleep.assert_called_once()

def test_update_asset_duration_sqlite_primitive_and_malformed_json(tmp_path):
    import sqlite3
    db_file = str(tmp_path / "test_assets_malformed.db")
    with sqlite3.connect(db_file) as conn:
        conn.execute("CREATE TABLE assets (id INTEGER PRIMARY KEY, script_id INTEGER UNIQUE, content TEXT)")
        conn.execute("INSERT INTO assets (script_id, content) VALUES (10, 'null')")
        conn.execute("INSERT INTO assets (script_id, content) VALUES (20, '[]')")
        conn.execute("INSERT INTO assets (script_id, content) VALUES (30, '{invalid_json')")
        conn.commit()

    synthesizer = VoiceSynthesizer()
    with patch("modules.voiceover.synthesizer.DB_PATH", db_file):
        for sid in (10, 20, 30):
            synthesizer._update_asset_duration(script_id=sid, scene_number=1, duration=5.0, audio_name="voice_1.mp3")
            with sqlite3.connect(db_file) as conn:
                cur = conn.cursor()
                cur.execute("SELECT content FROM assets WHERE script_id = ?", (sid,))
                data = json.loads(cur.fetchone()[0])
                assert isinstance(data, dict)
                assert data["assets"][0]["scene_number"] == 1

def test_synthesize_single_scene_error_cleans_up_corrupt_file():
    synthesizer = VoiceSynthesizer()
    with patch("modules.voiceover.synthesizer._generate_audio", side_effect=Exception("network timeout")), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove, \
         patch("os.makedirs"):
        with pytest.raises(Exception, match="network timeout"):
            synthesizer.synthesize_single_scene(script_id=12, scene_number=1, text="scene test")
        mock_remove.assert_called_once()

def test_synthesize_single_scene_masks_credentials_in_raised_exception():
    synthesizer = VoiceSynthesizer()
    with patch("modules.voiceover.synthesizer._generate_audio", side_effect=Exception("Auth error: http://user:supersecret999@proxy.lan:8080")), \
         patch("os.path.exists", return_value=False), \
         patch("os.makedirs"):
        with pytest.raises(RuntimeError) as exc_info:
            synthesizer.synthesize_single_scene(script_id=15, scene_number=1, text="scene test")
        assert "supersecret999" not in str(exc_info.value)
        assert "http://user:***@proxy.lan:8080" in str(exc_info.value)

def test_synthesize_voiceover_partial_failure_returns_false():
    synthesizer = VoiceSynthesizer()
    vo_json = json.dumps({
        "voiceover_scenes": [
            {"scene_number": 1, "spoken_text": "Scene 1 ok"},
            {"scene_number": 2, "spoken_text": "Scene 2 fail"}
        ]
    })
    # Scene 1 tạo file thành công, Scene 2 bị lỗi
    def fake_gen(text, path):
        if "Scene 2" in text:
            raise Exception("Scene 2 network drop")

    with patch("sqlite3.connect") as mock_conn, \
         patch("modules.voiceover.synthesizer._generate_audio", side_effect=fake_gen), \
         patch.object(synthesizer, "_update_asset_duration"), \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=4.0), \
         patch("os.path.exists", return_value=False), \
         patch("os.path.isfile", side_effect=[True, False]), \
         patch("os.path.getsize", side_effect=[100, 0]), \
         patch("time.sleep"), \
         patch("os.makedirs"):
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (vo_json,)
        mock_conn.return_value.cursor.return_value = mock_cur

        res = synthesizer.synthesize_voiceover(script_id=600)
        assert res is False

def test_synthesize_voiceover_masks_credentials_in_error_log(caplog):
    synthesizer = VoiceSynthesizer()
    vo_json = json.dumps({"voiceover_scenes": [{"scene_number": 1, "spoken_text": "Scene 1 text"}]})
    with patch("sqlite3.connect") as mock_conn, \
         patch("modules.voiceover.synthesizer._generate_audio", side_effect=Exception("Failed: http://user:secretpass123@proxy.domain:8080")), \
         patch("os.path.exists", return_value=False), \
         patch("os.path.isfile", return_value=False), \
         patch("os.makedirs"):
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (vo_json,)
        mock_conn.return_value.cursor.return_value = mock_cur

        paths = synthesizer.synthesize_voiceover(script_id=500)
        assert paths is False
        assert "secretpass123" not in caplog.text
        assert "http://user:***@proxy.domain:8080" in caplog.text

def test_synthesize_voiceover_malformed_db_json():
    synthesizer = VoiceSynthesizer()
    for bad_content in ("null", "[]", "{malformed", ""):
        with patch("sqlite3.connect") as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = (bad_content,) if bad_content != "" else None
            mock_conn.return_value.cursor.return_value = mock_cur
            assert synthesizer.synthesize_voiceover(script_id=999) is False

def test_synthesize_voiceover_error_cleans_up_corrupt_file():
    synthesizer = VoiceSynthesizer()
    vo_json = json.dumps({"voiceover_scenes": [{"scene_number": 1, "spoken_text": "Lỗi mạng"}]})
    with patch("sqlite3.connect") as mock_conn, \
         patch("modules.voiceover.synthesizer._generate_audio", side_effect=Exception("WS disconnect")), \
         patch("os.path.exists", side_effect=[False, True, False]), \
         patch("os.path.isfile", return_value=False), \
         patch("os.remove") as mock_remove, \
         patch("os.makedirs"):
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (vo_json,)
        mock_conn.return_value.cursor.return_value = mock_cur

        paths = synthesizer.synthesize_voiceover(script_id=400)
        assert paths is False
        mock_remove.assert_called_once()

def test_normalize_tts_text():
    assert _normalize_tts_text("") == ""
    assert _normalize_tts_text(None) == ""
    assert _normalize_tts_text("   \n\t  ") == ""

    # Ellipsis normalization
    sample_dots = "Bạn đang bước đi trong bóng tối... thì đột ngột, sàn nhà sụp đổ."
    normalized_dots = _normalize_tts_text(sample_dots)
    assert "..." not in normalized_dots
    assert "…" not in normalized_dots
    assert "bóng tối." in normalized_dots or "bóng tối," in normalized_dots

    # Unicode ellipsis
    sample_unicode = "Cơn ác mộng thực sự… bây giờ mới bắt đầu."
    assert "…" not in _normalize_tts_text(sample_unicode)

    # Whitespace and newlines collapse
    sample_spaces = "Câu 1. \n\n  Câu 2   với nhiều    khoảng trắng."
    normalized_spaces = _normalize_tts_text(sample_spaces)
    assert "\n" not in normalized_spaces
    assert "   " not in normalized_spaces
    assert "Câu 1. Câu 2 với nhiều khoảng trắng." == normalized_spaces

def test_generate_audio_fallback_voice_on_no_audio_received():
    from edge_tts.exceptions import NoAudioReceived
    calls = []
    def fake_comm(text, voice, **kwargs):
        calls.append(voice)
        inst = MagicMock()
        if len(calls) == 1:
            inst.save = AsyncMock(side_effect=NoAudioReceived("No audio was received. Please verify that your parameters are correct."))
        else:
            inst.save = AsyncMock(return_value=None)
        return inst

    with patch.dict(os.environ, {}, clear=True), \
         patch("edge_tts.Communicate", side_effect=fake_comm), \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        asyncio.run(_generate_audio("Xin chào bạn...", "out.mp3", allow_voice_fallback=True))

    assert len(calls) == 2
    assert calls[0] == "vi-VN-HoaiMyNeural"
    assert calls[1] == "vi-VN-NamMinhNeural"
    mock_sleep.assert_awaited_once()

def test_generate_audio_respects_env_voice():
    with patch.dict(os.environ, {"EDGE_TTS_VOICE": "vi-VN-NamMinhNeural", "EDGE_TTS_FALLBACK_VOICE": "vi-VN-HoaiMyNeural"}, clear=True), \
         patch("edge_tts.Communicate") as mock_comm:
        instance = MagicMock()
        instance.save = AsyncMock()
        mock_comm.return_value = instance

        asyncio.run(_generate_audio("Xin chào", "out.mp3"))
        mock_comm.assert_called_once_with("Xin chào", "vi-VN-NamMinhNeural")

def test_generate_audio_logs_no_audio_received_guidance(caplog):
    from edge_tts.exceptions import NoAudioReceived
    with patch.dict(os.environ, {}, clear=True), \
         patch("edge_tts.Communicate") as mock_comm, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        instance = MagicMock()
        instance.save = AsyncMock(side_effect=NoAudioReceived("No audio was received."))
        mock_comm.return_value = instance

        with pytest.raises(Exception):
            asyncio.run(_generate_audio("Test phrase", "out.mp3"))

        assert "tạm thời không trả về audio" in caplog.text or "rate limit" in caplog.text

def test_normalize_tts_text_mixed_ellipsis_and_punctuation_only():
    # Mixed unicode and ascii ellipses
    assert _normalize_tts_text("Chào bạn…….") == "Chào bạn."
    assert _normalize_tts_text("Chào bạn.……") == "Chào bạn."
    assert _normalize_tts_text("Chào bạn...….") == "Chào bạn."

    # Punctuation-only / non-speakable strings should return empty
    assert _normalize_tts_text("...") == ""
    assert _normalize_tts_text("……") == ""
    assert _normalize_tts_text("???") == ""
    assert _normalize_tts_text("- - -") == ""
    assert _normalize_tts_text("! . ?") == ""

def test_generate_audio_fallback_voice_two_way_swapping(caplog):
    from edge_tts.exceptions import NoAudioReceived
    calls = []
    def fake_comm(text, voice, **kwargs):
        calls.append(voice)
        inst = MagicMock()
        if len(calls) < 3:
            inst.save = AsyncMock(side_effect=NoAudioReceived("No audio was received."))
        else:
            inst.save = AsyncMock(return_value=None)
        return inst

    with patch.dict(os.environ, {}, clear=True), \
         patch("edge_tts.Communicate", side_effect=fake_comm), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        asyncio.run(_generate_audio("Xin chào", "out.mp3", allow_voice_fallback=True))

    assert len(calls) == 3
    assert calls[0] == "vi-VN-HoaiMyNeural"
    assert calls[1] == "vi-VN-NamMinhNeural"
    assert calls[2] == "vi-VN-HoaiMyNeural"
    # Verify accurate previous_voice in log
    assert "nghẽn giọng vi-VN-NamMinhNeural" in caplog.text
    assert "Chuyển sang giọng 'vi-VN-HoaiMyNeural'" in caplog.text

def test_synthesize_voiceover_skips_punctuation_only_scenes():
    synthesizer = VoiceSynthesizer()
    vo_json = json.dumps({
        "voiceover_scenes": [
            {"scene_number": 1, "spoken_text": "..."},
            {"scene_number": 2, "spoken_text": "Scene 2 hợp lệ"}
        ]
    })
    with patch("sqlite3.connect") as mock_conn, \
         patch("modules.voiceover.synthesizer._generate_audio") as mock_gen, \
         patch("modules.voiceover.synthesizer._generate_silence_audio") as mock_silence, \
         patch.object(synthesizer, "_update_asset_duration"), \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=3.5), \
         patch("os.path.exists", return_value=False), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.getsize", return_value=100), \
         patch("time.sleep"), \
         patch("os.makedirs"):
        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [(vo_json,), None, None]
        mock_conn.return_value.cursor.return_value = mock_cur

        res = synthesizer.synthesize_voiceover(script_id=700)
        assert res == ["/data/projects/700/voice_1.mp3", "/data/projects/700/voice_2.mp3"]
        assert mock_silence.call_count == 1
        assert mock_gen.call_count == 1
        assert mock_gen.call_args[0][0] == "Scene 2 hợp lệ"

def test_generate_audio_preserves_single_voice_by_default(caplog):
    from edge_tts.exceptions import NoAudioReceived
    calls = []
    def fake_comm(text, voice, **kwargs):
        calls.append(voice)
        inst = MagicMock()
        if len(calls) == 1:
            inst.save = AsyncMock(side_effect=NoAudioReceived("No audio was received."))
        else:
            inst.save = AsyncMock(return_value=None)
        return inst

    with patch.dict(os.environ, {}, clear=True), \
         patch("edge_tts.Communicate", side_effect=fake_comm), \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        asyncio.run(_generate_audio("Xin chào", "out.mp3", voice="vi-VN-HoaiMyNeural"))

    assert len(calls) == 2
    # Mặc định KHÔNG được tự ý đổi chéo sang NamMinh để giữ nguyên nhân vật
    assert calls[0] == "vi-VN-HoaiMyNeural"
    assert calls[1] == "vi-VN-HoaiMyNeural"
    assert "nhất quán" in caplog.text or "giữ nguyên" in caplog.text.lower()
    mock_sleep.assert_awaited_once()

def test_synthesize_voiceover_uses_consistent_voice_across_all_scenes():
    synthesizer = VoiceSynthesizer()
    vo_json = json.dumps({
        "voiceover_scenes": [
            {"scene_number": 1, "spoken_text": "Scene một"},
            {"scene_number": 2, "spoken_text": "Scene hai"}
        ]
    })
    with patch("sqlite3.connect") as mock_conn, \
         patch("modules.voiceover.synthesizer._generate_audio") as mock_gen, \
         patch.object(synthesizer, "_update_asset_duration"), \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=3.0), \
         patch("os.path.exists", return_value=False), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.getsize", return_value=100), \
         patch("time.sleep"), \
         patch("os.makedirs"):
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (vo_json,)
        mock_conn.return_value.cursor.return_value = mock_cur

        res = synthesizer.synthesize_voiceover(script_id=800, voice="vi-VN-NamMinhNeural")
        assert res == ["/data/projects/800/voice_1.mp3", "/data/projects/800/voice_2.mp3"]
        assert mock_gen.call_count == 2
        for call_args in mock_gen.call_args_list:
            # Voice truyền vào phải đồng bộ NamMinh cho tất cả các scene
            assert call_args[1].get("voice") == "vi-VN-NamMinhNeural" or (len(call_args[0]) >= 3 and call_args[0][2] == "vi-VN-NamMinhNeural")

def test_synthesize_single_scene_supports_voice_parameter():
    synthesizer = VoiceSynthesizer()
    with patch("modules.voiceover.synthesizer._generate_audio") as mock_gen, \
         patch.object(synthesizer, "_update_asset_duration"), \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=2.5), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.getsize", return_value=100), \
         patch("os.makedirs"):
        res = synthesizer.synthesize_single_scene(script_id=800, scene_number=1, text="Xin chào", voice="vi-VN-NamMinhNeural")
        assert res == "/data/projects/800/voice_1.mp3"
        assert mock_gen.call_count == 1
        assert (mock_gen.call_args[1].get("voice") == "vi-VN-NamMinhNeural" or
                (len(mock_gen.call_args[0]) >= 3 and mock_gen.call_args[0][2] == "vi-VN-NamMinhNeural"))

def test_api_synthesize_voice_endpoints_support_voice_param():
    from app import synthesize_voice, synthesize_voice_scene, SynthesizeVoiceRequest, SynthesizeSceneRequest

    with patch("app.VoiceSynthesizer") as mock_synth_cls, \
         patch("app.get_conn") as mock_conn:
        mock_synth = mock_synth_cls.return_value
        mock_synth.synthesize_voiceover.return_value = ["/data/projects/1/voice_1.mp3"]
        mock_synth.synthesize_single_scene.return_value = "/data/projects/1/voice_1.mp3"

        # 1. Test gọi synthesize_voice kèm payload voice
        req = SynthesizeVoiceRequest(voice="vi-VN-NamMinhNeural")
        resp = synthesize_voice(script_id=1, req=req)
        assert resp == {"status": "success", "paths": ["/data/projects/1/voice_1.mp3"]}
        mock_synth.synthesize_voiceover.assert_called_with(1, voice="vi-VN-NamMinhNeural", force=False)

        # 2. Test gọi synthesize_voice không kèm payload (tương thích ngược)
        resp_no_body = synthesize_voice(script_id=1, req=None)
        assert resp_no_body == {"status": "success", "paths": ["/data/projects/1/voice_1.mp3"]}
        mock_synth.synthesize_voiceover.assert_called_with(1, voice=None, force=False)

        # 3. Test gọi synthesize_voice_scene kèm voice
        req_scene = SynthesizeSceneRequest(text="Scene text", voice="vi-VN-NamMinhNeural")
        resp_scene = synthesize_voice_scene(script_id=1, scene_number=2, req=req_scene)
        assert resp_scene == {"status": "success", "audio_url": "/data/projects/1/voice_1.mp3"}
        mock_synth.synthesize_single_scene.assert_called_with(1, 2, "Scene text", voice="vi-VN-NamMinhNeural")

def test_synthesize_voiceover_forces_regenerate_when_voice_changes():
    from modules.voiceover.synthesizer import _generate_silence_audio
    synthesizer = VoiceSynthesizer()
    vo_json = json.dumps({"voiceover_scenes": [{"scene_number": 1, "spoken_text": "Scene một"}]})
    asset_json = json.dumps({"voice": "vi-VN-HoaiMyNeural", "assets": []})

    with patch("sqlite3.connect") as mock_conn, \
         patch("modules.voiceover.synthesizer._generate_audio") as mock_gen, \
         patch.object(synthesizer, "_update_asset_duration"), \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=3.0), \
         patch("os.path.exists", return_value=True), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.getsize", return_value=100), \
         patch("time.sleep"), \
         patch("os.makedirs"):
        mock_cur = MagicMock()
        # Lần 1: voiceovers, lần 2: assets (có voice Hoài My), lần 3: batch update assets
        mock_cur.fetchone.side_effect = [(vo_json,), (asset_json,), (asset_json,)]
        mock_conn.return_value.cursor.return_value = mock_cur

        # Gọi với giọng NamMinh -> khác giọng HoaiMy cũ -> Phải gọi _generate_audio dù file đã tồn tại!
        res = synthesizer.synthesize_voiceover(script_id=900, voice="vi-VN-NamMinhNeural")
        assert res == ["/data/projects/900/voice_1.mp3"]
        mock_gen.assert_called_once()
        assert mock_gen.call_args[1].get("voice") == "vi-VN-NamMinhNeural"

def test_generate_silence_audio_invokes_ffmpeg():
    from modules.voiceover.synthesizer import _generate_silence_audio
    with patch("subprocess.run") as mock_run:
        res = _generate_silence_audio("out_silence.mp3", duration=1.0)
        assert res is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd[0]
        assert "anullsrc=r=24000:cl=mono" in cmd

def test_synthesize_voiceover_forces_when_saved_voice_is_none_and_non_default_voice_requested():
    synthesizer = VoiceSynthesizer()
    vo_json = json.dumps({"voiceover_scenes": [{"scene_number": 1, "spoken_text": "Scene một"}]})
    # Dự án cũ: asset không có key voice
    asset_json = json.dumps({"script_id": 950, "assets": []})

    with patch("sqlite3.connect") as mock_conn, \
         patch("modules.voiceover.synthesizer._generate_audio") as mock_gen, \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=3.0), \
         patch("os.path.isdir", return_value=True), \
         patch("os.listdir", return_value=["voice_1.mp3"]), \
         patch("os.path.exists", return_value=True), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.getsize", return_value=100), \
         patch("time.sleep"), \
         patch("os.makedirs"):
        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [(vo_json,), (asset_json,), (asset_json,)]
        mock_conn.return_value.cursor.return_value = mock_cur

        res = synthesizer.synthesize_voiceover(script_id=950, voice="vi-VN-NamMinhNeural")
        assert res == ["/data/projects/950/voice_1.mp3"]
        # Phải tự động kích hoạt thu âm lại bằng force=True
        mock_gen.assert_called_once()

def test_synthesize_voiceover_single_db_update_transaction():
    synthesizer = VoiceSynthesizer()
    vo_json = json.dumps({
        "voiceover_scenes": [
            {"scene_number": 1, "spoken_text": "Scene 1"},
            {"scene_number": 2, "spoken_text": "Scene 2"}
        ]
    })
    asset_json = json.dumps({"script_id": 960, "assets": []})

    with patch("sqlite3.connect") as mock_conn, \
         patch("modules.voiceover.synthesizer._generate_audio"), \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=2.0), \
         patch("os.path.exists", return_value=False), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.getsize", return_value=100), \
         patch("time.sleep"), \
         patch("os.makedirs"):
        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [(vo_json,), (asset_json,), (asset_json,)]
        mock_conn.return_value.cursor.return_value = mock_cur

        synthesizer.synthesize_voiceover(script_id=960)
        # Chỉ có 1 câu lệnh UPDATE duy nhất vào assets sau vòng lặp
        update_calls = [c for c in mock_cur.execute.call_args_list if "UPDATE assets" in str(c)]
        assert len(update_calls) == 1

def test_synthesize_single_scene_empty_text_generates_silence():
    synthesizer = VoiceSynthesizer()
    with patch("modules.voiceover.synthesizer._generate_silence_audio") as mock_silence, \
         patch.object(synthesizer, "_update_asset_duration"), \
         patch("modules.voiceover.synthesizer.get_audio_duration", return_value=1.0), \
         patch("os.path.isfile", return_value=True), \
         patch("os.path.getsize", return_value=100), \
         patch("os.makedirs"):
        res = synthesizer.synthesize_single_scene(script_id=970, scene_number=1, text="...")
        assert res == "/data/projects/970/voice_1.mp3"
        mock_silence.assert_called_once()




