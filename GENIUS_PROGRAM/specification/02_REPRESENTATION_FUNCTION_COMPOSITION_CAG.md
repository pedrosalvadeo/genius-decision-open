# Representación, funcionalidad, composición y CAG

Specification candidata 1.0.0. Perfil operativo: `FP1_FINITE_EXACT`. Fuente: S1 P00001–P01532; las enmiendas explícitas figuran en `../theory/AMENDMENTS.md` y la revisión deductiva en `../theory/reviews/REVIEW_0_III.md`. Los nombres matemáticos de este documento no crean un segundo formato de intercambio: la serialización y los códigos de estado son los fijados por el contrato maestro de F1.

## 1. Contrato común de objetos finitos

Un conjunto finito se presenta mediante todas sus identidades; igualdad de identidades es exacta. Un producto utiliza claves tipadas, con un valor por clave. Una función parcial `f:A ⇀ B` se presenta mediante A, B, el subconjunto completo `D_f ⊆ A` y exactamente una fila `(a,f(a))` por `a∈D_f`. En el formato de intercambio, las claves presentes de una tabla cerrada **son** D_f; no hace falta otro campo de dominio que las duplique. Se rechazan claves repetidas, valores fuera del codominio y cualquier discrepancia con un dominio adicional expresamente declarado. Ausencia de un argumento en `D_f` significa pertenencia conocida al complemento; ausencia de la tabla o de una referencia obligatoria significa presentación inválida. Una tabla abierta o pendiente no es una función de este perfil. Los codominios numéricos pueden ser Q aunque sean infinitos: su representación y sus operaciones son exactas y cada tabla tiene soporte finito.

La especificación conserva por separado: valor, pertenencia al dominio, conocimiento disponible, validez de presentación, evidencia, estado de cómputo y alcance de cobertura. La pertenencia queda decidida para las tablas cerradas del perfil, pero la verdad empírica de sus premisas no se vuelve decidida por ello. Un consumidor no transforma un fallo de evidencia o cómputo en valor cero ni en conjunto vacío. Puede retener componentes ya obtenidas; no fabrica el registro conjunto que necesita todas sus componentes.

Los números calculados son racionales exactos. Los identificadores y categorías finitas se comparan con relaciones completas tabuladas. Un preorden se valida sobre todo el universo declarado: `(a,a)` para cada elemento y `(a,b),(b,c) ⇒ (a,c)` para cada triple. Una equivalencia requiere, además, simetría. Los números naturales H y L se presentan exactamente. No se admiten comparadores ejecutables arbitrarios ni tolerancias implícitas.

Cada resultado referencia su marco, modelo, contexto, inicialización, familia de políticas o política seleccionada, escenarios, horizonte, receta y versiones de las tablas que consumió, según corresponda. Cada testigo de ocurrencia conserva política, escenario, ejecución, ramas y tiempos. Las etiquetas de procedencia no se convierten en observables de un resumen salvo que este lo declare.

### Operaciones básicas

| Operación | Entrada y dominio | Salida y construcción | Obligación / diagnóstico distinguible |
|---|---|---|---|
| Composición parcial | `f:A⇀B`, `g:B⇀C`, presentaciones válidas | Dominio `{a∈D_f:f(a)∈D_g}` y valor `g(f(a))` | No evaluar g antes de comprobar ambos dominios; informar cuál falla |
| Registro conjunto | Familia finita declarada `(f_i)` sobre A | Dominio `⋂D_fi`, tupla por índice común | Conservar componentes ausentes; familia vacía produce tupla vacía en A |
| Registro de dominio y valor | f válida, a∈A | `(definido,f(a))` o `(fuera_de_dominio,⊥_f)` | `⊥_f` no es número ni tiene orden de calidad |
| Certificación positiva | Predicado parcial `P:A⇀{0,1}` | Gate 1 solo si a∈D_P y P(a)=1; gate 0 en los otros dos casos | Retener diagnóstico P=0 o fuera de dominio; el gate no los identifica |
| Comparación por preorden | Ambos valores definidos, mismo bloque y relación validada | Dominancia, equivalencia, estricta o incomparabilidad | Fuera de bloque/dominio no significa incomparabilidad |

Estas operaciones son totales sobre sus presentaciones válidas cuando devuelven registros de diagnóstico; los valores matemáticos internos conservan su parcialidad. Finitud garantiza terminación de las enumeraciones, sin afirmar eficiencia para tamaños arbitrarios.

