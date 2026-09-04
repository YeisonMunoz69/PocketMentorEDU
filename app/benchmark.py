"""
benchmark.py — Evaluación comparativa de configuraciones para artículo académico
Uso: python benchmark.py [--questions preguntas.json] [--output resultados/]
     python benchmark.py --quick   (5 preguntas, configuraciones reducidas)
"""

import sys
import json
import time
import csv
import logging
import argparse
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "app"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("benchmark")


# ─────────────────────────────────────────────────────────────────────────────
# PREGUNTAS DE BENCHMARK — alineadas a "College ESL Writers" (Hall & Wallace, 2018)
# Cada pregunta referencia la sección exacta del libro donde está la respuesta.
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_QUESTIONS = [

    # ── GRAMMAR ──────────────────────────────────────────────────────────────

    # Ch7 §7.4 — Count/Noncount Nouns & Articles (págs. 191-197)
    {   "id": "G1", "area": "grammar", "level": "basic",
        "text": "¿Cuándo se usa 'a' y cuándo 'an' en inglés? ¿Qué son los count nouns?",
        "expected_keywords": ["vowel", "consonant", "count", "noncount", "article", "indefinite"],
        "source_page": "191-197",
    },

    # Ch7 §7.8 — Simple Present vs Present Progressive (págs. 214-220)
    {   "id": "G2", "area": "grammar", "level": "intermediate",
        "text": "¿Cuál es la diferencia entre el simple present y el present progressive en inglés?",
        "expected_keywords": ["habit", "routine", "now", "happening", "currently", "action"],
        "source_page": "214-220",
    },

    # Ch7 §7.8 — Perfect tenses (págs. 220-227)
    {   "id": "G3", "area": "grammar", "level": "advanced",
        "text": "¿Qué es el present perfect y cómo se diferencia del simple past?",
        "expected_keywords": ["have", "has", "past participle", "experience", "recently", "already"],
        "source_page": "220-227",
    },

    # Ch7 §7.9 — Modal auxiliaries (págs. 228-235)
    {   "id": "G4", "area": "grammar", "level": "intermediate",
        "text": "¿Para qué sirven los modal auxiliaries en inglés? Da ejemplos de 'can', 'should' y 'must'.",
        "expected_keywords": ["modal", "auxiliary", "ability", "possibility", "obligation", "main verb"],
        "source_page": "228-235",
    },

    # ── VOCABULARY / WORD USAGE ───────────────────────────────────────────────

    # Ch6 §6.1 — Commonly Confused Words (págs. 139-150)
    {   "id": "V1", "area": "vocabulary", "level": "intermediate",
        "text": "¿Cuál es la diferencia entre 'affect' y 'effect' en inglés?",
        "expected_keywords": ["affect", "effect", "verb", "noun", "confused", "usage"],
        "source_page": "139-150",
    },

    # Ch2 §2.2 — Conjunctive Adverbs / Transitions (págs. 36-42)
    {   "id": "V2", "area": "vocabulary", "level": "intermediate",
        "text": "¿Qué son los conjunctive adverbs y cómo se usan para conectar ideas en inglés?",
        "expected_keywords": ["however", "therefore", "furthermore", "semicolon", "transition", "connect"],
        "source_page": "36-42",
    },

    # Ch2 §2.4 — Parallelism (págs. 61-67)
    {   "id": "V3", "area": "vocabulary", "level": "advanced",
        "text": "¿Qué es el parallelism en inglés y por qué es importante en la escritura?",
        "expected_keywords": ["parallel", "balanced", "structure", "series", "consistent", "grammar"],
        "source_page": "61-67",
    },

    # ── WRITING ───────────────────────────────────────────────────────────────

    # Ch3 §3.1 — Topic sentence & paragraph structure (págs. 68-75)
    {   "id": "W1", "area": "writing", "level": "basic",
        "text": "¿Cómo se estructura un párrafo en inglés? ¿Qué es el topic sentence?",
        "expected_keywords": ["topic sentence", "body", "conclusion", "main idea", "paragraph", "support"],
        "source_page": "68-75",
    },

    # Ch4 §4.3 — Thesis statement (págs. 97-108)
    {   "id": "W2", "area": "writing", "level": "intermediate",
        "text": "¿Qué es una thesis statement y qué características debe tener?",
        "expected_keywords": ["thesis", "arguable", "specific", "claim", "essay", "focus"],
        "source_page": "97-108",
    },

    # Ch5 §5.1 — Revising vs Editing (págs. 120-138)
    {   "id": "W3", "area": "writing", "level": "advanced",
        "text": "¿Cuál es la diferencia entre revising y editing al escribir un ensayo en inglés?",
        "expected_keywords": ["revising", "editing", "content", "structure", "grammar", "draft"],
        "source_page": "120-138",
    },

    # ── READING / SENTENCE STRUCTURE ─────────────────────────────────────────

    # Ch1 §1.1 — Sentence components (págs. 15-19)
    {   "id": "R1", "area": "reading", "level": "basic",
        "text": "¿Cuáles son los componentes básicos de una oración (sentence) en inglés?",
        "expected_keywords": ["subject", "verb", "object", "complete", "sentence", "predicate"],
        "source_page": "15-19",
    },

    # Ch2 §2.3 — Sentence fragments (págs. 49-60)
    {   "id": "R2", "area": "reading", "level": "intermediate",
        "text": "¿Qué es un sentence fragment y cómo se puede corregir?",
        "expected_keywords": ["fragment", "incomplete", "subject", "verb", "dependent", "clause"],
        "source_page": "49-60",
    },

    # ── FALLBACK (preguntas fuera del corpus) ─────────────────────────────────
    {   "id": "F1", "area": "general_english", "level": "intermediate",
        "text": "¿Quién ganó el último campeonato mundial de fútbol?",
        "expected_keywords": [],
        "expect_fallback": True,
        "source_page": "N/A",
    },
    {   "id": "F2", "area": "grammar", "level": "basic",
        "text": "¿Cómo programo una aplicación en Python usando inteligencia artificial?",
        "expected_keywords": [],
        "expect_fallback": True,
        "source_page": "N/A",
    },
]

