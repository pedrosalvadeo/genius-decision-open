# Salida, verificadores y diagnósticos FP1

Normativo. Los tipos ID, Nat, Q, Query, Point, Set y List son los de 01. Los resultados nunca sustituyen el Input original; todo certificado se verifica contra sus bytes y digest. F2 deberá exponer una operación de evaluación y otra de comprobación de un resultado/certificado recibido. Los nombres de funciones, CLI, lenguaje y transporte de proceso se deciden en F2; no cambian los objetos descritos aquí.

La unidad portable de una evaluación consta de dos archivos inseparables: `input.json` con los bytes UTF-8 originales exactos y `result.json` con Result. El hash del primero debe coincidir con input_digest del segundo. Estos nombres se aplican dentro de cada carpeta de evaluación; no requieren un campo extra de Result. Un certificado transferido sin ese Input es incompleto y el verificador lo rechaza. Un proceso puede recibir los dos objetos por su interfaz local, pero debe poder exportar esa misma pareja.

## 1 Objeto de salida y estados ortogonales

Un `Result` JSON tiene exactamente:

| Campo | Tipo / significado |
|---|---|
| format | Literal `genius-fp1-result/1.0` |
| input_digest | Cadena de 64 hex minúsculos, SHA-256 de bytes de entrada |
| specification | Literal `GENIUS-SPEC-1.0.0` |
| execution | Objeto `{status,limits,progress}` definido abajo |
| presentation | `VALID`, `INVALID` o `UNRESOLVED` |
| diagnostics | Set[Diagnostic] |
| checks | Set[Check] con IDs únicos |
| policies | Array de PolicyResult, como máximo una por ID recibido |
| decision | Cell[Decision] |
| integration | Cell[IntegrationCertificate] |

`execution.status` es `COMPLETE`, `LIMITED` o `ERROR`. Limits es array de `{name:Text,bound:Nat}` con nombres únicos y límites operativos aplicados; vacío significa que no se impuso límite artificial, no memoria infinita. Progress es `{completed_policies:Set[ID],expanded_nodes:Nat}`; expanded_nodes cuenta ocurrencias creadas y procesadas, no estados únicos, y no afirma completitud por sí solo. En COMPLETE todo chequeo obligatorio y toda política objetivo se han intentado; puede haber dominio parcial o componente inválido. En LIMITED/ERROR no se produce selección ni certificado de integración, aunque se puedan conservar datos ya certificados.

Presentation INVALID se reserva para sintaxis, estructura, claves, tipos y referencias imposibles. En ese caso policies=[], decision e integration son BLOCKED. Presentation UNRESOLVED significa que no terminó o que una referencia no se puede resolver por causalidad incompleta, conservando la razón exacta. Un fallo matemático de guarda (ψ insuficiente, ley no normalizada, orden no transitivo) tiene presentación tipada y Check FAIL; no se convierte en un error de JSON. Esos componentes se bloquean donde se indica, sin borrar otros valores independientes.

La implementación no confunde siete preguntas: ¿la presentación es válida?, ¿el componente cumple sus guardas?, ¿el objeto pertenece al dominio?, ¿se determinó esa pertenencia?, ¿qué valor tiene?, ¿terminó el cómputo?, ¿qué objetivo cubre? Ningún estado de una pregunta sustituye el de otra.

## 2 Celdas y referencias verificables

`Cell[T]` es exactamente una de estas variantes:

- `{state:"DEFINED",value:T,checks:Set[ID]}`: valor en el dominio del objeto nombrado; checks referencia comprobaciones PASS que acreditan sus guardas. Un verificador recalcula valor y cobertura.
- `{state:"OUTSIDE_DOMAIN",reasons:Set[ID],checks:Set[ID]}`: pertenencia negativa establecida para ese objeto parcial, reasons no vacío refiere Diagnostic; incluye los testigos que prueban la guarda fallida. No tiene value.
- `{state:"BLOCKED",reasons:Set[ID]}`: no se ha establecido valor ni pertenencia negativa por dependencia inválida/incompleta, límite o error. No tiene value. BLOCKED no equivale a OUTSIDE_DOMAIN.

Un objeto numérico disponible puede existir mientras el certificado de su calibración falla. Se puede conservar la medición en Input y el diagnóstico, pero no etiquetar como DEFINED la valoración acreditada que exige esa calibración. Un certificado de suficiencia en cambio tiene valor booleano comprobado: Check FAIL informa insuficiencia, no la inexistencia de f original. Cada celda nombra el objeto contractual al que se refiere; no existe un «valor global indefinido» que borre todos los demás.

