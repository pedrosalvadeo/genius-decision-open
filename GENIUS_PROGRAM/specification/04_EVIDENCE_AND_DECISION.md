# Evidencia, PVS y decisión — MVI–MVII

Specification GENIUS-SPEC-1.0.0. Perfil `FP1_FINITE_EXACT`. Fuente: S1 P02352–P03261; pruebas revisadas en `theory/reviews/REVIEW_VI_VII.md`. Los nombres en mayúsculas de este documento describen variantes semánticas; la codificación de transporte y los códigos definitivos pertenecen al contrato maestro. Una variante no es un booleano de acreditación.

## 1. Alcance y separación de planos

MVI recibe los árboles completos de MV, la tarea y sus referencias semánticas. Construye un evaluador parcial, y, cuando existe una ley legítima, un vector de tres masas. MVII recibe valoraciones de la misma política y aplica restricciones, comparación, frontera y, si fue solicitada mediante regla explícita, selección.

FP1 utiliza tablas finitas cerradas, identificadores tipados y operaciones exactas de conjuntos y racionales. No acepta código del usuario como lector, prueba o comparador. La finitud de los datos permite terminar las verificaciones aquí descritas. No demuestra decidibilidad de tareas o predicados arbitrarios.

Se conservan cinco planos distintos:

| Plano | Qué se establece | Qué no se deduce |
|---|---|---|
| Presentación | Tipos, claves, dominios declarados, referencias estructurales y consistencia de tablas | Verdad empírica |
| Premisas | Referencias del modelo, correspondencia con observaciones y reglas normativas declaradas | Que la procedencia por sí sola pruebe esas premisas |
| Evidencia formal | Coberturas, igualdades, pertenencia al dominio y constancia comprobadas sobre las tablas | Validación del modelo contra el mundo |
| Valor parcial | Valor matemático o ausencia de valor bajo la guarda especificada | Que ausencia sea cero o falsedad |
| Cómputo y alcance | Resultado terminado y conjunto efectivamente cubierto | Exhaustividad sobre políticas o mundos no declarados |

Un campo `fiel=true`, una firma, un nombre de protocolo o una referencia documental no sustituye las operaciones del verificador. Los certificados prueban consecuencias condicionales de las premisas declaradas. La fidelidad empírica de esas premisas requiere evidencia externa fuera de F1.

Cada valor y certificado conserva instancia, política, experimento, tarea, protocolo, versión de las tablas y claves de ocurrencia o consulta pertinentes. Igualdad numérica entre resultados no habilita intercambiar sus procedencias.

## 2. Entrada semántica y tarea

Para cada política π, MV entrega el experimento κπ, un árbol finito de consultas Qπ, su raíz, la relación de prefijo y el conjunto no vacío de hojas Fπ. Cada hoja alcanza H; todos los tiempos 0,…,H están representados. Ni masa cero ni fallo de una restricción eliminan hojas.

La tarea T declara:

1. Un universo finito de significados S, con identidad y descripción de cada significado.
2. Un dominio completo DΦ⊆S y una tabla Φ:DΦ→{0,1}. La ausencia de s en DΦ significa que Φ(s) no está definida. La tabla contiene exactamente las claves de DΦ.
3. Frontera, portadores, horizonte, tiempos requeridos y condiciones normativas a los que se refiere. Su correspondencia con S y Φ es una premisa explícita de la instancia. Si no declara condiciones de vida sostenida, su probabilidad se denomina probabilidad de éxito de la tarea; no adquiere interpretación biológica por renombrar el campo.
4. Para cada π, un dominio DJπ⊆Fπ y una tabla Jtask,π:DJπ→P₊(S), donde P₊(S) son los subconjuntos no vacíos. Una fila definida vacía es inválida; una hoja fuera del dominio declarado conserva la ausencia de referencia.
5. Registros de procedencia para las referencias y reglas. Deben distinguir premisas del modelo, observaciones aportadas y decisiones normativas. La implementación comprueba la identidad y el ámbito de esos registros; no certifica su verdad mediante una etiqueta.

Una tabla estructural requerida ausente, una clave ajena al universo o una fila duplicada contradictoria constituye presentación inválida. Una tabla presente con dominio parcial explícito es válida; su parcialidad puede impedir algunos resultados. No se reconstruye Jtask desde el veredicto que se desea obtener.

