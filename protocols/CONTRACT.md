# Genius Protocols 1.0 — contrato de intercambio

Identidad de producto: `GENIUS-PROTOCOLS-1.0.0`. Versión negociable de mensajes: `genius-protocols/1.0`. Este contrato es candidato de F4; su existencia no acepta G4. El dictamen del handoff determina su estado. Autoridad matemática: [Specification 00–06](../GENIUS_PROGRAM/specification/00_SPECIFICATION.md), `GENIUS-SPEC-1.0.0`, `FP1_FINITE_EXACT`, `GENIUS-THEORY-2026-09-23-S2`. Sujeto preservado: `GENIUS-KERNEL-1.0.1`. No se altera Kernel, Benchmark, teoría ni formatos FP1.

DEBE y NO DEBE expresan obligaciones de este perfil. Los objetos descritos tienen exactamente los campos indicados salvo los marcados opcionales. El contrato usa las estructuras JSON-RPC 2.0 con restricciones explícitas de transporte, IDs, métodos, notificaciones, recursos y sesión. No declara conformidad con MCP, A2A, HTTP u OpenAPI. `FP1_EXACT_ENUM_V1` es el protocolo lógico de evidencia dentro del Kernel, distinto de este transporte.

## P01. Proceso y delimitación

Un consumidor independiente inicia el servidor local y comunica por stdin/stdout binarios. Cada mensaje es un texto JSON UTF-8 seguido de un byte LF (`0A`); no hay encabezados, `Content-Length`, compresión, streaming de resultados ni mensajes de progreso. Los LF dentro de cadenas se escapan. Stdout contiene exclusivamente respuestas del protocolo; diagnósticos humanos usan stderr. CRLF se admite: el CR es whitespace del texto JSON y cuenta en su tamaño. Un frame vacío no es un keepalive: produce error de análisis.

La sesión procesa frames serialmente. El cliente espera la respuesta antes de iniciar otra solicitud; un batch es un solo frame. No se promete ejecución concurrente, transacciones, orden de finalización útil para dependencias ni entrega exactamente una vez. No se usa el ID RPC como identidad de una instancia, política o certificado.

El parser de control rechaza UTF-8 inválido, BOM inicial, sintaxis JSON inválida, constantes NaN/Infinity, claves repetidas en cualquier nivel y sustitutos Unicode aislados, también después de desescapar. Una repetición como `"a"` y `"\u0061"` es duplicado. No normaliza Unicode. Una pareja válida de escapes sustitutos representa su escalar Unicode. Agotamiento del parser por recursión se rechaza como error de análisis del frame; esta limitación operativa no es diagnóstico de una instancia FP1. El adaptador no modifica el límite de recursión del intérprete.

Un frame mal formado terminado por LF produce `-32700`, ID null, y permite leer el siguiente frame. EOF entre frames cierra normalmente. EOF con fragmento no terminado por LF, aunque el fragmento sea JSON completo, cierra con código no cero sin ejecutar ese fragmento ni emitir una respuesta para él. Un frame que excede el máximo produce, si stdout sigue disponible, `-32003` con ID null y cierra con código no cero; no intenta resincronizarse. Una salida truncada, EOF antes de la respuesta pendiente, fallo al iniciar proceso o señal de terminación es fallo de transporte para el cliente. No constituye Result ni prueba de dominio negativo.

## P02. Request, Response y batch

Request tiene `jsonrpc:"2.0"`, `method:string`, `params` opcional y `id` opcional. No admite otros campos. `params`, si está presente, debe ser objeto o array conforme a JSON-RPC; los métodos de este perfil solo admiten params objeto. Ausencia de params se interpreta como `{}` para despacho y no completa campos obligatorios de método.

ID admite cadena ASCII no vacía, entero JSON en el intervalo cerrado `[-9007199254740991,9007199254740991]`, o null. No admite booleanos, arrays, objetos ni números con parte fraccionaria o exponente, aunque su valor sea integral. No se convierten strings en números. El parser puede conservar un token numérico demasiado grande sin convertirlo en entero; su uso como ID se rechaza. Se recomienda ID string simple, único entre solicitudes pendientes. La presencia de `id:null` sigue siendo Request con respuesta; no equivale a omitir id.

Una Response es exactamente `{jsonrpc:"2.0",id:ID,result:objeto}` o `{jsonrpc:"2.0",id:ID,error:{code:entero,message:string}}`, nunca ambas variantes. Errores de análisis y Request inválida usan ID null. Un error posterior de método/params/sesión conserva el ID de la Request válida. Los errores no llevan `data`; los mensajes se fijan en P08.

