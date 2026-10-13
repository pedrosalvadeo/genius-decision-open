# Modelo de amenazas F5

Componente: GENIUS-INFRASTRUCTURE-1.0.0; perfil `local-fp1-v1`.
Autor funcional: seguridad/amenazas. Este documento es autoría, no dictamen de auditoría.
La aceptación efectiva y los resultados ejecutados están en los informes raíz y
`validation/F5/`. El alcance es Linux local, un operador confiado, código recibido
verificado, datos sintéticos FP1 y un trabajo activo por almacén. No hay endpoint.

## Activos y fronteras

1. Los bytes de Input, Result y Candidate, sus vínculos de digest, certificados,
   premisas, tablas parciales y estados matemáticos. El wrapper no modifica su
   interpretación ni añade una regla de elección.
2. Evidencia de intento, fallo, cancelación, versión y recuperación; su pérdida
   puede impedir demostrar qué se entregó, aunque el cálculo haya sucedido.
3. Disponibilidad de CPU, memoria virtual, pipes y almacenamiento locales.
4. Código e intérprete elegidos por el operador; el release identifica sus fuentes.

El operador escoge archivos locales y parámetros operativos. Los blobs FP1 son
entradas no confiables: su gramática admite datos, nunca programas o rutas que
el Kernel deba abrir. Supervisor y almacén pertenecen al mismo usuario local;
el worker es un proceso separado de ese usuario. El SO, intérprete, código,
cuenta y directorios antecesores administrados por el operador son la base de
confianza. Un hash no autentica esa base ni al autor de un artefacto.

El rechazo de UID 0 evita que la CLI funcione por defecto con privilegios de
administración. Se intentó lanzar los ensayos como `nobody`, pero el entorno solo mapea UID/GID
`0 0 1`: chown devolvió EINVAL antes de ejecutar. Se conserva ese negativo.
ENV01 autoriza únicamente el opt-in explícito `lab_single_uid_root` dentro de
ese namespace exacto, con capacidades efectivas/permitidas/heredables/ambientales
retiradas y NoNewPrivs=1, comprobados realmente. UID sigue siendo 0; esto no
acredita ejecución no-root ni cuenta dedicada y no habilita despliegue piloto.
Un operador fuera de este laboratorio debe usar una cuenta sin privilegios y
un almacén privado; esa combinación necesita su propio ensayo.

## Riesgos ordenados por efecto y condición

| ID | Amenaza, condición e impacto | Control y evidencia vinculada | Residuo |
|---|---|---|---|
| T01 | Entrada finita enorme o patológica retiene CPU/memoria; prioridad alta para disponibilidad local | Worker separado; RLIMIT_CPU y RLIMIT_AS; deadline y drenaje acotado; SEC5-CPU/AS/WALL | Presupuesto por worker, no cgroup del host; un cálculo útil puede ser interrumpido |
| T02 | Pipe bloqueado, salida excesiva o truncación se recibe como resultado; prioridad alta para integridad | Caps separados, lectura no bloqueante, EOF/JSON/ID/envelope/digest; SEC5-OUT/ERR/PARTIAL | La terminación puede ocurrir tras calcular y antes de entregar; no promete exactamente una vez |
| T03 | Entorno o cwd introducen imports/credenciales; impacto alto si el host los proporciona | Python -I -S -B, rutas explícitas y env mínimo; SEC5-ENV | No resiste modificación del intérprete, código confiado ni atacante de mismo UID |
| T04 | Muerte del supervisor abandona worker; disponibilidad y trazabilidad | Nueva sesión, señales/cancelación, kill/reap; Linux PDEATHSIG y comprobación del padre; SEC5-CANCEL/PARENT | El kernel/host y posibles descendientes de código comprometido quedan fuera; zombie sin ejecución depende de reaper externo |
| T05 | Path, enlace, overwrite o escritor concurrente alteran expediente; impacto alto en integridad | Almacén privado, rutas cerradas, dirfds/no-follow, creación exclusiva, lock no bloqueante; pruebas DATA | No protege contra cuenta propietaria maliciosa, root o host comprometido |
| T06 | Interrupción, disco lleno, corrupción o rollback errado dejan éxito ficticio; impacto alto | Staging/commit, inventario+hashes, backup/restauración a destino nuevo y fallo visible; pruebas DATA y recepción | fsync no demuestra supervivencia a cualquier hardware/fallo de alimentación; backups locales comparten host |
| T07 | Metadatos confunden límite operativo con inviabilidad, LIMITED o prueba matemática; impacto alto en significado | Estados del supervisor separados, Result completo preservado; pruebas de operación real y negativos | Verificador Kernel comparte constructores; no es segunda implementación matemática |
| T08 | Logs o artefactos exponen contenido; condición actual: solo sintéticos | Eventos operativos sin payload, permisos privados y entorno sin credenciales | No cifrado; input/result contienen datos completos y digests pueden correlacionarlos; datos reales no autorizados |
| T09 | Release/manifiesto manipulado parece auténtico | Original F4+comprobante preservados, manifiesto nuevo, reproducción independiente, trazabilidad Git | SHA-256 acredita identidad respecto del comprobante, no autoría, matemática ni verdad empírica |

T01/T02/T04/T05/T06 son condiciones que los ensayos provocan de forma acotada.
Su existencia no implica un incidente real anterior. T03/T08/T09 describen
amenazas plausibles y controles comprobables; no se afirma que hubiese una
intrusión, filtración o manipulación en F4. Las variantes de red, usuarios
remotos, autenticación, autorización multicliente y ejecución de código de
solicitantes no pertenecen al despliegue elegido.

## Límites aceptables solo para este alcance

No se construye un sandbox contra código hostil. No hay namespaces, seccomp,
contenedor, cuota global del SO, cifrado, firma de autoría ni prohibición de
sockets del kernel. Los rlimits no equivalen a esas capacidades. FSIZE=0 limita
bytes en archivos regulares, pero no prohíbe crear un archivo vacío, abrir un
socket, modificar nombres ni borrar archivos si los permisos lo permiten.

El proceso no recibe credenciales ni configura servicios remotos. Los fallos
y reintentos conservan sus identidades: un ID RPC no es ID de instancia ni llave
de deduplicación. Preservar hashes y pasar pruebas sintéticas no acredita
utilidad real, ausencia universal de defectos ni suficiencia matemática fuera
de FP1. La aprobación de estos residuos corresponde al Integrador dentro del
mandato local autorizado; un uso distinto necesita nuevo modelo y recepción.
