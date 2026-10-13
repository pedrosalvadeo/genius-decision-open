# Trazabilidad F4 — contrato, adaptador y evidencia

Autoridad: [CONTRACT P01–P09](CONTRACT.md), [Specification 00–06](../GENIUS_PROGRAM/specification/00_SPECIFICATION.md), [invariantes](../GENIUS_PROGRAM/INVARIANTS.md) y mandato F4. Estado: evidencia final examinada, PASS para los alcances indicados. Un nombre de test/diseño o una inspección de código no cuenta como ejecución. La aceptación de fase corresponde al Integrador con auditoría/recepción separadas, no al autor del contrato; esta matriz no concede G4.

## Reportes examinados

| Clave | Evidencia final | Resultado y naturaleza |
|---|---|---|
| A | [AUDIT_FINAL_02/REPORT.json](../validation/audit_runs/AUDIT_FINAL_02/REPORT.json) | 53 casos, 900 checks PASS; oráculos nuevos, proceso externo, sin importar sujeto. Fuentes iguales antes/después. |
| AC | [AUDIT_CONSUMER_FINAL/REPORT.json](../validation/audit_runs/AUDIT_CONSUMER_FINAL/REPORT.json) | 16 casos, 63 checks PASS; auditor distinto del autor del consumidor, peer adversarial sintético, terminación de su proceso y mutación de buffers. Fuentes iguales antes/después. |
| AF | [AUDIT_FAULTS_FINAL/REPORT.json](../validation/audit_runs/AUDIT_FAULTS_FINAL/REPORT.json) | 5 casos, 9 checks PASS; inyección explícita en la API Kernel en el límite con el adaptador. ERROR simulado y umbral real de salida 32 MiB; no fallo real del Kernel ni cálculo de instancia grande. Fuentes iguales antes/después. |
| C | [CONSUMER_CONFORMANCE_04/report.json](../validation/CONSUMER_CONFORMANCE_04/report.json) | C01–C25, 25 casos, 79 aserciones PASS; Node externo, fixture propio, exportación, CLI y controles del consumidor. C23 usa un Result ERROR sintético para probar tratamiento de forma. |
| R | [CONSUMER_REPLAY_02/report.json](../validation/CONSUMER_REPLAY_02/report.json) | 3338 llamadas heredadas F3 PASS: 3336 con identidad completa de respuesta y 2 rechazos de parser declarados. 508 casos de origen, 506 con llamadas. Reproducción de identidad, no nuevo oráculo matemático ni 3338 casos científicos nuevos. Fuentes iguales antes/después. |

Las tres baterías del auditor suman 74 casos/972 checks, sin contar borradores o reproducciones como casos nuevos. Los recuentos de C y R conservan su naturaleza propia y no se suman para fabricar un único tamaño de muestra. Los errores y reparaciones previos se mantienen en los reportes correspondientes.

## Requisito → mensajes → código → test → resultado

Las rutas de código de esta tabla son relativas a protocols/. `Session` está en `genius_protocols/server.py`; parser/blobs/límites están en `genius_protocols/wire.py`. Los IDs AUD4 corresponden al runner [tests/audit_blackbox.py](tests/audit_blackbox.py) y su diseño previo. Tener un ID implementado no implica que haya pasado; los reportes se incorporan al producirse.

