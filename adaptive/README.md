# Genius adaptativo — ejecución persistente

Genius puede ejecutar una misión técnica completa, guardar la evidencia y
continuarla en otro proceso. Este incremento construye el soporte de ejecución
del plan adaptativo. La calibración de recursos añade propuestas y revisión de
un parámetro; la generación general de hipótesis y la mejora de código siguen abiertas.

La misión original toma los archivos de un **commit Git explícito**, mide
TAR, gzip y ZIP, construye un modelo de existencias y flujos con esos tamaños,
lo evalúa con el gemelo y núcleo existentes, publica el archivo elegido en una
carpeta local, verifica su contenido y recuerda el resultado. Conserva los bits
ejecutables. No modifica los archivos ni lee contenido sin confirmar en Git.

El criterio declarado es minimizar bytes preservando el contenido. Los tiempos
de CPU son observaciones de una ejecución y no intervienen en la selección.
Este resultado operacional no mide bienestar humano ni sostenimiento de vida.

## Servicio público

La integración está activa en https://geniusdecision.app. La API recibe archivos
UTF-8 explícitos, con permisos por cuenta, y ejecuta el mismo ciclo desde el worker.
Guía: https://geniusdecision.app/static/missions.html. Contrato y garantías:
[ADAPTIVE_MISSIONS.md](../beta/docs/ADAPTIVE_MISSIONS.md).
La prueba de despliegue y reinicio está en [HANDOFF.md](HANDOFF.md).

## Aprendizaje de estimaciones de recursos

La nueva operación `resource_calibration_v1` propone una mediana usando sólo los
registros de aprendizaje enviados, la compara con una estimación base mediante
el núcleo existente y aplica guardas explícitas de error y subestimación. Guarda
la estimación adoptada o conservada en un artefacto privado. Otro ciclo puede
heredar esa memoria por `parent_mission_id` bajo igual contexto y registros nuevos.
Contrato: [RESOURCE_CALIBRATION.md](../beta/docs/RESOURCE_CALIBRATION.md).
Ejemplo sintético: [resource-calibration.json](examples/resource-calibration.json).
La activación de esta versión se registra en `HANDOFF.md`.

Esto añade aprendizaje de un parámetro con una regla fija y evidencia retrospectiva.
No aprende estructuras arbitrarias, no modifica código ni demuestra efectos futuros.
La CLI de archivos mantiene su contrato; la calibración se ofrece por REST/MCP.

## Comprobación con registros posteriores

El servicio incorpora predicciones congeladas y observaciones recibidas después,
con fecha de recepción del servidor, cantidad de datos fijada de antemano, recibos
inmutables e informe cerrado antes de reutilizar sus datos en otro aprendizaje.
Contrato: [PROSPECTIVE_VALIDATION.md](../beta/docs/PROSPECTIVE_VALIDATION.md).
El estado de despliegue se conserva en `HANDOFF.md`; los registros enviados no
se convierten por ello en mediciones independientes ni evidencia de bienestar.

## Ejecutar la CLI

Desde la raíz del repositorio, en Linux x86_64 con Python 3.12 y Git:

```bash
python3.12 -m venv /tmp/genius-adaptive-env
/tmp/genius-adaptive-env/bin/python -m pip install --only-binary=:all: --require-hashes -r adaptive/requirements.lock
export PYTHONPATH="$PWD/adaptive:$PWD/twin:$PWD/kernel"
export PYTHONDONTWRITEBYTECODE=1
/tmp/genius-adaptive-env/bin/python -m genius_adaptive init \
  --source . --commit 170739625c339e6f77c5ff845ec99d0b2ad7bf80 --state /tmp/genius-mission
/tmp/genius-adaptive-env/bin/python -m genius_adaptive run --state /tmp/genius-mission
/tmp/genius-adaptive-env/bin/python -m genius_adaptive inspect --state /tmp/genius-mission
```

`init` exige una carpeta nueva. `run` recupera una misión interrumpida o devuelve
el resultado ya completado, comprobando nuevamente el archivo entregado. Se
rechazan cambios de entradas, objetivo, fuentes del ejecutor, motor, versión de
Python, zlib o dependencias. Una actualización requiere una misión nueva o una
migración explícita, que todavía no está implementada.

