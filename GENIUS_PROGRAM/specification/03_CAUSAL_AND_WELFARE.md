# 03 — Futuros causales y bienestar

Specification candidata GENIUS-SPEC-1.0.0 · perfil FP1_FINITE_EXACT · fuente S1, MIV P01535–P01951 y MV P01952–P02344. Este documento fija la semántica matemática. La gramática de intercambio y los códigos de diagnóstico del contrato maestro la serializan; los nombres matemáticos de este documento no autorizan dialectos de JSON alternativos. Revisión deductiva: `theory/reviews/REVIEW_IV_V.md`.

## 1. Alcance y precedencia causal

MV construye los futuros desde primitivas causales declaradas. MIV registra bienestar sobre esas ejecuciones. Ni una medición, una preferencia, un resultado de CAG, una tarea de viabilidad ni una masa probabilística altera el árbol recibido. Las restricciones globales se evalúan después de construirlo.

FP1 instancia el caso fuerte finito de S1 10.2–10.3: horizonte natural H; conjuntos, relaciones y tablas finitos; familia explícita no vacía de políticas; toda ejecución llega a H; conjunto común no vacío de escenarios; exactamente una hoja por política y escenario; bienestar completo sobre soportes comunes. La teoría general de MV admite terminaciones anticipadas y varias realizaciones por escenario: esa generalidad se revisó, pero no se importa silenciosamente a FP1.

Los valores numéricos de bienestar son racionales exactos con comparación usual en una dimensión ya orientada en sentido «mayor es no peor». La unidad, interpretación y calibración se fijan por dimensión. No se convierten unidades, no se deducen preferencias y no se invierte una escala de costos sin una transformación explícita declarada. Un identificador de estado y otro de información pueden tener la misma cadena textual: pertenecen a espacios de tipos distintos y jamás son intercambiables por esa coincidencia.

## 2. Primitivas causales tipadas

Sean conjuntos finitos declarados X (estados causales), I (informaciones), A (acciones), U (entradas exógenas), Y (observaciones). FP1 fija una condición inicial c0 y usa C0={c0}; el espacio general de S1 puede contener otras condiciones e intervenciones, pero no se añaden campos ajenos al formato de `01_TYPES_AND_WIRE.md`. Se declara H ∈ N, T={0,…,H}, T−={0,…,H−1}, y Pi, una familia finita no vacía de identificadores de políticas. Los espacios requeridos por las tablas deben contener sus argumentos; no se exige A, U o Y no vacío cuando H=0 y no se utiliza ninguno de sus elementos.

Se conservan por separado:

| Objeto | Tipo y significado | Guarda formal |
|---|---|---|
| Marco M | Identificador de representación | Referenciado por todos los componentes |
| Modelo beta | Identificador de estructura y parámetros | No contiene una política elegida por resultado |
| Contexto gamma | Contexto efectivo con Base(gamma)=beta | FP1 usa modo pre; gamma y c0 fijados antes de comparar |
| c0 | Condición inicial seleccionada | Init_gamma(c0) está definido |
| Init_gamma | Tabla parcial C0 ⇀ X×I | Par realizado (x0,i0), no una distribución inferida |
| delta | Intervención concreta del modo fix de S1 general | Fuera del formato FP1; no se infiere ni sustituye |
| A_exec | Tabla (t,x) ↦ subconjunto de A | Ejecutabilidad física declarada |
| A_adm | Tabla (t,x) ↦ subconjunto de A | Admisibilidad local declarada, distinta de la anterior |
| pi | Tabla parcial T−×I ⇀ A | Una única acción por clave (t,i) |
| B_gamma | Tabla parcial T−×X×A ⇀ filas finitas | Cada fila definida contiene resultados con etiquetas locales únicas |
| U_gamma | Tabla parcial T−×I×A×Y ⇀ I | Determinista en la clave declarada |

Una fila causal contiene tuplas `(lambda,u,x_next,y_next)` con lambda única dentro de esa fila. La misma lambda puede aparecer en filas distintas; no identifica por sí sola una ejecución. Pueden existir dos resultados con iguales u, x_next e y_next y distintas lambda: son ocurrencias diferentes, permitidas en la sintaxis del modelo. La ruta fuerte FP1 solo se certifica cuando la comprobación final de escenarios conserva la unicidad exigida; no los fusiona para conseguirla. Si no la conserva, se emite el diagnóstico correspondiente sin declarar inválida por ese solo motivo toda la presentación causal.