| Requisito | Mensaje/propiedad observable | Adaptador | Test o diseño localizado | Evidencia y estado |
|---|---|---|---|---|
| P01 framing y stdout | LF/CRLF, frame malformado recuperable, EOF fragmentado, tamaño y cierre | `serve`; `strict_json` | AUD4-FRM-001; AUD4-CON-012–013; C14 | PASS A/AC/C; A ejerce frame exacto 16 MiB y exceso. |
| P01 UTF-8/JSON estricto | Duplicados desescapados, NaN/Infinity, sustitutos aislados; sin normalizar input | `strict_json`, `_unique_pairs`, `_unicode_scalars` | AUD4-PAR-001–009; AUD4-CON-002/010/012; C19 | PASS A/AC/C para los contraejemplos enumerados. |
| P02 forma/IDs/errores | Request cerrada, ID string/entero seguro/null; correlación | `Session.handle_request`, `valid_id`, `error_response` | AUD4-RPC-001–010; AUD4-REQ-001–003; AUD4-CON-011 | PASS A/AC. |
| P02 batch/notificaciones | Array de respuestas, batch vacío, >16, solo notificaciones, initialize dentro de batch | `Session.handle_payload`, `handle_request` | AUD4-NOT-001, AUD4-BAT-001; AUD4-FAULT-005 | PASS A/AF; inyección en AF para agregado de salida. |
| P03 sesión/compatibilidad | Initialize exacto, versiones/capacidades, repetición, cálculo antes READY | `initialization_result`, `_initialize`, `_compute` | AUD4-NEG-001; AUD4-CON-004–006; C01/C12/C13 | PASS A/AC/C; identidades y rechazo antes de enviar Input. |
| P04 bytes/digest | ByteEnvelope, bits de padding, dos inputs equivalentes con distinto digest; propiedad de bytes exportados | `decode_envelope`, `byte_envelope`; raw a API; consumidor | AUD4-ID-001, AUD4-BLOB-001–006; AUD4-CON-001/007–009; C02/C03/C18/C21/C25; AUD4-CON-016 | PASS A/AC/C; C25 y CON-016 acreditan copia de buffers antes de await, tras reparación conservada. |
| P05 evaluate | Input/result completos; invalidez input sigue Result | `_compute` → `genius_kernel.evaluate` | AUD4-SEM-001–002, AUD4-INP-001–006; C02/C09/C22; R | PASS A/C/R; R conserva naturaleza de reproducción. |
| P05 verify_result | Candidate ligado a Input; rechazo de alteraciones | `_compute` → `genius_kernel.verify_result` | AUD4-RES-001; C02/C03/C11/C22; R | PASS A/C/R, sin atribuir independencia matemática al verificador compartido. |
| P05 verify_certificate | Signos 0/1, superset A, cobertura/dominio/digest | `_compute` → `genius_kernel.verify_decisive_certificate` | AUD4-CER-001; C10/C22; R | PASS A/C/R; certificados de A construidos desde definiciones. |
| P05 parser candidate | SYNTAX antes TYPE, duplicados no destruidos, sin llamar verifier | `strict_json(candidate=True)`, `_compute` | AUD4-CER-002; autor `test_candidate_syntax_precedes_number_type_without_verifier`; F4-ADAPTER-01 | PASS A; autor comprueba además no invocar verifier. R tiene dos rechazos TYPE previstos, no identidad completa de su texto de error. |
| P06 límites | Cinco límites opcionales Nat string; ninguna restricción matemática implícita | `kernel_limits`, `_compute`, `initialization_result` | AUD4-LIM-001–009; C08/C11/C20 | PASS A/C; límites Kernel, input exacto 2 MiB y candidate exacto 8 MiB/excesos. |
| P06 salida demasiado grande | Error RPC, sin Result truncado ni LIMITED falso; IDs de batch | `handle_request`, `handle_payload` | AUD4-FAULT-003–005 | PASS AF: umbral configurado real 32 MiB, exceso y agregado; payload de prueba inyectado, no carga matemática grande. |
| P07 exactitud/identidad | Q>2^53, namespaces homónimos, ocurrencias reconvergentes, Unicode | ByteEnvelope; sin proyección matemática | AUD4-SEM-001; C04/C05; R | PASS A/C/R para los objetos/proyecciones comprobados. |
| P07 estados/cobertura | INVALID/UNRESOLVED/COMPLETE/LIMITED; Cells, verificación INCOMPLETE y RELATIVE | Retorno íntegro de API Kernel | AUD4-SEM-002, AUD4-LIM-008, AUD4-INP-001–006; C06–C09/C11/C24 | PASS A/C con resultados del Kernel real. |
| P07 ERROR | No convertir ejecución ERROR en infactibilidad o fallo RPC | Retorno íntegro de API Kernel; parser consumidor | AUD4-FAULT-002; AUD4-CON-003; C23 | PASS AF/AC/C como inyección o fixture de forma. No se provocó un fallo interno real del Kernel ni se verificó un certificado ERROR sintético. |
| P08 errores/terminación | Códigos exactos, transporte distinto de dominio, aborto de proceso | `ERROR_MESSAGES`, Session, serve; consumidor | AUD4-PAR/REQ/RPC/BLOB/LIM; AUD4-FAULT-001; AUD4-CON-013–015; C14–C17 | PASS A/AF/AC/C; -32603 inducido en AF; terminación, cancelación y timeout contra procesos peer sintéticos identificados. |
| P09 evidencia/límites | Cliente independiente, incompatibilidades, sin claims MCP/A2A | Contrato, adaptador y consumidor | COMPATIBILITY, TRANSPORT_DECISION, A/AC/AF/C/R y recepción | Cobertura técnica documentada; gate/recepción efectivos en documentos raíz. |

