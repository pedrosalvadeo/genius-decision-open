# Los 8 módulos como componentes del gemelo

Pedro, 17/10/2026: el módulo 0 lo sistematiza el gemelo; el módulo I también sirve al gemelo, pero sobre tantos escenarios (gemelos) como establezcan sus rutas. Cada módulo se sistematiza como componente de un sistema mayor.

Cada evaluación de un gemelo entrega ahora `canonical_results.modules` (`genius_twin/modules.py`): qué encarna cada módulo, qué recibe, qué entrega y su estado. El registro lee resultados; no calcula ninguno.

| Módulo | Lo encarna | Recibe | Entrega |
|---|---|---|---|
| 0 Representación | El gemelo: existencias, capacidades, historia | Fuentes y afirmaciones citadas | Estado inicial, historias, información |
| V Futuros | Rutas × escenarios: cada par es un **gemelo proyectado** | Estado inicial, rutas, escenarios | Trayectorias causales |
| I Funcionalidad | Funciones del sistema medidas en cada gemelo proyectado | Gemelos proyectados, `functions` | Perfil funcional por estado y terminal por escenario |
| II Multiescala | Subsistemas unidos por interfaces | Gemelos proyectados, `subsystems`, `interfaces` | Vista por subsistema, flujo por interfaz, recomposición exacta |
| III Capacidad generativa | Organizaciones (firmas de capacidades) | Gemelos proyectados | CAG posible y robusta por ruta |
| IV Bienestar | Portadores y dimensiones en el tiempo | Gemelos proyectados, vínculos | Perfil por escenario, paso, portador y dimensión |
| VI Evidencia y PVS | Condición de vida y ley de escenarios con procedencia | Gemelos proyectados, ley | PVS por ruta y rango bajo toda ley |
| VII Decisión | Comparación conjunta y frontera | I, II, III, IV, VI | Factibles, frontera, selección |

El orden de cálculo sigue el DAG de la especificación (05 §1), no la numeración: 0 → V → {I, II, III, IV, VI} → VII.

Estados: `FILLED`, `NEUTRAL` (módulo I sin funciones declaradas), `SINGLE_SYSTEM` (módulo II sin subsistemas declarados), `NO_LAW`, `NO_LIFE_CONDITION`, `MISSING`.

## Módulo I: funciones

Campo opcional `functions` del modelo `STOCK_FLOW_FINITE_V1`. Cada función tiene `id`, `label`, `serves` (portadores a los que sirve), `measure` y `when` (predicados de existencia o capacidad, como las reglas de las rutas).

- `current`: 1 si todos los predicados se cumplen en ese estado, 0 si no.
- `cumulative`: cantidad de estados hasta ese, incluido, en que se cumplieron.

El compilador crea un índice funcional FP1 por función, con calibración identidad sobre los valores alcanzados, una medición en cada estado alcanzado y una reducción que agrupa estados con el mismo perfil. El estado FP1 compilado es la historia completa, así que una medida acumulada es función del estado. El kernel compara perfiles terminales por escenario. `decision.functional_comparison` da el orden producto por escenario y sobre todos, sin sumar funciones. Sin `functions`, el perfil queda neutro como antes.

Funciones de los casos reales:

- Lake Mead: Glen Canyon opera con Powell en 3.510 pies o más; Mead en 1.000 pies o más. En el año mínimo, liberar 6 millones cumple Glen Canyon 11 meses y liberar 7, 8.
- Denver: embalses en 50 % o más, el mínimo de 2003. Reanudar el riego en mayo lo pierde en el invierno seco.
- Mendoza: Potrerillos con margen para crecidas (90 % o menos), umbral elegido por el modelizador.

En los tres casos la frontera no cambia: el bienestar sigue siendo incomparable entre portadores.

## Módulo II: subsistemas e interfaces

Campos opcionales `subsystems` (cada uno con sus existencias y portadores; deben repartir todas las existencias) e `interfaces` (`source` y `target`, dos subsistemas). En cada paso, una acción ejecutada que retira de las existencias del origen lleva sus depósitos a las del destino; la interfaz acumula ese flujo.

El compilador agrega un puerto FP1 por interfaz y una vista por subsistema (sus existencias, las interfaces que toca y la consulta, que es el testigo común κπ de 02 §4.2). El kernel comprueba que las vistas recomponen exactamente la relación de cada ruta (G07). Sin subsistemas queda la vista única de antes.

- Lake Mead: Powell con Glen Canyon y Mead con la cuenca baja; la interfaz es la liberación adicional a 6 millones (931 mil acre-pies con 7 millones).
- Denver: embalses y jardines, unidos por el riego exterior.
- Mendoza: Potrerillos, riego y lagunas, unidos por las entregas de riego y la ecológica.

Con esto los tres gemelos tienen los 8 módulos llenos.

## Siguiente: gemelo de gemelos

La cuenca del Colorado como sistema mayor que une Mead y Denver, con portadores comunes que no se cuentan dos veces. FP1 no admite transporte entre dos modelos (02 §2.4), así que esa composición necesita una capa propia por encima de cada gemelo.