Para ejecutar una misión preparada en un contenedor, construir el objetivo
`runtime` de `adaptive/Dockerfile`, montar su carpeta con escritura para UID
65534 y ejecutar `run --state /state`. El contenedor no incluye Git; la captura
inicial se prepara con la CLI del host. La imagen no abre un puerto ni arranca
un servicio de fondo.

## Estado y recuperación

Cada carpeta contiene `mission.json`, la copia de entradas, los tres archivos
candidatos, el archivo entregado, seis recibos JSON revisables, el diario SQLite
y los checkpoints SQLite de LangGraph. Un bloqueo de proceso permite un solo
escritor. Los recibos son inmutables; una clave con contenido distinto se rechaza.
El diario registra la intención antes del efecto y confirma el resultado después.

Al recuperar una intención pendiente, el adaptador debe consultar su destino.
Si encuentra el archivo exacto, lo reconcilia sin escribirlo otra vez. Si no puede
establecer qué ocurrió, conserva `EFFECT_OUTCOME_UNKNOWN` y no reintenta la
acción. Esta política no promete ejecución global «exactamente una vez». Un
futuro conector remoto necesitará idempotencia y conciliación propias.

El diario y los checkpoints cubren la ventana entre el trabajo realizado y su
registro por LangGraph. Las pruebas terminan realmente procesos en esa ventana,
antes y después de la publicación local. También cubren exclusión de escritores,
entradas modificadas, cambio de versión, errores de selección y archivos corruptos.

La CLI limita cada invocación a 120 s de reloj, 90 s de CPU y 512 MiB de espacio
de direcciones; captura hasta 4096 archivos y 16 MiB de contenido. Comprueba un
presupuesto de estado de 256 MiB al comenzar. Es un control de admisión, no una
cuota de disco continua. El contenedor de CI agrega límites externos de memoria,
procesos, CPU y disco temporal. Los llamados Python directos requieren que el
operador proporcione sus propios límites.

## Tecnología y alcance

LangGraph Functional API aporta checkpoints y recuperación sin imponer un
grafo estático de situaciones. SQLite conserva los estados de este prototipo
local de un solo escritor. El diario de Genius conserva además las evidencias
y los efectos; las garantías de efecto no se delegan al caché de tareas.

Los adaptadores actuales verifican distribución y aprendizaje de una estimación.
No constituyen planificación general ni una representación universal. En distribución,
el modelo se instancia con mediciones nuevas; en calibración se propone y contrasta
un parámetro. Ninguno aprende automáticamente una estructura nueva ni mejora el código.

No requiere claves de modelos ni hace inferencia pagada. No incorpora un cliente
LLM. Las dependencias transitivas están fijadas con hashes para la plataforma
probada. La traza remota se desactiva en la imagen y la CLI rechaza su activación.
Las carpetas de la CLI son de operador de confianza; no aceptan checkpoints de
terceros. La integración pública conserva su estado en la base principal y añade
permisos, cuotas, retención y respaldo/restauración. Los respaldos del servicio
incluyen esas misiones; las carpetas independientes de la CLI deben respaldarse
por separado con sus procesos detenidos.

## Verificación

```bash
PYTHONPATH=adaptive:twin:kernel /tmp/genius-adaptive-env/bin/python -m unittest discover -s adaptive/tests -v
docker build --target tests -f adaptive/Dockerfile -t genius-adaptive-test .
docker run --rm --init --network none --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 128 --memory 512m --cpus 1 \
  --read-only --tmpfs /tmp:rw,nosuid,nodev,size=256m genius-adaptive-test
```

Referencias de la decisión técnica, consultadas el 2026-10-14:
[Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api),
[persistencia](https://docs.langchain.com/oss/python/langgraph/persistence).
La documentación presenta SQLite como almacenamiento local de desarrollo;
la integración pública usa una sola réplica y un único worker; no demuestra
escalado con múltiples réplicas.
