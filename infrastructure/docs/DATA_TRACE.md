# Trazabilidad de datos y recuperación F5

Autor funcional Datos, 2026-09-26. Requisitos del [mandato F5](../../PHASE_5_PROMPT.md), §3.3–3.6 y §4; formatos preservados de [Specification01](../../GENIUS_PROGRAM/specification/01_TYPES_AND_WIRE.md), [Specification06](../../GENIUS_PROGRAM/specification/06_OUTPUT_AND_DIAGNOSTICS.md) y [Protocols P04/P07](../../protocols/CONTRACT.md). Implementación: [storage.py](../genius_infra/storage.py). Contrato operacional: [DATA_RECOVERY](DATA_RECOVERY.md) y [INCIDENTS](INCIDENTS.md).

Todas las filas siguientes usan el [reporte RUN_04](../../validation/F5/author/data/RUN_04/REPORT.json) y su [snapshot portable](../../validation/F5/author/data/RUN_04/SNAPSHOT.json), ejecutados por el autor. La [suite reproducible](../tests/test_storage.py) tiene17casos; no son17validaciones matemáticas ni auditoría externa. El resultado fue17/17PASS bajo CPython3.12.14, EUID0 namespace0→0/1, CapInh/Prm/Eff/Bnd/Amb0 y NoNewPrivs1. Esa identidad es LAB_ONLY_NOT_NONROOT.

| ID | Requisito y control implementado | Ensayo ejecutado | Resultado y límite |
|---|---|---|---|
| DATA01 | Bytes portables exactos y ausencia de sobrescritura; input/result opacos, O_EXCL y manifiesto | `test_01_exact_bytes_and_no_overwrite` | PASS: preserva bytes incluso UTF-8 inválido y cadenas de racionales grandes. Comprueba almacenamiento, no validez matemática del fixture. |
| DATA02 | Un trabajo por store, lock no bloqueante durante operación | `test_02_lock_other_process_and_release` | PASS con segundo proceso real: BUSY mientras hay lock, adquirido tras liberarse. Sin cola, deduplicación ni exactamente una vez. |
| DATA03 | Campos no se convierten en rutas; nombres simples, reservados y rechazo traversal | `test_03_paths_and_artifact_traversal` | PASS para rutas absolutas/nested/`..`/nombres reservados. Store solo admite los directorios internos definidos. |
| DATA04 | No seguir symlinks en raíz, ancestros o artefactos; descriptores O_NOFOLLOW | `test_04_symlink_root_ancestor_and_artifact` | PASS con symlinks reales. No acredita aislamiento ante actor hostil con mismo UID/host. |
| DATA05 | Archivos regulares con un solo enlace; impedir hardlinks y FIFO | `test_05_hardlink_and_fifo_rejected` | PASS con ambos tipos reales, sin bloquear lectura de FIFO. Snapshots describen tipos especiales; el ZIP no los activa. |
| DATA06 | Directorios0700, archivos0600, propietario operador; fallo ante permiso denegado | `test_06_owner_modes_and_actual_permission_denied` | PASS: modo0755 rechazado por API y EACCES real ante destino0500 después de retirar capabilities. No se afirma ensayo nonroot. |
| DATA07 | Detectar corrupción, faltantes, adicionales e inventario incoherente | `test_07_corruption_missing_extra_detected` | PASS: mutación de bytes, renombre que elimina archivo esperado y extra no listado. Hashes no autentican autoría ni matemática. |
| DATA08 | Mantener entrada aceptada e intento incompleto tras muerte | `test_08_real_process_kill_preserves_pending` | PASS: proceso real recibe SIGKILL después de begin; lock liberado, input exacto y staging INCOMPLETE, cero runs. No es corte físico de energía. |
| DATA09 | Error de escritura parcial no se publica ni permite commit posterior | `test_09_injected_enospc_partial_never_committed` | PASS con ENOSPC inyectado después de3bytes. Staging conserva prefijo; transacción inutilizable. No se llenó el disco real. |
| DATA10 | Backup/restore íntegros y rollback de datos a snapshot anterior sin borrar historia | `test_10_backup_restore_and_data_rollback` | PASS: snapshot incluye run y staging, segundo run queda solo en store original, restore reproduce snapshot y rechaza overwrite. Copia local, sin protección frente a pérdida del host. |
| DATA11 | Rechazar snapshot corrupto y no usar rutas del manifest como destinos | `test_11_corrupt_backup_and_malicious_manifest` | PASS: corrupción rechazada antes de crear destino; ruta `../../outside` nunca se materializa. El caso con manifest malicioso también mantiene corrupción previa, por lo que no acredita por sí solo un oráculo aislado de traversal de manifest; la implementación enumera nombres reales y compara mapa completo. |
| DATA12 | Backup incompleto no es restorable | `test_12_backup_interruption_incomplete_not_restorable` | PASS: EIO de copia inyectado; falta marcador BACKUP.json; restauración rechazada. No implica atomicidad de toda la carpeta de backup. |
| DATA13 | Cuotas declaradas, lock obligatorio y fallo operacional al exceder recursos | `test_13_limits_and_lock_requirement` | PASS: límite archivo/recuento y límites inválidos; begin sin lock rechazado. Cuotas son bytes lógicos, no espacio físico reservado ni KernelLIMITED. |
| DATA14 | No confirmar éxito si falla persistencia posterior a publicación | `test_14_post_rename_sync_failure_is_not_acknowledged` | PASS con fsync EIO inyectado tras rename: hay run visible, commit devolvió error. Operador debe inspeccionar; no hay exactly-once. |
| DATA15 | Inventario de snapshot incluye directorios vacíos | `test_15_backup_empty_directory_inventory` | PASS: staging vacío agregado al backup hace fallar integridad. No se certifica solo la lista de archivos. |
| DATA16 | Límite de artefactos y metadatos sin claves duplicadas | `test_16_artifact_count_and_metadata_duplicates` | PASS:33artefactos rechazados y configuración con clave duplicada rechazada. No altera parser matemático F4. |
| DATA17 | Copia/restore nunca modifica el inventario de su fuente | `test_17_nested_destinations_cannot_mutate_sources` | PASS: destinos dentro de fuente rechazados antes de crear, origen conserva identidad y sigue restaurable. |

