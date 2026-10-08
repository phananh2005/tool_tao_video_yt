from core.logger import get_logger
logger = get_logger(__name__)
import os
import sqlite3
import json
import subprocess
import asyncio
import time
import random
from core.database import DB_PATH

async def _generate_audio(text: str, output_path: str, voice: str = "vi-VN-HoaiMyNeural"):
    import edge_tts
    max_retries = 5  # Tăng số lần thử lại
    proxy = os.environ.get('EDGE_TTS_PROXY') # Hỗ trợ xoay proxy nếu người dùng thiết lập biến môi trường này
    
    for attempt in range(max_retries):
        try:
            if proxy:
                communicate = edge_tts.Communicate(text, voice, proxy=proxy)
            else:
                communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"      [!] Đã thử {max_retries} lần nhưng vẫn thất bại: {e}")
                raise e
            
            # Thời gian chờ tăng dần (Exponential backoff) kết hợp nhiễu ngẫu nhiên (Jitter)
            wait_time = (2 ** attempt) + random.uniform(1.0, 3.0)
            logger.warning(f"      [!] Lỗi sinh audio (lần {attempt + 1}): {e}. Thử lại sau {wait_time:.1f}s...")
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

class VoiceSynthesizer:
    def __init__(self):
        pass

    def synthesize_single_scene(self, script_id: int, scene_number: int, text: str):
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        os.makedirs(project_dir, exist_ok=True)
        
        audio_name = f"voice_{scene_number}.mp3"
        audio_path = os.path.join(project_dir, audio_name)
        
        logger.info(f"  -> Đang thu âm Scene {scene_number}: {text[:40]}...")
        asyncio.run(_generate_audio(text, audio_path))
        actual_duration = get_audio_duration(audio_path)
        
        # Thử cập nhật vào bảng assets nếu có
        self._update_asset_duration(script_id, scene_number, actual_duration, audio_name)
        return f"/data/projects/{script_id}/{audio_name}"

    def synthesize_voiceover(self, script_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT content FROM voiceovers WHERE script_id = ?", (script_id,))
        vo_row = cursor.fetchone()
        conn.close()
        
        if not vo_row:
            logger.info("=> Kịch bản này chưa hoàn thiện Phase 3 (Voiceover).")
            return False
            
        vo_data = json.loads(vo_row[0])
        
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        os.makedirs(project_dir, exist_ok=True)
        
        logger.info("\n[Synthesizer] Bắt đầu gọi Edge-TTS sinh âm thanh lồng tiếng...")
        paths = []
        for vo_sc in vo_data.get('voiceover_scenes', []):
            s_num = vo_sc['scene_number']
            text = vo_sc['spoken_text']
            
            audio_name = f"voice_{s_num}.mp3"
            audio_path = os.path.join(project_dir, audio_name)
            
            logger.info(f"  -> Đang thu âm Scene {s_num}: {text[:40]}...")
            if not (os.path.exists(audio_path) and os.path.getsize(audio_path) > 0):
                asyncio.run(_generate_audio(text, audio_path))
                time.sleep(random.uniform(2.0, 4.0)) # Nghỉ ngẫu nhiên 2-4 giây để tránh bị block WebSocket do rate limit
                
            actual_duration = get_audio_duration(audio_path)
            self._update_asset_duration(script_id, s_num, actual_duration, audio_name)
            paths.append(f"/data/projects/{script_id}/{audio_name}")
            
        logger.info("[Synthesizer] Hoàn tất! Đã lưu audio và đồng bộ thời lượng.")
        return paths
        
    def _update_asset_duration(self, script_id: int, scene_number: int, duration: float, audio_name: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM assets WHERE script_id = ?", (script_id,))
        asset_row = cursor.fetchone()
        
        if asset_row:
            asset_data = json.loads(asset_row[0])
            found = False
            for a_sc in asset_data.get('assets', []):
                if a_sc.get('scene_number') == scene_number:
                    a_sc['duration_seconds'] = duration
                    a_sc['audio_path'] = f"data/projects/{script_id}/{audio_name}"
                    found = True
                    break
            if not found:
                asset_data.setdefault('assets', []).append({
                    "scene_number": scene_number,
                    "duration_seconds": duration,
                    "audio_path": f"data/projects/{script_id}/{audio_name}"
                })
            cursor.execute("UPDATE assets SET content = ? WHERE script_id = ?", (json.dumps(asset_data), script_id))
        else:
            new_assets = {
                "script_id": script_id,
                "assets": [
                    {
                        "scene_number": scene_number,
                        "duration_seconds": duration,
                        "audio_path": f"data/projects/{script_id}/{audio_name}"
                    }
                ]
            }
            cursor.execute("INSERT INTO assets (script_id, content) VALUES (?, ?)", (script_id, json.dumps(new_assets)))
        
        conn.commit()
        conn.close()
