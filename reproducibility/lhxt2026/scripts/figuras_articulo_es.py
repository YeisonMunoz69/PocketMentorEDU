#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Genera las cuatro figuras vigentes del artículo LHXT 2026 en español.

Fuentes:
  * data/seed_runs.csv: cuatro semillas por modelo para cfg_eval_full.
  * data/teacher_ratings_anonymized.csv: valoraciones de los dos docentes.

Salidas:
  * SVG y PDF vectoriales en ``figures/``.
  * PNG a 600 DPI y copia PNG optimizada para Word en ``figures/``.
"""

from __future__ import annotations

import argparse
import csv
import statistics as st
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Patch
from matplotlib.ticker import FuncFormatter
from PIL import Image

try:
    import scienceplots  # noqa: F401

    HAS_SCIENCEPLOTS = True
except ImportError:
    HAS_SCIENCEPLOTS = False


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PACKAGE_ROOT / "data"
FIGURE_DIR = PACKAGE_ROOT / "figures"

BLUE = "#3366CC"
ORANGE = "#E66101"
BLUE_LIGHT = "#A9C9EE"
AMBER = "#E8C977"
INK = "#1A1A1A"
MUTED = "#555555"
GRID = "#D9D9D9"
SUMMARY_TEAL = "#008F83"
SUMMARY_PURPLE = "#8E63A9"
WHITE = "#FFFFFF"

MODELS = ("Phi-4-mini", "Qwen2.5-3B")
CONTENT_QUESTIONS = ("G1", "G2", "G3", "G4", "V1", "V2", "V3", "W1", "W2", "W3", "R1", "R2")
SEEDS = ("42", "7", "123", "2026")
W_GROUNDING, W_RELEVANCE, W_LEVEL = 0.40, 0.40, 0.20

def configure_style() -> None:
    if HAS_SCIENCEPLOTS:
        plt.style.use(["science", "no-latex"])
    else:
        plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.facecolor": WHITE,
            "axes.facecolor": WHITE,
            "axes.prop_cycle": plt.cycler(color=(BLUE, ORANGE)),
            "font.family": "serif",
            "font.serif": ["Source Serif 4", "Source Serif Pro", "Times New Roman", "DejaVu Serif"],
            "font.size": 8.0,
            "text.color": INK,
            "axes.labelcolor": MUTED,
            "axes.labelsize": 8.5,
            "axes.titlesize": 9.0,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "legend.fontsize": 7.0,
            "legend.frameon": False,
            "axes.edgecolor": GRID,
            "axes.linewidth": 0.65,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.top": False,
            "ytick.right": False,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "grid.alpha": 0.70,
            "mathtext.fontset": "cm",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.dpi": 600,
            "savefig.facecolor": WHITE,
            "savefig.bbox": "tight",
        }
    )


def point_decimal(value: float, _position: int | None = None) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text


def clean_axis(axis, grid: str | None = "y") -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    if grid:
        axis.grid(True, axis=grid)
        axis.set_axisbelow(True)


def load_benchmark_data() -> dict[str, dict[str, dict[str, dict]]]:
    source = DATA_DIR / "seed_runs.csv"
    data: dict[str, dict[str, dict[str, dict]]] = {
        model: {seed: {} for seed in SEEDS} for model in MODELS
    }
    with source.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            model = row["model"]
            seed = row["seed"]
            question_id = row["question_id"]
            if row["run_role"] != "analysis" or model not in data or seed not in data[model]:
                continue
            if row["config_id"] != "cfg_eval_full":
                continue
            data[model][seed][question_id] = {
                **row,
                "overall_score": float(row["overall_score"]),
                "grounding_score": float(row["grounding_score"]),
                "relevance_score": float(row["relevance_score"]),
            }
    for model in MODELS:
        for seed in SEEDS:
            missing = set(CONTENT_QUESTIONS) - set(data[model][seed])
            if missing:
                raise ValueError(f"Faltan preguntas en {source} para {model}/{seed}: {sorted(missing)}")
    return data


def load_teacher_data() -> dict[str, dict[str, tuple[int, int, int]]]:
    ratings: dict[str, dict[str, tuple[int, int, int]]] = {"Docente 1": {}, "Docente 2": {}}
    source = DATA_DIR / "teacher_ratings_anonymized.csv"
    with source.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            teacher = "Docente 1" if row["teacher_id"] == "teacher_1" else "Docente 2"
            ratings[teacher][row["response_code"]] = tuple(
                int(row[column]) for column in ("correction", "clarity", "level_adequacy")
            )
    codes = set(ratings["Docente 1"])
    if codes != set(ratings["Docente 2"]) or len(codes) != 10:
        raise ValueError("La submuestra docente debe contener las mismas diez respuestas para ambos docentes")
    return ratings


def level_component(row: dict) -> float:
    value = (
        row["overall_score"]
        - W_GROUNDING * row["grounding_score"]
        - W_RELEVANCE * row["relevance_score"]
    ) / W_LEVEL
    return max(0.0, min(1.0, value))


def output_paths(stem: str) -> dict[str, Path]:
    return {
        "svg": FIGURE_DIR / f"{stem}.svg",
        "png": FIGURE_DIR / f"{stem}.png",
        "png_word": FIGURE_DIR / f"{stem}_WORD.png",
        "pdf": FIGURE_DIR / f"{stem}.pdf",
    }


def save_figure(fig, stem: str, overwrite: bool) -> dict[str, Path]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    paths = output_paths(stem)
    existing = [path for path in paths.values() if path.exists()]
    if existing and not overwrite:
        joined = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"No se sobrescriben figuras existentes sin --overwrite: {joined}")
    fig.savefig(paths["svg"], format="svg")
    svg_text = paths["svg"].read_text(encoding="utf-8")
    svg_text = "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n"
    paths["svg"].write_text(svg_text, encoding="utf-8", newline="\n")
    fig.savefig(paths["png"], format="png", dpi=600)
    with Image.open(paths["png"]) as rendered:
        rendered.convert("RGB").save(
            paths["png_word"],
            format="PNG",
            dpi=(600, 600),
            optimize=True,
        )
    fig.savefig(paths["pdf"], format="pdf")
    plt.close(fig)
    return paths


def figure_01_score_anatomy(overwrite: bool) -> dict[str, Path]:
    fig, axis = plt.subplots(figsize=(7.08, 2.55))
    segments = (
        (0.40, BLUE, "fundamentación"),
        (0.40, BLUE_LIGHT, "relevancia"),
        (0.20, AMBER, "nivel"),
    )
    left = 0.0
    for width, color, _label in segments:
        axis.add_patch(
            FancyBboxPatch(
                (left + 0.004, 0.38),
                width - 0.008,
                0.28,
                boxstyle="round,pad=0,rounding_size=0.010",
                facecolor=color,
                edgecolor=WHITE,
                linewidth=1.4,
            )
        )
        axis.text(
            left + width / 2,
            0.52,
            f"{int(width * 100)} %",
            ha="center",
            va="center",
            fontsize=11.0,
            fontweight="bold",
            color=WHITE if color == BLUE else INK,
        )
        left += width

    notes = (
        (0.20, "fundamentación\ncompara la RESPUESTA\ncon el texto recuperado"),
        (0.60, "relevancia\ncompara la PREGUNTA\ncon el texto recuperado"),
        (0.90, "nivel\nusa la LONGITUD\nDE LA RESPUESTA"),
    )
    for center, text in notes:
        axis.text(center, 0.29, text, ha="center", va="top", fontsize=7.2, linespacing=1.30)

    axis.annotate(
        "la respuesta no interviene en este componente",
        xy=(0.60, 0.665),
        xytext=(0.60, 0.82),
        ha="center",
        fontsize=7.5,
        color=ORANGE,
        fontweight="bold",
        arrowprops={"arrowstyle": "-|>", "color": ORANGE, "linewidth": 1.1, "shrinkA": 2, "shrinkB": 3},
    )
    axis.text(
        0,
        1.19,
        "Anatomía del puntaje que el tutor reporta como «calidad»",
        fontsize=10.0,
        fontweight="bold",
        va="top",
    )
    axis.text(
        0,
        1.05,
        "El 60 % depende de la salida: 40 % del significado y 20 % de la longitud.",
        fontsize=7.8,
        color=MUTED,
        va="top",
    )
    axis.set_xlim(-0.01, 1.01)
    axis.set_ylim(-0.13, 1.25)
    axis.axis("off")
    return save_figure(fig, "Figura_01_anatomia_puntaje_ES", overwrite)


def figure_02_score_by_question(data, overwrite: bool) -> dict[str, Path]:
    fig, axes = plt.subplots(1, 2, figsize=(7.08, 3.15), sharey=True)
    for axis, model in zip(axes, MODELS):
        grounding = [
            W_GROUNDING * data[model]["42"][question]["grounding_score"]
            for question in CONTENT_QUESTIONS
        ]
        relevance = [
            W_RELEVANCE * data[model]["42"][question]["relevance_score"]
            for question in CONTENT_QUESTIONS
        ]
        level = [W_LEVEL * level_component(data[model]["42"][question]) for question in CONTENT_QUESTIONS]
        x = np.arange(len(CONTENT_QUESTIONS))
        axis.bar(x, grounding, 0.68, color=BLUE, edgecolor=WHITE, linewidth=1.2)
        axis.bar(x, relevance, 0.68, bottom=grounding, color=BLUE_LIGHT, edgecolor=WHITE, linewidth=1.2)
        axis.bar(
            x,
            level,
            0.68,
            bottom=np.add(grounding, relevance),
            color=AMBER,
            edgecolor=WHITE,
            linewidth=1.2,
        )
        axis.set_xticks(x)
        axis.set_xticklabels(CONTENT_QUESTIONS, fontsize=6.7)
        axis.set_ylim(0, 1.0)
        axis.yaxis.set_major_formatter(FuncFormatter(point_decimal))
        axis.set_title(model, fontsize=8.3, fontweight="bold", pad=4)
        clean_axis(axis)
    axes[0].set_ylabel("Puntaje reportado")
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.15, top=0.70, wspace=0.11)
    fig.text(
        0.075,
        0.97,
        "Composición del puntaje por pregunta",
        fontsize=10.0,
        fontweight="bold",
        ha="left",
        va="top",
    )
    fig.text(
        0.075,
        0.90,
        "La fundamentación usa la respuesta; la relevancia no la inspecciona directamente.",
        fontsize=7.7,
        color=MUTED,
        ha="left",
        va="top",
    )
    fig.legend(
        handles=(
            Patch(facecolor=BLUE, label="fundamentación (respuesta frente al texto)"),
            Patch(facecolor=BLUE_LIGHT, label="relevancia (pregunta frente al texto)"),
            Patch(facecolor=AMBER, label="nivel (conteo de palabras)"),
        ),
        loc="upper left",
        bbox_to_anchor=(0.071, 0.84),
        ncol=3,
        fontsize=6.5,
        handlelength=1.0,
        handletextpad=0.35,
        columnspacing=0.9,
    )
    return save_figure(fig, "Figura_02_composicion_por_pregunta_ES", overwrite)


def figure_03_variation(data, overwrite: bool) -> dict[str, Path]:
    within_model_sd: list[float] = []
    between_model_difference: list[float] = []
    for question in CONTENT_QUESTIONS:
        deviations = [
            st.stdev(data[model][seed][question]["overall_score"] for seed in SEEDS)
            for model in MODELS
        ]
        means = [
            st.mean(data[model][seed][question]["overall_score"] for seed in SEEDS)
            for model in MODELS
        ]
        within_model_sd.append(st.mean(deviations))
        between_model_difference.append(abs(means[0] - means[1]))

    noise = st.mean(within_model_sd)
    difference = st.mean(between_model_difference)
    fig = plt.figure(figsize=(7.08, 3.05))
    grid = fig.add_gridspec(1, 2, width_ratios=(1.05, 2.20), wspace=0.34)

    summary_axis = fig.add_subplot(grid[0])
    summary_axis.barh(
        (1, 0),
        (noise, difference),
        0.46,
        color=(SUMMARY_TEAL, SUMMARY_PURPLE),
        edgecolor=WHITE,
        linewidth=1.2,
    )
    labels = (
        (1, noise, "desviación estándar media\ndentro de cada modelo\npor pregunta"),
        (0, difference, "diferencia absoluta media\nentre modelos"),
    )
    for y, value, label in labels:
        summary_axis.text(
            value + 0.0013,
            y,
            f"{value:.3f}",
            va="center",
            fontsize=8.0,
            fontweight="bold",
        )
        summary_axis.text(0, y - 0.33, label, va="top", fontsize=6.6, color=MUTED, linespacing=1.25)
    summary_axis.set_xlim(0, max(noise, difference) * 1.42)
    summary_axis.set_ylim(-0.82, 1.58)
    summary_axis.set_yticks([])
    summary_axis.set_xticks([])
    for spine in summary_axis.spines.values():
        spine.set_visible(False)
    summary_axis.text(0, 1.22, "Dos resúmenes descriptivos", transform=summary_axis.transAxes, fontsize=8.7, fontweight="bold")
    summary_axis.text(
        0,
        1.14,
        "Tienen definiciones distintas; se presentan\njuntos por escala, no como una razón formal.",
        transform=summary_axis.transAxes,
        fontsize=6.5,
        color=MUTED,
        va="top",
        linespacing=1.25,
    )

    score_axis = fig.add_subplot(grid[1])
    x = np.arange(len(CONTENT_QUESTIONS))
    for index, (model, color, marker) in enumerate(zip(MODELS, (BLUE, ORANGE), ("o", "s"))):
        means = [
            st.mean(data[model][seed][question]["overall_score"] for seed in SEEDS)
            for question in CONTENT_QUESTIONS
        ]
        deviations = [
            st.stdev(data[model][seed][question]["overall_score"] for seed in SEEDS)
            for question in CONTENT_QUESTIONS
        ]
        score_axis.errorbar(
            x + (index - 0.5) * 0.22,
            means,
            yerr=deviations,
            fmt=marker,
            color=color,
            capsize=0,
            markersize=4.2,
            elinewidth=1.5,
            markeredgecolor=WHITE,
            markeredgewidth=0.8,
            linestyle="none",
            label=model,
        )
    score_axis.set_xticks(x)
    score_axis.set_xticklabels(CONTENT_QUESTIONS, fontsize=6.5)
    score_axis.set_ylim(0.60, 0.96)
    score_axis.yaxis.set_major_formatter(FuncFormatter(point_decimal))
    score_axis.set_ylabel("Puntaje reportado")
    score_axis.legend(loc="lower left", ncol=2, fontsize=6.5, handletextpad=0.3, columnspacing=0.8)
    clean_axis(score_axis)
    score_axis.set_title("Medias observadas y desviaciones estándar por pregunta", loc="left", fontsize=8.7, fontweight="bold", pad=22)
    score_axis.text(
        0,
        1.04,
        "Cada punto promedia cuatro semillas; la barra representa su dispersión.",
        transform=score_axis.transAxes,
        fontsize=6.8,
        color=MUTED,
    )
    fig.subplots_adjust(left=0.055, right=0.985, bottom=0.15, top=0.78)
    return save_figure(fig, "Figura_03_variacion_entre_modelos_ES", overwrite)


def figure_04_teacher_ratings(ratings, overwrite: bool) -> dict[str, Path]:
    codes = sorted(ratings["Docente 1"])
    mean_1 = {code: st.mean(ratings["Docente 1"][code]) for code in codes}
    mean_2 = {code: st.mean(ratings["Docente 2"][code]) for code in codes}
    fig, axis = plt.subplots(figsize=(7.08, 3.40))

    for code in codes:
        increases = mean_2[code] >= mean_1[code]
        color = BLUE if increases else ORANGE
        marker = "s" if increases else "o"
        axis.plot((0, 1), (mean_1[code], mean_2[code]), color=color, linewidth=1.35, alpha=0.86, zorder=2)
        axis.scatter(
            (0, 1),
            (mean_1[code], mean_2[code]),
            s=24,
            marker=marker,
            color=color,
            edgecolor=WHITE,
            linewidth=0.9,
            zorder=3,
        )

    for side, values, horizontal_alignment, offset in (
        (0, mean_1, "right", -0.035),
        (1, mean_2, "left", 0.035),
    ):
        grouped: dict[float, list[str]] = {}
        for code in codes:
            grouped.setdefault(round(values[code], 3), []).append(code)
        for value, value_codes in grouped.items():
            rows = [", ".join(sorted(value_codes)[index : index + 3]) for index in range(0, len(value_codes), 3)]
            axis.text(
                side + offset,
                value,
                "\n".join(rows),
                ha=horizontal_alignment,
                va="center",
                fontsize=6.6,
                color=MUTED,
                linespacing=1.18,
            )

    axis.set_xlim(-0.38, 1.28)
    axis.set_ylim(0.7, 5.2)
    axis.set_xticks((0, 1))
    axis.set_xticklabels(("Docente 1", "Docente 2"), fontsize=8.2, fontweight="bold")
    axis.set_ylabel("Calificación media (1 a 5)")
    axis.set_yticks((1, 2, 3, 4, 5))
    clean_axis(axis)
    axis.spines["bottom"].set_visible(False)
    axis.text(
        0,
        1.20,
        "Las mismas diez respuestas, valoradas por dos docentes de inglés",
        transform=axis.transAxes,
        fontsize=10.0,
        fontweight="bold",
    )
    axis.text(
        0,
        1.07,
        "Cada línea representa una respuesta. Las calificaciones no conservaron el mismo orden\n"
        "(rho de Spearman = −0.50); las decisiones de uso mostraron desacuerdo "
        "(kappa de Cohen = −0.43).",
        transform=axis.transAxes,
        fontsize=7.2,
        color=MUTED,
        linespacing=1.35,
    )
    fig.subplots_adjust(left=0.13, right=0.91, bottom=0.14, top=0.75)
    return save_figure(fig, "Figura_04_valoracion_docentes_ES", overwrite)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera las cuatro figuras del artículo LHXT 2026 en español.")
    parser.add_argument("--overwrite", action="store_true", help="Sobrescribe salidas con los mismos nombres.")
    args = parser.parse_args()

    configure_style()
    benchmark_data = load_benchmark_data()
    teacher_data = load_teacher_data()
    outputs = {
        "Figura 1": figure_01_score_anatomy(args.overwrite),
        "Figura 2": figure_02_score_by_question(benchmark_data, args.overwrite),
        "Figura 3": figure_03_variation(benchmark_data, args.overwrite),
        "Figura 4": figure_04_teacher_ratings(teacher_data, args.overwrite),
    }
    for label, paths in outputs.items():
        print(label)
        for file_type, path in paths.items():
            print(f"  {file_type}: {path}")


if __name__ == "__main__":
    main()
