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
    conn.commit()
    conn.close()
