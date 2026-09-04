"""
ingester.py — Pipeline de Ingesta Automática de Documentos
Detecta archivos nuevos/modificados en /knowledge, los procesa y actualiza
el índice vectorial y BM25 en /database.
Soporta: PDF, TXT, MD, DOCX
"""

import json
import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import numpy as np

log = logging.getLogger("ingester")

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}
CHILD_TOKENS  = 128   # tokens por child chunk (búsqueda)
PARENT_TOKENS = 1024  # tokens por parent chunk (contexto al modelo)
OVERLAP       = 32    # overlap entre child chunks


def _estimate_tokens(text: str) -> int:
    """Estimación simple: 1 token ≈ 4 caracteres."""
    return max(1, len(text) // 4)


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Divide texto en chunks por palabras con overlap."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size * 4]  # aprox palabras para chunk_size tokens
        chunk = " ".join(chunk_words)
        if chunk.strip():
            chunks.append(chunk)
        i += max(1, chunk_size * 4 - overlap * 4)
    return chunks


def _clean_text(text: str) -> str:
    """Limpieza básica de texto extraído."""
    text = re.sub(r'\s+', ' ', text)           # normalizar espacios
    text = re.sub(r'[\x00-\x08\x0b-\x1f]', '', text)  # control chars
    text = re.sub(r'\.{3,}', '…', text)        # puntos suspensivos
    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Extractores por tipo de archivo
# ─────────────────────────────────────────────────────────────────────────────

def extract_pdf(path: Path) -> List[Dict]:
    """Extrae texto de un PDF página por página."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(path))
        pages = []
        for i, page in enumerate(doc):
            text = _clean_text(page.get_text())
            if text:
                pages.append({"page": i + 1, "text": text})
        doc.close()
        return pages
    except ImportError:
        log.warning("PyMuPDF no disponible. Intentando con pdfplumber…")
        try:
            import pdfplumber
            pages = []
            with pdfplumber.open(str(path)) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = _clean_text(page.extract_text() or "")
                    if text:
                        pages.append({"page": i + 1, "text": text})
            return pages
        except ImportError:
            log.error("No hay extractor PDF disponible (PyMuPDF o pdfplumber).")
            return []


def extract_text(path: Path) -> List[Dict]:
    """Extrae texto de archivos TXT o MD."""
    try:
        text = _clean_text(path.read_text(encoding="utf-8", errors="ignore"))
        return [{"page": 1, "text": text}]
    except Exception as e:
        log.error(f"Error leyendo {path.name}: {e}")
        return []


def extract_docx(path: Path) -> List[Dict]:
    """Extrae texto de un archivo DOCX."""
    try:
        from docx import Document
        doc = Document(str(path))
        text = _clean_text("\n".join(p.text for p in doc.paragraphs))
        return [{"page": 1, "text": text}]
    except ImportError:
        log.warning("python-docx no disponible. DOCX omitido.")
        return []


EXTRACTORS = {
    ".pdf":  extract_pdf,
    ".txt":  extract_text,
    ".md":   extract_text,
    ".docx": extract_docx,
}


# ─────────────────────────────────────────────────────────────────────────────
# Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class Ingester:
    """
    Detecta documentos nuevos o modificados en /knowledge y los indexa.
    Mantiene un registro de hashes para evitar re-procesar archivos sin cambios.
    """

    def __init__(self, know_dir: Path, db_dir: Path, embedder=None):
        self.know_dir  = know_dir
        self.db_dir    = db_dir
        self.staging   = db_dir / "staging"
        self.hash_file = db_dir / "file_hashes.json"
        self._embedder = embedder  # embedder compartido para evitar doble carga
        self._get_embedder_cb = None # callback para lazy loading
        self._raw_chunks : List[Dict] = []
        self._hashes: Dict[str, str] = {}
        self._load_hashes()

    def _rel_path(self, path: Path) -> str:
        """Convierte path absoluto a relativo respecto a know_dir."""
        try:
            return str(path.relative_to(self.know_dir))
        except ValueError:
            return str(path)

    def _load_hashes(self):
        if self.hash_file.exists():
            with open(self.hash_file, encoding="utf-8") as f:
                raw = json.load(f)
            # Migración automática: convertir rutas absolutas a relativas
            migrated = {}
            for k, v in raw.items():
                p = Path(k)
                if p.is_absolute():
                    try:
                        rel = str(p.relative_to(self.know_dir))
                    except ValueError:
                        # La ruta absoluta no pertenece a know_dir (USB cambió de letra)
                        # Intentar extraer solo el nombre del archivo
                        rel = p.name
                    migrated[rel] = v
                else:
                    migrated[k] = v
            self._hashes = migrated

    def _save_hashes(self):
        with open(self.hash_file, "w", encoding="utf-8") as f:
            json.dump(self._hashes, f, indent=2, ensure_ascii=False)

    def _file_hash(self, path: Path) -> str:
        h = hashlib.md5()
        h.update(path.read_bytes())
        return h.hexdigest()

    def _find_new_files(self) -> List[Path]:
        new_files = []
        for ext in SUPPORTED_EXTENSIONS:
            for f in self.know_dir.rglob(f"*{ext}"):
                fhash = self._file_hash(f)
                rel_key = self._rel_path(f)
                if self._hashes.get(rel_key) != fhash:
                    new_files.append(f)
        return new_files

    def run(self):
        """Detecta y procesa archivos nuevos/modificados."""
        new_files = self._find_new_files()
        if not new_files:
            log.info("No hay documentos nuevos para indexar.")
            return

        log.info(f"Documentos a indexar: {len(new_files)}")
        for f in new_files:
            log.info(f"  → Procesando: {f.name}")
            self._process_file(f)
            self._hashes[self._rel_path(f)] = self._file_hash(f)

        self._save_hashes()
        self._rebuild_index()
        log.info("Indexación completada.")

    def _process_file(self, path: Path):
        """Extrae texto, genera chunks y los guarda en staging."""
        extractor = EXTRACTORS.get(path.suffix.lower())
        if not extractor:
            return

        pages = extractor(path)
        if not pages:
            log.warning(f"Sin texto extraído de {path.name}")
            return

        staging_file = self.db_dir / "staging" / f"{path.stem}.json"
        staging_file.parent.mkdir(exist_ok=True)

        staged_chunks   = []
        staged_parents  = {}

        for page_data in pages:
            page_text = page_data["text"]
            page_num  = page_data["page"]

            # Parent chunks (1024 tokens)
            parent_chunks = _chunk_text(page_text, PARENT_TOKENS, overlap=0)
            for pi, parent_text in enumerate(parent_chunks):
                parent_id = f"{path.stem}_p{page_num}_{pi}"
                staged_parents[parent_id] = {
                    "id":     parent_id,
                    "text":   parent_text,
                    "source": path.name,
                    "page":   page_num,
                }

                # Child chunks (128 tokens) dentro del parent
                child_chunks = _chunk_text(parent_text, CHILD_TOKENS, OVERLAP)
                for ci, child_text in enumerate(child_chunks):
                    child_id = f"{parent_id}_c{ci}"
                    staged_chunks.append({
                        "id":        child_id,
                        "parent_id": parent_id,
                        "text":      child_text,
                        "source":    path.name,
                        "page":      page_num,
                    })

        with open(staging_file, "w", encoding="utf-8") as f:
            json.dump({"chunks": staged_chunks, "parents": staged_parents},
                      f, ensure_ascii=False, indent=2)

        log.info(f"    {path.name}: {len(staged_chunks)} child chunks, "
                 f"{len(staged_parents)} parent chunks")

    def _rebuild_index(self):
        """
        Consolida todos los archivos staged en un único índice y genera embeddings.
        """
        all_chunks: List[Dict]       = []
        all_parents: Dict[str, Dict] = {}

        staging_dir = self.db_dir / "staging"
        staging_dir.mkdir(parents=True, exist_ok=True)
        staged_files = list(staging_dir.glob("*.json"))

        if not staged_files:
            log.warning("staging/ vacío: no hay documentos indexados aún.")
            return

        for staged_file in staged_files:
            with open(staged_file, encoding="utf-8") as f:
                data = json.load(f)
            all_chunks.extend(data["chunks"])
            all_parents.update(data["parents"])

        # Guardar chunks y parents
        chunks_file  = self.db_dir / "chunks.json"
        parents_file = self.db_dir / "parents.json"
        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        with open(parents_file, "w", encoding="utf-8") as f:
            json.dump(all_parents, f, ensure_ascii=False, indent=2)

        # Generar embeddings
        self._generate_embeddings(all_chunks)
        log.info(f"Índice consolidado: {len(all_chunks)} chunks totales.")

    def _generate_embeddings(self, chunks: List[Dict]):
        """Genera y guarda embeddings para todos los child chunks."""
        try:
            # Reusar embedder externo si está disponible (evita doble carga)
            if self._embedder is not None:
                embedder = self._embedder
                log.info("Generando embeddings… (usando embedder compartido)")
            elif self._get_embedder_cb is not None:
                embedder = self._get_embedder_cb()
                log.info("Generando embeddings... (usando callback compartido)")
            else:
                from sentence_transformers import SentenceTransformer
                log.info("Generando embeddings… (esto puede tardar varios minutos la primera vez)")
                embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            texts = [c["text"] for c in chunks]
            batch_size = 64
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embs  = embedder.encode(batch, convert_to_numpy=True,
                                        show_progress_bar=False)
                all_embeddings.extend(embs)
                log.info(f"  Embeddings: {min(i + batch_size, len(texts))}/{len(texts)}")

            emb_array = np.array(all_embeddings, dtype=np.float32)
            np.save(str(self.db_dir / "embeddings.npy"), emb_array)
            log.info(f"Embeddings guardados: {emb_array.shape}")
        except ImportError:
            log.error("sentence-transformers no disponible. Sin embeddings vectoriales.")