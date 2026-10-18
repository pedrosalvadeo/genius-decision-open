# Enmiendas explícitas a la lectura de S1

Estado: propuestas integradas por el formalizador de fundamentos/M0–MIII, sujetas a la revisión adversarial separada de F1. Fecha: 2026-09-23. Fuente S1 inalterada: `sources/S1_Matematica_Genius_Modulos_Astra_01.docx`. Pnnnnn identifica el párrafo en orden de `word/document.xml`, como en `S1_EXTRACTED.txt`; ese extracto sirve solo para localizar. Se contrastó el agrupamiento OMML del DOCX cuando la lectura derivada era ambigua.

## AM-01 / A-F1-001 — I-06: actualización informacional

**Localización:** S1 P00527–P00540, especialmente P00530, P00532, P00534–P00536 y P00538. Relación con módulo V: Definición 7.5, actualización `U_γ(t,ι,a,y')=ι'`.

**Original:** el lado izquierdo de P00535 agrupa correctamente `R_{t+1}(U_t^A(i,θ,y))`. El lado derecho tiene un delimitador de tres componentes OMML: `R_t` ; `(i)` ; `θ O_{t+1}(y)`. Su transcripción visible en `S1_READABLE.md` es `U_t^B(R_t,(i),θ O_{t+1}(y))`. No se trata solo de pérdida de separadores en texto plano: se inspeccionaron los tres nodos `m:e` del delimitador original.

**Problema:** U_t^B recibe primero una función en vez de información de I_t^B, mientras el segundo argumento queda i en vez de acción. La concatenación final tampoco produce una observación de tipo Y_{t+1}^B. La prosa P00536 exige que actualizar y después representar coincida con representar y después actualizar; P00538 utiliza correctamente `π_t^B(R_t(i))=π_t^A(i)`.

**Reparación adoptada:**

\[
\boxed{R_{t+1}(U_t^A(i,\theta,y))
=U_t^B(R_t(i),\theta,O_{t+1}(y)).}
\]

No se cambia el contenido causal: se reparan los límites de aplicación y las comas para hacer coincidir la ecuación con sus tipos y explicación. La alternativa literal que tratase R_t como información sería incompatible con P00530, P00536 y P00538, y se rechaza.

**Tipado completo:** para K∈{A,B},

\[
U_t^K:I_t^K\times A_t\times Y_{t+1}^K\rightharpoonup I_{t+1}^K,
\quad R_t:I_t^A\to I_t^B,
\quad O_{t+1}:Y_{t+1}^A\to Y_{t+1}^B.
\]

Las acciones se identifican en el mismo A_t. Un cambio de alfabeto de acciones necesita otro mapa y otro contrato, no está implícito en esta enmienda. R_t y O_{t+1} son totales sobre los universos declarados, como en S1. Las U pueden ser parciales; definir `v_t(i,a,y)=(R_t(i),a,O_{t+1}(y))` y declarar un conjunto K_t de triples pertinentes. Exigir tanto

\[
K_t\cap D_{U_t^A}=K_t\cap v_t^{-1}(D_{U_t^B})
\]

como igualdad de los valores compuestos sobre ese dominio. Esto precisa «con dominios compatibles» de P00534. Si se afirma transporte de todas las ejecuciones, K_t debe cubrir todos los triples realmente usados en las ejecuciones pertinentes, y la cobertura se comprueba.

**Prueba del transporte informacional:** la inicialización da `ι_0^B=R_0(ι_0^A)`. En el paso t, la correspondencia parcial de políticas da misma acción; la correspondencia causal conjunta da observaciones relacionadas por O. La igualdad de dominios permite calcular ambas U y la ecuación reparada da `ι_{t+1}^B=R_{t+1}(ι_{t+1}^A)`. La inducción termina en cualquier H finito. Para igualdad de conjuntos de trazas se necesitan también las dos direcciones de correspondencia causal; esta ecuación no las demuestra. Para transportar familias de políticas se necesita pertenencia y cobertura de un mapa entre esas familias; tampoco se deducen de la ecuación.

**Por qué hacen falta las guardas:** si dos informaciones i₁,i₂ tienen mismo R_t pero πA(i₁)≠πA(i₂), ninguna política funcional de B puede realizar ambas acciones. Si las U coinciden donde ambas están definidas pero una carece de actualización en un triple requerido, la trayectoria no se transporta. Estos contraejemplos separan igualdad de valores, igualdad de dominios y existencia de política trasladada.

