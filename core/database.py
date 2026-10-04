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
    conn.commit()
    conn.close()
