# Datos, integridad y recuperación — Infrastructure 1.0

Autor funcional: Datos. Este documento describe los controles implementados en `../genius_infra/storage.py`; la auditoría y recepción final corresponden a agentes separados. Alcance local Linux, propietario único, directorios ancestros y procesos del mismo UID confiables. Datos sintéticos del paquete, sin credenciales. Se conserva la Specification 01/06 y el contrato Protocols F4: el almacenamiento trata input, candidate y Result como bytes opacos y no cambia Nat/Q/Bit, certificados, premisas, ramas, tablas ni estados matemáticos.

## Unidad portable y estados operativos

Una evaluación entregada mantiene `input.json` y `result.json` exactos. Verificación conserva input y candidate exactos más respuesta/report. La capa de protocolo valida el vínculo `Result.input_digest`; storage agrega un manifiesto de los bytes recibidos, sin sustituir al verificador matemático. Todo certificado de Result permanece dentro de ese archivo completo; un candidato independiente sigue acompañado por su input original.

```
with store.exclusive():
    tx = store.begin({"input.json": input_bytes}, start_metadata)
    outcome = run_worker(...)
    tx.add(outcome.artifacts)
    run_id = tx.commit(outcome.metadata)
```

`begin` crea un identificador operacional UUID, distinto del ID RPC y de toda identidad matemática. Persiste input/candidate y `start.json` antes del worker. `add` crea exclusivamente archivos nuevos; `commit` agrega `outcome.json` y `MANIFEST.json`, comprueba el expediente y mueve el directorio desde `staging/` a `runs/` mediante rename bajo lock. Los archivos se sincronizan y también los directorios afectados. El lock se mantiene durante toda la ejecución y publicación; otro cliente recibe BUSY inmediatamente. No hay cola ni promesa exactamente una vez.

`COMMITTED` describe expediente completo, no éxito de cálculo. Puede contener un fallo operacional, cancelación o Result matemático LIMITED/ERROR; esos estados no se sustituyen por conclusiones de inviabilidad. Un directorio en staging es INCOMPLETE incluso si contiene un manifiesto válido: nunca se promueve automáticamente. Los fallos de escritura invalidan la transacción en memoria, impidiendo que un prefijo escrito parcialmente se certifique después. Reintentar crea nueva identidad y puede registrar `retry_of`; no deduplica ni reanuda la matemática.

Un error de fsync después del rename puede coexistir con un expediente visible y completo. La operación devuelve error y el operador debe inspeccionar el store: la ausencia de confirmación no demuestra ausencia de ejecución. La suite incluye este caso. No se ensayaron cortes físicos de energía ni garantías de hardware; fsync y rename no se presentan como esas pruebas.

## Rutas, permisos y cuotas

Store y subdirectorios exigen propietario EUID y modo 0700; archivos 0600. Se abren todos los componentes de ruta por descriptores con O_DIRECTORY/O_NOFOLLOW; archivos con O_NOFOLLOW y escritura O_EXCL. Solo archivos regulares con un enlace; se rechazan symlinks, hardlinks, FIFO, traversal, nombres de directorios internos inesperados y permisos amplios. La API no sobrescribe artefactos, manifests, destinos de backup o restauraciones. La defensa depende de ancestros y UID confiables; no contiene un atacante con la misma autoridad o control del host.

El perfil explícito `local-fp1-v1` aplica los máximos siguientes, que pueden reducirse al crear un store. Los valores se conservan en `store.json`, no en el problema matemático. Las cuotas excesivas causan fallo operacional, nunca KernelLIMITED inventado.

| Recurso | Máximo |
|---|---:|
| Archivo individual | 48 MiB |
| Expediente completo | 96 MiB |
| Bytes de archivos del store | 512 MiB |
| Expedientes, incluyendo staging | 128 |
| Artefactos por expediente | 32, más start/outcome/manifest |
| Cada metadato/manifiesto | 1 MiB |

Son cuotas de bytes lógicos de archivos, no reserva física de disco, inodos o memoria. Una escritura puede fallar por ENOSPC antes de alcanzar la cuota; se preserva su prefijo como evidencia incompleta. El contenido de los archivos se lee con tamaños acotados. Los nombres de artefacto son basenames de hasta 64 caracteres de `[a-z][a-z0-9_.-]*`; `start.json`, `outcome.json` y `MANIFEST.json` son reservados. Campos matemáticos nunca se usan como rutas.

