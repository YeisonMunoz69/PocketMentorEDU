import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys

# Pydantic Models for Requests
class ChatRequest(BaseModel):
    message: str
    subject: str = "general_english"
    level: str = "intermediate"
    mode: str = "normal"
    user_id: str = "estudiante_1"
    max_tokens: int = 512
    temperature: float = 0.4
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    top_k_rag: int = 5
    eval_mode: str = "fast"
    do_retry: bool = True

class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    bg_theme: Optional[str] = None
    temp: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    repeat_penalty: Optional[float] = None
    top_k_rag: Optional[int] = None
    eval_mode: Optional[str] = None
    auto_retry: Optional[bool] = None

class HardwareResetRequest(BaseModel):
    n_ctx: int
    gpu_layers: int
    cpu_threads: int

app = FastAPI(title="Pocket Mentor EDU API", version="2.0")

# Permitir CORS local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serviremos la carpeta frontend como estatica
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

KNOW_DIR = Path(__file__).parent.parent / "knowledge"
DB_DIR = Path(__file__).parent.parent / "database"
KNOW_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

# Variables globales para inyectar las dependencias desde main.py
_app_state = None
_rag = None
_evaluator = None
_memories = {}
_sess_dir = None

def get_mem(uid: str):
    from memory import SessionMemory
    uid = (uid or "default").strip()
    if uid not in _memories:
        _memories[uid] = SessionMemory(sess_dir=_sess_dir, user_id=uid)
    return _memories[uid]

def init_api(app_state, rag, evaluator, sess_dir: Path):
    """Inyecta las dependencias del motor principal a la API."""
    global _app_state, _rag, _evaluator, _sess_dir
    _app_state = app_state
    _rag = rag
    _evaluator = evaluator
    _sess_dir = sess_dir

SETTINGS_FILE = DB_DIR / "settings.json"

def load_settings_from_disk() -> dict:
    import json
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings_to_disk(settings: dict):
    import json
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

@app.get("/api/settings")
async def get_settings():
    return load_settings_from_disk()

@app.post("/api/settings")
async def update_settings(req: SettingsUpdate):
    settings = load_settings_from_disk()
    update_data = req.dict(exclude_unset=True)
    settings.update(update_data)
    save_settings_to_disk(settings)
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = FRONTEND_DIR / "chat.html"
    if not index_path.exists():
        return HTMLResponse("<h1>Falta frontend. Crea frontend/chat.html</h1>")
    return index_path.read_text(encoding="utf-8")

@app.get("/settings", response_class=HTMLResponse)
async def read_settings():
    settings_path = FRONTEND_DIR / "settings.html"
    if not settings_path.exists():
        return HTMLResponse("<h1>Falta frontend. Crea frontend/settings.html</h1>")
    return settings_path.read_text(encoding="utf-8")

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard():
    dash_path = FRONTEND_DIR / "dashboard.html"
    if not dash_path.exists():
        return HTMLResponse("<h1>Falta frontend. Crea frontend/dashboard.html</h1>")
    return dash_path.read_text(encoding="utf-8")

@app.get("/theme", response_class=HTMLResponse)
async def read_theme():
    theme_path = FRONTEND_DIR / "theme.html"
    if not theme_path.exists():
        return HTMLResponse("<h1>Falta frontend. Crea frontend/theme.html</h1>")
    return theme_path.read_text(encoding="utf-8")

@app.get("/knowledge", response_class=HTMLResponse)
async def read_knowledge():
    know_path = FRONTEND_DIR / "knowledge.html"
    if not know_path.exists():
        return HTMLResponse("<h1>Falta frontend. Crea frontend/knowledge.html</h1>")
    return know_path.read_text(encoding="utf-8")

