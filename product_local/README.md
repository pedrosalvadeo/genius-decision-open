# Genius: capa local R2

Primera capa local de expedientes, información y suficiencia certificada. Requiere Python 3.12 y biblioteca estándar, en POSIX/Linux. No necesita instalación de paquetes ni conexión de red. El Kernel y los contratos R1 son dependencias recibidas externas: esta carpeta no los reemplaza.

Ejecutar desde esta carpeta (`product_local/` en el repositorio). Fijar las rutas absolutas de las dependencias ya verificadas:

```bash
export GENIUS_R1_BASELINE=/ruta/recibida/R1
export GENIUS_R0_BASELINE=/ruta/recibida/R0
```

R1 debe contener `research/verify_fdq.py` y `research/fdq_oracle.py`; R0 debe contener `sources/repo/kernel/genius_kernel/`. El worker comprueba sus hashes recibidos e importa únicamente una copia temporal limpia de esos bytes, sin ejecutar archivos hermanos incidentales. Para reconstruir R0 desde R1, usar la herramienta `tools/receive_baseline.py` de R1 conforme a su recibo, con destino nuevo fuera de R1. No usar una instalación distinta de Kernel ni una rama reciente como sustitución implícita.

## Ejecutar y reconstruir un expediente

El ejemplo de horas es sintético: suma créditos contractuales y calcula exceso/déficit exactos. No acredita duración física, presencia ni utilidad. La copia permite preparar después una revisión sin editar el ejemplo versionado.

```bash
mkdir -p ../r2-demo
cp -R examples/hours ../r2-demo/hours-input
python3 -B -m genius_local run \
  --request ../r2-demo/hours-input/request.json \
  --case ../r2-demo/hours-case \
  --r1 "$GENIUS_R1_BASELINE" --baseline "$GENIUS_R0_BASELINE"
python3 -B -m genius_local inspect --case ../r2-demo/hours-case
python3 -B -m genius_local verify --case ../r2-demo/hours-case
```

`run`/`continue` devuelven un sobre de producto JSON. `inspect` reconstruye revisiones y último snapshot; `verify` comprueba la cadena y los artefactos. Una salida correcta de la CLI no es, por sí sola, una decisión matemática ni admisión empírica: leer transporte, ejecución, evidencia y decisiones por consulta.

Si falla la entrada o la publicación local, la CLI devuelve código 2 y un recibo de error por stderr. Cuando el sobre excede su presupuesto, el expediente conserva un cierre `BUDGET_CLOSED`, los recibos previos y el objeto no publicado por chunks; el error identifica HEAD. Ese recibo no es una respuesta RC01 truncada ni un Result matemático. Los límites numéricos están en `docs/OPERATIONAL_PROFILE.md`.

El ejemplo FDQ ejecuta el verificador recibido en proceso separado, conserva Input/Result originales y produce una afirmación formal condicional:

```bash
python3 -B -m genius_local run \
  --request examples/fdq_selector/request.json \
  --case ../r2-demo/fdq-case \
  --r1 "$GENIUS_R1_BASELINE" --baseline "$GENIUS_R0_BASELINE"
```

Su familia finita no prueba pertenencia de una medición física, ley agrícola o utilidad. La selección externa no cambia `OUTSIDE_DOMAIN` ni la cobertura del Result parcial.

## Continuar con un insumo pertinente

Una nueva revisión requiere `supersedes` contra el HEAD actual, número lógico siguiente y delta pertinente. Este ejemplo cambia un crédito de la copia de horas, actualiza el digest de la fuente y enlaza la revisión. Los bytes anteriores permanecen dentro del expediente.

