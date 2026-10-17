# Propuesta AM-02 — Ley empírica de escenarios y revisión de modelos con la experiencia

Estado: `ACEPTADA_CON_REPARACIONES`.
- Redactada el 2026-10-17 a pedido de Pedro ("si encuentras en la matemática una limitación, también puede mejorarse; lo único fijo es el ideal del bienestar y cuidar la vida").
- Pedro la dio por revisada el 2026-10-17.
- La revisión adversarial separada (sección final) pidió once reparaciones. Las tres bloqueantes y las demás están incorporadas abajo como **Reparaciones**.
- No modifica S1 ni el kernel. Sigue el formato de AM-01.

## Localización

- S1 Definición 8.9 (P02625–P02640), "Ley del experimento": "Se aporta una medida […] Para un cálculo finito exacto pueden utilizarse pesos racionales."
- S1 Definición 8.11 (P02680): la PVS está definida sólo con "una ley legítima" y $M^?=0$.
- S1 Definición 8.12 (P02754) y Teorema 8.10: el refinamiento de evidencia mantiene fijas "la misma tarea, realizaciones y ley".
- `specification/04_EVIDENCE_AND_DECISION.md:146`: "Modificar Φ, Jtask, la ley o el protocolo sin demostrar esa relación no autoriza aplicar el resultado."
- `specification/00_SPECIFICATION.md:36`: los modelos probabilísticos imprecisos quedan fuera del perfil.
- `twin/docs/EMPIRICAL_PROTOCOL.md`: "Una frecuencia observada en unas pocas trayectorias no valida automáticamente una ley conjunta de escenarios."

## Problema

1. **La ley sólo puede declararse.** Casi ningún sistema real trae una ley legítima sobre sus escenarios. Sin ella la PVS queda indefinida, el bloque común no se forma y la selección queda `OUTSIDE_DOMAIN` (`kernel/genius_kernel/decision.py:34-39, 68-90`). Los tres casos reales del gemelo (Denver, Mendoza, Lake Mead) están en esa situación. Genius puede descartar opciones inviables, pero no puede recomendar entre las viables en el mundo real.
2. **No hay operación de aprendizaje.** La teoría es finita y exacta. La actualización $U_t$ (Definición 7.5, AM-01) actualiza la información de una política dentro de un modelo fijo. No define cómo cambiar el modelo o la ley cuando la realidad los contradice. Por eso los contrastes con la realidad no pueden mejorar nada formalmente.
3. **Las proyecciones oficiales no son leyes.** Ejemplo medido (`twin/history/lake_mead/studies.csv`, 383 estudios de 2009 a 2026): a 12 meses, el almacenamiento real de Lake Mead cayó dentro del rango mínimo–máximo de Reclamation en 32 de 67 casos. Quedó por debajo del mínimo en 19 y por encima del máximo en 16. A 3 meses, dentro en 22 de 71. Tratar esos escenarios como equiprobables, o el rango como seguro, sería inventar una ley.

## Propuesta

### A. Ley empírica admitida (LEA)

Una LEA es una ley en el sentido de la Definición 8.9: masas racionales no negativas, filas completas y normalizadas sobre las mismas realizaciones. Lo que cambia es la premisa de legitimidad, que pasa de "declarada" a "empírica" y queda sujeta a cuatro condiciones comprobables:

1. **Procedimiento previo.** El procedimiento $P$ que asigna masas a los escenarios queda versionado y congelado, con el hash de los datos $D$ que usa. Esto ocurre antes de los resultados contra los que se comprueba.
2. **Calibración fuera de muestra.** Para cada banda de escenarios $b$ con masa nominal $q_b$ se registra la frecuencia observada $f_b$ en $n_b$ contrastes posteriores al congelamiento de $P$. Se admite sólo si $q_b$ cae dentro del intervalo de confianza declarado para $f_b$ (por ejemplo, Clopper–Pearson al nivel declarado).
3. **Comparación con regla propia.** Entre leyes candidatas se elige con una regla de puntuación estrictamente propia, como la logarítmica o la CRPS (Gneiting y Raftery, 2007). Así no se premia la sobreconfianza.
4. **Registro.** Todo resultado que use una LEA dice "PVS bajo ley empírica $E$". Lleva el certificado de calibración y el supuesto de clase `PROBABILITY` con su procedencia. Si alguna condición falla, la ley no se admite y la PVS sigue indefinida, como hoy.

