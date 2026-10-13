# Trazabilidad del mandato F5 a controles y evidencia

Candidata GENIUS-P5-2026-09-26-v1.0.0; componente
GENIUS-INFRASTRUCTURE-1.0.0. Matriz de autoría preparada el 2026-09-26 contra
[PHASE_5_PROMPT](../../PHASE_5_PROMPT.md), §3. Se distingue implementación,
ensayo ejecutado y aceptación. El [freeze de código/tests](../../validation/F5/CODE_FREEZE_01.json)
identifica la candidata sometida a revisión. El Integrador decide el gate con
los informes separados; esta matriz no lo concede.

## Registro de evidencia consultada

| Clave | Evidencia ejecutada | Unidad y resultado | Alcance |
|---|---|---|---|
| INT | [integration_run01/REPORT.json](../../validation/F5/author/integration_run01/REPORT.json), [comandos](../../validation/F5/author/integration_run01/COMMANDS.json) | 37 comprobaciones PASS | CLI completa: evaluación/verificaciones, fallo de plazo, reintento, backup/restauración/rollback y 10 ejecuciones seriales sintéticas |
| PLAT | [platform/run04/summary.json](../../validation/F5/author/platform/run04/summary.json), [invocación](../../validation/F5/author/platform/run04/invocation.json), [identidad](../../validation/F5/author/platform/run04/identity.json) | 8 casos PASS | Worker F4 real, estados preservados, límites/configuración y negociación; prueba de peer incompatible distinguida |
| DATA | [data/RUN_04/REPORT.json](../../validation/F5/author/data/RUN_04/REPORT.json), [snapshot portable](../../validation/F5/author/data/RUN_04/SNAPSHOT.json) | 17 casos PASS | Archivos/locks/permisos/interrupción reales; ENOSPC y determinados EIO inyectados explícitamente |
| SEC | [security/RUN_02/SUMMARY.json](../../validation/F5/author/security/RUN_02/SUMMARY.json), [informe](../../validation/F5/author/security/SECURITY_REPORT.md) | 12 casos PASS | Peers sintéticos confiados, contención compartida, fallos de canal/identidad/estructura y muerte del padre |
| RCV4 | [recepción actual F4](../../validation/F5/reception_f4/RECEIPT.json), [identidad ZIP](../../validation/F5/reception_f4/zip_identity.json), [verificación](../../validation/F5/reception_f4/verify_f4.stdout.json) | Recepción F4 con alcance declarado por ese informe | Distinta de evidencia histórica F4 y de nueva implementación F5 |

Las unidades no se suman entre sí: una comprobación INT no es un caso SEC,
las corridas repetidas no son nuevos casos independientes y ningún conteo
representa demostraciones matemáticas nuevas. Los informes de autoría no son
los informes de auditoría o recepción. Las corridas previas y negativos siguen
conservados con su propio estado.

## Seis áreas exigidas por §3