@app.get("/api/dashboard/history")
async def api_dash_history():
    """Retorna un historial simple de todas las sesiones registradas"""
    import os
    if not _sess_dir or not os.path.exists(_sess_dir):
        return {"sessions": []}
    
    import json
    sessions = []
    try:
        for file in os.listdir(_sess_dir):
            if file.endswith(".json"):
                with open(os.path.join(_sess_dir, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Calcular promedios basicos para la lista
                    total_score = 0
                    turns = data.get("turns", [])
                    evals_count = 0
                    for turn in turns:
                        if turn.get("evaluation"):
                            ev = turn["evaluation"]
                            total_score += ev.get("overall_score", 0)
                            evals_count += 1
                    
                    avg_score = (total_score / evals_count) if evals_count > 0 else 0
                    
                    sessions.append({
                        "user_id": data.get("user_id", "Desconocido"),
                        "level": data.get("level", ""),
                        "subject": data.get("subject", ""),
                        "start_time": data.get("start_time", ""),
                        "turns_count": len(turns),
                        "avg_score": round(avg_score, 2),
                        "assessed_skills": list(data.get("assessed_skills", {}).keys())
                    })
    except Exception as e:
        print(f"Error reading sessions: {e}")
    
    # Sort by start_time descending
    sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
    return {"sessions": sessions}

@app.get("/api/history")
async def get_all_history():
    """Retorna una lista simple de los archivos de conversación para la UI del usuario."""
    import os
    if not _sess_dir or not os.path.exists(_sess_dir):
        return {"history": []}
    
    import json
    history = []
    try:
        for file in os.listdir(_sess_dir):
            if file.endswith(".json"):
                with open(os.path.join(_sess_dir, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    history.append({
                        "file_id": file.replace('.json', ''),
                        "user_id": data.get("user_id", "Desconocido"),
                        "subject": data.get("subject", ""),
                        "level": data.get("level", ""),
                        "start_time": data.get("start_time", ""),
                        "turns_count": len(data.get("turns", [])),
                    })
    except Exception as e:
        print(f"Error reading history folder: {e}")
        
    history.sort(key=lambda x: x.get("start_time", ""), reverse=True)
    return {"history": history}

@app.get("/api/history/{file_id}")
async def get_history_detail(file_id: str):
    """Devuelve todo el detalle de una conversación guardada para pintarlo en la UI."""
    import os, json
    if not _sess_dir:
        return JSONResponse(status_code=500, content={"error": "Dir no inicializado"})
    
    file_path = os.path.join(_sess_dir, f"{file_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})
    return JSONResponse(status_code=404, content={"error": "No encontrado"})

@app.post("/api/history/{file_id}/resume")
async def resume_history(file_id: str):
    """Fuerza la carga de un archivo de historial especifico en la memoria del usuario para reanudar."""
    import os, json
    if not _sess_dir:
        return JSONResponse(status_code=500, content={"error": "no dir"})
    file_path = os.path.join(_sess_dir, f"{file_id}.json")
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "no found"})
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    uid = data.get("user_id", "default")
    mem = get_mem(uid)
    mem.reset_session()
    
    turns = data.get("turns", [])
    for t in turns:
        if "user_msg" in t:
            mem._history.append({"role": "user", "content": t["user_msg"]})
            mem._turn_count += 1
        if "agent_response" in t:
            mem._history.append({"role": "assistant", "content": t["agent_response"]})
            
    mem.current_file_id = file_id 
    
    return {"status": "ok"}

@app.delete("/api/history/{file_id}")
async def delete_history(file_id: str):
    """Elimina permanentemente una conversacion en el USB."""
    import os
    if not _sess_dir:
        return JSONResponse(status_code=500, content={"error": "Directorio DB no inicializado"})
    
    file_path = os.path.join(_sess_dir, f"{file_id}.json")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            # Limpiar memoria si esta cargado
            # Extraer uid real del archivo o forzar recarga (asumiendo formato user_id_timestamp)
            parts = file_id.split("_")
            if len(parts) > 1:
                uid = "_".join(parts[:-1])
                if uid in _memories:
                    del _memories[uid]
            
            return {"status": "ok", "message": "Conversación eliminada"}
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"Error eliminando: {str(e)}"})
    else:
        return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})

