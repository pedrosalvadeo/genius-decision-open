# Catálogo de conformidad de Fase 1

Versión candidata: GENIUS-SPEC-1.0.0. Fuente base preservada: S1, instantánea GENIUS-THEORY-2026-09-23-S1. La Specification usa S2 con enmiendas explícitas, incluida F1-ED-01. Perfil principal: **FP1_FINITE_EXACT**.

**Estado de todos los casos: DESIGNED.** Son oráculos matemáticos y contractuales derivados por razonamiento; no son resultados de ejecución sobre un Kernel. F1 no implementa el Kernel. Los valores sintéticos no validan empíricamente la utilidad, el bienestar o la vida sostenida.

`FP1_FINITE_EXACT` significa que el caso verifica un contrato del perfil, incluida la respuesta frente a una presentación que incumple una guarda. No significa que las variantes negativas satisfagan todas sus hipótesis. `THEORY_GENERAL` identifica una propiedad revisada de la teoría fuera de las operaciones prometidas por FP1, o una prueba de límite de esa promesa. Ningún caso general agrega capacidades al Kernel de F2 por su sola inclusión.

Los nombres de operaciones y resultados en este catálogo son descripciones semánticas, **no un segundo esquema de serialización**. Los tipos y códigos definitivos se toman de la Specification integrada. El índice JSON enumera las mismas entradas, premisas, resultados y derivaciones para enlazarlas con requisitos normativos. Una implementación futura deberá materializar fixtures completos, ejecutar los casos y registrar versión, resultado y evidencia; los estados actuales no se pueden convertir a PASS sin esa ejecución.

Las referencias `S1:Pxxxxx` localizan párrafos en el DOCX original, no páginas. Las fórmulas se interpretan con el original y `theory/sources/S1_READABLE.md`; el extracto de texto solo localiza. Los `INV-*` son las identidades persistentes del registro recibido de F0. Las vinculaciones se refieren a la regla pertinente y no significan que cada caso cubra todo el invariante.

## Instancia base B: agua y hábitat

Materialización portable: [entrada](WATER_HABITAT.input.json), [proyección esperada](WATER_HABITAT.expected.json) y [guía](WATER_HABITAT.README.md). La proyección es un oráculo DESIGNED, no una salida de Kernel ejecutada.

Fuente: S1 P03552–P03639, extendida por las consultas de P03641–P03656. Esta especificación matemática complementa el fixture completo que acompañará el paquete.

- Horizonte H=2; tiempos 0,1,2; escenarios Ξ={r,s}, regular y estrés; políticas Π={πa,πh,πah}, familia objetivo completa declarada.
- Un estado inicial x0 con organización ∅. La acción inicial instala B∈{{a},{h},{a,h}}. Sus dos resultados causales son (B,r) y (B,s), con etiquetas distintas, aunque observación común. En t=1 la política mantiene B en ambos estados, hasta t=2. La información del controlador no distingue r/s y la acción de mantenimiento tampoco depende de esa distinción.
- Por política: raíz h0_B; nodos n_B,r y n_B,s en t=1; hojas e_B,r y e_B,s en t=2. Edges: h0_B→n_B,r→e_B,r y h0_B→n_B,s→e_B,s. La identidad de nodo incluye política: las raíces de los tres árboles son ocurrencias distintas de la misma condición inicial. Las palabras exógenas son (u_regular,u_hold) y (u_estres,u_hold), con u_regular≠u_estres y observación común tras instalar; la biyección Ξ→hojas envía ξ a e_B,ξ. Hay 5 nodos por política, 15 en total.
- Organización Σ(x0)=∅ y Σ(B,ξ)=B. Perfil funcional común O=(1[a∈Σ],1[h∈Σ]), con dos índices, valores binarios y calibración identidad. La consulta funcional factoriza por (Σ,t); la tarea semántica no factoriza por Σ cuando se pierde ξ.
- Identidad generativa=B, conservación por inclusión, traducción identidad. Traza (∅,B,B); receta hold,1 robusta. Ach_hold,1={B}; CAG={∅,B}. La inclusión que compara **conjuntos de identidades** CAG no se sustituye por conservación entre las identidades que contienen.
- Dos portadores l1,l2 existen en todos los tiempos y una dimensión binaria es aplicable a ambos; todas las seis mediciones por hoja están presentes. w(l1,t)=1[a∈Σ(x_t)], w(l2,t)=1[h∈Σ(x_t)]. Se comparan el mismo portador, tiempo y dimensión, por separado para cada escenario.
- Las demandas identificadas d_a,d_h son las dos componentes funcionales en cada nodo, y pertenecen a un fondo de capacidad instantánea 1. En t=0 el uso es 0; después es 1,1,2 para las tres políticas. La restricción hard pide cumplir en cada nodo. Sus resultados no filtran el árbol causal ni forman parte de la tarea Φ.
- Semántica S={ (B,ξ): B∈{{a},{h},{a,h}}, ξ∈{r,s} }; J(e_B,ξ)={(B,ξ)}. La tarea es total: Φ(B,r)=1[B≠∅] y Φ(B,s)=1[{a,h}⊆B]. Estas referencias bastan aquí para la condición temporal en t=1,2 porque el proceso ya acredita que B se mantiene en ambos tiempos. No se generaliza ese uso del endpoint a procesos con daños intermedios.
- Puentes iniciales, factuales y semánticos son identidades sobre sus dominios explícitos, con intérpretes singleton coincidentes. Un lector exacto forma Sem(h) por unión de todas las hojas descendientes y solo decide cuando la imagen de Φ es singleton. No se agrega un requisito de endpoint adicional.
- Filas probabilísticas: (3/4,1/4) en la instalación y peso 1 para cada mantenimiento. La masa de cada hoja coincide con la de su escenario. Las hojas se conservan aunque una variante les asigne cero.

| Política | O en t=1,2 | w(l1) en t=0,1,2 | w(l2) en t=0,1,2 | V regular,estrés | VProb | Restricción hard |
|---|---|---|---|---|---|---|
| πa | (1,0) | (0,1,1) | (0,0,0) | (1,0) | (3/4,1/4,0) | Cumple |
| πh | (0,1) | (0,0,0) | (0,1,1) | (1,0) | (3/4,1/4,0) | Cumple |
| πah | (1,1) | (0,1,1) | (0,1,1) | (1,1) | (1,0,0) | Refutada: 2>1 |

No se declara selección. La frontera exacta de la familia factible es {πa,πh}.

## Índice de cobertura

