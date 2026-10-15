# Laboratorio de adaptación de la regulación

Este incremento permite seleccionar una espera de recuperación a partir de
resultados anteriores y evaluar la selección antes de proponer un cambio.
Se ejecuta localmente o en CI; no instala aprendizaje en el servicio público.
El regulador activo conserva su política de 60 segundos.

## Pregunta, criterios y datos

Pregunta v1: ¿una espera constante de 90, 120 o 180 segundos supera la de 60,
reduciendo fallos sin causar pérdidas excesivas por demora?

`plan.json`, `training.json` y `evaluation.json` quedaron fijados antes de la
primera ejecución; sus hashes y la hora se conservan en `predeclaration.json`.
Es un registro interno, no una preinscripción independiente ni un estudio ciego.
Hay cuatro escenarios de entrenamiento y siete de evaluación pública separados.

La pérdida es `100 × fallos operativos + 100 × solicitudes sin terminar + suma
de segundos pendientes de todas las solicitudes`. Cada solicitud cuenta desde
su llegada hasta éxito, fallo o cierre del horizonte, incluso antes de admisión.
Las ponderaciones son una decisión explícita de este ensayo sintético. No miden
dinero, energía, bienestar ni PVS y no están calibradas con tráfico real.

Se selecciona la menor pérdida total de entrenamiento; los empates conservan la
espera más corta. El candidato se guarda con hash antes de abrir la evaluación.
No se elige entre candidatos con resultados de evaluación. Para ser elegible
debe mejorar estrictamente ambas pérdidas totales y, en **cada** caso reservado,
no aumentar pérdida, fallos o tareas sin terminar, ni reducir éxitos. La mayor
demora de un éxito no puede crecer más de 30 s. Se exige cero infracciones de
pausa por sensores/almacenamiento, espera de recuperación y máximo de cuatro
misiones pendientes. La elegibilidad permite revisión; no promueve producción.

## Qué ejecuta el simulador

Cada simulación carga una instancia privada del módulo actual
`genius_beta/regulation.py` y la migración 011 en SQLite en memoria. Ejecuta sus
operaciones `refresh`, `admits`, `starts`, `begin` y `finish`. Cambia únicamente
`cooldown_seconds` en esa instancia y recalcula la identidad de su política.
El módulo importado por otras pruebas conserva su configuración original.

El reloj, sensores, duración de procesos y solicitudes se simulan. Los procesos
de misión no se ejecutan; no se leen bases privadas ni se usa red, Railway o un
proveedor LLM. No se simulan autenticación, cuotas diarias, respaldos, CPU ni red.
El límite de cuatro pendientes sí se aplica con independencia del regulador.

Cada paso de cinco segundos termina el proceso que corresponda, incorpora las
llegadas, reintenta admisiones pendientes en orden FIFO y puede iniciar una misión.
Después acumula la exposición de todas las solicitudes todavía pendientes. Un
proceso falla si su intervalo de ejecución coincide con una ventana de fallo.
Los fallos son terminales: no hay reintento automático de una misión fallida.
La presión de almacenamiento o sensores impide nuevas admisiones/arranques,
pero no mata lo que ya corre. El cierre del horizonte cuenta explícitamente
toda solicitud sin terminar. Se conserva un hash determinista de cada trayectoria.

## Reproducción

Desde la raíz, con Python y `PYTHONPATH=beta`:

```bash
python -B beta/tools/regulation_study.py verify \
  --lock adaptive/evidence/2026-10-15-regulation-study/lock.json \
  --candidate adaptive/evidence/2026-10-15-regulation-study/candidate.json \
  --report adaptive/evidence/2026-10-15-regulation-study/evaluation.json
```

Para una ejecución separada en un directorio vacío, usar sucesivamente `freeze`
con `--lock`, `train` con `--lock` y `--candidate`, y `evaluate` con esas dos rutas
y `--report`. Los archivos existentes no se sobrescriben. El bloqueo de entradas
incluye código del evaluador/controlador, pruebas, esquema, plan y datasets.
Cualquier alteración invalida la reproducción y exige un nuevo estudio versionado,
conservando el anterior y su commit para poder reproducirlo.

`test_regulation_study.py` contiene oráculos pequeños calculables a mano, casos
de truncamiento, aislamiento del runtime, separación entrenamiento/evaluación,
rechazo de candidatos modificados y reproducción exacta del informe. Corre en
el contenedor de CI sin red y sin credenciales, junto al regulador existente.

## Resultado del primer ensayo

| Espera | Pérdida de entrenamiento — menor es mejor |
| --- | ---: |
| 60 s, actual | 5435 |
| 90 s | 6355 |
| 120 s | 8605 |
| 180 s | 10475 |

La selección retuvo **60 segundos**. En los siete casos reservados su pérdida
fue 15970, idéntica a la base porque es la misma política. Estado
`REJECTED_BY_EVALUATION`: no se justifica un cambio, no se está rechazando el
funcionamiento del regulador actual. Todos los casos pasaron los límites de
comparación, pero no hubo mejora estricta en entrenamiento ni evaluación.

La espera de 90 s produjo dos fallos menos en el escenario recurrente, mientras
que en la interrupción larga mantuvo los mismos fallos y elevó la demora. Esto
motiva investigar reglas dependientes de historia observada, sin concluir aún
que una regla contextual sea superior. Ese nuevo ensayo debe fijar primero sus
señales disponibles, objetivo y casos separados, sin reutilizar estos casos como
evaluación inédita ni modificar retrospectivamente sus resultados.

Evidencia: [2026-10-15-regulation-study](../../../adaptive/evidence/2026-10-15-regulation-study).
El registro operacional privado sigue separado de los paquetes sintéticos públicos.
