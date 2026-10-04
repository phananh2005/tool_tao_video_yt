import os
import sqlite3
import json
import subprocess
import asyncio
from core.database import DB_PATH

async def _generate_audio(text: str, output_path: str, voice: str = "vi-VN-HoaiMyNeural"):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def get_audio_duration(file_path: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Lỗi lấy duration audio: {e}")
        return 10.0 # Mặc định fallback

class VoiceSynthesizer:
    def __init__(self):
        pass

    def synthesize_voiceover(self, script_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Lấy dữ liệu Voiceover và Asset hiện tại
        cursor.execute("SELECT content FROM voiceovers WHERE script_id = ?", (script_id,))
        vo_row = cursor.fetchone()
        
        cursor.execute("SELECT content FROM assets WHERE script_id = ?", (script_id,))
        asset_row = cursor.fetchone()
        
        conn.close()
        
        if not vo_row or not asset_row:
            print("=> Kịch bản này chưa hoàn thiện Phase 3 (Voiceover) hoặc Phase 4 (Ảnh).")
            return False
            
        vo_data = json.loads(vo_row[0])
        asset_data = json.loads(asset_row[0])
        
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        os.makedirs(project_dir, exist_ok=True)
        
        print("\n[Synthesizer] Bắt đầu gọi Edge-TTS sinh âm thanh lồng tiếng...")
        
        updated_assets = []
        
        for vo_sc in vo_data.get('voiceover_scenes', []):
            s_num = vo_sc['scene_number']
            text = vo_sc['spoken_text']
            
            audio_name = f"voice_{s_num}.mp3"
            audio_path = os.path.join(project_dir, audio_name)
            
            print(f"  -> Đang thu âm Scene {s_num}: {text[:40]}...")
            
            # Nếu chưa có file mp3 thì sinh mới
            if not (os.path.exists(audio_path) and os.path.getsize(audio_path) > 0):
                asyncio.run(_generate_audio(text, audio_path))
                
            # Đo lại thời gian thực tế của audio
            actual_duration = get_audio_duration(audio_path)
            
            # Cập nhật thời gian vào Asset của scene tương ứng
            for a_sc in asset_data.get('assets', []):
                if a_sc['scene_number'] == s_num:
                    a_sc['duration_seconds'] = actual_duration # Bơm biến thời gian mới vào
                    a_sc['audio_path'] = f"data/projects/{script_id}/{audio_name}"
                    updated_assets.append(a_sc)
                    break
                    
        # Lưu đè lại bảng Assets với thời lượng chính xác tuyệt đối
        asset_data['assets'] = updated_assets
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE assets SET content = ? WHERE script_id = ?", (json.dumps(asset_data), script_id))
        conn.commit()
        conn.close()
        
        print("[Synthesizer] Hoàn tất! Đã đồng bộ thời lượng Ảnh khớp với Tiếng.")
        return True