| Requisito del mandato | Control implementado o decisión documentada | Archivo de referencia | Ensayo/evidencia ejecutada | Límite de la afirmación |
|---|---|---|---|---|
| 1. Activos, actores y límites de confianza | T01–T09 distinguen blobs no confiables, operador/código/intérprete/host confiados, evidencia y disponibilidad | [THREAT_MODEL](THREAT_MODEL.md), [SECURITY](SECURITY.md) | SEC CPU/AS/WALL/OUT/ERR/ENV/PARENT; DATA03–07/09–12 | Ensayos provocados no equivalen a incidentes anteriores. No sandbox frente a código hostil, root o mismo UID |
| 1. Amenazas demostradas, plausibles y excluidas | Registro separado de defectos reproducidos, condiciones de fallo ensayadas, riesgos plausibles y red fuera de alcance | [THREAT_MODEL](THREAT_MODEL.md), [informe SEC](../../validation/F5/author/security/SECURITY_REPORT.md), [DATA_RECOVERY](DATA_RECOVERY.md) | F5-SEC-001, F5-DATA-001 y F5-DATA-002 conservan before/after | No pentest externo, red, multitenancy, autenticación remota ni datos reales |
| 2. Supervisor/worker, permisos e intérprete | Worker fijo, -I/-S/-B, env mínimo, argv sin shell, close_fds, sesión nueva; rechazo normal de UID0 | [supervisor.py](../genius_infra/supervisor.py), [worker.py](../genius_infra/worker.py), [PLATFORM](PLATFORM.md) | PLAT normal-root-refusal y flujo real; INT default_root_refusal_exit/default_refusal_no_store; SEC-ENV | Entorno solo mapea UID/GID0: la ejecución nonroot quedó impedida, con EINVAL conservado; no se simula UID |
| 2. Contención viable del entorno real | Opt-in `local-fp1-single-uid-lab-v1`: namespace exacto, capacidades Eff/Prm/Inh/Amb0 y NoNewPrivs1, comprobados antes de operar y en worker | [worker.py](../genius_infra/worker.py), [cli.py](../genius_infra/cli.py), [PLATFORM](PLATFORM.md), [SOURCES](SOURCES.md) | PLAT identity.json; DATA containment; SEC-ENV/observed.json | UID real permanece0; ENV01 acredita laboratorio UID0LAB, no mínimo privilegio nonroot ni piloto desplegable |
| 2. CPU/memoria/tiempo/bytes y terminación | Rlimits CPU/AS/CORE0/FSIZE0/NOFILE32; deadline monotónico, drenaje stdout/stderr separado y acotado, killpg/wait; PDEATHSIG más check del padre | [supervisor.py](../genius_infra/supervisor.py), [worker.py](../genius_infra/worker.py), [SECURITY](SECURITY.md) | SEC-CPU/AS/WALL/OUT/ERR/CANCEL/PARENT; INT wall_limit_exit/wall_not_mathematical | AS por worker, no RSS/cgroup global. Muerte operativa no se convierte en KernelLIMITED. PDEATHSIG no acredita contención de descendientes arbitrarios |
| 2. Concurrencia/cola y ausencia de defaults matemáticos | Un lock por store, BUSY no bloqueante, sin cola; perfil operativo explícito, LimitMap Kernel separado | [storage.py](../genius_infra/storage.py), [cli.py](../genius_infra/cli.py), [PLATFORM](PLATFORM.md) | DATA02/13; PLAT explicit_caps_and_invalid_limit_map/kernel_limited_is_delivered; INT real_kernel_limited_delivered | Una operación por store no limita stores paralelos de un operador; no cache/idempotencia/exactly-once |
| 3. Pareja portable, certificados y versiones | Input/candidate/result preservados como bytes; negociación exacta, envelopes/digests/binding; Result completo, metadatos operativos y componentes separados | [supervisor.py](../genius_infra/supervisor.py), [storage.py](../genius_infra/storage.py), [DATA_RECOVERY](DATA_RECOVERY.md) | INT exact_input_bytes/result_digest_bound/verify_result_valid/verify_certificate_valid; PLAT evaluate/verify; DATA01; SEC-ID/SHAPE/NEGOTIATE | Gramática exterior no es segundo verificador matemático. SHA-256 no autentica autoría ni premisas; el Kernel verificador comparte constructores |
| 3. Rutas, atomicidad, overwrite, cuotas y retención | Dirfds/no-follow, nombres internos cerrados, archivos exclusivos0700/0600, staging/commit, inventario+hashes, cuotas explícitas; no purga automática | [storage.py](../genius_infra/storage.py), [DATA_RECOVERY](DATA_RECOVERY.md) | DATA01/03–07/09/13–17; INT restore_no_overwrite_exit | Confianza en ancestros/UID; cuotas de bytes lógicos, no reserva física/inodos. Fallo post-rename puede dejar expediente visible sin confirmación |
| 3. Secretos | Entorno reducido, sin credenciales requeridas, eventos sin payload; artefactos privados con contenido sintético completo | [SECURITY](SECURITY.md), [cli.py](../genius_infra/cli.py), [THREAT_MODEL](THREAT_MODEL.md) | SEC-ENV con marcadores propios; DATA06 permisos; inspección del código de eventos | No escáner universal de secretos ni cifrado. Input/result son datos completos; no se autoriza introducir datos reales |
| 4. Observabilidad y correlación | start/outcome con versión, método, límites, reloj, razón, PID, bytes retenidos/observados y prefijos; run UUID separado de RPC ID y digest; retry_of explícito | [cli.py](../genius_infra/cli.py), [supervisor.py](../genius_infra/supervisor.py), [PLATFORM](PLATFORM.md) | INT retry_new_execution y expedientes; SEC-OUT/ERR/CANCEL/PARTIAL; DATA08 | stdout del worker sigue siendo protocolo; stdout CLI es resumen operativo. Prefijos no son respuesta válida ni medición final exacta del flujo |
| 5. Backup/restauración/rollback de datos | Snapshot local verificado; restauración en destino nuevo; rollback selecciona snapshot anterior sin borrar store posterior; staging nunca se promueve solo | [storage.py](../genius_infra/storage.py), [DATA_RECOVERY](DATA_RECOVERY.md) | DATA08/10–12/14/15/17; INT restored_content_same/rollback_content_same/rollback_exact_result/restore_no_overwrite_exit | No revierte ejecución ni acciones externas. Rollback de datos probado; una guía de cambio de release de software no se cuenta como ensayo adicional |
| 5. Incidente, parada e idempotencia delimitada | Detener admisión, preservar evidencia/staging, verificar, restaurar copia válida y crear nuevo intento. SIGINT/TERM y cancel_event terminan job; SIGKILL padre activa PDEATHSIG | [DATA_RECOVERY](DATA_RECOVERY.md), [PLATFORM](PLATFORM.md), [cli.py](../genius_infra/cli.py) | SEC-CANCEL/PARENT; DATA08/12/14; INT fallo de plazo y reintento | No autocompletar trabajo interrumpido; una confirmación perdida no prueba que nada sucedió. No idempotencia matemática o exactly-once prometidos |
| 6. Carga, degradación y recursos adversariales | Carga serial declarada y medidas del CLI; exceder recursos conserva fallo; cuotas y rechazo BUSY | [integration_cli.py](../tests/integration_cli.py), [test_security.py](../tests/test_security.py), [test_storage.py](../tests/test_storage.py) | INT 10 ejecuciones de input43586B, paralelo1; SEC-CPU/AS/WALL/OUT/ERR; DATA02/06/08/09/13 | Carga sintética pequeña y entorno único. ENOSPC/EIO son inyecciones; no se llenó el disco compartido. No capacidad productiva ni utilidad real |