## Defectos conservados y reparación

| Hallazgo | Evidencia anterior | Reparación y regresión |
|---|---|---|
| F5-DATA-001: commit tras escritura parcial | [Expediente](../../validation/F5/author/data/findings/F5-DATA-001/FINDING.md), código anterior y before.json | Transaction.poisoned impide add/commit después de excepción de escritura; after.json y DATA09. |
| F5-DATA-002: destino de backup dentro del store alteraba origen | [Expediente](../../validation/F5/author/data/findings/F5-DATA-002/FINDING.md), código anterior y before.json | Rechazo temprano DESTINATION_INSIDE_SOURCE en backup/restore; after.json y DATA17. |

Ambos son defectos de desarrollo F5 demostrados por el autor. No se atribuyen a F4 ni se regeneraron manifiestos para esconderlos. Auditoría y recepción separadas determinan su cierre formal.

## Evidencia anterior y alcance que permanece fuera

[RUN_01](../../validation/F5/author/data/RUN_01/REPORT.json) preserva15PASS y un fallo del arnés al intentar UID65534 no mapeado. [RUN_02](../../validation/F5/author/data/RUN_02/REPORT.json) preserva16errores de preparación por ruta `..` del arnés; ninguna de esas16pruebas se acredita allí. Sus listas iniciales estáticas de controles eran objetivos del arnés, no pruebas aprobadas. [RUN_03](../../validation/F5/author/data/RUN_03/REPORT.json) tiene16PASS tras reparación de entorno/arnés y DATA001. RUN_04 repite16 y agrega DATA17; no se suman las repeticiones como muestras independientes.

No se ensayaron pérdida física de energía/disco, restauración remota, NFS, propietario hostil, despliegue nonroot, purga automática, snapshots firmados, autenticidad, privacidad frente al mismo UID ni verdad empírica. La ausencia de credenciales es parte del alcance sintético; storage no inspecciona semánticamente cada blob para detectar secretos. Retención, versiones operativas, hashes y guía de incidentes están documentados, y la lectura matemática sigue perteneciendo al contrato y verificadores heredados.