| ID | Caso | Alcance | Estado |
|---|---|---|---|
| CF-001 | Agua/hábitat: testigo integrado completo | FP1 | DESIGNED |
| CF-002 | El escenario no puede elegir retrospectivamente la política | FP1 | DESIGNED |
| CF-003 | Testigos separados no acreditan una conjunción | FP1 | DESIGNED |
| CF-004 | Cero, dominio, evidencia y entrada inválida son planos distintos | FP1 | DESIGNED |
| CF-005 | Factorización parcial exacta: caso positivo | FP1 | DESIGNED |
| CF-006 | Fibra mixta: perder el dominio fabrica respuestas | FP1 | DESIGNED |
| CF-007 | Las marginales de una transición no acreditan DSuf | Teoría general | DESIGNED |
| CF-008 | La actualización informacional debe conmutar con su traducción | Teoría general | DESIGNED |
| CF-009 | Índices funcionales cambiantes producen un ciclo espurio | FP1 | DESIGNED |
| CF-010 | Calibración monótona que no refleja orden | Teoría general | DESIGNED |
| CF-011 | Unión natural espuria por pérdida de correlación | FP1 | DESIGNED |
| CF-012 | Recursos: identidad de demanda y presupuesto por instante | FP1 | DESIGNED |
| CF-013 | Traducir antes de intersectar robustez | FP1 | DESIGNED |
| CF-014 | CAG: cardinalidad, inclusión y origen | FP1 | DESIGNED |
| CF-015 | Alcance, mantenimiento, acumulación y coexistencia | FP1 | DESIGNED |
| CF-016 | Daño intermedio aunque coincida el endpoint | FP1 | DESIGNED |
| CF-017 | Reloj, existencia y medición no se rellenan con cero | FP1 | DESIGNED |
| CF-018 | Una sola biyección para toda la trayectoria | Teoría general | DESIGNED |
| CF-019 | Un matching negativo necesita todas las aristas decididas | Teoría general | DESIGNED |
| CF-020 | Una política no puede leer el estado oculto | FP1 | DESIGNED |
| CF-021 | La garantía no nace de una familia vacía | FP1 | DESIGNED |
| CF-022 | Límites de la ruta fuerte: escenario único y horizonte completo | FP1 | DESIGNED |
| CF-023 | Igual veredicto no prueba fidelidad de significado | Teoría general | DESIGNED |
| CF-024 | Certificados decisivos comprobados, no declarados | FP1 | DESIGNED |
| CF-025 | Raíz indeterminada con PVS definida | FP1 | DESIGNED |
| CF-026 | Masa indeterminada positiva no se renormaliza | FP1 | DESIGNED |
| CF-027 | Hojas nulas: PVS=1 no implica garantía universal | FP1 | DESIGNED |
| CF-028 | Una fila probabilística inválida no se sanea por masa cero | FP1 | DESIGNED |
| CF-029 | Una ley requiere datos; las masas se suman en una partición | FP1 | DESIGNED |
| CF-030 | Refinar evidencia no puede cambiar tarea, realización ni ley | Teoría general | DESIGNED |
| CF-031 | Factibilidad y comparación parcial sin cortocircuitos falsos | FP1 | DESIGNED |
| CF-032 | La frontera robusta no es la intersección de fronteras | Teoría general | DESIGNED |
| CF-033 | Cobertura de frontera y ausencia de selector por defecto | FP1 | DESIGNED |
| CF-034 | La simetría puede impedir selección equivariante | Teoría general | DESIGNED |
| CF-035 | Agotar recursos de cómputo no demuestra imposibilidad | FP1 | DESIGNED |
| CF-036 | Lector exacto sin admisión canónica: contraejemplo y reparación de 8.6 | Teoría general | DESIGNED |

## Casos y oráculos

### CF-001 — Agua/hábitat: testigo integrado completo

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** positive.

**Fuentes:** S1:P03552-P03639; S1:Teoremas 10.2 y 10.3. **Invariantes:** INV-06, INV-14, INV-16, INV-18, INV-20, INV-26, INV-28, INV-30.

**Precondiciones.** Usar exactamente la instancia B definida al comienzo del catálogo. Las identidades, referencias y ley son datos sintéticos explícitos; no evidencia empírica.

**Entrada.** B, con las tres políticas πa, πh, πah; H=2; Ξ={r,s}; q(r)=3/4, q(s)=1/4; receta hold,1 robusta; presupuesto instantáneo 1.

**Oráculo.** Cada política genera 5 nodos y 2 hojas; total 15 nodos y 6 hojas. CAGπB={∅,B}. PVS=(3/4,3/4,1). Factibles={πa,πh}; refutada por presupuesto={πah}; frontera exacta respecto de Π={πa,πh}; no hay selección solicitada. Las 2 hojas y los 5 nodos de πah permanecen registrados.

**Derivación.** Las ramas r y s conservan B durante t=1,2, por lo que ambas acreditan B mediante hold,1. En r todas las políticas cumplen la tarea; en s solo πah. Las masas positivas son por ello 3/4,3/4,1. La suma de demandas es 1,1,2 después de instalar. πa y πh intercambian ventajas funcionales y de bienestar, y sus CAG no se incluyen mutuamente. πah tampoco domina sus CAG: {a} y {h} no son elementos de {∅,{a,h}}. La frontera factible tiene exactamente dos elementos.

### CF-002 — El escenario no puede elegir retrospectivamente la política

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P00213-P00222; S1:Teorema 5.2. **Invariantes:** INV-08, INV-22.

**Precondiciones.** Una realización por política y escenario; políticas elegidas antes del escenario. Usar att y un origen o distinto de u,v,z.

**Entrada.** H=2; p,r:(o,u,z); p,s:(o,u,u); q,r:(o,v,v); q,s:(o,v,z). Todas las trazas están cubiertas.

**Oráculo.** Logros robustos p={u}, q={v}; repertorio robusto de la familia={u,v}; repertorio posible={u,v,z}. La proposición ∀ξ∃π que alcanza z es verdadera; ∃π∀ξ que alcanza z es falsa.

**Derivación.** Para p la intersección {u,z}∩{u}={u}; para q, {v}∩{v,z}={v}. Elegir p en r y q en s usa una política dependiente del escenario, que no pertenece a la familia elegida de antemano.

### CF-003 — Testigos separados no acreditan una conjunción

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P00170-P00201; S1:Definición 5.9 y Proposición 5.4. **Invariantes:** INV-06, INV-38.

**Precondiciones.** Toda atribución conjunta mantiene la misma política y la misma ocurrencia exigida por la consulta.

**Entrada.** Variante A: una política con hojas e1,e2; (A(e1),B(e1))=(1,0), (A(e2),B(e2))=(0,1). Variante B: p garantiza solo u en todas sus hojas y q garantiza solo v; D={u,v}.

**Oráculo.** A: existen testigos de A y B por separado; no existe hoja con A∧B. B: {u,v} está contenido en la unión de repertorios robustos, pero Joint_att(D)=∅.