FP1 instancia el modo pre: c0 y gamma se fijan antes de comparar y son comunes a Pi. S1 también define el modo fix, que conserva la intervención delta que produce ese c0 y ese gamma, con RealC0_beta(delta,c0) y Ctx_fix_beta(delta)=gamma. El formato FP1 no recibe esos objetos ni certifica transporte de intervenciones fix. Dos intervenciones con el mismo estado inicial no son sustitutas: pueden modificar de manera distinta la alimentación futura, las observaciones o la dinámica. Aun en una extensión que tabule RealC0 y Ctx, esas tablas certificarían pertenencia al modelo declarado; su adecuación física seguiría siendo una premisa externa identificada.

La clave de experimento es kappa_pi=(M,beta,gamma,c0,pi,H). No se omite la política aunque dos políticas tengan la misma tabla o produzcan las mismas trayectorias.

## 3. Inicialización e información legítima

La raíz realizada es `(0,x0,i0)` con Init_gamma(c0)=(x0,i0). No se reconstruye i0 a partir de x0 por conveniencia del evaluador.

El certificado basal fuerte general de S1 considera un conjunto H0 de historias y mapas totales b:H0→C0, s:H0→X, i:H0→I. Exige:

1. b^{-1}(c0) no vacío.
2. Para todo h de esa fibra, s(h)=x0 e i(h)=i0.
3. Las continuaciones del modelo parten de ese mismo par y utilizan el mismo contexto, proceso, actualización y política.

La primera condición evita una «realización» acreditada por un universal vacío. FP1 instancia el certificado con el testigo formal singleton declarado `history=h0`: H0={h0}, b(h0)=c0, s(h0)=x0 e i(h0)=i0. Las igualdades y no vacuidad quedan verificables en ese dominio formal. El nombre h0 no acredita observación de una historia real; la realización y adecuación causal externas permanecen en `initialization.basis`, `model.basis` e `information_basis`. No se extiende el certificado a otras historias no incluidas. Las obligaciones de suficiencia de M0 se aplican a cualquier reducción realmente utilizada.

La legitimidad formal de una política procede de dos reglas: la acción es pi(t,i), y la información siguiente es exactamente U_gamma(t,i,a,y_next). No consulta el estado oculto, una lambda, un escenario futuro ni la utilidad resultante. La legitimidad del canal de observación declarado es una premisa del modelo, separada de su verificación mecánica.

Para toda pareja de ocurrencias alcanzadas con el mismo `(t,i)`, la acción es la misma. Si en una de ellas esa acción no es ejecutable o localmente admitida, la política no obtiene certificado causal completo sobre la familia declarada. No se autoriza una acción alternativa elegida por x en esa ocurrencia.

## 4. Constructor exacto del árbol

Un nodo es una **ocurrencia** identificada por `(kappa_pi,p)`, donde p es la palabra de etiquetas de rama desde la raíz. Sus campos son tiempo |p|, estado x, información i y, salvo en la raíz, la acción, entrada y observación de la transición que lo produjo. Sus ancestros se conservan. La clave no es `(t,x)` ni `(t,x,i)`; la reconvergencia de estados no fusiona nodos.

Constructor para cada pi, sin consultar bienestar ni viabilidad:

1. Crear raíz p=palabra vacía, tiempo 0, estado x0 e información i0.
2. En un nodo de tiempo H, registrar hoja por horizonte. No consultar acción ni fila sucesora.
3. En un nodo de tiempo t<H, consultar a=pi(t,i). Verificar que está definida, a∈A_exec(t,x) y a∈A_adm(t,x).
4. Consultar B_gamma(t,x,a). La fila debe estar presente, ser no vacía y estar bien tipada.
5. Para **cada** resultado `(lambda,u,x_next,y_next)` de la fila, consultar i_next=U_gamma(t,i,a,y_next). Agregar su hijo `(p·lambda,t+1,x_next,i_next)` con todos los campos de transición.
6. Repetir hasta alcanzar H en todas las ramas.

Las tablas se validan como tablas finitas cerradas. Una clave fuera del dominio explícito de una función parcial significa indefinición formal. Una tabla obligatoria ausente o una referencia mal formada es una entrada inválida. Esas categorías no se confunden con falta de conocimiento empírico.

