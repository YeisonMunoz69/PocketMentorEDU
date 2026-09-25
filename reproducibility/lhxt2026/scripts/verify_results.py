#!/usr/bin/env python
"""Recompute the values reported in the LHXT 2026 article."""

from __future__ import annotations

import csv
import json
import math
import statistics as st
from pathlib import Path

from scipy.stats import spearmanr, t, wilcoxon


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent
DATA_DIR = PACKAGE_DIR / "data"
REPORT_PATH = PACKAGE_DIR / "verification_report.json"
CONTENT_IDS = {"G1", "G2", "G3", "G4", "V1", "V2", "V3", "W1", "W2", "W3", "R1", "R2"}
MODELS = ("Phi-4-mini", "Qwen2.5-3B")


def read_csv(name: str) -> list[dict]:
    with (DATA_DIR / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def truth(value: str) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes", "si", "sí"}


def rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def main_results() -> dict:
    rows = read_csv("benchmark_main.csv")
    if len(rows) != 196:
        raise AssertionError(f"Se esperaban 196 ejecuciones principales y se encontraron {len(rows)}")
    result = {}
    for model in MODELS:
        model_rows = [row for row in rows if row["model"] == model]
        semantic = [row for row in model_rows if row["config_id"] == "cfg_eval_full"]
        content = [row for row in semantic if row["question_id"] in CONTENT_IDS]
        rho, p_value = spearmanr(
            [float(row["overall_score"]) for row in content],
            [float(row["kw_score"]) for row in content],
        )
        speeds = [float(row["tokens_per_sec"]) for row in model_rows]
        probes = [row for row in model_rows if row["question_id"].startswith("F")]
        supported = [row for row in model_rows if row["question_id"] in CONTENT_IDS]
        result[model] = {
            "n": len(model_rows),
            "semantic_mean": rounded(st.mean(float(row["overall_score"]) for row in semantic)),
            "semantic_vs_keyword_spearman_rho": rounded(rho),
            "semantic_vs_keyword_p": rounded(p_value),
            "tokens_per_second_mean": rounded(st.mean(speeds)),
            "tokens_per_second_sd": rounded(st.stdev(speeds)),
            "tokens_per_second_min": rounded(min(speeds)),
            "tokens_per_second_max": rounded(max(speeds)),
            "correct_rejections": sum(truth(row["fallback_correct"]) for row in probes),
            "false_rejections": sum(truth(row["is_fallback"]) for row in supported),
            "detector_activations": sum(truth(row["is_fallback"]) for row in model_rows),
        }
    return result


def seed_results() -> dict:
    rows = read_csv("seed_runs.csv")
    if len(rows) != 140:
        raise AssertionError(f"Se esperaban 140 ejecuciones con semilla y se encontraron {len(rows)}")
    analysis = [
        row
        for row in rows
        if row["run_role"] == "analysis" and row["question_id"] in CONTENT_IDS
    ]
    per_question = {model: {} for model in MODELS}
    within_sd = []
    for model in MODELS:
        for question_id in sorted(CONTENT_IDS):
            values = [
                float(row["overall_score"])
                for row in analysis
                if row["model"] == model and row["question_id"] == question_id
            ]
            if len(values) != 4:
                raise AssertionError(f"{model}/{question_id}: se esperaban cuatro semillas")
            per_question[model][question_id] = st.mean(values)
            within_sd.append(st.stdev(values))

    phi = [per_question["Phi-4-mini"][key] for key in sorted(CONTENT_IDS)]
    qwen = [per_question["Qwen2.5-3B"][key] for key in sorted(CONTENT_IDS)]
    differences = [left - right for left, right in zip(phi, qwen)]
    mean_difference = st.mean(differences)
    standard_error = st.stdev(differences) / math.sqrt(len(differences))
    critical = t.ppf(0.975, len(differences) - 1)
    confidence_interval = (
        mean_difference - critical * standard_error,
        mean_difference + critical * standard_error,
    )
    statistic, p_value = wilcoxon(phi, qwen, alternative="two-sided")

    repeated = [row for row in rows if row["run_role"] == "determinism_control"]
    exact_controls = {}
    for model in MODELS:
        first = {
            row["question_id"]: row
            for row in rows
            if row["model"] == model and row["seed"] == "42"
        }
        second = {row["question_id"]: row for row in repeated if row["model"] == model}
        exact_controls[model] = all(
            first[key]["overall_score"] == second[key]["overall_score"]
            and first[key]["response_sha256"] == second[key]["response_sha256"]
            for key in first
        )

    return {
        "content_mean_phi": rounded(st.mean(phi)),
        "content_mean_qwen": rounded(st.mean(qwen)),
        "paired_mean_difference": rounded(mean_difference),
        "paired_difference_ci95": [rounded(value) for value in confidence_interval],
        "wilcoxon_w": rounded(statistic),
        "wilcoxon_p": rounded(p_value),
        "mean_within_model_sd": rounded(st.mean(within_sd)),
        "mean_absolute_between_model_difference": rounded(
            st.mean(abs(left - right) for left, right in zip(phi, qwen))
        ),
        "seed_42_control_exact": exact_controls,
    }


def teacher_results() -> dict:
    rows = read_csv("teacher_ratings_anonymized.csv")
    if len(rows) != 20:
        raise AssertionError(f"Se esperaban 20 valoraciones y se encontraron {len(rows)}")
    teachers = sorted({row["teacher_id"] for row in rows})
    by_teacher = {teacher: [] for teacher in teachers}
    for row in rows:
        mean_rating = st.mean(
            float(row[field]) for field in ("correction", "clarity", "level_adequacy")
        )
        by_teacher[row["teacher_id"]].append((row, mean_rating))

    summary = {}
    for teacher in teachers:
        pairs = by_teacher[teacher]
        rho, p_value = spearmanr(
            [float(row["automatic_score"]) for row, _ in pairs],
            [rating for _, rating in pairs],
        )
        summary[teacher] = {
            "mean_rating": rounded(st.mean(rating for _, rating in pairs)),
            "use_without_changes": sum(row["use_without_changes"] == "yes" for row, _ in pairs),
            "automatic_score_spearman_rho": rounded(rho),
            "automatic_score_spearman_p": rounded(p_value),
        }

    paired = {}
    for teacher in teachers:
        paired[teacher] = {
            row["response_code"]: (row, rating) for row, rating in by_teacher[teacher]
        }
    codes = sorted(set(paired[teachers[0]]) & set(paired[teachers[1]]))
    left = [paired[teachers[0]][code][1] for code in codes]
    right = [paired[teachers[1]][code][1] for code in codes]
    rho, p_value = spearmanr(left, right)
    left_use = [paired[teachers[0]][code][0]["use_without_changes"] == "yes" for code in codes]
    right_use = [paired[teachers[1]][code][0]["use_without_changes"] == "yes" for code in codes]
    agreements = sum(a == b for a, b in zip(left_use, right_use))
    observed = agreements / len(codes)
    expected = (sum(left_use) / len(codes)) * (sum(right_use) / len(codes))
    expected += ((len(codes) - sum(left_use)) / len(codes)) * (
        (len(codes) - sum(right_use)) / len(codes)
    )
    kappa = (observed - expected) / (1 - expected)
    summary["agreement"] = {
        "rating_spearman_rho": rounded(rho),
        "rating_spearman_p": rounded(p_value),
        "use_decision_agreements": agreements,
        "use_decision_kappa": rounded(kappa),
    }
    return summary


def assert_report(report: dict) -> None:
    expected = {
        ("main", "Phi-4-mini", "semantic_mean"): 0.794929,
        ("main", "Qwen2.5-3B", "semantic_mean"): 0.794857,
        ("seeds", "content_mean_phi"): 0.803042,
        ("seeds", "content_mean_qwen"): 0.800958,
        ("seeds", "wilcoxon_w"): 31.0,
        ("seeds", "wilcoxon_p"): 0.569336,
        ("teachers", "agreement", "use_decision_kappa"): -0.428571,
    }
    for path, value in expected.items():
        current = report
        for key in path:
            current = current[key]
        if not math.isclose(float(current), value, rel_tol=0, abs_tol=0.000001):
            raise AssertionError(f"{'.'.join(path)}: {current} != {value}")
    if not all(report["seeds"]["seed_42_control_exact"].values()):
        raise AssertionError("El control de la semilla 42 no fue idéntico")


def main() -> None:
    report = {
        "main": main_results(),
        "seeds": seed_results(),
        "teachers": teacher_results(),
    }
    assert_report(report)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"\nVerificación correcta. Informe: {REPORT_PATH}")


if __name__ == "__main__":
    main()
