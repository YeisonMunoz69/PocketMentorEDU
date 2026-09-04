"""
main.py — Pocket Mentor EDU v2.0
Integra: cifrado AES-256, detección de hardware, cierre limpio con métricas.
Modo 100% offline: no requiere internet después del setup inicial.
"""

import os, sys, signal, logging, time
from pathlib import Path

# ── Modo offline: configurar ANTES de importar cualquier librería ─────────────
# Esto asegura que sentence-transformers, huggingface_hub y gradio no intenten
# conectarse a internet. Las variables se configuran también en mentor.bat,
# pero aquí se refuerzan por si alguien ejecuta main.py directamente.
_BASE = Path(__file__).resolve().parent.parent
_CACHE = _BASE / "models" / ".cache"
if not os.environ.get("HF_HUB_OFFLINE"):
    os.environ["HF_HUB_OFFLINE"] = "1"
if not os.environ.get("TRANSFORMERS_OFFLINE"):
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
if not os.environ.get("GRADIO_ANALYTICS_ENABLED"):
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
if not os.environ.get("HF_HOME"):
    os.environ["HF_HOME"] = str(_CACHE / "huggingface")
if not os.environ.get("SENTENCE_TRANSFORMERS_HOME"):
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(_CACHE / "sentence_transformers")

BASE_DIR   = Path(__file__).resolve().parent.parent
APP_DIR    = BASE_DIR / "app"
MODELS_DIR = BASE_DIR / "models"
KNOW_DIR   = BASE_DIR / "knowledge"
DB_DIR     = BASE_DIR / "database"
SESS_DIR   = BASE_DIR / "sessions"
LOGS_DIR   = BASE_DIR / "logs"
PROMPT_DIR = BASE_DIR / "prompts"

for d in [KNOW_DIR, DB_DIR, DB_DIR/"staging", SESS_DIR, LOGS_DIR, PROMPT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "system.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("main")

sys.path.insert(0, str(APP_DIR))
from ingester  import Ingester
from rag       import RAGEngine
from evaluator import ResponseEvaluator
from crypto    import CryptoManager
from api       import init_api, app as fastapi_app


# ── Hardware detection ────────────────────────────────────────────────────────

def detect_hardware() -> dict:
    hw = {"cpu_threads": 4, "gpu_layers": 0, "ram_gb": 0}
    try:
        import psutil
        hw["cpu_threads"] = max(2, psutil.cpu_count(logical=False) or 4)
        hw["ram_gb"]      = round(psutil.virtual_memory().total / 1024**3, 1)
        if hw["ram_gb"] < 6:
            log.warning(f"RAM disponible ({hw['ram_gb']} GB) puede ser insuficiente (mínimo 8 GB recomendado).")
    except ImportError:
        pass

    # Detectar GPU CUDA
    try:
        import subprocess
        r = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and r.stdout.strip():
            hw["gpu_layers"] = 35
            log.info(f"GPU detectada: {r.stdout.strip()} — activando {hw['gpu_layers']} capas GPU.")
    except Exception:
        pass

    log.info(f"Hardware: {hw['cpu_threads']} hilos CPU | GPU layers: {hw['gpu_layers']} | RAM: {hw['ram_gb']} GB")
    return hw


def find_model(model_arg: str = None) -> Path:
    if model_arg:
        p = Path(model_arg)
        if not p.is_absolute():
            p = MODELS_DIR / model_arg
        if not p.exists():
            log.error(f"Modelo no encontrado: {p}")
            log.error(f"Disponibles: {[m.name for m in MODELS_DIR.glob('*.gguf')]}")
            sys.exit(1)
        return p
    candidates = sorted(MODELS_DIR.glob("*.gguf"))
    if not candidates:
        log.error("No se encontró ningún modelo .gguf en /models")
        sys.exit(1)
    log.info(f"Modelo: {candidates[0].name}")
    return candidates[0]


def load_model(model_path: Path, hw: dict):
    try:
        from llama_cpp import Llama
        
        # ── Contexto Dinámico basado en RAM ──
        ram = hw.get("ram_gb", 8)
        if ram < 8:
            n_ctx = 2048  # PC limitado, previene crashes
        elif ram < 16:
            n_ctx = 4096  # PC estándar
        else:
            n_ctx = 8192  # PC potente (16GB+)
            
        log.info(f"Cargando modelo... (RAM detectada: {ram}GB → n_ctx={n_ctx})")
        
        llm = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_threads=hw["cpu_threads"],
            n_gpu_layers=hw["gpu_layers"],
            verbose=False,
        )
        log.info("Modelo cargado.")
        return llm
    except ImportError:
        log.error("llama-cpp-python no instalado.")
        sys.exit(1)


# ── Cifrado ───────────────────────────────────────────────────────────────────

