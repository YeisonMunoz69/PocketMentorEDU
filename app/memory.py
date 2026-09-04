"""
memory.py — Memoria de sesión ESL
Señales de nivel adaptadas a English as Second Language.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

log = logging.getLogger("memory")

WINDOW_SIZE    = 5
SUMMARY_TOKENS = 200

# ── Señales de nivel ESL ──────────────────────────────────────────────────────
LEVEL_SIGNALS = {
    "advanced": [
        # inglés
        "subjunctive", "passive voice", "phrasal verb", "idiom", "connotation",
        "nuance", "conditional", "inversion", "collocation", "discourse",
        "register", "syntax", "morphology", "gerund", "infinitive clause",
        # español
        "voz pasiva", "subjuntivo", "modismo", "connotación", "registro formal",
        "frase preposicional", "cláusula", "sintaxis",
    ],
    "basic": [
        # inglés
        "what does", "how do you say", "what is", "i don't understand",
        "what means", "how to pronounce", "translate", "simple",
        "beginning", "don't know", "confused",
        # español
        "cómo se dice", "qué significa", "no entiendo", "qué quiere decir",
        "cómo se pronuncia", "desde el principio", "en palabras simples",
        "no sé", "para qué sirve", "qué es",
    ],
}


def detect_level_from_text(text: str) -> Optional[str]:
    t = text.lower()
    adv = sum(1 for kw in LEVEL_SIGNALS["advanced"] if kw in t)
    bas = sum(1 for kw in LEVEL_SIGNALS["basic"]    if kw in t)
    if adv >= 2: return "advanced"
    if bas >= 2: return "basic"
    return None


# ─────────────────────────────────────────────────────────────────────────────
class SessionMemory:

    def __init__(self, sess_dir: Path, user_id: str = "default"):
        self.sess_dir     = sess_dir
        self.user_id      = user_id
        self.profile_path = sess_dir / f"{user_id}_profile.json"
        self._history: List[Dict] = []
        self._summary: str = ""
        self._turn_count: int = 0
        self._profile: Dict = self._load_profile()

    # ── Perfil persistente ────────────────────────────────────────────────────

    def _load_profile(self) -> Dict:
        if self.profile_path.exists():
            try:
                with open(self.profile_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "user_id":        self.user_id,
            "level":          "intermediate",
            "subject":        "general_english",
            "topics_visited": [],
            "correct_streak": 0,
            "error_streak":   0,
            "total_turns":    0,
            "created_at":     datetime.now().isoformat(),
        }

    def _save_profile(self):
        try:
            self.sess_dir.mkdir(parents=True, exist_ok=True)
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(self._profile, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.warning(f"No se pudo guardar perfil: {e}")

    # ── Propiedades ───────────────────────────────────────────────────────────

    @property
    def level(self) -> str:
        return self._profile.get("level", "intermediate")

    @level.setter
    def level(self, v: str):
        self._profile["level"] = v

    @property
    def subject(self) -> str:
        return self._profile.get("subject", "general_english")

    @subject.setter
    def subject(self, v: str):
        self._profile["subject"] = v

    # ── Gestión de turnos ─────────────────────────────────────────────────────

    def add_turn(self, role: str, content: str, llm=None):
        self._history.append({"role": role, "content": content})
        if role == "user":
            self._turn_count += 1
            self._profile["total_turns"] = self._profile.get("total_turns", 0) + 1
            detected = detect_level_from_text(content)
            if detected:
                self._profile["level"] = detected
                log.debug(f"Nivel detectado automáticamente: {detected}")
        if len(self._history) > WINDOW_SIZE * 2:
            self._compress(llm)
        self._save_profile()

    def _compress(self, llm=None):
        old = self._history[:-WINDOW_SIZE * 2]
        self._history = self._history[-WINDOW_SIZE * 2:]
        if llm:
            try:
                snippet = " | ".join(
                    f"{t['role']}: {t['content'][:80]}" for t in old[:6])
                resp = llm(
                    f"Resume en máximo 3 líneas esta conversación de inglés:\n{snippet}\nResumen:",
                    max_tokens=80, temperature=0.1, echo=False)
                self._summary = resp["choices"][0]["text"].strip()
                return
            except Exception:
                pass
        self._summary = f"[{len(old)//2} turnos anteriores sobre {self.subject}]"

    def add_topic(self, topic: str):
        topics = self._profile.setdefault("topics_visited", [])
        if topic not in topics:
            topics.append(topic)
        if len(topics) > 20:
            self._profile["topics_visited"] = topics[-20:]

    def reset_session(self):
        self._history = []
        self._summary = ""
        self._turn_count = 0
        self._save_profile()

    # ── Bloques de contexto ───────────────────────────────────────────────────

    def build_memory_block(self) -> str:
        parts = []
        if self._summary:
            parts.append(f"[Resumen previo: {self._summary}]")
        for t in self._history[-WINDOW_SIZE * 2:]:
            label = "Estudiante" if t["role"] == "user" else "Tutor"
            parts.append(f"{label}: {t['content'][:300]}")
        return "\n".join(parts)

    def build_student_profile_block(self) -> str:
        p = self._profile
        topics = ", ".join(p.get("topics_visited", [])[-5:]) or "ninguno aún"
        return (
            f"Nivel CEFR: {p.get('level','intermediate')} | "
            f"Área: {p.get('subject','general_english')} | "
            f"Temas visitados: {topics} | "
            f"Turnos totales: {p.get('total_turns',0)}"
        )