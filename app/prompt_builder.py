"""
prompt_builder.py — Prompts ESL (English as Second Language)
Tutor de inglés básico: responde en español, enseña en inglés.
Niveles A1-B2 del Marco Común Europeo.
"""

import logging
from typing import Dict, Optional

log = logging.getLogger("prompts")

import json
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Carga dinámica de prompts desde archivos externos
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"

SUBJECT_CONFIGS: Dict[str, Dict] = {}
LEVEL_INSTRUCTIONS: Dict[str, str] = {}
PEDAGOGICAL_MODES: Dict[str, str] = {}

def _load_prompts():
    """Carga los prompts desde /prompts/ en disco, o usa fallbacks si no existen."""
    # 1. Subjects
    subj_dir = PROMPTS_DIR / "subjects"
    if subj_dir.exists():
        for f in subj_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    SUBJECT_CONFIGS[f.stem] = json.load(file)
            except Exception as e:
                log.error(f"Error cargando subject {f.name}: {e}")
    
    # Fallback si no hay ninguno
    if not SUBJECT_CONFIGS:
        SUBJECT_CONFIGS["general_english"] = {
            "name": "English Mentor", "area": "inglés general",
            "style": "amigable", "technique": "ejemplos sencillos",
            "verify_q": "¿Entendiste?"
        }

    # 2. Levels
    levels_file = PROMPTS_DIR / "levels" / "levels.json"
    if levels_file.exists():
        try:
            with open(levels_file, "r", encoding="utf-8") as file:
                LEVEL_INSTRUCTIONS.update(json.load(file))
        except Exception as e:
            log.error(f"Error cargando levels: {e}")
    
    if not LEVEL_INSTRUCTIONS:
        LEVEL_INSTRUCTIONS["intermediate"] = "Nivel intermedio."

    # 3. Modes
    modes_file = PROMPTS_DIR / "modes" / "modes.json"
    if modes_file.exists():
        try:
            with open(modes_file, "r", encoding="utf-8") as file:
                PEDAGOGICAL_MODES.update(json.load(file))
        except Exception as e:
            log.error(f"Error cargando modes: {e}")
    
    if not PEDAGOGICAL_MODES:
        PEDAGOGICAL_MODES["normal"] = ""

# Ejecutar carga inicial
_load_prompts()


# ─────────────────────────────────────────────────────────────────────────────
# Constructores
# ─────────────────────────────────────────────────────────────────────────────

def build_system_prompt(subject: str = "general_english",
                        level: str = "intermediate",
                        mode: str = "normal",
                        extra_rules: Optional[str] = None) -> str:
    cfg        = SUBJECT_CONFIGS.get(subject, SUBJECT_CONFIGS["general_english"])
    level_inst = LEVEL_INSTRUCTIONS.get(level, LEVEL_INSTRUCTIONS["intermediate"])
    mode_inst  = PEDAGOGICAL_MODES.get(mode, "")

    prompt = f"""Eres {cfg['name']}, un tutor especializado en {cfg['area']}.
Tu conocimiento proviene EXCLUSIVAMENTE de los documentos cargados en tu base de conocimientos.

━━━ IDIOMA DE RESPUESTA ━━━
Responde SIEMPRE en español, pero enseña y muestra ejemplos en inglés.
Esta regla es ABSOLUTA: el estudiante aprende inglés pero aún no lo domina.

━━━ ESTILO PEDAGÓGICO ━━━
Estilo: {cfg['style']}.
Técnica: {cfg['technique']}.

━━━ NIVEL DEL ESTUDIANTE ━━━
{level_inst}

━━━ REGLAS OBLIGATORIAS ━━━
1. FALLBACK — úsalo SOLO si la pregunta es completamente ajena al inglés o a la enseñanza
   de idiomas (deportes, política, programación, noticias, etc.).
   En ese caso responde exactamente:
   "No tengo información suficiente sobre eso en mi base de conocimientos. Te recomiendo consultar otras fuentes."
   Si la pregunta ES sobre inglés (gramática, vocabulario, pronunciación, escritura,
   lectura, conversación), SIEMPRE intenta responder con lo que sabes del contexto.
   NUNCA uses el fallback para preguntas de inglés, aunque el contexto sea escaso.
2. Cita la fuente al final: "Fuente: [nombre del documento], pág. [N]"
3. Corrige errores del estudiante con amabilidad, nunca de forma abrupta.
4. Al final de cada respuesta incluye la pregunta de verificación:
   "{cfg['verify_q']}"
5. No menciones que eres una IA ni que tienes limitaciones técnicas.
6. Nunca inventes información que no esté en el contexto. Si no tienes datos exactos
   (como una pronunciación IPA específica), describe el concepto con lo que sí sabes.{mode_inst}"""

    if extra_rules:
        prompt += f"\n\n━━━ REGLAS ADICIONALES ━━━\n{extra_rules}"

    return prompt


def build_full_prompt(system_prompt: str, context: str,
                      memory_block: str, student_profile: str,
                      query: str) -> str:
    parts = [system_prompt]

    if student_profile:
        parts.append(f"\n━━━ PERFIL DEL ESTUDIANTE ━━━\n{student_profile}")
    if memory_block:
        parts.append(f"\n━━━ HISTORIAL DE SESIÓN ━━━\n{memory_block}")
    if context:
        parts.append(f"\n━━━ DOCUMENTOS RELEVANTES (usa solo esta información) ━━━\n{context}")
    else:
        parts.append("\n[No se encontraron documentos relevantes para esta consulta.]")

    parts.append(f"\n━━━ PREGUNTA DEL ESTUDIANTE ━━━\n{query}")
    parts.append("\nTutor:")

    return "\n".join(parts)


def list_subjects() -> list:
    return list(SUBJECT_CONFIGS.keys())