import sqlite3
import json
import os

conn = sqlite3.connect('data/tubechain.db')
cursor = conn.cursor()
cursor.execute("SELECT content FROM assets WHERE script_id = 2")
row = cursor.fetchone()

if row:
    asset_data = json.loads(row[0])
    for a_sc in asset_data.get('assets', []):
        s_num = a_sc['scene_number']
        audio_name = f"voice_{s_num}.mp3"
        audio_path = f"data/projects/2/{audio_name}"
        a_sc['duration_seconds'] = 10.0 # dummy
        a_sc['audio_path'] = audio_path
        
    cursor.execute("UPDATE assets SET content = ? WHERE script_id = 2", (json.dumps(asset_data),))
    conn.commit()
    print("Fixed assets for script 2.")
conn.close()
