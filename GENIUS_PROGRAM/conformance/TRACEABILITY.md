# Matriz de trazabilidad de Fase 1

Specification candidata GENIUS-SPEC-1.0.0; perfil FP1_FINITE_EXACT; S1 preservada y snapshot S2 con enmiendas explícitas. Este documento desarrolla R-01–R-18 de `00_SPECIFICATION.md` y enlaza **fuente → obligación normativa → cláusula → caso diseñado**.

**Todos los CF tienen estado DESIGNED.** Ningún vínculo significa que un Kernel haya sido implementado o probado. La revisión deductiva de una regla, la revisión documental del paquete y la futura ejecución de conformidad son evidencias diferentes. Esta matriz no asigna PASS a ninguna de ellas. R-17 y R-18 requieren evidencia documental adicional; no se fuerzan a una cobertura de Kernel ficticia.

Abreviaturas de documentos:

- [01](../specification/01_TYPES_AND_WIRE.md): contrato normativo citado por sección.
- [02](../specification/02_REPRESENTATION_FUNCTION_COMPOSITION_CAG.md): contrato normativo citado por sección.
- [03](../specification/03_CAUSAL_AND_WELFARE.md): contrato normativo citado por sección.
- [04](../specification/04_EVIDENCE_AND_DECISION.md): contrato normativo citado por sección.
- [05](../specification/05_PIPELINE_AND_GUARANTEES.md): constructores, guardas G01–G15 y alcance.
- [06](../specification/06_OUTPUT_AND_DIAGNOSTICS.md): resultados, verificadores y diagnósticos.
- [00](../specification/00_SPECIFICATION.md): contrato normativo citado por sección.
- [Catálogo](CONFORMANCE_CASES.md) e [índice JSON](CASE_INDEX.json): entradas, precondiciones, oráculos y derivaciones de CF-001–CF-036.
- [Enmiendas](../theory/AMENDMENTS.md) y [revisión MVI–MVII](../theory/reviews/REVIEW_VI_VII.md): cambio explícito F1-ED-01 y sus argumentos.
- [S1 original](../theory/sources/S1_Matematica_Genius_Modulos_Astra_01.docx) y [S1 legible](../theory/sources/S1_READABLE.md): fuente de los párrafos citados; los números P son localizadores, no páginas.

Los rangos de invariantes abreviados conservan el prefijo: `INV-03,04` significa INV-03 e INV-04; `INV-P03,P04` significa INV-P03 e INV-P04. CW-*, VI-* y VII-* son obligaciones locales de los contratos 03/04, subordinadas a los requisitos R-* de esta matriz.

## Requisitos y evidencia diseñada

### R-01 — Tipos, dominio y presentación

**Obligación.** Cada valor DEBE conservar tipo y dominio; cero, fuera de dominio, presentación inválida y cálculo no concluido NO DEBEN identificarse. Las tablas parciales DEBEN interpretarse como cerradas.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §§1,2,10; 02 §1; 04 §1; 05 §2 paso1, G01; 06 §§1–2,5–6 |
| Fuentes | S1 P00091–P00168; Proposiciones 1.1–1.2 |
| Invariantes | INV-03,04,05,31 |
| Casos, solo DESIGNED | CF-004,005,006,017,024,027,028,031,035 |
| Alcance de la evidencia | FP1; casos de límites distinguen dato inválido y ausencia legítima. |

### R-02 — Identidad y procedencia

**Obligación.** Los resultados conjuntos DEBEN conservar marco, modelo, contexto, inicialización, política, escenario y ocurrencia compatibles. Igualdad de estado o número NO DEBE fusionar testigos.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §§1,2,3,10; 03 §§2,6; 04 §§1,11; 05 §§1–2, G02; 06 §§2–4 (digest y claves) |
| Fuentes | S1 P00170–P00201; P03325–P03348 |
| Invariantes | INV-01,02,06,22 |
| Casos, solo DESIGNED | CF-001,003,020,025,027 |
| Alcance de la evidencia | FP1; CF-003 impide fabricar conjunciones con testigos separados. |

