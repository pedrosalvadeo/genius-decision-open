# Incidentes, parada y recuperación local

Runbook de Infrastructure1.0 para un operador y un store local. Ejecutar desde la raíz de la release verificada. Las rutas de ejemplo deben sustituirse por directorios privados reales; los destinos deben ser nuevos y estar fuera del origen. No requieren red, credenciales ni servicios externos. El [estado de aceptación](../../ACCEPTANCE_REPORT.md) determina el alcance acreditado; este runbook no amplía el gate.

Los comandos siguientes usan `local-fp1-single-uid-lab-v1`, el entorno efectivamente ensayado: EUID0 en namespace de un solo UID/GID, capabilities0 y NoNewPrivs1. El programa rechaza ese perfil fuera de sus condiciones; no sustituye a un usuario nonroot ni prueba ese despliegue. El perfil normal disponible en la API es `local-fp1-v1` y exige Linux nonroot, cuyo funcionamiento no se acredita mediante los ensayos del laboratorio.

## 1. Detener e identificar el intento

1. Detener la presentación de nuevos trabajos. No existe cola del servicio: las invocaciones posteriores deben detenerse en su llamante.
2. Si el supervisor está en primer plano, enviar Ctrl-C una vez; desde otro terminal, enviar SIGTERM únicamente al PID conocido de esa invocación (`kill -TERM PID`). Conservar el PID y la hora. No terminar indiscriminadamente otros procesos Python.
3. Esperar el cierre del supervisor y conservar stdout, stderr y código de salida de la invocación. SIGINT/SIGTERM permiten registrar cancelación si el disco admite escrituras. SIGKILL o un fallo del host pueden dejar solo staging. Ningún procedimiento puede garantizar registrar el cierre de un proceso al que ya no se permite ejecutar.
4. No editar `input.json`, `result.json`, `start.json`, `outcome.json` ni manifiestos. No borrar staging para que desaparezca el incidente. Un worker terminado no demuestra inexistencia de solución ni inviabilidad.
5. Ejecutar la inspección siguiente; si devuelve BUSY, aún hay un propietario del lock. Eliminar `.lock` no es una forma válida de desbloquearlo. Cuando el proceso realmente termina, el sistema libera flock.

```
python3 -I infrastructure/operate.py check --store /ruta/privada/store --profile local-fp1-single-uid-lab-v1
```

`check` con PASS significa inventario/permisos/hashes correctos para runs comprometidos. La lista `incomplete` puede ser no vacía: sus archivos permanecen incompletos y no se validan matemáticamente por ese PASS. `COMMITTED` tampoco equivale a cálculo satisfactorio; consultar los metadatos operativos y el Result/report íntegro. El ID del expediente es identidad operacional, no ID RPC ni identidad matemática.

## 2. Registrar el incidente sin alterar evidencia

Crear un registro separado con fecha UTC, release y versiones, comando y límites elegidos, run_id conocido, código de salida, estado BUSY/FAILED/CANCELLED o error de filesystem, controles ejecutados y referencias a las copias conservadas. Los logs generales no necesitan incorporar payloads ni credenciales. Los archivos del store son evidencia privada y pueden incluir input/result completos.

Para un staging que no llegó a commit, no inferir que un archivo presente está completo: la interrupción puede haber ocurrido durante su escritura. Conservarlo tal como está. Si se necesita reusar ese input, cotejar sus bytes con la fuente original o con un digest previo confiable de la entrada completa; un hash calculado después del incidente solo identifica lo que sobrevivió.

Si hubo error después del rename/fsync, un run completo puede existir aunque la invocación devolviera error. Inspeccionar antes de reintentar. No hay confirmación exactamente una vez ni garantía de que un cálculo no ocurrió por no haber recibido su confirmación.

## 3. Reintentar

Reintentar solo después de determinar la causa operacional y conservar el intento anterior. Usar el input original exacto y los mismos límites cuando se busca reproducción; si se cambian límites, registrar el cambio. `--retry-of` correlaciona intentos y no los deduplica. Una nueva invocación siempre crea otro run.

```
python3 -I infrastructure/operate.py run --store /ruta/privada/store --profile local-fp1-single-uid-lab-v1 --method evaluate --input /ruta/privada/original-input.json --retry-of run-ID_ANTERIOR
```

Sustituir `run-ID_ANTERIOR` por el identificador real emitido o encontrado en staging. No usar literalmente el ejemplo. Para `verify_result` o `verify_certificate`, añadir `--candidate` con el candidato exacto original. Si la fuente original no se recuperó, registrar esa pérdida; no completar bytes faltantes ni presentar un input reconstruido como el original.

## 4. Cuota agotada, ENOSPC o permiso denegado