**Derivación.** En A cada una de las dos filas tiene un cero. En B ninguna fila de política contiene ambas demandas. Combinar una hoja de p con una de q, o dos hojas distintas de una política, cambia el cuantificador y no produce el testigo conjunto pedido.

### CF-004 — Cero, dominio, evidencia y entrada inválida son planos distintos

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** mixed.

**Fuentes:** S1:P00091-P00117; S1:P00143-P00168. **Invariantes:** INV-03, INV-04, INV-05, INV-31.

**Precondiciones.** En FP1 las tablas parciales son cerradas y su dominio es exactamente el conjunto de claves presentes. No existe un campo wire dom(f) que prometa filas adicionales.

**Entrada.** En un bloque semantics válido, states=[a,b] y task contiene solo {state:a,value:0}, con Bit codificado como cadena 0. Esto representa f(a)=0 y dom(f)={a}. Consultar a y b. Mutación real de formato: eliminar por completo el campo obligatorio semantics.task, conservando los demás campos. Para la tabla original consultar además el gate positivo en a y b.

**Oráculo.** En la tabla original f(a) está definido y vale 0; f(b) está establecido fuera de dominio. La mutación carece de un campo estructural obligatorio y es presentación inválida, no una función parcial vacía ni desconocimiento de f(b). El gate original vale 0 en a y b, pero debe conservar la diferencia entre valor cero y ausencia de dominio.

**Derivación.** La fila presente fija valor y pertenencia al dominio; b no está entre las claves. Un campo task presente con array vacío sería una función parcial válida de dominio vacío, distinto de borrar task. Un gate solo registra acreditación positiva y no recupera la razón de su cero. La pertenencia al dominio desconocida exigiría otra presentación epistemológica; la tabla cerrada original sí la decide.

### CF-005 — Factorización parcial exacta: caso positivo

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** positive.

**Fuentes:** S1:P00307-P00348. **Invariantes:** INV-10, INV-11.

**Precondiciones.** Funciones finitas explícitas; el dominio del factor se restringe a la imagen de ψ.

**Entrada.** U={a,b,c}; ψ(a)=ψ(b)=q, ψ(c)=r; dom(f)={a,b}; f(a)=f(b)=7.

**Oráculo.** FSuf se cumple. Factor único sobre im(ψ): dom(f̄)={q}, f̄(q)=7; r queda fuera de dominio. Dom(f̄∘ψ)={a,b}=dom(f).

**Derivación.** La fibra q está enteramente en dom(f) con valor constante 7. La fibra r no toca dom(f). Hay cobertura y saturación, y la composición reproduce tanto los valores como el dominio.

### CF-006 — Fibra mixta: perder el dominio fabrica respuestas

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P00307-P00348; S1:P00366-P00382. **Invariantes:** INV-03, INV-11, INV-33.

**Precondiciones.** Funciones parciales cerradas, con igualdad que incluye dominio.

**Entrada.** U={a,b}; ψ(a)=ψ(b)=q; dom(f)={a}; f(a)=0.

**Oráculo.** No existe factor exacto f̄ con f=f̄∘ψ. El dominio seguro máximo en im(ψ) es vacío. Debe conservarse f(a)=0 en el registro original; no se certifica factorizar toda f.

**Derivación.** Si f̄(q) existe, la composición está definida también en b, contradiciendo dom(f). Si no existe, pierde a. La fibra {a,b} no está contenida en dom(f), aunque los únicos valores observados sean constantes.

### CF-007 — Las marginales de una transición no acreditan DSuf

**Estado:** DESIGNED. **Alcance:** THEORY_GENERAL. **Tipo:** negative.

**Fuentes:** S1:P00469-P00525. **Invariantes:** INV-10, INV-13, INV-34.

**Precondiciones.** x e y comparten el estado reducido q y la misma acción habilitada α. Las observaciones 0,1 se conservan; los sucesores reducidos son U,V distintos. Es una obligación general de reducción dinámica; FP1 no recibe un certificado DSuf genérico ni comprime su árbol causal mediante este caso.

**Entrada.** Fila de x: {(U,0),(V,1)}. Fila de y: {(U,1),(V,0)}. Ambos son no terminales; sus conjuntos marginales de estados y observaciones coinciden.

**Oráculo.** La obligación DSuf_step falla en la fibra {x,y}; no se certifica igualdad de continuaciones reducidas de longitud 1.

**Derivación.** Los pares (U,0) y (V,1) aparecen solo en la primera fila. La igualdad de {U,V} y de {0,1} no conserva su correlación. El paso con par (U,0) es ya un testigo de traza discrepante.

### CF-008 — La actualización informacional debe conmutar con su traducción

**Estado:** DESIGNED. **Alcance:** THEORY_GENERAL. **Tipo:** negative.

**Fuentes:** S1:P00527-P00541; S1:P00535-P00536. **Invariantes:** INV-02, INV-22, INV-34.

**Precondiciones.** Caso del contrato corregido/tipado de I-06, no ejecución de una extensión arbitraria de FP1. La acción θ se conserva.

**Entrada.** I_A=I_B={0,1}; Y_A={0,1}; Y_B={*}; R_t=R_(t+1)=identidad; O(0)=O(1)=*; U_A(i,θ,y)=y; U_B(i,θ,*)=0. Tomar i=0,y=1.

**Oráculo.** La ecuación R_(t+1)(U_A(i,θ,y))=U_B(R_t(i),θ,O(y)) falla: 1≠0. No hay certificado de transporte informacional para estas tablas, aunque una reducción causal separada fuera exacta.

**Derivación.** Actualizar primero produce información 1, que R conserva. B solo ve * y su fila produce 0. Una política que actúa distinto con información 0 y 1 no se transporta mediante esa actualización sin cambiar su comportamiento.

### CF-009 — Índices funcionales cambiantes producen un ciclo espurio

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P00637-P00705; S1:P00781-P00802. **Invariantes:** INV-09, INV-12.

**Precondiciones.** Tres índices comunes I={1,2,3}; orden usual y calibración identidad.

**Entrada.** Perfiles a=(2,0,1), b=(1,2,0), c=(0,1,2). Regla incorrecta: comparar a/b solo en 1, b/c solo en 2 y c/a solo en 3.

**Oráculo.** En el producto fijo, cada par de alternativas distintas es incomparable. La supuesta cadena a>b>c>a no es una comparación válida del bloque común.

**Derivación.** Cada par tiene una coordenada favorable y otra desfavorable. Las tres desigualdades aisladas usan tres relaciones diferentes; su composición no entra en las hipótesis de transitividad del Teorema 3.1.

### CF-010 — Calibración monótona que no refleja orden

**Estado:** DESIGNED. **Alcance:** THEORY_GENERAL. **Tipo:** negative.