`DatumRef` es `{document:"INPUT"|"OUTPUT",pointer:Text}`. Pointer es una ruta JSON Pointer estándar (`~0` representa ~, `~1` representa /; índices decimales de arrays), relativa a los objetos completos y ligada a input_digest. No se usa como promesa de verdad: debe resolver y el verificador recalcula su contenido. Un Check no puede justificarse circularmente por una referencia a sí mismo; toda cadena de apoyo termina en Input o en un constructor anterior del DAG. Una comprobación por enumeración puede citar el objeto tabla completo en vez de repetir cada celda.

`Check` tiene `{id:ID,rule:ID,outcome:"PASS"|"FAIL"|"UNDETERMINED",policies:Set[ID],queries:Set[Query],points:Set[Point],support:Set[DatumRef],detail:Text}`. Rules son G01–G15, o los subtipos `INPUT_TYPES`, `QUERY_REFERENCE`, `CAUSAL_NODE`, `SCENARIO_MAP`, `CALIBRATION`, `FSUFF`, `RELATIONAL_JOIN`, `RESOURCE_SUM`, `GEN_ORDER`, `GEN_TRANSLATION`, `CAG_RECIPE`, `WELFARE_COVERAGE`, `SEM_UNION`, `DECISIVE_SET`, `LAW_ROW`, `LAW_MASS`, `VPROB`, `HARD_RESOURCE`, `HARD_TASK`, `PAIR_COMPARISON`, `FRONTIER`, `SELECTION`. Su significado es la operación especificada en 01–05, no una afirmación libre a interpretar por detail. Si una regla no aplica a un objeto no se crea Check para ese objeto. Un Gxx resume exactamente todas sus obligaciones, y no pasa por ausencia de subchequeos requeridos.

`Diagnostic` tiene `{id:ID,code:ID,component:ID,policies:Set[ID],queries:Set[Query],points:Set[Point],input_refs:Set[DatumRef],message:Text}`. Los refs de un Diagnostic son solo INPUT. IDs de diagnóstico/check/certificado son nominales generados y no constituyen prioridades. component pertenece a INPUT, CAUSAL, FUNCTIONAL, COMPOSITION, RESOURCE, CAG, WELFARE, EVIDENCE, LAW, HARD, DECISION o EXECUTION. Se conserva al menos un testigo reproducible de cada clase de fallo y el conjunto completo de ubicaciones faltantes para toda cobertura que se afirme haber examinado exhaustivamente.

### Objeto de cada celda y fallos de guarda

| Situación decidida, con cómputo completo | Celda y estado obligatorio |
|---|---|
| π(t,i) tabulada, pero acción no ejecutable/admisible | causal.nodes.action DEFINED (valor de π); causal.complete OUTSIDE_DOMAIN y Check causal FAIL |
| π(t,i) ausente, o nodo terminal | action OUTSIDE_DOMAIN, con motivo distinguido |
| Medición o calibración parcial ausente | points.profile OUTSIDE_DOMAIN; terminal OUTSIDE_DOMAIN si la afecta |
| Calibración numérica presente pero no conserva/refleja orden | points.profile puede ser DEFINED como vector evaluado; terminal BLOCKED como valoración acreditada, CALIBRATION FAIL |
| ψ insuficiente o join con fila espuria | reduction/composition OUTSIDE_DOMAIN como certificados parciales; perfiles originales conservados |
| Identidad, traducción o significado requerido ausente en tabla parcial válida | cag/additional OUTSIDE_DOMAIN; origen independiente cuando esté definido |
| Preorden inválido, significado traducido discrepante o transporte de orden falso | cag/additional BLOCKED por componente no acreditado, Check FAIL |
| Celda de bienestar aplicable ausente | celda y perfil afectado OUTSIDE_DOMAIN |
| Falta referencia Sem, Φ parcial o valores mixtos con árbol completo | sem o verdict OUTSIDE_DOMAIN según guarda, conservando lectura si existe |
| Árbol incompleto y conjunto de completaciones aún no determinado | sem/verdict dependientes BLOCKED; un certificado de futuro completo no se inventa |
| Fila de ley suministrada inválida | masses/vector/pvs BLOCKED, LAW_INVALID |
| Filas válidas pero falta una fila en masa positiva | vector/pvs OUTSIDE_DOMAIN de la ley determinada de FP1, LAW_UNDETERMINED; masas ya determinadas se conservan |
| Ley válida con masa indeterminada positiva | vector DEFINED, pvs OUTSIDE_DOMAIN |
| Presupuesto excedido con testigo legítimo | hard.value DEFINED 0 aun con otros faltantes |
| Sin refutación y cobertura parcial conocida de hard | hard.value OUTSIDE_DOMAIN si se terminó la evaluación; BLOCKED si el cómputo no terminó o su scope es desconocido |
| Selección none, única no singleton, frontera vacía o relativa | selection OUTSIDE_DOMAIN con motivo específico, no error |
| Límite o error interno antes de resolver objeto | celda afectada BLOCKED, sin inferir dominio negativo |

