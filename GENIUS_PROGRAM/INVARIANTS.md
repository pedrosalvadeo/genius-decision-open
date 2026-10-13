# Registro normativo de invariantes

Versión del registro heredado: 1.0.0; continuidad F1/F2/F3 bajo GENIUS-SPEC-1.0.0. Se conservan sus 49 invariantes teóricos y 6 de programa con los mismos IDs y enunciados. Estos invariantes obligan a la traducción y a la gobernanza del programa. Los de origen S1 preservan restricciones de la fuente; los de origen S0/F0 son reglas de programa, no nuevos teoremas. CONFIRMED documental no significa validación matemática independiente. Modificar una entrada requiere ADR, análisis de impacto y revisión conforme a [GOVERNANCE.md](GOVERNANCE.md).

| ID | Enunciado | Origen | Razón | Componentes afectados | Consecuencia de violación | Estado |
|---|---|---|---|---|---|---|
| INV-01 | Marco, modelo β y contexto γ tienen roles distintos | S1 P00059–P00089; Entrega 7 | Identificar el experimento | Todos | Resultados sin ámbito compatible | CONFIRMED documental |
| INV-02 | Estado causal x, información ι y organización Σ no son objetos intercambiables | S1 Entregas 1, 2 y 7 | Evitar pérdida de causalidad y omnisciencia | M0, MIII, MV | Política ilegítima o reducción falsa | CONFIRMED documental |
| INV-03 | Una función parcial incluye su dominio; igualdad requiere igual dominio e iguales valores | S1 P00091–P00105 | Preservar significado | Todos | Extensión silenciosa | CONFIRMED documental |
| INV-04 | Valor cero, fuera de dominio, dominio desconocido e invalidez se distinguen | S1 P00107–P00117 | Conservar diagnóstico | Todos | Falsedad o éxito inventados | CONFIRMED documental |
| INV-05 | Gate sin certificado positivo no equivale a predicado falso | S1 P00143–P00168 | Separar autorización y verdad | MVI, MVII | Rechazo mal interpretado | CONFIRMED documental |
| INV-06 | Afirmaciones conjuntas mantienen política y testigos de ejecución compatibles | S1 P00170–P00201; P03325–P03348 | No combinar existencias separadas | Todos | Logro conjunto ficticio | CONFIRMED documental |
| INV-07 | Garantía requiere familias realizables no vacías y dominio en casos exigidos | S1 P00203–P00211 | Evitar garantía por vacuidad | MIII, MV, MVI | Robusteza sin realizaciones | CONFIRMED documental |
| INV-08 | Existir política para todo escenario no se deduce de elegir política distinta por escenario | S1 P00213–P00221 | Respetar orden de cuantificadores | MIII, MV, MVII | Capacidad no implementable | CONFIRMED documental |
| INV-09 | Incomparabilidad definida no equivale a falta de datos o fuera de dominio | S1 P00224–P00239 | Conservar orden parcial | MI, MIV, MVII | Selección o empate falsos | CONFIRMED documental |
| INV-10 | Cada suficiencia se acredita para consulta, dominio y reducción específicos | S1 Teorema 2.1; P03518–P03532 | Limitar transferencia de certificados | M0 y consumidores | Resumen usado fuera de su alcance | CONFIRMED documental |
| INV-11 | El descenso de funciones parciales conserva cobertura, saturación y constancia en fibras | S1 Teorema 2.1; P03449–P03465 | Igualdad de funciones, no solo valores | M0, MI, MIII | Dominio alterado | CONFIRMED documental |
| INV-12 | Una comparación funcional fija índice, calibración y bloque | S1 Entrega 3 | Garantizar preorden | MI, MVII | Transitividad no justificada | CONFIRMED documental |
| INV-13 | Relaciones conjuntas no se sustituyen por marginales independientes sin prueba de recomposición | S1 Entrega 4 | Preservar correlaciones | MII y ensamblaje | Combinaciones imposibles | CONFIRMED documental |
| INV-14 | Demandas de recursos tienen identidad y unidades; restricción instantánea no se vuelve suma temporal | S1 Entrega 4; P03466–P03477 | Evitar doble cómputo y cambio de problema | MII, MVII | Factibilidad incorrecta | CONFIRMED documental |
| INV-15 | Identidad organizacional, funcionalidad y conservación generativa tienen significados distintos | S1 Entrega 5 | Separar organización y desempeño | MI, MIII | CAG mal tipado | CONFIRMED documental |
| INV-16 | Receta, traducción, horizonte y cuantificadores forman parte del CAG comparado | S1 Entrega 5 | Comparar objetos compatibles | MIII, MVII | Dominancia sin significado común | CONFIRMED documental |
| INV-17 | La traducción usada en robustez precede a la intersección correspondiente | S1 Entrega 5; P03478–P03486 | Preservar identidad común | MIII | Robustez nativa transportada incorrectamente | CONFIRMED documental |
| INV-18 | Cardinalidad del CAG no sustituye inclusión ni dominancia | S1 Entrega 5, Teorema 5.6 y contraejemplos | Conservar qué es generable | MIII, MVII | Capacidad sobreafirmada | CONFIRMED documental |
| INV-19 | Origen canónico del CAG no acredita logro futuro y conserva testigos separados | S1 P01379–P01409; P03485 | Distinguir estructura y realización | MIII | Garantía temporal ficticia | CONFIRMED documental |
| INV-20 | Reloj, existencia, aplicabilidad y medición de bienestar permanecen separados | S1 Entrega 6 | No borrar tiempos ni portadores sin medición | MIV | Ausencia interpretada como bienestar | CONFIRMED documental |
| INV-21 | Más CAG no implica más bienestar; comparaciones de población necesitan regla explícita | S1 Entrega 6, P01944–P01949 | Evitar equivalencia normativa inventada | MIII, MIV, MVII | Beneficio no demostrado | CONFIRMED documental |
| INV-22 | Políticas usan información legítima; causalidad conserva ramas adversas y de masa nula | S1 Entrega 7; P03501 | Conservar cobertura | MV y consumidores | Garantía por eliminación de casos | CONFIRMED documental |
| INV-23 | Estado terminal no sustituye trayectoria para condiciones históricas | S1 Entregas 6 y 7 | Conservar daños intermedios | MIV, MV, MVI | Viabilidad falsa | CONFIRMED documental |
| INV-24 | Semántica y certificados conservan no vaciedad, dominio de tarea y completaciones pertinentes | S1 Teoremas 8.3–8.5 | Evitar veredictos incompatibles | MVI | Certificación no justificada | CONFIRMED documental |
| INV-25 | Posibilidades e incertidumbre no suministran por sí solas una ley probabilística | S1 P02623–P02641 | No inventar probabilidades | MV, MVI | PVS sin fundamento | CONFIRMED documental |
| INV-26 | Masas positiva, negativa e indeterminada particionan el experimento; PVS definida exige masa indeterminada cero | S1 Entrega 8; P03497–P03501 | Conservar incertidumbre | MVI | Número presentado fuera de dominio | CONFIRMED documental |
| INV-27 | Probabilidad uno no implica garantía universal; hojas nulas se conservan | S1 Entrega 8 | Separar casi seguro y para todo | MVI, MVII | Robusteza falsa | CONFIRMED documental |
| INV-28 | Frontera relativa, cobertura exhaustiva y selección son afirmaciones diferentes | S1 Entrega 9; P03671 | Limitar alcance de decisión | MVII | Exhaustividad o elección no autorizadas | CONFIRMED documental |
| INV-29 | Constructores forman DAG de justificación; CAG no se filtra por una tarea que depende del mismo CAG | S1 P03350–P03377 | Evitar circularidad | Integración | Justificación circular | CONFIRMED documental |
| INV-30 | La ruta fuerte requiere escenarios comunes biyectivos y realizaciones hasta H | S1 P03307–P03323 | Preservar hipótesis de Teorema 10.2 | Integración, futuro perfil Kernel | Generalización inválida | CONFIRMED documental |
| INV-31 | Parcialidad se trata por componente, no por propagación uniforme de cualquier ausencia | S1 P03379–P03395 | Mantener rutas válidas y diagnósticos | Todos | Valor borrado o invalidez ocultada | CONFIRMED documental |
| INV-32 | Terminación exige presentación efectiva, no solo descripción finita | S1 Teorema 10.3 | Limitar computabilidad | Specification, Kernel | Promesa de cálculo no demostrada | CONFIRMED documental |
| INV-33 | Descenso sobre un dominio seguro no acredita factorizar toda la consulta original | S1 Proposición 2.2, P00366–P00382 | Mantener exclusiones | M0, MIII | Cobertura exagerada | CONFIRMED documental |
| INV-34 | Exactitud de trazas finitas no concede transporte de políticas, leyes o aceptación infinita | S1 P00527–P00559; P02283–P02289 | Separar garantías | M0, MV, MVI | Transporte sin premisas | CONFIRMED documental |
| INV-35 | Transporte exacto de orden conserva y refleja; reducción exacta de frontera requiere cobertura sobreyectiva pertinente | S1 Teoremas 3.4 y 9.7 | Mantener equivalencia, estricta y maximalidad | MI, MVII | Frontera alterada por mapa solo monótono | CONFIRMED documental |
| INV-36 | Procedencia y observable reducido permanecen separados | S1 Convención 4.1, P01092–P01109 | No esconder insuficiencia del resumen | MII | Certificado trivial que cambia la consulta | CONFIRMED documental |
| INV-37 | Reducción relacional no conserva multiplicidades ni probabilidades automáticamente | S1 Proposición 4.7, P01111–P01122 | Exigir masa por fibra y ley | MII, MVI | Probabilidad transportada incorrectamente | CONFIRMED documental |
| INV-38 | Alcance, mantenimiento, acumulación, política conjunta y coexistencia temporal son exigencias distintas | S1 Definiciones 5.5 y 5.9 | Conservar receta y testigos | MIII | Acumulación o coexistencia ficticias | CONFIRMED documental |
| INV-39 | Comparación anónima de trayectorias mantiene una misma biyección en tiempos y dimensiones | S1 P01761–P01833 | Preservar continuidad del portador | MIV | Igualdad instantánea presentada como igualdad histórica | CONFIRMED documental |
| INV-40 | Matching negativo exige grafo completo; comparación indefinida no es arista ausente | S1 P01835–P01868 | Certificar imposibilidad correctamente | MIV | Déficit artificial | CONFIRMED documental |
| INV-41 | Fidelidad conserva significado y dominio; igualdad de veredictos no basta | S1 P02383–P02418 | Separar verdad factual y evaluación | MVI, adaptadores | Semánticas distintas se identifican | CONFIRMED documental |
| INV-42 | Capacidad del lector no amplía información del controlador; testigo temporal pertenece a consulta o prefijo propio | S1 P02526–P02528 | Evitar filtración entre ramas | MV, MVI | Política con información ilegítima | CONFIRMED documental |
| INV-43 | Fila probabilística suministrada debe ser válida incluso en nodo nulo; omisión permitida no valida dato incorrecto | S1 P02639–P02640 | Separar medida y presentación de entrada | MVI | Ley inválida admitida | CONFIRMED documental |
| INV-44 | Prefijos y hojas no se suman como eventos disjuntos | S1 P02657–P02677 | Conservar partición foliar | MVI | Doble cómputo de masa | CONFIRMED documental |
| INV-45 | Refinamiento conserva valores, tarea, realizaciones y ley; transporte conserva indefinición | S1 P02753–P02805 | No cambiar experimento bajo etiqueta de nueva evidencia | MVI | Monotonía o masa no justificadas | CONFIRMED documental |
| INV-46 | PVS común requiere familia fiel completa no vacía, valores definidos e iguales; mezcla requiere ley adicional | S1 P02807–P02825 | Preservar incertidumbre estructural | MVI, MVII | Acuerdo fabricado al descartar casos | CONFIRMED documental |
| INV-47 | Fronteras exteriores posibles/necesarias no prueban realizabilidad de todas las admisiones desconocidas | S1 P03014–P03047 | Mantener correlaciones | MVII | Cota exterior presentada como resultado exacto | CONFIRMED documental |
| INV-48 | Robustez intersecta relaciones; frontera robusta no es en general intersección de fronteras | S1 P03049–P03073 | Conservar orden robusto | MVII | Alternativas válidas eliminadas | CONFIRMED documental |
| INV-49 | Selector equivariante necesita maximal fijado por estabilizador bajo sus hipótesis | S1 Teoremas 9.8–9.9, P03111–P03154 | No romper simetría por nombre tácito | MVII | Selección no justificada | CONFIRMED documental |
| INV-P01 | Teoría, Specification, Kernel, hipótesis, evidencia y producto conservan autoridad separada | S0 §§4, 14 | Evitar cambios semánticos por ingeniería | Programa | Release no aceptable | CONFIRMED mandato |
| INV-P02 | Diversidad Universal permanece como programa separado | S0 §6 | Preservar alcance | Programa | Importación teórica no autorizada | CONFIRMED mandato |
| INV-P03 | Ningún dato indispensable depende del chat ni de la cuenta | S0 §§0, 1, 19, 20 | Continuidad portable | Todas las fases | Handoff rechazado | CONFIRMED mandato |
| INV-P04 | Una fase no se certifica exclusivamente por su equipo autor | S0 §§17, 29 | Auditoría separada | Gates | Aceptación pendiente | CONFIRMED mandato |
| INV-P05 | Cada release fija fuentes, versiones, compatibilidad, limitaciones e integridad | F0 ADR-02, ADR-05 | Reproducibilidad | Configuración | Estado no reconstruible | CONFIRMED regla F0 |
| INV-P06 | Ningún diseño futuro ni prueba sintética se presenta como implementación o validación empírica | S0 §§3, 4, 25; F0 ADR-01 | Mantener evidencia proporcional | Comunicación y gates | Afirmación retirada y corregida | CONFIRMED regla F0 |