```bash
python3 -B - <<'PY'
import hashlib
import json
from pathlib import Path
from genius_local.controller import inspect

root = Path('../r2-demo/hours-input')
request = json.loads((root / 'request.json').read_bytes())
state = inspect('../r2-demo/hours-case')
source = root / 'hours.json'
hours = json.loads(source.read_bytes())
hours['assignments'][0]['credit_hours']['value'] = '9/1'
raw = (json.dumps(hours, sort_keys=True, separators=(',', ':')) + '\n').encode()
source.write_bytes(raw)
digest = hashlib.sha256(raw).hexdigest()
source_id = next(a['id'] for a in request['artifacts'] if a['path'] == 'hours.json')
for artifact in request['artifacts']:
    if artifact['id'] == source_id:
        artifact['sha256'] = digest
for operation in request['operations']:
    assessment = operation['parameters'].get('assessment')
    if assessment and assessment['source_ref'] == source_id:
        assessment['source_digest'] = digest
request['revision'] = state['latest']['request']['revision'] + 1
request['supersedes'] = {'revision': state['revisions'][-1]['revision'], 'sha256': state['head']}
request['novelty'] = {'reason': 'Nuevo crédito contractual estipulado', 'changed_refs': [source_id]}
(root / 'request-next.json').write_text(json.dumps(request, ensure_ascii=False, indent=2) + '\n')
PY
python3 -B -m genius_local continue \
  --request ../r2-demo/hours-input/request-next.json \
  --case ../r2-demo/hours-case \
  --r1 "$GENIUS_R1_BASELINE" --baseline "$GENIUS_R0_BASELINE"
```

Cambiar sólo IDs/prosa/fecha, o duplicar la misma consulta con nuevos IDs, no habilita un intento. Se reutiliza un recibo previo compatible antes de recalcular; cambio de consulta, insumo, norma o dependencia invalida esa reutilización. Dos intentos sin avance sustantivo requieren revisar el encargo.

Si cambia la implementación local, la caché conserva los recibos históricos pero deja de promoverlos como resultados vigentes. Para reevaluar, preparar una solicitud con revisión incrementada y `supersedes` actual, `novelty.reason` igual a `REVERIFY_IMPLEMENTATION_CHANGED` y `changed_refs` que incluya la operación afectada. El controlador comprueba que los hashes del productor cambiaron o faltaban en el recibo histórico C1; no basta cambiar ese texto. La revisión nueva conserva el resultado anterior y vuelve a aplicar las guardas actuales. Si el snapshot del productor anterior quedó `RUNNING`, `recover` devuelve ese requisito sin modificar el expediente; usar `continue` con la reevaluación explícita desde ese HEAD. Los resultados históricos no se trasladan como verificados a la nueva ejecución.

## Interrupción y cancelación

`--cancel-file RUTA` permite cancelación cooperativa: crear ese archivo pide detener trabajo entre operaciones o terminar el subproceso FDQ. SIGINT/SIGTERM admitidos por el controlador también solicitan cancelación local. Un subproceso terminado sin recibo no se presenta como cálculo matemático cancelado internamente.

Tras una terminación forzada del proceso padre, primero reconstruir:

```bash
python3 -B -m genius_local inspect --case ../r2-demo/hours-case
python3 -B -m genius_local recover --case ../r2-demo/hours-case
```

`recover` conserva recibos terminados y cierra el intento interrumpido con ejecución desconocida. No ejecuta de nuevo operaciones ni adopta revisiones huérfanas. Un reinicio posterior usa nueva solicitud enlazada, `novelty.reason` igual a `RETRY_INTERRUPTED_OPERATION` y `changed_refs` que identifiquen una operación realmente iniciada sin recibo. Esa excepción operacional no admite repetir un intento completo sin novedad. No se promete reanudar el estado interno de Kernel, rollback, protección contra pérdida de disco ni servicio permanente.

## Reproducir conformidad

La suite usa fixtures sintéticos, diagnósticos heredados rotulados y un cliente de comprobación sin imports de implementación. No constituye revisión humana ni estudio de consumidores. Para ejecutar los casos que dependen de R1/R0, las dos variables anteriores deben apuntar a dependencias íntegras; revisar el recuento de casos omitidos.

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Para regenerar los fixtures FDQ en una carpeta de trabajo nueva, sin sobrescribir los entregados:

```bash
python3 -B examples/build_fdq_fixtures.py \
  "$GENIUS_R1_BASELINE" ../r2-demo/generated-fdq "$GENIUS_R0_BASELINE"
```

Ese generador construye entradas de prueba y expectativas declaradas; el caso de inviabilidad usa Kernel recibido para producir su Result original y un argumento de recursos independiente para la expectativa. La certificación efectiva ocurre al ejecutar la suite/CLI, no por generar el fixture.

`docs/INTERFACE.md` fija campos y firmas; `docs/OPERATIONAL_PROFILE.md`, los límites/fallos; `docs/CONTRACT_MAPPING.md` y `docs/CONSUMER_LIMITS.md`, el alcance de los contratos recibidos. F6A continúa en diseño y G6A pendiente. Esta capa no admite macetas, realiza contactos, ejecuta estudios, despliega servicios ni inicia R3.
