# Consumidor independiente — diseño y evidencia

Autoría separada del adaptador: rol F4 consumidor. Node.js v24.19.0; solo módulos estándar `child_process`, `crypto`, `buffer`/Buffer, `fs`, `path`, `url` y `util`. Ninguna importación de Python, Kernel, adaptador, Benchmark ni oráculos heredados. La API pública está en `consumer/client.mjs`; la CLI está en `consumer/cli.mjs`. La autoridad utilizada fue PHASE_4_MANDATE, Specification 01/05/06, invariantes y CONTRACT P01–P09.

## Frontera de independencia

El proceso Node inicia otro proceso ejecutando `python3 -m genius_protocols` con `PYTHONPATH=protocols:kernel`. La única comunicación del consumidor con ese proceso son frames JSON-RPC UTF-8 por stdin/stdout. El cliente no llama funciones Python ni utiliza sus tipos u objetos en memoria.

El consumidor implementa por separado negociación estricta, framing, JSON estricto, comprobación de bytes/base64/SHA-256, inspección estructural de Result y clasificación de errores. La fixture C02/C04/C05/C06/C24 es una instancia finita H=0 construida en Node, con dos políticas, racionales mayores que 2^53, Unicode y cadenas iguales en espacios nominales diferentes; sus aserciones son independientes del adaptador. Esa fixture no acredita corrección general del Kernel.

El replay toma **datos** de los paquetes heredados F3, no importa el generador ni el código de sus oráculos. Comparar sus resultados completos demuestra preservación del expediente en el intercambio. No se vuelve a contabilizar esa comparación como nueva independencia matemática, ni se llama benchmark de rendimiento por incluir las llamadas PERF_FINAL.

## Decisiones del consumidor

| Obligación | Implementación y alcance |
|---|---|
| Versiones/capacidades | Identificadores exactos de wire, producto, Kernel, Specification, teoría, perfil y formatos. Capacidades/nombres como conjuntos sin duplicados. Campos desconocidos o límites distintos se rechazan. No hay downgrade ni reintento tácito. |
| Sesión/framing | Una solicitud pendiente, IDs string generados con contador BigInt, respuesta correlacionada por ID. Frame máximo antes de LF. EOF, error de proceso o respuesta truncada nunca se convierten en Result. |
| JSON externo | UTF-8 fatal, BOM no aceptado, claves duplicadas incluso escapadas rechazadas, sustitutos aislados rechazados, profundidad acotada. Los números del control deben ser enteros seguros; los documentos Result no admiten tokens numéricos. |
| Bytes/digest | Buffer → base64 canónico → SHA-256. Resultado decodificado sin serialización intermedia; digest del resultado y vínculo con los bytes originales de input comprobados. |
| Mutabilidad | Snapshots privados de input y candidate antes del request/await. El llamante no puede modificar el expediente ligado a los hashes mientras espera la respuesta. |
| Precisión/identidad | Nat/Q/Bit permanecen strings; ningún cálculo FP1 usa Number. Los IDs permanecen en su campo/namespace y no se deduplican por igualdad lexical. |
| Conjuntos/listas | Se conservan todos los arrays; no se extrae prioridad de orden de políticas o frontier. Las listas path siguen su orden. |
| Estados | Result mantiene presentation, execution, Cell, diagnostics, checks y cobertura. El resumen de CLI acompaña al archivo completo, nunca lo sustituye. |
| Verificación | Report exacto `{valid,status,errors}` y digests de input/candidate comprobados. VALID/true, INVALID/false e INCOMPLETE/null permanecen diferentes. |
| Fallos | `RPC_ERROR` conserva code/message del servidor. `TRANSPORT_CLOSED`, `TRANSPORT_IO`, `TRANSPORT_START`, `TRANSPORT_TIMEOUT`, `CANCELLED` y errores locales tienen plano propio. |
| Cancelación | AbortSignal/SIGINT/SIGTERM termina el proceso creado; no hay cancel RPC ni promesa de que el cálculo no comenzó. Una respuesta ya completada conserva su significado. |
| Exportación | mkdir exclusivo y archivos wx. No sobrescribe resultados, inputs ni errores previos. Una escritura incompleta puede dejar evidencia parcial y la siguiente ejecución usa otro directorio. |

La inspección local de Result comprueba la raíz cerrada, identidad, digest, estados, límites, progreso y celdas principales. No pretende ser un segundo validador exhaustivo de cada tabla matemática. Los resultados completos se preservan y el método de verificación público comprueba su afirmación. El parser JSON Node tiene un máximo de profundidad de 512, distinto del límite ambiental anunciado por Python; no se promete aceptar resultados arbitrariamente profundos.