**Fuentes:** S1:P00637-P00657; S1:P00742-P00765. **Invariantes:** INV-12, INV-35.

**Precondiciones.** Una referencia ordinal común con valores 0 y 1 y orden usual. Es un caso general de transporte exacto de órdenes; el significado empírico de una calibración FP1 sigue siendo una premisa y no se deriva solo del orden de los raw.

**Entrada.** r(p)=0, r(q)=1; h(0)=h(1)=0. Presentar h como transporte exacto de orden.

**Oráculo.** No se acredita transporte exacto. Originalmente q domina estrictamente p; después de h son equivalentes. La monotonía de h por sí sola es insuficiente.

**Derivación.** En el destino h(0)≥h(1) es verdadero, mientras 0≥1 es falso. Se incumple la reflexión del orden requerida; el resultado reducido no puede sustituir el orden original.

### CF-011 — Unión natural espuria por pérdida de correlación

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P00883-P00979. **Invariantes:** INV-13, INV-36.

**Precondiciones.** w=κπ identifica el experimento fijo y se conserva implícitamente en ambas vistas. Query es un puerto adicional con dos valores q0,q1 distintos; cada Query determina exactamente una fila completa. A y B son puertos binarios.

**Entrada.** R={(q0,0,0),(q1,1,1)} sobre (Query,A,B). Vista L_A sobre {A}: {0,1}. Vista L_QB sobre {Query,B}: {(q0,0),(q1,1)}. La unión de esquemas cubre Query,A,B; ninguna columna es compartida entre estas dos vistas salvo el experimento w implícito.

**Oráculo.** L_A⋈L_QB={(q0,0,0),(q0,1,0),(q1,0,1),(q1,1,1)}; filas espurias={(q0,1,0),(q1,0,1)}. La descomposición no es exacta aunque cada local sea la proyección correcta y el esquema completo esté cubierto.

**Derivación.** La vista A pierde la correlación con Query y B; combinarla con L_QB forma los cuatro pares. La fibra del experimento w no es rectangular para esta separación de puertos. Afirmar que el identificador de experimento basta para recomponer filas ignoraría que existen dos consultas distintas dentro de ese mismo experimento.

### CF-012 — Recursos: identidad de demanda y presupuesto por instante

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** mixed.

**Fuentes:** S1:P01017-P01060. **Invariantes:** INV-14.

**Precondiciones.** Un fondo de agua ρ medido en litros; capacidad instantánea 10 L; demandas no negativas.

**Entrada.** A: demandas distintas d1=6 L y d2=6 L en t=1. B: dos vistas repiten la misma demanda d1=6 L en t=1. C: d1 exige 6 L en t=1 y 6 L en t=2 con presupuesto instantáneo 10 L.

**Oráculo.** A falla: uso 12>10. B cumple: uso 6≤10 tras identificar d1 una sola vez. C cumple en ambos instantes: usos 6 y 6; no se impone 12≤10.

**Derivación.** La suma es sobre identidades distintas del mismo fondo y mismo instante. La igualdad de cantidades no identifica demandas; la repetición de una identidad tampoco la duplica. Sumar tiempos convertiría el límite instantáneo en un presupuesto acumulado distinto.

### CF-013 — Traducir antes de intersectar robustez

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:Definición 5.4; S1:Contraejemplo 5.2. **Invariantes:** INV-16, INV-17.

**Precondiciones.** Receta att, una política, dos escenarios y una hoja por escenario. La identificación nativa→común se declara legítima mediante significados no vacíos iguales; no se usa conservación.

**Entrada.** H=1; trazas nativas (o,a) y (o,b), a≠b; T(o)=o_c, T(a)=T(b)=c; o_c≠c. Logros nativos: {a} y {b}.

**Oráculo.** Logro robusto común={c}; CAG robusto común={o_c,c}. La ruta que primero intersecta los logros nativos devuelve erróneamente ∅ como logro robusto.

**Derivación.** T[{a}]∩T[{b}]={c}∩{c}={c}, mientras T[{a}∩{b}]=T[∅]=∅. La legitimidad semántica de T es una premisa explícita; la conveniencia de obtener c no la prueba.

### CF-014 — CAG: cardinalidad, inclusión y origen

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** mixed.

**Fuentes:** S1:Proposición 5.3; S1:Teorema 5.6; S1:P01379-P01409. **Invariantes:** INV-18, INV-19.

**Precondiciones.** Mismo marco común, origen o y receta att. Todas las identidades indicadas son distintas.

**Entrada.** A: CAGp={o,a,b}, CAGq={o,c}, realizados por trazas (o,a,b) y (o,c,c). B: única traza (o,a), H=1.

**Oráculo.** A: |CAGp|=3>|CAGq|=2, pero ninguno incluye al otro. B: Ach_att={a}, CAG={o,a}; o pertenece estructuralmente al CAG pero no tiene testigo de logro futuro.

**Derivación.** c falta en p y a falta en q, por lo que la cardinalidad no decide inclusión. En B el único tiempo positivo contiene a; añadir el singleton de origen no inventa una aparición en tiempo positivo.

### CF-015 — Alcance, mantenimiento, acumulación y coexistencia

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** mixed.

**Fuentes:** S1:Definición 5.5; S1:Teorema 5.1; S1:Definición 5.9. **Invariantes:** INV-16, INV-38.

**Precondiciones.** Identidades como conjuntos de componentes; conservación por inclusión; traza común completa; una política y un escenario.

**Entrada.** A: H=5, traza (∅,{a},{a,b},{b},{b,c},{b,c}). B: H=2, traza (o,u,v), u≠v; demandas de alcance D={u,v}.

**Oráculo.** A: Ach_att={{a},{a,b},{b},{b,c}}; Ach_hold,1={{a},{b},{b,c}}; Ach_acc={{a},{a,b}}; Ach_hold,0=Ach_att. B: la política pertenece a Joint_att(D), pero no hay instante que presente simultáneamente las identidades u y v.

**Derivación.** En A falla conservar {a,b} al pasar a {b}; ello bloquea acumulación posterior pero no borra los logros previos. {b,c} tiene ventana en t=4,5. En B los testigos de u y v son t=1 y t=2: exigir un instante común es otra consulta.

### CF-016 — Daño intermedio aunque coincida el endpoint

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:Entrega 6, reloj y registro de bienestar; S1:Entrega 7, monitor histórico. **Invariantes:** INV-20, INV-23.

**Precondiciones.** Un portador existente en t=0,1,2; una dimensión binaria completamente medida. Tarea Φ=1 si w(t)=1 en los tres tiempos.

**Entrada.** e_good: w=(1,1,1); e_dip: w=(1,0,1). Estados terminales observados y valores de bienestar terminales iguales.

**Oráculo.** Φ(e_good)=1 y Φ(e_dip)=0. Bienestar histórico good domina estrictamente dip. La proyección al endpoint no es suficiente para esta tarea.

