#!/usr/bin/env python
"""Build the public LHXT 2026 data package from the local research records.

The generated tables retain the numeric evidence and response hashes used by
the article. Full model responses, retrieved textbook passages, free-text
teacher comments, session logs, and system logs are deliberately excluded.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent
PROJECT_DIR = PACKAGE_DIR.parents[1]
DATA_DIR = PACKAGE_DIR / "data"

LOG_DIR = PROJECT_DIR / "logs" / "benchmarks"
PAPER_DIR = PROJECT_DIR / "papers" / "02-benchmark-lhxt2026"
QUESTION_SOURCE = PROJECT_DIR / "app" / "benchmark.py"
TEACHER_RATINGS = PAPER_DIR / "anclaje-docente" / "captura_docentes.csv"
TEACHER_KEY = PAPER_DIR / "anclaje-docente" / "clave_evaluacion.csv"

MAIN_RUNS = {
    "Phi-4-mini": LOG_DIR
    / "Phi-4-mini-instruct-Q4_K_M"
    / "benchmark_20260311_143428.csv",
    "Qwen2.5-3B": LOG_DIR
    / "Qwen2.5-3B-Instruct-Q4_K_M"
    / "benchmark_20260311_150946.csv",
}

SEED_RUNS = {
    "Phi-4-mini": {
        "42": "benchmark_20260902_140238.json",
        "7": "benchmark_20260903_122324.json",
        "123": "benchmark_20260903_125347.json",
        "2026": "benchmark_20260903_131956.json",
        "42_repeat": "benchmark_20260902_182028.json",
    },
    "Qwen2.5-3B": {
        "42": "benchmark_20260902_144618.json",
        "7": "benchmark_20260903_123651.json",
        "123": "benchmark_20260903_130631.json",
        "2026": "benchmark_20260903_135021.json",
        "42_repeat": "benchmark_20260902_184443.json",
    },
}

MODEL_DIRS = {
    "Phi-4-mini": "Phi-4-mini-instruct-Q4_K_M",
    "Qwen2.5-3B": "Qwen2.5-3B-Instruct-Q4_K_M",
}

RUN_FIELDS = (
    "model",
    "seed",
    "run_role",
    "source_run",
    "config_id",
    "question_id",
    "area",
    "level",
    "temperature",
    "top_p",
    "repeat_penalty",
    "max_tokens",
    "top_k_rag",
    "eval_mode",
    "t_rag_s",
    "t_gen_s",
    "t_eval_s",
    "t_total_s",
    "overall_score",
    "grounding_score",
    "relevance_score",
    "level_score",
    "passed",
    "is_fallback",
    "fallback_correct",
    "tokens_generated",
    "tokens_per_sec",
    "kw_score",
    "chunks_retrieved",
    "prompt_chars",
    "timestamp",
    "response_sha256",
    "context_sha256",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def write_csv(path: Path, fieldnames: Iterable[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def literal_assignment(path: Path, variable: str):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == variable for target in node.targets):
                return ast.literal_eval(node.value)
    raise ValueError(f"No se encontró {variable} en {path}")


def build_questions() -> None:
    rows = []
    for question in literal_assignment(QUESTION_SOURCE, "DEFAULT_QUESTIONS"):
        rows.append(
            {
                "question_id": question["id"],
                "area": question["area"],
                "level": question["level"],
                "question_es": question["text"],
                "expected_keywords": " | ".join(question.get("expected_keywords", [])),
                "source_page": question.get("source_page", ""),
                "expect_fallback": str(bool(question.get("expect_fallback", False))).lower(),
            }
        )
    write_csv(
        DATA_DIR / "questions.csv",
        (
            "question_id",
            "area",
            "level",
            "question_es",
            "expected_keywords",
            "source_page",
            "expect_fallback",
        ),
        rows,
    )


def build_configurations() -> None:
    names = (
        "config_id",
        "temperature",
        "top_p",
        "repeat_penalty",
        "max_tokens",
        "top_k_rag",
        "eval_mode",
    )
    rows = [dict(zip(names, values)) for values in literal_assignment(QUESTION_SOURCE, "CONFIGURATIONS")]
    write_csv(DATA_DIR / "configurations.csv", names, rows)


def public_run_row(row: dict, *, model: str, source: Path, seed: str = "", role: str = "main") -> dict:
    public = {field: row.get(field, "") for field in RUN_FIELDS}
    public.update(
        {
            "model": model,
            "seed": seed,
            "run_role": role,
            "source_run": source.name,
            "response_sha256": sha256_text(str(row.get("response_full", "")))
            if row.get("response_full") is not None
            else "",
            "context_sha256": sha256_text(
                json.dumps(
                    row.get("context_chunks", []),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            if row.get("context_chunks") is not None
            else "",
        }
    )
    return public


def build_main_runs() -> None:
    rows = []
    for model, path in MAIN_RUNS.items():
        rows.extend(public_run_row(row, model=model, source=path) for row in read_csv(path))
    write_csv(DATA_DIR / "benchmark_main.csv", RUN_FIELDS, rows)


def build_seed_runs() -> None:
    rows = []
    for model, runs in SEED_RUNS.items():
        model_dir = LOG_DIR / MODEL_DIRS[model]
        for seed, filename in runs.items():
            path = model_dir / filename
            payload = json.loads(path.read_text(encoding="utf-8"))
            source_rows = payload["results"] if isinstance(payload, dict) else payload
            role = "determinism_control" if seed == "42_repeat" else "analysis"
            rows.extend(
                public_run_row(row, model=model, source=path, seed=seed, role=role)
                for row in source_rows
            )
    write_csv(DATA_DIR / "seed_runs.csv", RUN_FIELDS, rows)


def build_teacher_ratings() -> None:
    key = {row["codigo"]: row for row in read_csv(TEACHER_KEY)}
    rows = []
    for rating in read_csv(TEACHER_RATINGS):
        code = rating["codigo"]
        mapped = key[code]
        rows.append(
            {
                "response_code": code,
                "teacher_id": rating["evaluador"].replace("docente_", "teacher_"),
                "model": mapped["modelo"],
                "question_id": mapped["question_id"],
                "area": mapped["area"],
                "level": mapped["nivel"],
                "automatic_score": mapped["puntaje_automatico"],
                "is_fallback": mapped["es_respaldo"].strip().lower(),
                "tokens": mapped["tokens"],
                "correction": rating["correccion"],
                "clarity": rating["claridad"],
                "level_adequacy": rating["adecuacion_nivel"],
                "use_without_changes": "yes"
                if rating["usaria_con_estudiante"].strip().casefold() in {"si", "sí", "yes", "true", "1"}
                else "no",
            }
        )
    fields = (
        "response_code",
        "teacher_id",
        "model",
        "question_id",
        "area",
        "level",
        "automatic_score",
        "is_fallback",
        "tokens",
        "correction",
        "clarity",
        "level_adequacy",
        "use_without_changes",
    )
    write_csv(DATA_DIR / "teacher_ratings_anonymized.csv", fields, rows)


def write_source_checksums() -> None:
    inputs = [QUESTION_SOURCE, TEACHER_RATINGS, TEACHER_KEY]
    inputs.extend(MAIN_RUNS.values())
    for model, runs in SEED_RUNS.items():
        inputs.extend(LOG_DIR / MODEL_DIRS[model] / filename for filename in runs.values())
    lines = []
    for path in sorted(set(inputs), key=lambda item: str(item).casefold()):
        lines.append(f"{sha256_file(path)}  {path.relative_to(PROJECT_DIR).as_posix()}")
    (PACKAGE_DIR / "SOURCE_FILES.sha256").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    build_questions()
    build_configurations()
    build_main_runs()
    build_seed_runs()
    build_teacher_ratings()
    write_source_checksums()
    print(f"Datos públicos generados en {DATA_DIR}")


if __name__ == "__main__":
    main()
