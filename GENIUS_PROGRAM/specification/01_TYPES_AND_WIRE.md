# Tipos y formato normativo FP1

Este archivo fija la representación de entrada y la vinculación de sus campos con los contratos matemáticos. Versión `genius-fp1/1.0`. Todos los bloques enumerados son obligatorios. Un objeto tiene exactamente los campos de su tipo; campos extra, claves JSON duplicadas, tipos incorrectos y referencias nominales inexistentes constituyen INVALID_INPUT. Ningún archivo suministrado se ejecuta como código.

## 1 Tipos básicos

| Tipo | Codificación y significado |
|---|---|
| ID | Cadena ASCII no vacía, patrón `[A-Za-z][A-Za-z0-9_.-]*`; distingue mayúsculas; nominal por espacio de nombres |
| Text | Cadena de escalares Unicode, sin sustitutos Unicode aislados; conserva contenido exactamente |
| Nat | Cadena decimal `0` o `[1-9][0-9]*`; nunca número JSON ni flotante |
| Q | Cadena `n/d`, n entero decimal canónico sin + ni -0 y d entero positivo canónico; gcd(abs(n),d)=1; cero se escribe `0/1` |
| Qnonneg | Q ≥ 0 |
| Bit | Cadena `0` o `1` |
| Set[T] | Array sin duplicados, semántica de conjunto finito; orden no tiene significado |
| List[T] | Array ordenado; posición sí tiene significado |
| Pair[A,B] | Array de longitud dos con tipos A,B; no objeto ambiguo |
| Point | Objeto `{t:Nat,x:ID}` con t≤H y x en states |
| Query | Objeto `{policy:ID,path:List[ID]}`; path es secuencia de etiquetas de rama desde la raíz; tiempo=longitud(path) |
| Cell[T] | Unión etiquetada definida en 06; distingue valor, fuera de dominio e invalidez |

Dos cadenas iguales en espacios de nombres distintos no identifican el mismo objeto. No se deduce estado=información ni identidad organizacional=estado porque sus cadenas coincidan. Las comparaciones racionales son exactas por productos cruzados de enteros; no se redondean. No se imponen límites matemáticos de longitud; los límites de implementación son operativos y se declaran antes del cálculo.

Una `Table[K,V]` se codifica como array de los objetos fila especificados más abajo, con una sola fila por clave K. Incluso filas idénticas repetidas son inválidas. Todas las tablas son cerradas y finitas: sus claves presentes son exactamente su dominio. Una fila omitida en una tabla parcial representa una función no definida allí, no un valor cero ni una instrucción de adivinar. Una tabla obligatoria ausente es un error de formato diferente. Las filas suministradas fuera de un dominio nominal declarado son inválidas, incluso si no se alcanzan.

## 2 Objeto raíz Instance

Campos exactos: `format`, `meta`, `assumptions`, `initialization`, `model`, `policies`, `scenarios`, `functional`, `composition`, `resources`, `generative`, `welfare`, `semantics`, `law`, `constraints`, `selection`.

- `format` es literalmente `genius-fp1/1.0`.
- `meta` tiene `id`, `framework`, `model`, `context`, `condition` (todos ID), `horizon` (Nat), `specification` (literal GENIUS-SPEC-1.0.0), `theory_snapshot` (literal GENIUS-THEORY-2026-09-23-S2), `profile` (literal FP1_FINITE_EXACT), `claim_scope` (literal FORMAL_INSTANCE_ONLY).
- `assumptions`: array de `{id:ID, kind:K, statement:Text, provenance:Text}`. K pertenece a MODEL, INITIALIZATION, INFORMATION, SEMANTIC, CALIBRATION, NORMATIVE, PROBABILITY o SYNTHETIC. IDs únicos. Ninguna etiqueta convierte la afirmación en hecho probado. Toda referencia `basis` de los campos siguientes es Set[ID] no vacío de esta tabla. El expediente conserva estas premisas como ASSUMED_EXTERNAL; SYNTHETIC significa estipulación del ejemplo formal, no observación real.

El digest de entrada es SHA-256 de los bytes UTF-8 exactos recibidos, antes de interpretar JSON. Así dos codificaciones equivalentes pueden tener distinto digest; la equivalencia semántica no se infiere del digest. Dentro de un cálculo todas las claves usan ese mismo digest y `meta`. La salida preserva esos bytes o una referencia incluida con el mismo hash. No necesita acceso a una red para interpretarlos.

