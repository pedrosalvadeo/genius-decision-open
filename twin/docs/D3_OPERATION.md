# D3 — Arranque y operación

El objetivo vigente es poner Genius en funcionamiento como producto. La validación con casos reales se pospone por decisión del usuario y no es un requisito para desarrollar, probar o montar sus capacidades. Esta entrega acredita operación local y un montaje autenticado probado localmente; no acredita una nueva publicación en la nube.

## Ejecutar el constructor local

Desde la raíz del repositorio completo, con Python 3.12 y las dependencias de `beta/requirements.lock` instaladas:

```bash
export PYTHONPATH="$PWD/twin:$PWD/kernel:$PWD/beta:$PWD/product_local:$PWD/consumer_views"
python -m genius_twin --database ./var/twin.sqlite3 --port 8765
```

Abrir `http://127.0.0.1:8765`. El lanzador escucha sólo en loopback, mantiene un lock exclusivo sobre esa base, recupera trabajos interrumpidos y serializa las solicitudes. Un segundo lanzador sobre la misma base es rechazado. La app local no es un servicio multiusuario; para ello usar el montaje beta.

El relato inicia un borrador. Completar el formulario, revisar el modelo y confirmar sus premisas antes de evaluar. Los ejemplos de cuidado y distribución de tiempo son hipotéticos. También se conserva el semillero D1. Guardar un borrador no lo convierte en modelo admitido. Editar, comparar y restaurar preserva las versiones anteriores; restaurar agrega una versión.

## Montaje con cuentas

La imagen beta ahora incluye `twin/genius_twin`, los ejemplos y `kernel/genius_kernel`. La nueva capacidad se habilita explícitamente con `GENIUS_TWIN_ENABLED=1`; el valor predeterminado es desactivado. Con ella habilitada, el espacio de la cuenta enlaza `/twin/` y sus operaciones usan `/api/twin`. No se cambiaron variables, servicios ni despliegues remotos como parte de D3.

Se reutilizan las cuentas beta, su cookie HttpOnly/CSRF, las claves Bearer revocables y la suspensión del servicio. GET `/api/twin/runtime` entrega el CSRF de la sesión; un agente Bearer recibe null. No se acepta un selector de usuario en los cuerpos. La base de cada cuenta se ubica en `DATA_DIR/twins/<id>.sqlite3`; sus locks de lifecycle y el lock global del compilador viven en `DATA_DIR/twin-locks`.

La configuración de producción previa sigue siendo necesaria: origen HTTPS, volumen `/data`, proceso sin privilegios y datos del responsable. Esta entrega no afirma que esa configuración haya sido revisada o activada nuevamente. `beta/deploy/start.py` conserva el bootstrap y supervisión anteriores; al habilitar twin amplía la ventana de salida a 105 s y los tiempos de Gunicorn a 120/100 s, para la evaluación de hasta 90 s.

### Límites de ejecución y almacenamiento

| Límite beta | Valor predeterminado |
|---|---:|
| Compiladores del gemelo simultáneos | 1 |
| Tiempo por evaluación | 90 s |
| Memoria virtual del hijo | 384 MiB |
| Salida del hijo | 16 MiB |
| Modelo JSON | 256 KiB |
| Espacio compartido de base principal y gemelos | 128 MiB |
| Expedientes / versiones por expediente | 20 / 20 |
| Propuestas por expediente | 100 |
| Evaluaciones solicitadas por cuenta / global al día | 20 / 200 |

La admisión de escritura reserva margen para SQLite/WAL y el mínimo de disco libre heredado. Las solicitudes son síncronas: cuando otro compilador ocupa el servicio se devuelve 429, sin crear una cola oculta. Una operación simultánea sobre la misma cuenta devuelve 409. Agotar tiempo/memoria/salida o interrumpir un proceso es un fallo operativo sin conclusión matemática. El hijo recibe sólo el modelo y un entorno mínimo, y en Linux muere si termina su padre. No ejecuta código, URLs ni instrucciones contenidos en el modelo.

Un resultado se reutiliza sólo con la misma versión e identidad de modelo, compilador, núcleo y ejecutor. Los recibos históricos quedan congelados. Una evaluación puede terminar correctamente con probabilidades o integración fuera de dominio: la UI conserva los resultados parciales y no inventa una selección.

## Exportación, borrado y retención