En esa fila, «inválida» significa soporte de hijos declarado incorrecto o suma distinta de uno tras pasar tipos/estructura, según la excepción explícita de 01 §8. Un ID léxico de rama extra no es UNKNOWN_REFERENCE global. Duplicados, masa negativa, tipo incorrecto y Query imposible se rechazan antes como presentación INVALID; no se reclasifican como indeterminación probabilística.

La tabla fija la distinción entre una función tabulada y la valoración acreditada que la consume. Los objetos cuya presentación matemática es inválida bloquean a sus consumidores; una función parcial válida permite decidir pertenencia negativa a su dominio. Los testigos de fallo no desaparecen por usar BLOCKED.

## 3 Expediente por política

`PolicyResult` tiene exactamente `{policy,causal,functional,composition,resources,generative,welfare,evidence,probability,hard}`. Policy es ID. Cada campo restante tiene el siguiente tipo cerrado. Toda tabla derivada tiene claves únicas. Los conjuntos vacíos matemáticamente legítimos usan DEFINED con array vacío; no se sustituyen por OUTSIDE_DOMAIN.

### Causal

`causal` es `{complete:Cell[Bit],nodes:Array[Node],leaves:Set[Query],scenarios:Cell[ScenarioMap]}`. Node tiene `{query:Query,t:Nat,x:ID,i:ID,action:Cell[ID],outcomes:Array[Edge]}`. Edge tiene `{branch:ID,u:ID,next_x:ID,y:ID,next_i:Cell[ID],child:Query}`. Action representa exactamente el valor parcial π(t,i), no una acción ya acreditada como ejecutable/admisible. Una acción tabulada se conserva DEFINED aunque sus guardas causales fallen; complete y los Check expresan ese fallo. Next_i representa el valor parcial U, y su existencia tampoco acredita por sí sola toda la arista. Un nodo terminal t=H tiene action OUTSIDE_DOMAIN con motivo TERMINAL_NO_ACTION y outcomes=[]; no es error. Si no se puede decidir acción o actualización se conservan sus motivos; un child cuya actualización es desconocida no se presenta como Node completo. Los prefijos completos conocidos se conservan, sin inventar hojas a H. Complete es DEFINED 1 exactamente para árbol completo acreditado; si una condición necesaria falla, OUTSIDE_DOMAIN con motivo. Leaves contiene SOLO nodos terminales efectivamente construidos. ScenarioMap es array de `{scenario:ID,leaf:Query}` con cobertura y unicidad exigidas.

### Funcionalidad y composición

`functional` tiene `{points:Array[{point:Point,profile:Cell[FunctionalVector]}],terminal:Cell[FunctionalTerminal],reduction:Cell[ReductionCertificate]}`.

Points enumera exactamente una fila por punto distinto (t,x) de los Node construidos de ESA política, también si el árbol está incompleto. Su profile es el vector numérico f evaluado por las tablas; sus checks acreditan medición y aplicación, y no afirman calibración ordinal hasta que CALIBRATION pase. Terminal sí es la valoración acreditada para comparación y requiere esa guarda común.