### R-03 — Causalidad e información legítima

**Obligación.** MV DEBE generar todas las ramas de cada política usando únicamente la tabla por tiempo e información legítima; NO DEBE filtrar por tarea, presupuesto o masa.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §3; 02 §2.4; 03 §§2–4; 05 §2 pasos2–3, G03; 06 §3 Causal |
| Fuentes | S1 P00527–P00541; Teoremas 7.3–7.5; P03568 |
| Invariantes | INV-02,06,22,23,34,42 |
| Casos, solo DESIGNED | CF-001,003,020,021,027,035; general: CF-008 |
| Alcance de la evidencia | FP1 para construcción directa; CF-008 documenta el límite general del transporte informacional, sin prometer un adaptador wire. |

### R-04 — Escenarios y horizonte de la ruta fuerte

**Obligación.** La ruta fuerte DEBE acreditar todas las hojas a H, un conjunto común no vacío de palabras exógenas y exactamente una hoja por palabra en cada política.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §3; 03 §5; 05 G04 y §4; 06 §3 Causal, ScenarioMap |
| Fuentes | S1 P03307–P03323; Teorema 10.2 |
| Invariantes | INV-07,08,30 |
| Casos, solo DESIGNED | CF-001,002,020,021,022 |
| Alcance de la evidencia | FP1. Variantes que incumplen la guarda no se califican como imposibilidad física. |

### R-05 — Funcionalidad y bloque calibrado

**Obligación.** La comparación funcional DEBE utilizar todos los índices declarados y calibración común; NO DEBE cambiar la regla por pareja ni confundir incomparabilidad con dominio ausente.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §4; 02 §§3.1–3.3; 05 §2 paso4, G05; 06 §3 Funcionalidad |
| Fuentes | S1 P00604–P00765; Teoremas 3.1 y 3.4 |
| Invariantes | INV-09,12,35 |
| Casos, solo DESIGNED | CF-001,009,031; general: CF-010 |
| Alcance de la evidencia | FP1 para perfil tabulado. CF-010 comprueba el teorema general de transporte exacto, no que el Kernel certifique verdad empírica de calibración. |

### R-06 — Suficiencia y alcance de una reducción

**Obligación.** El descenso DEBE verificar cobertura, saturación y constancia en fibras; un dominio seguro NO DEBE presentarse como factor de toda la consulta. Suficiencia funcional NO DEBE usarse como suficiencia causal/semántica sin prueba propia.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §4; 02 §§2.1–2.4; 05 G06 y §4; 06 §3 ReductionCertificate |
| Fuentes | S1 P00307–P00382; P00469–P00541; P03518–P03532 |
| Invariantes | INV-10,11,33,34 |
| Casos, solo DESIGNED | CF-005,006,016; general: CF-007,008 |
| Alcance de la evidencia | FP1 implementa descenso funcional. DSuf y transporte de políticas permanecen contratos generales sin gramática de entrada adicional en FP1. |

### R-07 — Composición relacional

**Obligación.** La recomposición DEBE cotejar cobertura de puertos, proyecciones exactas y unión natural global, conservando correlaciones. Marginales compatibles NO DEBEN presentarse como relación conjunta acreditada.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §5; 02 §§4.1,4.2,4.4; 05 G07; 06 §3 CompositionCertificate |
| Fuentes | S1 P00883–P01002; P01074–P01122 |
| Invariantes | INV-13,36,37 |
| Casos, solo DESIGNED | CF-001,011; general: CF-007 |
| Alcance de la evidencia | En FP1 w es el ámbito fijo de política y Query es un puerto; una vista puede perder Query y debe igualmente superar la unión exacta. CF-011 usa filas de Query único. |

### R-08 — Recursos identificados y unidades

