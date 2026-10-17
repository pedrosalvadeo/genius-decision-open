# Archivo histórico de proyecciones de Lake Mead

- `transcribed_2015_2026.csv`: Lake Mead en los 24-Month Study de enero, abril, julio y octubre, de 2015 a 2026. Incluye los escenarios más probable, mínimo y máximo, salvo los de julio (Reclamation publica mínimo y máximo en agosto).
  - **Provisional.** Las filas se transcribieron leyendo los PDF con un lector de páginas que resume, no con un analizador determinista.
  - Control hecho: las filas históricas coinciden entre escenarios en cada estudio.
  - Los estudios que no se pudieron leer están en `transcribed_failures.txt`.
- `studies.csv`, cuando exista: la cosecha determinista del nodo de historia (`.github/workflows/genius-node.yml`, rama `node-history`), con `pdftotext` y el SHA-256 de cada PDF.
  - Reemplaza a la transcripción.
  - La transcripción queda como segunda lectura independiente: cada diferencia entre ambas es una alarma de medición.

Contrastar y aprender (desde la raíz):

```bash
python twin/history/hindcast.py summary twin/history/lake_mead/transcribed_2015_2026.csv
python twin/history/hindcast.py learn twin/history/lake_mead/transcribed_2015_2026.csv --lake mead --lead 12 --phase-size 8
```