FunctionalVector es array de `{index:ID,value:Q}` exactamente para todos los índices. FunctionalTerminal es array de `{scenario:ID,profile:FunctionalVector}` exactamente para Xi. ReductionCertificate tiene `{scope:Set[Point],domain_f:Set[Point],domain_psi:Set[Point],fibers:Array[{reduced:ID,points:Set[Point],value:Cell[FunctionalVector]}]}`. Fibers es partición del dominio ψ restringido a scope; value fuera de dominio solo para fibras totalmente fuera de Df. Se requiere Df⊆Dψ y saturación antes de emitir ese certificado. El registro por política puede repetir el certificado global idéntico, cuya scope es el P completo común; no puede cambiar su alcance silenciosamente. Si hay otras políticas incompletas el certificado global queda BLOCKED; los perfiles locales completos permanecen utilizables según 05.

`composition` es Cell[CompositionCertificate], con `{queries:Set[Query],views:Array[{id:ID,rows:Array[ProjectedRow]}],join:Array[ProjectedRow]}`. ProjectedRow tiene `{query:Query|null,values:Array[{port:ID,value:ID}]}`. Query es null exactamente cuando la vista no contiene esa columna; values contiene exactamente sus puertos. En join siempre hay query y todos los puertos. El verificador deriva R de Input, las proyecciones, deduplicación, join y cobertura; no confía en equality=true. Join puede resultar exponencial: un límite no permite certificar igualdad.

### Recursos, CAG y bienestar

`resources` es array de `{query:Query,resource:ID,total:Cell[Qnonneg]}` que cubre cada consulta construida y cada recurso. El resultado de suma se recalcula desde TODAS las demandas de ese recurso; los testigos distinguen falta de una celda de una suma mayor al presupuesto.

`generative` tiene `{origin:Cell[ID],traces:Array[{leaf:Query,identities:Cell[List[ID]],achievements:Cell[Set[ID]]}],cag:Cell[Set[ID]],additional:Cell[Set[ID]],witnesses:Array[CAGWitness]}`. Identities tiene longitud H+1 en traza completa; achievements usa receta/mode de Input. Cada CAGWitness tiene `{identity:ID,leaf:Query,t:Nat,window:List[Nat]}`. Att usa window=[t]; hold usa [t,…,t+length]; acc usa [0,…,t]. Las identidades logradas se toman en t≥1; origen se acredita separadamente con t=0 y no requiere CAGWitness futuro. Witnesses enumera TODOS los tiempos acreditantes y sus ventanas/cadenas por identidad y hoja de las achievements definidas, no solo los logros que sobreviven a la operación robusta. Para mode possible cada logro resultante tiene así sus testigos en las hojas que lo logran; para robust se comprueba que cada logro resultante tenga testigos en todas las hojas. El verificador además recalcula el conjunto completo de logros de cada traza, de modo que los testigos positivos no oculten logros ni hojas. Additional elimina solo el origen del conjunto de logros. Si repertorio futuro está fuera de dominio, cag y additional no se emiten como conjuntos vacíos; origin puede seguir disponible.

`welfare` es `{cells:Array[{query:Query,carrier:ID,dimension:ID,value:Cell[Q]}],profile:Cell[WelfareProfile]}`. Cells cubre exactamente las celdas aplicables de consultas construidas. WelfareProfile es array de `{scenario:ID,t:Nat,carrier:ID,dimension:ID,value:Q}` con exactamente Xi×soporte aplicable, recuperando la consulta prefijo correcta. El reloj y existencia se mantienen en Input aun en tiempos sin celdas aplicables. No se duplica una medición compartida por ramas; solo se referencia en el perfil de cada escenario.

### Evidencia y probabilidad

`evidence` es array de `{query:Query,sem:Cell[SemanticRead],verdict:Cell[DecisiveCertificate]}` para toda consulta construida. SemanticRead tiene `{leaves:Set[Query],references:Array[{leaf:Query,states:Set[ID]}],states:Set[ID]}`. Cada conjunto de states presente es no vacío; leaves se recalcula del árbol completo, references lo cubre exactamente, states es la unión. El certificado tiene `{id:ID,kind:"DECISIVE_SET",query:Query,protocol:"FP1_EXACT_ENUM_V1",read:SemanticRead,A:Set[ID],value:Bit,task_rows:Array[{state:ID,value:Bit}]}`. El generador usa A=read.states; el verificador de un certificado externo admite cualquier A que satisfaga §4 de04, con task_rows exactamente A. El certificado es ligado a digest por su Result envolvente. Nunca se acepta aislado sin Input y digest.