## 3 Inicialización y causalidad

`initialization` tiene `{history:ID, condition:ID, x0:ID, i0:ID, basis:Set[ID]}`. `condition` coincide con meta.condition; x0 pertenece a states e i0 a information. Define el testigo formal singleton h0 con b(h0)=condition, s(h0)=x0, i(h0)=i0. La realización en un sistema real depende de basis; no se obtiene por poner nombre a h0. No se transporta silenciosamente otra historia a este testigo.

`model` tiene los campos siguientes:

| Campo | Tipo / fila | Clave y obligación |
|---|---|---|
| states, information, actions, observations, exogenous | Set[ID] | states/information no vacíos; los demás pueden ser vacíos si H=0; deben cubrir todas sus referencias |
| basis, information_basis | Set[ID] no vacío | Interpretación causal y legitimidad informacional, conservadas como premisas |
| executable, admissible | Array de `{t:Nat,x:ID,actions:Set[ID]}` | Clave (t,x), t<H. Conjuntos locales de acciones físicamente ejecutables/admitidas separados |
| transitions | Array de `{t:Nat,x:ID,a:ID,outcomes:List[Outcome]}` | Clave (t,x,a), t<H; cada outcome tiene `{branch:ID,u:ID,next_x:ID,y:ID}`; branch único dentro de fila |
| updates | Array de `{t:Nat,i:ID,a:ID,y:ID,next_i:ID}` | Clave (t,i,a,y), t<H; representa Uγ |

Una fila causal suministrada puede ser vacía como presentación de ausencia conocida de continuación, pero no certifica un nodo que deba continuar. No representa terminación anticipada: FP1 no tiene regla de terminación anterior a H. Una fila ausente es falta de dominio distinta de fila vacía. Las dos impiden certificar ese árbol fuerte. Las tablas de acciones vacías tampoco se convierten en hojas.

`policies` es array no vacío de `{id:ID, decisions:Array[{t:Nat,i:ID,a:ID}]}`, IDs únicos, clave de decisions (t,i), t<H. Es **exactamente Π objetivo**: no es muestra de una familia adicional escondida. El Kernel no puede añadir/eliminar una política para mejorar cobertura. Una misma política usa la misma decisión para igual tiempo e información, aunque estados ocultos difieran. Los dominios de decisiones, acciones locales, filas y updates se verifican en cada ocurrencia alcanzada. No se eliminan ramas por presupuesto, bienestar o probabilidad.

`scenarios` es array no vacío de `{id:ID,inputs:List[ID]}`; IDs y palabras inputs únicos, longitud H, entradas en exogenous. Las hojas se agrupan por la palabra de campos `u` realmente recorrida. La ruta fuerte exige que, para cada política, esas palabras sean exactamente las declaradas y cada fibra tenga una sola hoja. El ID del escenario solo abrevia su palabra. Para H=0 debe haber exactamente un escenario de palabra vacía y cada raíz es una hoja. La correspondencia entre políticas usa la misma palabra exógena; su interpretación física sigue en las premisas del modelo.

## 4 Funcionalidad y suficiencia

`functional` tiene `indices`, `measurements`, `reduction`.

- `indices` es array de `{id:ID, calibration:Array[{raw:Q,value:Q}], basis:Set[ID]}`; IDs únicos y raw único en cada calibración. Cada calibración es una función parcial finita al mismo espacio racional ordenado de esa componente, común a todos los puntos y políticas. Un raw sin calibración deja esa coordenada fuera de dominio.
- `measurements` es array de `{t:Nat,x:ID,index:ID,raw:Q}`, clave (t,x,index). Se admite dominio parcial explícito. El perfil de un punto está definido si todas las componentes del índice común tienen medición y calibración. Índice vacío produce el vector vacío, sin propiedad sustantiva de funcionalidad.
- `reduction` tiene `{ids:Set[ID], rows:Array[{t:Nat,x:ID,reduced:ID}]}`; clave Point, reduced en ids. Representa ψ sobre los puntos alcanzados P, sin alterar los estados usados por MV. Las filas de reducción/medición fuera de P se conservan pero no amplían el alcance del certificado; sus referencias nominales y tiempos siguen válidos.

