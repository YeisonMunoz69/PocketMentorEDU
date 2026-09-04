"""
medir_latencias.py — Medición empírica de tiempos de respuesta para artículo de arquitectura
Uso: engine\\python\\python.exe app\\medir_latencias.py
     engine\\python\\python.exe app\\medir_latencias.py --repeticiones 5

Propósito: Generar datos propios de latencia (tiempos de respuesta por fase)
para el artículo Entramado.md. NO es un benchmark de calidad — solo mide tiempos.

Salida: logs/latencia_entramado/latencia_YYYYMMDD_HHMMSS.txt
"""

import sys
import time
import logging
import argparse
import statistics
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "app"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("latencia")

# ── Preguntas representativas (3 de dificultad variada) ────────────────────
PREGUNTAS = [
    {
        "id": "L1", "area": "grammar", "level": "basic",
        "text": "¿Cuándo se usa 'a' y cuándo 'an' en inglés?",
    },
    {
        "id": "L2", "area": "writing", "level": "intermediate",
        "text": "¿Cómo se estructura un párrafo en inglés? ¿Qué es el topic sentence?",
    },
    {
        "id": "L3", "area": "vocabulary", "level": "advanced",
        "text": "¿Qué es el parallelism en inglés y por qué es importante en la escritura?",
    },
]


def medir_consulta(llm, rag, pregunta, es_primera=False):
    """Mide los tiempos de cada fase de una consulta completa."""
    from prompt_builder import build_system_prompt, build_full_prompt

    # ── Fase RAG ──────────────────────────────────────────────────────────
    t_rag0 = time.perf_counter()
    results = rag.hybrid_search(pregunta["text"], top_k=5, llm=llm)
    t_rag = time.perf_counter() - t_rag0

    context = rag.build_context(results)

    # ── Fase Prompt ───────────────────────────────────────────────────────
    prompt = build_full_prompt(
        system_prompt=build_system_prompt(
            subject=pregunta["area"],
            level=pregunta["level"],
            mode="normal",
        ),
        context=context,
        memory_block="",
        student_profile=f"Nivel: {pregunta['level']} | Área: {pregunta['area']}",
        query=pregunta["text"],
    )

    # ── Fase LLM ──────────────────────────────────────────────────────────
    t_gen0 = time.perf_counter()
    try:
        r = llm(
            prompt,
            max_tokens=512,
            temperature=0.3,
            top_p=0.90,
            repeat_penalty=1.1,
            echo=False,
            stop=["Estudiante:", "━━━", "\n\nTutor:", "Human:",
                  "\nFuente:", "\n---", "[Fuente:", "---\n"],
        )
        t_gen = time.perf_counter() - t_gen0
        tokens = r["usage"]["completion_tokens"]
    except Exception as e:
        t_gen = time.perf_counter() - t_gen0
        tokens = 0
        log.error(f"Error en generación: {e}")

    t_total = t_rag + t_gen
    tok_s = tokens / t_gen if t_gen > 0 else 0

    return {
        "id": pregunta["id"],
        "es_primera": es_primera,
        "t_rag_s": round(t_rag, 2),
        "t_gen_s": round(t_gen, 2),
        "t_total_s": round(t_total, 2),
        "tokens": tokens,
        "tok_s": round(tok_s, 2),
    }