La inspección puede producir un árbol parcial diagnosticado. Si se conoce un resultado físico y falta U en él, se conserva ese resultado y se señala la información sucesora ausente; no se inventa i_next ni se etiqueta esa rama como terminada. El árbol parcial no satisface el contrato de cobertura de FP1 y no se usa para certificar garantías universales ni una frontera exhaustiva.

FP1 no tiene una regla de terminación anticipada. Si una instancia la declara como parte de su semántica, queda fuera de este perfil, sin eliminar ese hecho de la teoría. Una fila vacía, política indefinida, acción inadmisible, medición ausente, muerte de un portador o llegada a un destino no sirve como terminación implícita. A H=0 la raíz es la única hoja y ninguna acción es requerida.

### Garantías del constructor

**Corrección:** inducción sobre profundidad: la raíz es la inicialización y cada hijo utiliza una acción de la política y un resultado de la fila causal con su actualización correcta.

**Cobertura:** toda continuación válida de un nodo aparece porque se enumeran todos los resultados, con sus lambda; la inducción añade todo prefijo válido. Un árbol aportado por un productor debe contrastarse con las filas originales, no solo con una topología internamente coherente.

**Finitud:** la raíz es finita, cada fila es finita y hay H+1 niveles. Si existe una cota b≥1 de ramificación en los nodos usados, el número de nodos no supera Σ_{t=0}^H b^t. Esta cota no promete rendimiento práctico para H grandes.

**No vacuidad de completaciones:** todo nodo tiene una hoja descendiente, por inducción en H−t usando una fila no vacía. Así el conjunto Q_pi de consultas coincide con Pref(F_pi), y F_pi no es vacío. La relación de prefijo es reflexiva y se mantiene dentro de la misma kappa_pi.

Las completaciones son L_pi(h)={e∈F_pi:h es prefijo de e}. Si se exige que todas las consultas originales tengan una completación dentro de F'⊆F_pi, necesariamente F'=F_pi: una hoja omitida era ella misma una consulta. Aceptar una subfamilia para otra tarea no redefine Q_pi ni F_pi.

## 5. Escenarios y correspondencia fuerte FP1

En MV un escenario es la secuencia de entradas de una ejecución, no un alias libre de una hoja:

`word_u(e)=(u0,…,u_{H−1})`.

FP1 declara un conjunto finito no vacío Xi de identificadores de escenario, cada uno con su palabra exógena de longitud H. Las palabras son distintas entre escenarios. Se verifica para **cada** pi:

1. La imagen `{word_u(e):e∈F_pi}` coincide exactamente con las palabras declaradas en Xi.
2. Para cada xi, la fibra `{e∈F_pi:word_u(e)=word_u(xi)}` contiene exactamente una hoja.
3. Se deriva la correspondencia e_pi:Xi→F_pi asignando a cada escenario la única hoja de su fibra; por ello es una biyección y cubre todas las hojas. El formato de entrada no necesita una tabla adicional de correspondencia; cualquier certificado de salida se comprueba contra esa derivación.

No basta que dos conjuntos tengan igual cardinalidad. Tampoco bastaría que un productor de certificados aportara una tabla ID↔hoja bijectiva si asignara a una hoja una palabra distinta de su secuencia u. Dos ramas ocultas distintas con la misma palabra u no se convierten en una sola por compartir observación; la instancia conserva ambos futuros y no satisface la ruta fuerte FP1.

A H=0, Xi tiene exactamente un escenario, la palabra vacía, y cada política posee una sola hoja raíz. Dos IDs que nombran esa misma palabra no constituyen dos escenarios.

Para comparar políticas se conserva el escenario común, pero no se igualan las ejecuciones: RunKey(e_pi,xi) y RunKey(e_sigma,xi) tienen distintas kappa si pi≠sigma. La correspondencia formal por entradas no demuestra por sí sola que esas entradas tengan la interpretación empírica pretendida.

## 6. Salida causal y diagnósticos

La salida causal certificada entrega, por política:

- kappa_pi; raíz; todos los nodos y sus registros; Q_pi, F_pi y relación de prefijo.
- Para cada hoja, RunKey, secuencia completa de estados, información, acciones, entradas, observaciones y etiquetas, con reloj E_e^T={0,…,H}.
- L_pi(h) para consultas requeridas, o un procedimiento finito exacto que lo derive del árbol.
- Xi, palabras exógenas y bijección e_pi verificadas; procedencia hacia filas B y U utilizadas.
- Certificados de cobertura, ejecutabilidad y admisibilidad local; premisas externas de representación identificadas.

