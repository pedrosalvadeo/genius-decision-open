# Regulación según fallos observados: ensayo v1

Este ensayo implementa y evalúa una regla que cambia la espera de recuperación
durante una secuencia de fallos. La regla existe como adaptador local del
laboratorio; no está instalada en el servicio público.

## Regla y memoria disponible

Después de tres fallos operativos consecutivos espera 60 segundos. Si una prueba
de recuperación vuelve a fallar, aumenta la espera según el incremento elegido
en entrenamiento. La fórmula es `min(180, 60 + incremento × max(0, fallos − 3))`.
Los incrementos candidatos son 15, 30 y 60 segundos. El control usa incremento 0,
equivalente a los 60 segundos constantes del regulador activo.

El contador persistido en SQLite es el único dato que recibe la regla: usa el
resultado actual ya observado y los fallos anteriores. No recibe ventanas de
fallo, reloj futuro, duración real de una interrupción ni escenarios de evaluación.
Un éxito reinicia el contador; resultados neutros y errores de dominio no lo
reinician ni lo incrementan. La espera nunca baja de 60 ni supera 180 segundos.
Recargar el adaptador conserva la historia porque la lee de SQLite.

El adaptador ejecuta el `finish` actual con el valor calculado dentro de la misma
transacción. Cambia sólo una instancia privada del módulo, restaura su parámetro
al salir y registra la espera elegida. La identidad identifica regla, incremento
y código del adaptador; no pretende ser la identidad de la política desplegada.
Esto no es una migración de la política persistida del servicio. El manejo de
reinicios reales y la activación requerirían un contrato e integración posteriores.

## Ensayo fijado antes de medir

El plan mantiene las ponderaciones y límites del primer estudio: pérdida de
`100 × fallos + 100 × solicitudes sin terminar + segundos acumulados pendientes`;
mejora total estricta en entrenamiento y evaluación; en cada caso reservado, no
empeorar pérdida, éxitos, fallos o solicitudes sin terminar. La mayor demora de
un éxito puede aumentar como máximo 30 s. No se admiten infracciones de las pausas
por sensores/almacenamiento, espera de recuperación o máximo de cuatro pendientes.
Son criterios sintéticos explícitos, sin calibración con usuarios reales.

`generate_fixtures.py` produjo 16 escenarios de entrenamiento y 16 de evaluación
con semillas distintas. Incluyen cargas bajas y altas, fallos cortos, prolongados,
recurrentes y de régimen cambiante, almacenamiento, sensores y combinaciones.
Sus trayectorias no duplican las del ensayo anterior ni se solapan entre conjuntos.
`predeclaration.json` registra hashes y fecha internos anteriores a la primera
ejecución. Los datos son públicos; no se trata de una evaluación ciega.

Se nomina el mejor incremento **positivo** por pérdida de entrenamiento, con
desempate por menor incremento. El control de cero sigue separado para evitar
una evaluación trivial de la base contra sí misma. Nominar no significa aprobar:
si no supera la base en entrenamiento, ya incumple una condición de promoción.
El candidato se guarda con hash antes de evaluar y no puede reseleccionarse con
los resultados reservados. Se conservan los fallos de evaluación.

El reloj, señales y procesos son simulados; las transiciones del controlador y
SQLite sí se ejecutan. El motor del ensayo es una versión separada del anterior:
las 32 trayectorias con incremento cero reproducen exactamente sus métricas,
modos y hashes. No se alteraron su código, datos ni recibos históricos.
No se simulan cuotas diarias, autenticación, respaldos, CPU ni red. No se accede
a bases privadas ni se envían trabajos a Railway. Las tareas sin terminar al
cerrar el horizonte se cuentan explícitamente, incluida la espera previa a admisión.

## Resultado: propuesta rechazada

| Incremento tras otra prueba fallida | Pérdida de entrenamiento |
| --- | ---: |
| 0 s, control actual | 242210 |
| 15 s | 246560 |
| 30 s, candidato elegido | 241955 |
| 60 s | 255600 |

El incremento de 30 s mejora el entrenamiento en 255 unidades (aproximadamente
0,11%). En evaluación, la pérdida sube de **286155 a 301995**: aproximadamente
5,54% peor. Siete escenarios empeoran y nueve empatan; ninguno mejora su pérdida.
Estado **REJECTED_BY_EVALUATION**. No se modifican los criterios para aceptarlo.

La evaluación detecta por qué contar sólo fallos puede engañar: en algunos casos
hay menos fallos pero una espera mucho mayor. En el caso `eval-02-long-busy`, las
tareas completadas bajan de 45 a 41 y las pendientes suben de 70 a 74. En
`eval-07-mixed-sparse`, los fallos bajan de siete a seis, pero la mayor demora
de un éxito sube de 140 a 310 s. El límite de no empeorar impide la promoción.
Esto refuta la mejora de este candidato bajo estos datos y ponderaciones; no
prueba que toda regla adaptativa sea peor o que 60 s sea universalmente óptimo.

## Verificación y reproducción

Trece pruebas nuevas verifican límites, clasificación de fallos, reinicio tras
éxito, conservación ante resultados neutros, recarga del adaptador, rollback ante
token incorrecto, causalidad del prefijo observado, separación de datos, identidad
de fuentes y reproducción del informe. Con las 29 anteriores suman 42 aprobadas.
Las pruebas de integración siguen ejecutándose en el contenedor de CI sin red.

Desde la raíz del repositorio, con `PYTHONPATH=beta`:

```bash
python -B beta/tools/regulation_history_study.py verify \
  --lock adaptive/evidence/2026-10-15-regulation-history/lock.json \
  --candidate adaptive/evidence/2026-10-15-regulation-history/candidate.json \
  --report adaptive/evidence/2026-10-15-regulation-history/evaluation.json
```

Para una nueva ejecución usar rutas vacías con las fases `freeze`, `train` y
`evaluate`; los recibos existentes no se sobrescriben. Cambiar regla, fuentes,
criterios o datos exige otro estudio versionado y conservar el anterior.

El siguiente trabajo prioritario es cerrar la comprobación pública de misión
cuando el registro lo permita y definir observación en sombra con métricas
operativas reales. Antes de otra búsqueda de reglas hace falta precisar qué
demora, fallos y carga importan en el servicio, con tratamiento explícito de
resultados incompletos y datos privados. Los paquetes sintéticos públicos no
sustituyen esa evidencia ni miden bienestar/PVS. La política pública sigue en 60 s.