**Impacto:** M0, MV y todo reclamo de transporte de garantías de control. No afecta la prueba de Teorema 2.4, que trata trazas del sistema generativo sin concluir transporte de políticas por sí solo. La reparación establece obligaciones finitamente comprobables si se suministran las tablas pertinentes. El formato actual `FP1_FINITE_EXACT` no admite un segundo modelo ni mapas R/O entre presentaciones, por lo que ese verificador de transporte pertenece a una extensión posterior. Dentro de la instancia FP1 se mantiene la misma presentación, correspondiente al caso identidad; la ecuación no se convierte en una premisa booleana.

**Estado de revisión del autor:** `REPAIRED`; argumento deductivo revisado, pendiente del dictamen separado de F1 al escribir esta entrada. No es demostración mecanizada ni validación empírica.

## A-F1-002 — Separadores y agrupación en fundamentos/M0–MIII

La inspección detectó otros agrupamientos mal ubicados en las fórmulas OMML. La Specification presenta abajo su lectura tipada; preserva el DOCX y no atribuye el defecto al derivado cuando aparece en el original. Se trata de erratas de notación con resolución fijada por los tipos, la prosa inmediata y los ejemplos. No se modifican hipótesis ni conclusiones de los 25 resultados numerados revisados.

| Localizador | Defecto observado / referencia contextual | Lectura adoptada y razón |
|---|---|---|
| P00423 | El segundo delimitador separa `b` de `+mm`, dando `(b,+mm)`; P00433 fija biomasa siguiente b+m y el ejemplo mantiene m | `(b,m)↦(b+m,m)`. Regla sintética sobre `N×{0,1}`, consistente con los estados y resultados del ejemplo |
| P00477, P00484, P00492 y apariciones en prueba 2.4 | Separación de ψ respecto de su argumento y concatenación de los demás componentes; P00478 dice «pares completos» | Par `(ψ(s'),o(y))`, fila `Bbar(ψ(s),a)` y paso traducido `(a,ψ(s'),o(y))`. Los tipos de ψ,o y de B fuerzan estas aplicaciones |
| P00590, P00596, P00609, P00611, P00613, P00615 | OMML separa Σ o F_i de su argumento y concatena x con A o t; P00587 y P00594 dan los tipos y P00605–P00611 el orden de comprobación | `y_i(x)=F_i(Σ(x),x,A)`; `o_i(x,t)=u_i(F_i(Σ(x),x,A),x,t)`; dominios `D_i^F={(x,t):x∈D_Σ ∧ (Σ(x),x,A)∈D_Fi}` y `D_i={(x,t)∈D_i^F:(y_i(x),x,t)∈D_ui}` |
| P01095 | Delimitadores de la fila distribuyen mal los signos de asignación; P01097–P01103 especifican valores | `h₁=(w₁,a=0,b=0)`, `h₂=(w₂,a=0,b=1)`; ψ conserva solo a y q consulta b |
| P01191, P01194 y expresiones homólogas de Runs en MIII | La transcripción de aplicaciones presenta separadores dentro de `b_γ(w)`; P01184 declara esa inicialización como argumento único | `Runs_{H,γ}(b_γ(w);π;ξ)` y ocurrencias `{(ξ,e):ξ∈Ξ(w,π), e∈Runs_{H,γ}(b_γ(w);π;ξ)}`. El escenario no reemplaza la ejecución |

La notación `a ⪰̸ c` y formas equivalentes del derivado se leen como negación de la relación completa indicada, conforme a los contraejemplos y definiciones. No se usa la posición tipográfica del trazo para crear otra relación.

**Auditoría y alcance:** se reconstruyeron las expresiones por sus tipos y se revisaron los argumentos donde se usan. Se documenta esta normalización en vez de afirmar que el texto fuente era formalmente impecable. Los teoremas se registran como válidos bajo sus hipótesis y esta lectura tipada; la enmienda de notación se registra como `REPAIRED_NOTATION`. La revisión separada decide la aceptación del paquete.

## A-F1-003 — Especializaciones de perfil sin reforma de S1

Estas decisiones se declaran para evitar presentarlas como nuevas hipótesis de toda la teoría:

- El perfil usa familias Π y Ξ finitas no vacías, una ejecución completa por escenario y política, y horizonte fijo H; S1 MIII general permite más casos. Un H=0 sigue siendo finito: logros futuros vacíos y CAG canónico igual al singleton del origen.
- Las firmas generativas del intercambio pueden estar ya cocientadas como IDs, con equivalencia literal de IDs. La igualdad de significado no fusiona automáticamente identidades. La traducción sobre IDs factoriza la traducción de estados de S1 y es una subclase más restrictiva.
- Los preórdenes, equivalencias y mapas del perfil se deciden mediante tablas cerradas; la condición matemática de finitud sola no provee esas tablas.
- El contrato de recursos inicial trata consumos racionales no negativos de una misma unidad y ámbito temporal. Extensiones con cantidades firmadas exigen declarar su interpretación y contrato.
- Exigir fidelidad de conservación en todos los pares de identidades alcanzadas es una validación finita más fuerte que comprobar únicamente los pares usados por la receta. Si el contrato maestro adopta esa guardia, se conserva como restricción del perfil, no como condición necesaria de Teorema 5.1 ni de `att` general.