Los diagnósticos deben distinguir, al menos, política fuera de Pi; decisión fuera de dominio; acción físicamente inexecutable; acción localmente inadmisible; fila causal fuera de dominio o vacía; actualización fuera de dominio; referencia/tipo inconsistente; resultado omitido; duplicación de etiqueta local; inicialización no acreditada; correspondencia de escenarios incorrecta; extensión fuera de perfil. Una restricción global incumplida es un resultado posterior de una ejecución conservada, no un error causal que autorice borrarla.

## 7. Registro enriquecido de bienestar

Para cada e∈F_pi se conserva:

`W_tilde(e)=(E_e^T,S_e^L,I_e^W,D_e^W,w_e)`.

| Componente | Dominio y obligación |
|---|---|
| E_e^T | Reloj derivado de e, no de mediciones ni portadores |
| S_e^L | Conjunto de `(carrier,t)` donde el portador existe; t∈E_e^T |
| I_e^W | Índices `(carrier,t,dimension)` aplicables; todo `(carrier,t)` pertenece a S_e^L |
| D_e^W | Dominio explícito de mediciones, subconjunto de I_e^W |
| w_e | Función con dominio exactamente D_e^W y valor en la escala declarada de cada índice |

El registro incluye RunKey(e), procedencia de mediciones, significado/unidad/calibración de las dimensiones y frontera. Un portador conserva el mismo identificador entre tiempos y escalas. Dos vistas que incluyen la misma persona no crean dos portadores.

FP1 fija soportes comunes E*={0,…,H}, S* e I*, y escalas/calibraciones comunes, para todas las hojas comparadas. Su ruta fuerte exige E_e^T=E*, S_e^L=S*, I_e^W=I*, D_e^W=I* y un racional w_e(i) para todo i∈I*. Se exige esta cobertura también para políticas que después sean descartadas por presupuesto u otra restricción global. La medición de una rama no sustituye a la de otra con el mismo estado final.

La presentación FP1 almacena cada medición en la clave `(pi,path,carrier,dimension)` del nodo de tiempo t=|path| correspondiente. El registro de una hoja se deriva recorriendo sus nodos: `w_e(carrier,t,dimension)` es el valor en el prefijo de e de longitud t. Por construcción, dos hojas que comparten el mismo prefijo dentro de una política comparten las mediciones de ese prefijo. No se permiten valores incompatibles para una única ocurrencia que aparece en varios registros de hoja. Esta coherencia no identifica ocurrencias de políticas distintas ni ramas reconvergentes. Las unidades y calibraciones de la plantilla siguen siendo comunes.

Aunque la ruta fuerte FP1 exige medición completa, no elimina campos del objeto general. I*=∅ no implica S*=∅: puede existir un portador sin dimensiones declaradas. S*=∅ tampoco implica E*=∅: el proceso conserva tiempos sin portadores. La teoría general y la sintaxis de tablas parciales FP1 admiten D_e^W⊊I_e^W; es un registro parcial válido. Sin embargo, carece de una precondición de la comparación completa FP1 y no se completa con ceros. Puede conservarse un bloque comparativo menor explícitamente identificado como relativo según el contrato de decisión; no acredita cobertura de la familia objetivo completa.

Si falta el registro de una hoja entera, falla la cobertura. Si existe el registro y falta una medición, falla la completitud requerida para esa comparación. Si hay una medición fuera del reloj o del soporte conocido, la presentación es inconsistente. «Desconocido», «conjunto vacío conocido», «fuera del dominio» y «valor cero» son estados distintos.

## 8. Comparador completo de bienestar de FP1

La regla elegida es el producto identificado, temporal y por escenario. Para dos políticas del bloque:

`pi >=_W sigma` si y solo si para todo xi∈Xi y todo i=(carrier,t,dimension)∈I* se cumple `w_{e_pi,xi}(i) >= w_{e_sigma,xi}(i)`.

La relación se consulta solo tras verificar el mismo bloque de marcos/ámbito, Pi/Xi, horizonte, soporte, índices, unidades y calibraciones requeridos. No empareja por nombre parecido, posición de fila, estado final o coincidencia numérica entre diferentes dimensiones.

El comparador conserva como evidencia cada par de RunKey y cada coordenada consultada. Un fallo de dominancia se acredita mediante `(xi,i,value_pi,value_sigma)` con value_pi<value_sigma. Si un registro requerido no es válido o no está completo, la salida no es «no domina»: la consulta comparativa carece de las precondiciones de este perfil.