## Evidencia por requisito

| IDs | Requisito y comprobación |
|---|---|
| C01, C12, C13 | P03/P09: negociación compatible, falta de versión/capacidad y peer que miente sobre perfil. No se envía input tras incompatibilidad. |
| C02, C03, C10, C18, C21, C25 | P04/P05: pareja exacta, digests independientes, JSON equivalente con bytes diferentes, rechazo de cross-binding, certificados, no overwrite y snapshots previos a await. |
| C04, C05 | P07/INV-02/09/28/42/49: Q grandes con signo, Nat string, Unicode, IDs nominales, dos maximales y ninguna selección implícita. |
| C06, C07, C08, C09, C11, C23, C24 | P05–P08/INV-03/04/05/31: parcialidad terminada, referencia UNRESOLVED, LIMITED/BLOCKED, INVALID, verificación INCOMPLETE, gramática ERROR y refutación formal completa. |
| C14, C15, C16 | P01/P08: proceso terminado con exit 7 antes de reply, cancelación del padre y timeout local. Todos permanecen separados de agotamiento o dominio negativo. |
| C17, C19, C20 | P01/P02/P06/P08: digest params incorrecto, continuación de sesión, duplicados de salida, números de Result y límites operativos no admitidos. |
| C22 | CLI reusable: cuatro comandos como procesos externos, paquetes y reports reales. |
| Replay de F3 | P04/P05/P07: todas las llamadas originales por ID, resultados completos, reports positivos/negativos/incompletos y entradas inválidas. Conserva casos, bytes, digests y configuración. |

C23 usa una fixture modificada explícitamente para comprobar que el lector conserva execution.ERROR y Cell.BLOCKED. No induce un fallo del Kernel, no obtiene validación matemática de esa fixture ni acredita cobertura dinámica de RPC -32603. C14–C16 sí usan procesos externos reales; sus peers de prueba no ejecutan el Kernel y solo sirven para producir fallos de transporte deterministas.

## Fallos originales y reparaciones

No se modificó el Kernel, Benchmark, baseline ni el adaptador. La historia permanece en `validation/CONSUMER_REPAIRS` y los directorios de ejecución numerados.

| Reparación | Fallo retenido | Cambio y regresión |
|---|---|---|
| R01 | `consumer_conformance_before_R01.mjs`, `R01_original_stderr.txt`: paréntesis faltante en el harness antes de ejecutar tests. | Cierre de llamada sha256 en el harness; no cambio de producto/contrato. |
| R02 | `CONSUMER_REPLAY_01/report.json`: 3.336 identidades y dos diferencias de errores de candidatos con número JSON; el comparador las marcó FAIL. | Separar identidad del objeto heredado de rechazo contractual P05. Se conservan `full_object_equal:false`, expected original, `protocol_expected`, `contract_rejection_equal`, candidato y reports. No se cambia el veredicto ni se finge igualdad. |
| R03 | `CONSUMER_CONFORMANCE_03/C25.json` y `client_before_R03.mjs`: mutar el Buffer del llamante durante await podía cambiar la copia exportada posterior sin cambiar digest. | Copiar input/candidate antes de enviar. C25 exige que ambos archivos posteriores conserven los hashes del request; conformance 04 pasa. |

Resultado definitivo de la suite específica: `validation/CONSUMER_CONFORMANCE_04/report.json`, **25 casos / 79 aserciones PASS**. Los informes anteriores se conservan, incluidos los fallos. El replay definitivo es `validation/CONSUMER_REPLAY_02/report.json`: **508 fichas, 506 con llamadas, 3.338 llamadas PASS, 3.336 identidades completas y 2 rechazos contractuales P05**; cero fallos. Hay 3.188 llamadas de CORRECTNESS_FINAL y 150 de PERF_FINAL. Los archivos `source_snapshot`, `source_hashes_before` y `source_hashes_after` vinculan la ejecución a las fuentes usadas: `sources_unchanged_during_run:true`.

## Límites de la afirmación

El cliente usa requests individuales e IDs string; no expone batch, IDs numéricos/null ni notificaciones. Esas capacidades del servidor pertenecen a la auditoría específica del adaptador. Solo se declara stdio local, sin red, autenticación, firmas, aislamiento duro, persistencia de jobs ni cancelación selectiva. Un digest no prueba procedencia o premisas empíricas. F4 no abre F5 ni crea un servicio público.
