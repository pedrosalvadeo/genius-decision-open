# Propuesta AM-05 — Decisión dentro de una ventana de oportunidad

Estado: `ACEPTADA`. Pedro la aprobó el 2026-10-18 («Apruebo»).
- Redactada el 2026-10-18, después de que Pedro señalara que cada decisor tiene su propia capacidad de cálculo y su propia ventana de oportunidad: algunas decisiones admiten mucho tiempo y otras casi nada. Además la realidad cambia, y los gemelos deben ajustarse durante el cálculo previo a actuar.
- No modifica S1 ni el kernel FP1.

## Lo que ya está hecho sin cambiar la matemática

1. **Pasos comprometidos.** `twin/genius_twin/decision_window.py` recibe la ventana del decisor en segundos exactos:
   - el tiempo disponible;
   - la duración real de un paso;
   - cuánto falta para la acción del paso 1, contado desde el estado observado;
   - la antigüedad de esa observación cuando empieza el cálculo;
   - cuánto tarda en aplicarse una decisión;
   - la ruta que sigue ahora;
   - su costo medido.

   Las acciones que ocurren antes de que la decisión pueda actuar ya están decididas: siguen la ruta actual. El resultado es un modelo declarado común, y el kernel lo evalúa y verifica como a cualquier otro. Se sirve en `POST /cases/<cid>/window` y en la herramienta MCP `twin_decision_window`.
2. **Frescura.** Cada cálculo queda fijado a la evidencia con la que empezó, y su job nunca se reescribe. Cada job informa `elapsed_seconds`. `GET /jobs/<id>/freshness` (herramienta MCP `twin_job_freshness`) declara superado el resultado cuando hay una observación registrada durante el cálculo, después, o antes pero en una versión posterior. El gemelo vivo (`living.reanchor`) parte de la observación nueva, con menos pasos por delante, y por eso calcula más rápido.

**Ejemplo, banco de sangre del invierno 2026/27.** El paso es una semana y la campaña de donantes ocurre en las semanas 1 a 3:
- si la decisión actúa en la semana 2 o 3, las cuatro rutas siguen siendo distintas y la frontera no cambia: campaña, campaña con postergación, y postergación;
- si la decisión llega después de la semana 3, la campaña ya no es una opción: «campaña» queda igual a «seguir igual», y «campaña con postergación» queda igual a «postergar»;
- en ese caso la frontera se reduce a postergar las cirugías programadas. Seguir igual falla la condición de vida con gripe severa: su PVS es 2/3.

La ventana cambia la decisión, aunque la matemática es la misma.

## Problema que queda

Cuando el cálculo completo no entra en la ventana, hoy Genius no entrega nada: un tiempo agotado no prueba inviabilidad. El decisor actúa sin información, o sigue con lo que ya hacía.

Mediciones puntuales del 2026-10-18, en una sola máquina (el contenedor de trabajo), repetidas por la revisión:
- los cinco casos de campo tardan de 2,6 a 4,7 s, entre 25 y 44 ms por celda;
- el modelo más grande admitido tiene 256 celdas, unos 10 s;
- una evaluación de un solo escenario del banco de sangre tarda de 1,4 a 1,8 s. Tres de ellas suman más que la evaluación completa, porque cada corrida tiene un costo fijo cercano a 1 s.

Para una persona que decide en días, esto alcanza. Para un agente que decide en menos de un segundo, no alcanza, y esta propuesta tampoco lo resuelve: con el ejecutor actual ni siquiera un escenario entra en un segundo. Lo que sí resuelve son las ventanas de segundos a minutos que no alcanzan para el modelo completo.

## Propuesta

### A. Evaluación por escenarios con cotas exactas

1. Los escenarios se evalúan de a uno, cada uno como modelo de un solo escenario con ley `{s: "1/1"}`. El kernel verifica cada corrida.
2. **Orden.** Los escenarios se evalúan por masa decreciente bajo la ley. Los empates se resuelven por el orden que declare el decisor antes de calcular, por ejemplo el peor caso primero. Nunca se ordena mirando resultados.
3. **Cotas.** Valen si la ley no es nula y la tarea es una condición de vida (`life_conditions`); para una tarea operacional la PVS no aplica, como hoy. Después de evaluar el conjunto $E$ de escenarios, con masa $m(E)$, para cada ruta $r$:
   - si $r$ falla la condición de vida en algún escenario de $E$ y el modelo exige todos los escenarios (`require_all_scenarios`), queda refutada; ningún escenario que falte la rescata;
   - $\mathrm{PVS}(r) \in [\,m(\text{éxitos de } r \text{ en } E),\; m(\text{éxitos de } r \text{ en } E) + 1 - m(E)\,]$. Es exacto: la parte no evaluada vale entre 0 y su masa;
   - un escenario evaluado sin decidir (un umbral nulo) no refuta y aporta lo mismo que uno no evaluado: entre 0 y su masa;
   - con `require_all_scenarios: false` ninguna ruta queda refutada, así que nunca se selecciona antes de terminar;
   - las funciones, la CAG y el bienestar se informan sólo en los escenarios evaluados. Nada se extrapola a los que faltan.