**Derivación.** La condición universal temporal falla en t=1 de dip. La fibra del endpoint contiene dos veredictos; por constancia en fibras no puede existir factor de la tarea a través de ese endpoint.

### CF-017 — Reloj, existencia y medición no se rellenan con cero

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P01543-P01586; S1:P01657-P01674. **Invariantes:** INV-04, INV-20, INV-31.

**Precondiciones.** Comparación conservadora FP1 exige reloj, soporte, índices y medición común completa.

**Entrada.** Reloj {0,1}, portador l, dimensión j. A: l existe en ambos tiempos y w=(0,0). B: l existe solo en t=0, w(l,0,j)=0. C: l existe en ambos tiempos, índices para ambos, dom(w) solo {(l,0,j)}.

**Oráculo.** A/B no pertenece al bloque de soportes comunes; A/C no pertenece al bloque de medición completa. En B (l,1) está fuera del soporte; en C (l,1,j) existe y es aplicable pero no está medido. Ninguno es el valor cero de A.

**Derivación.** Los dominios e índices forman parte del registro. Rellenar con cero convertiría las tres historias en (0,0), identificando ausencia de portador, ausencia de medición y bienestar definido. FP1 no define una regla poblacional alternativa para esos cambios.

### CF-018 — Una sola biyección para toda la trayectoria

**Estado:** DESIGNED. **Alcance:** THEORY_GENERAL. **Tipo:** negative.

**Fuentes:** S1:P01761-P01833. **Invariantes:** INV-39.

**Precondiciones.** Regla anónima explícita de trayectorias completas; dos poblaciones de dos portadores, dos tiempos y una dimensión binaria.

**Entrada.** A: a1=(1,0), a2=(0,1). B: b1=(1,1), b2=(0,0).

**Oráculo.** A y B son incomparables bajo la regla anónima. En cada instante sus multiconjuntos son {0,1}, pero eso no acredita equivalencia histórica.

**Derivación.** A no domina B porque ningún portador de A domina (1,1). B no domina A porque ambas trayectorias de A necesitarían la única trayectoria (1,1) de B; no existe biyección. Cambiar el emparejamiento entre tiempos violaría la regla.

### CF-019 — Un matching negativo necesita todas las aristas decididas

**Estado:** DESIGNED. **Alcance:** THEORY_GENERAL. **Tipo:** mixed.

**Fuentes:** S1:P01835-P01868. **Invariantes:** INV-04, INV-40.

**Precondiciones.** El caso comprueba el contrato general de matching; FP1 conserva portadores identificados y no añade este comparador automáticamente.

**Entrada.** A: lados L={b1,b2}, R={a1,a2}; aristas verdaderas conocidas {(b1,a1)}; (b2,a2) aún no evaluada; las otras dos falsas. B: resolver (b2,a2)=verdadera. C: resolverla=falsa.

**Oráculo.** A: no se acredita imposibilidad ni déficit de Hall usando la arista desconocida como ausente. B: matching perfecto {(b1,a1),(b2,a2)}. C: certificado negativo X={b2}, N(X)=∅ sobre el grafo completo.

**Derivación.** En A quedan dos completaciones compatibles con respuestas opuestas. B tiene una biyección cubierta. En C |N(X)|=0<1=|X| y se conoce exhaustivamente que b2 no tiene vecinos. Si el perfil exige tabla cerrada, A sería una solicitud todavía no concluida o una entrada incompleta, nunca un negativo matemático.

### CF-020 — Una política no puede leer el estado oculto

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:Entrega 7, políticas e información; S1:P02526-P02528; S1:P03568. **Invariantes:** INV-02, INV-22, INV-42.

**Precondiciones.** H=2; tras la primera acción hay estados x_r y x_s con la misma observación y la misma información legítima ι*. Las acciones α y β están localmente habilitadas en ambos. Las ramas tienen entradas exógenas u_r≠u_s, pero observación y actualización informacional iguales; el mantenimiento usa u_hold. Los escenarios son las palabras (u_r,u_hold) y (u_s,u_hold), con una hoja por palabra. Así la ilegalidad de control se prueba sin introducir además varias hojas por escenario.

**Entrada.** Pretendida política en t=1: elegir α si estado=x_r y β si estado=x_s, con α≠β. Se presenta como dos filas para la misma clave (1,ι*).

**Oráculo.** La presentación no define una función π_1(ι*) y no es una política legítima de la familia. La alternativa válida que elige α en ambos estados sí puede incluirse. El lector posterior puede distinguir r/s sin autorizar esa distinción al controlador.

**Derivación.** Un argumento de función no puede tener dos valores. Indexar la tabla por x oculto cambiaría la información admisible y el problema de control. La omnisciencia del evaluador no forma parte de ι*.

### CF-021 — La garantía no nace de una familia vacía

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P00203-P00211; S1:Definición 5.6. **Invariantes:** INV-07.

**Precondiciones.** Se solicita una afirmación robusta relativa a escenarios declarados.

**Entrada.** A: Ξ=∅. B: Ξ={r,s}; Runs(r)={e_r}, Runs(s)=∅; Ach(e_r)={u}.

**Oráculo.** En A no se cumple la no vaciedad de escenarios; en B falla la no vaciedad por escenario. Ninguna variante acredita que una política garantice u ni todas las identidades. FP1 tampoco puede certificar su biyección escenario-hoja.

**Derivación.** La definición robusta incluye las guardas separadas. La verdad lógica de un universal vacío no suministra una realización; intersectar solo las fibras no vacías eliminaría el escenario s declarado.

### CF-022 — Límites de la ruta fuerte: escenario único y horizonte completo

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P03307-P03323; S1:Teorema 10.2. **Invariantes:** INV-30.

**Precondiciones.** Se pide el certificado de ensamblaje FP1 con H=2 y Ξ={r,s}.

**Entrada.** A: tres hojas e_r1,e_r2,e_s, con asignación de escenario r,r,s. B: dos ramas, una termina en t=1 y otra en t=2.

**Oráculo.** A no admite la biyección exigida entre dos escenarios y tres hojas. B incumple realización hasta H. No se emite el certificado fuerte FP1; estos datos no se declaran físicamente imposibles ni se niega que otra ruta teórica pueda tratarlos.

**Derivación.** En A dos hojas comparten r y |F|=3≠2=|Ξ|. En B rellenar artificialmente el último estado hasta t=2 cambiaría la traza y podría fabricar un hold,1. El perfil es una restricción explícita de implementación, no una modificación del dominio de la teoría general.

### CF-023 — Igual veredicto no prueba fidelidad de significado

**Estado:** DESIGNED. **Alcance:** THEORY_GENERAL. **Tipo:** mixed.

