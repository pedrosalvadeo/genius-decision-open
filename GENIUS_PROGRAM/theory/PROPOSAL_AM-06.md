# Propuesta AM-06 — PVS primero solo cuando su ventaja es robusta a la ley

Estado: `PROPUESTA`. Espera la aprobación de Pedro.
- Redactada el 2026-10-21, a partir de una auditoría externa («Auditoría B») que Pedro pidió revisar. La auditoría propone que la PVS vaya antes que el bienestar en el orden del kernel.
- Reescrita el mismo día, después de que Pedro preguntara: «¿es inteligente elegir la de 0,85 si la de 0,80 da considerablemente más bienestar?». La primera versión elegía siempre la PVS más alta. Pedro aceptó cambiarla («Sí») por la regla de esta versión.
- **No cambia el orden producto de los cuatro criterios (S1, especificación §00): funciones, CAG, bienestar y PVS.** Solo agrega un modo a la regla de selección explícita, que ya existe (`selection.mode`: `none`, `unique`, `priority`).

## Qué dijo la auditoría y qué se comprobó

1. **Correcto.** `decision.py` compara las rutas con los cuatro criterios en conjunción, y `verifier.py` (`_CONSTRUCTOR_PARENTS["PAIR"]`) sigue la misma estructura. Ninguno de los dos suma criterios.
2. **No corresponde.** La auditoría contrasta el kernel con un `PVS_METHOD.md` v0.1, que no está en el repositorio. La especificación propia (`specification/00_SPECIFICATION.md`) pide «producto de cuatro criterios… ninguna escalarización ni prioridad implícita», y el kernel la cumple.
3. **Incompleto.** La auditoría dice que la PVS no filtra, pero la vida ya filtra: la restricción dura `task_all` (`require_all_scenarios`) saca del conjunto de candidatas a toda ruta que pierde la condición de vida en alguna hoja, antes de comparar.
4. **Propiedad del orden actual.** Si una ruta tiene menos PVS que otra, no puede dominarla. Por eso, entre las candidatas, alguna de PVS máxima siempre está en la frontera. Para priorizar la PVS no hace falta cambiar la comparación: alcanza con elegir dentro de la frontera.
5. **Ya decidido por Pedro (2026-10-18, opción 2).** Primero la condición de vida y la PVS, y después la mejor ruta de cada portador, mostrando los conflictos, sin sumar criterios. Esto rige hoy en `twin/genius_twin/route_search.py`, `beta/genius_beta/compare.py` (/comparar) y en el informe para empresas. **El kernel no lo sabe:** quien lo llama directamente por API o MCP recibe solo la frontera.

## Problema

1. La regla de Pedro vive en el código de cada aplicación. El kernel no la verifica, y no la recibe quien usa el kernel sin pasar por esas aplicaciones.
2. **Elegir siempre la PVS más alta no es inteligente.** La PVS depende de la ley de escenarios, es decir de cuánta probabilidad se le da a cada escenario, y esa ley suele ser incierta. Las leyes de los gemelos de campo están declaradas o certificadas con pocos datos (AM-02), y la del gemelo de la Tierra es 1/3 por escenario, porque el IPCC no da probabilidades. Si una ruta tiene 0,85 con la ley declarada y otra 0,80, pero con otra ley igual de defendible el orden se invierte, preferir la primera no protege más vida. Solo sacrifica el bienestar de alguien por un número que no se sabe si es cierto.
3. **Cuando la ventaja es cierta, sí debe ganar.** Perder la vida no tiene vuelta: una muerte o un colapso no se compensan con bienestar después, mientras que un bienestar menor casi siempre se puede recuperar.

## Propuesta

### A. Leyes admisibles

El decisor declara, antes de calcular, el conjunto de leyes admisibles $\mathcal{L}$:
- **Por defecto, toda ley sobre los escenarios declarados.** Es lo más prudente, y no requiere ningún dato más.
- **O una lista finita de leyes**, cada una con su procedencia y en el formato actual de `/law`. Por ejemplo, las tres candidatas de AM-02 o AM-02.1, o rangos publicados por una fuente. La ley declarada del modelo siempre forma parte de la lista.

Nunca se eligen leyes mirando los resultados.

### B. Ventaja robusta de PVS

