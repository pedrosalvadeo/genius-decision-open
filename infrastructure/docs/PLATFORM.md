# Plataforma local F5

## Arquitectura y significado

El CLI mantiene un lock no bloqueante por store durante admisión, ejecución y publicación. No existe cola. Una transacción guarda los bytes exactos de input y del candidate cuando corresponde, junto con metadatos de la solicitud, antes de iniciar el worker. No persiste el frame RPC de request. Un staging superviviente se conserva para diagnóstico de interrupción. La persistencia corresponde a `storage.py`, la interfaz a `cli.py` y la contención a `supervisor.py`/`worker.py`.

El supervisor crea un grupo de procesos nuevo y ejecuta exclusivamente el worker incluido, con el intérprete actual, `-I -S -B`, `shell=False`, cwd `/`, entorno reducido a PATH/LANG/LC_ALL y `close_fds=True`. No acepta ejecutables, rutas de código ni URLs dentro de la instancia. El worker instala controles antes de cargar el Kernel/Protocols congelados desde las rutas de la entrega. No se usan archivos de salida del worker ni sockets.

Antes de enviar la instancia se negocia y valida `genius.initialize`: versión wire, identidades de producto/teoría/especificación/perfil, formatos, capacidades y límites exactos de F4. Una identidad incompatible detiene el proceso sin enviar la operación. Luego se envía exactamente una operación y EOF.

Stdout contiene exclusivamente el protocolo F4; stderr es un canal separado. El supervisor retiene bytes exactos, con máximos declarados. Los eventos incluyen razón, tiempo transcurrido, PID y contadores, sin payloads. El ID RPC fijo de una sesión no es identidad matemática; input_digest conserva la identidad de bytes recibidos. Los bytes Result decodificados se exportan sin reserializar. `report.json` es una serialización derivada del report; `response.json` preserva la respuesta original.

## Controles y API

`SupervisorLimits(cpu_seconds, address_space_bytes, wall_seconds, max_stdout_bytes, max_stderr_bytes)` exige todos los campos. La API no selecciona defaults. Se admiten CPU entre 1 y 3600 s, AS entre 64 MiB y 8 GiB, wall positivo hasta 3600 s, stdout 1 byte a 48 MiB y stderr 1 byte a 1 MiB. Son límites del perfil operativo; no alteran Instance ni agregan límites cooperativos Kernel.

El CLI ofrece el perfil elegido explícitamente `local-fp1-v1`: CPU 10 s, AS 256 MiB, wall 30 s, stdout 34 MiB, stderr 64 KiB, con overrides explícitos. Linux recibe rlimits soft=hard: CPU/AS configurados, CORE=0, FSIZE=0 y NOFILE=32. AS es espacio de direcciones por proceso, no RSS ni presupuesto de toda una máquina. CPU es tiempo de CPU por proceso, no tiempo transcurrido.

Wall se mide con `time.monotonic`; select no bloqueante drena ambos canales. Exceso de bytes, tiempo o cancelación termina el grupo con SIGKILL y recoge el worker mediante wait. No se atribuye causalmente SIGKILL a memoria: se informa la señal observada. Un fallo de instalación de límites aborta el bootstrap.

Linux `PR_SET_PDEATHSIG(SIGKILL)` se instala en el worker y se comprueba después que getppid conserva el PID esperado, para cerrar la carrera de muerte previa del supervisor. Los cambios de credenciales deben ocurrir antes de iniciar el worker. La muerte del supervisor no depende de un manejador Python para detener el worker. No se promete recolección por un supervisor ya muerto; un zombie sin ejecución es distinto de un proceso activo. El perfil no ejecuta código de terceros ni permite descendientes arbitrarios.

`run_worker(method, input_bytes, candidate_bytes=None, kernel_limits=None, *, limits, cancel_event=None, lab_single_uid_root=False)` acepta evaluate/verify_result/verify_certificate. Los Kernel limits opcionales preservan las strings exactas de F4 y no reciben valores implícitos. `Outcome` contiene status, reason, artifacts y metadata. El caller configura señales SIGINT/SIGTERM mediante un event; la API recoge también KeyboardInterrupt. El flag LAB no reduce privilegios implícitamente: exige que el caller haya ejecutado `enter_lab_containment()` en el proceso dedicado y comprueba sus condiciones.

El bootstrap compartido expone `apply_containment(cpu_seconds, address_space_bytes, parent_pid, *, lab_single_uid_root=False)`. El worker productivo recibe el opt-in interno únicamente cuando run_worker fue llamado con el flag correspondiente; vuelve a verificar identidad, mapas, capabilities y NoNewPrivs antes de cargar F4.

## Fallos operativos y respuestas completas

DELIVERED significa que una respuesta F4 completa compatible llegó y el proceso terminó normalmente. No implica Result COMPLETE, presentación válida, selección ni certificado fuerte. Un Result genuino LIMITED/ERROR y un report INVALID/INCOMPLETE pueden entregarse normalmente.

