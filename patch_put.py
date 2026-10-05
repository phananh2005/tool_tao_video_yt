import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

new_put = """@app.put("/api/assets/{script_id}")
def update_assets(script_id: int, req: UpdateAssetRequest):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM assets WHERE script_id = ?", (script_id,))
    row = cursor.fetchone()
    if row:
        existing_data = json.loads(row[0])
        # Merge audio info from existing to req.content
        for existing_sc in existing_data.get('assets', []):
            for new_sc in req.content.get('assets', []):
                if new_sc.get('scene_number') == existing_sc.get('scene_number'):
                    if 'duration_seconds' in existing_sc:
                        new_sc['duration_seconds'] = existing_sc['duration_seconds']
                    if 'audio_path' in existing_sc:
                        new_sc['audio_path'] = existing_sc['audio_path']
        cursor.execute("UPDATE assets SET content = ? WHERE script_id = ?", (json.dumps(req.content), script_id))
    else:
        cursor.execute("INSERT INTO assets (script_id, content) VALUES (?, ?)", (script_id, json.dumps(req.content)))
    conn.commit()
    conn.close()
    return {"status": "success"}"""

content = re.sub(r'@app\.put\("/api/assets/\{script_id\}"\).*?return \{"status": "success"\}', new_put, content, flags=re.DOTALL)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