La ruta $p$ tiene **ventaja robusta de PVS** sobre $q$ cuando:
- $\mathrm{PVS}_L(p) \ge \mathrm{PVS}_L(q)$ para toda ley $L \in \mathcal{L}$;
- y hay al menos una ley con desigualdad estricta.

Es decir, ninguna ley admisible pone a $p$ por debajo de $q$. Con «toda ley», esto equivale a comparar escenario por escenario: $p$ conserva la vida al menos en todos los escenarios en que $q$ la conserva, y en alguno más. Así se comprueba en tiempo finito.

**Ejemplo.**
- Hay tres escenarios. La ruta A conserva la vida en los escenarios 1 y 2, y la ruta B solo en el 1. A tiene ventaja robusta: ninguna ley la pone debajo.
- Ahora A conserva la vida en 1 y 2, y B en 1 y 3. Con una ley A tiene 0,85 y B 0,80, pero con otra, que da más peso al escenario 3, el orden se invierte. Ninguna tiene ventaja robusta, y la PVS no decide entre ellas.

### C. Nuevo modo de selección `life_pvs`

- `selection: {"mode": "life_pvs", "laws": "ALL" | [ ... ], "basis": [...]}`. Exige al menos una restricción `task_all`; sin ella el modelo es inválido (`INPUT_TYPE` en `/selection/mode`), porque sin el filtro de vida el modo no significa lo que dice.
- Con cobertura exhaustiva y frontera no vacía, el kernel calcula $M$: las rutas de la frontera a las que ninguna otra ruta de la frontera supera con ventaja robusta de PVS.
  - Si $|M| = 1$, selecciona esa ruta.
  - Si $|M| > 1$, devuelve `SELECTION_NOT_UNIQUE`, informa $M$ y no elige. Esas rutas quedan con el bienestar de cada portador a la vista; el gemelo ya informa la mejor ruta de cada uno (`by_actor`). La PVS no decide entre ellas porque su diferencia depende de la ley.
- Sin cobertura exhaustiva o sin frontera, rige lo de hoy: `SELECTION_SCOPE` o `SELECTION_EMPTY`.
- **Nunca elige una ruta dominada:** solo se elige dentro de la frontera.
- **No usa ningún umbral de tolerancia inventado.** La única fuente de incertidumbre que se admite es la ley, y la declara el decisor.

### D. Verificación

- `verifier.py` recalcula la PVS de cada ruta de la frontera bajo cada ley de la lista y comprueba $M$ y la selección. Con `ALL`, hace la comparación escenario por escenario a partir de los veredictos de las hojas ya certificados y del mapa de escenarios. En el grafo de constructores, `SELECTION` pasa a tener como padres `{FRONTIER, VPROB, SCENARIOS}`.
- Los modos existentes no cambian. Los casos que hoy declaran `none`, `unique` o `priority` dan exactamente el mismo resultado; las pruebas de conformidad lo comprueban.

### E. Gemelos y aplicaciones

- `stockflow_compiler` acepta `selection: "life_pvs"` cuando `require_all_scenarios` es verdadero. Los casos de campo siguen con `none` hasta que Pedro decida cambiarlos.
- `law_range` sigue informando la PVS mínima y máxima de cada ruta. Además, el gemelo informa qué pares de rutas tienen ventaja robusta.
- La búsqueda de rutas hoy elige campeones entre las rutas de PVS más alta con la ley declarada. Pasa a usar la ventaja robusta, para que el kernel y las aplicaciones digan lo mismo. `/comparar` y el informe para empresas ya muestran el filtro de vida y el rango de PVS; agregan la ventaja robusta.

## Lo que esta propuesta no hace

- **No da más peso a la PVS que al bienestar en la comparación.** La frontera no cambia.
- **No agrega un modo «Pareto para decisiones de bajo impacto».** Decidir qué decisión es de bajo impacto sería una prioridad implícita, y por ahí se puede rebajar la vida.
- **No cambia bienestar por vida.** Si el bienestar extra de una ruta ayuda a sostener la vida, por ejemplo menos pobreza, eso se modela dentro de la condición de vida, no se compensa por fuera.
- **No convierte las fronteras planetarias en restricciones con nombre.** Hoy entran como condición de vida: el informe para empresas etiqueta cada stock con uno de los 9 límites. Nombrarlas en el kernel es otro trabajo.
