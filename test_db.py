import sqlite3
conn = sqlite3.connect('data/tubechain.db')
c = conn.cursor()
c.execute("SELECT is_synthesized FROM voiceovers WHERE script_id = 2")
print("is_synthesized:", c.fetchone())
