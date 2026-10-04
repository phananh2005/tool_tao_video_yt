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
