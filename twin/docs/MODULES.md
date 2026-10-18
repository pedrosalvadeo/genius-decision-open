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

## Gemelo de gemelos: la federación

FP1 no admite transporte entre dos modelos (02 §2.4), así que `genius_twin/federation.py` (`genius-federation/1`) nunca fusiona modelos en una instancia. Cada gemelo miembro se evalúa y verifica con el kernel por separado, con los escenarios conjuntos renombrados dentro de él. La capa conjunta sólo lee resultados de los miembros.

- **Escenarios conjuntos:** cada uno nombra un escenario de cada miembro (sin repetir), con una ley conjunta.
- **Acoplamientos:** lo que mueve una interfaz de un miembro, paso a paso, escalado y con retardo, entra como drenaje (o entrada) en una existencia de otro. El destino se reevalúa una vez por combinación de rutas de sus fuentes. Un solo nivel: un destino no puede ser fuente.
- **Portadores comunes:** `shared_carriers` les da una sola identidad entre miembros, para no contarlos dos veces.
- **Resultado:** rutas conjuntas (producto de rutas), condición de vida conjunta por escenario (falla si falla en algún miembro), PVS conjunta y su rango bajo toda ley, y frontera por orden producto sobre bienestar paso a paso de cada portador, funciones terminales y PVS conjunta, sin sumas.

Primer caso, `cases/colorado_basin_2027/federation.json`: Denver y Lake Mead/Powell alineados por la nieve del alto Colorado (seco con mínimo, normal con más probable, húmedo con máximo). El riego exterior de Denver se repone en su mitad del alto Colorado (la fuente de la mitad de su suministro) y deja de llegar a Powell al paso siguiente. Reanudar el riego en mayo saca de Powell unos 28 mil acre-pies: mejor para los jardines de Denver, peor para Denver Water y para Glen Canyon. Las seis rutas conjuntas tienen PVS conjunta 1 y quedan en la frontera.

Cualquier agente la lee por API y MCP: `GET /api/twin/federations` y `/federations/<id>` (`twin_federations`, `twin_federation`) devuelven la especificación y el resultado congelado en `federation_result.json`. Se regenera con `python -m genius_twin.federation <caso>` y una prueba exige que coincida con lo que la federación calcula.

## Módulo VII: recomendación por actor

La frontera conjunta suele traer todas las opciones porque ninguna es mejor para todos. `decision.by_actor` responde a cada portador por separado: entre las rutas que mantienen la condición de vida (todas si ninguna la mantiene), cuáles no supera ninguna otra en sus propias coordenadas, que son sus condiciones de bienestar en cada escenario y paso y las funciones que le sirven. No se suman actores, escenarios ni pasos. La federación hace lo mismo con rutas conjuntas, y un portador común es un solo actor.

- Lake Mead: la cuenca baja, liberar 7 millones; Glen Canyon, liberar 6.
- Denver: la población, reanudar el riego (en mayo o con 70 %, no comparables entre sí); Denver Water, mantener la prohibición.
- Mendoza: regantes, lagunas y población, dotación reforzada con entrega ecológica; Irrigación, dotación de año seco.
- Cuenca del Colorado: para Glen Canyon, sólo que Denver mantenga la prohibición y Powell libere 6 millones.

## Módulo 0: gemelo vivo

La predicción congelada no se toca nunca; el gemelo vivo es otro modelo. `genius_twin/living.py` (`reanchor`) toma el modelo congelado y un paso con todo su estado observado (cada existencia y las capacidades presentes) y arma un modelo nuevo cuyo paso 0 es ese estado, con las reglas restantes de cada ruta y los eventos restantes de cada escenario. Si falta una existencia, no la completa con ninguna trayectoria: rechaza. Si dos escenarios dejan de diferir, lo dice. La ley, las hipótesis y las funciones quedan como estaban.

`python twin/cases/predictions.py live <caso> --date <fecha de un paso> --stock id=valor ... --capability ... --observed-at ... --source ...` evalúa ese gemelo y agrega a `<caso>/living.json` qué concluye ahora: factibles, frontera, mejor ruta por actor, PVS y la nueva trayectoria. Junto con `contrast` (cuánto se apartó la lectura de cada ruta y escenario) el gemelo aprende del sistema real sin recalibrar nada a escondidas. `lake_mead_2028` ya tiene su predicción congelada; la primera lectura real llega con el 24-Month Study de noviembre.

## Módulo VI: ley empírica de los inviernos de Denver

`twin/history/nrcs_snow.py` corre en el nodo de historia (GitHub Actions, porque este entorno no llega al NRCS) y baja la nieve del 1 de abril de 1991 a 2026 de las estaciones SNOTEL de las cuencas de Denver Water. `twin/history/snow_law.py` asigna cada año al invierno del modelo más parecido y aplica AM-02: un tercio cada uno queda descalibrado y se admite seco 4/39, normal 28/39, húmedo 7/39, con 36 resultados independientes. En Denver la PVS no depende de la ley, así que la decisión no cambia; sí cambia lo que el gemelo sabe: el húmedo de 150 % nunca ocurrió en 36 años.

## Módulo IV en el Colorado: por qué no se separan los estados todavía

Los recortes de 2027 y 2028 están fijados por estado (Arizona 760, California 440 y Nevada 50 mil acre-pies, México 250 por tratado) y no dependen de liberar 6 o 7 millones. Lo que sí distingue a los estados es la condición de vida: Las Vegas toma agua bajo el nivel muerto de Hoover (toma a 860 pies con bombeo de nivel bajo); Arizona, California y México dependen de que Hoover libere. Ningún escenario de 2027-2028 se acerca a 895 pies, así que separar portadores hoy no cambia ningún resultado. Conviene hacerlo cuando un escenario baje de 1.000 pies.

## Módulo III: capacidades que siguen al estado, y un límite de la CAG

Una capacidad puede declarar `holds_when`: existe exactamente en los estados cuyas existencias lo cumplen (se pierde y se recupera con el estado). Primer uso, `cases/lake_mead_2028` (mensual en 2027, trimestral en 2028, para caber en el límite de producción): Glen Canyon Dam genera electricidad sólo con Powell en 3.490 pies o más. Con afluencia mínima, liberar 7 millones en 2027 la deja sin generar desde agosto de 2027 hasta la primavera de 2028; liberar 6 la mantiene, pero deja a Mead bajo 1.000 pies desde marzo de 2028.

**Límite encontrado.** La CAG del kernel es el origen más lo que la receta logra (`kernel/genius_kernel/structural.py`, "Origin plus declared union/intersection"). Mide qué organizaciones nuevas genera una ruta, pero nunca castiga perder una capacidad que ya existía: las dos rutas de Mead 2028 tienen la misma CAG robusta. Hoy la pérdida se ve en la organización de cada mes y en una función (meses con generación). Propuesta (pendiente de aprobación, como AM-02): agregar a III una **CAG conservada**, las capacidades de origen que la ruta mantiene en todos los estados de todas las ramas, comparada por inclusión junto a la CAG actual en la decisión.

## Siguiente

Sumar portadores comunes reales (por ejemplo, la población que depende de varios embalses) y reemplazar las hipótesis de alineación y desvío por datos (archivos de pronósticos y desvíos de Moffat y Roberts).
