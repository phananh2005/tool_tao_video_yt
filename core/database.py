import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tubechain.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS ideas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        title TEXT NOT NULL,
        topics TEXT NOT NULL,
        rabbit_hole_series BOOLEAN,
        part_number INTEGER,
        summary TEXT,
        similarity_score REAL,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )''')
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS scripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idea_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(idea_id) REFERENCES ideas(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS voiceovers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS seo_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
import json
import sqlite3
import os
from core.contracts import IdeaJSON

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tubechain.db')

def get_or_create_project(name: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM projects WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        project_id = row[0]
    else:
        cursor.execute("INSERT INTO projects (name) VALUES (?)", (name,))
        project_id = cursor.lastrowid
        
    cursor.execute("""CREATE TABLE IF NOT EXISTS scripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idea_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(idea_id) REFERENCES ideas(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS voiceovers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS seo_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    conn.commit()
    conn.close()
    return project_id

def get_project_ideas(project_id: int) -> list[IdeaJSON]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, topics, rabbit_hole_series, part_number, summary FROM ideas WHERE project_id = ?", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    ideas = []
    for row in rows:
        topics = json.loads(row[1]) if row[1] else []
        ideas.append(IdeaJSON(title=row[0], topics=topics, rabbit_hole_series=bool(row[2]), part_number=row[3], summary=row[4]))
    return ideas

def save_idea(project_id: int, idea: IdeaJSON, similarity_score: float, status: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    topics_str = json.dumps(idea.topics)
    cursor.execute('''INSERT INTO ideas 
        (project_id, title, topics, rabbit_hole_series, part_number, summary, similarity_score, status, series_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        (project_id, idea.title, topics_str, idea.rabbit_hole_series, idea.part_number, idea.summary, similarity_score, status, idea.series_id))
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS scripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idea_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(idea_id) REFERENCES ideas(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS voiceovers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS seo_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    conn.commit()
    conn.close()

def get_ideas_without_script():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.title, i.status 
        FROM ideas i 
        LEFT JOIN scripts s ON i.id = s.idea_id 
        WHERE s.id IS NULL AND i.status IN ('pass', 'warn')
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'title': r[1], 'status': r[2]} for r in rows]

def get_idea_by_id(idea_id: int) -> IdeaJSON:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, topics, rabbit_hole_series, part_number, summary FROM ideas WHERE id = ?", (idea_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    topics = json.loads(row[1]) if row[1] else []
    return IdeaJSON(title=row[0], topics=topics, rabbit_hole_series=bool(row[2]), part_number=row[3], summary=row[4])

def save_script(idea_id: int, script_obj):
    import json
    scenes_dict = [sc.__dict__ for sc in script_obj.scenes]
    script_dict = {
        'idea_id': script_obj.idea_id,
        'estimated_total_duration': script_obj.estimated_total_duration,
        'scenes': scenes_dict
    }
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO scripts (idea_id, content) VALUES (?, ?)", (idea_id, json.dumps(script_dict)))
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS voiceovers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS seo_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    conn.commit()
    conn.close()

def get_scripts_without_voiceover():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, i.title, i.summary 
        FROM scripts s
        JOIN ideas i ON s.idea_id = i.id
        LEFT JOIN voiceovers v ON s.id = v.script_id 
        WHERE v.id IS NULL
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{'script_id': r[0], 'title': r[1], 'summary': r[2]} for r in rows]

def get_script_by_id(script_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM scripts WHERE id = ?", (script_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    
    script_dict = json.loads(row[0])
    # Tái tạo lại cấu trúc object (Dict)
    return script_dict

def save_voiceover(script_id: int, voiceover_obj):
    import json
    scenes_dict = [sc.__dict__ for sc in voiceover_obj.voiceover_scenes]
    vo_dict = {
        'script_id': voiceover_obj.script_id,
        'voiceover_scenes': scenes_dict
    }
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO voiceovers (script_id, content) VALUES (?, ?)", (script_id, json.dumps(vo_dict)))
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS seo_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    conn.commit()
    conn.close()

def get_scripts_without_assets():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, i.title 
        FROM scripts s
        JOIN ideas i ON s.idea_id = i.id
        LEFT JOIN assets a ON s.id = a.script_id 
        WHERE a.id IS NULL
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{'script_id': r[0], 'title': r[1]} for r in rows]

