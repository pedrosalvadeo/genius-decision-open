# La Tierra: clima y bosques, 2025-2105

Primer gemelo de la Tierra. Usa los mismos ocho módulos y el mismo kernel que los casos de agua y de sangre. `world.json` lo genera `build.py` a partir de extractos citados.

El nodo de historia comprueba cada cita contra la página viva con `twin/history/source_quotes.py` y `twin/history/earth_2026/quotes.json`. Varias citas vienen de fuentes secundarias que reproducen el texto original: el cuadro del IPCC, el capítulo 1 del AR6 y el Acuerdo de París. Cada número citado lleva su cita; los demás son hipótesis o decisiones declaradas.

## Situación (fuentes, 2015 a 2025)

- La Tierra ya cruzó 7 de los 9 límites planetarios (Planetary Health Check 2025).
- En 2024 el calentamiento fue de 1,52 °C, de los cuales 1,36 °C son humanos. Para 1,5 °C al 50 % quedaban 130 GtCO2 desde 2025 (Forster et al. 2025).
- El presupuesto de CO2 para 2 °C desde 2020 era de 1150, 1350 y 1700 GtCO2, con 67, 50 y 33 % de probabilidad de no pasarlo (IPCC AR6). Entre 2020 y 2024 se emitieron cerca de 200 GtCO2.
- En 2025 se emitieron 42,2 GtCO2, contando fósiles y uso del suelo (Global Carbon Budget 2025).
- Con las políticas actuales el mundo va a 2,8 °C (PNUMA 2025).
- Hay 4140 Mha de bosque y se deforestan 10,9 Mha por año (FAO, FRA 2025).
- El IPCC no asigna probabilidades a sus escenarios socioeconómicos.

## Modelo

El modelo tiene ocho décadas, de 2025 a 2105.

**Rutas.** Son decisiones de la humanidad. Cada década, la ruta mantiene una fracción del ritmo de emisiones y deforestación de 2025:

| Ruta | Fracción por década | CO2 2025-2105 |
|---|---|---|
| `fast`: a cero en 2045 | 75, 25 % | 422 GtCO2 |
| `medium`: a cero en 2065 | 100, 75, 50, 25 % | 1055 GtCO2 |
| `slow`: a cero en 2085 | 100, 75, 50, 50, 25, 25 % | 1371,5 GtCO2 |
| `current_policies` | 100 % siempre | 3376 GtCO2 |

**Escenarios.** Representan la respuesta del clima a cada tonelada de CO2, y el presupuesto para 2 °C desde 2025 depende de ella:
- más sensible: 950 GtCO2;
- central: 1150 GtCO2;
- menos sensible: 1500 GtCO2.

La ley es un tercio para cada escenario, declarada a partir de las probabilidades del IPCC. No es una ley empírica AM-02, porque el clima del siglo no se repite 30 veces. Las trayectorias del IPCC entran como rutas y no como escenarios, por eso no necesitan probabilidad.

**Condición de vida.** No superar el presupuesto de 2 °C, la línea superior del Acuerdo de París, en ninguna década. Los portadores vivos son las generaciones futuras y las otras especies.

**Bienestar.**
- Generaciones futuras y personas de hoy: el presupuesto que queda.
- Otras especies: los bosques.
- Economías fósiles: el CO2 que pueden emitir.

**Funciones (módulo I):** protección frente al calentamiento (`safety`) y bosques no menores que en 2025 (`ecosystems`).

### Hipótesis para revisar

- El presupuesto de 2025 se obtiene restando 200 GtCO2 al de 2020. El Global Carbon Budget 2025 da cerca de 1055 GtCO2 al 50 % desde 2026.
- Los escenarios representan los tercios de forma optimista. El tercio más sensible estaría mejor representado por el presupuesto del 83 % (900 GtCO2 desde 2020), que no se pudo verificar textual. Por eso las PVS de las rutas frágiles pueden estar sobrestimadas.
- Las rutas son escalones por década, y la deforestación baja al mismo ritmo que las emisiones.
- No se modelan emisiones negativas, gases distintos del CO2 por separado ni puntos de inflexión.
- La expansión de bosque es de 6,78 Mha por año en todas las rutas. Incluye plantaciones.
- No se modelan costos de mitigación ni daños económicos.
- Cuando una ruta agota el presupuesto, el modelo deja de registrar sus emisiones posteriores. Su bienestar después de ese punto no tiene sentido, y la condición de vida ya la descarta.

## Resultado del kernel

| Ruta | Más sensible | Central | Menos sensible | PVS (ley declarada) | PVS bajo toda ley |
|---|---|---|---|---|---|
| A cero en 2045 | conserva | conserva | conserva | 1 | 1 |
| A cero en 2065 | pierde (2055-2065) | conserva | conserva | 2/3 | 0 a 1 |
| A cero en 2085 | pierde | pierde | conserva | 1/3 | 0 a 1 |
| Políticas actuales | pierde | pierde | pierde | **0** | **0** |

- **La trayectoria actual tiene PVS = 0 bajo cualquier ley.** Agota el presupuesto de 2 °C entre 2045 y 2065, según cuán sensible sea el clima.
- Sólo bajar a cero en 2045 conserva la condición de vida en los tres escenarios. Como es la única ruta viable, también es la mejor para cada portador, y no queda conflicto que elegir entre las rutas que conservan la vida.
- Con 1,5 °C (130 GtCO2 desde 2025), todas las rutas la incumplirían en todos los escenarios antes de 2030.
- **Límite:** cinco de los siete límites planetarios cruzados (agua, nitrógeno, fósforo, acidificación y entidades nuevas) todavía no están en el gemelo. La PVS de la Tierra con todos ellos sólo puede ser igual o menor.

Para reproducirlo, desde la raíz: `PYTHONPATH=twin:kernel python -m unittest twin.tests.test_case_earth`.
