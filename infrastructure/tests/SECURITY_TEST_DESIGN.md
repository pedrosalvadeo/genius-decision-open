# Prerregistro de ensayos de seguridad autor F5

Fecha 2026-09-26. Se fija antes de la primera corrida. Sujeto: Infrastructure
1.0.0. Los sources antes/después se conservan por corrida. Los once casos usan
peers confiados sintéticos y `apply_containment` compartido con el worker real;
no modifican Kernel, Protocols ni fuentes F4. La validación de `run_worker` sí
se ejerce, salvo SEC5-ENV que inspecciona el transporte privado de ensayo.

| Caso | Estímulo acotado | Oráculo previo |
|---|---|---|
| SEC5-CPU | Spin con CPU soft=hard=1 s, wall=5 s | EXIT_NONZERO; SIGKILL/SIGXCPU; termina antes de wall; sin Result; reaped |
| SEC5-AS | Solicitar bytearray128MiB con AS64MiB | MemoryError controlado, exit74, EXIT_NONZERO; sin Result; reaped |
| SEC5-WALL | Sleep30s, wall0.35s | WALL_LIMIT; tiempo observado menor2s; sin Result; reaped |
| SEC5-OUT | Flood stdout, cap8192B | STDOUT_LIMIT; prefijo8192B explícito; sin Result; reaped |
| SEC5-ERR | Flood stderr, cap4096B | STDERR_LIMIT; prefijo4096B explícito; sin Result; reaped |
| SEC5-PARTIAL | Handshake válido, JSON parcial y EOF0 | TRANSPORT_INCOMPLETE_OR_INVALID; sin Result; reaped |
| SEC5-ID | Respuesta JSON completa con ID extranjero | TRANSPORT_INCOMPLETE_OR_INVALID; sin Result; reaped |
| SEC5-NEGOTIATE | Versión wire no compatible | INITIALIZATION_INVALID; instancia nunca transmitida; sin Result; reaped |
| SEC5-CANCEL | Evento cancel durante sleep | CANCELLED como status/reason; sin Result; reaped |
| SEC5-ENV | Env con marcadores sintéticos/sitecustomize trampa; inspector | UID distinto0; -I/-S/-B observados; env no heredado; rlimits CPU/AS/CORE/FSIZE/NOFILE exactos; EMFILE y EFBIG reales; file size0 |
| SEC5-PARENT | Supervisor separado SIGKILL después de worker dormido | Worker desaparece o queda zombie sin ejecutar dentro2s; no claim de reaper host |

La suite se lanza con UID sin privilegios y escribe en destino nuevo. Fallos de
oráculo/arnés se conservan y clasifican, y no se promueven a defectos de producto
sin testigo. Todos los fallos de proceso se comprueban contra la separación de
estados: no DELIVERY, ni Result/execution.LIMITED inventado. La evidencia cruda
usa datos sintéticos; no escanea ni vuelca variables reales.


## Enmienda ENV01 / SEC5-SHAPE, previa a la corrida completa

El primer intento como nobody falló antes de ejecutar por EINVAL en chown y
mapeo UID/GID único `0 0 1`. Negativo NON_ROOT_ATTEMPT_01.json preservado. La
suite admite opt-in `--lab-single-uid-root`, llama enter_lab_containment solo
en su propio subprocess, conserva UID0 y comprueba capacidades0/NNP1 reales.
SEC5-ENV en ese perfil exige UID0 y retiro de capacidades; además exige que la
API normal siga rechazando UID0 aun con capacidades retiradas. No acredita
operación no-root, por lo que el oráculo de identidad inicial se sustituye
explícitamente en este perfil de laboratorio. Los demás oráculos no cambian.

Se incorpora caso12 SEC5-SHAPE: envelope correcto con Result incompleto solo
format/input_digest debe rechazarse TRANSPORT_INCOMPLETE_OR_INVALID, sin
result.json ni entrega. El negativo ejecutado contra snapshot del sujeto
anterior demostró DELIVERED/OK; evidencia íntegra en
validation/F5/author/security/SEC5-SHAPE_FINDING. No cambió ningún componente F4.

## Reparaciones del arnés tras RUN_01

Se preservan RUN_01, sus errores y fuentes. Procfs numérico refleja otro namespace
que los PIDs devueltos por subprocess; se usa waitpid/kill(pid,0) para recolección
y pidfd_open/select para confirmar muerte del worker tras SIGKILL del padre.
El fixture emite readiness mediante directorio vacío después de aplicar controles;
FSIZE0 no se relaja. Tempfile usa /tmp explícito porque su autodetección escribe
un archivo y fallaba bajo FSIZE0. Los oráculos CPU/AS/plazo/bytes/estados siguen
idénticos; RUN_02 repite toda la suite y conserva hashes antes/después.