**Obligación.** Los usos DEBEN sumar una vez cada demanda identificada del mismo recurso/instante, con unidades y dominios válidos. NO DEBEN sumar instantes cuando la restricción es instantánea.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §5; 02 §4.3; 04 §7.1; 05 G08; 06 §3 Recursos y Restricciones |
| Fuentes | S1 P01017–P01060; P03592–P03600 |
| Invariantes | INV-14 |
| Casos, solo DESIGNED | CF-001,012,031 |
| Alcance de la evidencia | FP1; presupuestos son una obligación hard separada de posibilidad causal y de tarea. |

### R-09 — CAG y testigos temporales

**Obligación.** CAG DEBE conservar receta, traducción, política, no vacuidad y testigos; traducir antes de robustez. El origen estructural y la cardinalidad NO DEBEN sustituir logros futuros o inclusión. Su construcción NO DEBE depender de una tarea definida desde ese mismo CAG.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §6; 02 §§5.1–5.6; 05 §1, G09; 06 §3 generative y CAGWitness |
| Fuentes | S1 Definiciones 5.4–5.10; Teoremas 5.1–5.2; Proposiciones 5.3–5.4; P03350–P03377 |
| Invariantes | INV-07,08,15,16,17,18,19,29,38 |
| Casos, solo DESIGNED | CF-001,002,003,013,014,015,021,035 |
| Alcance de la evidencia | FP1 por política singleton. Los cuantificadores del caso CF-002 mantienen elecciones de política antes del escenario. |

### R-10 — Bienestar histórico con identidad

**Obligación.** El registro DEBE conservar reloj, existencia, aplicabilidad, medición y portador. El comparador FP1 DEBE usar todo el bloque común de escenario/portador/tiempo/dimensión, sin reemplazarlo por endpoint, suma o matching tácito.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §7; 03 §§7–10; 05 G10; 06 §3 welfare y WelfareProfile |
| Fuentes | S1 P01543–P01586; P01657–P01868; Definiciones 6.1–6.8 |
| Invariantes | INV-20,21,23,39,40 |
| Casos, solo DESIGNED | CF-001,016,017; generales: CF-018,019 |
| Alcance de la evidencia | FP1 usa portadores identificados. Los casos anónimos CF-018/019 son límites teóricos y no capacidades de F2. |

### R-11 — Evidencia, semántica y admisión de certificados

**Obligación.** El lector DEBE recalcular todas las completaciones y referencias; el verificador DEBE comprobar no vacuidad, inclusión, dominio y constancia. DV=D* SOLO se afirma con admisión de cada certificado canónico, incluidos los de valor cero.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §8; 04 §§2–4; VI-01..VI-04; 05 §2 paso7, G11; 06 §3 SemanticRead y DecisiveCertificate |
| Fuentes | S1 P02383–P02621; Teoremas 8.3–8.6; enmienda F1-ED-01 (S2) |
| Invariantes | INV-05,24,41,42 |
| Casos, solo DESIGNED | CF-024,025,026,027,036; general: CF-023 |
| Alcance de la evidencia | FP1_EXACT_ENUM_V1 satisface la clausura canónica. CF-036 es el contraejemplo general al enunciado literal y el control de la reparación para FP1. |

### R-12 — Ley, masas y dominio de PVS

**Obligación.** Las probabilidades DEBEN proceder de una ley legítima; las filas suministradas DEBEN ser válidas incluso en nodos nulos. VProb DEBE particionar hojas; PVS SOLO está definida cuando M?=0. No se renormaliza ni infiere garantía universal de PVS=1.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §8; 04 §§5,6; VI-05..VI-08; 05 G12; 06 §3 probability y LeafPartition |
| Fuentes | S1 P02623–P02805; Teoremas 8.7–8.11; Proposición 8.9 |
| Invariantes | INV-25,26,27,37,43,44,45,46 |
| Casos, solo DESIGNED | CF-001,025,026,027,028,029; general: CF-030 |
| Alcance de la evidencia | FP1 para leyes y masas. Transporte general (CF-029C) y lectores parciales (CF-030) se limitan expresamente; no se promete mezcla de modelos. |

### R-13 — Restricciones y factibilidad