FAILED/CANCELLED describe operación, no matemática. Los bytes parciales quedan como `worker.stdout`/`worker.stderr`, marcados como prefijos cuando el límite descartó exceso. No se transforman en Result, KernelLIMITED, infactibilidad ni certificado. Las cantidades observadas tras exceder un cap son cotas inferiores, no tamaños finales del flujo.

Si se recibió una respuesta completa válida antes de una terminación posterior, sus artifacts se conservan con `response_validated=true`, aunque status operativo sea FAILED/CANCELLED; el significado de una respuesta recibida no se revoca por una anomalía posterior (P08). Un error RPC válido se conserva y clasifica RPC_ERROR, sin fabricar Result.

F5-AUD-001 demostró que el primer supervisor omitía esos artifacts si llegaban bytes adicionales por stdout después del LF de la respuesta. La reparación separa los dos frames esperados por LF y valida la respuesta completa antes de clasificar los bytes posteriores. Conserva response/result exactos, mantiene FAILED operacional y registra la cantidad de bytes adicionales retenidos. El ruido, otra línea o un flood posterior no convierten el flujo en DELIVERED; los negativos antes/después permanecen en `validation/F5/author/platform/F5-AUD-001`.

## Identidad y límites ambientales

La API y el bootstrap rechazan UID efectivo 0 por defecto. El entorno de autoría tiene EUID0 y mapas `/proc/self/uid_map`/`gid_map` con solo `0 0 1`. Preparar una ejecución nobody falló con errno22; la evidencia está en `validation/F5/author/platform/run01/environment_failure.json`. Ninguna cuenta, mapa o configuración del sistema fue modificada para sortearlo.

ADR-F5-ENV01 introduce un opt-in de laboratorio separado: `local-fp1-single-uid-lab-v1` en CLI; `lab_single_uid_root=True` en API. Solo admite EUID0 con ambos mapas exactamente `0 0 1`. Antes de tocar el store, el CLI llama `enter_lab_containment()` en su propio proceso: activa PR_SET_NO_NEW_PRIVS, usa capset v3 para vaciar effective/permitted/inheritable y vacía ambient. Luego verifica `/proc/self/status` y falla si no observa ceros en los cuatro conjuntos y NoNewPrivs=1. La API y el worker verifican esos requisitos nuevamente. No simulan UID: metadata conserva EUID0 y `LAB_ONLY_NOT_NONROOT`. Los controles se heredan por exec; no modifican el shell ni otros procesos del usuario. El bounding set observado también es cero, pero esa condición ambiental no fue fabricada por la función.

Este perfil permite evidencia sintética de laboratorio. No demuestra ejecución nonroot ni autoriza un despliegue como root. El perfil normal sigue rechazando EUID0 incluso después de reducir capabilities. La admisión nonroot en otro entorno necesita recepción allí; el intento fallido original se conserva.

Este wrapper no es una frontera de seguridad frente al mismo UID, al administrador ni al código Python comprometido. No instala un filtro OS de sockets; su topología y código no usan red. Las fuentes del runtime y el intérprete deben ser de confianza. Limita al worker; el supervisor puede consumir memoria al verificar respuestas hasta su máximo permitido. Los archivos de evidencia no contienen credenciales; el digest acredita bytes, no autoría ni corrección matemática.

## Pruebas

`python3 -B infrastructure/tests/test_platform.py --output <directorio-nuevo>` ensaya bytes de entrada/salida, negociación antes del envío, evaluate/verify real, KernelLIMITED entregado, input inválido conservado, candidate inválido, cancelación y validación de caps. En el entorno de namespace documentado, el ensayo ejecutado agrega `--laboratory-root` y reduce capabilities del propio proceso de pruebas antes de empezar. La última corrida autora de plataforma es `validation/F5/author/platform/run04`: ocho casos PASS, snapshot real de identidad, argv y hashes de las fuentes en invocation.json. Se conservan run01 (bloqueo ambiental), run02 y run03. El test de rechazo root normal sigue presente; las pruebas autoras no aceptan por sí solas G5.

Seguridad preservó SEC5-SHAPE: un peer sintético con Result limitado a format/digest era aceptado por el primer supervisor. La reparación añade la gramática exterior cerrada de Specification06, execution/progress/limits, claves de registros y variantes Cell raíz. La verificación de recepción estructural exterior no es validación matemática ni un segundo verificador íntegro de tipos anidados. Para validar el expediente se utiliza verify_result/verify_certificate del Kernel congelado; ese verificador comparte constructores con el evaluador y no es matemáticamente independiente. Ninguna de estas comprobaciones valida premisas empíricas.

Las pruebas autoras de plataforma no sustituyen auditoría o recepción independientes. Las pruebas de seguridad usan peers sintéticos que invocan la misma función apply_containment del bootstrap; sus resultados deben distinguirse del flujo real F4.