def save_asset(script_id: int, asset_obj):
    import json
    scenes_dict = [sc.__dict__ for sc in asset_obj.assets]
    asset_dict = {
        'script_id': asset_obj.script_id,
        'assets': scenes_dict
    }
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO assets (script_id, content) VALUES (?, ?)", (script_id, json.dumps(asset_dict)))
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS seo_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_id INTEGER UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(script_id) REFERENCES scripts(id)
    )""")
    conn.commit()
    conn.close()

def get_ready_to_render_projects():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Lấy những kịch bản đã có dữ liệu Asset (hình ảnh)
    cursor.execute("""
        SELECT s.id, i.title, s.content, a.content
        FROM scripts s
        JOIN ideas i ON s.idea_id = i.id
        JOIN assets a ON s.id = a.script_id
    """)
    rows = cursor.fetchall()
    conn.close()
    
    projects = []
    for r in rows:
        script_id = r[0]
        title = r[1]
        
        try:
            script_data = json.loads(r[2])
            asset_data = json.loads(r[3])
            
            # Gộp dữ liệu: map scene_number -> duration (từ script) và image_path (từ asset)
            timeline = []
            
            # Tạo dictionary tra cứu nhanh thời lượng từ Script
            durations = {}
            for sc in script_data.get('scenes', []):
                durations[sc['scene_number']] = sc['duration_seconds']
                
            # Duyệt qua các Asset để ráp thành timeline
            for a_sc in asset_data.get('assets', []):
                s_num = a_sc['scene_number']
                if s_num in durations:
                    timeline.append({
                        'scene_number': s_num,
                        'duration': durations[s_num],
                        'image_path': a_sc['image_path']
                    })
            
            # Sắp xếp lại cho đúng thứ tự từ đầu đến cuối
            timeline.sort(key=lambda x: x['scene_number'])
            
            projects.append({
                'script_id': script_id,
                'title': title,
                'timeline': timeline
            })
        except Exception as e:
            print(f"Lỗi parse dữ liệu cho script {script_id}: {e}")
            
    return projects

def get_ready_to_render_projects_with_audio():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.id, i.title, a.content
        FROM scripts s
        JOIN ideas i ON s.idea_id = i.id
        JOIN assets a ON s.id = a.script_id
    """)
    rows = cursor.fetchall()
    conn.close()
    
    projects = []
    for r in rows:
        script_id = r[0]
        title = r[1]
        
        try:
            asset_data = json.loads(r[2])
            timeline = []
            
            for a_sc in asset_data.get('assets', []):
                # Chỉ đưa vào render những phân cảnh có audio
                if 'audio_path' in a_sc:
                    timeline.append({
                        'scene_number': a_sc['scene_number'],
                        'duration': a_sc.get('duration_seconds', 10),
                        'image_path': a_sc['image_path'],
                        'audio_path': a_sc['audio_path']
                    })
            
            if timeline:
                timeline.sort(key=lambda x: x['scene_number'])
                projects.append({
                    'script_id': script_id,
                    'title': title,
                    'timeline': timeline
                })
        except Exception as e:
            print(f"Lỗi: {e}")
            
    return projects

def get_rendered_projects_without_seo():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, i.title, s.content, a.content
        FROM scripts s
        JOIN ideas i ON s.idea_id = i.id
        JOIN assets a ON s.id = a.script_id
        LEFT JOIN seo_metadata seo ON s.id = seo.script_id 
        WHERE seo.id IS NULL
    """)
    rows = cursor.fetchall()
    conn.close()
    
    projects = []
    for r in rows:
        try:
            projects.append({
                'script_id': r[0],
                'title': r[1],
                'script_dict': json.loads(r[2]),
                'asset_dict': json.loads(r[3])
            })
        except:
            pass
    return projects

def save_seo_metadata(script_id: int, seo_dict: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO seo_metadata (script_id, content) VALUES (?, ?)", (script_id, json.dumps(seo_dict)))
    conn.commit()
    conn.close()


def delete_project_media(project_id: int):
    import shutil
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tìm các script thuộc project này
    cursor.execute("SELECT s.id FROM scripts s JOIN ideas i ON s.idea_id = i.id WHERE i.project_id = ?", (project_id,))
    script_ids = [row[0] for row in cursor.fetchall()]
    
    # Xóa folder vật lý chứa Media (ảnh, video)
    for sid in script_ids:
        proj_dir = os.path.join(os.path.dirname(DB_PATH), '..', 'data', 'projects', str(sid))
        if os.path.exists(proj_dir):
            shutil.rmtree(proj_dir)
            
    # KHÔNG xóa dữ liệu trong DB để Phase 1 Idea Engine còn dùng chống trùng lặp.
    conn.close()