**Fuentes:** S1:P02383-P02450. **Invariantes:** INV-24, INV-41.

**Precondiciones.** Universo semántico S={u,v}; tarea definida Φ(u)=Φ(v)=1; referencia de origen J_A(a)={u,v}. Los adaptadores multivaluados son una extensión teórica; el protocolo mínimo FP1 no incluye un adaptador arbitrario como entrada.

**Entrada.** A: Q(a)={b_u}, J_B(b_u)={u}. B: Q(a)={b_u,b_v}, J_B(b_u)={u}, J_B(b_v)={v}. C: como B pero J_B no definido en b_v.

**Oráculo.** A no es fiel, aunque todos los veredictos visibles sean 1. B es fiel para a. C no acredita fidelidad, porque una interpretación de la fibra requerida está fuera de dominio.

**Derivación.** A tiene unión de significados {u}≠{u,v}. B tiene unión {u}∪{v}={u,v}, no vacía, con cobertura completa. En C no se puede formar la unión declarada con todas sus interpretaciones; descartar b_v repetiría la pérdida de significado de A.

### CF-024 — Certificados decisivos comprobados, no declarados

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** mixed.

**Fuentes:** S1:P02452-P02477; S1:P02517-P02542. **Invariantes:** INV-07, INV-24.

**Precondiciones.** Consulta h con dos hojas e_u,e_v; J(e_u)={u}, J(e_v)={v}; por tanto Sem(h)={u,v}. Φ(u)=1, Φ(v)=0; lector exacto de referencias y tarea.

**Entrada.** Certificado c1: A={u}, valor 1. c2: A={u,v}, valor 1. c3: A=∅, valor 1. Control positivo: consulta de hoja e_u, A={u}, valor 1.

**Oráculo.** c1 falla inclusión Sem(h)⊆A; c2 falla constancia Φ[A]={1}; c3 falla inclusión y no vaciedad relevante. Ninguno autoriza V(h)=1. El control positivo sí autoriza V(e_u)=1.

**Derivación.** Cada fallo se comprueba contra tablas: v falta en c1; Φ(v)=0 en c2; Sem(h) no está contenido en vacío en c3. Para e_u, Sem={u}⊆A⊆dom(Φ) y Φ[A]={1}. Dos certificados opuestos correctos son imposibles con Sem no vacía.

### CF-025 — Raíz indeterminada con PVS definida

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** positive.

**Fuentes:** S1:P03641-P03656; S1:P02606-P02621. **Invariantes:** INV-26, INV-31.

**Precondiciones.** Instancia B y protocolo exacto, restringiendo la consulta a πa.

**Entrada.** Sem(h0)={({a},r),({a},s)}; Φ de esos dos puntos=1,0; masas foliares 3/4,1/4.

**Oráculo.** V(h0) está fuera de su dominio decisivo; ambas hojas sí están definidas. VProb=(3/4,1/4,0) y PVS=3/4. La indeterminación de la raíz no invalida la instancia ni vuelve indefinidas todas las componentes.

**Derivación.** Φ[Sem(h0)]={0,1} carece de valor único. La PVS se construye con la partición de hojas completas, no con el veredicto de la raíz. Ambas hojas están decididas, de modo que la masa indeterminada foliar es cero.

### CF-026 — Masa indeterminada positiva no se renormaliza

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P02657-P02716; S1:P02739-P02751. **Invariantes:** INV-25, INV-26, INV-44.

**Precondiciones.** Dos hojas e1,e2 con masas legítimas 3/4,1/4. J(e1)={u}; J(e2)={v,w}; tarea total Φ(u)=Φ(v)=1 y Φ(w)=0; lector exacto.

**Entrada.** V(e1)=1; e2 queda indeterminada por semántica mixta. Solicitar VProb, PVS y una eventual cota de extensiones.

**Oráculo.** VProb=(3/4,0,1/4). PVS está fuera de dominio. No devolver 3/4 como PVS ni 1 por renormalizar las hojas decididas. El intervalo [3/4,1] solo es cota condicional de extensiones admisibles si estas existen; aquí la semántica fija de e2 no admite un veredicto universal único.

**Derivación.** La masa 1/4 de e2 pertenece íntegra a la tercera región. No hay una ley dada entre v y w que permita dividirla. Cambiar la referencia para decidir e2 alteraría la instancia; la desigualdad de cotas no demuestra que se alcancen sus extremos.

### CF-027 — Hojas nulas: PVS=1 no implica garantía universal

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** mixed.

**Fuentes:** S1:P02679-P02716; S1:P03501. **Invariantes:** INV-22, INV-26, INV-27.

**Precondiciones.** Dos hojas causales e1,e0, con pesos 1 y 0. No se eliminan ramas por su masa.

**Entrada.** A: J(e1)={u}, Φ(u)=1; J(e0)={v}, Φ(v)=0. B: mantener e1 y reemplazar J(e0) por {v,w} con Φ(v)=0, Φ(w)=1. C: mantener e1 y dejar J fuera de dominio en e0.

**Oráculo.** A: VProb=(1,0,0), PVS=1, y la garantía universal es falsa por e0. B: V(e0) indeterminado, VProb=(1,0,0), PVS=1; tampoco hay garantía universal acreditada. C: Sem(raíz) fuera de dominio por completación sin referencia; V(e0) fuera de dominio; PVS=1 todavía, si la evaluación parcial y ley están bien formadas. Las dos hojas permanecen en A/B/C.

**Derivación.** Una región puede ser no vacía y tener masa cero. La condición M?=0 no exige D_V=F. El cuantificador universal y la cobertura semántica sí inspeccionan la hoja nula. C separa falta de referencia en un dominio parcial declarado de una tabla mal formada.

### CF-028 — Una fila probabilística inválida no se sanea por masa cero

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P02623-P02655. **Invariantes:** INV-43.

**Precondiciones.** Árbol H=2: raíz→n+ con peso 1 y n0 con peso 0. n+ tiene una hoja con condicional 1; n0 tiene dos hojas l01,l02.

**Entrada.** Fila suministrada en n0: q(l01|n0)=1 y q(l02|n0)=1.

**Oráculo.** La ley presentada es inválida: la fila en n0 suma 2. No se acepta porque sus masas de hojas serían multiplicadas por cero. Reemplazarla por (1/2,1/2) da una fila válida y masas 0,0.

**Derivación.** La norma de fila exige distribución sobre exactamente todos los hijos. Una eventual autorización teórica a omitir filas en nodos nulos no convierte una fila aportada incorrecta en válida; FP1 fija sus obligaciones de completitud por separado.

### CF-029 — Una ley requiere datos; las masas se suman en una partición

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** mixed.

**Fuentes:** S1:P02623-P02677; S1:P02782-P02805; S1:P01111-P01122. **Invariantes:** INV-25, INV-37, INV-44, INV-45.