# Modo rápido: cubre gramática básica, vocabulario, escritura y fallback
QUICK_QUESTIONS = [q for q in DEFAULT_QUESTIONS
                   if q["id"] in ("G1", "G2", "V2", "W1", "W2", "F1")]


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIONES A COMPARAR
# ─────────────────────────────────────────────────────────────────────────────

CONFIGURATIONS = [
    # ID           temperature  top_p   repeat_p  max_tokens  top_k_rag  eval_mode
    ("cfg_conservative", 0.1,  0.85,    1.1,      512,        3,         "fast"),
    ("cfg_balanced",     0.3,  0.90,    1.1,      512,        5,         "fast"),
    ("cfg_default",      0.4,  0.90,    1.1,      512,        5,         "fast"),
    ("cfg_creative",     0.7,  0.95,    1.05,     512,        7,         "fast"),
    ("cfg_high_recall",  0.3,  0.90,    1.1,      512,        10,        "fast"),
    ("cfg_long_ans",     0.3,  0.90,    1.1,      800,        5,         "fast"),
    # Con evaluador full (embeddings) — solo en modo completo para comparar latencia
    ("cfg_eval_full",    0.3,  0.90,    1.1,      512,        5,         "full"),
]

QUICK_CONFIGURATIONS = [
    ("cfg_conservative", 0.1, 0.85, 1.1, 512, 3,  "fast"),
    ("cfg_default",      0.4, 0.90, 1.1, 512, 5,  "fast"),
    ("cfg_creative",     0.7, 0.95, 1.05,512, 7,  "fast"),
]


# ─────────────────────────────────────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────────────────────────────────────

