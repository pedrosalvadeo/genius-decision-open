# Genius Protocols 1.0

Interfaz local de intercambio JSON-RPC 2.0 por stdio, con servidor Python y consumidor independiente Node.js. El contrato completo está en [CONTRACT.md](CONTRACT.md). No se anuncia MCP, A2A, HTTP ni OpenAPI. La identidad negociada incluye Specification, perfil, formatos y Kernel; una coincidencia de transporte por sí sola no autoriza otro significado matemático.

Requisitos ejecutados: Node.js **v24.19.0**, Python **3.12.14**, bibliotecas estándar de ambos lenguajes, Linux. No hay instalación npm/pip, red, cuenta, credenciales ni servicio externo. Ejecuta los comandos siguientes desde la raíz de `GENIUS_PHASE_4_HANDOFF`. Cada directorio `--out` debe ser nuevo y su padre debe existir. Una segunda ejecución usa otro nombre; no reemplaza resultados anteriores.

## Servidor y consumidor

El servidor directo se inicia así y recibe un mensaje UTF-8 terminado por LF por solicitud. Su primer mensaje debe negociar `genius.initialize`:

```bash
PYTHONPATH=protocols:kernel python3 -m genius_protocols
```

La CLI Node inicia ese proceso automáticamente, negocia y valida las capacidades antes de enviar una instancia. `--python EXECUTABLE` permite elegir el ejecutable Python sin invocar un shell.

```bash
node protocols/consumer/cli.mjs capabilities --out validation/MY_CAPABILITIES_01

node protocols/consumer/cli.mjs eval \
  --input examples/water_habitat_f4/input.json \
  --out validation/MY_EVALUATION_01

node protocols/consumer/cli.mjs verify \
  --input validation/MY_EVALUATION_01/input.json \
  --candidate validation/MY_EVALUATION_01/result.json \
  --out validation/MY_VERIFICATION_01

node protocols/consumer/cli.mjs verify-certificate \
  --input validation/CONSUMER_CONFORMANCE_04/artifacts/C10_valid/input.json \
  --candidate validation/CONSUMER_CONFORMANCE_04/artifacts/C10_valid/candidate.json \
  --out validation/MY_CERTIFICATE_VERIFICATION_01
```

`eval` exporta **input.json y result.json con sus bytes exactos**, `digests.json` y la negociación. `verify` y `verify-certificate` exportan input, candidate, verification y sus digests; nunca sustituyen el candidato por una versión reparada. Los archivos se escriben exclusivamente (`wx`), dentro de un directorio creado exclusivamente. Una interrupción al escribir puede dejar un directorio incompleto; se conserva para inspección y la siguiente ejecución debe usar otro.

El ejemplo completo conservado está en `examples/water_habitat_f4`; [examples/README_F4.md](../examples/README_F4.md) documenta su expediente. La pareja exportada también se puede comprobar por la CLI original del Kernel, fuera del adaptador:

```bash
PYTHONPATH=kernel python3 -m genius_kernel verify \
  validation/MY_EVALUATION_01/input.json \
  validation/MY_EVALUATION_01/result.json
```

Para límites operativos, `--limits FILE` recibe un objeto como `{"max_operations":"0"}`. Las cinco claves permitidas son `max_nodes`, `max_operations`, `max_seconds`, `max_input_bytes`, `max_integer_digits`; valores Nat canónicos de hasta 12 dígitos, siempre strings. No se convierten los números del problema a `Number`. Omitir la opción equivale a no imponer límites artificiales adicionales. Los límites de transporte y del parser siguen siendo aplicables y se anuncian al negociar.

La CLI devuelve código cero cuando recibió y exportó un resultado/report válido de protocolo, incluso cuando el resultado tiene presentación INVALID, ejecución LIMITED o el verificador rechaza el candidato. El JSON de stdout conserva esos estados para que el llamante decida. Código uno indica error de CLI, filesystem, protocolo o transporte; el detalle está en stderr. Ctrl-C/SIGTERM termina el proceso hijo y descarta la sesión: no fabrica un Result LIMITED ni una refutación matemática.

## API Node reutilizable

`protocols/consumer/client.mjs` exporta `GeniusClient`. `initialize()` precede toda instancia; `evaluate(Buffer)`, `verifyResult(Buffer,Buffer)` y `verifyCertificate(Buffer,Buffer)` devuelven bytes originales junto con el resultado/report completo. `close()` libera el proceso. Todas las operaciones son seriales: esperar cada promesa antes de enviar otra.

El cliente acepta `{command,args,cwd,env,timeoutMs,onFrame}` para controlar únicamente el proceso que inicia. `onFrame(direction,Buffer)` permite registrar los frames exactos sin importar código Python. En cada llamada de cálculo/verificación, `{limits,signal,timeoutMs}` configura límites, cancelación del proceso y plazo local. Los Buffers del llamante se copian antes de enviar: modificarlos durante `await` no puede alterar lo exportado después. El plazo predeterminado de 60 segundos es del cliente, no un límite matemático del servidor.

`exportExchange(newDirectory,exchange,capabilities)` en `consumer/package.mjs` genera un expediente de bytes. El cliente comprueba digest de cada blob, eco exacto del input y vínculo `Result.input_digest`. No implementa otro evaluador matemático: la aceptación de un certificado se obtiene mediante el método de verificación público, cuyo Kernel comparte constructores con la evaluación.

## Reproducción de evidencia

```bash
node protocols/tests/consumer_conformance.mjs validation/MY_CONSUMER_CONFORMANCE_01
node protocols/tests/consumer_replay.mjs validation/MY_CONSUMER_REPLAY_01 all
```

La primera suite tiene C01–C25: negociación, precisión >2^53, Unicode, IDs nominales, conjuntos, parcialidad, estados ortogonales, bytes/digests, certificados, rechazo, límites, exportación y procesos que mueren o se cancelan. C23 es una prueba explícita de la gramática del estado ERROR, no una afirmación de haber provocado un fallo real del Kernel.

El replay recorre las 3.338 llamadas guardadas en F3 (`CORRECTNESS_FINAL` y `PERF_FINAL`), sin importar Benchmark ni Kernel. Las 508 fichas incluyen dos sin llamadas. Conserva archivos fuente, digests, cada input/candidate/resultado/report y comparación por ID original. Compara el objeto heredado completo para los candidatos aceptados por el parser; para los dos candidatos heredados con número JSON registra separadamente el rechazo `CANDIDATE_TYPE` exigido por P05 y la diferencia de mensaje heredado. Es evidencia de intercambio de datos heredados, **no un nuevo oráculo matemático ni una medición de rendimiento**.

`correctness` o `performance` pueden reemplazar `all` para limitar el replay. Los informes finales y las limitaciones de interpretación están en [CONSUMER_DESIGN.md](CONSUMER_DESIGN.md). No se requieren permisos de publicación y estos comandos no publican, despliegan ni contactan terceros.
