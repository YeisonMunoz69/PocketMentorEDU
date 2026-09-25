# Paquete de reproducibilidad LHXT 2026

Este directorio contiene la evidencia pública del artículo *Evaluación de modelos compactos para tutoría de inglés sin conexión: estabilidad y límites de un benchmark RAG*. El paquete permite reconstruir las estadísticas y las cuatro figuras sin publicar sesiones de uso, registros del sistema, formularios escaneados, comentarios docentes sin anonimizar ni fragmentos extensos del libro utilizado como corpus.

## Alcance

La prueba comprende 196 ejecuciones principales, formadas por catorce preguntas, siete configuraciones y dos modelos. El análisis de estabilidad añade 140 ejecuciones de `cfg_eval_full`: cuatro semillas por modelo y una repetición de la semilla 42 como control. La valoración docente contiene veinte filas, correspondientes a diez respuestas calificadas de forma independiente por dos docentes.

Los indicadores automáticos describen apego al material recuperado y propiedades de la salida. No constituyen medidas de calidad pedagógica ni de aprendizaje. Las pruebas se realizaron sin estudiantes.

## Contenido

- `data/benchmark_main.csv`: 196 ejecuciones principales, sin texto generado.
- `data/seed_runs.csv`: 140 ejecuciones con semilla, con hashes de respuestas y contextos, pero sin su contenido textual.
- `data/questions.csv`: banco de doce preguntas de contenido y dos sondas fuera de alcance.
- `data/configurations.csv`: siete configuraciones del benchmark.
- `data/teacher_ratings_anonymized.csv`: calificaciones, decisiones de uso y enlace con el puntaje automático; no contiene nombres ni comentarios libres.
- `scripts/build_public_data.py`: deriva las tablas públicas desde los registros locales.
- `scripts/verify_results.py`: recalcula las cifras principales y comprueba los valores publicados.
- `scripts/figuras_articulo_es.py`: regenera las cuatro figuras en español desde los datos públicos.
- `verification_report.json`: salida de la verificación cuantitativa.
- `SOURCE_FILES.sha256`: huellas de los archivos locales utilizados para construir el paquete.
- `MANIFEST.sha256`: huellas de los archivos públicos de esta carpeta.

`SOURCE_FILES.sha256` identifica los registros originales, pero esos archivos no se publican completos porque algunos contienen respuestas generadas y fragmentos recuperados del libro. Los hashes permiten comprobar que una reconstrucción posterior partió de los mismos archivos locales.

## Verificación pública

Desde la raíz del repositorio:

```powershell
python reproducibility/lhxt2026/scripts/verify_results.py
python reproducibility/lhxt2026/scripts/figuras_articulo_es.py --overwrite
python reproducibility/lhxt2026/scripts/make_manifest.py
```

Estos comandos utilizan únicamente los CSV incluidos en el paquete. El script
`build_public_data.py` se conserva para la trazabilidad interna de los autores:
reconstruye los CSV públicos desde los registros originales, que no se publican
porque contienen respuestas completas y fragmentos recuperados del libro.

La comprobación estadística requiere SciPy. La generación de figuras requiere Matplotlib, NumPy y Pillow; `scienceplots` es opcional. Las versiones utilizadas para la verificación local se registran en `ENVIRONMENT.md`. Ese archivo describe el entorno de comprobación del paquete y no sustituye las versiones originales cuando estas no quedaron registradas durante la ejecución.

## Datos docentes

Los docentes autorizaron el uso de sus calificaciones y la mención de sus nombres en el artículo. El conjunto público conserva identificadores genéricos y excluye formularios escaneados y comentarios libres. Esta decisión reduce el riesgo de publicar información que no era necesaria para reproducir las estadísticas reportadas.

## Licencias y atribución

El repositorio aún no concede una licencia para reutilizar el código. Mientras no se incorpore una licencia aprobada por los autores y la institución, se aplica el derecho de autor por defecto. El libro *College ESL Writers: Applied Grammar and Composing Strategies for Success* se distribuye bajo CC BY-NC-SA 4.0 y no se duplica dentro de este paquete.
