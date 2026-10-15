# Ensayo HTTP con estrategias y selección contextual

Código y plan publicados antes de medir en
`20503abac466166d8938a1ac36e71f4a0c50144b`, PR 35, creado a las
`2026-10-15T04:28:20Z`. El diario empieza a las `04:28:36.360964+00:00`
y termina a las `04:30:14.524613+00:00`. Fechas locales del observador;
no sello temporal independiente para cada predicción.

Se hicieron las 18 mediciones previstas: seis iniciales y doce puntuadas, todas
con salud correcta y sin reemplazos. No se creó ninguna cuenta o credencial.
La fuente fue el GET público de salud existente; el selector se ejecutó en el
operador, no en el servidor. No cambiaron archivos del runtime ni configuración
de Railway. Este resultado no verifica una nueva ruta REST/MCP.

## Datos y resultado

Base heredada del ciclo anterior: 7835 ms. Tolerancia: 1000 ms. Ambos valores
quedaron fijos antes de medir. Observaciones iniciales:
5490, 5386, 6091, 5473, 5487, 5344 ms.

Observaciones puntuadas: 5356, 5367, 5425, 6127, 5452, 5341, 4392, 5418,
5477, 5439, 5389, 5521 ms.

| Predicciones | Error absoluto total (ms) | Máxima subestimación (ms) |
| --- | ---: | ---: |
| Base fija | 29316 | 0 |
| Mediana reciente | 2521 | 760 |
| Último valor | 3823 | 1026 |
| Mediana contextual | 2521 | 760 |
| Elección adaptativa ejecutada | 29316 | 0 |

El selector eligió `baseline` doce veces; su resultado es
`NO_CONFIRMED_IMPROVEMENT`. Una alternativa necesita al menos tres puntuaciones
anteriores del mismo contexto y pasar todas las guardas, incluida no empeorar la
máxima subestimación. Ninguna elección pudo reemplazar la base bajo esa regla.
El menor error de las medianas es un resultado descriptivo de predicciones
guardadas antes del objetivo; no una mejora de la política efectivamente aplicada.

Las doce observaciones puntuadas tuvieron contexto
`previous_at_or_below_baseline`; no se evalúa aquí discriminación entre contextos.
La mediana contextual y la reciente coinciden en esta secuencia. La ausencia de
subestimación de la base refleja sobreestimación persistente, no precisión.
Una revisión del criterio exigiría versionar el contrato antes de medir otros
datos. No se ajustó el criterio ni se repitió el estudio para obtener aprobación.

## Archivos y comprobaciones

- `plan.json`: plan anterior al ensayo, sin cambios posteriores.
- `live-study.json`: 38 eventos (plan, 18 pares predicción/observación, informe),
  hashes, fechas, fuentes, decisiones previas y verificación del núcleo nativo.
- `summary.json`: resultados compactos, identidades y límites.
- `adaptive-tests.txt`: 45 pruebas locales aprobadas, incluidas 12 nuevas.

Reabrir el estudio completo con una función que falla ante cualquier intento de
medición devolvió el mismo informe y bytes idénticos sin solicitudes nuevas.
Se verificaron cadena, normalización, tiempos, predicciones recalculadas usando
sólo prefijos, puntuación y acuerdo del núcleo. CI inicial aprobado:
adaptativo 38681634388, servicio 38681634395, cápsula 38681634383.
El PR registra el CI del commit final de evidencia.

Los hashes hacen auditable la consistencia; no atestiguan un sensor independiente
ni impiden reescritura deliberada de todo el historial por el operador. La latencia
incluye red/proxy, conexión, lectura y validación local. No mide directamente el
procesamiento del servidor ni demuestra efectos causales, generalización,
bienestar o PVS. El resultado anterior negativo permanece en `2026-10-15-real-http`.