La conciliación histórica de los 72 candidatos cartográficos se conserva en el [ZIP F0 inmutable](../baseline/GENIUS_PHASE_1_HANDOFF/history/GENIUS_PHASE_0_HANDOFF.zip), miembro GENIUS_PHASE_0_HANDOFF/GENIUS_PROGRAM/theory/RECONCILIATION.md. Los candidatos no constituyen otro registro normativo independiente. Las etiquetas CONFIRMED documental de esta tabla conservan su alcance histórico; la revisión matemática actual se consulta por resultado en [FORMAL_INDEX.md](theory/FORMAL_INDEX.md).


## Aplicación explícita en F1

La Specification mantiene estos invariantes y hace comprobables sus obligaciones dentro de FP1_FINITE_EXACT. [TRACEABILITY](conformance/TRACEABILITY.md) enlaza requisitos con casos diseñados; [AMENDMENTS](theory/AMENDMENTS.md) conserva las reparaciones sin alterar S1.

- INV-02/22/42: políticas por (tiempo, información), actualización tipada de AM-01 y lector del evaluador separado del controlador. Coincidir cadenas de ID no iguala sus tipos nominales.
- INV-03/04/31: tablas cerradas y registros distintos de valor, dominio, validez, evidencia, cómputo y cobertura; ausencia no se completa con cero.
- INV-24: AM-02 exige admisión de certificados canónicos además del lector exacto; FP1 los genera para veredictos 0 y 1.
- INV-30: escenarios son palabras exógenas reales; su imagen coincide y cada fibra tiene una sola hoja en la ruta fuerte. No basta renombrar hojas.
- INV-14/20: recursos y bienestar completos se verifican incluso para políticas luego refutadas; las mediciones de prefijos compartidos pertenecen a la misma ocurrencia.
- INV-28/49: frontera relativa no habilita selección global FP1; none, unique y priority son reglas explícitas. La prioridad rompe solo las simetrías que modifica como dato adicional.
- INV-P01/P06: el inventario, revisión y ejemplo formal no son Kernel, Benchmark ni validación empírica. El gate F1 depende de la revisión separada registrada en el handoff.