Se calcula el dominio del perfil completo sobre P y el dominio de ψ restringido a P. Se verifica Df⊆Dψ, saturación de Df en las fibras de ψ y constancia de f en las fibras definidas. Un certificado exacto incluye esos conjuntos, la partición por fibras y los valores descendidos. Fracasar el certificado no invalida perfiles originales disponibles ni concede permiso para comprimir la causalidad. El bloque de comparación funcional usa perfiles terminales en todas las correspondencias de escenario verificadas.

La instancia de MI toma r_i=raw y h_i=calibration_i, con el orden racional usual. En todos los raw medidos alcanzados P donde la calibración esté definida se exige, para cada par a,b, a≤b si y solo si h_i(a)≤h_i(b); se exige además cobertura de todos los raw alcanzados para la guarda fuerte. Es una calibración que preserva y refleja orden, común a todas las políticas. Si falla, los números tabulados siguen siendo números disponibles, pero no constituyen valoraciones funcionales acreditadas de este perfil. Una escala normativa distinta requiere otra especificación explícita.

## 5 Relaciones multiescala y recursos

`composition` tiene `ports`, `rows`, `views` y `basis`.

- `ports` es array de `{id:ID,values:Set[ID],basis:Set[ID]}`; IDs únicos y distintos de la cadena reservada `query`.
- `rows` es array de `{query:Query,values:Array[{port:ID,value:ID}]}`, clave Query. Cada fila contiene exactamente una celda por puerto, con valor en su dominio nominal. La ruta fuerte exige exactamente una fila para cada consulta del árbol de cada política, incluidas raíces y hojas; no filas para consultas inexistentes.
- `views` es array de `{id:ID,columns:Set[ID]}` con IDs únicos. Cada columna es un puerto o `query`; la unión de columnas debe cubrir todos los puertos y query. Un array de vistas vacío falla esa cobertura (aunque haya cero puertos, queda query).
- `basis` es Set[ID] no vacío que identifica el significado de la relación y los puertos.

Para cada política por separado se forma Rπ de filas completas, usando Query como valor nominal de la columna query. Cada vista se calcula como proyección de Rπ sobre sus columnas, eliminando duplicados de la proyección. La unión natural identifica columnas compartidas por nombre/tipo, no por coincidencia accidental de valores de puertos diferentes. Se comprueba igualdad de conjuntos entre Rπ y la unión natural de TODAS sus proyecciones. Una relación global vacía no acredita realizabilidad; MV aporta esa obligación. Datos de procedencia no se añaden a un observable reducido para hacer trivial la suficiencia.

La correspondencia con MII fija el escenario relacional w=κπ en cada relación por política y trata Query como un puerto observable adicional. Todas las proyecciones conservan ese w fijo implícito, aunque alguna pueda omitir la columna query. Así no se mezclan políticas para reconstruir una relación ni se altera la definición fuente de proyección que conserva w.

`resources` tiene `kinds`, `demands`, `values` y `basis`.

- `kinds`: array de `{id:ID,unit:ID}`; IDs únicos.
- `demands`: array de `{id:ID,resource:ID,unit:ID,basis:Set[ID]}`; IDs únicos; resource existe y unit coincide con la unidad de ese recurso. Cada ID representa una demanda física identificada. La exactitud de esa identificación en el mundo es una premisa, no una inferencia del nombre.
- `values`: array de `{query:Query,demand:ID,value:Qnonneg}`, clave (Query,demand). Todos los IDs de demanda se consideran aplicables en todas las consultas: demanda ausente se declara con valor cero explícito; omisión de fila es dato fuera de dominio. Ninguna fila refiere consulta inexistente.
- `basis`: Set[ID] no vacío.

Para cada consulta y recurso se suman UNA vez las demandas de ese recurso. La suma está definida si todas esas celdas están definidas; suma de familia vacía es cero. Presupuestos se declaran en constraints. No se suman valores entre tiempos ni se ponderan por probabilidad.

## 6 Organización y CAG

`generative` tiene `native_ids`, `common_ids`, `meaning_atoms`, `native_meaning`, `common_meaning`, `native_order`, `common_order`, `identity`, `translation`, `recipe`, `mode`, `basis`.