Una Request estructuralmente válida sin id es una notificación: no produce respuesta y no ejecuta ninguno de estos métodos ni cambia la sesión. Esto incluye método desconocido, params objeto/array o params ausente. Un objeto sin id que no sea Request válida, por ejemplo `method:3` o params escalar, sí produce `-32600` con ID null. Esta política de no ejecución de notificaciones es restricción explícita del perfil; las operaciones con resultado se solicitan con id.

Un array raíz no vacío de hasta 16 elementos es batch. Cada elemento se valida y despacha; las respuestas forman un array, omitiendo notificaciones. Elementos inválidos producen `-32600` con ID null en ese array. Si todos los elementos son notificaciones válidas, no se emite nada, ni `[]`. El batch vacío produce un único objeto error `-32600`. Un batch de más de 16 elementos produce un único objeto error `-32003`, ID null, sin ejecutar elementos. El procesamiento del servidor es serial en orden de entrada, pero el cliente correlaciona exclusivamente por id. El batch no es atómico.

La negociación requiere Request independiente: `genius.initialize` dentro de batch produce `-32002` por Request con id y no cambia estado. Por tanto, un cliente nunca depende de una inicialización previa dentro del mismo batch. Reutilizar un id vuelve a ejecutar una Request: no hay caché ni deduplicación de operaciones.

## P03. Negociación obligatoria

La sesión comienza UNINITIALIZED. Único método que la habilita: `genius.initialize` con params exactos:

```json
{"protocol_versions":["genius-protocols/1.0"],"required_capabilities":["evaluate","verify_result","verify_certificate"]}
```

Ambas listas contienen strings no vacías sin duplicados. `protocol_versions` no puede estar vacía; `required_capabilities` puede estar vacía. Solo se soporta `genius-protocols/1.0`. La oferta debe contenerla y cada capacidad requerida debe estar soportada; versiones adicionales desconocidas no invalidan una oferta que contiene la compatible. Ausencia de versión común o capacidad requerida no disponible devuelve `-32001`, no ejecuta Kernel y deja UNINITIALIZED. Una oferta con tipos/campos incorrectos devuelve `-32602`.

El éxito devuelve exactamente:

```json
{
  "protocol_version":"genius-protocols/1.0",
  "protocols_version":"GENIUS-PROTOCOLS-1.0.0",
  "kernel_version":"GENIUS-KERNEL-1.0.1",
  "specification":"GENIUS-SPEC-1.0.0",
  "theory_snapshot":"GENIUS-THEORY-2026-09-23-S2",
  "profile":"FP1_FINITE_EXACT",
  "input_format":"genius-fp1/1.0",
  "result_format":"genius-fp1-result/1.0",
  "capabilities":["evaluate","verify_result","verify_certificate"],
  "transport_limits":{
    "max_frame_bytes":"16777216",
    "max_input_bytes":"2097152",
    "max_candidate_bytes":"8388608",
    "max_response_bytes":"33554432",
    "max_batch_items":"16",
    "max_limit_digits":"12"
  },
  "default_kernel_limits":{},
  "allowed_kernel_limits":["max_nodes","max_operations","max_seconds","max_input_bytes","max_integer_digits"],
  "environment":{"python_recursion_depth":"1000"},
  "cancellation":"PROCESS_TERMINATION_ONLY"
}
```

`environment.python_recursion_depth` es el Nat decimal del límite real capturado del intérprete; `1000` es el entorno observado, no un valor que deba imponerse. Las listas de capacidades/nombres tienen semántica de conjunto. Los demás valores anteriores son los de esta versión. La respuesta de éxito cambia la sesión a READY. Un segundo initialize, incluso idéntico, devuelve `-32002`. Los tres métodos de cálculo/verificación antes de READY devuelven `-32002`, sin invocar Kernel. Un método desconocido devuelve `-32601` con independencia de la sesión. Tras negociar no se añade un campo de versión redundante a cada params; el proceso es el ámbito de la versión elegida. Para otra negociación se abre otro proceso.

El consumidor comprueba los identificadores exactos, capacidades y límites que necesita antes de enviar una instancia. No equipara compatibilidad de transporte con compatibilidad matemática; una Specification, perfil o formato distinto requiere soporte declarado y nueva revisión. No hay downgrade silencioso.

## P04. ByteEnvelope e identidad portable