La dominancia estricta es `pi >=_W sigma` y no `sigma >=_W pi`. La equivalencia es dominancia en ambos sentidos; bajo racionales usuales equivale a igualdad en todas las coordenadas. Si no domina ninguna dirección, se informa incomparabilidad. No se suma bienestar de personas, escenarios, dimensiones ni tiempos. No se usan las probabilidades de los escenarios para borrar coordenadas de masa cero.

**Prueba del preorden.** La reflexividad es la de ≥ racional coordenada a coordenada. Si pi domina a sigma y sigma a tau, cada coordenada de pi es ≥ a la de sigma y esta ≥ a la de tau; la transitividad racional da pi≥_W tau sobre el mismo conjunto fijo Xi×I*. La prueba falla si se cambia el conjunto de índices entre parejas. El cociente por equivalencia es un orden parcial.

Si I*=∅, toda comparación resulta equivalente por vacuidad. El resultado debe conservar esa condición; no acredita bienestar positivo, existencia ni supervivencia. Exigir un perfil no vacío o una condición de existencia corresponde a una restricción explícita de la aplicación. H=0 sí admite un perfil no vacío con mediciones en t=0.

Este producto es una regla normativa/comparativa declarada de FP1. No se presenta como única regla deducida de los datos. Soportes diferentes, duraciones distintas, nacimientos/muertes comparativos o anonimato requieren otro perfil o un contrato comparativo adicional.

## 9. Existencia, persistencia, destinos y monitor

Con soporte conocido, `HayPortadores(e)` equivale a S_e^L≠∅. Para un T_req⊆E_e^T explícito:

- `ExistenciaEn(e,T_req)` significa para todo t∈T_req existe algún carrier con `(carrier,t)∈S_e^L`.
- `Persistencia(e,carrier0,T_req)` significa para todo t∈T_req, `(carrier0,t)∈S_e^L`.

La primera no implica la segunda para algún portador común: en t=0 puede existir únicamente a y en t=1 únicamente b. Si se utiliza un universal para acreditar existencia efectiva, se exige T_req≠∅. La consulta sobre T_req=∅ es verdadera por lógica, pero no demuestra que exista nadie.

Como objeto derivado opcional, una tabla de regiones K_t⊆X, total sobre T, permite definir `m0=1[x0∉K0]`, `m_{t+1}=m_t OR 1[x_{t+1}∉K_{t+1}]`. La inducción da `m_t=1` exactamente cuando hubo al menos una violación antes o en t. El monitor permanece en uno en toda extensión; no modifica información ni acciones. Para afectar un veredicto debe existir una tarea o restricción que lo consuma expresamente.

El monitor y los destinos de esta sección son consultas teóricas derivadas revisadas. `K_t` y predicados de destino no son campos de entrada ni operaciones obligatorias del formato FP1 de 01. Para representar una exigencia histórica dentro de ese formato se usa la tarea semántica tabulada con referencias justificadas; incorporar un constructor independiente de monitor o destino requiere una extensión versionada. No se añade un campo ni capacidad tácitos al futuro Kernel.

Una consulta de destino necesita su predicado, dominio contextual y evidencia de reconocimiento. Alcanzar un destino, terminar en él, permanecer en él y evitar daños anteriores son proposiciones diferentes. Un destino puede usarse como predicado finito adicional si su dominio y propósito están declarados. No cambia el árbol ni crea una regla de parada FP1.

## 10. Resultados generales revisados fuera de la implementación FP1