**Obligación.** Cada hard DEBE acreditarse con cobertura positiva completa o testigo negativo, conservando faltantes. La partición factible/refutada/indeterminada NO DEBE borrar futuros ni completar booleans sin evidencia.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §9; 04 §7; VII-01; 05 §2 paso8, G13; 06 §3 hard |
| Fuentes | S1 P02903–P02927; P03592–P03638 |
| Invariantes | INV-04,05,07,14,31 |
| Casos, solo DESIGNED | CF-001,012,027,031 |
| Alcance de la evidencia | FP1; CF-031 deriva H1/H2 de presupuestos permitidos, no de una tabla libre de veredictos. |

### R-14 — Comparación, frontera y cobertura

**Obligación.** La relación integrada DEBE verificar todos los dominios y cuatro criterios en un bloque fijo antes de comparar. La frontera DEBE mantener su conjunto comparado y alcance; NO DEBE llamarse exhaustiva de un objetivo con omisiones no justificadas.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §§4,6,7,9; 04 §§8,9; VII-02..VII-04; 05 §4, G14–G15; 06 §4 Decision y PairComparison |
| Fuentes | S1 P02883–P03095; Teoremas 9.2–9.7 |
| Invariantes | INV-09,12,18,21,28,35,47,48 |
| Casos, solo DESIGNED | CF-001,009,014,031,033; general: CF-032 |
| Alcance de la evidencia | FP1 para un bloque/instancia. CF-032 distingue frontera robusta general de intersección de fronteras y no exige un agregador de modelos a F2. |

### R-15 — Selección explícita

**Obligación.** La selección DEBE usar el modo y regla declarados con su dominio. NONE NO DEBE elegir por nombre, orden de llegada, PVS o desempate tácito; la prioridad es un dato normativo adicional.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §9; 04 §10; VII-05; 05 §2 paso10 y §4; 06 §4 selection y §5 SELECTION_* |
| Fuentes | S1 P03097–P03154; Teoremas 9.8–9.9 |
| Invariantes | INV-28,49 |
| Casos, solo DESIGNED | CF-001,033; general: CF-034 |
| Alcance de la evidencia | FP1: none/unique/priority sobre alcance admitido. CF-034 limita la pretensión general de equivarianza; no prohíbe una prioridad explícita que cambie el problema. |

### R-16 — Efectividad, estados de cómputo y dependencia

**Obligación.** Una implementación DEBE construir resultados correctos bajo guardas con recursos suficientes; NO cumple devolviendo siempre un diagnóstico. El agotamiento operativo NO DEBE transformarse en imposibilidad matemática. El DAG DEBE permanecer acíclico.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §§1,10; 02 §5.1; 03 §6; 04 §1; 00 Contrato de eficacia; 05 §§1,2,5; 06 §§1,5,6 |
| Fuentes | S1 P03350–P03395; P03534–P03550; Teorema 10.3 |
| Invariantes | INV-29,31,32 |
| Casos, solo DESIGNED | CF-001,004,022,035 |
| Alcance de la evidencia | DESIGNED: CF-001 obliga al caso positivo y CF-035 separa límite operativo/guardas. No hay rendimiento ni ejecución de Kernel acreditados. |

### R-17 — Trazabilidad y proporcionalidad de evidencia

**Obligación.** Cada resultado DEBE conservar fuente, versión, premisas, entrada identificada y testigos recomputables; el programa DEBE diferenciar teoría, contrato, código y validación empírica. Las enmiendas DEBEN mantenerse explícitas y S1 preservada.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §§2,10; 03 §§6,11; 04 §§1,11; 00 Autoridad y alcance; 05 §3 alcance condicional; 06 §§1–4 (Check, DatumRef, IntegrationCertificate) |
| Fuentes | S0 §§4,5,9–14,25; S1 P00170–P00201; Convención 1.3; F1-ED-01 |
| Invariantes | INV-01,06,P01,P05,P06 |
| Casos, solo DESIGNED | CF-001,003,023,024,035,036; todos para fuente/oráculo |
| Alcance de la evidencia | Obligación mixta: enlaces a casos diseñados verifican aspectos semánticos; registro de versiones, hashes y enmiendas exige además auditoría documental del paquete. No se declara cubierto por un test matemático único. |