ByteEnvelope es exactamente `{encoding:"base64",data:string,sha256:string}`. `sha256` contiene 64 hexadecimales minúsculos y debe igualar SHA-256 de los bytes decodificados. Se usa alfabeto base64 estándar RFC 4648 §4, padding obligatorio cuando corresponde, sin whitespace, caracteres ajenos, alfabeto URL-safe ni bits de padding no canónicos. La condición comprobable es `base64_encode(base64_decode(data)) == data` después de decodificar estrictamente. La secuencia vacía se representa por `data:""` y su digest real. Un envelope bien formado no acredita que sus bytes sean UTF-8 o una instancia válida.

Cada blob se valida por campos/tipos, codificación, tamaño decodificado y digest antes de invocar Kernel. Para evitar una asignación excesiva se puede rechazar con `-32003` una cadena data cuya longitud supere `4*ceil(max_bytes/3)` antes de decodificar; esto prevalece aunque esa cadena también tenga codificación inválida. No se interpretan rutas, URLs, comandos, contenido ejecutable ni referencias a archivos externos. `input` lleva exactamente los bytes que recibirá `evaluate`/los verificadores. No se parsea y vuelve a serializar antes del digest, ni se normalizan whitespace, escapes, newline, orden de miembros o Unicode. Un fallo de base64 o digest dentro de los límites devuelve `-32602`; exceso del tamaño de blob devuelve `-32003`.

El resultado de evaluate contiene el input original y el Result completo, ambos como bytes identificados. El consumidor exporta los bytes decodificados como `input.json` y `result.json`; verifica los hashes de ambos blobs y que `Result.input_digest` iguale el digest de input. Así obtiene la unidad portable requerida por Specification 06. El digest del blob Result identifica su serialización concreta; no añade un campo a Result. No se exige que toda implementación serialice resultados matemáticamente equivalentes con idénticos bytes.

Dos inputs con igual objeto JSON pero bytes distintos siguen siendo inputs con digest distinto. Nunca se acepta un certificado del primero para el segundo por equivalencia aparente. Un digest detecta identidad de bytes según la función usada; no acredita origen, autenticidad, verdad empírica ni validez matemática.

## P05. Métodos de evaluación y verificación

| Método | Params exactos | Result RPC exacto |
|---|---|---|
| `genius.evaluate` | `{input:ByteEnvelope,limits?:LimitMap}` | `{input:ByteEnvelope,result:ByteEnvelope}` |
| `genius.verify_result` | `{input:ByteEnvelope,candidate:ByteEnvelope,limits?:LimitMap}` | `{input_digest:Digest,artifact_digest:Digest,report:VerificationReport}` |
| `genius.verify_certificate` | `{input:ByteEnvelope,candidate:ByteEnvelope,limits?:LimitMap}` | `{input_digest:Digest,artifact_digest:Digest,report:VerificationReport}` |

En evaluate, todo input que supera las comprobaciones del blob pasa intacto a la API Kernel. Incluye bytes UTF-8 inválidos, JSON con duplicados, campos FP1 incorrectos o una versión de Instance no soportada: esas presentaciones generan el Result correspondiente del Kernel. No se convierten en error RPC ni se rellenan. Result preserva su gramática cerrada completa; no hay proyección de valores favorable, omisión de testigos ni resúmenes usados como sustituto.

En verify_result, candidate decodifica a Result de Specification 06. En verify_certificate, candidate decodifica al envelope ya expuesto por la API Kernel: `{input_digest:Digest,certificate:DecisiveCertificate}`. Ese envelope no tiene un campo `format` inventado. El Input original es obligatorio en ambos métodos. `artifact_digest` identifica los bytes originales de candidate aun cuando se rechaza. El parser de candidate verifica UTF-8, JSON, Unicode escalar y ausencia de duplicados antes de crear el objeto para el verificador. Nunca se permite que un parser elimine claves duplicadas aceptando la última.

VerificationReport tiene exactamente `{valid:boolean|null,status:"VALID"|"INVALID"|"INCOMPLETE",errors:Array[string]}`. Las combinaciones son true/VALID, false/INVALID y null/INCOMPLETE. Un rechazo de sintaxis estricta del candidate produce exactamente `{valid:false,status:"INVALID",errors:["CANDIDATE_SYNTAX"]}` sin llamar al verificador Kernel. Como los dos formatos de candidate usan Nat/Q/Bit como strings y no contienen números JSON, el parser puede rechazar cualquier token numérico JSON con `errors:["CANDIDATE_TYPE"]`, sin convertirlo ni ejecutar el verificador. El límite ambiental del parser de candidate puede causar `CANDIDATE_SYNTAX`; es un rechazo del artefacto dentro de este parser acotado, no refutación de una afirmación matemática.

