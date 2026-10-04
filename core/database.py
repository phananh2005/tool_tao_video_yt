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
    conn.commit()
    conn.close()
    return project_id

def get_project_ideas(project_id: int) -> list[IdeaJSON]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, topics, rabbit_hole_series, part_number, summary FROM ideas WHERE project_id = ? AND status != 'dropped'", (project_id,))
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
        (project_id, title, topics, rabbit_hole_series, part_number, summary, similarity_score, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
        (project_id, idea.title, topics_str, idea.rabbit_hole_series, idea.part_number, idea.summary, similarity_score, status))
    
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
    conn.commit()
    conn.close()