No hay borrado por TTL ni purga automática. Los negativos e intentos incompletos consumen cuota y se conservan. Si se necesita reducir retención, primero se realiza backup verificado; el operador puede continuar en un store nuevo y conservar el anterior. Esta versión no implementa eliminación selectiva. Los metadatos no necesitan secretos; el CLI solo genera campos operacionales permitidos. Storage como API Python acepta metadatos del llamante confiable y no promete detectar una credencial pegada arbitrariamente en un input o metadata.

## Backup, restauración y rollback

`store.backup(destination)` exige el lock exclusivo y verifica primero todo el store. Crea un destino nuevo con `store.json`, `runs`, `staging` y escribe `BACKUP.json` al final. Este manifiesto registra inventario de directorios y hashes/tamaños de todos los archivos. Incluye staging sin convertirlo en resultado. Devuelve SHA-256 de BACKUP.json como referencia verificable de bytes, sin autenticar autoría. El backup es una copia local, no protección ante pérdida del disco/host.

`Store.restore(source, destination)` valida inventario, cuotas, manifiestos de runs y snapshot antes de crear el destino nuevo. Backup y restore rechazan destinos situados dentro de su origen antes de crear nada, preservando su inventario. Nunca usa rutas dictadas por el manifiesto; enumera y valida nombres reales. Compara otra vez los bytes al copiarlos. El marcador `store.json` se escribe al final de la restauración y después se verifica el nuevo store. Un backup incompleto/corrupto no restaura; un restore interrumpido conserva un destino incompleto, que no debe confundirse con un store listo. El destino anterior no se modifica.

Rollback de datos es restaurar un snapshot anterior en otro directorio y seleccionar explícitamente ese store en próximas operaciones. El store con operaciones posteriores se conserva. No revierte acciones externas ni la ejecución matemática; no cambia versiones del Kernel. Rollback de software requiere volver a una release verificada completa según la guía operacional, sin mezclar módulos de releases distintas.

Procedimiento de incidente: detener nuevos jobs; conservar proceso/código de salida y staging; ejecutar `verify`; si falla integridad, no regenerar hashes; conservar el original y restaurar una copia válida en un destino nuevo; verificar esa copia y repetir un flujo completo; registrar el incidente y nuevo intento. Si falta copia válida, el dato afectado permanece no recuperado: no se inventa ni reevalúa silenciosamente para ocultar la pérdida.

## Evidencia y límites de ensayo

`../tests/test_storage.py` comprueba byte exacto y rechazo de overwrite, lock de otro proceso, rutas, symlinks/hardlinks/FIFO, permisos, corrupción/ausentes/adicionales, SIGKILL de un proceso real tras begin, backup/restore/rollback, cuotas y negativos. ENOSPC después de escritura parcial, EIO en backup y EIO después de rename se inyectan explícitamente; no se llena el disco compartido. La prueba de permisos exige proceso sin CAP_DAC_OVERRIDE, y su condición real se registra en el informe. Los fixtures de tipos especiales se reconstruyen por el script; snapshots JSON registran su tipo y bytes para no distribuir symlinks/FIFO como archivos del paquete.

F5-DATA-001 conserva el fallo de autor en el que un commit posterior a ENOSPC podía certificar un prefijo. La reparación mínima marca la transacción como inutilizable tras excepción de escritura y el test09 exige rechazo del commit posterior. No es un defecto de F4 ni una modificación matemática. La primera ejecución del arnés intentó cambiar UID en un namespace que solo mapea UID0; falló errno22 y se conserva como fallo del arnés, no prueba de permisos ejecutada.

F5-DATA-002 conserva el fallo de autor por permitir destino de backup dentro del store, que alteraba el inventario original. La reparación rechaza esa ubicación en backup y restore antes de escribir; test17 demuestra conservación del origen. La repetición final RUN_04 aprobó17casos. Los reportes efectivos se encuentran en `../../validation/F5/author/data/`. Pasar esta suite es evidencia de autor, no G5 ni auditoría independiente.

## Fuentes primarias

Consultadas 2026-09-26, documentación CPython 3.12.14:

- https://docs.python.org/3.12/library/os.html — API de descriptores, opciones de apertura, escritura/fsync y rename. La implementación exige las facilidades Linux observadas; no se afirma soporte multiplataforma.
- https://docs.python.org/3.12/library/fcntl.html — exclusión no bloqueante con flock. El bloqueo es cooperativo, no autenticación ni contención del propietario hostil.