**Construcción recomendada.** Bandas a partir de los errores pasados, usando predicción conformal:
- Con intercambiabilidad, los cuantiles de los errores pasados dan bandas con cobertura marginal garantizada de al menos $1-\alpha$ (Vovk, Gammerman y Shafer, 2005; Angelopoulos y Bates, 2021).
- Las series hidrológicas no son intercambiables. Por eso se declara el supuesto y se usa la variante adaptativa (Gibbs y Candès, 2021).
- La condición 2 comprueba la cobertura real en vez de suponerla. Lo que se corrió es predicción conformal de ventana fija, que da cobertura marginal, no la variante adaptativa. Las bandas miden incertidumbre de salidas: sirven de diagnóstico, no son una ley (reparación 1).
- Primera comprobación (`twin/history/lake_mead/README.md`): con los últimos 120 errores, las bandas al 90 % de Lake Mead cubrieron la realidad en el 90–93 % de los casos de 6 a 23 meses, pero en el 82 % a 3 meses. Esa banda a 3 meses no se admitiría.

### B. Operador de revisión $\mathcal R$

Los modelos y las leyes se versionan: $M_0, M_1, \dots$ La revisión es

$$M_{k+1}=\mathcal R(M_k, g, D_{\le t}),$$

donde $g$ es un genoma de datos acotado (nunca código) y $D_{\le t}$ es la evidencia publicada hasta $t$. $\mathcal R$ sólo produce $M_{k+1}$ si $g$ supera la regla de descubrimiento y confirmación de `twin/docs/LEARNING_PROTOCOL.md`: menor error en un bloque, sin empeorar el máximo, y repetido en el bloque siguiente que no vio. Valen cuatro reglas:

- **Monotonía del registro.** Ninguna evaluación pasada se edita. Cada evaluación queda indexada por la versión con que se hizo.
- **Dentro de una versión** vale la Definición 8.12 sin cambios.
- **Entre versiones** no se transportan veredictos. Las versiones se comparan sólo por su desempeño en resultados posteriores al congelamiento de ambas, en sentido precuencial (Dawid, 1984).
- **Autoridad.** Una versión nueva entra a un gemelo como propuesta. La confirma quien decide, como cualquier mundo.

## Reparaciones (revisión adversarial del 2026-10-17)

Prevalecen sobre el texto de A y B donde difieran.

1. **La ley es sobre realizaciones, no sobre bandas.** Una LEA asigna masa a las realizaciones completas del gemelo, es decir, a sus palabras de eventos. Una banda de error de una variable de salida no es una ley. Toda LEA declara y versiona tres cosas:
   - el mapa Γ que lleva de los datos históricos a una realización (por ejemplo, "el escenario oficial cuya trayectoria quedó más cerca");
   - el impulsor exógeno con que se juzga ese mapa (afluencia no regulada, demanda), nunca una salida que dependa de la política en vigor;
   - el supuesto explícito de que la ley no depende de la política.
2. **Celdas y tarea.** Si la tarea no es constante dentro de la celda que representa cada realización, la PVS bajo la LEA vale sólo para el escenario representativo. Se informa así, nunca como probabilidad del mundo real.
3. **Retrospectiva no es prospectiva.** Una calibración sobre historia ya existente se rotula `RETROSPECTIVE_PREQUENTIAL`. Es provisional: cada pronóstico usa sólo datos anteriores, pero el procedimiento se escribió después de verlos. La procedencia `EMPIRICAL_CALIBRATED` exige además contrastes prospectivos: cada pronóstico se registra con su hash antes del resultado y se controla con una prueba secuencial de validez continua, como un proceso e o una martingala de prueba. Si esa prueba rechaza, la ley se revoca. Los resultados pasados conservan su rótulo "bajo E versión k" y quedan marcados, no editados. Se cuentan todas las variantes de P probadas.
4. **No rechazar no es demostrar.** La calibración se admite sólo con un mínimo declarado de resultados independientes (orígenes que no se superponen, o inferencia robusta a la dependencia). Se controla la multiplicidad entre celdas y plazos (Bonferroni u Holm). Cada celda se prueba por separado; en una banda, cada cola por separado.
5. **Una ley parcial no es ley.** Si falla la calibración de un plazo o de una celda con masa positiva, se rechaza toda la LEA o se acorta el horizonte.
6. **El operador $\mathcal R$** elige leyes con la regla propia de A.3, no con el error absoluto, y toda versión nueva se recertifica. La monotonía del registro es una invariante del registro (cadena de hashes sólo de agregado), no un teorema. El corolario de estabilidad del Teorema 8.10 no vale entre versiones.
7. **Fragilidad.** Si el orden de PVS entre políticas cambia para alguna ley dentro de los intervalos declarados, el resultado es `SELECTION_FRAGILE_UNDER_LAW`: se mantiene la frontera y no se recomienda. Es un diagnóstico, no una ley imprecisa, así que el perfil no cambia.
8. **Orden sin ley.** Si los escenarios donde una política cumple la tarea incluyen los de otra, su PVS es mayor o igual bajo toda ley. Ese orden no necesita LEA y se informa primero. Si dos políticas cumplen en los mismos escenarios, ninguna ley las separa.
9. **Performatividad.** La ley se revoca cuando la política en vigor difiere de la de los datos de calibración, por ejemplo porque se siguen recomendaciones de Genius.
10. **Rótulo completo.** Toda salida dice: "PVS bajo ley empírica E (retrospectiva o prospectiva, n independientes, horizonte, supuesto de independencia de la política)". Repite que la PVS está por debajo de CAG y del bienestar.
11. **Alcance.** Una LEA no basta para que el bloque común se forme: también deben estar definidos CAG, bienestar y la valoración funcional (`kernel/genius_kernel/decision.py:34-39`).