def detectar_hardware():
    """Detecta RAM, CPU y GPU disponibles."""
    import os
    info = {}

    try:
        import psutil
        info["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
        info["cpu_hilos"] = psutil.cpu_count(logical=True)
        info["cpu_fisicos"] = psutil.cpu_count(logical=False)
    except ImportError:
        info["ram_gb"] = "N/D"
        info["cpu_hilos"] = os.cpu_count() or "N/D"
        info["cpu_fisicos"] = "N/D"

    # GPU
    try:
        from llama_cpp import Llama
        info["gpu"] = "Verificar manualmente"
    except:
        info["gpu"] = "No disponible"

    return info


def generar_reporte(resultados, hw_info, modelo_nombre, n_gpu_layers):
    """Genera reporte de texto para el artículo."""
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("=" * 80)
    lines.append("MEDICIÓN EMPÍRICA DE LATENCIAS — PocketMentorEDU")
    lines.append(f"Fecha: {ts}")
    lines.append(f"Propósito: Datos de latencia para artículo de arquitectura (Entramado)")
    lines.append("=" * 80)
    lines.append("")

    # Hardware
    lines.append("HARDWARE DETECTADO")
    lines.append("-" * 40)
    lines.append(f"  RAM total:       {hw_info.get('ram_gb', 'N/D')} GB")
    lines.append(f"  CPU hilos:       {hw_info.get('cpu_hilos', 'N/D')}")
    lines.append(f"  CPU físicos:     {hw_info.get('cpu_fisicos', 'N/D')}")
    lines.append(f"  GPU layers:      {n_gpu_layers}")
    lines.append(f"  Modelo:          {modelo_nombre}")
    lines.append("")

    # Resultados individuales
    lines.append("RESULTADOS POR CONSULTA")
    lines.append("-" * 80)
    lines.append(f"{'ID':<6} {'Primera':<9} {'RAG (s)':<10} {'LLM (s)':<10} {'Total (s)':<11} {'Tokens':<8} {'Tok/s':<7}")
    lines.append("-" * 80)

    for r in resultados:
        primera = "SÍ" if r["es_primera"] else "no"
        lines.append(
            f"{r['id']:<6} {primera:<9} {r['t_rag_s']:<10.2f} {r['t_gen_s']:<10.2f} "
            f"{r['t_total_s']:<11.2f} {r['tokens']:<8} {r['tok_s']:<7.2f}"
        )

    lines.append("-" * 80)
    lines.append("")

    # Estadísticas agregadas
    # Separar primera consulta de las demás
    primera = [r for r in resultados if r["es_primera"]]
    subsiguientes = [r for r in resultados if not r["es_primera"]]

    lines.append("RESUMEN ESTADÍSTICO")
    lines.append("-" * 50)

    if primera:
        p = primera[0]
        lines.append(f"  Primera consulta (incluye lazy loading):")
        lines.append(f"    RAG: {p['t_rag_s']:.2f} s | LLM: {p['t_gen_s']:.2f} s | Total: {p['t_total_s']:.2f} s")
        lines.append("")

    if subsiguientes:
        rag_times = [r["t_rag_s"] for r in subsiguientes]
        gen_times = [r["t_gen_s"] for r in subsiguientes]
        total_times = [r["t_total_s"] for r in subsiguientes]
        tok_rates = [r["tok_s"] for r in subsiguientes if r["tok_s"] > 0]

        lines.append(f"  Consultas subsiguientes (n={len(subsiguientes)}):")
        lines.append(f"    RAG:   promedio={statistics.mean(rag_times):.2f} s, "
                     f"rango=[{min(rag_times):.2f}, {max(rag_times):.2f}] s")
        lines.append(f"    LLM:   promedio={statistics.mean(gen_times):.2f} s, "
                     f"rango=[{min(gen_times):.2f}, {max(gen_times):.2f}] s")
        lines.append(f"    Total: promedio={statistics.mean(total_times):.2f} s, "
                     f"rango=[{min(total_times):.2f}, {max(total_times):.2f}] s")
        if tok_rates:
            lines.append(f"    Tok/s: promedio={statistics.mean(tok_rates):.2f}, "
                         f"rango=[{min(tok_rates):.2f}, {max(tok_rates):.2f}]")

    lines.append("")

    # Rango global para el artículo
    all_totals = [r["t_total_s"] for r in resultados]
    lines.append("RANGO PARA EL ARTÍCULO")
    lines.append("-" * 50)
    lines.append(f"  Latencia total: {min(all_totals):.0f} – {max(all_totals):.0f} s")
    lines.append(f"  (incluye primera consulta con lazy loading)")
    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Medición de latencias para artículo de arquitectura")
    parser.add_argument("--repeticiones", type=int, default=3,
                        help="Número de repeticiones por pregunta (default: 3)")
    parser.add_argument("--model", type=str, default=None,
                        help="Nombre o ruta del .gguf a usar")
    parser.add_argument("--n_gpu_layers", type=int, default=0,
                        help="Capas a descargar en GPU (default: 0 = solo CPU)")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("  MEDICIÓN EMPÍRICA DE LATENCIAS — Entramado")
    log.info(f"  Preguntas: {len(PREGUNTAS)} × {args.repeticiones} repeticiones")
    log.info(f"  GPU layers: {args.n_gpu_layers}")
    log.info("=" * 60)

    # ── Verificar dependencias ────────────────────────────────────────────
    try:
        from llama_cpp import Llama
    except ImportError:
        log.error("Falta llama-cpp-python. Usa: engine\\python\\python.exe app\\medir_latencias.py")
        sys.exit(1)

    from ingester import Ingester
    from rag import RAGEngine

    know_dir = BASE_DIR / "knowledge"
    db_dir = BASE_DIR / "database"

    log.info("Verificando índice…")
    Ingester(know_dir=know_dir, db_dir=db_dir).run()

    log.info("Cargando RAG…")
    rag = RAGEngine(db_dir=db_dir, know_dir=know_dir)

    # ── Buscar modelo ─────────────────────────────────────────────────────
    models_dir = BASE_DIR / "models"
    if args.model:
        model_path = Path(args.model)
        if not model_path.is_absolute():
            model_path = models_dir / args.model
    else:
        models = sorted(models_dir.glob("*.gguf"))
        if not models:
            log.error("No se encontró modelo .gguf en /models")
            sys.exit(1)
        model_path = models[0]

    modelo_nombre = model_path.stem

    try:
        import psutil
        threads = max(2, psutil.cpu_count(logical=False) or 4)
    except ImportError:
        import os
        threads = max(2, os.cpu_count() or 4)

    log.info(f"Cargando modelo: {model_path.name} ({threads} hilos, {args.n_gpu_layers} GPU layers)…")
    llm = Llama(
        model_path=str(model_path),
        n_ctx=4096,
        n_threads=threads,
        n_gpu_layers=args.n_gpu_layers,
        verbose=False,
    )

    # ── Detectar hardware ─────────────────────────────────────────────────
    hw_info = detectar_hardware()
    log.info(f"Hardware: RAM={hw_info.get('ram_gb')} GB, "
             f"CPU={hw_info.get('cpu_hilos')} hilos")

    # ── Ejecutar mediciones ───────────────────────────────────────────────
    resultados = []
    total_consultas = len(PREGUNTAS) * args.repeticiones
    consulta_num = 0

    for rep in range(args.repeticiones):
        log.info(f"\n--- Repetición {rep + 1}/{args.repeticiones} ---")
        for pregunta in PREGUNTAS:
            consulta_num += 1
            es_primera = (consulta_num == 1)

            log.info(f"  [{consulta_num}/{total_consultas}] "
                     f"{'[PRIMERA] ' if es_primera else ''}"
                     f"Q{pregunta['id']} — {pregunta['text'][:50]}…")

            resultado = medir_consulta(llm, rag, pregunta, es_primera)
            resultados.append(resultado)

            log.info(f"    RAG={resultado['t_rag_s']:.1f}s | "
                     f"LLM={resultado['t_gen_s']:.1f}s | "
                     f"Total={resultado['t_total_s']:.1f}s | "
                     f"Tok/s={resultado['tok_s']:.1f}")

    # ── Generar reporte ───────────────────────────────────────────────────
    reporte = generar_reporte(resultados, hw_info, modelo_nombre, args.n_gpu_layers)

    out_dir = BASE_DIR / "logs" / "latencia_entramado"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"latencia_{ts}.txt"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(reporte)

    print("\n" + reporte)
    print(f"\nReporte guardado en: {out_path}")


if __name__ == "__main__":
    main()
