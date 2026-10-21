# Propuesta AM-06 — Selección «vida y PVS primero» dentro del kernel

Estado: `PROPUESTA`. Espera la aprobación de Pedro.
- Redactada el 2026-10-21, a partir de una auditoría externa («Auditoría B») que Pedro pidió revisar. La auditoría propone que la PVS vaya antes que el bienestar en el orden del kernel.
- **No cambia el orden producto de los cuatro criterios (S1, especificación §00): funciones, CAG, bienestar y PVS.** Solo agrega un modo a la regla de selección explícita, que ya existe (`selection.mode`: `none`, `unique`, `priority`).

## Qué dijo la auditoría y qué se comprobó

1. **Correcto.** `decision.py` compara las rutas con los cuatro criterios en conjunción, y `verifier.py` (`_CONSTRUCTOR_PARENTS["PAIR"]`) sigue la misma estructura. Ninguno de los dos suma criterios.
2. **No corresponde.** La auditoría contrasta el kernel con un `PVS_METHOD.md` v0.1, que no está en el repositorio. La especificación propia (`specification/00_SPECIFICATION.md`) pide «producto de cuatro criterios… ninguna escalarización ni prioridad implícita», y el kernel la cumple.
3. **Incompleto.** La auditoría dice que la PVS no filtra, pero la vida ya filtra: la restricción dura `task_all` (`require_all_scenarios`) saca del conjunto de candidatas a toda ruta que pierde la condición de vida en alguna hoja, antes de comparar.
4. **Propiedad del orden actual.** Si una ruta tiene menos PVS que otra, no puede dominarla. Por eso, entre las candidatas, alguna de PVS máxima siempre está en la frontera. Para priorizar la PVS no hace falta cambiar la comparación: alcanza con elegir dentro de la frontera.
5. **Ya decidido por Pedro (2026-10-18, opción 2).** Primero la condición de vida y la PVS, y después la mejor ruta de cada portador, mostrando los conflictos, sin sumar criterios. Esto rige hoy en `twin/genius_twin/route_search.py`, `beta/genius_beta/compare.py` (/comparar) y en el informe para empresas. **El kernel no lo sabe:** quien lo llama directamente por API o MCP recibe solo la frontera.

## Problema

La regla de Pedro vive en el código de cada aplicación. El kernel no la verifica, y no la recibe quien usa el kernel sin pasar por esas aplicaciones.

## Propuesta

### A. Nuevo modo de selección `life_pvs`

- `selection: {"mode": "life_pvs", "basis": [...]}`. Exige al menos una restricción `task_all`; sin ella el modelo es inválido (`INPUT_TYPE` en `/selection/mode`), porque sin el filtro de vida el modo no significa lo que dice.
- Con cobertura exhaustiva y frontera no vacía, el kernel calcula $M = \{p \in \text{frontera} : \mathrm{PVS}(p) = \max_{q \in \text{frontera}} \mathrm{PVS}(q)\}$.
  - Si $|M| = 1$, selecciona esa ruta.
  - Si $|M| > 1$, devuelve `SELECTION_NOT_UNIQUE`, informa $M$ y no elige. Entre esas rutas, la elección queda en manos de cada portador; el gemelo ya informa la mejor ruta de cada uno (`by_actor`).
- Por la propiedad 4, el máximo dentro de la frontera es el máximo entre todas las candidatas. El modo nunca elige una ruta dominada.
- Sin cobertura exhaustiva o sin frontera, rige lo de hoy: `SELECTION_SCOPE` o `SELECTION_EMPTY`.

### B. Verificación

- `verifier.py` recalcula $M$ con los valores de PVS ya certificados (`VPROB`) y comprueba la selección o la ausencia de selección. En el grafo de constructores, `SELECTION` pasa a tener como padres `{FRONTIER, VPROB}`.
- Los modos existentes no cambian. Los casos que hoy declaran `none`, `unique` o `priority` dan exactamente el mismo resultado; las pruebas de conformidad lo comprueban.

### C. Gemelos y aplicaciones

- `stockflow_compiler` acepta `selection: "life_pvs"` cuando `require_all_scenarios` es verdadero. Los casos de campo siguen con `none` hasta que Pedro decida cambiarlos.
- `/comparar`, la búsqueda de rutas y el informe para empresas siguen igual. Pueden leer la selección del kernel en vez de recalcularla.

## Lo que esta propuesta no hace

- **No da más peso a la PVS que al bienestar en la comparación.** Una ruta con más PVS y menos bienestar para alguien sigue siendo incomparable con la otra; la frontera no cambia.
- **No agrega un modo «Pareto para decisiones de bajo impacto».** Decidir qué decisión es de bajo impacto sería una prioridad implícita, y por ahí se puede rebajar la vida.
- **No convierte las fronteras planetarias en restricciones con nombre.** Hoy entran como condición de vida: el informe para empresas etiqueta cada stock con uno de los 9 límites. Nombrarlas en el kernel es otro trabajo.

## Pregunta abierta para Pedro

Con este modo, una ruta con PVS 0,85 se elige sobre otra con PVS 0,80, aunque la segunda dé mucho más bienestar a todos. Es la lectura literal de «vida y PVS primero». Si se prefiere tolerar diferencias pequeñas de PVS, haría falta un umbral declarado, y eso también cambiaría la matemática. Esta propuesta no lo incluye.
