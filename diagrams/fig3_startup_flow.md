# Figura 3 — Ciclo de Inicialización del Sistema

> **Descripción:** Diagrama de flujo que representa el proceso completo de arranque de
> PocketMentorEDU, desde la ejecución del launcher `INICIAR.bat` hasta que el servidor
> está disponible en `http://localhost:8000`. Incluye todas las comprobaciones, decisiones
> y pasos de configuración de cada componente.

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor":        "#162032",
    "primaryTextColor":    "#dce8f5",
    "primaryBorderColor":  "#3d6b94",
    "lineColor":           "#5b8db8",
    "secondaryColor":      "#0d1b2a",
    "tertiaryColor":       "#1a2d40",
    "background":          "#0d1b2a",
    "mainBkg":             "#162032",
    "clusterBkg":          "#0e1e30",
    "clusterBorder":       "#3d6b94",
    "edgeLabelBackground": "#162032",
    "fontFamily":          "Georgia, serif",
    "fontSize":            "13px"
  }
}}%%

flowchart TD

  %% ── INICIO ────────────────────────────────────────────────────────────
  A(["▶  INICIAR.bat\nexecuted by user"])

  %% ── VALIDACIONES BAT ─────────────────────────────────────────────────
  B{"engine/python/\npython.exe\nexists?"}
  BERR[/"❌ ERROR\nPython portable not found\nRun setup.bat first"/]
  C{"VC++ Redistributable\ninstalled?"}
  D["Install vc_redist.x64.exe\n(silently from engine/vcredist/)"]
  E["Set environment variables\n─────────────────────────────\nHF_HUB_OFFLINE=1\nTRANSFORMERS_OFFLINE=1\nGRADIO_ANALYTICS_ENABLED=False\nHF_HOME=models/.cache/huggingface\nSENTENCE_TRANSFORMERS_HOME=\n  models/.cache/sentence_transformers"]

  %% ── MAIN.PY ─────────────────────────────────────────────────────────
  subgraph INIT["main.py — Orquestación del arranque"]
    direction TB

    subgraph HW_STEP["① Hardware Detection  ·  detect_hardware()"]
      H1["psutil.cpu_count(logical=False)\n→ cpu_threads (mín. 2)"]
      H2["psutil.virtual_memory().total\n→ ram_gb"]
      H3["subprocess: nvidia-smi\n--query-gpu=name"]
      H4{"CUDA GPU\ndetected?"}
      H5["gpu_layers = 35"]
      H6["gpu_layers = 0\n(CPU only)"]
      H7["Determinar n_ctx:\n< 8 GB RAM  → 2048\n< 16 GB RAM → 4096\n≥ 16 GB RAM → 8192"]
      H1 --> H2 --> H3 --> H4
      H4 -->|"Sí"| H5
      H4 -->|"No"| H6
      H5 --> H7
      H6 --> H7
    end

    subgraph CRYPTO_STEP["② Crypto Manager  ·  setup_crypto()"]
      CR1["CryptoManager(BASE_DIR)"]
      CR2{"*.enc files in\nknowledge/ or database/?"}
      CR3["Prompt contraseña\npor consola"]
      CR4{"Contraseña\ncorrecta?"}
      CR5["CryptoManager.unlock_data()\nDescifra AES-256-GCM"]
      CR6[/"❌ EXIT(1)\nContraseña incorrecta"/]
      CR7["Modo abierto\n(sin cifrado activo)"]
      CR1 --> CR2
      CR2 -->|"Sí"| CR3 --> CR4
      CR4 -->|"Sí"| CR5
      CR4 -->|"No"| CR6
      CR2 -->|"No"| CR7
    end

    subgraph RAG_STEP["③ RAG Engine Init  ·  RAGEngine.__init__()"]
      RA1["RAGEngine(db_dir, know_dir)"]
      RA2{"chunks.json\nexists?"}
      RA3["_load_index():\n• Carga chunks.json (child)\n• Carga parents.json\n• np.load(embeddings.npy)\n• Verifica sincronía n_chunks==n_emb"]
      RA4["_build_bm25():\nBM25Okapi(tokenized_chunks)"]
      RA5["Índice vacío\n(se construirá en ingesta)"]
      RA1 --> RA2
      RA2 -->|"Sí"| RA3 --> RA4
      RA2 -->|"No"| RA5
    end

    subgraph ING_STEP["④ Ingesta de Documentos  ·  Ingester.run()"]
      IN1["Ingester(know_dir, db_dir)\n_get_embedder_cb = rag._get_embedder"]
      IN2["_load_hashes():\nLee file_hashes.json\nMigra rutas absolutas → relativas"]
      IN3["_find_new_files():\nMD5 hash comparison\nPara cada archivo en knowledge/"]
      IN4{"Archivos\nnuevos?"}
      IN5["Para cada nuevo archivo:\n_process_file(path)\n─────────────────────────\n• extract_pdf/txt/md/docx\n• Parent chunks: 1024 tokens\n• Child  chunks:  128 tokens\n• Guarda staging/{stem}.json"]
      IN6["_rebuild_index():\n• Consolida staging/*.json\n• chunks.json + parents.json\n• _generate_embeddings()\n  (batch_size=64)\n  → embeddings.npy"]
      IN7["Sin cambios → skip\n(tiempo de arranque < 1s)"]
      IN8["rag.reload():\nRecarga índice desde disco\nReconstruye BM25"]
      IN1 --> IN2 --> IN3 --> IN4
      IN4 -->|"Sí"| IN5 --> IN6 --> IN8
      IN4 -->|"No"| IN7 --> IN8
    end

    subgraph LLM_STEP["⑤ Carga del Modelo LLM  ·  AppState.__init__()"]
      LM1["find_model(args.model):\nsorted(models/*.gguf)[0]"]
      LM2{"Model file\nexists?"}
      LM3[/"❌ EXIT(1)\nNo .gguf found"/]
      LM4["Llama(\n  model_path,\n  n_ctx    = hw['n_ctx'],\n  n_threads= hw['cpu_threads'],\n  n_gpu_layers= hw['gpu_layers'],\n  verbose  = False\n)"]
      LM5["AppState.model_name\n= model_path.stem"]
      LM1 --> LM2
      LM2 -->|"Sí"| LM4 --> LM5
      LM2 -->|"No"| LM3
    end

    subgraph EVAL_STEP["⑥ Evaluador  ·  ResponseEvaluator"]
      EV1["ResponseEvaluator(logs_dir, mode='fast')"]
      EV2["set_embedder_cb(rag._get_embedder)\n(lazy loading compartido)"]
      EV1 --> EV2
    end

    subgraph API_STEP["⑦ API Server  ·  FastAPI + Uvicorn"]
      AP1["init_api(app_state, rag, evaluator, sess_dir)\nInyecta dependencias globales:\n_app_state, _rag, _evaluator, _sess_dir"]
      AP2["Mount /static → frontend/\nMount GET / → chat.html\nMount GET /dashboard, /settings..."]
      AP3["signal.signal(SIGINT, _shutdown)\nsignal.signal(SIGTERM, _shutdown)"]
      AP4["uvicorn.run(\n  fastapi_app,\n  host='127.0.0.1',\n  port=8000,\n  log_level='warning'\n)"]
      AP1 --> AP2 --> AP3 --> AP4
    end

  end

  %% ── FIN ────────────────────────────────────────────────────────────
  READY(["✅  Sistema listo\nhttp://localhost:8000\n────────────────────────\nLogs en logs/system.log\nFrontend accesible desde\ncualquier navegador local"])

  SHUTDOWN["_shutdown()\n──────────────────────\n1. evaluator.save_session_metrics()\n2. CryptoManager.lock()\n   (si is_unlocked)\n3. sys.exit(0)"]

  %% ── CONEXIONES ────────────────────────────────────────────────────
  A       --> B
  B       -->|"No"| BERR
  B       -->|"Sí"| C
  C       -->|"No"| D --> E
  C       -->|"Sí"| E
  E       --> INIT
  HW_STEP --> CRYPTO_STEP
  CRYPTO_STEP --> RAG_STEP
  RAG_STEP --> ING_STEP
  ING_STEP --> LLM_STEP
  LLM_STEP --> EVAL_STEP
  EVAL_STEP --> API_STEP
  AP4     -->|"Servidor activo"| READY
  READY   -->|"SIGINT / SIGTERM"| SHUTDOWN

  %% ── ESTILOS ────────────────────────────────────────────────────────
  classDef startEnd  fill:#1a3a5c,stroke:#5b9bd5,color:#ddeeff,rx:20,font-weight:bold
  classDef error     fill:#3a1a1a,stroke:#c05050,color:#ffaaaa
  classDef decision  fill:#252510,stroke:#b0a000,color:#ffe070
  classDef shutdown  fill:#2a1a30,stroke:#8050b0,color:#d0b0f0

  class A,READY startEnd
  class BERR,CR6,LM3 error
  class B,C,CR2,CR4,RA2,IN4,LM2,H4 decision
  class SHUTDOWN shutdown
```

## Tiempos de Arranque Estimados

| Paso | Sin cambios | Con 1 PDF nuevo (339 chunks) |
|------|-------------|-------------------------------|
| Hardware detection | ~100 ms | ~100 ms |
| Crypto (sin cifrado) | ~1 ms | ~1 ms |
| RAG index load | ~200 ms | ~200 ms |
| Ingesta + embeddings | **~0 ms** (skip) | **~3–8 min** (primera vez) |
| Carga modelo GGUF | ~15–45 s | ~15–45 s |
| Uvicorn bind | ~500 ms | ~500 ms |
| **Total** | **~20–50 s** | **~20 min (primera vez)** |
