# PocketMentorEDU

PocketMentorEDU is an offline-capable intelligent tutoring platform designed for private, reproducible educational deployments. The architecture integrates local large language model (LLM) inference, hybrid retrieval-augmented generation (RAG), pedagogical prompt scaffolding, and real-time response evaluation without requiring external API dependencies during runtime.

---

## Technical Overview

The platform is designed to operate on commodity hardware in disconnected environments (such as portable USB distributions or localized laboratory settings). Key components include:

- **Local Inference Engine**: Executes quantized GGUF models via `llama-cpp-python` with configurable thread and context parameters.
- **Hybrid Retrieval Pipeline**: Combines dense semantic search (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) with sparse lexical matching (`rank-bm25`), parent-document chunking, and reciprocal rank fusion (RRF).
- **Neural Re-ranking**: Refines retrieved passages using a cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) prior to prompt synthesis.
- **Pedagogical Scaffolding**: Applies structured prompt templates across English as a Second Language (ESL) subjects and Common European Framework of Reference (CEFR) proficiency tiers (A1–B2).
- **Automated Response Indicators**: Computes source-grounding, query-context relevance, output-length coherence, lexical overlap, and latency. These indicators do not measure pedagogical quality or learning.
- **Web Interface**: Lightweight local dashboard and chat client served via FastAPI and vanilla web technologies.

---

## Hardware and Software Prerequisites

### Hardware Requirements
- **Processor**: x86-64 CPU with AVX2 instruction support (minimum 4 physical cores recommended).
- **Memory**: 8 GB RAM minimum (16 GB recommended for concurrent embeddings and generation).
- **Storage**: At least 6 GB of free disk space for model weights, vector embeddings, and dependencies.

### Software Requirements
- **Operating System**: Windows 10/11 (64-bit).
- **Python**: Version 3.11.x (recommended) or compatible 64-bit distribution.
- **Visual C++ Runtime**: Microsoft Visual C++ 2015-2022 Redistributable (x64).

---

## Evaluator Quick Start

Follow these steps to set up and evaluate the system on a target workstation.

### Step 1: Clone the Repository
```bash
git clone https://github.com/YeisonMunoz69/PocketMentorEDU.git
cd PocketMentorEDU
```

### Step 2: Set Up Virtual Environment and Dependencies
```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -U "huggingface_hub[cli]"
```

### Step 3: Acquire a Model File
Download a quantized GGUF model into the `models/` directory. For evaluation, the following lightweight models are recommended:

#### Option A: Phi-4-mini-instruct (Q4_K_M)
```bash
huggingface-cli download unsloth/Phi-4-mini-instruct-GGUF Phi-4-mini-instruct-Q4_K_M.gguf --local-dir models --local-dir-use-symlinks False
```

#### Option B: Qwen2.5-3B-Instruct (Q4_K_M)
```bash
huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF qwen2.5-3b-instruct-q4_k_m.gguf --local-dir models --local-dir-use-symlinks False
```

### Step 4: Pre-cache Embedding and Cross-Encoder Weights
Run the cache utility once while connected to the internet:
```bash
python app/cache_models.py
```
This stores local checkpoints of the multilingual bi-encoder and cross-encoder under `models/.cache/`. Subsequent runs operate entirely offline.

### Step 5: Launch the Application
Start the service via:
```bash
python app/main.py
```
Alternatively, on Windows systems with portable engines configured, run:
```bat
INICIAR.bat
```
Once the service is active, navigate to:
```
http://localhost:8000
```

---

## Pre-configured Evaluation Assets

The repository contains baseline assets to ensure immediate out-of-the-box operation:

1. **Pedagogical Configuration (`prompts/`)**:
   - `prompts/levels/levels.json`: Instruction profiles for CEFR levels A1 through B2.
   - `prompts/modes/modes.json`: Scaffolding modes (Tutor, Socratic, Practice, Assessment).
   - `prompts/subjects/*.json`: Curated domain prompts for Grammar, Vocabulary, Reading, Speaking, Writing, Pronunciation, and General English.

