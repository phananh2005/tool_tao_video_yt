import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.database import init_db
import sqlite3
from core.database import DB_PATH
from modules.voiceover.synthesizer import VoiceSynthesizer

def get_ready_projects():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, i.title 
        FROM scripts s
        JOIN ideas i ON s.idea_id = i.id
        JOIN voiceovers v ON s.id = v.script_id
        JOIN assets a ON s.id = a.script_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{'script_id': r[0], 'title': r[1]} for r in rows]

def main():
    init_db()
    
    projects = get_ready_projects()
    if not projects:
        print("\n=> Không có Dự án nào đủ điều kiện lồng tiếng (Cần có Voiceover và Ảnh).")
        return
        
    print("\n=== DANH SÁCH DỰ ÁN SẴN SÀNG LỒNG TIẾNG AI (EDGE-TTS) ===")
    for p in projects:
        print(f"[{p['script_id']}] - Tên: {p['title']}")
        
    choice = input("\nNhập số ID của Dự án muốn lồng tiếng: ").strip()
    if not choice.isdigit():
        return
        
    script_id = int(choice)
    engine = VoiceSynthesizer()
    engine.synthesize_voiceover(script_id)

if __name__ == '__main__':
    main()