@app.post("/api/chat")
async def chat_endpoint(req: Request):
    """
    Recibe el mensaje y devuelve Server-Sent Events (SSE) para el efecto
    de maquina de escribir (streaming) caracter por caracter.
    """
    body = await req.json()
    msg = body.get("message", "")
    subj = body.get("subject", "general_english")
    lvl = body.get("level", "intermediate")
    mode = body.get("mode", "normal")
    uid = body.get("user_id", "estudiante_1")
    mt = body.get("max_tokens", 512)
    tp = body.get("temperature", 0.4)
    tpp = body.get("top_p", 0.9)
    rp = body.get("repeat_penalty", 1.1)
    topk = body.get("top_k_rag", 5)
    eval_mode = body.get("eval_mode", "fast")
    do_retry = body.get("auto_retry", True)

    if not msg.strip():
        return JSONResponse({"error": "Mensaje vacio"})

    async def event_stream():
        # Fake generator for now. Se implementara process_message adaptado
        # para Async generator.
        from prompt_builder import build_system_prompt, build_full_prompt
        import time
        memory = get_mem(uid)
        memory.level = lvl
        memory.subject = subj
        memory.add_turn("user", msg, _app_state.llm)
        memory.add_topic(subj)

        t0 = time.time()
        # RAG Search (Bloqueante, ejecutado en hilo si fuera muy lento, pero es ok)
        results = _rag.hybrid_search(msg, top_k=topk, llm=_app_state.llm)
        context = _rag.build_context(results)
        
        prompt = build_full_prompt(
            system_prompt=build_system_prompt(subject=subj, level=lvl, mode=mode),
            context=context,
            memory_block=memory.build_memory_block(),
            student_profile=memory.build_student_profile_block(),
            query=msg,
        )

        # Extraer nombres de las fuentes para la UI
        sources_list = []
        for r in results:
            src_path = r.get("source", "")
            if src_path:
                src_name = Path(src_path).name
                page = r.get("page", "")
                label = f"{src_name} (pág. {page})" if page else src_name
                sources_list.append(label)
        
        unique_sources = list(set(sources_list))

        # Enviar senal de "Contexto encontrado"
        import json
        yield f"data: {json.dumps({'type': 'context', 'count': len(results), 'sources': unique_sources})}\n\n"
        
        response_text = ""
        t1 = time.time()
        # Llamar al generador de Llama-cpp-python streaming
        try:
            stream = _app_state.llm(
                prompt, max_tokens=int(mt), temperature=float(tp),
                top_p=float(tpp), repeat_penalty=float(rp), echo=False,
                stream=True, stop=["Estudiante:", "━━━", "\n\nTutor:", "Human:",
                                    "\nFuente:", "\n---", "[Fuente:", "---\n"]
            )
            for chunk in stream:
                token = chunk["choices"][0]["text"]
                response_text += token
                # Evitar comillas rotas en JSON parse
                import json
                safe_token = json.dumps({"type": "token", "text": token})
                yield f"data: {safe_token}\n\n"
                await asyncio.sleep(0.01)  # Ceder hilo
                
        except Exception as e:
            import json
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

        response_text = response_text.strip()
        memory.add_turn("assistant", response_text)
        t2 = time.time()
        
        # Guardado en archivo persistente USB para el Historial
        import os, json
        from datetime import datetime
        
        if getattr(memory, 'current_file_id', None):
            file_id = memory.current_file_id
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_id = f"{uid}_{ts}"
            memory.current_file_id = file_id
            
        file_path = os.path.join(_sess_dir, f"{file_id}.json")
        
        sess_data = {
            "file_id": file_id,
            "user_id": uid,
            "subject": memory.subject,
            "level": memory.level,
            "start_time": datetime.now().isoformat(),
            "turns": []
        }
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    sess_data["start_time"] = old_data.get("start_time", sess_data["start_time"])
            except Exception: pass
            
        turns_list = []
        current_turn = {}
        for item in memory._history:
            if item["role"] == "user":
                current_turn = {"user_msg": item["content"]}
            elif item["role"] == "assistant":
                current_turn["agent_response"] = item["content"]
                turns_list.append(current_turn)
                current_turn = {}
                
        sess_data["turns"] = turns_list
        sess_data["turns_count"] = len(turns_list)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sess_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving session: {e}")

        if eval_mode != "off":
            _evaluator.set_mode(eval_mode)
            ev = _evaluator.evaluate(msg, response_text, results, lvl)
            metrics_payload = {
                "type": "metrics",
                "data": ev,
                "rag_time": t1 - t0,
                "gen_time": t2 - t1
            }
            yield f"data: {json.dumps(metrics_payload)}\n\n"

        # Emitir evento fin
        yield f"data: {{\"type\": \"done\"}}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/api/upload")
async def api_upload(files: List[UploadFile] = File(...)):
    """
    Sube archivos a la carpeta 'knowledge' y dispara el pipeline de Ingesta (RAG).
    """
    import shutil
    from ingester import Ingester
    
    saved_files = []
    for file in files:
        file_path = KNOW_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
        
    try:
        # Re-correr la ingesta (busca archivos nuevos en KNOW_DIR)
        embedder = _rag._get_embedder()
        ingester = Ingester(know_dir=KNOW_DIR, db_dir=DB_DIR, embedder=embedder)
        ingester.run()
        # Recargar el RAG engine en memoria para que vea los nuevos chunks
        _rag.reload()
        
        return {"status": "ok", "message": f"{len(saved_files)} archivos indexados.", "files": saved_files}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Fallo en ingesta: {str(e)}"})

@app.post("/api/hardware/reload")
async def api_hw_reload(req: HardwareResetRequest):
    success = _app_state.reload_llm(req.n_ctx, req.gpu_layers, req.cpu_threads)
    if success:
        return {"status": "ok"}
    return JSONResponse(status_code=500, content={"error": "Fallo al recargar LLM"})

@app.get("/api/system/stats")
async def api_sys_stats():
    import psutil
    vm = psutil.virtual_memory()
    # Also attempt to read knowledge folder size
    know_sz = 0
    if KNOW_DIR.exists():
        know_sz = sum(f.stat().st_size for f in KNOW_DIR.glob('**/*') if f.is_file())
        
    return {
        "ram_percent": vm.percent,
        "ram_usage_bytes": vm.used,
        "ram_used_gb": round(vm.used / (1024**3), 2),
        "ram_total_gb": round(vm.total / (1024**3), 2),
        "model_name": getattr(_app_state, 'model_name', 'Unknown'),
        "knowledge_size_mb": round(know_sz / (1024*1024), 2)
    }
