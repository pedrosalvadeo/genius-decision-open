# Propuesta AM-02 — Ley empírica de escenarios y revisión de modelos con la experiencia

Estado: `PROPUESTA`, redactada el 2026-10-17 a pedido de Pedro ("si encuentras en la matemática una limitación, también puede mejorarse; lo único fijo es el ideal del bienestar y cuidar la vida"). No modifica S1, `AMENDMENTS.md` ni el kernel hasta su revisión. Sigue el formato de AM-01.

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
- La condición 2 comprueba la cobertura real en vez de suponerla.

### B. Operador de revisión $\mathcal R$

Los modelos y las leyes se versionan: $M_0, M_1, \dots$ La revisión es

$$M_{k+1}=\mathcal R(M_k, g, D_{\le t}),$$

donde $g$ es un genoma de datos acotado (nunca código) y $D_{\le t}$ es la evidencia publicada hasta $t$. $\mathcal R$ sólo produce $M_{k+1}$ si $g$ supera la regla de descubrimiento y confirmación de `twin/docs/LEARNING_PROTOCOL.md`: menor error en un bloque, sin empeorar el máximo, y repetido en el bloque siguiente que no vio. Valen cuatro reglas:

- **Monotonía del registro.** Ninguna evaluación pasada se edita. Cada evaluación queda indexada por la versión con que se hizo.
- **Dentro de una versión** vale la Definición 8.12 sin cambios.
- **Entre versiones** no se transportan veredictos. Las versiones se comparan sólo por su desempeño en resultados posteriores al congelamiento de ambas, en sentido precuencial (Dawid, 1984).
- **Autoridad.** Una versión nueva entra a un gemelo como propuesta. La confirma quien decide, como cualquier mundo.

## Invariantes que no cambian

- El ideal de bienestar y cuidado de la vida es el fin del cálculo, no un parámetro aprendible.
- La PVS sigue siendo una probabilidad bajo una tarea y un protocolo. Nunca sustituye los registros de CAG ni las historias de bienestar de los portadores (S1:5138, 5152).
- Ningún error operativo se presenta como bienestar (`OBSERVED_ABSOLUTE_ERROR_NOT_WELLBEING_OR_PVS`).

## Impacto

- **Kernel FP1:** sin cambios. Una LEA entra por el campo `law` existente; el gemelo ya convierte un mapa escenario→masa en filas condicionales (`twin/genius_twin/stockflow_compiler.py:154-158`). Hace falta un registro nuevo, el certificado de calibración, y una comprobación de admisión antes de aceptar `law` con procedencia empírica.
- **Selección:** con una LEA admitida, la PVS queda definida y el bloque común puede formarse. Genius podría recomendar entre opciones viables en casos reales, siempre con la ley y su calibración a la vista.
- **Perfil:** se agrega la clase de procedencia `EMPIRICAL_CALIBRATED`. Las leyes imprecisas (intervalos o conjuntos credales) siguen fuera del perfil; serían una AM-03 si la experiencia muestra que hacen falta.

## Trabajo pendiente antes de aceptar

1. Revisión de Pedro y revisión adversarial separada, como en AM-01.
2. Implementar la admisión de LEA y probarla primero en Lake Mead, con el archivo histórico completo que reúne el nodo de historia.
3. Demostrar que la LEA cumple las condiciones de la Definición 8.9 sobre las realizaciones del gemelo, y que $\mathcal R$ no altera evaluaciones registradas.

## Referencias externas

- T. Gneiting y A. E. Raftery (2007), *Strictly Proper Scoring Rules, Prediction, and Estimation*, JASA 102(477).
- V. Vovk, A. Gammerman y G. Shafer (2005), *Algorithmic Learning in a Random World*, Springer.
- A. N. Angelopoulos y S. Bates (2021), *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*, arXiv:2107.07511.
- I. Gibbs y E. Candès (2021), *Adaptive Conformal Inference Under Distribution Shift*, NeurIPS.
- A. P. Dawid (1984), *Statistical Theory: The Prequential Approach*, JRSS A 147(2).
