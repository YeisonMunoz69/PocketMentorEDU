"""
evaluator.py — Indicadores automáticos de respuesta con toggle ON/OFF
Modos:
  - OFF   : sin evaluación, score fijo 1.0, máxima velocidad
  - FAST  : Jaccard sobre tokens (sin embeddings, ~0ms)
  - FULL  : similitud coseno con embeddings (~200-500ms extra)

Los puntajes describen apego al contexto recuperado y propiedades de la salida.
No estiman calidad pedagógica ni aprendizaje.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

log = logging.getLogger("evaluator")

SCORE_THRESHOLD = 0.60

NO_INFO_PATTERNS = [
    "no tengo información", "no encontr", "no está en",
    "mi base de conocimientos", "no puedo responder",
    "outside my knowledge", "not in the context",
    "don't have information", "no information about",
]

# ── Modos de evaluación ───────────────────────────────────────────────────────
EVAL_MODE_OFF  = "off"    # bypass total — máxima velocidad
EVAL_MODE_FAST = "fast"   # Jaccard tokens — sin embeddings
EVAL_MODE_FULL = "full"   # coseno con embeddings

DEFAULT_MODE = EVAL_MODE_FAST


def _normalize(text: str) -> str:
    return text.lower().strip()


def _jaccard(a: str, b: str) -> float:
    ta = set(_normalize(a).split())
    tb = set(_normalize(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0


def _is_fallback(response: str) -> bool:
    resp_lower = _normalize(response)
    return any(p in resp_lower for p in NO_INFO_PATTERNS)


# ─────────────────────────────────────────────────────────────────────────────
class ResponseEvaluator:

    def __init__(self, logs_dir: Optional[Path] = None,
                 mode: str = DEFAULT_MODE):
        self.logs_dir = logs_dir
        self.mode     = mode          # "off" | "fast" | "full"
        self._embedder = None         # se inyecta desde main.py
        self._get_embedder_cb = None  # se inyecta desde main.py para carga lazy
        self._session_metrics: List[Dict] = []

    # ── Inyección del embedder (llamado desde main.py) ────────────────────────
    def set_embedder(self, embedder):
        """Recibe el mismo embedder que usa el RAG — sin doble carga."""
        self._embedder = embedder
        log.info("Evaluator: embedder inyectado.")

    def set_embedder_cb(self, cb):
        """Recibe callback para lazy loading del embedder."""
        self._get_embedder_cb = cb
        log.info("Evaluator: callback de embedder inyectado.")

    def set_mode(self, mode: str):
        assert mode in (EVAL_MODE_OFF, EVAL_MODE_FAST, EVAL_MODE_FULL), \
            f"Modo inválido: {mode}"
        self.mode = mode
        log.info(f"Evaluator modo: {mode}")

    # ── Evaluación principal ──────────────────────────────────────────────────
    def evaluate(self, query: str, response: str,
                 context_chunks: List[Dict],
                 student_level: str = "intermediate") -> Dict:

        # ── MODO OFF: bypass completo ─────────────────────────────────────────
        if self.mode == EVAL_MODE_OFF:
            result = {
                "pass": True, "overall_score": 1.0,
                "grounding_score": 1.0, "relevance_score": 1.0,
                "is_fallback": False, "mode": "off",
                "details": "Evaluación desactivada.",
            }
            self._record(query, result)
            return result

        # ── Fallback detection ────────────────────────────────────────────────
        if _is_fallback(response):
            result = {
                "pass": True, "overall_score": 0.80,
                "grounding_score": 1.0, "relevance_score": 0.0,
                "is_fallback": True, "mode": self.mode,
                "details": "Fallback activado correctamente.",
            }
            self._record(query, result)
            return result

        # ── Scores según modo ─────────────────────────────────────────────────
        if self.mode == EVAL_MODE_FULL:
            if self._embedder is None and self._get_embedder_cb is not None:
                self._embedder = self._get_embedder_cb()
                
            if self._embedder is not None:
                relevance_score, grounding_score = self._scores_embeddings(
                    query, response, context_chunks)
            else:
                relevance_score, grounding_score = self._scores_jaccard(
                    query, response, context_chunks)
        else:
            relevance_score, grounding_score = self._scores_jaccard(
                query, response, context_chunks)

        level_score = self._level_coherence(response, student_level)

        overall = (0.40 * grounding_score +
                   0.40 * relevance_score +
                   0.20 * level_score)

        result = {
            "pass":            overall >= SCORE_THRESHOLD,
            "overall_score":   round(overall, 3),
            "grounding_score": round(grounding_score, 3),
            "relevance_score": round(relevance_score, 3),
            "level_score":     round(level_score, 3),
            "is_fallback":     False,
            "mode":            self.mode,
            "details":         "",
        }
        self._record(query, result)
        return result

    # ── Scores Jaccard (fast) ─────────────────────────────────────────────────
    def _scores_jaccard(self, query, response, chunks):
        if chunks:
            rel = min(1.0, max(_jaccard(query, c["text"][:300])
                               for c in chunks) * 5)
            ctx = " ".join(c["text"][:200] for c in chunks)
            grd = min(1.0, _jaccard(response, ctx) * 8)
        else:
            rel, grd = 0.0, 0.2
        return rel, grd

    # ── Scores embeddings (full) ──────────────────────────────────────────────
    def _scores_embeddings(self, query, response, chunks):
        try:
            texts = [query, response] + [c["text"][:512] for c in chunks[:5]]
            vecs  = self._embedder.encode(texts, convert_to_numpy=True,
                                          show_progress_bar=False)
            q_vec, r_vec = vecs[0], vecs[1]
            c_vecs = vecs[2:]

            if len(c_vecs):
                rel = float(max(_cosine(q_vec, cv) for cv in c_vecs))
                grd = float(max(_cosine(r_vec, cv) for cv in c_vecs))
            else:
                rel, grd = 0.0, 0.2

            # Mapear de [-1,1] a [0,1]
            rel = (rel + 1) / 2
            grd = (grd + 1) / 2
            return rel, grd
        except Exception as e:
            log.warning(f"Embeddings eval falló, fallback Jaccard: {e}")
            return self._scores_jaccard(query, response, chunks)

    # ── Coherencia de nivel ───────────────────────────────────────────────────
    def _level_coherence(self, response: str, level: str) -> float:
        words = len(response.split())
        if level == "basic":
            return min(1.0, 1.0 - max(0, words - 200) / 200)
        elif level == "advanced":
            return min(1.0, words / 250)
        return min(1.0, words / 150)

    # ── Registro ──────────────────────────────────────────────────────────────
    def _record(self, query: str, result: Dict):
        self._session_metrics.append({
            "ts":       datetime.now().isoformat(),
            "query":    query[:100],
            "score":    result["overall_score"],
            "fallback": result.get("is_fallback", False),
            "pass":     result["pass"],
            "mode":     result.get("mode", self.mode),
        })

    def save_session_metrics(self, session_id: str = ""):
        if not self.logs_dir or not self._session_metrics:
            return
        fname = f"session_{session_id or datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        fpath = self.logs_dir / fname
        payload = {"summary": self._compute_summary(), "turns": self._session_metrics}
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        log.info(f"Métricas guardadas: {fname}")

    def _compute_summary(self) -> Dict:
        if not self._session_metrics:
            return {}
        scores    = [m["score"]    for m in self._session_metrics]
        fallbacks = [m["fallback"] for m in self._session_metrics]
        passed    = [m["pass"]     for m in self._session_metrics]
        n = len(scores)
        return {
            "total_turns":   n,
            "avg_score":     round(sum(scores) / n, 3),
            "fallback_rate": round(sum(fallbacks) / n, 3),
            "pass_rate":     round(sum(passed) / n, 3),
            "min_score":     round(min(scores), 3),
            "max_score":     round(max(scores), 3),
        }

    def get_session_summary(self) -> Dict:
        return self._compute_summary()

    def load_historical_metrics(self) -> List[Dict]:
        if not self.logs_dir:
            return []
        sessions = []
        for f in sorted(self.logs_dir.glob("session_*.json")):
            try:
                with open(f, encoding="utf-8") as fp:
                    data = json.load(fp)
                s = data.get("summary", {})
                s["session_file"] = f.name
                sessions.append(s)
            except Exception:
                pass
        return sessions
