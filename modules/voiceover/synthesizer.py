from core.logger import get_logger
logger = get_logger(__name__)
import os
import sqlite3
import json
import subprocess
import asyncio
import time
import random
import re
from core.database import DB_PATH

def _mask_credentials(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'(://[^:\s]*):([^@\s]+)@', r'\1:***@', str(text))

def _normalize_tts_text(text: str) -> str:
    if not text:
        return ""
    clean = str(text).replace('\r\n', ' ').replace('\n', ' ').replace('\t', ' ')
    clean = clean.replace('…', '.')
    clean = re.sub(r'\.{2,}', '.', clean)
    clean = re.sub(r'([!?]){2,}', r'\1', clean)
    clean = re.sub(r'[ ]{2,}', ' ', clean)
    clean = clean.strip()
    if not re.search(r'[\w\d]', clean):
        return ""
    return clean

async def _generate_audio(text: str, output_path: str, voice: str = None, allow_voice_fallback: bool = False):
    clean_text = _normalize_tts_text(text)
    if not clean_text:
        logger.warning("      [!] Văn bản cần sinh audio rỗng, bỏ qua.")
        return

    import edge_tts
    max_retries = 5  # Tăng số lần thử lại
    proxy = os.environ.get('EDGE_TTS_PROXY') # Hỗ trợ xoay proxy nếu người dùng thiết lập biến môi trường này
    primary_voice = voice or os.environ.get('EDGE_TTS_VOICE') or "vi-VN-HoaiMyNeural"
    fallback_voice = os.environ.get('EDGE_TTS_FALLBACK_VOICE') or (
        "vi-VN-NamMinhNeural" if primary_voice == "vi-VN-HoaiMyNeural" else "vi-VN-HoaiMyNeural"
    )
    current_voice = primary_voice

    for attempt in range(max_retries):
        try:
            if proxy:
                communicate = edge_tts.Communicate(clean_text, current_voice, proxy=proxy)
            else:
                communicate = edge_tts.Communicate(clean_text, current_voice)
            await communicate.save(output_path)
            return
        except Exception as e:
            raw_err = str(e)
            masked_err = _mask_credentials(raw_err)
            err_lower = raw_err.lower()
            is_403 = "403" in err_lower or "invalid response status" in err_lower
            is_no_audio = "no audio was received" in err_lower

            if attempt == max_retries - 1 or (is_403 and not proxy):
                if is_403:
                    logger.error("      [!] Lỗi 403 Forbidden từ Edge-TTS WebSocket. Token Sec-MS-GEC có thể đã hết hạn. Hãy chạy: pip install --upgrade edge-tts>=7.3.1 hoặc thiết lập EDGE_TTS_PROXY.")
                logger.error(f"      [!] Sinh audio thất bại: {masked_err}")
                raise e

            if is_no_audio:
                if allow_voice_fallback:
                    previous_voice = current_voice
                    current_voice = fallback_voice if current_voice == primary_voice else primary_voice
                    logger.warning(f"      [!] Microsoft Edge-TTS tạm thời không trả về audio (rate limit hoặc nghẽn giọng {previous_voice}). Chuyển sang giọng '{current_voice}' và thử lại...")
                else:
                    logger.warning(f"      [!] Microsoft Edge-TTS tạm thời không trả về audio cho giọng '{current_voice}'. Đang giữ nguyên giọng để đảm bảo nhất quán nhân vật và thử lại...")
                wait_time = (2 ** attempt) + random.uniform(2.0, 4.0)
            else:
                wait_time = (2 ** attempt) + random.uniform(1.0, 3.0)

            logger.warning(f"      [!] Lỗi sinh audio (lần {attempt + 1}): {masked_err}. Thử lại sau {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)

def get_audio_duration(file_path: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Lỗi lấy duration audio: {e}")
        return 10.0 # Mặc định fallback

def _generate_silence_audio(output_path: str, duration: float = 1.0) -> bool:
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(duration), "-acodec", "libmp3lame", "-q:a", "9", output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            check=True
        )
        return True
    except Exception as e:
        logger.error(f"Lỗi tạo silence audio: {e}")
        return False

class VoiceSynthesizer:
    def __init__(self):
        pass

    def synthesize_single_scene(self, script_id: int, scene_number: int, text: str, voice: str = None, allow_voice_fallback: bool = False):
        if not isinstance(scene_number, int) or isinstance(scene_number, bool) or scene_number <= 0:
            raise ValueError(f"scene_number không hợp lệ: {scene_number}")
        if not text or not str(text).strip():
            raise ValueError(f"Văn bản thu âm cho Scene {scene_number} không được để trống hoặc thiếu từ ngữ phát âm.")

        clean_text = _normalize_tts_text(text)
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        os.makedirs(project_dir, exist_ok=True)

        audio_name = f"voice_{scene_number}.mp3"
        audio_path = os.path.join(project_dir, audio_name)

        if not clean_text:
            logger.info(f"  -> Scene {scene_number} chỉ có dấu câu/ngắt nghỉ ({text!r}), sinh audio im lặng...")
            if not _generate_silence_audio(audio_path, duration=1.0):
                raise RuntimeError(f"Không thể tạo audio im lặng cho Scene {scene_number}")
        else:
            logger.info(f"  -> Đang thu âm Scene {scene_number}: {clean_text[:40]}...")
            try:
                asyncio.run(_generate_audio(clean_text, audio_path, voice=voice, allow_voice_fallback=allow_voice_fallback))
            except Exception as e:
                if os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except OSError:
                        pass
                masked_err = _mask_credentials(str(e))
                logger.error(f"  [!] Lỗi thu âm Scene {scene_number}: {masked_err}")
                raise RuntimeError(f"Lỗi thu âm Scene {scene_number}: {masked_err}") from None

        if not (os.path.isfile(audio_path) and os.path.getsize(audio_path) > 0):
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass
            raise RuntimeError(f"Không tạo được file âm thanh cho Scene {scene_number} tại {audio_path}")

        actual_duration = get_audio_duration(audio_path)

        # Thử cập nhật vào bảng assets nếu có
        self._update_asset_duration(script_id, scene_number, actual_duration, audio_name)
        return f"/data/projects/{script_id}/{audio_name}"

    def synthesize_voiceover(self, script_id: int, voice: str = None, allow_voice_fallback: bool = False, force: bool = False):
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM voiceovers WHERE script_id = ?", (script_id,))
            vo_row = cursor.fetchone()
            cursor.execute("SELECT content FROM assets WHERE script_id = ?", (script_id,))
            asset_row = cursor.fetchone()
        finally:
            conn.close()

        if not vo_row or not vo_row[0]:
            logger.info("=> Kịch bản này chưa hoàn thiện Phase 3 (Voiceover).")
            return False

        try:
            vo_data = json.loads(vo_row[0])
        except Exception as e:
            logger.warning(f"=> Dữ liệu voiceover trong DB không hợp lệ: {e}")
            return False

        if not isinstance(vo_data, dict):
            logger.info("=> Dữ liệu voiceover không phải định dạng object hợp lệ.")
            return False

        target_voice = voice or os.environ.get('EDGE_TTS_VOICE') or "vi-VN-HoaiMyNeural"
        saved_voice = None
        if asset_row is not None and asset_row[0]:
            try:
                ad = json.loads(asset_row[0])
                if isinstance(ad, dict):
                    saved_voice = ad.get('voice')
            except Exception:
                saved_voice = None

        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        os.makedirs(project_dir, exist_ok=True)

        if saved_voice and saved_voice != target_voice:
            force = True
            logger.info(f"[Synthesizer] Phát hiện đổi giọng từ '{saved_voice}' sang '{target_voice}'. Tự động thu âm lại toàn bộ.")
        elif saved_voice is None and target_voice != "vi-VN-HoaiMyNeural":
            existing_audio_files = [
                f for f in os.listdir(project_dir) if f.startswith("voice_") and f.endswith(".mp3")
            ] if os.path.isdir(project_dir) else []
            if existing_audio_files:
                force = True
                logger.info(f"[Synthesizer] Dự án cũ có audio trên đĩa và yêu cầu giọng '{target_voice}'. Bật force để thu âm lại.")

        vo_scenes = vo_data.get('voiceover_scenes')
        if not isinstance(vo_scenes, list):
            logger.info("=> Kịch bản không có danh sách voiceover_scenes hợp lệ.")
            return False

        logger.info("\n[Synthesizer] Bắt đầu gọi Edge-TTS sinh âm thanh lồng tiếng...")
        paths = []
        updates = []
        valid_scenes_count = 0
        for vo_sc in vo_scenes:
            if not isinstance(vo_sc, dict):
                continue
            s_num = vo_sc.get('scene_number')
            if not isinstance(s_num, int) or isinstance(s_num, bool) or s_num <= 0:
                logger.warning(f"  -> Bỏ qua Scene có scene_number không hợp lệ: {s_num}")
                continue

            valid_scenes_count += 1
            raw_text = vo_sc.get('spoken_text')
            clean_norm_text = _normalize_tts_text(raw_text)
            audio_name = f"voice_{s_num}.mp3"
            audio_path = os.path.join(project_dir, audio_name)

            if not clean_norm_text:
                logger.info(f"  -> Scene {s_num}: lời thoại rỗng hoặc chỉ có dấu câu ({raw_text!r}), đang sinh audio im lặng...")
                if force or not (os.path.exists(audio_path) and os.path.getsize(audio_path) > 0):
                    _generate_silence_audio(audio_path, duration=1.0)
            else:
                text = clean_norm_text
                logger.info(f"  -> Đang thu âm Scene {s_num}: {text[:40]}...")
                if force or not (os.path.exists(audio_path) and os.path.getsize(audio_path) > 0):
                    try:
                        asyncio.run(_generate_audio(text, audio_path, voice=target_voice, allow_voice_fallback=allow_voice_fallback))
                        time.sleep(random.uniform(2.0, 4.0)) # Nghỉ ngẫu nhiên 2-4 giây để tránh bị block WebSocket do rate limit
                    except Exception as err:
                        logger.error(f"  [!] Lỗi sinh audio Scene {s_num}: {_mask_credentials(str(err))}")
                        if os.path.exists(audio_path):
                            try:
                                os.remove(audio_path)
                            except OSError:
                                pass

            if os.path.isfile(audio_path) and os.path.getsize(audio_path) > 0:
                actual_duration = get_audio_duration(audio_path)
                updates.append({
                    "scene_number": s_num,
                    "duration_seconds": actual_duration,
                    "audio_name": audio_name
                })
                paths.append(f"/data/projects/{script_id}/{audio_name}")
            else:
                if os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except OSError:
                        pass
                logger.warning(f"  [!] Không tìm thấy file audio đã sinh cho Scene {s_num}: {audio_path}")

        if valid_scenes_count > 0 and len(paths) < valid_scenes_count:
            logger.error(f"[Synthesizer] Chỉ thu âm thành công {len(paths)}/{valid_scenes_count} scenes. Trả về thất bại để tránh cập nhật is_synthesized = 1.")
            return False

        if updates:
            self._batch_update_asset_durations(script_id, updates, voice=target_voice)

        logger.info("[Synthesizer] Hoàn tất! Đã lưu audio và đồng bộ thời lượng.")
        return paths
        
    def _update_asset_duration(self, script_id: int, scene_number: int, duration: float, audio_name: str, voice: str = None):
        self._batch_update_asset_durations(script_id, [{
            "scene_number": scene_number,
            "duration_seconds": duration,
            "audio_name": audio_name
        }], voice=voice)

    def _batch_update_asset_durations(self, script_id: int, updates: list, voice: str = None):
        if not updates:
            return
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM assets WHERE script_id = ?", (script_id,))
            asset_row = cursor.fetchone()

            asset_data = {}
            if asset_row is not None and asset_row[0]:
                try:
                    parsed = json.loads(asset_row[0])
                    if isinstance(parsed, dict):
                        asset_data = parsed
                except Exception:
                    asset_data = {}
            asset_data.setdefault('script_id', script_id)
            if voice:
                asset_data['voice'] = voice

            existing_assets = asset_data.get('assets')
            if not isinstance(existing_assets, list):
                existing_assets = []
                asset_data['assets'] = existing_assets

            existing_map = {}
            for a_sc in existing_assets:
                if isinstance(a_sc, dict) and isinstance(a_sc.get('scene_number'), int):
                    existing_map[a_sc['scene_number']] = a_sc

            for up in updates:
                s_num = up['scene_number']
                audio_rel = f"data/projects/{script_id}/{up['audio_name']}"
                if s_num in existing_map:
                    existing_map[s_num]['duration_seconds'] = up['duration_seconds']
                    existing_map[s_num]['audio_path'] = audio_rel
                else:
                    new_item = {
                        "scene_number": s_num,
                        "duration_seconds": up['duration_seconds'],
                        "audio_path": audio_rel
                    }
                    existing_assets.append(new_item)
                    existing_map[s_num] = new_item

            if asset_row is not None:
                cursor.execute("UPDATE assets SET content = ? WHERE script_id = ?", (json.dumps(asset_data), script_id))
            else:
                cursor.execute("INSERT INTO assets (script_id, content) VALUES (?, ?)", (script_id, json.dumps(asset_data)))
            conn.commit()
        finally:
            conn.close()