- Los tres primeros son Set[ID]. Firmas nativas y comunes se identifican por igualdad de ID: son representaciones ya cocientadas. No se identifica equivalencia causal ni de desempeño.
- Cada meaning es array de `{identity:ID,atoms:Set[ID]}` con clave identity en su alfabeto; atoms no vacío y contenido en meaning_atoms. Los mapas pueden ser parciales; cobertura requerida se comprueba antes de evaluar receta. Igualdad de significados entre IDs diferentes no los fusiona automáticamente.
- Cada order es Set[Pair[ID,ID]] sobre su alfabeto. Las matrices DEBEN ser reflexivas y transitivas en el alfabeto declarado; simetría/antisimetría no se exigen. Un orden declarado no preorden produce invalidez de ese componente, no reparación automática.
- `identity` es array de `{t:Nat,x:ID,native:ID}`, clave Point. `translation` es array de `{native:ID,common:ID}`, clave native. Mapa compuesto a identidad común: g(t,x)=translation(identity(t,x)). Es una subclase de la traducción sobre estados de S1. No se presume inyectividad ni transporte de leyes.
- Para las identidades nativas alcanzadas y traducidas requeridas, meaning_native(n)=meaning_common(T(n))≠∅. Para hold/acc se comprueba además, para TODOS los pares de identidades nativas alcanzadas requeridas, n≤m iff T(n)≤T(m). Esta guarda es más fuerte que comprobar únicamente los pares efectivamente usados por una ventana; su alcance restrictivo se declara. Para att no se usa conservación, pero las matrices declaradas siguen debiendo ser preórdenes.
- `recipe` es `{kind:"att"}` o `{kind:"acc"}` o `{kind:"hold",length:Nat}`. `mode` es possible o robust. `basis` identifica el propósito, significado y conservación.

El contrato finito comprueba todas las identidades requeridas en todas las realizaciones, incluso después de una pérdida que interrumpe acc. El origen disponible se conserva aunque no esté definido el repertorio futuro. La receta se evalúa sobre trazas comunes ANTES de unión/intersección. Por política, CAG={g0}∪logros; adicional=logros\{g0}. CAG incluye identidades completas aparecidas, no todas sus suborganizaciones. Los testigos conservan política, hoja, tiempo y, para hold, ventana; los de acc conservan la cadena correspondiente.

## 7 Bienestar

`welfare` tiene `carriers:Set[ID]`, `dimensions:Array[{id:ID,basis:Set[ID]}]`, `existence:Set[{t:Nat,carrier:ID}]`, `applicability:Set[{t:Nat,carrier:ID,dimension:ID}]`, `values:Array[{query:Query,carrier:ID,dimension:ID,value:Q}]` y `basis:Set[ID]`.

IDs de dimensions únicos. Cada celda applicable requiere existencia de ese portador en ese tiempo y referencias nominales correctas. Cada medición exige consulta real y su tiempo derivado, existencia y aplicabilidad; clave (Query,carrier,dimension). Una medición fuera de esos soportes es inválida, no dato simplemente ausente. Los valores ya están en la escala racional común especificada por basis de cada dimensión; no se recalibran por política.

El reloj de cada hoja es {0,…,H}, incluso donde existence es vacío. La plantilla existence/applicability es GLOBAL y se usa en todas las políticas y escenarios. Las mediciones pueden faltar como dominio parcial; la ruta fuerte exige todas las celdas aplicables de cada ocurrencia. Se conserva el dominio de medición como conjunto propio, aunque en ruta fuerte coincida con aplicabilidad. Una misma ocurrencia compartida por hojas usa la misma medición, sin duplicar portador por vista/escala. La comparación es producto por escenario, tiempo, portador y dimensión, en ese soporte común. Soporte vacío da equivalencia vacía y no acredita vida ni existencia.

## 8 Semántica y ley

`semantics` tiene `states:Set[ID]`, `references:Array[{leaf:Query,states:Set[ID]}]`, `task:Array[{state:ID,value:Bit}]`, `protocol` (literal FP1_EXACT_ENUM_V1), `basis:Set[ID]`.

References es función parcial por hoja COMPLETA del árbol; sus conjuntos presentes deben ser no vacíos y subconjuntos de states. Task es función parcial por state. Una referencia vacía suministrada es inválida. Una referencia omitida es fuera de dominio; no se infiere referencia a partir de la tarea o de un veredicto favorable. El lector exacto obtiene completaciones del árbol, calcula la unión de TODAS las referencias si están definidas y verifica cobertura/dominio/constancia como describe 04. No se suministran veredictos ni certificados decisivos como sustitutos de esas comprobaciones.

