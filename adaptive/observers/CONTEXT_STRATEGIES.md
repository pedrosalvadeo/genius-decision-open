# Predicciones y selección según contexto previo

`context_study.py` ejecuta un ensayo acotado desde el observador. Añade elección
entre estrategias, además de ajuste de valores. **Es un módulo del operador,
no una nueva misión disponible por REST/MCP**. Sólo hace GET de salud al servicio;
no requiere cuenta, secretos, cuotas de misiones, otro despliegue ni tráfico
permanente. La API sigue ofreciendo calibración y predicciones constantes.

## Contrato fijado antes de observar

`PAST_ONLY_CONTEXT_SELECTOR_V1` conserva una base entera congelada con referencia
de procedencia. Su contexto es `unknown` antes de la primera medición y luego
indica si **el valor anterior** estuvo por encima de la base. No utiliza la
duración, estado HTTP, cuerpo ni otro dato del objetivo que todavía va a medir.
Es un contexto temporal mínimo, no una representación completa de la red.

Se calculan cuatro predicciones antes de cada petición:

| Estrategia | Datos permitidos |
| --- | --- |
| `baseline` | Base congelada en el plan |
| `rolling_median` | Mediana inferior de hasta tres valores anteriores |
| `last_value` | Último valor observado; base si no existe |
| `context_median` | Mediana inferior de hasta tres valores anteriores cuyos contextos coincidan con el actual; con menos de dos, mediana reciente |

Las mediciones iniciales (`warmup_count`) alimentan esos predictores pero no
aportan puntuaciones para seleccionar estrategias. Después, cada predicción se
puntúa una sola vez frente al mismo objetivo recibido más tarde. Antes de una
nueva predicción se examinan sólo las puntuaciones ya completadas **del mismo
contexto**, sin ventana sobre esas puntuaciones dentro del ensayo acotado.

Con menos de tres puntuaciones previas de ese contexto se elige la base. Con tres
o más, una alternativa es elegible sólo si reduce el error absoluto acumulado,
no aumenta la máxima subestimación y ésta está dentro de la tolerancia del plan.
Entre elegibles gana el menor error; los empates siguen el orden fijo mediana
reciente, último valor, mediana contextual. Un empate con la base conserva la
base. El selector puede volver a ella si nuevas observaciones invalidan las
guardas. Estas guardas sobre el pasado no garantizan el resultado siguiente.

## Evaluación del comportamiento efectivamente ejecutado

El informe compara las cuatro estrategias y la secuencia `adaptive` que el
selector realmente eligió **antes de cada objetivo**. Sólo esta secuencia se
contrasta con la base para el resultado principal. No se presenta al ganador
elegido retrospectivamente entre alternativas como un despliegue exitoso.
Todos usan las mismas observaciones puntuadas; se excluye el calentamiento.

La suma de errores se contrasta con el núcleo nativo mediante el modelo finito
de margen de error. Su selección única o empate debe coincidir con la aritmética.
La elección histórica y las guardas adicionales están fuera de ese modelo.
`OBSERVED_GUARDED_IMPROVEMENT` exige menor error acumulado, máxima subestimación
no peor y dentro de la tolerancia. Es una mejora observada en esa secuencia,
no significación estadística, garantía futura, ahorro de latencia ni efecto causal.
El resto devuelve `NO_CONFIRMED_IMPROVEMENT`. Se informa también si la propia base
incumple la tolerancia; mantenerla no la certifica.

## Persistencia y recuperación

Antes de medir se publica un recibo inmutable `PREDICT` con contexto, predicciones,
elección y evidencia usada. Cada intento termina en `OBSERVE` si su respuesta se
pudo guardar, incluyendo muestras rechazadas. Los archivos usan creación atómica
sin sobrescritura y fsync; un bloqueo permite un solo escritor. Los eventos ligan
hash, orden y fecha UTC. El plan liga contrato HTTP, Python, código de selección,
colector, persistencia y núcleo. Cambiar cualquiera impide reanudar la medición.

Al reabrir se recalculan las predicciones desde cada prefijo y se verifican
normalización, inicio posterior a la predicción, cadena, orden y reporte. Un
resultado ya guardado no se vuelve a medir. Una intención sin resultado queda
`MEASUREMENT_OUTCOME_UNKNOWN`: requiere revisión y no se sustituye. Una muestra
fallida también detiene el ensayo sin reemplazo. Si se interrumpe después de la
última observación, se puede cerrar el informe usando lo ya guardado.

Estos recibos y relojes pertenecen al operador; no tienen sello temporal ni
atestación externa. Los hashes detectan inconsistencias, no a un operador que
reescriba deliberadamente todo su historial. No cargar estado de terceros.
El origen y las limitaciones de la medición HTTP son los del [observador](README.md).
Bienestar, PVS, generalización y causas de cambios de latencia siguen sin medir.

## Ejecutar

Con las dependencias existentes del proyecto, Python 3.12 y desde su raíz:

```bash
PYTHONPATH=adaptive:twin:kernel python3.12 -B -m observers.context_study \
  --plan adaptive/evidence/2026-10-15-context-http/plan.json \
  --state /ruta/nueva/estudio-contextual
```

El plan de referencia declara seis mediciones iniciales y doce puntuadas, base
7835 ms heredada del ensayo anterior y tolerancia 1000 ms. Son elecciones para
una exploración operacional pequeña, no un SLA. El resultado previo negativo se
conserva. Este ensayo nuevo cambia la hipótesis a selección temporal contextual;
no repite el protocolo constante para buscar una aprobación.

Antes de usar el comando para un estudio nuevo, declarar su objetivo y plan.
Para reanudar, conservar el plan y directorio originales. El informe completo
queda en `--state/evidence.json`; los eventos parciales en `--state/events` se
conservan incluso si el comando termina con código 2. No hay credencial que borrar.
La ejecución no modifica el servicio ni el estimador desplegado.

Pruebas: `adaptive/tests/test_context_strategies.py`. Incluyen selección contextual
con datos sintéticos, reversión desfavorable, exclusión de datos futuros,
mediciones fallidas, resultado incierto, reinicio tras guardar observación,
integridad, concurrencia y acuerdo con el núcleo nativo.
