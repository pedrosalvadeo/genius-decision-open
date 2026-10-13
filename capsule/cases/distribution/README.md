# Caso real: distribuir las fuentes Genius

Pregunta: ¿qué formato transfiere estas mismas fuentes con menos bytes? Se construyeron tres archivos del mismo snapshot y se midieron sus tamaños y hashes. Ver measurement.json. Son observaciones reales de archivos, no valores sintéticos.

El criterio propuesto compara bytes enviados; el modelo excluye tiempo de CPU, compatibilidad y reintentos. El presupuesto comparativo equivale al tamaño del TAR. La ley puntual sólo identifica este inventario ya medido. No estima probabilidad de una transferencia futura ni PVS de la vida.

```bash
python3 capsule/genius.py evaluate capsule/cases/distribution/model.json --evidence capsule/cases/distribution/evidence.json --out /tmp/genius-distribution
python3 capsule/genius.py verify /tmp/genius-distribution
```

El caso conserva la medición del primer paquete producido. Al incorporar archivos nuevos, medir nuevamente y crear una versión nueva del caso, sin sustituir esa observación histórica. La receta de construcción se encuentra en capsule/build_publication.py; el SHA de cada archivo medido identifica exactamente la observación.
