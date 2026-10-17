# Archivo histórico de proyecciones de Lake Mead

- `transcribed_2015_2026.csv`: Lake Mead en los 24-Month Study de enero, abril, julio y octubre, de 2015 a 2026. Incluye los escenarios más probable, mínimo y máximo, salvo los de julio (Reclamation publica mínimo y máximo en agosto).
  - **Provisional.** Las filas se transcribieron leyendo los PDF con un lector de páginas que resume, no con un analizador determinista.
  - Control hecho: las filas históricas coinciden entre escenarios en cada estudio.
  - Los estudios que no se pudieron leer están en `transcribed_failures.txt`.
- `studies.csv`: la cosecha determinista del nodo de historia (`.github/workflows/genius-node.yml`, corrida 39011458727 del 2026-10-17, rama `node-history`), con `pdftotext` y el SHA-256 de cada PDF.
  - 383 estudios publicados de septiembre de 2009 a octubre de 2026: 200 más probables, 106 mínimos, 73 máximos y las variantes de 6 y 7 maf de octubre de 2026. Lake Mead y Lake Powell, 12 meses históricos y 24 proyectados por estudio.
  - Reemplaza a la transcripción.
  - Control cruzado: los 4497 valores que aparecen en ambas fuentes coinciden exactamente. La transcripción tiene 3 filas más (máximo de abril de 2025), que la cosecha no encontró.
  - Revisiones: 4 meses de Lake Powell (2009 y 2011–2012) cambiaron entre estudios, como mucho 11 kaf. Ningún valor de Lake Mead cambió.

Contrastar y aprender (desde la raíz):

```bash
python twin/history/hindcast.py summary twin/history/lake_mead/studies.csv
python twin/history/hindcast.py learn twin/history/lake_mead/studies.csv --lake mead --lead 12
```

## Lo que muestra el archivo completo (corrida del 2026-10-17)

Almacenamiento de Lake Mead, error = real − proyectado, en kaf:

| Plazo | Más probable: sesgo medio | Error absoluto medio | Real dentro de [mínimo, máximo] |
|---|---|---|---|
| 3 meses | +83 | 224 | 22 de 71 |
| 6 meses | +159 | 431 | 32 de 69 |
| 12 meses | +334 | 833 | 32 de 67 |
| 23 meses | +413 | 1414 | 36 de 64 |

- El rango mínimo–máximo de Reclamation contuvo la realidad en menos de la mitad de los casos, y las salidas por arriba y por abajo son parecidas. No es un intervalo de confianza.
- Con el archivo completo, ninguna corrección simple (mediana o media de errores pasados) mejora de forma estable el más probable a 12 meses: en 7 ensayos no hubo variante elegible o se rechazó en confirmación. A 3 y 6 meses se adoptaron correcciones en algunos ensayos y se rechazaron en otros. El resultado de la transcripción parcial (mejora del 20–30 %) no se sostiene.
- Lo que sí se sostiene es que hay que medir la incertidumbre en vez de tomarla de los escenarios publicados. Ese es el camino de la propuesta AM-02.

Bandas empíricas al 90 % (`hindcast.py bands`): el más probable más los cuantiles 5 % y 95 % de los últimos 120 errores conocidos, sólo con información publicada antes de cada estudio.

| Plazo | Real dentro de la banda | Ancho medio (kaf) | Ancho medio del rango de Reclamation (kaf) |
|---|---|---|---|
| 3 meses | 146 de 177 (82 %) | 931 | 231 |
| 6 meses | 154 de 171 (90 %) | 2053 | 567 |
| 12 meses | 148 de 159 (93 %) | 5042 | 1612 |
| 23 meses | 124 de 137 (91 %) | 6183 | 4180 |

- De 6 a 23 meses, las bandas cumplen la cobertura que declaran. A 3 meses se quedan cortas.
- La incertidumbre real a 12 meses es unas tres veces el rango publicado.
- Con ventanas de 36 errores o al 80 % la cobertura queda por debajo de lo nominal. Los errores están correlacionados en el tiempo.