La exportación de cuenta incluye los expedientes de gemelo. El borrado de expediente exige la versión actual, registra el tombstone después de validar la solicitud y antes de borrar. El borrado de cuenta adquiere el mismo lock y elimina sus bases y archivos WAL/SHM. Si la cuenta está ocupada se pide reintentar; no se cancela silenciosamente un cálculo ni se permite recrear datos de una cuenta eliminada.

`python -m genius_beta.maintenance` incluye el barrido de gemelos: elimina cuentas huérfanas y expedientes sin actividad durante el plazo configurado. Exportación, borrado de cuenta y mantenimiento siguen incluyendo los gemelos aunque posteriormente se deshabilite su interfaz.

### Copias y restauración offline

```bash
python beta/deploy/backup.py backup /data/genius/genius.sqlite3 /backups/genius-YYYYMMDD.sqlite3
```

Se producen la base principal, su `.manifest.json` y, cuando existe almacenamiento de gemelos, una carpeta compañera `.sqlite3.twins/`. **Conservar y transportar las tres piezas juntas.** El manifiesto contiene el hash de cada base. Se usa la API de backup de SQLite; no se copian archivos WAL activos. Cada expediente de cuenta se captura bajo su lock. Las cuentas se capturan en momentos distintos: esto no es una transacción global simultánea entre usuarios.

Para recuperar, detener web y worker, conservar una copia legible del estado actual de privacidad y producir un destino offline nuevo:

```bash
python beta/deploy/backup.py restore /backups/genius-YYYYMMDD.sqlite3 /recovery/restored.sqlite3 --current-db /data/genius/genius.sqlite3 --services-stopped
```

Se comprueban hashes, integridad, migraciones y antigüedad máxima de siete días. La restauración aplica borrados vigentes e interseca usuarios y expedientes actualmente existentes; no revive cuentas/casos eliminados. Descarta sesiones/claves/consentimientos de investigación heredados y deja los trabajos activos interrumpidos, sujetos a reintento explícito. Las entradas twin de la restauración están en `/recovery/restored.sqlite3.twins`.

Inspeccionar ese resultado offline antes de promoverlo. Con servicios todavía detenidos, instalar la base restaurada como `DATA_DIR/genius.sqlite3` y su carpeta compañera como `DATA_DIR/twins`, conservando propietario UID 10001 y permisos privados. No fusionar con archivos WAL/SHM del estado anterior. Si cualquier verificación falla, mantener el resultado offline. Este procedimiento y sus invariantes se probaron localmente; no se ejecutó una recuperación sobre una cuenta o volumen real.

## Frontera del incremento

El perfil configurable representa existencias, flujos, acciones y políticas finitas. No es un simulador universal ni interpreta automáticamente toda la causalidad del relato. La UI permite configurar las premisas y el motor calcula sus consecuencias.

Las observaciones del mundo y el cierre de revisión para STOCKFLOW todavía no están implementados. D1 conserva su contraste y suspensión por discrepancia. El criterio funcional nativo del nuevo perfil permanece neutral, explícitamente sin una función sustantiva inventada; bienestar, CAG y tarea sí tienen mapeos calculados. No hay MCP nuevo, acción física, calibración empírica ni recibo RC01. Estos límites no impiden operar las capacidades recibidas.

## Integración D4 para publicación

D4 integra D3 con la versión pública `7d1debb`, conservando registro, privacidad, decisiones cotidianas, agentes y MCP. El respaldo R2 cifra un único paquete que incluye las bases de gemelo y sus hashes. El presupuesto de 128 MiB cubre el conjunto; no se amplían límites de infraestructura. El borrado de un gemelo registra primero una intención remota cifrada y luego el tombstone local. Si no se confirma, devuelve 503 y permite reintentar. El worker incorpora el barrido horario de gemelos.

La recuperación R2 tras pérdida total usa las intenciones remotas vigentes para filtrar los expedientes del snapshot; conserva el destino suspendido, elimina credenciales y aplica retención. El procedimiento local que exige la base actual sigue disponible. La cadencia remota conserva el intervalo diario: esta publicación no fuerza un respaldo adicional fuera de su presupuesto. Las claves personales Bearer pueden acceder a `/api/twin`; las claves autónomas de agentes y MCP conservan sus ámbitos anteriores y no exponen todavía herramientas del gemelo.
