from core.logger import get_logger
logger = get_logger(__name__)
import sqlite3
import json

conn = sqlite3.connect('data/tubechain.db')
cursor = conn.cursor()
cursor.execute("SELECT content FROM assets WHERE script_id = 2")
row = cursor.fetchone()
if row:
    data = json.loads(row[0])
    logger.info(json.dumps(data, indent=2, ensure_ascii=False))
else:
    logger.info("No assets found for script 2")