`F4-AUD-001` conserva un borrador instrumental que había fijado FAIL antes de comparar valores; la comparación real dio identidad correcta. Su reporte final lo clasifica NO_DEFECT_REPRODUCED. No se cuenta como defecto del adaptador ni se borra el intento anterior. `F4-ADAPTER-01` sí conserva una discrepancia de precedencia en desarrollo, su reparación y controles; no modificó el contrato ni el Kernel.

## Invariantes: conservación y ámbito

Esta tabla cubre el registro normativo mediante grupos de IDs. Un envelope íntegro es mecanismo de conservación, pero su hash por sí solo no verifica obligaciones matemáticas. Los oráculos concretos y reproducciones delimitan la evidencia; no se acredita una segunda implementación matemática completa.

| Invariantes | Obligación de interoperabilidad | Cláusula/método y evidencia | Estado/alcance |
|---|---|---|---|
| INV-01,02,15 | Separar marco/modelo/contexto y namespaces estado/información/organización | P04/P07; evaluate; AUD4-SEM-001, C04, R | PASS para conservación y proyección independiente; no equivalencia nominal inventada. |
| INV-03,04,05,09,31 | Preservar dominio, valor, invalidez, gate y comparación indefinida | P05/P07/P08; evaluate/verifiers; AUD4-SEM-002/INP/LIM, C06–C11, R | PASS para variantes comprobadas; no colapsar a bool/null. |
| INV-06,07,08,16,17,19,38 | Política y testigos compatibles, familias no vacías, recetas y cuantificadores intactos | P07; par input/result completo; R, AUD4-SEM-001/RES-001, C05 | PASS de transporte/identidad y proyecciones indicadas; R no revalida independientemente todos los teoremas. |
| INV-10,11,33,36 | Suficiencia con dominio/saturación/constancia y procedencia separada | P07; evaluate/verifier; R y artefactos F3 enlazados por cada llamada | PASS de conservación heredada; no nuevo algoritmo ni prueba de suficiencia. |
| INV-12,18,21,35 | Criterios e índices fijos; inclusión≠cardinalidad; conservación/reflexión de orden | P07; evaluate/verifier; C04/C05, AUD4-SEM-001, R | PASS de proyecciones y transporte; no puntuación ni conversión normativa. |
| INV-13,14,37 | Relaciones conjuntas, identidad de demanda/unidad y no transporte automático de masas | P07; AUD4-SEM-001 con recurso 1/3; R | PASS para proyección de recurso y conservación heredada; no reducción relacional nueva. |
| INV-20,23 | Reloj/existencia/aplicabilidad/medición e historia completos | P07; AUD4-SEM-002, C06, R | PASS para parcialidad de bienestar y conservación de objetos; no validación empírica de trayectorias. |
| INV-22,30,34,42 | Información legítima, todas las ramas, palabras exógenas y ocurrencias | P07; AUD4-SEM-001/002, C07, R | PASS de reconvergencia/hoja nula/actualización ausente; no equivalencia entre modelos. |
| INV-24,41 | Certificado no vacío, con dominio y cobertura; significado no reemplazado por veredicto | P05/P07; AUD4-CER-001/RES-001, C10, R | PASS: certificados 0/1/superset desde definiciones y mutaciones; no acreditación de premisas externas. |
| INV-25,26,27,43,44 | Ley separada; tripartición; hojas nulas; filas válidas y prefijos no sumados | P07; AUD4-SEM-001/002, AUD4-RES-001, R | PASS para PVS=1 con hoja fallida de masa 0, ley inválida y conservación heredada. |
| INV-28,29,49 | Frontera/cobertura/selección distintas, DAG sin circularidad y sin desempate por ID | P07; AUD4-SEM-002/RES-001, C05/C06/C24, R | PASS para alcance/selección y transporte; selector heredado, no regla nueva ni prueba general de equivarianza. |
| INV-32 | Presentación efectiva y límites operativos sin cambiar problema | P01/P06/P08; AUD4-LIM/FRM/FAULT, AUD4-CON-013–015, C08/C11/C14–C16 | PASS para límites/errores declarados; no promesa de recursos ilimitados. |
| INV-39,40 | Comparación anónima/matching requiere contrato y evidencia propios | P09/COMPATIBILITY | NOT_SUPPORTED por FP1; no afirmación de prueba de matching |
| INV-45,46,47,48 | Refinamiento/mezcla/modelos/fronteras exteriores no inferidos de mensajes | P07/P09/COMPATIBILITY | Sin operación nueva; extensiones generales NOT_SUPPORTED, objetos FP1 conservados |
| INV-P01,P02,P06 | Separar autoridad, excluir Diversidad Universal y no promover sintéticos a validación real | P09, decisión transporte, compatibilidad | Revisión documental; no test empírico |
| INV-P03,P05 | Continuidad autónoma, versiones, fuentes e integridad | P03/P04/P09; SOURCES; C02/C21/C22, AUD4-NEG-001; paquete/verificador a cargo Integrador | PASS de intercambio/exportación local; recepción y manifiesto efectivos en los documentos raíz. |
| INV-P04 | Autor no acepta solo su objeto | Diseñador, adaptador, consumidor, auditor y receptor separados funcionalmente | A/AC/AF son revisión separada ejecutada; gate y recepción corresponden a documentos raíz. |