Las referencias de hojas describen todos los tiempos y portadores pertinentes de la tarea según sus premisas. FP1 no introduce una regla que deduzca condiciones de toda una trayectoria desde el endpoint. Tal lectura solo es válida si la correspondencia declarada demuestra que los contenidos terminales determinan las condiciones de la trayectoria. En el ejemplo de agua/hábitat, se comprueba la conservación de servicios entre t=1 y t=2; el endpoint aislado no basta.

## 3. Semántica de una consulta

Para h∈Qπ se calcula desde el árbol, sin confiar en una lista aportada por un certificado:

\[
L(h)=\{e\in F_\pi:h\sqsubseteq e\}.
\]

La semántica está definida exactamente cuando L(h)≠∅ y L(h)⊆DJπ. En ese caso:

\[
Sem(h)=\bigcup_{e\in L(h)}J_{task,\pi}(e).
\]

Si falta una referencia, no se devuelve la unión parcial como Sem(h). Se devuelven las hojas sin referencia y el diagnóstico de dominio. En un árbol FP1 válido, la primera guarda se verifica automáticamente, pero se conserva como obligación del contrato para rechazar árboles vacíos o consultas ajenas.

La no vaciedad de cada referencia y de L(h) implica Sem(h)≠∅. Si h⊑h′ y ambas semánticas están definidas, L(h′)⊆L(h) y ∅≠Sem(h′)⊆Sem(h). Este refinamiento semántico no concede al controlador conocimiento de la rama futura.

## 4. Protocolo efectivo que cierra I-07

El único protocolo admitido por FP1 es `FP1_EXACT_ENUM_V1`. Su capacidad declarada conjunta es leer exactamente todas las referencias de las completaciones del árbol finito **y admitir el certificado canónico para cada consulta semánticamente decisiva**, tanto para valor cero como para valor uno. Admitir solo un lector no implicaría esa clausura de certificados; esta es la reparación explícita F1-ED-01 del Teorema 8.6, documentada en la revisión. El lector pertenece al evaluador. La política continúa actuando exclusivamente mediante la información legítima certificada en MV.

### 4.1 Lector admitido

Variante semántica `SEM_UNION`:

| Campo lógico | Contenido |
|---|---|
| Identidad | Instancia, κπ, tarea T, protocolo y consulta h |
| Payload | Lista de hojas L aportada, referencias a sus filas Jtask y conjunto S aportado |
| Verificación | Recalcular L(h), exigir L=L(h); comprobar todas las referencias, dominios y no vaciedad; recalcular su unión y exigir S=Sem(h) |
| Salida aceptada | Sem(h) y testigos de cobertura completa |
| Guarda no satisfecha | Ausencia explícita de semántica; lista de referencias faltantes |

Las listas del payload son declaraciones a comprobar, no una fuente independiente de cobertura. La unión retiene todos los significados, incluidos los desfavorables y los ajenos al dominio de Φ. Un lector que omite una hoja, aunque sea nula para la ley, no obtiene aceptación.

### 4.2 Certificado admitido

Variante semántica `DECISIVE_SET`:

| Campo lógico | Contenido |
|---|---|
| Identidad | La misma identidad del lector, más identificador de certificado |
| Payload | Lectura `SEM_UNION`, conjunto A⊆S, valor v∈{0,1}, referencias a todas las filas Φ de A |
| Comprobaciones | Lectura aceptada; ∅≠Sem(h)⊆A; A⊆DΦ; para todo s∈A, Φ(s)=v |
| Conclusión | Para todo s∈Sem(h), Φ(s)=v |

El verificador enumera A, verifica su dominio completo y su imagen exacta; no acepta un campo «constante» o «cobertura completa». No reduce A a A∩DΦ. El algoritmo del evaluador construye el certificado canónico con A=Sem(h) siempre que la guarda se cumpla; no depende de que un usuario decida presentar uno.

Por construcción, un certificado aceptado tiene al menos un significado testigo. Dos certificados aceptados de una misma consulta y mismas versiones no pueden tener valores distintos: ambos contienen s∈Sem(h) y deben coincidir con Φ(s). Un payload que contradiga un resultado comprobado se rechaza; no se transforma en un tercer resultado semántico ni se elige el certificado favorable.

FP1 no admite lectores arbitrarios ni certificados basados únicamente en hechos de un prefijo. La fuente sí permite esas rutas generales si su cobertura se demuestra. Aquí la lectura exacta cubre ese caso mediante enumeración. Una violación histórica puede producir un certificado con varios significados y veredicto cero, sin identificar un único futuro. Los hechos de una rama hermana no se incorporan como observaciones históricas de h.