### R-18 — Transferencia autocontenida

**Obligación.** El paquete DEBE permitir a un receptor sin memoria reconstruir fuentes, enmiendas, perfiles, formatos, obligaciones, oráculos y límites, sin chat ni cuenta original. La aceptación DEBE quedar respaldada por revisión separada y protocolo de transferencia.

| Vinculación | Contenido |
|---|---|
| Cláusulas | 01 §§2,10 (entrada conservada y sin consulta externa); contratos completos 01–06; 00 Autoridad y alcance; 05 §5 límite F1/F2; 06 §6 conformidad futura |
| Fuentes | S0 §§0,1,18,19,20,29; PHASE_1_MANDATE: salida y gate |
| Invariantes | INV-P03,P04,P05,P06 |
| Casos, solo DESIGNED | No tiene caso CF de Kernel equivalente; CF-001 aporta un testigo portable y CF-036 conserva una reparación indispensable |
| Alcance de la evidencia | Verificación de F1 documental y de recepción, separada de conformidad del Kernel. El informe de recepción/auditoría del handoff debe establecer su resultado; esta matriz no lo sustituye. |

## Lectura inversa y límites de cobertura

| Grupo de casos | Requisitos principales | Razón de agrupación |
|---|---|---|
| CF-001 | R-01–R-17 en sus componentes aplicables | Testigo positivo integrado; obliga a producir resultados, sin reemplazar los negativos |
| CF-002–CF-003 | R-02,R-03,R-04,R-09 | Cuantificadores, testigos y política común |
| CF-004–CF-008 | R-01,R-03,R-06 | Dominio, suficiencia y límites de transporte |
| CF-009–CF-010 | R-05,R-14 | Bloque funcional y transporte exacto de orden |
| CF-011–CF-012 | R-07,R-08,R-13 | Correlaciones, demanda e instante |
| CF-013–CF-015 | R-09,R-14 | Traducción, receta, origen e inclusión de CAG |
| CF-016–CF-019 | R-06,R-10 | Trayectorias, soporte y límites de comparación poblacional |
| CF-020–CF-022 | R-03,R-04 | Información, no vacuidad y perfil fuerte |
| CF-023–CF-024 | R-11,R-17 | Fidelidad y certificados efectivos |
| CF-025–CF-030 | R-11,R-12 | Dominio del veredicto, masa, PVS y refinamiento |
| CF-031 | R-01,R-13,R-14 | Hard parcial y dominio completo de comparación |
| CF-032–CF-034 | R-14,R-15 | Frontera, alcance y selección |
| CF-035 | R-03,R-09,R-16 | Agotamiento operativo y circularidad |
| CF-036 | R-11,R-17 | Contraejemplo al 8.6 literal y clausura canónica de S2 |

El catálogo no pretende agotar todas las combinaciones de errores sintácticos ni todas las entradas finitas. F2 deberá convertir los casos FP1 en fixtures y pruebas ejecutables, completar las comprobaciones de tipos del formato y documentar cobertura. Los casos THEORY_GENERAL son revisiones de propiedades y límites; no justifican añadir capacidades, lectores o comparadores al perfil sin un contrato adicional.

En particular, las entradas de calibración semántica, interpretación causal, referencias empíricas, legitimidad de información y valores normativos siguen siendo premisas externas identificadas. Un test sintético comprueba consecuencias de esas premisas dentro de la instancia; no valida sus afirmaciones sobre el mundo.

La columna de casos de R-18 permanece expresamente sin un equivalente de Kernel: sus obligaciones se acreditan mediante revisión de portabilidad, manifiesto, integridad del paquete y recepción sin contexto. La release no puede inferir esa aceptación del hecho de que todos los CF tengan un oráculo escrito.