`probability` es `{masses:Array[{query:Query,mass:Cell[Qnonneg]}],partition:Cell[LeafPartition],vector:Cell[MassVector],pvs:Cell[Qnonneg]}`. LeafPartition tiene `{positive:Set[Query],negative:Set[Query],undecided:Set[Query]}` y cubre solo hojas del árbol completo. MassVector tiene `{success:Qnonneg,failure:Qnonneg,undecided:Qnonneg}` de suma uno. Partition depende de semántica válida, no de que exista ley. Masses cubre todas las consultas construidas; con ley inválida no se usan masas aparentemente correctas para certificar vector o pvs. Pvs solo definida con ley y vector legítimos y undecided=0; se comprueba además 0≤pvs≤1. Un error estructural de referencias no se clasifica como hoja undecided; una referencia ausente en función parcial válida sí.

### Restricciones

`hard` es array de `{constraint:ID,value:Cell[Bit],scope:Cell[Set[Query]],known_scope:Set[Query],checked:Set[Query],violations:Set[Query],missing:Set[Query]}`; una fila por restricción recibida. Scope es DEFINED Q o F según regla cuando el árbol es completo; known_scope coincide entonces con su valor. Con árbol incompleto scope es BLOCKED y known_scope contiene únicamente consultas ya legitimadas dentro del alcance (para LEAVES solo terminales reales a H). Checked contiene todas las consultas de known_scope con juicio local determinado, violations las de juicio0, missing las restantes. Los conjuntos checked y missing particionan known_scope; violations⊆checked. Para valor1 se exige scope DEFINED y missing=violations=vacío. Para valor0 basta violations no vacío, pero se conservan missing. Para fuera de dominio se exige scope DEFINED, violations vacío y missing no vacío. Si scope está BLOCKED, hard puede ser DEFINED 0 solo con testigo negativo ya legitimado en known_scope; de lo contrario hard queda BLOCKED. El expediente conserva Check UNDETERMINED para cobertura y no emite conclusión positiva. Los datos no examinados por límite permanecen BLOCKED, no OUTSIDE_DOMAIN.

## 4 Decisión y certificado de integración

Decision tiene `{target:Set[ID],B:Set[ID],C:Set[ID],feasible:Set[ID],failed:Set[ID],unknown:Set[ID],omitted:Array[{policy:ID,reasons:Set[ID]}],pairs:Array[PairComparison],frontier:Set[ID],dominators:Array[{policy:ID,by:Set[ID]}],coverage:"EXHAUSTIVE"|"RELATIVE",selection:Cell[ID]}`. Target=Π. Feasible,failed,unknown particionan Π según H. B es exactamente el bloque de05, C=B∩feasible. Omitted cubre Π\C: razones distinguen falta de valoración y restricción fallida/indeterminada. Frontier contiene todos los maximales de C. Dominators tiene una fila por C\frontier y `by` no vacío de dominadores estrictos en C; puede listar uno o más, sin exigir listarlos todos. Para maximal, la matriz completa prueba ausencia, no una frase.

PairComparison tiene `{left:ID,right:ID,functional:Bit,cag:Bit,welfare:Bit,pvs:Bit,weak:Bit,strict:Bit}` para EXACTAMENTE B×B. Cada bit afirma left≥right para su criterio; weak es su conjunción, strict=weak(left,right) AND NOT weak(right,left). Dos comparaciones falsas son incomparabilidad definida; equivalencia requiere ambas weak1. Pares fuera de B no aparecen con false: sus dominios faltan y se explican en omitted o diagnósticos. Las direcciones son racional≥, inclusión CAGright⊆CAGleft y producto de coordenadas terminales/históricas; no suma, cardinalidad ni votación.

IntegrationCertificate tiene `{id:ID,profile:"FP1_FINITE_EXACT",theory_snapshot:"GENIUS-THEORY-2026-09-23-S2",target:Set[ID],guards:Set[ID],selection_check:ID,assumptions:Set[ID],claim:"CONDITIONAL_FORMAL_INSTANCE"}`. Guards referencia exactamente un resumen PASS para cada G01–G15; cada resumen remite a todas sus obligaciones recomputables. Selection_check referencia un Check SELECTION PASS posterior a cobertura: acredita el valor seleccionado o la ausencia correcta de selección según regla y dominio. G15 solo acredita frontera/cobertura y no depende del selector. Assumptions referencia TODA la tabla de premisas del Input (incluidas las no usadas, sin afirmar acreditarlas). El verificador comprueba la conjunción, cobertura y vinculación de todas las tablas. Un ID de certificado, hash, firma o etiqueta PASS no reemplaza esas comprobaciones. Integration puede estar OUTSIDE_DOMAIN si una guarda falla de modo decidido o BLOCKED si quedan dependencias sin resolver. La aceptación documental de F1 NO es uno de estos certificados de ejecución.