**Precondiciones.** H=2; raíz h, nodo n en t=1, dos hojas e1,e2 en t=2; únicos veredictos foliares 1 y 0 respectivamente. Las variantes A/B verifican operaciones FP1; C ilustra exclusivamente el límite general del transporte de leyes, fuera de sus entradas obligatorias.

**Entrada.** A: solo árbol y veredictos, sin ley. B: ley masa(e1)=1/3, masa(e2)=2/3; masa(h)=masa(n)=1. C: intentar mapear e1 y e2 a una única hoja z; masa imagen(z)=1.

**Oráculo.** A no determina PVS; leyes válidas (1/4,3/4) y (3/4,1/4) producirían PVS distintas. B: masas foliares suman 1 y PVS=1/3; sumar h,n,e1,e2 daría 3 y es incorrecto. C: la masa se transporta a 1, pero no existe V′(z) que conserve a la vez los valores 1 y 0; no se acredita conservación de PVS por ese mapa.

**Derivación.** Posibilidades no seleccionan una distribución. Los eventos de prefijos contienen hojas y se solapan. El transporte de evaluación parcial exige constancia de veredicto, incluido dominio, por cada fibra; la fibra {e1,e2} de C incumple esa constancia.

### CF-030 — Refinar evidencia no puede cambiar tarea, realización ni ley

**Estado:** DESIGNED. **Alcance:** THEORY_GENERAL. **Tipo:** mixed.

**Fuentes:** S1:P02753-P02780. **Invariantes:** INV-45.

**Precondiciones.** Misma tarea total Φ(u)=Φ(v)=1, referencias J(e1)={u}, J(e2)={v}, mismas hojas y masas 1/2,1/2. Los lectores son protocolos legítimos parciales de la teoría general.

**Entrada.** V1 decide solo e1 con valor 1; V2 decide e1,e2 con valor 1. Mutación W: decide ambas, pero asigna 0 a e1. Mutación de experimento: cambiar ley o tarea bajo etiqueta de refinamiento.

**Oráculo.** V1: masas (1/2,0,1/2), PVS indefinida. V2: (1,0,0), PVS=1; es refinamiento. W no es refinamiento y además contradice la tarea dada. Cambiar ley o tarea tampoco entra en el teorema de refinamiento.

**Derivación.** El dominio crece y el valor antiguo se conserva únicamente en V2. La masa positiva aumenta 1/2 y la indeterminada disminuye 1/2. Los protocolos parciales ilustran la teoría general; FP1 con lector exacto ya decidiría ambas hojas desde estas referencias.

### CF-031 — Factibilidad y comparación parcial sin cortocircuitos falsos

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** mixed.

**Fuentes:** S1:P02883-P02946. **Invariantes:** INV-04, INV-05, INV-09, INV-31.

**Precondiciones.** Dos restricciones presupuestarias H1,H2 derivadas de sumas de recursos tabuladas, no booleans hard admitidos como entrada. Tres políticas {a,b,c} y un árbol H=0 por política; cada raíz es su única hoja y los recursos tienen una demanda pertinente cada uno, unidad común y cota 1.

**Entrada.** Variante hard: en recurso1 los valores de demanda de las raíces a,b,c son 0,2,0; en recurso2 son 0, fuera de dominio, fuera de dominio. De aquí se derivan H1(a)=H2(a)=1; H1(b)=0 y H2(b) indefinida; H1(c)=1 y H2(c) indefinida. Variante independiente de comparación: usar B y omitir solo la medición w de l1 en el nodo regular de πah en t=1, manteniendo su aplicabilidad; comparar πh⪰πah. PVSπh=3/4<PVSπah=1, pero la valoración completa de bienestar de πah está fuera de dominio.

**Oráculo.** En la variante hard: factibles={a}; refutadas={b}; sin acreditación completa y sin refutación={c}. Conservar en b el diagnóstico de H2 ausente además del fallo de H1. En la variante de comparación, πh⪰πah queda fuera de dominio por la medición requerida ausente, no simplemente falsa por la PVS desfavorable u otro criterio. La PVSπah=1 sigue definida: la ausencia de medición no borra sus referencias semánticas tabuladas.

**Derivación.** La refutación de una restricción basta para clasificar b como incumplimiento, pero no elimina otros diagnósticos. La relación integrada parcial está definida solo cuando todas sus valoraciones y pares de comparación lo están. En la variante B modificada, el orden racional de PVS es conocido, pero no existe el perfil de bienestar completo requerido de πah. Un cortocircuito booleano no puede ampliar el dominio de la relación ni la falta de una medición eliminar objetos independientes.

### CF-032 — La frontera robusta no es la intersección de fronteras

**Estado:** DESIGNED. **Alcance:** THEORY_GENERAL. **Tipo:** negative.

**Fuentes:** S1:P03049-P03073. **Invariantes:** INV-48.

**Precondiciones.** Bloque común C={a,b}; ambas alternativas factibles; dos preórdenes completos definidos.

**Entrada.** ω1: a≻b. ω2: b≻a. Cada relación incluye las dos parejas reflexivas.

**Oráculo.** Fr_ω1(C)={a}; Fr_ω2(C)={b}; intersección de fronteras=∅. Relación robusta=intersección de relaciones={(a,a),(b,b)}; su frontera={a,b}.

**Derivación.** No hay dominancia débil unánime de ninguna alternativa sobre la otra. Por tanto ambas son maximales del orden robusto. Intersectar conjuntos de maximales realizaría una operación diferente y eliminaría dos soluciones robustamente maximales.

### CF-033 — Cobertura de frontera y ausencia de selector por defecto

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** mixed.

**Fuentes:** S1:P02961-P03012; S1:P03097-P03110. **Invariantes:** INV-28.

**Precondiciones.** Proyección de una instancia FP1 al bloque de cuatro criterios: todas las alternativas son factibles; CAG={o,g}, perfil funcional=(1) y perfil de bienestar=(1) son los mismos en todas; solo varía PVS. Esos perfiles constantes comparten índice, soporte y ámbito. El campo obligatorio selection es {mode:none} (literal JSON: {"mode":"none"}).

**Entrada.** A: objetivo Π={a,b,c}, PVS(a)=1/4, PVS(b)=1/2, PVS(c)=3/4; el resultado candidato cubre solo C={a,b}. B: objetivo declarado Π=C={a,b}, con las mismas PVS. C: Π=C={a,b}, PVS(a)=PVS(b)=1/2. En A/B/C los otros tres criterios permanecen constantes y selection.mode=none.

**Oráculo.** A: Fr(C)={b}, mientras Fr(Π)={c}; el resultado limitado a C no puede afirmar frontera exhaustiva de Π. B: Fr(Π)={b}, exhaustiva de esa familia bajo las demás guardas fuertes; aun siendo singleton, mode=none no selecciona. C: Fr(Π)={a,b}; tampoco se emite elección única.