2. **Reference Corpus (`knowledge/`)**:
   - Contains an open-educational resource (OER) reference textbook (*College ESL Writers: Applied Grammar and Composing Strategies for Success*).
   - On initial launch, `app/ingester.py` parses this document and builds the hybrid retrieval index (`database/chunks.json`, `database/embeddings.npy`). Additional PDF, TXT, MD, or DOCX files placed in `knowledge/` are automatically detected and indexed upon system startup.

---

## Automated Benchmark and Reproducibility

An automated benchmarking script is included to measure response latency, tokens per second, source-grounding, query-context relevance, output-length coherence, and lexical overlap across experimental configurations. These indicators describe adherence to the retrieved material and properties of the output; they are not measures of teaching effectiveness or student learning.

```bash
python app/benchmark.py --quick
```

Command-line parameters:
- `--quick`: Executes an abbreviated evaluation suite (5 representative queries across baseline configurations).
- `--seed <int>`: Sets a fixed random seed for reproducible LLM token generation.
- `--model <name>`: Explicitly specifies a model file in `models/`.
- `--configs <names>`: Selects specific RAG configurations (e.g., `cfg_eval_full`, `cfg_no_rag`).

Results are exported to `logs/benchmarks/` in CSV, JSON, and tabular text formats.

The curated evidence used in the LHXT 2026 article is available under
`reproducibility/lhxt2026/`. That package contains numeric run data, response
hashes, anonymized teacher ratings, verification scripts, and reproducible
figures. It excludes session logs, system logs, scanned forms, full generated
responses, and retrieved textbook passages.

---

## Repository Structure

```text
PocketMentorEDU/
├── app/                  # Application core logic
│   ├── api.py            # FastAPI endpoints and state management
│   ├── benchmark.py      # Automated benchmarking and metric collection
│   ├── cache_models.py   # Embedding and cross-encoder pre-caching
│   ├── crypto.py         # AES-256 local database encryption utilities
│   ├── evaluator.py      # Automated response indicator calculation
│   ├── icons.py          # SVG and interface iconography
│   ├── ingester.py       # Document ingestion and chunking pipeline
│   ├── main.py           # Application entry point and orchestrator
│   ├── memory.py         # Session history and student profile tracking
│   ├── prompt_builder.py # Pedagogical prompt synthesis
│   ├── rag.py            # Hybrid retrieval and re-ranking engine
│   └── ui.py             # Interface integration helpers
├── diagrams/             # System architectural diagrams (Mermaid format)
├── frontend/             # Static web assets (HTML, CSS, JavaScript)
├── knowledge/            # Source educational documents for RAG indexing
├── prompts/              # Pedagogical scaffolding definitions and configs
│   ├── levels/           # CEFR proficiency profiles
│   ├── modes/            # Interaction strategies
│   └── subjects/         # Curated ESL subject instructions
├── reproducibility/      # Public evidence and verification scripts
│   └── lhxt2026/         # LHXT 2026 benchmark package
├── INICIAR.bat           # Windows runtime launcher
├── requirements.txt      # Python package dependencies
└── README.md             # Project documentation
```

---

## Offline Deployment Architecture

To support offline execution and controlled repetition:
- Setting the environment variables `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` isolates the runtime from external network calls.
- Model weights, tokenizers, and embeddings are read directly from local relative paths.
- Student interactions and generated embeddings remain strictly on the host system within `database/` and `sessions/`.
- A fixed sampling seed can reproduce a run in the observed software and hardware environment, but reproducibility across different environments is not assumed.

---

## License and Attribution

- No software license has yet been granted for the platform source code. Until a license is added, default copyright applies; contact the authors for reuse permissions.
- Language models (e.g., Qwen, Phi) are subject to their respective upstream licensing agreements.
- Included reference documentation in `knowledge/` is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).
