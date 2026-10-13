# Genius Infrastructure — operación local FP1

Producto `GENIUS-INFRASTRUCTURE-1.0.0`. Linux, CPython3.12.14 observado,
biblioteca estándar. Supervisor y almacenamiento nuevos alrededor de
Protocols1.0.0 y Kernel1.0.1 intactos. No se instala ningún servicio.

El estado de recepción y del gate está en [ACCEPTANCE_REPORT](../ACCEPTANCE_REPORT.md);
estas instrucciones no constituyen aceptación ni autorización de despliegue.
El perfil normal se ejecuta como usuario **no root**, con código confiable y una carpeta privada
de trabajo en un filesystem Linux local. El propietario del store debe ser
quien opera los comandos. No hay soporte para NFS, usuarios hostiles del mismo
UID, código aportado por terceros ni host comprometido.

## Flujo completo

Desde la raíz del paquete, sustituir `/ruta/privada` por una carpeta existente
controlada por el operador. Usar destinos nuevos para store y snapshots.

```bash
python3 -I infrastructure/operate.py init --store /ruta/privada/store --profile local-fp1-v1
python3 -I infrastructure/operate.py run --store /ruta/privada/store --profile local-fp1-v1 --method evaluate --input examples/water_habitat_f4/input.json
python3 -I infrastructure/operate.py check --store /ruta/privada/store --profile local-fp1-v1
python3 -I infrastructure/operate.py backup --store /ruta/privada/store --destination /ruta/privada/snapshot01 --profile local-fp1-v1
python3 -I infrastructure/operate.py restore --backup /ruta/privada/snapshot01 --destination /ruta/privada/restored01 --profile local-fp1-v1
python3 -I infrastructure/operate.py check --store /ruta/privada/restored01 --profile local-fp1-v1
```

`run` devuelve el `run_id` generado. El resultado exacto queda en
`store/runs/<run_id>/result.json`, junto a `input.json`, negociación, respuesta,
stdout/stderr privados y metadatos operativos. Para verificarlo mediante G4:

```bash
python3 -I infrastructure/operate.py run --store /ruta/privada/store --profile local-fp1-v1 --method verify_result --input /ruta/privada/store/runs/ID/input.json --candidate /ruta/privada/store/runs/ID/result.json
```

`verify_certificate` usa el mismo par input/candidate, con el envelope de
certificado F4. El reporte verifica la instancia formal, no las premisas del
mundo. `DELIVERED` describe la entrega operativa: puede contener un Result
INVALID/LIMITED o un VerificationReport INVALID/INCOMPLETE. Leer el artefacto.
Un resultado completo recibido antes de una terminación tardía se conserva,
aunque la operación cierre FAILED. No se fabrica un Result tras una salida
incompleta o un timeout.

## Laboratorio con namespace de un único UID

El entorno usado en los ensayos solo mapea UID/GID 0: ambos archivos
`/proc/self/uid_map` y `/proc/self/gid_map` contienen exactamente la terna
`0 0 1` (ignorando whitespace). El intento de usar nobody falló con errno22
y se conserva como evidencia. Para este entorno existe el opt-in separado
`local-fp1-single-uid-lab-v1`, según ADR-F5-ENV01. Solo admite esos mapas y
EUID real 0; no es un perfil genérico para ejecutar como root.

Antes de operar el store, cada comando LAB activa `NoNewPrivs=1` y vacía
capabilities effective, permitted, inheritable y ambient. Verifica los cuatro
conjuntos en cero y el flag en `/proc/self/status`; falla si no puede instalar
o comprobar los controles. El worker los verifica nuevamente. Los metadatos
de ejecución conservan EUID0 y `LAB_ONLY_NOT_NONROOT`: estos ensayos no
demuestran una ejecución nonroot ni autorizan desplegar como root.

La reducción ocurre en el proceso del comando y se hereda por sus workers;
el shell invocante y los demás procesos permanecen sin cambios. Por eso se
elige el perfil LAB en **cada comando**, incluidos check, backup y restore.
Desde la raíz del paquete, con una carpeta privada existente y destinos nuevos:

```bash
python3 -I infrastructure/operate.py init --store /ruta/privada/lab-store --profile local-fp1-single-uid-lab-v1
python3 -I infrastructure/operate.py run --store /ruta/privada/lab-store --profile local-fp1-single-uid-lab-v1 --method evaluate --input examples/water_habitat_f4/input.json
python3 -I infrastructure/operate.py check --store /ruta/privada/lab-store --profile local-fp1-single-uid-lab-v1
python3 -I infrastructure/operate.py backup --store /ruta/privada/lab-store --destination /ruta/privada/lab-snapshot01 --profile local-fp1-single-uid-lab-v1
python3 -I infrastructure/operate.py restore --backup /ruta/privada/lab-snapshot01 --destination /ruta/privada/lab-restored01 --profile local-fp1-single-uid-lab-v1
python3 -I infrastructure/operate.py check --store /ruta/privada/lab-restored01 --profile local-fp1-single-uid-lab-v1
```

Para verificar el resultado, reemplazar `ID` por el run_id devuelto por evaluate:

```bash
python3 -I infrastructure/operate.py run --store /ruta/privada/lab-store --profile local-fp1-single-uid-lab-v1 --method verify_result --input /ruta/privada/lab-store/runs/ID/input.json --candidate /ruta/privada/lab-store/runs/ID/result.json
```

Rollback de datos también exige elegir LAB en este entorno:

```bash
python3 -I infrastructure/operate.py rollback --backup /ruta/privada/lab-snapshot01 --destination /ruta/privada/lab-rollback01 --profile local-fp1-single-uid-lab-v1
```

El perfil normal conserva el rechazo de EUID0 incluso con capabilities vacías.
En otro entorno, operar como usuario nonroot con el perfil normal requiere
comprobar allí identidad, permisos y recuperación. El estado del gate y sus
límites de alcance se determinan por recepción, no por elegir un perfil.

## Perfil que el operador elige expresamente

`--profile` es obligatorio al crear store o ejecutar. Los perfiles
`local-fp1-v1` y `local-fp1-single-uid-lab-v1` comparten estos límites; su
diferencia es la condición de identidad descrita arriba:

| Control | Valor |
|---|---:|
| CPU worker | 10 segundos |
| Espacio de direcciones worker | 256 MiB |
| Tiempo total supervisor | 30 segundos |
| Stdout acumulado worker | 34 MiB |
| Stderr acumulado worker | 64 KiB |
| Input / candidato | 2 MiB / 8 MiB, límites F4 |
| Store / run / archivo / runs | 512 MiB / 96 MiB / 48 MiB / 128 |
| Concurrencia | Un job por store, rechazo BUSY, sin cola |

Overrides operativos explícitos: `--cpu-seconds`, `--address-space-mib`,
`--wall-seconds`, `--max-stdout-bytes`, `--max-stderr-bytes`; se registran en el
expediente. Las cuotas de datos se fijan al crear el store. Son límites de esta
operación, sin modificar H, Π, ramas, precisión ni selección. `--kernel-limits`
recibe un archivo LimitMap F4 opcional. Ausente significa no añadir límites
cooperativos al Kernel; no se infiere un límite matemático del perfil.

## Recuperación, parada y lectura

SIGINT/SIGTERM cancelan el worker y registran resultado operativo cuando el
almacenamiento sigue disponible. SIGKILL del supervisor no puede registrar un
cierre; el worker Linux recibe señal por muerte del padre y staging queda
incompleto. `check` lo identifica sin promoverlo a run terminado. No editar ni
borrar evidencia para volver a intentar: usar un nuevo run y `--retry-of ID`
solo para correlación. Reutilizar ID RPC tampoco deduplica cálculos.

`rollback --backup SNAPSHOT --destination NUEVO_STORE` restaura datos de una
instantánea elegida, sin sobrescribir el store anterior. Para rollback de código,
extraer el ZIP F4 original conservado en history a un directorio nuevo,
verificarlo y usar su CLI; F4 carece de los controles operativos nuevos. Detener
el wrapper antes de cambiar fuentes. No mezclar módulos de releases distintas.

No hay purga automática. Retener runs fallidos e incompletos; ante cuota agotada,
hacer backup verificable y comenzar un store nuevo. Si el filesystem rechaza
escrituras o muere el supervisor, el único registro disponible puede ser staging
y la salida capturada por el invocante. No se promete persistir logs en disco lleno.

Ver [datos y recuperación](docs/DATA_RECOVERY.md), [plataforma](docs/PLATFORM.md),
[amenazas](docs/THREAT_MODEL.md), [seguridad](docs/SECURITY.md) y
[fuentes primarias](docs/SOURCES.md). El paquete conserva evidencia sintética;
los archivos privados de un store pueden contener datos y no son logs públicos.