## 2. M0: representación y suficiencia

### 2.1 Estado, información y organización

Una historia admisible `h∈H_t` tiene estado `Γ_X,t^hist(h)∈X_t`, con `Γ_X,t^hist` total sobre H_t. La organización `Γ_Σ,t:X_t⇀S_t` puede ser parcial. La información `ι_t∈I_t` es otro objeto; una política solo recibe `(t,ι_t)` en su tabla. Ni la equivalencia organizacional ni la igualdad de un perfil funcional acreditan suficiencia causal.

H_t, sus mapas y las entradas externas relevantes son datos declarados. Cuando se afirma suficiencia, se declara la familia de consultas o la relación dinámica concreta; el validador comprueba esa afirmación sobre la presentación, no la adecuación de H_t al mundo.

### 2.2 Descenso exacto de una consulta

**Entrada:** conjuntos A,Q,B finitos, `ψ:A⇀Q` y `f:A⇀B` válidos. **Salida:** veredicto de `FSuf(ψ;f)`, factor canónico si pasa y testigos exhaustivos de fallos.

Algoritmo matemático:

1. Formar `uncovered = D_f \ D_ψ`.
2. Para cada `q∈im ψ`, formar `F_q={a∈D_ψ:ψ(a)=q}`. Estas fibras son no vacías.
3. Registrar si F_q mezcla miembros de D_f y de su complemento. Registrar pares definidos de F_q con valores distintos.
4. FSuf se acredita exactamente cuando los tres registros están vacíos. Construir `D_fbar=ψ[D_f]` y `fbar(q)=f(a)` para cualquier a∈F_q.
5. Si falla FSuf, puede construirse separadamente `f_safe` sobre las fibras totalmente incluidas en D_f y de valor único. Este resultado no lleva el veredicto FSuf de f completa. Conservar fibras rechazadas y argumentos definidos no cubiertos.

**Propiedad:** el factor canónico satisface igualdad de dominio y valor `f=fbar∘ψ`, y es único al restringir su dominio a `im ψ` (Teorema 2.1). El factor seguro tiene el máximo dominio seguro de fibras enteras (Proposición 2.2); no recupera argumentos fuera de D_ψ.

Para una familia finita de consultas `(f_j)` sobre A, el cociente mínimo agrupa por el vector completo de registros de dominio y valor `(registro_fj(a))_j`. La proyección `q_T:A→A/~_T` es total. Todas las consultas descienden; cualquier otra representación **total** suficiente factoriza esa proyección por un mapa único sobre su imagen (Teorema 2.3). Si no hay consultas, existe una sola clase cuando A no es vacío y ninguna si A es vacío. La construcción exige conocer las tablas de las consultas; no permite obtener respuestas desconocidas gratuitamente.

### 2.3 Suficiencia dinámica de un paso

**Alcance:** esta sección explicita y revisa el contrato matemático general de S1. La versión de intercambio FP1 no recibe dos sistemas ni mapas dinámicos ψ/o; por tanto, no define una operación obligatoria de validación o construcción DSuf. Incorporarla requeriría una extensión versionada del formato y su conformidad. La única reducción suministrada por el formato actual es la funcional de §2.2/§3.1, que no sustituye los estados causales.

**Entrada:** sistema finito `S=(S,A,Y,E,B,T)`, con `E:S→P(A)` total, `B(s,a)⊆S×Y` explícito y no vacío para cada `a∈E(s)`, y `E(s)=∅ ⇔ s∈T`. Mapas totales `ψ:S→Q`, `o:Y→Z`.

**Comprobación:** para todo s,t con ψ(s)=ψ(t), verificar E(s)=E(t), igualdad de condición terminal y, para cada a habilitada, igualdad exacta de conjuntos:

\[
\{(\psi(s'),o(y)):(s',y)\in B(s,a)\}
=\{(\psi(t'),o(y)):(t',y)\in B(t,a)\}.
\]

Una discrepancia devuelve s,t,a y una pareja de la diferencia simétrica; un fallo de habilitación devuelve la acción discrepante. La relación B se compone por pares completos, nunca por el producto de sus dos marginales.

**Salida válida:** sistema reducido sobre `im ψ`, con `Ebar(ψ(s))=E(s)`, Tbar imagen de T y `Bbar(ψ(s),a)` igual al conjunto anterior. No depende del representante por las comprobaciones. El Teorema 2.4 prueba por inducción que las trazas traducidas de longitud hasta n coinciden exactamente para todo n finito, con parada anticipada únicamente en T.

El chequeo puede limitarse a un subsistema cerrado explícitamente declarado; en ese caso la conclusión se limita a él. La reducción de conjuntos de resultados no transporta IDs de rama, multiplicidades, ley probabilística, condiciones infinitas ni familias de políticas. Por ello no autoriza por sí sola comprimir las ocurrencias de MV. `FP1_FINITE_EXACT` mantiene las ocurrencias causales originales.

### 2.4 Transporte informacional: resolución I-06

**Alcance:** esta es la reparación y justificación del transporte general de S1. El formato FP1 actual no admite un segundo modelo ni tablas R/O entre presentaciones. El transporte entre modelos queda fuera de sus operaciones implementables exigidas; los datos de una instancia se conservan internamente en su propia presentación.

Para dos presentaciones A y B, fijar un universo común de acciones `A_t`, información `I_t^K`, observaciones `Y_{t+1}^K` y actualizaciones parciales

\[
U_t^K:I_t^K\times A_t\times Y_{t+1}^K\rightharpoonup I_{t+1}^K,
\quad K\in\{A,B\}.
\]

Declarar mapas totales `R_t:I_t^A→I_t^B` y `O_{t+1}:Y_{t+1}^A→Y_{t+1}^B`. En el conjunto explícito K_t de triples pertinentes, sea `v_t(i,a,y)=(R_t(i),a,O_{t+1}(y))`. Exigir:

\[
(i,a,y)\in D_{U_t^A}\iff v_t(i,a,y)\in D_{U_t^B},
\]
\[
R_{t+1}(U_t^A(i,a,y))
=U_t^B(R_t(i),a,O_{t+1}(y))
\quad ((i,a,y)\in K_t\cap D_{U_t^A}).
\]

Los mapas son totales, por lo que la primera condición es precisamente la compatibilidad de dominios de ambas composiciones restringidas a K_t. Se registra por separado un dominio discordante o un valor discordante. Para un transporte de ejecuciones completas, K_t cubre todos los triples realmente usados en las ejecuciones de la dirección declarada y se valida esa cobertura contra las trazas. Para una equivalencia bidireccional, se necesita también cobertura de los triples relevantes de B; la sobreyección de los datos de A a los usados en B no se supone.

Las políticas parciales correspondientes cumplen, sobre el ámbito informacional pertinente, `i∈D_πA ⇔ R_t(i)∈D_πB` y `π_t^B(R_t(i))=π_t^A(i)`. Si se intenta construir πB a partir de πA, deben verificarse cobertura, saturación de dominio y constancia de πA en las fibras de R_t; se aplica Teorema 2.1. Extender fuera de `im R_t` necesita filas adicionales explícitas. Además, se comprueba pertenencia a la familia de políticas permitida, ejecutabilidad/admisibilidad en cada estado alcanzado e inicialización compatible `ι_0^B=R_0(ι_0^A)`.

**Argumento de transporte.** Suponer correspondencia de los resultados causales conjuntos, de inicialización y de acciones. Si `ι_t^B=R_t(ι_t^A)`, la ecuación de políticas da la misma acción. La correspondencia causal da `y_{t+1}^B=O_{t+1}(y_{t+1}^A)` en el paso emparejado. La igualdad de dominios permite ambas actualizaciones; la ecuación anterior da `ι_{t+1}^B=R_{t+1}(ι_{t+1}^A)`. La base vale por inicialización, luego la inducción conserva información y acciones durante todo horizonte finito. Para levantar todas las trazas se requieren las dos inclusiones causales pertinentes, no solo esta identidad de actualización.

Al comparar familias en una futura extensión se deberá presentar un mapa de transporte entre políticas y su alcance: inclusión en una dirección, cobertura de la familia objetivo, o correspondencia en ambas direcciones. Cada pareja deberá verificarse. La ecuación de actualización sola no establece ninguna de esas coberturas. El argumento identifica obligaciones finitamente comprobables **si una extensión admite las tablas pertinentes**; no promete que FP1 actual las reciba ni implemente ese verificador. Dentro de FP1, conservar una misma presentación corresponde matemáticamente al caso identidad R/O, sin introducir tablas adicionales ni certificar equivalencia con un segundo modelo.

## 3. MI: funciones y calibración

### 3.1 Evaluación

**Entrada:** X,T,S finitos, entorno fijo A, índice funcional finito I, `Σ:X⇀S`, y por componente i:

\[
F_i:S\times X\times\{A\}\rightharpoonup Y_i,
\quad u_i:Y_i\times X\times T\rightharpoonup O_i.
\]

O_i tiene preorden validado; en Q se usa su orden usual exacto y no una enumeración infinita de pares. Para cada p=(x,t), comprobar secuencialmente `x∈D_Σ`, `(Σ(x),x,A)∈D_Fi` y `(F_i(Σ(x),x,A),x,t)∈D_ui`. Solo entonces devolver

\[
o_i(x,t)=u_i(F_i(\Sigma(x),x,A),x,t).
\]

Mantener cuál de las tres guardas falló. El perfil completo `O(p)=(o_i(p))_i` tiene dominio `⋂D_i`. No quitar índices para completar un perfil. Una subfamilia es otro objeto con otro identificador y alcance. I vacío es un caso legítimo pero vacuo: perfil vacío definido sin consultar Σ.

**Especialización del intercambio:** `functional.measurements` suministra el resultado bruto por `(t,x,i)` y `indices[i].calibration` suministra `raw↦value`. Se instancia el contrato general usando el punto causal aumentado `(t,x)`, Σ identidad y F_i igual a la medición tabulada; u_i aplica la calibración común. No es obligatorio que F2 implemente otros programas F_i o u_i arbitrarios. El índice global se mantiene para todas las políticas y la comparación inicial utiliza perfiles terminales de escenarios correspondientes. La reducción funcional suministrada se verifica sobre todos los puntos alcanzados P con la consulta perfil completo; nunca comprime el estado causal del árbol.

### 3.2 Bloque comparativo y evidencia de calibración

**Entrada:** bloque explícito B⊆D_O, mismos I y órdenes, referencias finitas preordenadas `R_i`, tablas `r_i:X×T⇀R_i` y `h_i:R_i⇀O_i`. Una descripción semántica independiente identifica lo que cada referencia representa.

**Comprobaciones exhaustivas:** B⊆D_ri; `r_i[B]⊆D_hi`; `o_i(p)=h_i(r_i(p))` para cada p∈B; y, para todos a,b en `r_i[B]`,

\[
a\leq_i^R b\iff h_i(a)\preceq_i h_i(b).
\]

La factorización común y los dos sentidos del orden son hechos verificables. La correspondencia empírica de r_i con su magnitud es una premisa identificada, con procedencia, cuya veracidad no acredita la tabla. Un booleano «calibrado» no sustituye las tablas ni las comprobaciones. Es posible que las magnitudes sean racionales; deben usarse referencias y unidades comunes, sin normalizar por máximos individuales tácitamente.

En el intercambio, la referencia r_i es el valor `raw`, h_i es su tabla `calibration` y ambos órdenes son el orden usual racional. Se exige `a≤b ⇔ calibration_i(a)≤calibration_i(b)` en todas las parejas de valores raw alcanzados en el bloque de calibración declarado. La tabla es común, no se escoge una normalización por política. El contrato maestro fija ese bloque y conserva el diagnóstico de fallo de calibración separado de una medición no definida.

**Salida:** relación `p≽_DFR q ⇔ ∀i:o_i(q)≼_i o_i(p)` para todas las parejas de B. Se conserva la dirección y se derivan equivalencia, estricta e incomparabilidad con ambas consultas. La prueba de preorden es coordenada a coordenada; cambiar índices por pareja invalida el contrato. La equivalencia funcional no identifica estados causales.

### 3.3 Transporte de valores

Para cada `k_i:O_i⇀O_i'`, verificar cobertura de `o_i[B]` y preservación **y reflexión** del orden en todas las parejas alcanzadas. Después componer las tablas. Se conservan dominancia, equivalencia, estricta e incomparabilidad dentro de B (Teorema 3.4). Para conservar la función parcial completa, exigir cobertura de toda `o_i[D_i]`. No hace falta inyectividad literal en un preorden, pero sí conservar su orden; la monotonía sola es insuficiente.

## 4. MII: relaciones, interfaces y recursos

### 4.1 Presentación

Una unidad de escala conserva entidad, espacio de estados, estado y organización. La relación parte/todo es un dato estructural, no una inferencia del número de escala. Cada puerto s tiene ID, universo V_s, significado, entidad, tiempo, rol y unidad cuando corresponda. Las equivalencias de unidades o nombres se resuelven mediante traducciones explícitas antes de componer. Dos valores iguales no son el mismo puerto ni la misma demanda.

Una relación finita `R⊆W×∏_{s∈S}V_s` enumera filas completas. Su modo se declara: ejecuciones completas, donde w determina como máximo una fila, o completaciones, donde puede haber varias filas por w. Un w común debe pertenecer al mismo ámbito experimental. La coincidencia de etiqueta no demuestra compatibilidad física.

### 4.2 Proyección, unión natural y auditoría

**Proyección:** para U⊆S, conservar w y restringir cada fila a U; eliminar solamente duplicados extensionales del conjunto de filas proyectadas. Guardar por separado las filas originales como procedencia. Esta deduplicación no es una operación sobre probabilidades ni sobre ocurrencias del árbol causal.

**Unión natural:** para familia no vacía `(L_j,S_j)`, comprobar compatibilidad de tipos compartidos. Enumerar combinaciones de una fila de cada tabla con el mismo w; aceptar exactamente las que coinciden en todos los puertos compartidos. Producir la asignación única sobre `S=⋃S_j`. Equivale a `{(w,z):∀j (w,z|S_j)∈L_j}`. Si una tabla está vacía, la unión natural está vacía; no se elimina esa tabla.

**Auditoría con global R:** verificar cobertura `⋃S_j=S`, `L_j=π_Sj R` para cada j y `⋈L_j=R`. Informar diferencias locales y filas espurias/perdidas globales. Para dos vistas, una comprobación equivalente de exactitud global verifica rectangularidad por cada fibra de interfaz η: si `(η,a,b')` y `(η,a',b)` pertenecen a R, también `(η,a,b)`.

**Sin global suministrado:** formar J=⋈L_j y comprobar `π_Sj J=L_j` para cada j. Si todas las igualdades valen, J testimonia existencia de un global con esas proyecciones (Teorema 4.4). La realización no vacía exige además J≠∅. Si todas las tablas son vacías, el global vacío satisface las igualdades pero no testimonia ejecución alguna. La igualdad de interfaces por parejas es necesaria en muchos casos, pero no reemplaza esta comprobación conjunta.

**Especialización del intercambio:** para cada política se fija el testigo común w=κπ y se trata `query` como un puerto tipado adicional que identifica la ocurrencia. Por eso una vista puede omitir la columna query sin violar la convención de conservar w: el ámbito κπ sigue fijado externamente. Se calculan las vistas desde Rπ y se comprueba recomposición exacta sobre todos los puertos, incluida query. Omitir query puede perder correlaciones y hacer fallar el chequeo; el validador no la reintroduce en cada vista. La tabla global FP1 exige una fila por consulta causal, aunque el módulo relacional general también admita completaciones múltiples por testigo.

### 4.3 Recursos compartidos

Por cada fondo ρ se suministra unidad, ámbito temporal, capacidad racional `C_ρ≥0` y conjunto finito D_ρ de **identidades de demanda**. La tabla `c_ρ(r,d)` asigna un racional no negativo a cada `(r,d)` requerido; para cantidades firmadas o recuperaciones se necesita otro contrato, fuera de esta especialización inicial. La reutilización de un mismo ID exige el mismo significado, unidad, instante y valor. Referencias múltiples a una misma demanda se resuelven a un solo ID; demandas distintas se suman aunque sus valores sean iguales.

Si falta un consumo dentro de la tabla parcial, la evaluación presupuestaria de esa fila está fuera de dominio; no tiene consumo cero. Si las tablas no están correctamente presentadas, la entrada es inválida. Para cada fila completa, calcular `U_ρ(r)=Σ_{d∈D_ρ}c_ρ(r,d)` y la condición `U_ρ(r)≤C_ρ`. Conservar todas las filas, incluidos incumplimientos. `R satisface todos los presupuestos` exige dominio completo de los consumos y ausencia de desigualdades incumplidas en todas las filas/fondos. R≠∅ es una condición independiente.

Una capacidad por instante se evalúa por instante; no se suma entre tiempos salvo un fondo acumulado expresamente declarado. Un límite físico se incorpora al modelo causal con ese significado; un límite normativo puede rechazar una alternativa después sin borrar sus ejecuciones causales.

### 4.4 Reducción y resultados conjuntos

Para `ψ:R→Z` total y consultas parciales q sobre R, aplicar M0 a las tablas de cada q. La comprobación exacta es que `ψ(h)=ψ(h')` implique igualdad del registro completo de dominio y valor de todas las consultas. Si interesa preservar motivos de indefinición, cada motivo debe incluirse entre los observables requeridos. No añadir el ID de procedencia a ψ para hacerla artificialmente inyectiva.

El factor conserva los vectores **conjuntos** `(registro_q(h))_q` de dominio y valor porque todas sus componentes proceden de la misma fila. No afirmar conservación de multiplicidades o masa; su transporte corresponde a la ley explícita de MVI.

## 5. MIII: identidad, recetas y capacidad generativa

### 5.1 Datos previos y ausencia de circularidad

MIII recibe de MV todas las ejecuciones causales requeridas. En `FP1_FINITE_EXACT`, H es natural finito, Π es familia explícita finita no vacía, Ξ es conjunto común finito no vacío y existe para cada π una biyección verificada `b_π:Ξ→Leaves_π`; cada hoja termina exactamente en H. El cuerpo causal se genera antes de evaluar la tarea de viabilidad. Ninguna hoja se elimina por presupuesto normativo, bienestar, probabilidad cero, falta de evidencia o valoración desfavorable. Si una condición impide acreditar el perfil, se diagnostica; no se reemplaza la familia por sus miembros favorables.

Estos requisitos especializan S1. La teoría general permite múltiples realizaciones por escenario, parada anticipada y familia de políticas vacía, pero esas variantes no reciben conformidad con este perfil. Una alternativa de decisión corresponde a una política π: su CAG se calcula con la familia singleton `{π}`. El CAG de la familia completa puede calcularse aparte y lleva otro ámbito; no se atribuye ese repertorio agregado a cada alternativa.

### 5.2 Identidad y traducción

**Contrato de S1:** firmas totales `Γ_G,A:X_A→S_G,A` y `Γ_G,c:X_c→S_G,c`, equivalencias completas sobre firmas alcanzadas, y preórdenes de conservación en los cocientes. Validar equivalencias y preórdenes. Construir `q_G(x)=[Γ_G(x)]`. La identidad de clase se obtiene extensionalmente; el nombre de un representante no agrega preferencia ni significado.

**Especialización de intercambio FP1:** los universos de identidades nativas y comunes se entregan ya cocientados como IDs, cuya equivalencia es igualdad exacta de ID. La firma `q_A(t,x)` es una tabla parcial y debe cubrir todos los pares tiempo/estado de las trazas para certificar CAG. El tiempo se considera parte del estado tipado pertinente; no se infiere que un estado con el mismo nombre en tiempos distintos tenga la misma firma. La traducción `τ:Q_A⇀Q_c` opera sobre las identidades y el resultado es `g_t=τ(q_A(t,x_t))`. Es una factorización más restrictiva que una traducción general sobre estados: dos apariciones de una misma identidad nativa reciben una misma imagen. Esta elección reduce las entradas del perfil, no modifica S1. No hace falta presentar estados comunes independientes cuando sus identidades cocientadas ya son el codominio operativo.

Los significados se presentan sobre un universo semántico finito común de átomos tipados. Una tabla de significado asigna a cada firma/clase pertinente un conjunto no vacío de esos átomos. Comprobar constancia por clase cuando se suministra por firma. La interpretación de los átomos es una premisa externa con referencia y procedencia; la igualdad/no vaciedad de conjuntos sí se comprueba. No se infiere fidelidad a partir del resultado CAG.

La traducción funcional parcial general `T_Ac:X_A⇀X_c` cubre **todos los estados de todas las trazas**, incluido x0. Para cada estado alcanzado x, verificar `J_A(q_G,A(x))=J_c(q_G,c(T_Ac(x)))≠∅`. En el intercambio especializado se verifica equivalentemente `J_A(n)=J_c(τ(n))≠∅` para toda identidad nativa n alcanzada; la traza común se produce mediante τ. Igualdad de conjuntos de significado no identifica automáticamente IDs. Se permite τ no inyectiva.

En S1, si la receta utiliza conservación, se verifica preservación y reflexión en cada par requerido, tanto si el resultado es verdadero como si es falso. Para `hold,L` son los pares `(x_t,x_s)` con `1≤t`, `t+L≤H`, `t≤s≤t+L`. Para `acc` son **todos** los pares consecutivos `(x_{s-1},x_s)`, s=1,…,H, incluso después de la primera pérdida. Para `att` no se necesita transportar pares de conservación, aunque todo preorden suministrado debe ser válido. Para hold/acc, FP1 aplica la guardia uniforme más fuerte sobre **todos los pares** de identidades nativas alcanzadas requeridas: `n⊴_A m ⇔ τ(n)⊴_c τ(m)`. Esto implica la guardia de cada receta. Si τ fusiona dos IDs en una receta con conservación, reflexión exige que sean mutuamente conservativos en el preorden nativo; no exige igualdad literal porque el orden es un preorden. La igualdad de significado de identidades y el transporte de conservación son obligaciones distintas.

Una traducción no definida o una desigualdad semántica impide certificar el CAG requerido. No produce CAG adicional vacío. El origen puede estar representado y retenerse con su propio estado aun si fallan obligaciones futuras. Las traducciones relacionales no son una entrada de este perfil.

### 5.3 Recetas, algoritmo y testigos

Con traza común completa `(g_0,…,g_H)` y conservación validada:

\[
Ach_{att}(e)=\{g_t:1\leq t\leq H\};
\]
\[
Ach_{hold,L}(e)=\{g_t:1\leq t,\ t+L\leq H,
\ \forall s\in\{t,\ldots,t+L\}:g_t\trianglelefteq g_s\};
\]
\[
Ach_{acc}(e)=\{g_t:1\leq t\leq H,
\ \forall s\in\{1,\ldots,t\}:g_{s-1}\trianglelefteq g_s\}.
\]

Enumerar tiempos candidatos y comparaciones exactas. Conservar por cada g todos los tiempos que acreditan su logro, y la ventana o prefijo de soporte cuando corresponde. Las comparaciones necesarias se validan **antes** de aprovechar un fallo para detener la acumulación de logros. `hold,0=att`; L≥H da hold vacío; H=0 da todos los logros futuros vacíos. El origen sigue siendo un objeto distinto.

Por Teorema 5.1, `hold,L+1⊆hold,L⊆att` y `acc⊆att`. Un logro acc a tiempo t conserva todos los anteriores por transitividad, pero no promete conservación después de t. Una identidad encontrada dos veces aparece una vez en el conjunto y conserva ambos testigos. Los conjuntos no cuentan eventos repetidos.

### 5.4 Posibilidad, robustez y política común

Para cada política π, una vez verificadas cobertura causal, biyección de escenarios, no vaciedad y todos los requisitos anteriores:

\[
P_\pi^{r,poss}=\bigcup_{\xi\in\Xi}Ach_r(b_\pi(\xi)),
\quad P_\pi^{r,rob}=\bigcap_{\xi\in\Xi}Ach_r(b_\pi(\xi)).
\]

La intersección se inicia con los logros de una hoja real, nunca con un universo universal en ausencia de hojas. Para cada g posible, conservar las ocurrencias y tiempos favorables. Para g robusto, conservar un mapa de **cada escenario** a su hoja y testigos temporales. Si g no es robusto, un escenario/hoja sin logro testimonia el fallo dentro de una evaluación completa; si faltan datos, no usarlo como contraejemplo factual.

Para una familia Π:

\[
G_r^{poss}=\bigcup_{\pi\in\Pi}P_\pi^{r,poss},
\quad G_r^{rob}=\bigcup_{\pi\in\Pi}P_\pi^{r,rob}.
\]

Por tanto, `g∈G_rob` significa `∃π ∀ξ ∃t…` para alcance en este perfil. La política se fija antes de conocer el escenario; t puede variar por hoja. No significa `∀ξ ∃π…`. Ninguna probabilidad interviene. La unión exterior conserva el mapa `g↦políticas que lo garantizan`, sin fusionar políticas.

Para demanda finita D de identidades, construir `Joint_r(w,D)={π∈Π:D⊆P_π^{r,rob}}` mediante inclusión exacta. D vacío da Π si los CAG por política están en dominio; no acredita una demanda sustantiva. Joint no vacío garantiza logro de cada identidad en cada realización bajo la misma política; no garantiza simultaneidad ni coexistencia. Si ese requisito importa, debe declararse otra receta, fuera de las tres recetas iniciales.

### 5.5 Origen y CAG

El origen se calcula solo desde la inicialización `g0=q_G,c(T_Ac(x0))`, o en el intercambio especializado `g0=τ(q_A(0,x0))`, antes de cualquier agregado. Para receta r y cuantificador d:

\[
CAG^{r,d,+}=G_r^d\setminus\{g0\},
\qquad CAG^{r,d}=\{g0\}\cup CAG^{r,d,+}.
\]

La salida conserva por separado g0, G, CAG+, CAG, política/familia, receta, L cuando corresponda, cuantificador, H, traducción, cobertura y testigos. Si g0 también se logra en futuro, el registro G y sus tiempos lo muestran; su inclusión canónica en CAG no demuestra ese retorno. Un CAG adicional vacío solo se presenta como valor si toda la construcción está en dominio.

### 5.6 Descenso y comparación

Para una equivalencia inicial declarada sobre un conjunto finito W, una clase completa C se admite para descenso solo si todos sus miembros tienen CAG certificado, mismo ámbito, g0 constante y CAG constante. Enumerar cada clase; cualquier miembro ausente del dominio o cualquier discrepancia excluye toda la clase. Devuelve la función sobre las clases seguras y conserva los miembros excluidos. Para factorizar la función parcial original completa hacen falta además saturación de D_f y constancia en todas sus clases definidas. Los testigos de política de un miembro no se atribuyen a otro por igualdad de conjuntos CAG.

En un bloque de comparación fijar significado común, receta, L, cuantificador, H, condiciones experimentales y variables autorizadas a cambiar. Para comparar políticas de `FP1_FINITE_EXACT`, mantener inicialización, proceso, escenarios comunes y marco; cambiar únicamente la política identificada. Definir `A≽_CAG B ⇔ CAG(B)⊆CAG(A)` mediante diferencias de conjuntos. Equivalencia es igualdad, estricta es inclusión propia y la incomparabilidad requiere dos diferencias no vacías. Una falta de dominio o ámbito común se registra aparte.

La relación es preorden y su cociente por igualdad de CAG es orden parcial (Teorema 5.6). Cardinalidades iguales no implican equivalencia. Más CAG no demuestra más bienestar, viabilidad, funcionalidad ni preferencia. Esas magnitudes conservan sus propios contratos en los módulos siguientes.

## 6. Obligaciones comprobables y límites

| Obligación local | Evidencia mecánica finita | Premisa externa identificada | Efecto de incumplimiento |
|---|---|---|---|
| FSuf funcional de FP1; DSuf solo contrato general fuera del formato actual | Enumeración de fibras; para una extensión DSuf, filas conjuntas y diferencias | Relevancia de consultas/modelo | No certificar la reducción; conservar contraejemplo |
| Transporte entre presentaciones, fuera del formato FP1 actual | En una extensión: dominios, ecuaciones, inicialización, membresía y cobertura del mapa | Legitimidad de la información declarada | No trasladar garantía de control entre modelos |
| Perfil y calibración | Cobertura de componentes, factorización y reflexión del orden | Significado/medición de referencias | Perfil parcial o comparación no admitida según el fallo |
| Composición | Tipado, cobertura, proyecciones y unión natural exactas | Correspondencia real de puertos/testigos | No acreditar global exacto o realización |
| Presupuesto | Dominios y sumas racionales por ID/unidad/tiempo | Capacidad y criterio normativo o físico | Diagnóstico de ausencia o incumplimiento; sin borrar filas |
| Identidad generativa | Equivalencia, preorden, constancia y significado no vacío | Elección de propósito y significado | No certificar CAG en ámbito afectado |
| Traducción CAG | Cobertura de todos los estados y pares requeridos; igualdad semántica | Adecuación de la traducción al sistema | Retener origen disponible, no sustituir CAG por vacío |
| Robustez | Todas las hojas y escenarios, intersección y testigos por hoja | Completitud causal respecto al mundo | Garantía únicamente relativa al modelo declarado |
| Comparación | Tablas completas y mismo bloque | Criterios/variables autorizadas | Fuera de dominio o incomparabilidad, según corresponda |

La terminación de estos constructores se deduce de las enumeraciones finitas y operaciones decidibles del perfil. La fidelidad de un modelo real, su utilidad, la novedad científica y la corrección de una futura implementación no se deducen de este contrato. Los casos de conformidad prueban implementaciones respecto al contrato; los ejemplos sintéticos no validan aplicaciones reales.
