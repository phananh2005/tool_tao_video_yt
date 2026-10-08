from core.logger import get_logger
logger = get_logger(__name__)
import os
import json
import sqlite3
import shutil
import math
import sys
from typing import List, Optional
from core.contracts import IdeaJSON

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tubechain.db')


def migrate_db(conn: Optional[sqlite3.Connection] = None):
    """Migration script: thêm cột is_synthesized vào bảng voiceovers nếu chưa tồn tại."""
    should_close = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        should_close = True

    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(voiceovers)")
    columns = [col[1] for col in cursor.fetchall()]
    if columns and "is_synthesized" not in columns:
        cursor.execute("ALTER TABLE voiceovers ADD COLUMN is_synthesized BOOLEAN DEFAULT 0")
        conn.commit()

    if should_close:
        conn.close()


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
        series_id TEXT,
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
        is_synthesized BOOLEAN DEFAULT 0,
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

    migrate_db(conn)

    conn.commit()
    conn.close()


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


def get_project_ideas(project_id: int) -> List[IdeaJSON]:
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


def get_idea_by_id(idea_id: int) -> Optional[IdeaJSON]:
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
    scenes_dict = [sc.__dict__ for sc in script_obj.scenes]
    script_dict = {
        'idea_id': script_obj.idea_id,
        'estimated_total_duration': script_obj.estimated_total_duration,
        'scenes': scenes_dict
    }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM scripts WHERE idea_id = ?", (idea_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE scripts SET content = ? WHERE idea_id = ?", (json.dumps(script_dict), idea_id))
    else:
        cursor.execute("INSERT INTO scripts (idea_id, content) VALUES (?, ?)", (idea_id, json.dumps(script_dict)))
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
    return json.loads(row[0])


def save_voiceover(script_id: int, voiceover_obj, is_synthesized: bool = False):
    scenes_dict = [sc.__dict__ for sc in voiceover_obj.voiceover_scenes]
    vo_dict = {
        'script_id': voiceover_obj.script_id,
        'voiceover_scenes': scenes_dict
    }
    synth_val = getattr(voiceover_obj, 'is_synthesized', is_synthesized)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM voiceovers WHERE script_id = ?", (script_id,))
    if cursor.fetchone():
        cursor.execute(
            "UPDATE voiceovers SET content = ?, is_synthesized = ? WHERE script_id = ?",
            (json.dumps(vo_dict), 1 if synth_val else 0, script_id)
        )
    else:
        cursor.execute(
            "INSERT INTO voiceovers (script_id, content, is_synthesized) VALUES (?, ?, ?)",
            (script_id, json.dumps(vo_dict), 1 if synth_val else 0)
        )
    conn.commit()
    conn.close()


