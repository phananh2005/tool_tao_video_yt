# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
import os

from core.database import (
    DB_PATH, init_db, get_or_create_project, get_project_ideas, save_idea,
    get_idea_by_id, save_script, get_script_by_id, save_voiceover, save_asset,
    save_seo_metadata, get_ready_to_render_projects_with_audio, delete_project_media
)
from core.contracts import ScriptJSON, SceneJSON, VoiceoverJSON, VoiceoverSceneJSON, AssetJSON, AssetSceneJSON

from modules.idea_engine.adapter import GeminiWebAdapter
from modules.idea_engine.engine import IdeaEngine
from modules.script_gen.engine import ScriptGeneratorEngine
from modules.voiceover.engine import VoiceoverEngine
from modules.voiceover.synthesizer import VoiceSynthesizer
from modules.scene_illustrator.engine import SceneIllustratorEngine
from modules.video_assembler.engine import VideoAssemblerEngine
from modules.seo_optimizer.engine import SEOOptimizerEngine

app = FastAPI(title="TubeChain Web UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

def get_conn():
    return sqlite3.connect(DB_PATH)

# --- MODELS ---
class ThemeRequest(BaseModel):
    theme: str
    is_rabbit_hole: bool = False

class UpdateScriptRequest(BaseModel):
    content: dict

class UpdateVoiceoverRequest(BaseModel):
    content: dict

class UpdateAssetRequest(BaseModel):
    content: dict

class UpdateSeoRequest(BaseModel):
    content: dict

# --- DASHBOARD ---
@app.get("/api/dashboard")
def get_dashboard():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, created_at FROM projects ORDER BY id DESC")
    projects = cursor.fetchall()
    
    cursor.execute("""
        SELECT i.project_id, COUNT(i.id) 
        FROM ideas i 
        LEFT JOIN scripts s ON i.id = s.idea_id 
        WHERE s.id IS NULL AND i.status NOT IN ('drop', 'rejected')
        GROUP BY i.project_id
    """)
    unused_counts = {r[0]: r[1] for r in cursor.fetchall()}
    
    cursor.execute("""
        SELECT 
            i.project_id, 
            s.id as script_id, 
            i.id as idea_id, 
            i.title, 
            i.rabbit_hole_series, 
            i.part_number, 
            i.series_id,
            (CASE WHEN seo.id IS NOT NULL THEN 6
                  WHEN a.id IS NOT NULL THEN 4
                  WHEN v.id IS NOT NULL THEN 3
                  ELSE 2 END) as phase
        FROM scripts s
        JOIN ideas i ON s.idea_id = i.id
        LEFT JOIN voiceovers v ON s.id = v.script_id
        LEFT JOIN assets a ON s.id = a.script_id
        LEFT JOIN seo_metadata seo ON s.id = seo.script_id
    """)
    active_scripts = cursor.fetchall()
    conn.close()
    
    result = []
    for p in projects:
        p_id = p[0]
        p_scripts = []
        for r in active_scripts:
            if r[0] == p_id:
                p_scripts.append({
                    "script_id": r[1],
                    "idea_id": r[2],
                    "title": r[3],
                    "rabbit_hole_series": bool(r[4]),
                    "part_number": r[5],
                    "series_id": r[6],
                    "phase": r[7]
                })
        p_scripts.sort(key=lambda x: (x['series_id'] or '', x['part_number'], x['script_id']))
        result.append({
            "id": p_id,
            "name": p[1],
            "created_at": p[2],
            "unused_ideas_count": unused_counts.get(p_id, 0),
            "active_scripts": p_scripts
        })
    return result


@app.delete("/api/projects/{project_id}/media")
def delete_project_media_api(project_id: int):
    try:
        delete_project_media(project_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- PHASE 1: IDEA FACTORY ---
@app.post("/api/phase1/brainstorm")
def brainstorm_ideas(req: ThemeRequest):
    project_id = get_or_create_project(req.theme)
    try:
        adapter = GeminiWebAdapter()
        engine = IdeaEngine(adapter)
        
        new_ideas = engine.generate_ideas(req.theme, count=5, is_rabbit_hole=req.is_rabbit_hole)
        history = get_project_ideas(project_id)
        
        results = []
        for idea in new_ideas:
            max_sim = max([engine.calculate_similarity(idea.topics, old.topics) for old in history] + [0.0])
            status = 'drop' if max_sim > 0.85 else ('warn' if max_sim >= 0.60 else 'pass')
            
            save_idea(project_id, idea, max_sim, status)
                
            results.append({
                "title": idea.title,
                "topics": idea.topics,
                "similarity": max_sim,
                "status": status
            })
        return {"project_id": project_id, "ideas": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/ideas")
def get_ideas_for_project(project_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.title, i.topics, i.status, i.similarity_score 
        FROM ideas i
        LEFT JOIN scripts s ON i.id = s.idea_id
        WHERE i.project_id = ? AND s.id IS NULL AND i.status NOT IN ('drop', 'rejected')
        ORDER BY i.id DESC
    """, (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "topics": json.loads(r[2]), "status": r[3], "score": r[4]} for r in rows]
@app.put("/api/ideas/{idea_id}/reject")
def reject_idea(idea_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE ideas SET status = 'rejected' WHERE id = ?", (idea_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}


# --- PHASE 2: SCRIPT BUILDER ---
@app.post("/api/phase2/generate/{idea_id}")
def generate_script(idea_id: int):
    idea_obj = get_idea_by_id(idea_id)
    if not idea_obj:
        raise HTTPException(status_code=404, detail="Idea not found")
        
    try:
        adapter = GeminiWebAdapter()
        engine = ScriptGeneratorEngine(adapter=adapter)
        script = engine.generate_full_script(idea_id, idea_obj)
        save_script(idea_id, script)
        
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM scripts WHERE idea_id = ?", (idea_id,))
        script_id = cursor.fetchone()[0]
        conn.close()
        return {"script_id": script_id, "script": script.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scripts/{script_id}")
def get_script(script_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM scripts WHERE id = ?", (script_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Script not found")
    return json.loads(row[0])

@app.put("/api/scripts/{script_id}")
def update_script(script_id: int, req: UpdateScriptRequest):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE scripts SET content = ? WHERE id = ?", (json.dumps(req.content), script_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

# --- PHASE 3: VOICE STUDIO ---
@app.post("/api/phase3/generate/{script_id}")
def generate_voiceover(script_id: int):
    script_dict = get_script(script_id)
    
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM ideas i JOIN scripts s ON s.idea_id = i.id WHERE s.id = ?", (script_id,))
    title_row = cursor.fetchone()
    conn.close()
    title_for_vo = title_row[0] if title_row else "Unknown"
    
    try:
        adapter = GeminiWebAdapter()
        engine = VoiceoverEngine(adapter=adapter)
        vo_obj = engine.generate_full_voiceover(script_id, script_dict, title_for_vo)
        save_voiceover(script_id, vo_obj)
        return {"status": "success", "voiceover": vo_obj.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voiceovers/{script_id}")
def get_voiceover(script_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM voiceovers WHERE script_id = ?", (script_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Voiceover not found")
    return json.loads(row[0])

@app.put("/api/voiceovers/{script_id}")
def update_voiceover(script_id: int, req: UpdateVoiceoverRequest):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE voiceovers SET content = ? WHERE script_id = ?", (json.dumps(req.content), script_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/phase3_5/synthesize/{script_id}")
def synthesize_voice(script_id: int):
    vo_data = get_voiceover(script_id)
    try:
        synth = VoiceSynthesizer()
        
        # recreate object
        from core.contracts import VoiceoverJSON, VoiceoverSceneJSON
        vo_scenes = [VoiceoverSceneJSON(**s) for s in vo_data.get('voiceover_scenes', [])]
        vo_obj = VoiceoverJSON(script_id=script_id, voiceover_scenes=vo_scenes)
        
        result_paths = synth.synthesize_all(vo_obj)
        return {"status": "success", "paths": result_paths}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- PHASE 4: ART GALLERY ---
@app.post("/api/phase4/generate/{script_id}")
def generate_assets(script_id: int):
    script_dict = get_script(script_id)
    try:
        adapter = GeminiWebAdapter()
        engine = SceneIllustratorEngine(adapter=adapter)
        asset_obj = engine.generate_prompts_and_images(script_id, script_dict)
        save_asset(script_id, asset_obj)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/{script_id}")
def get_assets(script_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM assets WHERE script_id = ?", (script_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Assets not found")
    return json.loads(row[0])

@app.put("/api/assets/{script_id}")
def update_assets(script_id: int, req: UpdateAssetRequest):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE assets SET content = ? WHERE script_id = ?", (json.dumps(req.content), script_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

# --- PHASE 5: RENDER ROOM ---
@app.post("/api/phase5/render/{script_id}")
def render_video(script_id: int):
    try:
        engine = VideoAssemblerEngine()
        
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM ideas i JOIN scripts s ON s.idea_id = i.id WHERE s.id = ?", (script_id,))
        title_row = cursor.fetchone()
        conn.close()
        title = title_row[0] if title_row else f"Video_{script_id}"
        
        projects = get_ready_to_render_projects_with_audio()
        project = next((p for p in projects if p['script_id'] == script_id), None)
        
        if not project:
            raise Exception("Project chưa có đủ hình ảnh & âm thanh để render.")
            
        out_path = engine.assemble_video(project['timeline'], project['title'])
        return {"status": "success", "video_path": out_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- PHASE 6: SEO & PUBLISH ---
@app.post("/api/phase6/generate/{script_id}")
def generate_seo(script_id: int):
    script_dict = get_script(script_id)
    try:
        adapter = GeminiWebAdapter()
        engine = SEOOptimizerEngine(adapter=adapter)
        seo_dict = engine.generate_metadata(script_dict)
        save_seo_metadata(script_id, seo_dict)
        return {"status": "success", "seo": seo_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seo/{script_id}")
def get_seo(script_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM seo_metadata WHERE script_id = ?", (script_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="SEO not found")
    return json.loads(row[0])


# Static Files (Giao diện Web)
os.makedirs("web", exist_ok=True)
app.mount("/", StaticFiles(directory="web", html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

@app.delete("/api/scripts/{script_id}/media")
def delete_script_media_api(script_id: int):
    import shutil
    try:
        from core.database import DB_PATH
        proj_dir = os.path.join(os.path.dirname(DB_PATH), '..', 'data', 'projects', str(script_id))
        if os.path.exists(proj_dir):
            shutil.rmtree(proj_dir)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