### 4.3 Evaluador y dominio exacto

Se define:

\[
D_* = \{h\in D_{Sem}: Sem(h)\subseteq D_\Phi\ \land\ |\Phi[Sem(h)]|=1\}.
\]

El algoritmo obtiene V(h)=v si h∈D*, mediante el certificado canónico; fuera de D* conserva V(h) indefinida. Sus motivos, comprobables exhaustivamente, son referencia semántica ausente, significado fuera de DΦ o coexistencia de veredictos cero y uno. Es posible conocer exactamente que una consulta está fuera de DV sin tener un valor de V para ella.

La equivalencia DV=D* se demuestra en ambas direcciones: aceptación implica las tres guardas; si se cumplen, A=Sem(h) es un certificado admitido. Esta equivalencia depende de este protocolo concreto y de tablas válidas. No promete completitud para todo lenguaje de evidencia.

La vía completa de S1, con extracción Υ, traducción Qeval e interpretación τ, no es una segunda capacidad obligatoria en FP1: su conclusión decidible se obtiene aquí mediante el lector exacto. Una afirmación de fidelidad factual general necesita además verificar por tabla los dominios y las igualdades Jexec(h)=Jloc(Υ(h))=Jc(Qeval(Υ(h))) y τloc(Υ(h))=τc(Qeval(Υ(h))). La existencia de un certificado `DECISIVE_SET` no certifica esas igualdades. Si se presenta una vía completa como material justificativo, tampoco se omiten Sem(h)={Sfull(h)}, Sfull(h)∈DΦ ni sus guardas temporales y terminales. Implementar lectores de esa vía es una extensión versionada fuera del conjunto obligatorio FP1.

## 5. Ley finita exacta, vector de masas y PVS

Cada política conserva su propia ley identificada. La existencia de escenarios, hojas o referencias semánticas no asigna pesos a ninguna rama.

Una presentación de ley contiene un mapa parcial de nodos internos a filas racionales. Cada fila suministrada qh tiene exactamente los hijos causales de h, pesos racionales no negativos y suma exacta uno. Se validan todas las filas suministradas antes de propagar masas, incluso las de nodos nulos. Una fila con hijos omitidos o ajenos, peso negativo o suma incorrecta es inválida.

Se inicia p(raíz)=1. Para cada nodo con masa determinada:

1. Si tiene fila, p(c)=p(h)qh(c) para cada hijo.
2. Si p(h)=0 y no tiene fila, se asigna masa cero a todos sus descendientes para esta ley fija. No se inventa la distribución condicional faltante.
3. Si p(h)>0 y falta fila, la ley foliar no está determinada. Se identifica el nodo y no se emiten VProb ni PVS como valores de esa ley.

La ausencia estructural de la presentación de ley no equivale a una ley parcial aceptada. Las filas parciales válidas pueden producir un diagnóstico de ley no determinada. Un límite de recursos de cómputo tampoco es una masa desconocida: es un estado de cómputo separado.

La inducción sobre la altura del árbol demuestra que, cuando se determina la ley, la masa de las hojas bajo h es p(h); en la raíz suma uno. Las hojas nulas siguen en Fπ y en todas las obligaciones universales.

Con V legítimo se construyen, exclusivamente sobre hojas:

\[
F^+=\{e\in F_\pi\cap D_V:V(e)=1\},\quad
F^-=\{e\in F_\pi\cap D_V:V(e)=0\},\quad
F^?=F_\pi\setminus D_V.
\]

Son disjuntas y exhaustivas. Se suman racionalmente sus pesos y se obtiene:

\[
VProb=(M^+,M^-,M^?),\qquad M^++M^-+M^?=1.
\]

Los prefijos no se suman junto con sus completaciones. La PVS se define exactamente si la ley es legítima y M?=0; entonces PVS=M+. Si M?>0 se entrega VProb con PVS indefinida. No se renormaliza sobre F+∪F−. Una presentación inválida se rechaza antes de construir estas regiones; no se contabiliza como hoja indeterminada.

La guarda fuerte de la integración FP1 exige PVS definida para cada π de la familia objetivo. Una entrada tabular válida puede quedar fuera de esa guarda y producir diagnósticos parciales legítimos. No debe recibir el certificado fuerte integrado ni una frontera exhaustiva que dependa de valoraciones ausentes.