No se encontró un contraejemplo a las 25 proposiciones/teoremas de fundamentos y M0–MIII interpretados con sus hipótesis explícitas. Esto no equivale a ausencia demostrada de errores en toda la teoría; el dictamen se limita al tramo leído y a las comprobaciones descritas en su revisión.

## AM-02 / F1-ED-01 — Clausura de admisión en Teorema 8.6

**Autoría y evidencia:** hallazgo del formalizador MVI–MVII, contrastado por el Integrador contra S1 y recogido aquí por instrucción de integración. Desarrollo completo en `reviews/REVIEW_VI_VII.md`, sección F1-ED-01, y contrato operativo en `../specification/04_EVIDENCE_AND_DECISION.md`. Este registro no afirma que ya haya concluido la auditoría independiente.

**Original y localización:** Definición 8.6 (S1 P02518–P02528) distingue lectores y certificados admitidos por un protocolo. Teorema 8.6 (P02610–P02618) afirma `D_V=D_*` cuando el protocolo admite lectura exacta fundamentada de Sem(h). P02620 reconoce que restricciones sobre certificados pueden reducir el dominio.

**Problema y contraejemplo:** admitir un lector exacto no implica admitir el certificado que utiliza la demostración. Tomar una consulta h con `Sem(h)={p,q}`, p≠q, ambos en D_Φ y `Φ(p)=Φ(q)=0`. El protocolo permite leer exactamente ese conjunto, pero no admite certificados decisivos; alternativamente, admite solo certificados de valor uno. La vía completa exige significado singleton, así que tampoco aplica. Entonces h∈D_* y h∉D_V. El supuesto literal sobre lectura no basta para la igualdad anunciada.

**Enunciado reparado:** si el protocolo admite la lectura exacta fundamentada de Sem y, **para cada h∈D_***, admite el certificado canónico `A_h=Sem(h)` con el único valor `v_h∈Φ[Sem(h)]`, satisfaciendo las restantes guardas de evidencia aplicables, entonces `D_V=D_*`.

**Prueba:** `D_V⊆D_*` sigue de las guardas de cualquier ruta admitida: semántica no vacía, cobertura, dominio y constancia; la vía completa también cumple esas condiciones. Para `h∈D_*`, la lectura exacta obtiene el conjunto no vacío Sem(h), incluido en D_Φ y con un único veredicto. La nueva hipótesis garantiza que el certificado canónico resultante se admite, de modo que h∈D_V. Se obtienen ambas inclusiones.

**Impacto y resolución FP1:** `FP1_EXACT_ENUM_V1` constituye una capacidad conjunta de lectura exacta y certificación canónica, admite tanto veredictos cero como uno y genera automáticamente el certificado cuando las guardas se cumplen. El verificador recalcula cobertura, dominio y constancia; no depende de un flag ni de una decisión favorable del usuario. Así el perfil satisface constructivamente la hipótesis añadida y puede utilizar el teorema reparado. El enunciado sin esa hipótesis no se invoca sobre protocolos arbitrarios. El cálculo posterior de masas y PVS conserva sus propias hipótesis.

**Estado:** `REPAIRED_HYPOTHESIS`. Es una reparación sustantiva del alcance del teorema, distinta de una errata de notación. Fuentes intactas, revisión separada pendiente al registrar el hallazgo.

## AM-03 / F1-ED-02 — Acuerdo de una completación foliar

**Fuente:** S1 P02739–P02751, Proposición 8.9; análisis en `reviews/REVIEW_VI_VII.md`, F1-ED-02. La extensión se tipa `V*:F→{0,1}`, mientras V puede estar definida también en prefijos no foliares. La frase «coincide con V en D_V» se reemplaza por **«coincide con V en F∩D_V»**. No se exige D_V⊆F ni se descartan evaluaciones tempranas.

La prueba fuente opera sobre regiones foliares: `F^+⊆{V*=1}⊆F^+∪F^?`, porque la extensión conserva los éxitos y fallos foliares establecidos. Aplicar la medida da `M^+≤P(V*=1)≤M^++M^?`. La corrección tipa la hipótesis sin afirmar existencia de una extensión admisible ni alcanzabilidad de los extremos. Estado: `REPAIRED_TYPING`; la desigualdad permanece válida bajo la hipótesis correctamente restringida.