### Primera aplicación: Lake Mead 2027

`twin/history/empirical_law.py`, sobre `twin/history/lake_mead/studies.csv`:
- **Resultados disponibles:** 14 estudios de octubre de 2012 a 2025 con resultado publicado y sin superposición. La realidad siguió de cerca al mínimo en 6, al más probable en 4 y al máximo en 4.
- **Candidatos:** las masas iguales y las frecuencias suavizadas pasan la calibración. Las masas iguales puntúan mejor.
- **Resultado:** no se admite. Hay 14 resultados independientes y se exigen 30, y la clasificación se juzga con el almacenamiento, que depende de la operación, no con la afluencia.
- **Orden sin ley (reparación 8):** las dos políticas fallan sólo en el año mínimo, así que su PVS es igual bajo cualquier ley. Ninguna ley puede recomendar entre liberar 6 o 7 millones con esta tarea. Lo que las distingue es cuánto baja Powell (4.072 frente a 3.141 kaf), que la tarea binaria no mide.

## Invariantes que no cambian

- El ideal de bienestar y cuidado de la vida es el fin del cálculo, no un parámetro aprendible.
- La PVS sigue siendo una probabilidad bajo una tarea y un protocolo. Nunca sustituye los registros de CAG ni las historias de bienestar de los portadores (S1:5138, 5152).
- Ningún error operativo se presenta como bienestar (`OBSERVED_ABSOLUTE_ERROR_NOT_WELLBEING_OR_PVS`).

## Impacto

- **Kernel FP1:** sin cambios. Una LEA entra por el campo `law` existente; el gemelo ya convierte un mapa escenario→masa en filas condicionales (`twin/genius_twin/stockflow_compiler.py:154-158`). Hace falta un registro nuevo, el certificado de calibración, y una comprobación de admisión antes de aceptar `law` con procedencia empírica.
- **Selección:** con una LEA admitida, la PVS queda definida y el bloque común puede formarse. Genius podría recomendar entre opciones viables en casos reales, siempre con la ley y su calibración a la vista.
- **Perfil:** se agrega la clase de procedencia `EMPIRICAL_CALIBRATED`. Las leyes imprecisas (intervalos o conjuntos credales) siguen fuera del perfil; serían una AM-03 si la experiencia muestra que hacen falta.

## Trabajo pendiente

1. Cosechar un impulsor exógeno: la afluencia no regulada a Powell, que ya está en las mismas tablas. Juzgar con él qué escenario siguió la realidad.
2. Registrar pronósticos prospectivos con hash y prueba secuencial (reparación 3).
3. Demostrar, por cada LEA admitida, que sus filas son completas sobre las realizaciones del gemelo (Definición 8.9).
4. Agregar el diagnóstico de fragilidad y el orden sin ley a la salida del gemelo.

## Referencias externas

- T. Gneiting y A. E. Raftery (2007), *Strictly Proper Scoring Rules, Prediction, and Estimation*, JASA 102(477).
- V. Vovk, A. Gammerman y G. Shafer (2005), *Algorithmic Learning in a Random World*, Springer.
- A. N. Angelopoulos y S. Bates (2021), *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*, arXiv:2107.07511.
- I. Gibbs y E. Candès (2021), *Adaptive Conformal Inference Under Distribution Shift*, NeurIPS.
- A. P. Dawid (1984), *Statistical Theory: The Prequential Approach*, JRSS A 147(2).

## Revisión adversarial separada (2026-10-17)

La hizo una sesión independiente que leyó la propuesta, S1, la especificación, el kernel y el gemelo. Dictamen: `ACCEPT_WITH_REPAIRS`.
- **Bloqueantes:** la LEA no era una ley sobre realizaciones; la retrospectiva no era posterior al congelamiento; la prueba de calibración no podía rechazar y no tenía en cuenta la dependencia.
- **A corregir:** método citado frente a método corrido; ley parcial; regla de $\mathcal R$; imprecisión; performatividad.
- **Menores:** rótulo, alcance, y una fuga de información en `hindcast.py`: los errores pasados usaban el valor real ya revisado. Ya se corrigió; no cambia los resultados de Mead porque Mead no tiene revisiones.
