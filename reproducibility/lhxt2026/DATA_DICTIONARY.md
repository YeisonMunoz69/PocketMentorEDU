# Diccionario de datos

## `benchmark_main.csv` y `seed_runs.csv`

| Campo | Descripción |
|---|---|
| `model` | Nombre abreviado del modelo evaluado. |
| `seed` | Semilla de muestreo. Está vacío en la corrida principal de marzo. |
| `run_role` | `main`, `analysis` o `determinism_control`. |
| `source_run` | Nombre del archivo local del que procede la fila. |
| `config_id` | Identificador de la configuración experimental. |
| `question_id` | Identificador estable de la pregunta. |
| `area` | Área temática del banco. |
| `level` | Nivel configurado para el estudiante. |
| `temperature`, `top_p`, `repeat_penalty` | Parámetros de muestreo. |
| `max_tokens` | Longitud máxima configurada para la salida. |
| `top_k_rag` | Número de fragmentos solicitados al recuperador. |
| `eval_mode` | Rama léxica (`fast`) o semántica (`full`). |
| `t_rag_s`, `t_gen_s`, `t_eval_s`, `t_total_s` | Duraciones registradas en segundos. |
| `overall_score` | Puntaje compuesto almacenado por el evaluador. |
| `grounding_score` | Comparación de la respuesta con el contexto. |
| `relevance_score` | Comparación de la consulta con los fragmentos recuperados. |
| `level_score` | Componente de longitud. No aparece en los registros principales antiguos. |
| `passed` | Indica si el puntaje superó el umbral implementado. No significa corrección pedagógica. |
| `is_fallback` | Activación del detector de respuesta alternativa. |
| `fallback_correct` | Resultado del detector frente a las sondas fuera de alcance. |
| `tokens_generated`, `tokens_per_sec` | Conteo de tokens y velocidad observada. |
| `kw_score` | Cobertura externa de seis palabras o expresiones esperadas. No es el índice de Jaccard. |
| `chunks_retrieved` | Número de fragmentos recuperados. |
| `prompt_chars` | Longitud del prompt, cuando el registro la conserva. |
| `timestamp` | Marca temporal escrita por el benchmark. |
| `response_sha256` | Huella de la respuesta completa. Permite comparar réplicas sin publicar el texto. |
| `context_sha256` | Huella del conjunto de fragmentos recuperados. |

## `teacher_ratings_anonymized.csv`

| Campo | Descripción |
|---|---|
| `response_code` | Código aleatorio de la respuesta valorada. |
| `teacher_id` | Identificador genérico del evaluador. |
| `model`, `question_id`, `area`, `level` | Clave de la respuesta evaluada. |
| `automatic_score` | Puntaje automático presentado de forma ciega durante el análisis posterior. |
| `is_fallback`, `tokens` | Activación del detector y longitud de la salida. |
| `correction`, `clarity`, `level_adequacy` | Calificaciones de 1 a 5. |
| `use_without_changes` | Decisión dicotómica sobre el uso de la respuesta sin modificaciones. |

## `questions.csv`

`expected_keywords` contiene seis palabras o expresiones esperadas separadas por `|`. Las sondas F1 y F2 no tienen palabras esperadas y usan `expect_fallback=true`.