**Derivación.** Los tres criterios constantes dan dominancia mutua en cada par; la conjunción de cuatro criterios se reduce aquí al orden de PVS. En A, 3/4>1/2 hace que el omitido c domine a b. En C igualdad de los cuatro criterios implica equivalencia. El modo none es un dato explícito obligatorio y prohíbe elegir por nombre, posición de fila o incluso unicidad de la frontera.

### CF-034 — La simetría puede impedir selección equivariante

**Estado:** DESIGNED. **Alcance:** THEORY_GENERAL. **Tipo:** mixed.

**Fuentes:** S1:P03111-P03154. **Invariantes:** INV-49.

**Precondiciones.** Datos del problema y frontera invariantes bajo G={id,swap}; swap intercambia a y b. Se exige explícitamente equivarianza.

**Entrada.** A: Fr={a,b} y el estabilizador contiene swap. B: Fr={a,b,c}, swap(c)=c y los demás datos siguen invariantes.

**Oráculo.** A: no existe selector determinista equivariante definido en este problema. B: seleccionar c satisface la condición de punto fijo del estabilizador para este problema; para una familia se requieren además las hipótesis del Teorema 9.9.

**Derivación.** En A s(K)=swap(s(K)) exigiría que a=b, lo cual es falso. Elegir por el nombre rompe la simetría. En B c permanece fijo y es maximal. Una prioridad externa que distinguiera a/b cambiaría los datos y el estabilizador; no puede introducirse tácitamente.

### CF-035 — Agotar recursos de cómputo no demuestra imposibilidad

**Estado:** DESIGNED. **Alcance:** FP1_FINITE_EXACT. **Tipo:** negative.

**Fuentes:** S1:P03350-P03395; S1:P03534-P03550. **Invariantes:** INV-29, INV-31, INV-32.

**Precondiciones.** Caso de un futuro evaluador con límite externo de trabajo; no se fija algoritmo ni unidad de costo normativa en F1.

**Entrada.** A: instancia B, pero detener la evaluación después de construir la hoja regular de πa y antes de revisar su rama estrés; se permite solo un paso de inspección foliar. B: grafo de construcción propuesto CAG→Φ y Φ→filtrar futuros→CAG.

**Oráculo.** A: cómputo no concluido, cobertura insuficiente y ningún certificado de PVS ni frontera exhaustiva. No afirmar imposibilidad, incumplimiento, PVS=1 ni ausencia de hojas estrés. B: el grafo contiene un ciclo y no es un DAG de justificación; no se certifica ensamblaje mediante él.

**Derivación.** A inspeccionó un éxito de masa 3/4 pero no estableció la partición completa; la rama faltante de B existe y falla con masa 1/4. La terminación matemática sin límite arbitrario no garantiza completar cualquier presupuesto de máquina. En B CAG se necesita para definir Φ antes del filtro que pretende construir ese mismo CAG. La construcción válida genera los futuros y CAG antes de evaluar la tarea; los resultados adversos no se borran.

### CF-036 — Lector exacto sin admisión canónica: contraejemplo y reparación de 8.6

**Estado:** DESIGNED. **Alcance:** THEORY_GENERAL. **Tipo:** counterexample.

**Fuentes:** S1:P02518-P02528; S1:P02544-P02572; S1:P02610-P02621; F1-ED-01 en theory/reviews/REVIEW_VI_VII.md; Specification 04 §4. **Invariantes:** INV-05, INV-24, INV-41.

**Precondiciones.** Se interpreta literalmente el Teorema 8.6 sin añadir una clausura protocolaria no enunciada. La lectura exacta y la admisión de certificados son capacidades separadas. El protocolo general P admite el lector exacto, pero ningún certificado decisivo; no se lo presenta como el protocolo FP1.

**Entrada.** Consulta h con dos completaciones e_p,e_q; J(e_p)={p}, J(e_q)={q}, p≠q. Universo y dominio de tarea {p,q}; Φ(p)=Φ(q)=0. Sem(h)={p,q}. La vía completa exige Sem(h)={S_full(h)}, que aquí no se cumple. Control reparado: P+ admite, para cada consulta de D*, el certificado canónico A=Sem(h) con el único valor v de Φ[Sem(h)], además del lector exacto fundamentado.

**Oráculo.** Para P, h∈D* porque Sem(h) es no vacía, está dentro de DΦ y Φ[Sem(h)]={0}; sin embargo h∉D_V: no hay certificado admitido ni semántica singleton para la vía completa. Por ello la lectura literal DV=D* es falsa bajo solo la hipótesis del lector. Para P+, el certificado A={p,q}, v=0 está admitido y satisface las guardas, por lo que V(h)=0. FP1_EXACT_ENUM_V1 satisface precisamente esta cláusula adicional al construir y admitir certificados canónicos de valor 0 y de valor 1.

**Derivación.** La inclusión D_V⊆D* se conserva por corrección de toda ruta admitida. La recíproca necesita convertir una lectura en evidencia que el protocolo permita usar: existencia matemática del conjunto A no implica admisión. En P ninguna ruta permite emitir un valor, aun cuando se conoce la constancia de Φ. En P+ la clausura provee la admisión faltante; ∅≠{p,q}⊆{p,q}⊆DΦ y Φ[{p,q}]={0} prueban la corrección. La reparación explícita F1-ED-01 fortalece la hipótesis del teorema; no modifica silenciosamente S1. La equivalencia en FP1 queda condicionada a protocolo exacto, tablas válidas y todas las guardas de esa ruta.

## Criterio para su futura ejecución

Un caso positivo requiere los valores y testigos indicados, además de cualquier guarda exigida por el contrato integrado. Un caso negativo exige señalar la obligación concreta que falla y conservar resultados independientes que sigan definidos. Un diagnóstico genérico no sustituye la razón enumerada en el oráculo. No basta que un evaluador devuelva siempre una excepción: CF-001 y los controles positivos exigen construir valores correctos.

Los casos tienen datos racionales, conjuntos finitos e igualdades exactas; no requieren tolerancias numéricas. No se aceptan como ejecución de estos casos una simulación aleatoria, la inspección de una sola rama o la mera validación sintáctica del fixture. El registro futuro deberá indicar cobertura total o parcial, versión de Specification/Kernel y evidencia trazable a cada CF. Los casos de teoría general requieren un objetivo de implementación separado antes de convertirse en promesas de F2.

La integridad mecánica de este documento o su índice, y el recálculo auxiliar de números, no equivalen a ejecutar conformidad contra una implementación. El diseño admite revisión adversarial de cada derivación y queda sujeto a la auditoría separada de F1.
