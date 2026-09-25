# Paquete de reproducibilidad LHXT 2026, versión 1.0.0

Esta versión acompaña el artículo *Evaluación de modelos compactos para tutoría
de inglés sin conexión: estabilidad y límites de un benchmark RAG*.

## Contenido

- 196 ejecuciones principales en dos modelos y siete configuraciones.
- 140 ejecuciones para el análisis de cuatro semillas y el control repetido de
  la semilla 42.
- Veinte calificaciones docentes anonimizadas.
- Cuatro figuras en SVG, PNG y PDF.
- Scripts para recalcular las estadísticas, regenerar las figuras y comprobar
  las huellas SHA-256 del paquete.

## Exclusiones deliberadas

No se publican respuestas completas de los modelos, fragmentos recuperados del
libro, registros de sesión, registros del sistema, formularios escaneados,
nombres de docentes ni comentarios libres. Los datos numéricos y las huellas de
las respuestas y los contextos permiten verificar los resultados reportados sin
divulgar ese contenido.

## Verificación

Desde la raíz del repositorio:

```powershell
python reproducibility/lhxt2026/scripts/verify_results.py
python reproducibility/lhxt2026/scripts/figuras_articulo_es.py --overwrite
python reproducibility/lhxt2026/scripts/make_manifest.py
```

Las dependencias y el entorno comprobado se describen en
`requirements-verification.txt` y `ENVIRONMENT.md`.

## Licencia

Esta versión no concede una licencia de reutilización para el código del
proyecto. Se aplica el derecho de autor por defecto hasta que los autores y la
institución aprueben una licencia explícita.