1. **Resumen suficiente de bienestar (6.3).** Una representación total Psi de registros permite descender una consulta parcial f si y solo si la elevación de f con una marca distinguida de indefinición es constante en cada fibra. Se exige constancia de dominio y valor; el valor final o una media no bastan para consultas de daño intermedio. FP1 conserva registros completos y no necesita aceptar resúmenes arbitrarios.
2. **Dominancia anónima (6.4–6.5).** Entre poblaciones de igual tamaño y perfiles personales homogéneos y completos, una biyección única para toda la trayectoria que no empeore perfiles produce un preorden. Se decide por emparejamiento perfecto solo si las correspondencias admisibles se caracterizan exactamente por aristas locales. Restricciones globales de emparejamiento requieren otro procedimiento. Un certificado negativo exige el grafo completo y un déficit de vecinos verificable. FP1 no activa anonimato.
3. **Reglas poblacionales generales (6.6–6.7).** Se pueden certificar reflexividad y transitividad de una relación completamente definida sobre un bloque finito. Eso no determina su justificación normativa; ni las mediciones ni las leyes de preorden deciden si es mejor una o dos vidas con el mismo perfil. FP1 no extiende la relación a soportes diferentes.
4. **Régimen y reducción causal (7.6).** Una reducción conserva conjuntos de trazas proyectadas si preserva conjuntamente entradas, estados sucesores y observaciones desde cada representante alcanzado, conmuta información, conserva acciones, inicialización y parada, y usa políticas realmente admitidas. No basta igualar proyecciones marginales. Omitir etiquetas en esa prueba no conserva número de ocurrencias, RunKey ni probabilidades. FP1 calcula sobre el árbol nativo completo; no acepta una reducción de ocurrencias sin contrato adicional.
5. **Terminaciones y multiplicidad de escenarios (7.3–7.5).** Los teoremas generales admiten hojas por terminación causal y fibras Runs(pi,xi) múltiples. Sus pruebas son válidas bajo sus hipótesis, pero la ruta comparativa FP1 exige horizonte común y fibras singleton. Una extensión futura deberá modificar explícitamente bienestar, correspondencia de escenarios, referencia semántica y ley.

## 11. Obligaciones de conformidad y procedencia

| ID | Obligación verificable | Fundamento S1 | Caso mínimo de refutación |
|---|---|---|---|
| CW-01 | Identidades de M,beta,gamma,c0,pi,H separadas y modo válido | 7.1–7.3 | Igual x0 con contextos distintos no acredita mismo experimento |
| CW-02 | Inicialización definida y realizada; fibra no vacía si se declara certificado basal | 7.1 | Fibra vacía satisface igualdades universales pero no realización |
| CW-03 | Acción función de (t,i); información solo Init/U declarados | 7.2 | Dos estados ocultos con misma i requieren la misma acción |
| CW-04 | Ejecutabilidad y admisibilidad local en todos los nodos utilizados | 7.5,7.8 | Acción admitida en un estado e inexecutable en otro con igual i |
| CW-05 | Toda fila requerida no vacía; todas las ramas y actualizaciones incluidas | 7.3 | B={seguro,inseguro}; productor omite inseguro |
| CW-06 | Claves de ocurrencia preservadas; no fusionar por x o i | 7.6–7.7 | Dos ramas reconvergen al mismo par (x,i) |
| CW-07 | Todas las hojas a H; escenarios son palabras u; imagen exacta y fibras singleton | 7.7,10.2 | Dos hojas distintas con misma palabra u; no satisface FP1 |
| CW-08 | Q=Pref(F), L(h) no vacío, comparación contra todas las filas | 7.3–7.5 | Hoja omitida no tiene completación en F' |
| CW-09 | Reloj, existencia, aplicabilidad y medición separados | 6.1 | Mismo I vacío con S distintos; mismo S con relojes distintos |
| CW-10 | Una medición por clave aplicable y D=I; cobertura de todas las hojas | 6.4,10.2 | Hoja presente sin medición no puede desaparecer |
| CW-11 | Bloque y producto Xi×I* fijos, unidades/calibraciones comunes | 6.2 | Intersecciones observadas por pareja generan un ciclo |
| CW-12 | Trayectoria completa; portadores identificados sin duplicación | 6.3,6.4 | (2,0,2) no equivale a (2,2,2) por igual final |
| CW-13 | Vacuidad explicitada; existencia no inferida de comparación | 6.1,§4 MIV | I*=∅ vuelve equivalentes las políticas sin acreditar vida |
| CW-14 | Racional exacto, sin suma, pesos ni conversión implícita | 6.5,6.9; perfil | Mejoría en una dimensión y daño en otra da incomparabilidad |
| CW-15 | Daños intermedios y hojas de masa cero permanecen | 7.7,§14 MV | Trayectoria r,u,s viola K1 aunque termina en s |
| CW-16 | Misma política/hoja y referencias de origen en afirmaciones conjuntas | §12 MIV; 10.1 | CAG de pi_a y bienestar de pi_b no forman un logro conjunto |

Los casos son diseños de conformidad, no ejecuciones de un Kernel. La conclusión contractual tiene alcance sobre el modelo finito declarado. La fidelidad del modelo a una población, sistema físico o aplicación real permanece una obligación empírica separada.