PVS=1 no implica V(e)=1 para toda hoja: una hoja de masa cero puede fallar o tener V indefinida. El predicado universal debe verificarse por separado sobre todo Fπ. Las cotas [M+,M++M?] son cotas para una extensión total semánticamente admisible, si existe; no se etiquetan como PVS y no se afirma alcanzabilidad de extremos sin testigos.

## 6. Conservaciones adicionales y límites

La ley, la tarea y el conjunto de realizaciones permanecen fijos en un refinamiento de evidencia. Si DV1⊆DV2 y V2 coincide con V1 en DV1, las masas de éxito y fallo no disminuyen y la indeterminada no aumenta. Si PVS1 ya existía, PVS2=PVS1. Modificar Φ, Jtask, la ley o el protocolo sin demostrar esa relación no autoriza aplicar el resultado.

Un transporte total T:F→F′ conserva las tres masas si p′ es la imagen directa de p y preserva para toda e la etiqueta semántica completa V̂(e)∈{0,1,indefinida}. Las hojas nulas pertenecen al dominio de T. Esta propiedad no demuestra cobertura causal del destino. Si varias fuentes colapsan en una fibra, sus etiquetas deben coincidir para que exista tal V̂′.

La PVS común entre realizaciones locales requiere familia completa no vacía, cada PVS definida y el mismo valor en todas. FP1 no necesita ese agregador de varios modelos; no promedia modelos ni omite miembros fuera de dominio.

## 7. Restricciones obligatorias efectivas

La familia finita J se declara antes de evaluar. Cada restricción pertenece a una de las variantes admitidas. La validación conserva todos sus diagnósticos; encontrar una refutación no autoriza ocultar faltantes ni presentaciones inválidas.

### 7.1 Presupuesto instantáneo de recursos

Variante semántica `ALL_RESOURCE_LEQ` (nombre de transporte `resource_budget`). Se declara el recurso, la unidad, la cota racional y los componentes cuya demanda conjunta utiliza la tabla de recursos de MII. El conjunto de puntos requerido para π contiene todas las ocurrencias (e,t) con e∈Fπ y 0≤t≤H, incluidas hojas nulas. Se verifica en cada punto la suma conjunta de los componentes especificados contra la cota. No se suman tiempos distintos ni se pondera por probabilidad.

El dominio de una suma local exige todas sus demandas pertinentes, la cota y sus unidades compatibles. Las referencias a componentes y recursos son estructurales: deben existir. Una demanda fuera del dominio parcial declarado deja esa suma indefinida.

- H_j(π)=1 requiere cobertura de todos los puntos y que cada suma esté definida y sea ≤ cota.
- H_j(π)=0 requiere al menos un punto con suma definida > cota. Su certificado conserva (κπ, RunKey, t, recurso, demandas, suma y cota). Otros puntos pueden seguir indefinidos y se mantienen en el diagnóstico.
- Si no hay exceso acreditado y existe algún punto sin suma definida, H_j(π) permanece indefinida.

El certificado positivo enumera todos los puntos requeridos y sus desigualdades; el verificador recalcula cobertura y sumas. El negativo permite recomputar su testigo. Ningún certificado consiste solamente en un valor hard afirmado. Este juicio universal de tres estados permite refutar con un testigo aunque la función «vector completo de sumas» permanezca parcial; no afirma que esa función se haya vuelto total.

### 7.2 Éxito universal de tarea, cuando se solicita

Variante semántica `ALL_TASK_EQ1` (nombre de transporte `task_all`) con modo explícito `LEAVES` o `ALL_NODES`. El conjunto requerido es Fπ o Qπ respectivamente. La tarea, el protocolo y su identidad se fijan en la restricción.

- Valor 1 si todas las consultas requeridas están en DV y tienen V=1.
- Valor 0 si al menos una tiene V=0, con su certificado decisivo.
- Indefinida si no hay cero y falta algún veredicto.

PVS=1 no reemplaza esta verificación. `ALL_NODES` exige decisión positiva incluso en prefijos: es una condición adicional de evidencia, no un sinónimo de éxito eventual. Si el usuario solo exige presupuesto, esta restricción no se añade automáticamente.

FP1 no admite una tabla arbitraria de booleans hard como prueba ni nuevos programas de restricción sin extensión del contrato.

### 7.3 Partición de factibilidad

Tras rechazar contradicciones y entradas inválidas:

\[
A_{feas}=\{\pi:\forall j\in J,\ H_j(\pi)=1\},\quad
A_{fail}=\{\pi:\exists j\in J,\ H_j(\pi)=0\},\quad
A_{unk}=\Pi\setminus(A_{feas}\cup A_{fail}).
\]

La consulta de H incluye su dominio. Un fallo conocido con otras restricciones indeterminadas pertenece a Afail y conserva los faltantes. Con J vacío, todas las políticas son factibles respecto de esa familia vacía; no se acredita una condición no declarada. Excluir una política por hard no borra sus futuros, CAG, bienestar ni PVS.

## 8. Comparación integrada de cuatro criterios

En FP1 las alternativas son exactamente las políticas enumeradas Π. Comparten marco, modelo, contexto, inicialización, horizonte y correspondencia de escenarios. Cada criterio tiene índice fijo; nunca se eligen solo las coordenadas disponibles de cada par.

| Criterio | Valor por π | Dirección favorable y guardas |
|---|---|---|
| Funcionalidad | Perfil indexado de MI prescrito por el contrato integrado | Producto de órdenes calibrados; mismas coordenadas, escenarios y ámbito |
| CAG | CAG de MIII, con familia singleton {π}, receta y modo común declarado (`possible` o `robust`) | Inclusión CAGσ⊆CAGπ; mismo origen, identidad, receta y modo |
| Bienestar | Historia/familia indexada de MIV | Producto en el mismo escenario, portador, tiempo y dimensión; soporte y unidades comunes |
| PVS | Racional M+ de MVI | ≥; PVS definida para ambos, misma tarea y protocolo comparables |

Los perfiles funcionales y de bienestar se consumen tal como los define el contrato integrado; no se resumen por cardinalidad o promedio. Las identidades de portadores y organizaciones no se infieren por igualdad de valores.

Se comprueban todos los dominios de valoración y comparación antes de emitir dominancia, incluso si algún criterio ya resulta desfavorable. La comparación indefinida se distingue de dos valores definidos e incomparables.

Sobre un bloque B⊆Π que satisface todas las guardas, cada criterio usa el mismo preorden para todos sus pares. En FP1 esos preórdenes provienen de inclusión, órdenes calibrados y orden racional. Se verifica la estructura de cada orden tabulado; la transitividad aparente del resultado conjunto no certifica sus componentes.

\[
\pi\succeq\sigma \iff \forall i\in\{O,CAG,W,PVS\},\ Y_i(\pi)\succeq_iY_i(\sigma).
\]

La estricta es π≻σ si π≽σ y no σ≽π. La equivalencia exige ambas comparaciones; la incomparabilidad exige que ambas estén definidas y sean falsas. El resultado incluye el detalle de los cuatro criterios y los testigos de una desigualdad, inclusión fallida o dominio ausente.

La conjunción de preórdenes es reflexiva y transitiva, su estricta es irreflexiva y transitiva, y el cociente por dominancia mutua es un orden parcial. Ninguna de estas propiedades produce una utilidad escalar o una elección única.

## 9. Frontera y certificado de alcance

Para C⊆B∩Afeas:

\[
Fr(C)=\{\pi\in C:\nexists\sigma\in C,\ \sigma\succ\pi\}.
\]

El procedimiento finito comprueba todos los pares pertinentes. Por cada excluida conserva al menos un dominador; por cada maximal conserva el registro de ausencia de dominadores en todo C. Una frontera no vacía existe si C es finito no vacío. Si C es vacío, su frontera es vacía y la selección queda sin valor.

La salida declara C, B, el conjunto objetivo y las políticas omitidas con sus motivos. «Exhaustiva» siempre se refiere a ese objetivo. En una entrada válida parcial, B reúne las políticas con las cuatro valoraciones completas y compatibles con el ámbito común; C=B∩Afeas. La ruta fuerte utiliza B=Π, hard decidido para todas las políticas y C=Afeas; su frontera es exhaustiva para las factibles de Π. La cobertura no se extiende a estrategias que nunca fueron enumeradas.

Si se compara solo C⊆S y hay un mismo preorden definido sobre S, se pueden comprobar dos obligaciones distintas:

1. Cada a∈Fr(C) carece de dominador en S\C: acredita Fr(C)⊆Fr(S).
2. Además, cada u∈S\C tiene un dominador estricto en S: acredita Fr(C)=Fr(S).