- Cuota lógica: `check` y `store.json` permiten conocer tamaños y límites. Los intentos incompletos también consumen cuota; no existe purga automática. Conservar el store y continuar en otro nuevo si es necesario.
- ENOSPC: detener entradas nuevas. Puede no haber espacio para logs, un backup en el mismo filesystem o la metadata final. Conservar el prefijo sobreviviente; la transacción que sufrió error de escritura queda inutilizable y no puede hacer commit. Preparar un destino privado con capacidad suficiente fuera del origen y realizar backup cuando el filesystem vuelva a admitir la operación. Este handoff no demuestra recuperación ante pérdida física del disco.
- EACCES/permisos: verificar propietario y permisos sin ampliar a 0777. Los stores requieren propietario operador, directorios0700 y archivos0600. Si hay desviaciones, conservar su evidencia y determinar su causa antes de corregir permisos o elegir una copia válida. Un cambio de permisos no repara bytes corruptos.
- No extraer conclusiones matemáticas de ninguno de estos errores. La CLI informa OPERATION_FAILED y errno cuando existe; el detalle exacto de StoreError puede necesitar inspección del expediente con la API o el auditor.

ENOSPC y EIO se ensayaron mediante inyección acotada, no llenando el disco compartido. EACCES se produjo realmente contra un directorio0500 en ENV01 sin CAP_DAC_OVERRIDE.

## 5. Backup y restauración demostrable

Con el store inactivo y verificable, crear una instantánea en un destino nuevo; conservar su comprobante JSON con SHA-256 de BACKUP.json. Ese digest identifica bytes, no autoría. Backup incorpora staging sin promoverlo a run terminado.

```
python3 -I infrastructure/operate.py backup --store /ruta/privada/store --destination /ruta/privada/snapshot01 --profile local-fp1-single-uid-lab-v1
python3 -I infrastructure/operate.py restore --backup /ruta/privada/snapshot01 --destination /ruta/privada/restored01 --profile local-fp1-single-uid-lab-v1
python3 -I infrastructure/operate.py check --store /ruta/privada/restored01 --profile local-fp1-single-uid-lab-v1
```

Comparar los runs, hashes, tamaños y staging del store restaurado con el snapshot seleccionado. Para un flujo semántico completo, verificar un par input/result comprometido mediante la interfaz F4:

```
python3 -I infrastructure/operate.py run --store /ruta/privada/restored01 --profile local-fp1-single-uid-lab-v1 --method verify_result --input /ruta/privada/restored01/runs/RUN_ID/input.json --candidate /ruta/privada/restored01/runs/RUN_ID/result.json
```

Ese comando agrega un intento nuevo; realizar la comparación de identidad del snapshot antes. Leer el `report.json` de ese nuevo intento: DELIVERED solo acredita la entrega, no que el report sea VALID. La verificación matemática sigue siendo condicional al input y sus premisas.

Un backup interrumpido sin BACKUP.json o con inventario/hash discrepante no restaura. Una restauración interrumpida queda en su destino nuevo incompleto; conservarla, y usar otro destino nuevo para el siguiente intento. No existe reparación automática de snapshots ni sobrescritura de destinos. Destinos dentro del origen se rechazan antes de escribir.

## 6. Corrupción

Ante hash, inventario o formato discrepante: detener nuevos trabajos, conservar fuente y reporte, y rechazar su uso como la evidencia identificada. No regenerar manifiestos para hacer PASS. El backup ordinario valida la fuente y rechazará un store corrupto; esto es un control, no un mecanismo para archivar forensemente cualquier árbol dañado.

Restaurar una copia previa verificada en otro directorio mediante el procedimiento anterior. El original corrupto permanece conservado. Sin copia válida, el dato afectado no está recuperado. Una reevaluación del input original puede ser un experimento nuevo, nunca sustitución silenciosa del resultado histórico perdido.

## 7. Rollback de datos y de software

Rollback de datos selecciona una instantánea anterior y crea otro store:

```
python3 -I infrastructure/operate.py rollback --backup /ruta/privada/snapshot01 --destination /ruta/privada/rollback01 --profile local-fp1-single-uid-lab-v1
python3 -I infrastructure/operate.py check --store /ruta/privada/rollback01 --profile local-fp1-single-uid-lab-v1
```

Indicar explícitamente `--store /ruta/privada/rollback01` en invocaciones futuras. El store con operaciones posteriores no se borra ni se fusiona. Rollback no revierte efectos externos, reanuda cálculos ni modifica la matemática.

Para volver al software F4: detener el wrapper F5, conservar stores y evidencia, verificar tamaño/SHA-256 de [ZIP F4](../../history/GENIUS_PHASE_4_HANDOFF.zip) contra su [comprobante](../../history/GENIUS_PHASE_4_VERIFICATION.json), extraer en un directorio nuevo y ejecutar allí `python3 tools/verify_package.py`. Seguir su README para su interfaz local stdio. F4 carece de los límites duros/almacenamiento F5; volver a F4 no mantiene implícitamente esos controles. No mezclar archivos de ambas releases bajo la misma identidad ni seguir ejecutando un proceso cuyas fuentes se cambian.

## Evidencia aplicable

La [matriz de datos](DATA_TRACE.md) vincula estos procedimientos con17casos de autor y sus límites; la [guía de datos](DATA_RECOVERY.md) define API y cuotas. Auditoría y recepción se consultan en sus informes separados; el runbook no se autocertifica.