def set_voiceover_synthesized(script_id: int, is_synthesized: bool = True):
    """Cập nhật cờ is_synthesized cho voiceover của script_id (Phase 3.5)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE voiceovers SET is_synthesized = ? WHERE script_id = ?", (1 if is_synthesized else 0, script_id))
    conn.commit()
    conn.close()


def is_voiceover_synthesized(script_id: int) -> bool:
    """Kiểm tra kịch bản script_id đã tổng hợp âm thanh (Phase 3.5) xong chưa."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT is_synthesized FROM voiceovers WHERE script_id = ?", (script_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row and row[0] is not None else False


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
    scenes_dict = [sc.__dict__ for sc in asset_obj.assets]
    asset_dict = {
        'script_id': asset_obj.script_id,
        'assets': scenes_dict
    }
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT content FROM assets WHERE script_id = ?", (script_id,))
    row = cursor.fetchone()

    if row:
        existing_data = json.loads(row[0])
        for existing_sc in existing_data.get('assets', []):
            for new_sc in asset_dict['assets']:
                if new_sc.get('scene_number') == existing_sc.get('scene_number'):
                    if 'duration_seconds' in existing_sc:
                        new_sc['duration_seconds'] = existing_sc['duration_seconds']
                    if 'audio_path' in existing_sc:
                        new_sc['audio_path'] = existing_sc['audio_path']
        cursor.execute("UPDATE assets SET content = ? WHERE script_id = ?", (json.dumps(asset_dict), script_id))
    else:
        cursor.execute("INSERT INTO assets (script_id, content) VALUES (?, ?)", (script_id, json.dumps(asset_dict)))

    conn.commit()
    conn.close()


def get_ready_to_render_projects():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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

            timeline = []
            durations = {}
            for sc in script_data.get('scenes', []):
                durations[sc['scene_number']] = sc['duration_seconds']

            for a_sc in asset_data.get('assets', []):
                s_num = a_sc['scene_number']
                if s_num in durations:
                    timeline.append({
                        'scene_number': s_num,
                        'duration': durations[s_num],
                        'image_path': a_sc['image_path']
                    })

            timeline.sort(key=lambda x: x['scene_number'])
            projects.append({
                'script_id': script_id,
                'title': title,
                'timeline': timeline
            })
        except Exception as e:
            logger.error(f"Lỗi parse dữ liệu cho script {script_id}: {e}")

    return projects


def get_ready_to_render_projects_with_audio():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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
            if not isinstance(script_data, dict) or not isinstance(asset_data, dict):
                continue
            expected_scenes = []
            valid_scene_numbers = True
            for scene in script_data.get('scenes', []):
                scene_number = scene.get('scene_number') if isinstance(scene, dict) else None
                if not isinstance(scene_number, int) or isinstance(scene_number, bool):
                    valid_scene_numbers = False
                    break
                expected_scenes.append(scene_number)
            if (
                not valid_scene_numbers
                or not expected_scenes
                or len(set(expected_scenes)) != len(expected_scenes)
            ):
                continue

            assets = asset_data.get('assets', [])
            if not isinstance(assets, list) or len(assets) != len(expected_scenes):
                continue

            asset_by_scene = {}
            valid_assets = True
            for asset in assets:
                if not isinstance(asset, dict):
                    valid_assets = False
                    break
                scene_number = asset.get('scene_number')
                if not isinstance(scene_number, int) or isinstance(scene_number, bool):
                    valid_assets = False
                    break
                if scene_number in asset_by_scene:
                    valid_assets = False
                    break
                asset_by_scene[scene_number] = asset

            if not valid_assets or set(asset_by_scene) != set(expected_scenes):
                continue

            timeline = []
            for scene_number in expected_scenes:
                asset = asset_by_scene[scene_number]
                image_path = asset.get('image_path')
                audio_path = asset.get('audio_path')
                duration = asset.get('duration_seconds', 10)
                if (
                    not isinstance(image_path, str) or not image_path.strip()
                    or not isinstance(audio_path, str) or not audio_path.strip()
                    or not isinstance(duration, (int, float)) or isinstance(duration, bool)
                    or (isinstance(duration, (int, float)) and duration > 86400)
                    or (isinstance(duration, int) and duration > sys.float_info.max)
                    or (isinstance(duration, float) and not math.isfinite(duration))
                    or duration <= 0
                ):
                    valid_assets = False
                    break
                project_dir = os.path.join(os.path.dirname(DB_PATH), 'projects', str(script_id))
                if any(
                    not os.path.isfile(os.path.join(project_dir, os.path.basename(path)))
                    or os.path.getsize(os.path.join(project_dir, os.path.basename(path))) <= 0
                    for path in (image_path, audio_path)
                ):
                    valid_assets = False
                    break
                timeline.append({
                    'scene_number': scene_number,
                    'duration': duration,
                    'image_path': image_path,
                    'audio_path': audio_path,
                })

            if valid_assets:
                timeline.sort(key=lambda x: x['scene_number'])
                projects.append({
                    'script_id': script_id,
                    'title': title,
                    'timeline': timeline
                })
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Lỗi parse render inputs cho script {script_id}: {e}")

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
        except Exception:
            pass
    return projects


def save_seo_metadata(script_id: int, seo_dict: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM seo_metadata WHERE script_id = ?", (script_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE seo_metadata SET content = ? WHERE script_id = ?", (json.dumps(seo_dict), script_id))
    else:
        cursor.execute("INSERT INTO seo_metadata (script_id, content) VALUES (?, ?)", (script_id, json.dumps(seo_dict)))
    conn.commit()
    conn.close()


def delete_project_media(project_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, i.id
        FROM scripts s
        JOIN ideas i ON s.idea_id = i.id
        JOIN seo_metadata seo ON s.id = seo.script_id
        WHERE i.project_id = ?
    """, (project_id,))
    completed_scripts = cursor.fetchall()

    for sid, iid in completed_scripts:
        proj_dir = os.path.join(os.path.dirname(DB_PATH), 'projects', str(sid))
        if os.path.exists(proj_dir):
            shutil.rmtree(proj_dir)

        cursor.execute("UPDATE ideas SET status = 'archived' WHERE id = ?", (iid,))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
