# Lake Mead y Lake Powell, año hidrológico 2027

Tercer caso real del gemelo dinámico. `world.json` lo genera `build.py` a partir de los cuatro 24-Month Study de octubre de 2026 del Bureau of Reclamation (más probable con 6 y con 7 millones de acre-pies, mínimo probable y máximo probable), el comunicado de Interior del 21/8/2026 y una nota de Hoodline. Las filas de las tablas están transcritas celda por celda (cota en pies / almacenamiento en miles de acre-pies). Cada número citado lleva su cita; los demás son hipótesis o decisiones declaradas.

A diferencia de Denver y Mendoza, los escenarios no son del modelizador: son las tres afluencias que publica Reclamation cada mes.

## Situación (fuentes, octubre 2026)

- Fin de septiembre de 2026: Mead 1.037,80 pies (6.827 mil acre-pies); Powell 3.518,08 pies (5.155).
- Directrices 2027-2028: Powell libera entre 6,0 y 7,0 millones de acre-pies en 2027, el volumen se decide en abril y el objetivo es mantener 3.510 pies o más.
- Entregas a la cuenca baja reducidas 1,25 millones de acre-pies en 2027.
- Más probable con 6 millones: Mead toca 1.007,73 pies en julio de 2027. Con 7 millones: 1.015,68 pies en mayo.
- Mínimo probable (6 millones): Powell baja a 3.497,03 pies en septiembre de 2027.

## Modelo

Unidad: miles de acre-pies a fin de mes. Doce pasos mensuales, de octubre de 2026 a septiembre de 2027. Dos existencias: Mead y Powell.

| Opción | Regla |
|---|---|
| `release_6` | Powell libera 6 millones de acre-pies en el año operativo 2027 |
| `release_7` | Powell libera 7 millones: de mayo a septiembre pasan a Mead 170, 274, 203, 216 y 68 mil acre-pies más |

Escenarios: afluencia mínima, más probable y máxima. Tarea operacional: Powell en 3.510 pies o más (≈4.724 mil acre-pies) y Mead en 1.000 pies o más (≈4.478) todos los meses. Bienestar: agua en Mead para los usuarios de la cuenca baja y agua en Powell para la operación de Glen Canyon Dam (representación elegida por el modelizador). Sin ley de probabilidad.

Cuatro de las seis combinaciones reproducen exactamente un estudio publicado (Mead): 6 millones con afluencia más probable y mínima, y 7 millones con afluencia más probable y máxima.

### Hipótesis y decisiones para revisar

- El efecto de liberar 7 en vez de 6 millones se toma de la diferencia entre los dos estudios más probables y se supone igual con cualquier afluencia. Con él se arman los dos cruces sin estudio (mínima con 7, máxima con 6).
- Powell queda hasta 14 mil acre-pies por debajo del estudio de 7 millones, porque no se modela su menor evaporación. El sesgo es prudente.
- Los volúmenes a 3.510 pies (Powell) y 1.000 pies (Mead) se interpolan linealmente entre filas publicadas.
- 1.000 pies en Mead es una referencia elegida por el modelizador; 3.510 pies en Powell es el objetivo oficial.

## Resultado del kernel

Revisión del 17/10/2026: la tarea es una condición de vida (Lake Mead sobre su nivel muerto de 895 pies, representado con 2.547 mil acre-pies) y la ley es un tercio por afluencia, el candidato calibrado de AM-02 sobre 13 octubres. Revisión del 18/10/2026: AM-02 la admite sobre los últimos 30 años de afluencia no regulada de Powell (1996-2025, `twin/history/powell_law.py`); con el registro completo desde 1964 admitiría 12/65, 27/65 y 2/5.

- PVS = 1 con ambas liberaciones, con la ley declarada y con cualquier otra: en 2027 ninguna combinación acerca Mead al nivel muerto. El mínimo es 4.696 mil acre-pies (6 millones, afluencia mínima, julio).
- Bienestar: en cada afluencia, liberar 7 es mejor para la cuenca baja (más agua en Mead) y peor para Glen Canyon (menos en Powell). Las opciones no se pueden ordenar sin sumar portadores, así que la frontera tiene las dos y no hay selección.
- Con 7 millones y afluencia mínima Powell termina en 3.141 mil acre-pies, por debajo de los 4.724 que corresponden al objetivo operativo de 3.510 pies (con 6 millones, 4.072). Ese objetivo ya no es la tarea; se ve en la dimensión de bienestar de Powell.
- Las directrices permiten liberar menos de 6 millones tras consultas. No hay proyección publicada para eso, así que el modelo no lo representa.

Reproducir: `PYTHONPATH=twin:kernel python -m unittest twin.tests.test_case_lake_mead` desde la raíz.

## Predicción congelada y contraste

`prediction.json` congela, el 17/10/2026, el almacenamiento de Mead para cada opción y afluencia. Cada 24-Month Study (hacia el día 15) publica como dato histórico el almacenamiento del mes anterior; esa es la lectura que se contrasta. `observations.json` acumula esas lecturas sin recalibrar el modelo:

La predicción se congeló con la revisión anterior del mundo (tarea operativa, sin ley), que se conserva byte a byte en `frozen_world.json`. La revisión actual cambia la tarea y la ley, no las trayectorias, así que el contraste sigue valiendo.

```bash
python twin/cases/predictions.py contrast lake_mead_2027 --date 2026-10-31 --value <miles de acre-pies> --observed-at <ISO8601> --source "<estudio, URL y fila exacta>"
```

`twin.tests.test_predictions` falla si `world.json` cambia sin volver a congelar la predicción.