`law` tiene `rows:Array[{query:Query,weights:Array[{branch:ID,mass:Qnonneg}]}]` y `basis:Set[ID]`.

Clave Query no terminal. Cada fila presente cubre EXACTAMENTE las etiquetas de resultados del nodo, sin duplicados, y suma uno. Se valida incluso en nodo de masa cero. Raíz tiene masa uno. Fila ausente en nodo de masa positiva impide una ley completa; fila ausente en nodo de masa cero permite asignar masa cero a sus hijos, sin inventar condicionales. Una hoja no puede tener fila de ley. Todas las hojas/ramas permanecen en el modelo. En H=0 la única masa es uno y rows debe ser vacío.

La columna weights.branch es una declaración de soporte de la ley que se coteja con el soporte causal, no una referencia nominal global de la validación inicial. Si es un ID léxicamente válido pero ajeno a los hijos del nodo, o si omite un hijo, la fila produce LAW_INVALID con presentación estructural válida. Una suma distinta de uno produce el mismo diagnóstico. En cambio un branch de tipo incorrecto, una clave duplicada, una masa negativa (viola Qnonneg), una Query probadamente inexistente o una fila en una hoja constituyen error estructural. Esta distinción específica prevalece sobre la regla general de referencias nominales del encabezado.

La ley se vincula a ocurrencias (política,path), no solo a estado: dos ocurrencias no se fusionan por compartir estado. Una fila inválida produce LAW_INVALID y bloquea cálculos probabilísticos dependientes, sin borrar las ejecuciones y evaluaciones semánticas disponibles.

## 9 Restricciones y selección

`constraints` es array de restricciones con IDs únicos, cada una de uno de estos tipos cerrados:

- `{id:ID,kind:"resource_budget",resource:ID,bound:Qnonneg,basis:Set[ID]}`: todas las consultas de cada política, raíz incluida; unidades del recurso; exige demanda total≤bound.
- `{id:ID,kind:"task_all",scope:"ALL_NODES"|"LEAVES",basis:Set[ID]}`: exige veredicto V=1 en todas las consultas del alcance de cada política, sin usar probabilidades para omitir consultas nulas.

El juicio H_j es 1 con cobertura positiva completa, 0 si existe refutación certificada, y fuera de dominio si no se puede certificar ninguna. Una refutación puede coexistir con otras consultas no evaluables: mantiene diagnósticos completos. No equivale a evaluar una conjunción parcial convencional fuera de su dominio. Restricciones vacías hacen factibles todas las políticas respecto de esa lista, sin acreditar condiciones nunca declaradas. La decisión usa el mismo constraint set para toda Π.

`selection` es `{mode:"none"}` o `{mode:"unique"}` o `{mode:"priority",order:List[ID],basis:Set[ID]}`. Priority exige una permutación exacta de Π; la lista constituye una preferencia adicional explícita. None no selecciona aun con frontera singleton. Unique selecciona únicamente si la frontera EXHAUSTIVE es singleton. Priority elige el primer elemento de su orden que esté en una frontera EXHAUSTIVE no vacía. En una frontera RELATIVE ningún modo selecciona para el problema completo. No se deduce prioridad del orden de llegada, orden alfabético ni orden de arrays que son Set.

## 10 Referencias a consultas y validación cruzada

Query es válida si la política existe y el prefijo de branchs recorre resultados reales de su árbol. Las tablas sobre consultas se cotejan después de expandir causalidad, nunca dando por válida una rama porque una tabla la nombre. Si la causalidad es incompleta y no permite decidir si una referencia es válida, esa validación queda NOT_EVALUATED; no se elimina la referencia ni se la declara inexistente. La ruta fuerte no está acreditada. Referencias a una rama probadamente inexistente son inválidas.

Todos los objetos recibidos permanecen congelados durante una evaluación. Dos puntos con igual (t,x) comparten las mediciones funcionales y la identidad generativa por definición de sus tablas. Bienestar, ley y referencias de tarea se vinculan a ocurrencias, con los alcances históricos correspondientes. El InputID de una tabla no demuestra fidelidad de su interpretación: la conclusión siempre es condicional a las premisas explícitas.
