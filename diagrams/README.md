# Diagramas Técnicos — PocketMentorEDU

> **Generados por:** Antigravity AI  
> **Fecha:** 2026-03-17  
> **Versión analizada:** v2.0 ESL Edition  
> **Formato:** Mermaid (renderizable en GitHub, Notion, Obsidian, mermaid.live)

---

## Índice de Figuras

| # | Archivo | Tipo | Descripción |
|---|---------|------|-------------|
| 1 | [fig1_architecture_overview.md](./fig1_architecture_overview.md) | `flowchart TB` | **Arquitectura General por Capas** — 9 capas técnicas desde el launcher hasta el frontend |
| 2 | [fig2_rag_pipeline.md](./fig2_rag_pipeline.md) | `flowchart TD` | **Pipeline RAG Híbrido** — 9 fases del ciclo de inferencia por mensaje |
| 3 | [fig3_startup_flow.md](./fig3_startup_flow.md) | `flowchart TD` | **Ciclo de Inicialización** — Arranque completo del sistema desde `INICIAR.bat` |
| 4 | [fig4_class_diagram.md](./fig4_class_diagram.md) | `classDiagram` | **Diagrama de Clases UML** — 8 clases con atributos, métodos y relaciones |
| 5 | [fig5_sequence_diagram.md](./fig5_sequence_diagram.md) | `sequenceDiagram` | **Diagrama de Secuencia** — Ciclo de vida completo de una pregunta del estudiante |
| 6 | [fig6_knowledge_graph.md](./fig6_knowledge_graph.md) | `graph LR` | **Knowledge Graph Conceptual** — Entidades, propiedades y relaciones semánticas |

---

## Cómo visualizar

### Opción A — mermaid.live (recomendado para artículo)
1. Abre [https://mermaid.live](https://mermaid.live)
2. Pega el bloque de código Mermaid de cualquier figura
3. Exporta como **SVG** (calidad vectorial para artículo) o **PNG**

### Opción B — GitHub
Los archivos `.md` se renderizan automáticamente en GitHub si el repositorio los contiene.

### Opción C — VS Code
Instala la extensión **"Markdown Preview Mermaid Support"** para previsualizar localmente.

---

## Descripción de Capas (Figura 1)

| Capa | Módulo | Responsabilidad técnica |
|------|--------|------------------------|
| ⓪ Launcher | `INICIAR.bat` + `main.py` | Arranque, variables de entorno offline, orquestación del ciclo de vida |
| ① Hardware | `detect_hardware()` | Detección CPU/GPU/RAM, ajuste dinámico de `n_ctx` |
| ② Seguridad | `crypto.py` | AES-256-GCM + PBKDF2 (600K iter.) sobre `knowledge/` y `database/` |
| ③ Ingesta | `ingester.py` | Extracción multi-formato, chunking Parent/Child, embeddings batch |
| ④ Motor RAG | `rag.py` | Vector coseno + BM25 + RRF + Parent-Doc Retrieval + CrossEncoder |
| ⑤ LLM + Prompts | `prompt_builder.py` | 7 áreas ESL × 3 niveles CEFR × 4 modos pedagógicos + inferencia |
| ⑥ Memoria/Indicadores | `memory.py` + `evaluator.py` | Ventana deslizante, compresión LLM e indicadores Jaccard/coseno |
| ⑦ API | `api.py` + `uvicorn` | REST endpoints + SSE streaming asíncrono |
| ⑧ Frontend | `frontend/*.html/js/css` | UI neumórfica, offline 100%, sin frameworks externos |

---

## Tecnologías representadas

```
llama-cpp-python      → Inferencia LLM local (GGUF)
sentence-transformers → Embeddings (paraphrase-multilingual-MiniLM-L12-v2) 
                        + Re-ranking (ms-marco-MiniLM-L-6-v2)
rank-bm25             → Búsqueda léxica BM25Okapi
FastAPI + Uvicorn     → Servidor ASGI con SSE nativo
PyMuPDF               → Extracción de texto PDF
cryptography          → AES-256-GCM + PBKDF2
numpy                 → Almacenamiento y operaciones vectoriales
psutil                → Detección de hardware
```
