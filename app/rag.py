"""
rag.py — Motor RAG Híbrido Avanzado
Implementa:
  • Parent-Document Retrieval (child 128t → parent 1024t)
  • Búsqueda híbrida: embeddings coseno + BM25
  • Fusión con Reciprocal Rank Fusion (RRF)
  • Re-ranking con CrossEncoder (MiniLM)
  • Query Expansion (2 variantes adicionales)
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Traduccion rapida de terminos matematicos comunes ES → EN
# ─────────────────────────────────────────────────────────────────────────────

_MATH_TERMS = {
    "funcion": "function", "función": "function",
    "derivada": "derivative", "integral": "integral",
    "limite": "limit", "límite": "limit",
    "logaritmo": "logarithm", "exponencial": "exponential",
    "ecuacion": "equation", "ecuación": "equation",
    "polinomio": "polynomial", "trigonometria": "trigonometry",
    "trigonométrica": "trigonometric", "algebra": "algebra",
    "calculo": "calculus", "cálculo": "calculus",
    "matriz": "matrix", "vector": "vector",
    "dominio": "domain", "rango": "range",
    "continuidad": "continuity", "diferenciable": "differentiable",
    "serie": "series", "sucesion": "sequence", "sucesión": "sequence",
    "convergencia": "convergence", "divergencia": "divergence",
    "teorema": "theorem", "demostracion": "proof",
    "conjunto": "set", "relacion": "relation", "relación": "relation",
    "grafica": "graph", "gráfica": "graph",
    "pendiente": "slope", "tangente": "tangent",
    "propiedades": "properties", "regla": "rule",
    "resolver": "solve", "simplificar": "simplify",
    "sistema": "system", "inecuacion": "inequality",
    "valor": "value", "variable": "variable",
}

def _spanish_to_english_terms(text: str) -> str:
    """Reemplaza terminos matematicos en español por su equivalente en ingles."""
    result = text.lower()
    for es, en in _MATH_TERMS.items():
        result = result.replace(es, en)
    return result



log = logging.getLogger("rag")


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────────────────────

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.array(a), np.array(b)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0


def _rrf(rankings: List[List[str]], k: int = 60) -> Dict[str, float]:
    """Reciprocal Rank Fusion sobre listas de IDs ordenados."""
    scores: Dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return scores


# ─────────────────────────────────────────────────────────────────────────────
# Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class RAGEngine:
    """
    Motor RAG con búsqueda híbrida, re-ranking y query expansion.
    """

    def __init__(self, db_dir: Path, know_dir: Path):
        self.db_dir   = db_dir
        self.know_dir = know_dir
        self._chunks: List[Dict]       = []   # child chunks indexados
        self._parents: Dict[str, Dict] = {}   # parent_id → parent chunk
        self._embeddings: List[np.ndarray] = []
        self._bm25 = None
        self._embedder = None
        self._reranker = None
        self._load_index()

    # ── Carga del índice ──────────────────────────────────────────────────────

    def _load_index(self):
        """Carga índice vectorial y BM25 desde disco si existen."""
        index_file   = self.db_dir / "chunks.json"
        parents_file = self.db_dir / "parents.json"
        embeddings_file = self.db_dir / "embeddings.npy"

        if not index_file.exists():
            log.info("No hay índice previo. Se construirá al ingestar documentos.")
            return

        with open(index_file, encoding="utf-8") as f:
            self._chunks = json.load(f)
        with open(parents_file, encoding="utf-8") as f:
            self._parents = json.load(f)

        if embeddings_file.exists():
            try:
                raw = np.load(str(embeddings_file), allow_pickle=False)
                self._embeddings = list(raw)
                if len(self._embeddings) != len(self._chunks):
                    log.warning("Embeddings y chunks desincronizados. Limpiando embeddings.")
                    self._embeddings = []
            except Exception as e:
                log.warning(f"No se pudieron cargar embeddings: {e}")
                self._embeddings = []

        self._build_bm25()
        log.info(f"Índice cargado: {len(self._chunks)} chunks, {len(self._parents)} padres.")

    def _build_bm25(self):
        """Construye el índice BM25 desde los chunks en memoria."""
        if not self._chunks:
            return
        try:
            from rank_bm25 import BM25Okapi
            tokenized = [c["text"].lower().split() for c in self._chunks]
            self._bm25 = BM25Okapi(tokenized)
        except ImportError:
            log.warning("rank_bm25 no disponible. Búsqueda híbrida desactivada.")

    def reload(self):
        """Recarga el índice desde disco (llamado tras ingesta)."""
        self._chunks = []
        self._parents = {}
        self._embeddings = []
        self._bm25 = None
        self._load_index()

    # ── Embedder (lazy load) ──────────────────────────────────────────────────

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                model_name = "paraphrase-multilingual-MiniLM-L12-v2"
                self._embedder = SentenceTransformer(model_name)
                log.info(f"Embedder cargado: {model_name}")
            except ImportError:
                log.error("sentence-transformers no disponible.")
                raise
        return self._embedder

    def embed(self, texts: List[str]) -> np.ndarray:
        embedder = self._get_embedder()
        return embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    # ── Re-ranker (lazy load) ─────────────────────────────────────────────────

    def _get_reranker(self):
        if self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                log.info("Re-ranker CrossEncoder cargado.")
            except Exception as e:
                log.warning(f"CrossEncoder no disponible: {e}. Se omitirá re-ranking.")
        return self._reranker

    # ── Query Expansion ───────────────────────────────────────────────────────

    def expand_query(self, query: str, llm=None) -> List[str]:
        """
        Genera variantes de la consulta incluyendo traduccion al ingles.
        Clave porque los docs academicos de OpenStax estan en ingles.
        """
        variants = [query]
        variants.append(query.replace("?","").replace("¿","").strip())

        if llm is not None:
            try:
                prompt = (
                    "Translate this question to English, then give 1 alternative English "
                    "phrasing. Output only 2 English lines, no numbering:\n\n"
                    + query + "\n\nEnglish:"
                )
                resp = llm(prompt, max_tokens=60, temperature=0.1, echo=False)
                english = resp["choices"][0]["text"].strip().split("\n")
                variants += [v.strip() for v in english if v.strip() and len(v.strip()) > 5][:2]
            except Exception as e:
                log.warning(f"Query expansion failed: {e}")
                variants.append(_spanish_to_english_terms(query))
        else:
            variants.append(_spanish_to_english_terms(query))

        return [v for v in variants if v.strip()][:4]


    # ── Búsqueda vectorial ────────────────────────────────────────────────────

    def _vector_search(self, query: str, top_k: int = 15) -> List[Tuple[str, float]]:
        if not self._embeddings or not self._chunks:
            return []
        q_vec = self.embed([query])[0]
        sims = [(_cosine_similarity(q_vec, e), i)
                for i, e in enumerate(self._embeddings)]
        sims.sort(reverse=True)
        return [(self._chunks[i]["id"], score) for score, i in sims[:top_k]]

    # ── Búsqueda BM25 ─────────────────────────────────────────────────────────

    def _bm25_search(self, query: str, top_k: int = 15) -> List[Tuple[str, float]]:
        if self._bm25 is None or not self._chunks:
            return []
        scores = self._bm25.get_scores(query.lower().split())
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(self._chunks[i]["id"], float(s)) for i, s in ranked[:top_k]]

    # ── Búsqueda híbrida con RRF ──────────────────────────────────────────────

    def hybrid_search(self, query: str, top_k: int = 10,
                      llm=None) -> List[Dict]:
        """
        Ejecuta query expansion + búsqueda híbrida + RRF + re-ranking.
        Retorna los top_k chunks padres con mayor relevancia.
        """
        if not self._chunks:
            return []

        queries = self.expand_query(query, llm)
        all_vec_ranks: List[List[str]] = []
        all_bm25_ranks: List[List[str]] = []

        for q in queries:
            vec_results  = self._vector_search(q, top_k=30)
            bm25_results = self._bm25_search(q, top_k=30)
            all_vec_ranks.append([r[0] for r in vec_results])
            all_bm25_ranks.append([r[0] for r in bm25_results])

        # Fusión RRF
        vec_rrf  = _rrf(all_vec_ranks)
        bm25_rrf = _rrf(all_bm25_ranks)

        # Combinar scores (60% vector, 40% BM25)
        all_ids = set(vec_rrf) | set(bm25_rrf)
        combined = {
            cid: 0.6 * vec_rrf.get(cid, 0) + 0.4 * bm25_rrf.get(cid, 0)
            for cid in all_ids
        }

        # Top candidatos (child chunks)
        top_ids = sorted(combined, key=lambda x: combined[x], reverse=True)[:top_k * 2]

        # Recuperar parent chunks
        seen_parents = set()
        candidates = []
        for cid in top_ids:
            chunk = next((c for c in self._chunks if c["id"] == cid), None)
            if chunk:
                pid = chunk.get("parent_id", cid)
                if pid not in seen_parents:
                    seen_parents.add(pid)
                    parent = self._parents.get(pid, chunk)
                    candidates.append({
                        "id": pid,
                        "text": parent.get("text", chunk["text"]),
                        "source": chunk.get("source", "Desconocido"),
                        "page": chunk.get("page", 0),
                        "score": combined[cid],
                    })

        # Re-ranking con CrossEncoder
        reranker = self._get_reranker()
        if reranker and len(candidates) > 1:
            pairs = [(query, c["text"][:768]) for c in candidates]
            try:
                rerank_scores = reranker.predict(pairs)
                for i, c in enumerate(candidates):
                    c["rerank_score"] = float(rerank_scores[i])
                candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            except Exception as e:
                log.warning(f"Re-ranking falló: {e}")

        return candidates[:top_k]

    # ── Construcción del contexto ─────────────────────────────────────────────

    def build_context(self, results: List[Dict], max_tokens: int = 2048) -> str:
        """Construye el bloque de contexto para el prompt."""
        parts = []
        total = 0
        for r in results:
            snippet = r["text"][:1200]  # ~300 tokens aprox
            token_est = len(snippet.split())
            if total + token_est > max_tokens:
                break
            parts.append(
                f"[Fuente: {r['source']}, pág. {r['page']}]\n{snippet}"
            )
            total += token_est
        return "\n\n---\n\n".join(parts)