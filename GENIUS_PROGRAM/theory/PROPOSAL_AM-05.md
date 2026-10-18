# Propuesta AM-05 — Decisión dentro de una ventana de oportunidad

Estado: `PROPUESTA`. Necesita la aprobación de Pedro.
- Redactada el 2026-10-18, después de que Pedro señalara que cada decisor tiene su propia capacidad de cálculo y su propia ventana de oportunidad: algunas decisiones admiten mucho tiempo y otras casi nada. Además la realidad cambia, y los gemelos deben ajustarse durante el cálculo previo a actuar.
- No modifica S1 ni el kernel FP1.

## Lo que ya está hecho sin cambiar la matemática

1. **Pasos comprometidos.** `twin/genius_twin/decision_window.py` recibe la ventana del decisor en segundos exactos:
   - el tiempo disponible;
   - la duración real de un paso;
   - cuánto falta para la acción del paso 1;
   - cuánto tarda en aplicarse una decisión;
   - la ruta que sigue ahora;
   - su costo medido.

   Las acciones que ocurren antes de que la decisión pueda actuar ya están decididas: siguen la ruta actual. El resultado es un modelo declarado común, y el kernel lo evalúa y verifica como a cualquier otro. Se sirve en `POST /cases/<cid>/window` y en la herramienta MCP `twin_decision_window`.
2. **Frescura.** Cada cálculo queda fijado a la evidencia con la que empezó. Cada job informa `freshness` y `elapsed_seconds`. Si se registró una observación durante el cálculo o después, el resultado se declara superado; no se reescribe. El gemelo vivo (`living.reanchor`) parte de la observación nueva, con menos pasos por delante, y por eso calcula más rápido.

**Ejemplo, banco de sangre del invierno 2026/27.** El paso es una semana y la campaña de donantes ocurre en las semanas 1 a 3:
- si la decisión actúa en la semana 2 o 3, las cuatro rutas siguen siendo distintas y la frontera no cambia: campaña, campaña con postergación, y postergación;
- si la decisión llega después de la semana 3, la campaña ya no es una opción: «campaña» queda igual a «seguir igual», y «campaña con postergación» queda igual a «postergar»;
- en ese caso la frontera se reduce a postergar las cirugías programadas. Seguir igual falla la condición de vida con gripe severa: su PVS es 2/3.

La ventana cambia la decisión, aunque la matemática es la misma.

## Problema que queda

Cuando el cálculo completo no entra en la ventana, hoy Genius no entrega nada: un tiempo agotado no prueba inviabilidad. El decisor actúa sin información, o sigue con lo que ya hacía.

Mediciones del 2026-10-18 en el contenedor de trabajo:
- los cinco casos de campo tardan de 2,9 a 4,7 s, entre 29 y 44 ms por celda;
- el modelo más grande admitido tiene 256 celdas, unos 10 s;
- una evaluación de un solo escenario del banco de sangre tarda de 1,4 a 1,8 s. Hay un costo fijo cercano a 1 s por corrida.

Para una persona que decide en días, esto alcanza. Para un agente que decide en menos de un segundo, no alcanza.

## Propuesta

### A. Evaluación por escenarios con cotas exactas

1. Los escenarios se evalúan de a uno, cada uno como modelo de un solo escenario con ley `{s: 1}`. El kernel verifica cada corrida.
2. **Orden.** Los escenarios se evalúan por masa decreciente bajo la ley. Los empates se resuelven por el orden que declare el decisor antes de calcular, por ejemplo el peor caso primero. Nunca se ordena mirando resultados.
3. **Cotas.** Después de evaluar el conjunto $E$ de escenarios, con masa $m(E)$, para cada ruta $r$:
   - si $r$ falla la condición de vida en algún escenario de $E$ y el modelo exige todos los escenarios (`require_all_scenarios`), queda refutada; ningún escenario que falte la rescata;
   - $\mathrm{PVS}(r) \in [\,m(\text{éxitos de } r \text{ en } E),\; m(\text{éxitos de } r \text{ en } E) + 1 - m(E)\,]$. Es exacto: la parte no evaluada vale entre 0 y su masa;
   - las funciones, la CAG y el bienestar se informan sólo en los escenarios evaluados. Nada se extrapola a los que faltan.
4. Si la ley es nula, no hay orden por masa. Rige el orden declarado, y la PVS sigue indefinida como hoy.

### B. Qué se entrega al cerrar la ventana

- **Siempre:** las rutas no refutadas, la cota de PVS de cada una, los escenarios evaluados y la frescura del resultado. También la ruta comprometida, que es lo que ocurre si no se decide nada.
- **Una selección sólo si queda una sola ruta no refutada.** Se rotula como condicionada a los escenarios no evaluados, porque uno de ellos todavía podría refutarla. No se selecciona por una cota de PVS sola: la PVS queda debajo de la CAG y del bienestar, y la frontera sigue el orden producto.
- **En otro caso:** `NO_SELECTION_WITHIN_WINDOW`, con las cotas. Genius no completa lo que falta con supuestos.
- **El rótulo nombra lo no evaluado:** «PVS en [a, b], con k de S escenarios evaluados (masa m)».

### C. Ciclo con la realidad

Si llega una observación durante el cálculo:
- el cálculo en curso termina sobre su evidencia y se marca superado;
- el siguiente parte del gemelo re-anclado;
- al cerrar la ventana se entrega el resultado más fresco que haya terminado, con su antigüedad.

Una observación no detiene un cálculo verificado a mitad de camino, porque un resultado a medias no tiene verificación.

## Por qué necesita aprobación

- **Módulo VII.** Hoy sólo emite resultados de evaluaciones completas. A y B le permiten emitir cotas y, en casos estrictos, una selección con escenarios sin evaluar.
- **Módulo VI.** La combinación de cotas entre corridas es aritmética exacta, pero ocurre fuera del verificador FP1, que verifica cada corrida por separado.
- **Orden de los empates.** Lo declara el decisor. Es un supuesto nuevo y queda en el certificado.

## Invariantes que no cambian

- El ideal de bienestar y cuidado de la vida es el fin del cálculo.
- Una cota no es una estimación. La PVS indefinida sigue indefinida.
- Ningún criterio distinto se suma.
- El kernel FP1 no cambia.