DATA01–17 abrevia los nombres completos `test_01_...` a `test_17_...` del
[reporte final DATA](../../validation/F5/author/data/RUN_04/REPORT.json).
El detalle por requisito de almacenamiento está en [DATA_TRACE](DATA_TRACE.md),
y los procedimientos en [INCIDENTS](INCIDENTS.md). DATA11 conserva una corrupción
previa al modificar el manifiesto: demuestra rechazo, pero no se cuenta como
oráculo aislado de traversal; DATA03/04 sí ejercen rutas y enlaces directamente.
Los nombres SEC son IDs exactos de su SUMMARY. PLAT conserva nombres completos
en [test_platform.py](../tests/test_platform.py) y artefactos de su corrida.

## Medición de capacidad que sí se ejecutó

INT registró diez ejecuciones seriales, input de 43586 bytes, sin cola ni
servicio remoto facturado. Tiempo de pared del CLI: mínimo0.157618s,
mediana0.186829s y máximo0.199603s; total1.842984s y 5.425984 ejecuciones/s en
esa secuencia. El tiempo CPU observado de hijos fue1.841559s. Estos números
identifican una observación reproducible bajo sus condiciones, no una garantía
de latencia, SLA, escalabilidad, precio o producción. El costo monetario del
cómputo local/suscripción no se asignó ni midió.

## Conservación normativa y recepción

La autoridad matemática continúa en Specification00–06 y su instantánea,
con los invariantes de [GENIUS_PROGRAM/INVARIANTS](../../GENIUS_PROGRAM/INVARIANTS.md).
No se añadieron axiomas, prioridades, pesos, probabilidades ni selección por
orden. CLI/almacén transportan bytes; timeout/fallo de canal no determina
dominio, falsedad, inviabilidad ni probabilidad. PLAT e INT separan un Result
LIMITED genuino de un fallo del supervisor; los checks Kernel/certificados
siguen disponibles completos cuando se entrega el resultado.

F4 fue recibida antes de abrir F5 y se conserva como genealogía. RCV4 distingue
verificación actual de evidencia heredada; sus hashes no se reinterpretan
como corrección matemática. F5 agrega controles operativos al perfil local,
sin anunciar MCP, A2A, OpenAPI o red ni iniciar F6.

Estado de este registro: **auditoría independiente F5 y recepción sin historia
pendientes al redactar la matriz**. Los dictámenes posteriores deben consultarse
en [ACCEPTANCE_REPORT](../../ACCEPTANCE_REPORT.md) y en sus expedientes de
`validation/F5/audit/` y `validation/F5/receiver/`; los resultados de autoría
no los reemplazan. La aceptación técnica de residuos locales pertenece al
Integrador dentro del mandato. El perfil nonroot/piloto no está acreditado por
UID0LAB y cualquier despliegue requiere decisión y evidencia propias.

## Cierre posterior de la matriz

La mención pendiente anterior identifica la fecha de autoría de esta matriz.
La auditoría final de freeze02 pasó 26 casos únicos/94 checks, incluidos
21 casos/76 checks de regresión tras F5-AUD-001. El receptor distinto recibió
el ZIP, verificó bytes y reprodujo flujo y recuperación. Dictámenes completos
en [auditoría](../../validation/F5/AUDIT_REPORT_F5.md) y
[recepción](../../validation/F5/RECEIVER_REPORT_F5.md). La decisión del gate y
aceptación acotada de residuos están en [aceptación](../../ACCEPTANCE_REPORT.md).