## 5 Catálogo mínimo de diagnósticos

Los códigos siguientes son cerrados para esta versión; `message` añade detalle sin crear nuevas semánticas.

| Códigos | Interpretación |
|---|---|
| INPUT_SYNTAX, INPUT_TYPE, DUPLICATE_KEY, UNKNOWN_FIELD, UNKNOWN_REFERENCE, BAD_TIME, INVALID_VARIANT | Presentación estructural inválida |
| QUERY_UNRESOLVED | No se conoce si la consulta existe por dependencia causal incompleta |
| POLICY_MISSING, ACTION_DOMAIN_MISSING, ACTION_NOT_EXECUTABLE, ACTION_NOT_ADMISSIBLE, TRANSITION_MISSING, TRANSITION_EMPTY, UPDATE_MISSING | Nodo causal no acreditado para continuar |
| TERMINAL_NO_ACTION | Ausencia esperada de acción a H |
| SCENARIO_COVERAGE, SCENARIO_MULTIPLE | Imagen de palabras incorrecta o fibra múltiple |
| FUNCTION_MISSING, CALIBRATION_MISSING, CALIBRATION_ORDER | Función/calibración ausente o violación de orden |
| REDUCTION_MISSING, REDUCTION_DOMAIN, REDUCTION_VALUE | Falta de reducción, dominio no saturado o valor no constante |
| COMPOSITION_COVERAGE, COMPOSITION_SPURIOUS | Relación incompleta o join con filas espurias |
| RESOURCE_MISSING | Suma local sin todas sus celdas |
| GEN_IDENTITY_MISSING, GEN_TRANSLATION_MISSING, GEN_MEANING_MISSING, GEN_MEANING_MISMATCH, GEN_ORDER_INVALID, GEN_ORDER_TRANSPORT | Guardas generativas no satisfechas |
| WELFARE_MISSING | Celda aplicable sin medición |
| SEM_REFERENCE_MISSING, TASK_OUTSIDE_DOMAIN, VERDICT_MIXED | Sem/V fuera de dominio parcial legítimo |
| LAW_INVALID, LAW_UNDETERMINED, POSITIVE_UNDECIDED_MASS | Ley inválida, fila positiva ausente o PVS sin dominio |
| HARD_VIOLATION, HARD_UNDECIDED | Refutación o dominio no decidido de restricción |
| COMPARISON_GUARD, RELATIVE_COVERAGE, NO_FEASIBLE_POLICY | Comparabilidad/alcance/ausencia de factibles acreditada |
| SELECTION_DISABLED, SELECTION_NOT_UNIQUE, SELECTION_EMPTY, SELECTION_SCOPE | Regla sin valor; no constituyen error de evaluación |
| DEPENDENCY_BLOCKED, COMPUTATION_LIMIT, INTERNAL_ERROR, CERTIFICATE_REJECTED | Bloqueo operativo o rechazo del verificador |

Una tabla partial conocida se puede evaluar completamente y producir OUTSIDE_DOMAIN con todos sus faltantes. Un cómputo no terminado produce BLOCKED. Una igualdad que falla con testigo es FAIL, no UNDETERMINED. Los validadores deben informar el error con la misma precisión con que prometen el éxito.

## 6 Conformidad de implementación

Con entrada dentro de G01–G15 y recursos suficientes, el Kernel debe devolver COMPLETE, las valoraciones y frontera exactas y el certificado fuerte verificable. Rechazar sistemáticamente entradas válidas no constituye implementación conforme. Con datos parciales tipados, debe conservar los resultados independientes y motivos de dominio especificados; con entrada estructural inválida, rechazarla; con límite, declarar LIMITED. El verificador acepta los certificados válidos de esta gramática y rechaza alteraciones de hojas, dominios, signos, reglas, cobertura o digest.

El orden de arrays Set o de IDs generados no es parte del oráculo. Los tests comparan conjuntos, funciones y racionales exactos, y validan referencias de evidencia. La carpeta conformance contiene casos DISEÑADOS y una proyección de resultado sintético; F1 no declara ejecutado este contrato de Kernel.
