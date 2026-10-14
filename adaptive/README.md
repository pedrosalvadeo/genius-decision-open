# Genius adaptativo — primer ciclo persistente

Genius puede ejecutar una misión técnica completa, guardar la evidencia y
continuarla en otro proceso. Este incremento construye el soporte de ejecución
del plan adaptativo; la revisión de modelos, la generación de hipótesis y la
mejora autónoma de código siguen abiertas.

La misión implementada toma los archivos de un **commit Git explícito**, mide
TAR, gzip y ZIP, construye un modelo de existencias y flujos con esos tamaños,
lo evalúa con el gemelo y núcleo existentes, publica el archivo elegido en una
carpeta local, verifica su contenido y recuerda el resultado. Conserva los bits
ejecutables. No modifica los archivos ni lee contenido sin confirmar en Git.

El criterio declarado es minimizar bytes preservando el contenido. Los tiempos
de CPU son observaciones de una ejecución y no intervienen en la selección.
Este resultado operacional no mide bienestar humano ni sostenimiento de vida.

## Ejecutar

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

La secuencia actual verifica la infraestructura con un adaptador concreto. No
constituye todavía planificación general ni una representación universal. El
modelo se instancia con mediciones nuevas; almacenar una observación no equivale
a aprender automáticamente su estructura o a mejorar el propio programa.

No requiere claves de modelos ni hace inferencia pagada. No incorpora un cliente
LLM. Las dependencias transitivas están fijadas con hashes para la plataforma
probada. La traza remota se desactiva en la imagen y la CLI rechaza su activación.
El estado es de operador de confianza; no acepta carpetas ni checkpoints de
terceros ni se expone a usuarios del servicio público.

La adopción en Railway requiere decidir cómo integrar permisos por usuario,
cuotas persistentes, migraciones, retención y respaldo/restauración. Los backups
actuales del servicio **no incluyen estas bases**. Hasta completar esa integración,
conservar una copia de la carpeta completa con el proceso detenido; el repositorio
guarda fuentes y evidencia pública, no el estado privado de futuras misiones.

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
no se da por resuelto el despliegue multiusuario o de múltiples réplicas.