def setup_crypto() -> tuple:
    """
    Retorna (crypto_manager, is_encrypted).
    Si hay archivos .enc presentes, pide contraseña y descifra.
    Si no, ofrece activar cifrado pero no lo obliga.
    """
    cm = CryptoManager(BASE_DIR)
    enc_files = list(KNOW_DIR.rglob("*.enc")) + list(DB_DIR.rglob("*.enc"))

    if enc_files:
        log.info(f"Datos cifrados detectados ({len(enc_files)} archivos). Solicita contraseña.")
        print("\n" + "═"*50)
        print("  🔐  POCKET MENTOR EDU — Datos protegidos")
        print("═"*50)
        if cm.prompt_password():
            try:
                cm.unlock_data()
                log.info("Datos descifrados correctamente.")
                return cm, True
            except ValueError:
                log.error("Contraseña incorrecta. Saliendo.")
                sys.exit(1)
        else:
            log.error("Sin contraseña. No se pueden cargar datos cifrados.")
            sys.exit(1)
    else:
        # Sin cifrado activo — continuar normalmente
        log.info("Sin cifrado activo. Ejecutando en modo abierto.")
        return cm, False


def lock_on_exit(cm: CryptoManager, evaluator, session_id: str):
    """Cifra los datos y guarda métricas al cerrar."""
    log.info("Cerrando sistema…")
    try:
        evaluator.save_session_metrics(session_id)
        log.info("Métricas de sesión guardadas.")
    except Exception as e:
        log.warning(f"No se pudieron guardar métricas: {e}")

    if cm.is_unlocked:
        try:
            log.info("Cifrando datos…")
            cm.lock()
            log.info("Datos cifrados. Sistema cerrado de forma segura.")
        except Exception as e:
            log.error(f"Error cifrando datos: {e}")


# ── State Manager ─────────────────────────────────────────────────────────────

class AppState:
    """Maneja el ciclo de vida del LLM para permitir su recarga en caliente
    desde la interfaz web sin tener que cerrar el programa completo."""
    def __init__(self, model_path: Path, hw: dict):
        self.model_path = model_path
        self.hw = hw
        self.llm = load_model(model_path, hw)
        self.model_name = model_path.stem

    def reload_llm(self, n_ctx: int, gpu_layers: int, threads: int) -> bool:
        try:
            import gc
            log.info("Descargando modelo actual de RAM...")
            del self.llm
            gc.collect()
            
            self.hw["gpu_layers"] = gpu_layers
            self.hw["cpu_threads"] = threads
            
            from llama_cpp import Llama
            log.info(f"Recargando modelo (n_ctx={n_ctx}, gpu={gpu_layers}, threads={threads})...")
            self.llm = Llama(
                model_path=str(self.model_path),
                n_ctx=n_ctx,
                n_threads=threads,
                n_gpu_layers=gpu_layers,
                verbose=False,
            )
            log.info("Modelo recargado exitosamente en caliente.")
            return True
        except Exception as e:
            log.error(f"Error recargando LLM: {e}")
            return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pocket Mentor EDU")
    parser.add_argument("--model", type=str, default=None,
                        help="Archivo .gguf a usar (ej: Phi-4-mini-Q4_K_M.gguf). "
                             "Si no se indica, usa el primero de /models.")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("  POCKET MENTOR EDU v2.0 — ESL Edition")
    log.info("=" * 60)

    session_id = time.strftime("%Y%m%d_%H%M%S")

    # 1. Hardware
    hw = detect_hardware()

    # 2. Cifrado
    cm, is_encrypted = setup_crypto()

    # 3. RAG — crear primero para reusar su embedder en la ingesta
    rag = RAGEngine(db_dir=DB_DIR, know_dir=KNOW_DIR)

    # 4. Ingesta — pasar un callback del embedder del RAG para evitar doble carga en RAM
    # Solo inicializará el embedder de ser necesario procesar nuevos archivos.
    ingester = Ingester(know_dir=KNOW_DIR, db_dir=DB_DIR)
    ingester._get_embedder_cb = rag._get_embedder
    ingester.run()
    rag.reload()  # actualizar el indice si hubo nuevos documentos

    # 5. Modelo LLM (Manejado por AppState)
    model_path = find_model(args.model)
    log.info(f"Modelo seleccionado: {model_path.name}")
    app_state = AppState(model_path, hw)

    # 6. Evaluador — inyectar callback para carga lazy
    evaluator = ResponseEvaluator(logs_dir=LOGS_DIR, mode="fast")
    try:
        evaluator.set_embedder_cb(rag._get_embedder)
    except Exception as e:
        log.warning(f"No se pudo inyectar embedder callback en evaluador: {e}")

    # 7. Cierre limpio
    def _shutdown(sig=None, frame=None):
        lock_on_exit(cm, evaluator, session_id)
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # 8. API y Web UI (FastAPI)
    log.info("Inyectando dependencias al motor API...")
    init_api(app_state, rag, evaluator, SESS_DIR)

    log.info("Lanzando servidor local en http://localhost:8000")
    try:
        import uvicorn
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")
    finally:
        lock_on_exit(cm, evaluator, session_id)


if __name__ == "__main__":
    main()