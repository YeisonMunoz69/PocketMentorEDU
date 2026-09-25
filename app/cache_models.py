"""
cache_models.py — Descarga y cachea modelos de SentenceTransformers en la USB
Ejecutar UNA SOLA VEZ con internet (durante setup.bat).
Después, el sistema funciona 100% offline.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "models" / ".cache"

# Configurar variables de entorno ANTES de importar sentence_transformers
os.environ["HF_HOME"] = str(CACHE_DIR / "huggingface")
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(CACHE_DIR / "sentence_transformers")

# Crear directorios
(CACHE_DIR / "huggingface").mkdir(parents=True, exist_ok=True)
(CACHE_DIR / "sentence_transformers").mkdir(parents=True, exist_ok=True)

print(f"  Cache dir: {CACHE_DIR}")
print()

# ── Descargar modelo de embeddings ────────────────────────────────────────────
print("  [1/2] Descargando embedder: paraphrase-multilingual-MiniLM-L12-v2 (~180MB)")
print("        Esto puede tardar unos minutos...")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    # Verificar que funciona
    test = model.encode(["test"], convert_to_numpy=True)
    print(f"        OK — dimensiones: {test.shape}")
except Exception as e:
    print(f"  [ERROR] No se pudo descargar el embedder: {e}")
    sys.exit(1)

# ── Descargar modelo de re-ranking ────────────────────────────────────────────
print()
print("  [2/2] Descargando re-ranker: cross-encoder/ms-marco-MiniLM-L-6-v2 (~90MB)")
print("        Esto puede tardar unos minutos...")
try:
    from sentence_transformers import CrossEncoder
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    # Verificar que funciona
    test_score = reranker.predict([("test query", "test document")])
    print(f"        OK — score de prueba: {test_score}")
except Exception as e:
    print(f"  [AVISO] No se pudo descargar el re-ranker: {e}")
    print(f"          El sistema funcionará sin reordenamiento neural de fragmentos.")

print()
print("  Modelos cacheados correctamente en la USB.")
print(f"  Ubicación: {CACHE_DIR}")
print("  El sistema ahora puede funcionar 100% offline.")