4. Si la ley es nula, no hay orden por masa. Rige el orden declarado, y la PVS sigue indefinida como hoy. Lo que se informa es su rango bajo toda ley, y sólo cuando están evaluados todos los escenarios: va de 0 a 1 si la ruta falla en alguno y tiene éxito en otro, es 1 si tiene éxito en todos y es 0 si falla en todos. Mientras falte un escenario el rango no se informa, porque ese escenario puede cambiar cualquiera de sus extremos. (Al implementar se corrigió el texto aprobado, que decía que un fallo evaluado fija el extremo superior en 0: con éxitos en otros escenarios, una ley puede ponerles toda la masa.)

### B. Qué se entrega al cerrar la ventana

- **Siempre:** las rutas no refutadas, la cota de PVS de cada una, los escenarios evaluados y la frescura del resultado. También la ruta comprometida, que es lo que ocurre si no se decide nada.
- **Una selección sólo si el modelo la permite (`selection: "unique"`) y queda una sola ruta no refutada.** Los cinco casos de campo declaran `selection: "none"`, y entonces no se selecciona nunca, igual que con el cálculo completo. Se rotula como condicionada a los escenarios no evaluados, porque uno de ellos todavía podría refutarla. No se selecciona por una cota de PVS sola: la PVS queda debajo de la CAG y del bienestar, y la frontera sigue el orden producto.
- **En otro caso:** `NO_SELECTION_WITHIN_WINDOW`, con las cotas. Genius no completa lo que falta con supuestos.
- **El rótulo nombra lo no evaluado:** «PVS en [a, b], con k de S escenarios evaluados (masa m)».

### C. Ciclo con la realidad

Si llega una observación durante el cálculo:
- el cálculo en curso termina sobre su evidencia y se marca superado;
- el siguiente parte del gemelo re-anclado;
- al cerrar la ventana se entrega el resultado más fresco que haya terminado, con su antigüedad.

Una observación no detiene un cálculo verificado a mitad de camino, porque un resultado a medias no tiene verificación.

## Revisión adversarial separada (2026-10-18)

Una sesión independiente leyó la propuesta y el código, y repitió las mediciones. Su dictamen fue `ACCEPT_WITH_REPAIRS`:
- comprobó que el compromiso de pasos es exacto, con reglas condicionales incluidas, y que el conteo de pasos no tiene errores de borde;
- confirmó el ejemplo del banco de sangre.

Sus reparaciones ya están incorporadas:
1. La frescura cuenta también observaciones de versiones posteriores, y se lee aparte, para que el job congelado no cambie.
2. Las horas se comparan como fechas, no como texto.
3. La ventana cuenta la antigüedad de la observación.
4. Si la ruta comprometida queda igual a otra, se informa la que se conserva.
5. La selección respeta `selection` y se dice qué pasa con `require_all_scenarios: false`.
6. Las cotas valen sólo con ley, condición de vida y escenarios decididos.
7. Se dice qué se informa con ley nula.
8. La ley de un solo escenario es `"1/1"`.
9. Se quitó la idea de que esto sirve para decisiones de menos de un segundo.
10. Las cifras se presentan como mediciones puntuales de una máquina.

## Por qué necesita aprobación

- **Módulo VII.** Hoy sólo emite resultados de evaluaciones completas. A y B le permiten emitir cotas y, en casos estrictos, una selección con escenarios sin evaluar.
- **Módulo VI.** La combinación de cotas entre corridas es aritmética exacta, pero ocurre fuera del verificador FP1, que verifica cada corrida por separado.
- **Orden de los empates.** Lo declara el decisor. Es un supuesto nuevo y queda en el certificado.

## Invariantes que no cambian

- El ideal de bienestar y cuidado de la vida es el fin del cálculo.
- Una cota no es una estimación. La PVS indefinida sigue indefinida.
- Ningún criterio distinto se suma.
- El kernel FP1 no cambia.

## Hecho al aprobar (2026-10-18)

1. `twin/genius_twin/anytime.py` evalúa escenario por escenario y entrega las cotas, las rutas refutadas y, cuando corresponde, la selección condicionada.
2. Se sirve en `POST /cases/<cid>/anytime/evaluate` y en la herramienta MCP `twin_evaluate_anytime`. Cuenta como una evaluación y no se guarda como predicción congelada: para contrastar observaciones sigue haciendo falta la evaluación completa.
3. La ventana máxima es de 60 s por pedido. Así queda margen para la corrida que esté en curso al cerrarse la ventana.
4. Con los tres escenarios del banco de sangre evaluados, las cotas coinciden exactamente con la PVS de la evaluación completa.
5. El estado quedó como `ACEPTADA` en `AMENDMENTS.md`.