## Exclusiones y evidencia todavía no acreditada

No se registra PASS para MCP, A2A, HTTP/OpenAPI, firma/autenticación, operación pública, memoria/CPU duramente aisladas, cancelación selectiva, reinicio/reanudación de trabajo, multiusuario, datasets reales ni plataformas/versiones de runtime no ejecutadas. Son incompatibilidades o trabajo fuera del mandato, no tests omitidos convertidos en éxito. A sí comprueba los límites reales de frame/input/candidate; AF comprueba el límite real de salida con payloads inyectados. Esto no constituye una prueba de rendimiento de instancias matemáticas grandes. Las regresiones de autor con máximo reducido tienen alcance distinto y no se recuentan como la evidencia independiente AF.

La presentación INVALID puede producir un Result veraz verificable. La preservación de ERROR se ejerció únicamente mediante inyección/fixture sintético: no se provocó un fallo interno real del Kernel ni se acreditó matemáticamente el fixture por pasarlo por el pipe. INCOMPLETE sí se obtuvo de los verificadores reales bajo límites. La rama específica RecursionError del parser permanece documentada e inspeccionada, sin un caso focal independiente en estas baterías; no se declara su cobertura experimental. Los resultados PASS se limitan a los controles enumerados.

En R, dos candidatos de F3 contienen numbers JSON y reciben CANDIDATE_TYPE conforme a P05; su `full_object_equal` es false explícito. Se comparan como rechazo contractual esperado, no como identidad del report heredado. Las otras 3336 llamadas sí conservan identidad completa de objeto. El primer replay con dos discrepancias se mantiene como [CONSUMER_REPLAY_01](../validation/CONSUMER_REPLAY_01/report.json), con reparación del oráculo identificada en [R02](../validation/CONSUMER_REPAIRS/R02.json).

La mutación de buffers durante await produjo un fallo real de exportación del consumidor: [C25 anterior](../validation/CONSUMER_CONFORMANCE_03/C25.json). La copia antes de await conserva input y candidate ligados a sus digests; [C25 corregido](../validation/CONSUMER_CONFORMANCE_04/C25.json) y [R03](../validation/CONSUMER_REPAIRS/R03.json) registran la reparación. El hallazgo no se atribuye al Kernel ni se oculta detrás del PASS final.