Si candidate supera ese parser, la API Kernel verifica forma, digest, reglas, dominios, cobertura y afirmaciones; su report se conserva íntegro. Rechazo del certificado sigue siendo una respuesta RPC exitosa con report INVALID. Un límite de verificación produce el report INCOMPLETE del Kernel, nunca true. El verificador comparte constructores con el evaluador; esta interfaz no crea un verificador matemático independiente.

## P06. Límites declarados, separados del problema

Los seis `transport_limits` de P03 se aplican antes o después del cálculo según su objeto. Tamaños de frame y response cuentan bytes UTF-8 del JSON **sin** el LF delimitador; si hay CR final, sí se cuenta. Input/candidate se miden después de decodificar base64. Los límites se conocen antes de enviar datos y no son restricciones de la instancia ni garantías de memoria/tiempo. Máximos de blob y frame se aplican conjuntamente; un batch puede exceder el frame aunque cada input aislado quepa.

LimitMap es objeto opcional con cualquier subconjunto de `max_nodes,max_operations,max_seconds,max_input_bytes,max_integer_digits`. Cada valor es string Nat canónica `0|[1-9][0-9]*`, como máximo 12 dígitos. No se admiten numbers JSON, negativos, decimales, signos, ceros iniciales, null, booleanos ni claves adicionales. La conversión a entero se limita a estos argumentos operativos. Una clave ausente no impone su límite artificial; `{}` y omisión tienen el mismo efecto. No hay defaults ocultos ni timeout duro del servidor.

Los cinco significados son los de [Kernel README](../kernel/README.md): ocurrencias, checkpoints operativos, segundos cooperativos, bytes de Input y dígitos de numerales recibidos. El límite `max_input_bytes` de LimitMap puede ser menor que el máximo de transporte y produce el comportamiento LIMITED del Kernel; no modifica el límite wire. El límite de recursión ambiental se anuncia y el Kernel lo registra en `execution.limits`. No se modifica H, Π, ramas, ley, constraints ni enteros derivados para satisfacer presupuestos.

Si la respuesta serializada excede 32 MiB, se devuelve `-32003` para el id correspondiente. En batch, si la respuesta agregada excede el máximo, se sustituyen **todas** las respuestas que habrían sido emitidas por errores `-32003`, manteniendo sus ids, incluidos null; las notificaciones siguen omitidas. Los cálculos anteriores pudieron haber ocurrido. No se emite un Result truncado ni un LIMITED fabricado, y no se afirma que una operación no se ejecutó. La siguiente Request válida puede seguir en READY. La materialización de un resultado puede consumir memoria antes de medir su salida; no hay garantía de contención de memoria.

## P07. Preservación semántica obligatoria

| Objeto del contrato FP1 | Identificación y regla en el consumidor |
|---|---|
| Nat, Q, Bit | Conservar strings exactas. Q mantiene numerador/denominador reducido y signo; no pasar por float/Number, redondear ni convertir a puntuación. BigInt/racionales explícitos solo si se requieren cálculos externos exactos. |
| Tipos nominales | Resolver IDs en el namespace del campo. Igual string en estado, información, portador o identidad generativa no fusiona objetos. |
| Experimento/política | Mantener input_digest, meta, policy, horizonte, marco/modelo/contexto/condición. Dos políticas distintas no se fusionan por igual trayectoria. |
| Ocurrencia/hoja | Query es `{policy,path}`; conservar orden de path y cada rama. No deduplicar por `(t,x)` o por estado final. Mantener hojas de masa cero. |
| Escenario | Usar el mapa comprobado de palabra exógena a hoja por política; no emparejar por posición de array. |
| Tabla parcial | Claves presentes son dominio. Una fila ausente no se completa con cero, false, vacío o preferencia; tabla obligatoria ausente conserva invalidez. |
| Conjuntos/listas | Set no tiene prioridad; List sí conserva orden semántico. No inferir selección de orden de bytes, llegada, nombres o filas. |
| Premisas | Conservar toda assumptions/basis, contenido Unicode y procedencia. Permanecen premisas externas, no verdades autenticadas por digest o nombre de protocolo. |
| Evidencia/certificado | Conservar checks, diagnostics, DatumRef, testigos, guardas y referencias completas. Verificar contra el Input ligado, no aceptar etiquetas PASS aisladas. |
| Comparación/cobertura | Conservar target, B, C, partición hard, matriz de pares, frontier, omisiones, cobertura y selection. RELATIVE nunca habilita selección global. |