class BenchmarkRunner:

    def __init__(self, llm, rag, evaluator, output_dir: Path):
        self.llm       = llm
        self.rag       = rag
        self.evaluator = evaluator
        self.out       = output_dir
        self.out.mkdir(parents=True, exist_ok=True)
        self.results: List[Dict] = []

    def _generate(self, prompt: str, temperature: float, top_p: float,
                  repeat_penalty: float, max_tokens: int) -> tuple:
        """Retorna (texto, tokens_generados, tiempo_segundos)."""
        t0 = time.perf_counter()
        try:
            r = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                repeat_penalty=repeat_penalty,
                echo=False,
                stop=["Estudiante:", "━━━", "\n\nTutor:", "Human:",
                      "\nFuente:", "\n---", "[Fuente:", "---\n"],
            )
            elapsed = time.perf_counter() - t0
            text    = r["choices"][0]["text"].strip()
            tokens  = r["usage"]["completion_tokens"]
            return text, tokens, elapsed
        except Exception as e:
            elapsed = time.perf_counter() - t0
            log.error(f"Inferencia error: {e}")
            return "", 0, elapsed

    def run_single(self, question: Dict, cfg: tuple) -> Dict:
        (cfg_id, temperature, top_p, repeat_p, max_tokens, top_k, eval_mode) = cfg
        from prompt_builder import build_system_prompt, build_full_prompt

        self.evaluator.set_mode(eval_mode)

        # ── RAG ───────────────────────────────────────────────────────────────
        t_rag0 = time.perf_counter()
        results = self.rag.hybrid_search(question["text"], top_k=top_k, llm=self.llm)
        t_rag   = time.perf_counter() - t_rag0

        context = self.rag.build_context(results)

        # ── Prompt ────────────────────────────────────────────────────────────
        prompt = build_full_prompt(
            system_prompt=build_system_prompt(
                subject=question["area"],
                level=question["level"],
                mode="normal",
            ),
            context=context,
            memory_block="",
            student_profile=f"Nivel: {question['level']} | Área: {question['area']}",
            query=question["text"],
        )

        # ── Generación ────────────────────────────────────────────────────────
        response, tokens, t_gen = self._generate(
            prompt, temperature, top_p, repeat_p, max_tokens)

        # ── Evaluación ────────────────────────────────────────────────────────
        t_eval0 = time.perf_counter()
        ev = self.evaluator.evaluate(
            query=question["text"],
            response=response,
            context_chunks=results,
            student_level=question["level"],
        )
        t_eval = time.perf_counter() - t_eval0

        # ── Keywords encontradas ──────────────────────────────────────────────
        resp_lower = response.lower()
        kw_found   = [k for k in question.get("expected_keywords", []) if k in resp_lower]
        kw_total   = len(question.get("expected_keywords", []))
        kw_score   = (len(kw_found) / kw_total) if kw_total > 0 else None

        # ── Fallback correctness ──────────────────────────────────────────────
        expect_fb  = question.get("expect_fallback", False)
        got_fb     = ev.get("is_fallback", False)
        fb_correct = (expect_fb == got_fb) if expect_fb else None

        tokens_per_sec = tokens / t_gen if t_gen > 0 else 0

        record = {
            "config_id":       cfg_id,
            "question_id":     question["id"],
            "area":            question["area"],
            "level":           question["level"],
            # Parámetros
            "temperature":     temperature,
            "top_p":           top_p,
            "repeat_penalty":  repeat_p,
            "max_tokens":      max_tokens,
            "top_k_rag":       top_k,
            "eval_mode":       eval_mode,
            # Tiempos
            "t_rag_s":         round(t_rag,  3),
            "t_gen_s":         round(t_gen,  3),
            "t_eval_s":        round(t_eval, 3),
            "t_total_s":       round(t_rag + t_gen + t_eval, 3),
            # Calidad
            "overall_score":   ev.get("overall_score", 0),
            "grounding_score": ev.get("grounding_score", 0),
            "relevance_score": ev.get("relevance_score", 0),
            "passed":          ev.get("pass", False),
            "is_fallback":     got_fb,
            "fallback_correct":fb_correct,
            # Tokens
            "tokens_generated":tokens,
            "tokens_per_sec":  round(tokens_per_sec, 2),
            # Cobertura de keywords
            "kw_score":        round(kw_score, 3) if kw_score is not None else None,
            "kw_found":        ", ".join(kw_found),
            # Respuesta (primeras 300 chars)
            "response_preview":response[:300].replace("\n", " "),
            "chunks_retrieved":len(results),
            "timestamp":       datetime.now().isoformat(),
            # ── Trazabilidad para auditoria del evaluador (LHXT 2026) ─────────
            "level_score":     ev.get("level_score"),
            "response_full":   response,
            "prompt_chars":    len(prompt),
            "context_chunks":  [
                {
                    "rank":   i + 1,
                    "text":   c.get("text", ""),
                    "source": c.get("source") or c.get("metadata", {}).get("source"),
                    "page":   c.get("page") or c.get("metadata", {}).get("page"),
                    "score":  c.get("score"),
                }
                for i, c in enumerate(results)
            ],
        }
        return record

    def run_all(self, questions: List[Dict], configs: List[tuple]):
        total = len(questions) * len(configs)
        done  = 0
        log.info(f"Iniciando benchmark: {len(questions)} preguntas × {len(configs)} configs = {total} ejecuciones")
        log.info(f"Tiempo estimado: {total * 60 // 60} - {total * 90 // 60} minutos (depende del hardware)")
        print()

        for ci, cfg in enumerate(configs):
            cfg_id = cfg[0]
            log.info(f"[{ci+1}/{len(configs)}] Configuración: {cfg_id} "
                     f"(temp={cfg[1]}, top_k={cfg[5]}, eval={cfg[6]})")

            for qi, q in enumerate(questions):
                done += 1
                pct = done / total * 100
                log.info(f"  [{done}/{total} {pct:.0f}%] Q{q['id']} — {q['text'][:55]}…")

                try:
                    record = self.run_single(q, cfg)
                    self.results.append(record)
                    log.info(f"    score={record['overall_score']:.2f} | "
                             f"rag={record['t_rag_s']:.1f}s | "
                             f"gen={record['t_gen_s']:.1f}s | "
                             f"tok/s={record['tokens_per_sec']:.1f}")
                except Exception as e:
                    log.error(f"  ERROR en {cfg_id}/{q['id']}: {e}")
                    continue

            print()

        log.info(f"Benchmark completo. {len(self.results)} resultados.")

    def save(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # ── CSV completo ──────────────────────────────────────────────────────
        csv_path = self.out / f"benchmark_{ts}.csv"
        # Las columnas largas (respuesta completa y fragmentos) solo van al JSON:
        # en el CSV romperian la lectura tabular.
        CSV_SKIP = ("response_full", "context_chunks")
        if self.results:
            fields = [k for k in self.results[0].keys() if k not in CSV_SKIP]
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(self.results)
            log.info(f"CSV: {csv_path}")

        # ── JSON completo ─────────────────────────────────────────────────────
        json_path = self.out / f"benchmark_{ts}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"results": self.results, "summary": self._summary()},
                      f, indent=2, ensure_ascii=False)
        log.info(f"JSON: {json_path}")

        # ── Tabla resumen para el artículo ────────────────────────────────────
        summary_path = self.out / f"summary_{ts}.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(self._format_article_table())
        log.info(f"Tabla artículo: {summary_path}")

        return csv_path, json_path, summary_path

    def _summary(self) -> Dict:
        """Estadísticas por configuración — listo para el artículo."""
        by_cfg: Dict[str, List[Dict]] = {}
        for r in self.results:
            by_cfg.setdefault(r["config_id"], []).append(r)

        summary = {}
        for cfg_id, rows in by_cfg.items():
            scores    = [r["overall_score"]  for r in rows]
            rag_times = [r["t_rag_s"]        for r in rows]
            gen_times = [r["t_gen_s"]        for r in rows]
            tok_rates = [r["tokens_per_sec"] for r in rows if r["tokens_per_sec"] > 0]
            pass_rate = sum(1 for r in rows if r["passed"]) / len(rows)
            fb_correct= [r["fallback_correct"] for r in rows if r["fallback_correct"] is not None]
            kw_scores = [r["kw_score"]       for r in rows if r["kw_score"] is not None]

            summary[cfg_id] = {
                "n":                len(rows),
                "avg_score":        round(statistics.mean(scores),    3),
                "std_score":        round(statistics.stdev(scores),   3) if len(scores)>1 else 0,
                "pass_rate":        round(pass_rate,                  3),
                "avg_rag_s":        round(statistics.mean(rag_times), 3),
                "avg_gen_s":        round(statistics.mean(gen_times), 3),
                "avg_total_s":      round(statistics.mean([r["t_total_s"] for r in rows]), 3),
                "avg_tokens_per_s": round(statistics.mean(tok_rates), 2) if tok_rates else 0,
                "fallback_accuracy":round(statistics.mean([float(b) for b in fb_correct]), 3) if fb_correct else None,
                "avg_kw_coverage":  round(statistics.mean(kw_scores), 3) if kw_scores else None,
                # Param de esta config
                "temperature":      rows[0]["temperature"],
                "top_k_rag":        rows[0]["top_k_rag"],
                "eval_mode":        rows[0]["eval_mode"],
            }
        return summary

    def _format_article_table(self) -> str:
        """Genera tabla en texto plano lista para copiar al artículo."""
        summary = self._summary()
        lines = []
        lines.append("=" * 95)
        lines.append("TABLA COMPARATIVA DE CONFIGURACIONES — Pocket Mentor EDU")
        lines.append(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 95)
        lines.append("")

        # Encabezado
        h = (f"{'Config':<20} {'Temp':>5} {'TopK':>5} {'Score':>7} {'±σ':>6} "
             f"{'Pass%':>7} {'RAG(s)':>7} {'Gen(s)':>7} {'Tok/s':>7} {'KW%':>6}")
        lines.append(h)
        lines.append("-" * 95)

        # Ordenar por score descendente
        sorted_cfgs = sorted(summary.items(), key=lambda x: x[1]["avg_score"], reverse=True)
        for cfg_id, s in sorted_cfgs:
            kw = f"{s['avg_kw_coverage']*100:.0f}%" if s["avg_kw_coverage"] is not None else "  N/A"
            row = (f"{cfg_id:<20} {s['temperature']:>5.2f} {s['top_k_rag']:>5} "
                   f"{s['avg_score']:>7.3f} {s['std_score']:>6.3f} "
                   f"{s['pass_rate']*100:>6.1f}% "
                   f"{s['avg_rag_s']:>7.2f} {s['avg_gen_s']:>7.1f} "
                   f"{s['avg_tokens_per_s']:>7.1f} {kw:>6}")
            lines.append(row)

        lines.append("-" * 95)
        lines.append("")

        # Tabla por área
        lines.append("SCORES POR ÁREA ESL")
        lines.append("-" * 50)
        by_area: Dict[str, List] = {}
        for r in self.results:
            by_area.setdefault(r["area"], []).append(r["overall_score"])
        for area, scores in sorted(by_area.items()):
            lines.append(f"  {area:<20} avg={statistics.mean(scores):.3f}  "
                         f"min={min(scores):.3f}  max={max(scores):.3f}  n={len(scores)}")

        lines.append("")
        lines.append("MÉTRICAS GLOBALES")
        lines.append("-" * 50)
        all_scores = [r["overall_score"] for r in self.results]
        all_gen    = [r["t_gen_s"]       for r in self.results]
        all_tps    = [r["tokens_per_sec"] for r in self.results if r["tokens_per_sec"] > 0]
        fb_results = [r for r in self.results if r.get("expect_fallback") or r.get("is_fallback")]
        lines.append(f"  Ejecuciones totales:  {len(self.results)}")
        lines.append(f"  Score global:         {statistics.mean(all_scores):.3f} ± {statistics.stdev(all_scores):.3f}")
        lines.append(f"  Tiempo gen promedio:  {statistics.mean(all_gen):.1f}s")
        lines.append(f"  Tokens/s promedio:    {statistics.mean(all_tps):.1f}" if all_tps else "  Tokens/s:            N/A")

        lines.append("")
        lines.append("MEJOR CONFIGURACIÓN POR CRITERIO")
        lines.append("-" * 50)
        best_score = max(summary.items(), key=lambda x: x[1]["avg_score"])
        best_speed = min(summary.items(), key=lambda x: x[1]["avg_total_s"])
        best_tps   = max(summary.items(), key=lambda x: x[1]["avg_tokens_per_s"])
        lines.append(f"  Mayor score:     {best_score[0]}  ({best_score[1]['avg_score']:.3f})")
        lines.append(f"  Menor latencia:  {best_speed[0]}  ({best_speed[1]['avg_total_s']:.1f}s total)")
        lines.append(f"  Mayor tokens/s:  {best_tps[0]}   ({best_tps[1]['avg_tokens_per_s']:.1f} tok/s)")
        lines.append("")
        lines.append("=" * 95)
        return "\n".join(lines)

    def print_live_summary(self):
        """Resumen en consola al terminar."""
        print("\n" + self._format_article_table())


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Pocket Mentor EDU — Benchmark")
    parser.add_argument("--quick",     action="store_true", help="Modo rápido: 5 preguntas, 3 configs")
    parser.add_argument("--questions", type=str, default=None, help="JSON con preguntas personalizadas")
    parser.add_argument("--output",    type=str, default=None, help="Carpeta de salida")
    parser.add_argument("--configs",   type=str, default=None,
                        help="Subconjunto de configuraciones separadas por coma "
                             "(p. ej. cfg_eval_full). Por defecto: todas.")
    parser.add_argument("--seed",      type=int, default=None,
                        help="Semilla fija para la generacion. Sin ella la salida no es "
                             "reproducible.")
    parser.add_argument("--model",     type=str, default=None,
                        help="Nombre o ruta del archivo .gguf a usar (ej: Phi-4-mini-Q4_K_M.gguf). "
                             "Si no se especifica, usa el primer .gguf de /models.")
    args = parser.parse_args()

    # ── Cargar preguntas ──────────────────────────────────────────────────────
    if args.questions:
        qpath = Path(args.questions)
        if not qpath.exists():
            log.error(f"Archivo de preguntas no encontrado: {qpath}")
            sys.exit(1)
        with open(qpath, encoding="utf-8") as f:
            questions = json.load(f)
        log.info(f"Preguntas personalizadas: {len(questions)}")
    else:
        questions = QUICK_QUESTIONS if args.quick else DEFAULT_QUESTIONS

    configs = QUICK_CONFIGURATIONS if args.quick else CONFIGURATIONS
    if args.configs:
        wanted = [c.strip() for c in args.configs.split(",") if c.strip()]
        configs = [c for c in CONFIGURATIONS if c[0] in wanted]
        if not configs:
            raise SystemExit(f"Ninguna configuracion coincide con {wanted}. "
                             f"Disponibles: {[c[0] for c in CONFIGURATIONS]}")

    # out_dir se define más abajo junto al modelo, para incluir su nombre en la ruta

    log.info("=" * 60)
    log.info("  POCKET MENTOR EDU — BENCHMARK")
    log.info(f"  Modo: {'RÁPIDO' if args.quick else 'COMPLETO'}")
    log.info(f"  Preguntas: {len(questions)} | Configs: {len(configs)}")
    log.info(f"  Modelo: {args.model or '(primero en /models)'}")
    log.info("=" * 60)

    # ── Verificar dependencias ────────────────────────────────────────────────
    missing = []
    try:
        from llama_cpp import Llama
    except ImportError:
        missing.append("llama-cpp-python")
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    try:
        import sentence_transformers
    except ImportError:
        missing.append("sentence-transformers")

    if missing:
        log.error("="*60)
        log.error("DEPENDENCIAS FALTANTES: " + ", ".join(missing))
        log.error("")
        log.error("SOLUCIÓN — usa el Python del proyecto, NO el del sistema:")
        log.error("  Windows (desde la raíz del proyecto):")
        log.error("    engine/python/python.exe app/benchmark.py --quick")
        log.error("")
        log.error("  O activa el entorno primero:")
        log.error("    mentor.bat   (luego abre otra ventana y corre benchmark)")
        log.error("="*60)
        sys.exit(1)

    # ── Inicializar sistema ───────────────────────────────────────────────────
    try:
        from ingester  import Ingester
        from rag       import RAGEngine
        from evaluator import ResponseEvaluator
    except ImportError as e:
        log.error(f"Error importando módulos del sistema: {e}")
        sys.exit(1)

    know_dir = BASE_DIR / "knowledge"
    db_dir   = BASE_DIR / "database"

    log.info("Verificando índice…")
    Ingester(know_dir=know_dir, db_dir=db_dir).run()

    log.info("Cargando RAG…")
    rag = RAGEngine(db_dir=db_dir, know_dir=know_dir)

    log.info("Buscando modelo…")
    models_dir = BASE_DIR / "models"
    if args.model:
        # Puede ser nombre de archivo o ruta absoluta
        model_path = Path(args.model)
        if not model_path.is_absolute():
            model_path = models_dir / args.model
        if not model_path.exists():
            log.error(f"Modelo no encontrado: {model_path}")
            log.error(f"Modelos disponibles en /models: {[m.name for m in models_dir.glob('*.gguf')]}")
            sys.exit(1)
    else:
        models = sorted(models_dir.glob("*.gguf"))
        if not models:
            log.error("No se encontró modelo .gguf en /models")
            sys.exit(1)
        model_path = models[0]

    model_name = model_path.stem

    try:
        import psutil
        threads = max(2, psutil.cpu_count(logical=False) or 4)
    except ImportError:
        import os
        threads = max(2, os.cpu_count() or 4)
        log.warning("psutil no disponible — usando os.cpu_count()")

    log.info(f"Cargando modelo: {model_path.name} ({threads} hilos)…")
    llama_kwargs = dict(model_path=str(model_path), n_ctx=4096,
                        n_threads=threads, n_gpu_layers=0, verbose=False)
    if args.seed is not None:
        # llama-cpp-python movio 'seed' fuera del constructor en la serie 0.3.
        # Se intenta con semilla y, si la version no la acepta, se reintenta sin
        # ella dejando constancia, en lugar de abortar la corrida.
        try:
            llm = Llama(seed=args.seed, **llama_kwargs)
            log.info(f"Semilla fija: {args.seed}")
        except TypeError:
            log.warning(f"Esta version de llama-cpp-python no acepta 'seed' en el "
                        f"constructor; la corrida NO sera reproducible.")
            llm = Llama(**llama_kwargs)
    else:
        log.warning("Sin semilla fija — la generacion NO sera reproducible.")
        llm = Llama(**llama_kwargs)

    # Incluir nombre del modelo en la carpeta de salida para comparar experimentos
    if args.output:
        out_dir = Path(args.output)
    else:
        out_dir = BASE_DIR / "logs" / "benchmarks" / model_name

    evaluator = ResponseEvaluator(logs_dir=out_dir, mode="fast")
    try:
        evaluator.set_embedder(rag._get_embedder())
    except Exception:
        pass

    # ── Correr benchmark ──────────────────────────────────────────────────────
    runner = BenchmarkRunner(llm=llm, rag=rag, evaluator=evaluator, output_dir=out_dir)
    runner.run_all(questions=questions, configs=configs)

    # ── Guardar y mostrar ─────────────────────────────────────────────────────
    csv_p, json_p, summary_p = runner.save()
    runner.print_live_summary()

    print(f"\n{'='*60}")
    print(f"  Archivos generados:")
    print(f"  CSV:     {csv_p}")
    print(f"  JSON:    {json_p}")
    print(f"  Tabla:   {summary_p}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()