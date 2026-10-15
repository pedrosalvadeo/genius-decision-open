# Regulación operativa de misiones v1

Este controlador conecta observación, acción y memoria en las misiones en cola.
Es una política explícita de realimentación, no aprendizaje de sus propios umbrales.
Su objetivo operacional es evitar que entren nuevas misiones mientras se acumula
trabajo, falta almacenamiento o se repiten fallos de ejecución. No mide bienestar
ni PVS y no demuestra todavía una mejora de disponibilidad en tráfico real.

## Alcance y activación

`GENIUS_MISSION_REGULATION_ENABLED=true` habilita el controlador si también está
activo `GENIUS_ADAPTIVE_ENABLED=true`. Por defecto permanece desactivado. El worker
existente realiza las observaciones; no requiere otro servicio, cron, proveedor,
credencial ni aumento de recursos. La activación efectiva se registra en el handoff.

Controla únicamente admisión y arranque de `source_distribution_v1` y
`resource_calibration_v1` en `adaptive_missions`. Los expedientes tradicionales,
evaluaciones síncronas del gemelo y cierres de pronósticos contextuales conservan
sus controles existentes; no se presentan como regulados por este componente.
La actividad diplomática y la generación de código son procesos separados.

## Señales y decisiones

El worker observa cada cinco segundos cuando recibe turnos de ejecución, también
durante una misión. Una admisión o arranque exige una observación nueva dentro de
su transacción. No hace una llamada de red para observar. Las señales son número
de misiones en cola/ejecución, bytes de las bases y sus archivos auxiliares en el
volumen, y espacio libre del sistema de archivos. No mide CPU, dinero, energía
física, calidad semántica del resultado ni tiempo de respuesta de terceros.

| Modo | Entrada y salida | Acción |
| --- | --- | --- |
| NORMAL | Condiciones dentro de límites | Admite y ejecuta con las cuotas previas. |
| DRAINING | Entra con 4 misiones pendientes; sale al quedar 1 o menos | Pausa admisiones y sigue consumiendo la cola aceptada. |
| RESOURCE_PAUSED | Entra al usar al menos 85% del límite de bases, o quedar menos del mínimo libre + 8 MiB. Sale con uso no mayor a 70% y libre al menos mínimo + 16 MiB | Pausa admisiones y nuevos arranques. No borra datos ni adquiere capacidad. |
| COOLDOWN | Tres fallos operativos consecutivos; espera 60 s desde el fallo que activa la pausa | Conserva cola y memoria; no arranca ni admite misiones nuevas. |
| PROBING | Terminó la espera, pero aún no hay éxito observado | Permite una ejecución de la cola; si está vacía admite una sola misión. Un éxito reinicia el contador. Otro fallo operativo vuelve a esperar. |
| SENSOR_PAUSED | Observación no disponible o reloj anterior a la última observación | Pausa hasta poder observar de nuevo coherentemente. |
| REVIEW_REQUIRED | La identidad de la política persistida difiere | No reinicia silenciosamente el historial; exige revisión del operador. |

Los márgenes de entrada/salida evitan alternar continuamente por fluctuaciones
pequeñas. El orden de prioridad es almacenamiento, espera por fallos, prueba de
recuperación y acumulación de trabajo. Una pausa no mata una misión ya iniciada:
siguen vigentes sus controles de capacidad, cancelación, 60 s y memoria acotada.

Se cuentan `MISSION_TIMEOUT`, `MISSION_PROCESS_FAILED`, `MISSION_PROTOCOL_FAILED`
y `STORAGE_CAPACITY`. Rechazos del dominio, revisión del estado, cancelaciones y
el código genérico `MISSION_EXECUTION_FAILED` no se atribuyen a fallos del host.
Esta clasificación acotada puede omitir fallos internos no distinguibles todavía.
Esos resultados neutros tampoco demuestran recuperación ni borran fallos previos.

Un arranque y su marcador de control se confirman con el cambio a `running` en la
misma transacción. El resultado y la liberación del marcador se guardan juntos.
Al reiniciar el worker, un marcador pendiente queda como resultado desconocido y
exige espera/prueba; no se cuenta como éxito. Se conservan checkpoints y límite de
tres intentos por misión. No se inventa trabajo para superar la pausa ni se relanza
una misión fallida sin el reintento explícito que exige el contrato existente.

## Interfaz y memoria

`GET /api/missions/regulation`, permiso `missions:read`, y MCP
`mission_regulation` exponen protocolo, habilitación, modo, fecha de observación,
alcance y hash de política. `/api/health` incorpora el mismo estado resumido.
Una observación mayor a 15 s aparece como `OBSERVATION_STALE`; no certifica un
estado fresco. Un `NORMAL` del controlador no elimina otras restricciones como
suspensión del operador, salud del respaldo, scopes, capacidad o cuotas.

Una admisión pausada devuelve HTTP 503, código `mission_regulated` y
`Retry-After: 5`. Ese tiempo indica cuándo volver a consultar; no promete que la
pausa haya terminado. No consume cuota de ejecución ni cambia el borrador a cola.
Repetir una misión ya en cola, en ejecución o completada recupera su estado antes
del control de admisión. Lectura, exportación, cancelación y borrado conservan sus
permisos y controles previos. El cliente no tiene una operación para subir límites,
reiniciar fallos o desactivar la política.

Migración aditiva 011: estado único y diario de hasta 512 eventos, con retención
de siete días. Registra transiciones, señales anteriores/actuales y resultados
operativos agregados; no contiene entradas, resultados de usuarios, IDs de cuenta
o misión, credenciales ni mensajes de terceros. El estado mantiene sólo la última
observación y un marcador aleatorio de la ejecución activa. El diario permite
constatar, por ejemplo, que la cola bajó; no atribuye causalidad por ese hecho.

La memoria permanece en la base privada y sus respaldos cifrados, no se sube a
GitHub. Los recibos de pruebas públicos usan situaciones sintéticas declaradas.
La restauración admite los prefijos históricos exactos hasta 011 y conserva la
suspensión del operador; nunca relaja hashes de migraciones anteriores.
Inspección local del operador: `PYTHONPATH=beta python -m genius_beta.regulation`.
Esa orden sólo lee; su salida no debe confundirse con el estado público resumido.

## Validación y continuación

`beta/tests/test_regulation.py` prueba umbrales/márgenes, falta de sensores, reloj,
memoria acotada, espera y una sola prueba, rechazo sin cuota, permisos/MCP,
admisiones concurrentes, fallos inyectados y un proceso realmente terminado con
SIGKILL que luego reanuda sus checkpoints y completa una misión. Se verifica la
compatibilidad con misiones, pronósticos, club y recuperación cifrada existentes.

Esto es regulación con reglas fijas y registro de efectos observados. El
[laboratorio de políticas](../experiments/regulation/README.md) ya compara otras
esperas de recuperación contra un objetivo y ensayo fijados antes de medir.
El primer ensayo retuvo los 60 s actuales: ninguna alternativa mejoró su objetivo
de entrenamiento. No instala aprendizaje ni cambios de política en producción.
No se permite que el controlador cambie sus umbrales a partir de
una única ejecución, se financie, amplíe cuotas, modifique permisos o promueva código.
