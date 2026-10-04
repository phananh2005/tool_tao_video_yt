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
    # Danh sách dự án
    cursor.execute("SELECT id, name, created_at FROM projects ORDER BY id DESC")
    projects = cursor.fetchall()
    
    # Gom dữ liệu để tính toán Phase
    cursor.execute("SELECT id, project_id, status FROM ideas")
    ideas = cursor.fetchall()
    
    cursor.execute("SELECT id, idea_id, content FROM scripts")
    scripts = cursor.fetchall()
    
    cursor.execute("SELECT id, script_id, content FROM voiceovers")
    voiceovers = cursor.fetchall()
    
    cursor.execute("SELECT id, script_id, content FROM assets")
    assets = cursor.fetchall()
    
    cursor.execute("SELECT id, script_id, content FROM seo_metadata")
    seo = cursor.fetchall()
    
    conn.close()
    
    result = []
    for p in projects:
        p_id = p[0]
        # Tìm idea mới nhất không bị drop của project này
        p_ideas = [i for i in ideas if i[1] == p_id and i[2] != 'drop']
        
        phase = 1
        idea_id = p_ideas[-1][0] if p_ideas else None
        script_id = None
        
        if idea_id:
            p_script = [s for s in scripts if s[1] == idea_id]
            if p_script:
                script_id = p_script[-1][0]
                phase = 2
                
                p_vo = [v for v in voiceovers if v[1] == script_id]
                if p_vo:
                    phase = 3
                    
                    p_asset = [a for a in assets if a[1] == script_id]
                    if p_asset:
                        phase = 4
                        
                        # Giả định Phase 5 (Render) đã xong nếu có ở seo
                        p_seo = [s for s in seo if s[1] == script_id]
                        if p_seo:
                            phase = 6
        
        result.append({
            "id": p_id,
            "name": p[1],
            "created_at": p[2],
            "phase": phase,
            "current_idea_id": idea_id,
            "current_script_id": script_id
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
        
        new_ideas = engine.generate_ideas(req.theme, count=5)
        history = get_project_ideas(project_id)
        
        results = []
        for idea in new_ideas:
            max_sim = max([engine.calculate_similarity(idea.topics, old.topics) for old in history] + [0.0])
            status = 'drop' if max_sim > 0.85 else ('warn' if max_sim >= 0.60 else 'pass')
            
            if status != 'drop':
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
    cursor.execute("SELECT id, title, topics, status, similarity_score FROM ideas WHERE project_id = ? AND status != 'drop' ORDER BY id DESC", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "topics": json.loads(r[2]), "status": r[3], "score": r[4]} for r in rows]

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
