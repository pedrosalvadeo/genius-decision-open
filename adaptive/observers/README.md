# Observaciones reales desde un cliente operador

La [comparación contextual de estrategias](CONTEXT_STRATEGIES.md) añade un segundo
modo local: registrar varias predicciones antes de cada medición y elegir entre
ellas con evidencia anterior del mismo contexto. Ese modo aún no es una operación
REST/MCP; el ciclo con misiones desplegadas descrito abajo mantiene su contrato.

Este adaptador mide el tiempo de respuesta de `GET https://geniusdecision.app/api/health`
y alimenta las misiones públicas existentes. La medición es real cuando se ejecuta
contra esa URL; las pruebas automatizadas usan respuestas y valores simulados.
No requiere cambios de Railway, secretos de infraestructura ni un proveedor LLM.

## Qué mide

El reloj monotónico del cliente mide desde antes de abrir la solicitud hasta
terminar de leer, cerrar y validar localmente su respuesta. Incluye la red y
cualquier proxy configurado en el entorno, conexión, TLS, descarga y validación
local del JSON. No identifica el tiempo de procesamiento del
servidor ni representa la experiencia de todos los usuarios. Pide `no-cache`,
pero no puede demostrar que todos los intermediarios respeten esa cabecera.
Cada solicitud usa el lector HTTP de Python; no se interpreta como un usuario
independiente o un experimento causal sobre el servicio.

El recibo conserva inicio y final UTC, duración en nanosegundos, redondeo hacia
arriba a milisegundos, estado HTTP, tamaño y hash de respuesta, resultado de salud
y hash del contrato de la fuente. La observación enviada a Genius incluye el hash
de ese recibo. La correspondencia se comprueba al leer el checkpoint y al contrastar
la recepción del servidor. Es trazabilidad del observador; no firma de un sensor
independiente ni prueba de que un operador no haya modificado sus propios archivos.

Sólo se admite la URL pública fija; no se envían credenciales en las mediciones.
Se rechazan redirecciones, respuestas de más de 64 KiB, salud no correcta y errores
de reloj o transporte. El timeout de socket es 20 segundos; no es un límite global
de duración del estudio. No se reintenta una
medición: un fallo queda registrado y detiene el estudio, sin sustituirlo por un
valor favorable ni tratar una duración censurada como observación completa.

## Ciclo disponible

```bash
mkdir -p /ruta/privada /ruta/evidencia
PYTHONPATH=adaptive python3.12 -B -m observers.study \
  --state /ruta/privada/estudio.json \
  --out /ruta/evidencia/recibo.json \
  --count 5 --tolerance-ms 1000
```

Requiere Python 3.12 en Linux y biblioteca estándar, acceso HTTPS al servicio y
capacidad disponible en sus cuotas existentes. No instala dependencias nuevas.
Las rutas deben ser distintas y sus carpetas deben existir. El estado privado
contiene una credencial temporal mientras el ensayo está abierto: **no publicarlo**.
Usar una ruta nueva para un estudio nuevo y conservar la misma para reanudarlo.

El plan queda guardado antes de pedir datos:

1. Una medición separada proporciona la estimación base.
2. Cinco mediciones de aprendizaje y tres posteriores de comprobación se envían
   a una calibración. Se conserva la base si la propuesta no pasa sus guardas.
3. La entrega completada congela estimación, base, contexto, tolerancia y cantidad.
4. Se realizan exactamente `--count` nuevas mediciones, entre 3 y 30, después de
   congelar. Cada una se guarda antes de enviarse y se liga a su recibo del servidor.
5. Se comprueban cadena, tiempos, predicciones fijas, errores e informe cerrado.
6. Los registros puntuados se usan como aprendizaje en una misión hija, con otras
   dos mediciones posteriores como comprobación. El informe anterior debe permanecer
   intacto. La predicción hija aún requiere su propia comprobación prospectiva.
7. Se elimina la cuenta dedicada, se verifica la revocación HTTP 401 y se elimina
   el token del checkpoint. El recibo público contiene los pasos y mediciones.

Con la configuración indicada son 16 solicitudes de medición y dos misiones, más
las operaciones API de preparación, lectura y limpieza. La tolerancia 1000 ms es
una elección operacional explícita de este ensayo, no un SLA del producto ni una
medida de bienestar. Se fija antes de medir y no puede modificarse al reanudar.
`PASS` significa recorrido íntegro; el informe puede devolver legítimamente
`NO_CONFIRMED_IMPROVEMENT` y la siguiente calibración puede conservar su base.
No hay selección de la mejor ejecución ni garantía de que aprender mejore el resultado.

La fuente conserva el nombre de procedencia `submitted_observations` que admite
el servicio. No se convierte en `synthetic` ni en `independently_verified` por
conveniencia. Bienestar, PVS y generalización permanecen sin medir. El recurso
modelado es tiempo observado de una petición, no ahorro de agua o CPU.

## Recuperación y límites

La escritura del checkpoint usa reemplazo atómico, fsync, permisos 0600 y un
bloqueo de un solo escritor. El código del observador, plan y configuración de
proxy declarada quedan ligados al estado. Reanudar exige esos mismos valores y
el mismo entorno de observación; no se certifica que la ruta de red no haya cambiado.
Los archivos son de un operador de confianza, no checkpoints de terceros.

Repetir el comando reusa muestras guardadas, claves de idempotencia y observaciones
aceptadas. Un cierre entre reservar una medición y guardar su resultado deja
`MEASUREMENT_OUTCOME_UNKNOWN`: se detiene para revisión, no toma una sustituta.
Si el alta de la cuenta fue aceptada pero se perdió su credencial antes de guardarla,
queda `REGISTRATION_OUTCOME_UNKNOWN` y no se crea otra cuenta automáticamente.
Si la eliminación remota quedó incierta antes de guardar su recibo, un 401 posterior
no basta para declarar borrado comprobado. Son ventanas explícitas de resultado
desconocido; no se promete ejecución exactamente una vez ni limpieza infalible.

Ante un error, el comando conserva estado y recibo parcial y termina con código 2.
La salida omite detalles de transporte que podrían contener información privada.
Las muestras rechazadas y sus fallos quedan disponibles para revisión. Para borrar
la cuenta dedicada de un estudio interrumpido, sin volver a medir:

```bash
PYTHONPATH=adaptive python3.12 -B -m observers.study \
  --state /ruta/privada/estudio.json --out /ruta/evidencia/recibo.json \
  --count 5 --tolerance-ms 1000 --cleanup-only
```

La limpieza no convierte un estudio incompleto en aprobado. El adaptador se ejecuta
bajo demanda; no deja un proceso permanente, un cron ni una campaña de tráfico.
Otros dominios requieren adaptar la fuente, las unidades y el contrato de evidencia,
y cuando corresponda el modelo: no basta con cambiar el nombre de una variable.

## Verificación

Las pruebas de `adaptive/tests/test_http_observer.py` cubren medidas fallidas,
redondeo, integridad, privacidad, concurrencia y recuperación. El ensayo offline
`adaptive/integration/test_http_observer.py` utiliza el servicio y worker reales,
con mediciones sintéticas; pierde una respuesta después de guardar la observación,
reanuda sin duplicarla, aprende desde el informe y borra la cuenta.

La evidencia de ejecución real se guarda por separado en
[`../evidence/2026-10-15-real-http`](../evidence/2026-10-15-real-http).
