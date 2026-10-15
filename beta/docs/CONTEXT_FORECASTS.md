# resource_context_forecast_v1

Contrato aditivo de predicción secuencial según contexto previo. No cambia
`resource_forecast_v1`, su evaluador congelado ni los recibos del observador v1.
El estado de despliegue efectivo se registra en `adaptive/HANDOFF.md`.

## Plan y procedencia

Cada misión propia `resource_calibration_v1` completada puede tener un plan
contextual. `POST /api/missions/ID/context-forecast` recibe exactamente
`artifact_sha256`, `warmup_count` (entero 3..10), `scored_count` (entero 6..30).
Hereda **la estimación aceptada como base**, unidad, recurso, contexto descriptivo,
tipo de datos y tolerancia. Congela esos valores, los recuentos, regla y hash de
las fuentes del ejecutor/núcleo. No hereda como base la antigua propuesta rechazada.
Repetir el mismo plan devuelve el existente; cambiarlo requiere una misión nueva.

La regla `PAST_ONLY_CONTEXT_SELECTOR_V1` reproduce la del observador publicado en
PR 35. La implementación de servicio está en `genius_adaptive/contextual.py` y
una prueba compara cada prefijo con aquella implementación, que sigue intacta
para reabrir su evidencia histórica. Contexto: el valor anterior mayor que la
base congelada o menor/igual; primera predicción `unknown`. Estrategias: base,
mediana inferior de hasta tres valores recientes, último valor, mediana inferior
de hasta tres objetivos anteriores con igual contexto (al menos dos; si no,
usa mediana reciente). Los valores iniciales alimentan predictores, no selección.

Después del calentamiento, sólo puntuaciones **ya recibidas del mismo contexto**
pueden cambiar la elección. Se exigen al menos tres, menor error absoluto total,
máxima subestimación no peor que la base y dentro del límite congelado. Se elige
la elegible con menor error; empate entre elegibles: mediana reciente, último
valor, mediana contextual. Sin elegibles se conserva la base. El objetivo actual
puede conservar una base excesiva: esto no certifica precisión ni seguridad futura.

## Protocolo

| Operación | JSON exacto | Permiso |
| --- | --- | --- |
| `GET /api/missions/ID/context-forecast` | Sin cuerpo | `missions:read` |
| `POST .../context-forecast` | `{artifact_sha256,warmup_count,scored_count}` | `missions:write` |
| `POST .../context-forecast/predictions` | `{forecast_sha256,prediction_id}` | `missions:write` |
| `POST .../context-forecast/observations` | `{forecast_sha256,prediction_sha256,observation}` | `missions:write` |
| `POST .../context-forecast/close` | `{forecast_sha256}` | `missions:run` |

`prediction_id` admite 1..64 letras ASCII, números, `_` o `-`.
`observation` es `{id,value,observed_at,source}`: mismo ID de predicción,
valor entero 0..1000000, fecha ISO con zona y fuente no vacía de hasta 240 caracteres.
Sólo se acepta si su fecha declarada es estrictamente posterior a la emisión
del servidor y no posterior a la recepción. No se admiten objetivos sin predicción.

El servidor persiste contexto, todas las predicciones, estrategia elegida,
evidencia anterior usada, hash y fecha antes de responder. El cliente debe
**recibir la predicción antes de medir el objetivo**. Nunca enviar objetivos ya
conocidos fingiendo un nuevo tiempo de evento. El servidor comprueba su propio
orden de emisión/recepción, no puede atestiguar por sí solo cuándo sucedió el
evento externo ni que el remitente no omita, copie o seleccione datos.

Sólo puede haber una predicción pendiente. Su recibo se encadena al último
objetivo (o al plan), y el objetivo a su predicción. Predicción y observación son
inmutables; repetir mismo ID/contenido recupera el recibo. Un ID reutilizado con
contenido distinto se rechaza. No hay operación para saltar o reemplazar un
objetivo fallido: conservar/exportar el estudio incompleto o borrarlo. Reintentar
una entrega de datos conserva el mismo dato e ID; no tomar una medición sustituta.

Estados: `ready_to_predict`, `awaiting_observation`, `ready_to_close`, `complete`.
El total fijado es calentamiento más registros puntuados. Una vez completo no
se pueden añadir registros. `close` requiere todos ellos y produce el informe
inmutable. No reajusta decisiones pasadas ni el artefacto padre.

## Núcleo, recursos y recuperación

El informe compara todas las estrategias y la política `adaptive` efectivamente
ejecutada. Sólo esta última determina `OBSERVED_GUARDED_IMPROVEMENT` frente a la
base bajo las tres guardas; en otro caso, `NO_CONFIRMED_IMPROVEMENT`. Las
alternativas son comparación descriptiva, no elección retrospectiva presentada
como éxito. El modelo nativo compara el mismo error absoluto en unidades
declaradas; no representa un recurso físico, bienestar ni PVS.

`close` ejecuta el modelo finito en `ProcessEvaluator`: máximo 20 segundos,
384 MiB y 2 MiB de salida, sin credenciales en el entorno. Comparte el bloqueo de
compilador con gemelos y misiones, y las cuotas diarias de ejecución de misiones
y agentes. La base de datos no queda bloqueada durante el cálculo. El reporte
incluye el resultado nativo completo y su verificación; la selección matemática
de error mínimo debe coincidir con la aritmética directa (incluidos empates).

Un fallo o límite de ejecución conserva los recibos y permite otro `close`
explícito dentro de cuotas. Un intento de cálculo fallido consume cuota. Una
respuesta perdida tras guardar el informe se recupera sin recalcular ni consumir
otra cuota. La revisión final de propiedad impide recrear una misión borrada
durante el cálculo. No hay tarea contextual permanente en segundo plano.

Migración aditiva 010 en la base principal: plan, predicciones y observaciones;
transacciones serializadas, unicidad y triggers de inmutabilidad. Los respaldos
cifrados y exportaciones incluyen los nuevos datos. La restauración admite
prefijos históricos exactos y revisados hasta 010; nunca relaja hashes antiguos.
Retención, borrado de misión/cuenta y registro remoto de borrados aplican por
cascada. Leer, exportar y borrar siguen disponibles con ejecución desactivada.

Cambiar el código/núcleo congelado impide nuevas predicciones, observaciones y
cierres hasta revisión; se conservan lectura, exportación, borrado y recuperación
idempotente de recibos ya guardados. El añadido de un módulo al runtime también
hace que misiones antiguas **incompletas** requieran revisión si su identidad no
coincide al reanudarlas. Las misiones completadas conservan sus entregas.

MCP: `mission_context_get`, `mission_context_freeze`, `mission_context_predict`,
`mission_context_observe`, `mission_context_close`. OpenAPI:
`/static/context-forecast-openapi.json`. Exportación propia por
`GET /api/missions/ID/export`; la exportación global mantiene sus permisos previos.
El protocolo contextual aún no crea automáticamente misiones hijas desde su
informe; la ruta antigua de aprendizaje desde `resource_forecast_v1` se conserva.

Pruebas de integración: `beta/tests/test_context_forecasts.py`, incluyendo
aislamiento, secuencia, reinicio, concurrencia, límites, fallo nativo, borrado
durante cálculo y restauración con protección contra resurrección de datos.
Estos ensayos sintéticos comprueban el mecanismo; no demuestran mejora empírica
general, sensores verificados, bienestar ni sostenimiento de la vida.