`presentation` mantiene VALID/INVALID/UNRESOLVED. `execution.status` mantiene COMPLETE/LIMITED/ERROR. Las celdas conservan DEFINED con su valor, OUTSIDE_DOMAIN con sus motivos, o BLOCKED sin valor; nunca se reducen a null o booleano. Una falta de dominio no es fallo RPC, ni COMPLETE implica presentación válida, frontera exhaustiva o selección. La tabla de estados de Specification 06 permanece normativa.

## P08. Errores y cancelación

| Code RPC | Message exacto | Plano y consecuencia |
|---|---|---|
| -32700 | Parse error | Control UTF-8/JSON/duplicados/Unicode o parser no procesable; sin invocación de Kernel para ese frame. |
| -32600 | Invalid Request | Estructura Request, ID fuera del perfil, extra root fields o batch vacío. |
| -32601 | Method not found | Nombre de método no implementado. |
| -32602 | Invalid params | Campos de método, ByteEnvelope, base64/digest o LimitMap inválidos. |
| -32603 | Internal error | Fallo del adaptador fuera de un Result/report Kernel; no se fabrica un valor matemático. |
| -32001 | Incompatible protocol | No hay versión común o falta capacidad requerida. |
| -32002 | Invalid session state | Cálculo antes de initialize, repetición de initialize o initialize en batch. |
| -32003 | Transport limit exceeded | Exceso de frame/blob/batch/respuesta; comportamiento de cierre definido por P01/P06. |

Presentación FP1 inválida, fallo de guarda, Cell fuera de dominio, agotamiento del Kernel y rechazo de certificado están en Result/report, no en esta tabla. `error` señala una operación de protocolo no entregada normalmente; no debe transformarse en `Result.execution.ERROR`. A la inversa, un Result real con ERROR permanece dentro de `result` RPC.

La prioridad de procesamiento es: tamaño/framing → parser estricto del frame completo → forma de Request → omisión de notificación válida → existencia de método → estado de sesión → campos params y LimitMap → blob input → blob candidate cuando corresponde → parser candidate → API Kernel → tamaño de respuesta. Así, un defecto de sintaxis en cualquier parte de un batch impide despachar todo el frame; un elemento Request inválido de un batch JSON válido solo aporta su error. Un defecto de sintaxis/duplicados/Unicode en candidate precede a CANDIDATE_TYPE por token numérico. No se promete enumerar todos los defectos de un mensaje rechazado.

No existe método cancel, ni cancelación selectiva o confirmación de aborto. El cliente puede terminar el proceso que creó; pierde la sesión y las Requests pendientes. Clasifica toda operación pendiente sin respuesta completa como fallo de transporte, aun si el proceso había comenzado o terminado internamente el cálculo. Si había recibido y validado una respuesta completa, esa respuesta conserva su significado. Se inicia otro proceso para continuar. Un timeout local del cliente no es LIMITED del Kernel, OUTSIDE_DOMAIN, frontera vacía ni certificado de inexistencia.

## P09. Compatibilidad, evidencia y exclusiones

La versión wire se acepta por igualdad de identificador, no por orden de strings ni inferencia de compatibilidad SemVer. Una reparación que conserve este contrato requiere nueva identidad de producto y evidencia; campos o significados incompatibles requieren otra versión wire. Toda extensión preserva contrato/historia recibidos y revisión conforme a [VERSIONING](../GENIUS_PROGRAM/VERSIONING.md). No se aceptan extensiones desconocidas silenciosamente.

G4 exige consumidor de otro proceso y lenguaje sin importar Python/Kernel, controles independientes, ida/vuelta de bytes, incompatibilidad de versión/capacidad, invalidación de certificados, precisión mayor que 2^53, estados parciales, errores, límites y terminación durante solicitud. Los casos enlazan requisito P01–P09 → mensaje → adaptador → test → resultado; los informes determinan qué se ejecutó. Este documento no cuenta pruebas como ejecutadas.

Fuera de la capacidad: red/HTTP, autenticación, multitenancy, firmas, descubrimiento MCP/A2A, OpenAPI, trabajos persistentes, reanudación, caché idempotente, suscripciones, stream de resultados, ejecución distribuida, aislamiento duro de CPU/memoria y equivalencia entre modelos distintos. Nada de ello se anuncia por producir JSON. El transporte local no valida premisas empíricas, originalidad, utilidad real ni rendimiento universal, y no abre F5.
