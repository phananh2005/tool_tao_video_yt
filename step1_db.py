import sqlite3
import os

DB_PATH = os.path.join('data', 'tubechain.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE ideas ADD COLUMN series_id TEXT")
    print("Added series_id to ideas table.")
except sqlite3.OperationalError as e:
    print(f"Error (maybe already exists): {e}")

conn.commit()
conn.close()

# Update core/contracts.py
with open('core/contracts.py', 'r', encoding='utf-8') as f:
    contracts = f.read()

if 'series_id: Optional[str] = None' not in contracts:
    contracts = contracts.replace('summary: str', 'summary: str\n    series_id: Optional[str] = None')
    with open('core/contracts.py', 'w', encoding='utf-8') as f:
        f.write(contracts)
    print("Updated core/contracts.py")

# Update core/database.py to handle series_id in save_idea
with open('core/database.py', 'r', encoding='utf-8') as f:
    db_code = f.read()

old_insert = """cursor.execute('''INSERT INTO ideas 
        (project_id, title, topics, rabbit_hole_series, part_number, summary, similarity_score, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
        (project_id, idea.title, topics_str, idea.rabbit_hole_series, idea.part_number, idea.summary, similarity_score, status))"""

new_insert = """cursor.execute('''INSERT INTO ideas 
        (project_id, title, topics, rabbit_hole_series, part_number, summary, similarity_score, status, series_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        (project_id, idea.title, topics_str, idea.rabbit_hole_series, idea.part_number, idea.summary, similarity_score, status, idea.series_id))"""

if 'series_id' not in old_insert and old_insert in db_code:
    db_code = db_code.replace(old_insert, new_insert)
    with open('core/database.py', 'w', encoding='utf-8') as f:
        f.write(db_code)
    print("Updated save_idea in core/database.py")
elif new_insert in db_code:
    pass
else:
    # Manual replace
    db_code = db_code.replace("similarity_score, status)", "similarity_score, status, series_id)")
    db_code = db_code.replace("VALUES (?, ?, ?, ?, ?, ?, ?, ?)", "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
    db_code = db_code.replace("idea.summary, similarity_score, status))", "idea.summary, similarity_score, status, idea.series_id))")
    with open('core/database.py', 'w', encoding='utf-8') as f:
        f.write(db_code)
    print("Manually updated save_idea in core/database.py")