Un elemento omitido equivalente a uno encontrado puede ser maximal; por eso la primera obligación no implica la segunda. Sin valoraciones suficientes para aplicar el mismo preorden en S, no se certifica ninguna de esas garantías globales por defecto.

Cuando hard sigue indeterminado pero el preorden sí está definido en Afeas∪Aunk, pueden informarse, con su etiqueta de cotas para una familia exterior:

\[
N=A_{feas}\cap Fr(A_{feas}\cup A_{unk}),\qquad
P=\{a\in A_{feas}\cup A_{unk}:\nexists f\in A_{feas},\ f\succ a\}.
\]

Son los miembros necesarios y posibles de las fronteras sobre todos Afeas∪T, T⊆Aunk. No se afirma que todas esas admisiones sean realizables simultáneamente. Este diagnóstico opcional no convierte a una entrada parcial en instancia de la ruta fuerte.

Robustez entre varios modelos, reducción de alternativas y selección equivariante sobre familias de problemas tienen resultados revisados en S1. Son extensiones fuera del perfil operativo mínimo; una implementación FP1 no afirma soportarlas por haber calculado una frontera ordinaria.

## 10. Selección explícita

La selección tiene variante de regla separada:

| Regla | Dominio y resultado |
|---|---|
| `NONE` | Sin valor seleccionado; se devuelve la frontera y su alcance |
| `UNIQUE` | Selecciona únicamente si la frontera está certificada `EXHAUSTIVE` y contiene exactamente una política |
| `PRIORITY_LIST` | Requiere una lista de prioridad completa sin duplicados sobre Π y una frontera `EXHAUSTIVE` no vacía; selecciona su primer maximal |

`NONE` es el comportamiento por defecto. No se desempata por orden de entrada, ID, alfabeto o PVS sin regla solicitada. La lista de prioridad constituye un dato normativo adicional. Debe transportarse con el problema; no se afirma equivarianza bajo simetrías que la cambian. FP1 no permite seleccionar sobre una frontera `RELATIVE` en ninguno de sus modos. La selección con alcance local pertenece a la teoría general y requeriría un contrato de extensión separado.

## 11. Salidas y obligaciones para F2

El registro por política incluye V parcial en todas las consultas con motivos, certificados generados, filas y masas de ley o diagnóstico de no determinación, partición foliar, VProb cuando procede, PVS con su dominio y juicios hard con cobertura y testigos. El registro de decisión incluye los cuatro criterios con procedencia, bloque y matriz de comparación, partición de factibilidad, frontera, cobertura del objetivo y selector con regla y dominio.

F2 deberá preservar esos objetos y distinguir presentación inválida, entrada válida fuera de una guarda, cálculo no terminado y resultado matemático definido. Deberá implementar exactamente las operaciones finitas descritas; no necesita motores de prueba generales ni intérpretes de código para el usuario.

Obligaciones nucleares para la matriz de trazabilidad:

| ID | Comprobación | Fuente |
|---|---|---|
| VI-01 | Jtask parcial a conjuntos no vacíos; no derivada del veredicto | P02453–P02464 |
| VI-02 | L exacto y cobertura total antes de Sem | P02459–P02477 |
| VI-03 | Certificado: no vaciedad, inclusión, dominio completo y constancia | P02518–P02542 |
| VI-04 | DV=D* solo para protocolo exacto admitido | P02607–P02621 |
| VI-05 | Filas racionales completas, incluso nulas; omisión positiva no determina ley | P02625–P02650 |
| VI-06 | Tripartición foliar sin prefijos duplicados; suma uno | P02658–P02677 |
| VI-07 | PVS definida si y solo si ley legítima y M?=0 | P02680–P02736 |
| VI-08 | No renormalización y no inferencia PVS=1⇒garantía universal | P02712–P02736 |
| VII-01 | Hard con prueba por cobertura o testigo; parcialidad preservada | P02904–P02927 |
| VII-02 | Cuatro criterios comunes y todos sus dominios | P02847–P02901 |
| VII-03 | Preórdenes componentes antes de integrar | P02930–P02959 |
| VII-04 | Frontera con objetivo explícito y dos obligaciones de cobertura | P02962–P03012 |
| VII-05 | Selección con regla y dominio explícitos | P03098–P03110 |

La interpretación fuerte de estas obligaciones queda condicionada a las premisas de la instancia. El cierre de I-07 es contractual y deductivo: la fase no ha implementado ni ejecutado el Kernel.