## AM-04 / F1-ED-03 — Notación y ámbitos de MVI–MVII

Hallazgos del formalizador MVI–MVII documentados con análisis OMML en `reviews/REVIEW_VI_VII.md`:

| Fuente | Corrección explícita | Justificación e impacto |
|---|---|---|
| P02461 | `L(h)≠∅ ∧ L(h)⊆D_J` | La referencia semántica exige no vaciedad y cobertura conjuntamente; omitir conjunción no elimina ninguna guarda |
| P02609 | `Sem(h)⊆D_Φ ∧ |Φ[Sem(h)]|=1` dentro del dominio de Sem | El dominio decisivo exige tanto dominio total de tarea en la semántica como constancia; el conjunto no vacío procede del contrato Sem |
| P02892 | `(Y_i(a),Y_i(b))∈D_i` | El par de argumentos del comparador se tipa con dos valores, como exige Definición 9.2; no con la función Y_i y una concatenación de sus argumentos |
| P03100 | Separar la familia de problemas de un problema miembro con símbolos distintos | Evita sobrecarga de K; no cambia la acción de simetría ni los cuantificadores del selector |

Estado: `REPAIRED_NOTATION`. Estas normalizaciones no reemplazan la hipótesis adicional de AM-02 ni constituyen nuevos resultados.

## Cierre de revisión separada en esta release

Las notas anteriores conservan el estado que tenían al registrarse. La auditoría interna separada final verificó AM-01–AM-04 y las normalizaciones de REVIEW_INTEGRATION §7 y emitió PASS para el contrato FP1. Véase [AUDIT_REPORT](../validation/AUDIT_REPORT.md); el gate integral se fundamenta en [ACCEPTANCE_REPORT](../../ACCEPTANCE_REPORT.md). No es aceptación del enunciado literal de 8.6 sin su hipótesis adicional, ni prueba mecanizada o validación empírica.

## AM-02 — Ley empírica de escenarios y revisión de modelos

**Texto completo:** `PROPOSAL_AM-02.md`, con la revisión adversarial separada y sus once reparaciones.

**Estado:** `ACEPTADA_CON_REPARACIONES` el 2026-10-17. Agrega una premisa de legitimidad empírica para la ley de la Definición 8.9 (LEA) y un operador de revisión de modelos versionados.

**Alcance:** no cambia S1 ni el kernel FP1. Ninguna LEA está admitida todavía: la primera aplicación, Lake Mead 2027, se rechaza por falta de resultados independientes y porque su clasificación depende de la política en vigor.

## AM-02.1 — Ley empírica con varios conductores

**Texto completo:** `PROPOSAL_AM-02.1.md`.

**Estado:** `ACEPTADA` el 2026-10-18 por Pedro. Extiende la LEA de AM-02 a escenarios definidos por 2 o 3 conductores exógenos a la vez. Los escenarios forman una partición de todas las combinaciones de categorías. Hay tres candidatas fijadas de antemano: masas iguales, frecuencia conjunta y conductores independientes. Se comprueban como en AM-02.

**Alcance:** no cambia S1 ni el kernel FP1. Se sirve en `POST /laws/driver/joint` y en el MCP (`twin_joint_driver_law`). En la cuenca del Colorado, 14 de los últimos 30 años no alinearon la nieve de Denver con la afluencia a Powell, lo que refuta el supuesto `SharedHydrology` de la federación. Qué ley gana depende de la partición, así que esa ley es frágil. Una revisión adversarial separada pidió diez reparaciones, ya incorporadas.

## AM-05 — Decisión dentro de una ventana de oportunidad

**Texto completo:** `PROPOSAL_AM-05.md`.

**Estado:** `ACEPTADA` el 2026-10-18 por Pedro. Cuando el cálculo completo no entra en la ventana del decisor, los escenarios se evalúan de a uno, por masa decreciente, y se entregan cotas exactas de PVS y rutas refutadas. Una selección sólo se emite si el modelo la permite y queda una única ruta no refutada, condicionada a los escenarios que faltan. Una revisión adversarial separada pidió diez reparaciones, ya incorporadas.

**Alcance:** no cambia S1 ni el kernel FP1. Los pasos comprometidos (`decision_window.py`) y la frescura de cada resultado ya funcionan sin cambiar la matemática. El cálculo por escenarios se sirve en `POST /cases/<cid>/anytime/evaluate` y en el MCP (`twin_evaluate_anytime`).
