# Lake Mead y Lake Powell, años hidrológicos 2027 y 2028

Extiende `lake_mead_2027` hasta septiembre de 2028 con los cuatro 24-Month Study de octubre de 2026 (más probable con 6 y con 7 millones de acre-pies, mínimo y máximo probable). Las filas de 2028 están en el archivo `twin/history/lake_mead/studies.csv`, con el sha256 de cada PDF; `build.py` las transcribe. El caso de 2027 queda intacto, porque su predicción está congelada y se contrasta con las lecturas.

## Qué agrega

- **Módulo V, dos años:** pasos mensuales hasta septiembre de 2027 y trimestrales en 2028 (diciembre, marzo, junio y septiembre), 16 pasos. Con 24 pasos mensuales la evaluación pesa 28 MB y supera el límite de producción (16 MB por evaluación, dentro de un presupuesto de 128 MiB para todas las bases); con trimestres pesa 15 MB. Lo que pasa dentro de cada trimestre de 2028 no se mide.
- **Módulo III, una capacidad que sigue al estado:** Glen Canyon Dam genera electricidad sólo con Powell en 3.490 pies o más (cota mínima de generación de Reclamation; unos 3.742 mil acre-pies, extrapolando el estudio mínimo). El campo nuevo `holds_when` hace que la capacidad exista exactamente en los estados que lo cumplen: se pierde bajo ese nivel y vuelve si Powell sube.
- **Módulo I:** una tercera función, estados con generación, junto a Powell en 3.510 pies y Mead en 1.000 pies.
- **Módulo II:** una segunda interfaz, la liberación de 2028 que la ruta de 7 millones deja en Powell.

## Rutas

| Ruta | Regla |
|---|---|
| `release_6` | Powell libera 6 millones en 2027 y lo que Reclamation proyecta para 2028 |
| `release_7` | Libera 7 millones en 2027 (931 mil acre-pies más hacia Mead de mayo a septiembre) y, según los estudios más probables, menos en 2028: Mead deja de recibir 327, 295 y 325 mil acre-pies en los trimestres de enero a septiembre |

Los estudios más probables muestran que la ventaja de Mead con 7 millones se devuelve casi entera en 2028: en septiembre de 2028 Mead queda 23 mil acre-pies por debajo de la ruta de 6.

## Resultado del kernel

- PVS = 1 con las dos rutas y con cualquier ley: Mead nunca se acerca a su nivel muerto.
- Con afluencia mínima, liberar 7 millones deja a Glen Canyon sin generar desde agosto de 2027 y al menos hasta marzo de 2028 (en el estudio mensual, hasta abril). Liberar 6 la mantiene, aunque en febrero de 2028 Powell queda a cerca de un pie de la cota.
- Con afluencia mínima, liberar 6 deja a Mead bajo 1.000 pies desde marzo de 2028; liberar 7, desde junio (en el estudio mensual, abril).
- Funciones: las rutas son incomparables (6 es mejor en generación y en 3.510 pies; 7 es mejor en Mead a 1.000 pies). Frontera con las dos, sin selección.
- Por actor, a dos años ninguna ruta es la mejor para la cuenca baja ni para Glen Canyon en todas sus coordenadas: la ventaja de cada una en 2027 se revierte en parte en 2028.
- La CAG no cambia: el kernel siempre incluye la organización de origen, así que perder una capacidad existente no la reduce. La pérdida se ve en la organización de cada paso y en la función de generación. Es un límite de la definición de CAG, descrito en `twin/docs/MODULES.md`.

## Hipótesis para revisar

- El efecto de 2027 y el de 2028 vienen de la diferencia entre los dos estudios más probables y se suponen iguales con cualquier afluencia. En la afluencia mínima Reclamation probablemente no liberaría 7 millones, y bajo 3.490 pies la presa además pierde capacidad de liberar, que no se modela.
- Octubre a diciembre de 2027 (3, 3 y 1 mil acre-pies, evaporación) no se modelan.
- Los extractos sobre la cota mínima de generación vienen del índice del buscador, porque la página de Reclamation no se pudo abrir desde el entorno de construcción.
- La ley de un tercio por afluencia fue calibrada por AM-02 para un año; para el segundo no está contrastada.

Reproducir: `PYTHONPATH=twin:kernel python -m unittest twin.tests.test_case_lake_mead_2028` desde la raíz.
