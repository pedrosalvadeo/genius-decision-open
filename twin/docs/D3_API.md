# D3 — API de gemelos declarados

La misma capa `http_api.make_blueprint(service_factory, name="twin_api")` sirve a la UI y a clientes automáticos. La app local registra `/api`, conserva el control de Host/origen y solo debe escuchar en loopback. El montaje beta registra `/api/twin` bajo su autenticación, CSRF, cuotas y Store por usuario. El Blueprint no implementa autorización: su factory debe devolver únicamente el servicio autorizado de la solicitud. No acepta un `user_id` proporcionado por el cliente.

Esta API calcula consecuencias de modelos declarados. Confirmar un modelo no autentica datos, no establece validez empírica y no autoriza intervenir en el mundo. La validación empírica está pospuesta y no bloquea las operaciones de modelización.

## Descubrimiento

| Método y ruta relativa | Respuesta |
|---|---|
| GET `/capabilities` | Perfiles, ejemplos, operaciones, límites del ejecutor y estados separados; `mcp:false`, `physical_actions:false`, `rc01_receipt:false` |
| GET `/profiles` | `{profiles:[{id,label,scope,confirmation,observations}]}` |
| GET `/profiles/<id>/schema` | JSON Schema del perfil, con reglas semánticas adicionales indicadas; la validación del servidor es autoritativa |
| GET `/examples` | `{examples:[{id,title,profile}]}` |
| GET `/examples/<id>` | `{id,title,profile,model,provenance}`; lookup por catálogo cerrado, sin rutas/URLs del consumidor |

Perfiles: `SEMILLERO_14D_SYNTHETIC_V1` conserva D1; `STOCK_FLOW_FINITE_V1` admite un modelo configurable de existencias/flujos y políticas finitas. El contrato completo del segundo vive en `STOCKFLOW_CONTRACT.md`, su schema y sus ejemplos. No sumar bienestar entre portadores ni etiquetar una tarea operacional como supervivencia biológica. Las celdas nativas no definidas se conservan; `null` de la vista de producto no reemplaza una celda FP1.

## Expediente, borrador y propuestas

POST `/cases` con `{text,title?,profile?}` devuelve HTTP 201 y `{case,proposal,obligations,draft}`. Sin `profile`, o con `profile:"STOCK_FLOW_FINITE_V1"`, el caso empieza como borrador general en cualquier dominio. No interpreta parámetros ni ejecuta IA externa. `case.profile` conserva el perfil solicitado desde versión cero. La plantilla sintética D1 (semillero) se propone sólo si se pide por nombre con `profile:"SEMILLERO_14D_SYNTHETIC_V1"` y aún exige reconocimiento explícito; desde el 2026-10-18 las palabras del relato nunca eligen el perfil. `GET /capabilities` informa `STOCK_FLOW_FINITE_V1` como perfil por defecto, y las variables observables de D1 están en su entrada de `profiles`.

GET `/cases` devuelve `{cases:[...]}`. GET `/cases/<cid>` devuelve `{case,draft,versions,proposals,jobs,observations}`. `case.current_version:0` significa que todavía no se aceptó un modelo. Una obligación `MODELO_PENDIENTE` explica lo que falta; confirmar una propuesta válida resuelve esa obligación, sin afirmar admisión empírica.

PATCH `/cases/<cid>/draft`:

```json
{"base_version":0,"draft_revision":0,"text":"Premisas en preparación","model":null}
```

`model` puede ser un objeto incompleto o null. El borrador se guarda con `revision+1`, `base_version`, `text`, `model`, `updated_at`, `state:"DRAFT_NOT_ADMITTED"`. Persistirlo no ejecuta validación formal ni crea versión. Un conflicto de versión aceptada o revisión del borrador produce 409 sin pisar otro trabajo. El borrador y las versiones confirmadas son objetos distintos.

POST `/cases/<cid>/proposals`:

```json
{"base_version":0,"kind":"declared_model","text":"Declaro este modelo y sus premisas","structured":{"model":{"profile":"STOCK_FLOW_FINITE_V1"}}}
```

El objeto abreviado anterior muestra el sobre; no constituye un modelo válido. Sustituir `model` por un ejemplar completo conforme al schema. `declared_model` permite base cero y revisiones posteriores; el servidor valida antes de persistir la propuesta. Devuelve 201 `{proposal}` con `material_changes`, `metadata.changed_fields`, el modelo completo y origen `USER_DECLARED_MODEL`. Una propuesta no cambia la versión activa ni ejecuta cálculo.

POST `/proposals/<pid>/accept`:

```json
{"base_version":0,"idempotency_key":"confirmacion-modelo-1","confirmed":true,"acknowledge_declared":true}
```

Para D1 se exige `acknowledge_synthetic:true` en lugar de `acknowledge_declared`. El reconocimiento se decide por el perfil real de la propuesta, no por un campo del cliente que modifique su alcance. Una operación aceptada crea versión inmutable y devuelve `{case,version}`. La misma clave y solicitud exacta devuelven la respuesta original; reutilizar la clave para otra solicitud produce 409. La confirmación de una propuesta obsoleta produce 409 y no crea una versión.

POST de propuesta con `kind:"restore"`, versión actual en `base_version` y `structured:{version:<anterior>}` restaura el contenido del modelo mediante una nueva versión. Conserva historia, observaciones y revisión pendiente. Los cambios acotados D1 (`hypothetical_intervention`, `preference`, `fact_correction`) se conservan para ese perfil; los modelos configurables se editan como propuestas completas.

## Evaluación e historia

POST `/cases/<cid>/evaluate` con `{version:1}` devuelve `{job,evaluation}`. El recorrido HTTP espera un subproceso limitado. El job se persiste primero como `running` y termina `completed`, `failed` o, tras recuperación autorizada, `interrupted`. No hay cola asíncrona pública en este Blueprint. Los límites del ejecutor se publican en capabilities; agotarlos no prueba inviabilidad. GET `/jobs/<jid>` devuelve el mismo sobre congelado. El job agrega `elapsed_seconds`: lo que tardó, para que cada decisor mida su propio costo. GET `/jobs/<jid>/freshness` dice si el resultado sigue vigente: `CURRENT`, o `SUPERSEDED_BY_NEWER_OBSERVATION` con las observaciones registradas durante el cálculo, después, o antes pero en una versión posterior. El job nunca se reescribe; una observación nueva pide re-anclar y evaluar otra vez.

POST `/cases/<cid>/window` con `{version, window}` planifica para la ventana de oportunidad de un decisor (`genius_twin/decision_window.py`, formato `genius-decision-window/1`). `window` declara, en segundos exactos, el tiempo disponible, la duración real de un paso del modelo, cuánto falta para la acción del paso 1 desde el estado observado, la antigüedad de esa observación al empezar a calcular, cuánto tarda en aplicarse una decisión, la ruta que se sigue ahora y el costo medido por celda. Devuelve si la evaluación entra en la ventana, cuántos pasos quedan comprometidos con la ruta actual antes de que la decisión pueda actuar, qué rutas se vuelven idénticas y el modelo a evaluar. No borra escenarios ni rutas por su cuenta.

POST `/cases/<cid>/anytime/evaluate` con `{version, budget_seconds, tie_order?}` aplica AM-05 (`genius_twin/anytime.py`, formato `genius-anytime-evaluation/1`). Evalúa los escenarios de a uno, por masa decreciente y con los empates en `tie_order`, hasta agotar `budget_seconds` (60 como máximo). Cada corrida la verifica el kernel. Devuelve las rutas refutadas, la PVS de cada ruta como intervalo exacto, el bienestar, las funciones y la CAG de los escenarios evaluados, y una selección sólo si el modelo permite una única y queda una sola ruta no refutada. Cuenta como una evaluación y no se guarda como job.

La identidad de ejecución contiene perfil, hashes de dominio/compilador/registry/runner/kernel y contexto de límites. `execution_key` combina esa identidad con el digest del modelo. Reutilización de completed solo dentro de la misma versión e identidad; una actualización del compilador o límites no devuelve el recibo anterior como si fuera nuevo. Las evaluaciones antiguas siguen disponibles. La identidad del modelo no reemplaza `Result.input_digest`, que sigue referenciando los bytes exactos de FP1.

El sobre `genius-twin-evaluation/0.2.0` conserva `canonical_results`, `native_result`, `native_input_json`, `native_runs`, `verification`, `compilation_manifest`, versión, job e identidades. Para transporte y almacenamiento el sobre se empaqueta sin pérdida (`genius_twin/envelope.py`): cada Result nativo se guarda una vez, como su texto canónico, y al leerlo se reconstruye el sobre idéntico. `rc01_receipt:null` y su estado están afuera de los Result nativos: no se produce un recibo R2 ficticio.

Estados separados:

- Trabajo: transporte/ciclo de ejecución. `completed` no garantiza selección ni integración definida.
- Admisión: `SYNTHETIC_ONLY`, `DECLARED_MODEL_ONLY` o `MODEL_REVIEW_REQUIRED`.
- Empírico: `NOT_ASSESSED`; no deriva de un cálculo ni de aceptación del usuario.
- Matemático: cada celda nativa y verificación permanece intacta, incluidos los estados parciales.
- Recomendación: `CONDITIONAL_TO_DECLARED_MODEL` solo si existe selección canónica; `NO_SELECTION_UNDER_DECLARED_MODEL` si no hay selección; `NOT_ISSUED_UNVERIFIED_RESULT` ante verificación no recibida; `SUSPENDED_PENDING_MODEL_REVIEW` prevalece si hay revisión pendiente.

GET `/cases/<cid>/compare?before=1&after=2` devuelve ambas versiones, cambios por campo raíz y resultados congelados si existen. Ningún valor repetido transporta el certificado antiguo. GET `/cases/<cid>/export` devuelve `genius-twin-dossier/0.1.0`, expediente completo, evaluaciones e identidad del objeto exportado; la UI y el agente consumen el mismo contenido.

## Observaciones y lifecycle

D1 mantiene POST `/cases/<cid>/observations` con su contrato y referencias de predicción congelada. `STOCK_FLOW_FINITE_V1` declara `observations:false`: no admite todavía una observación del mundo mediante ese endpoint. Se rechaza explícitamente con 422, sin transformar variables de otros dominios en agua/tiempo del fixture. Editar una premisa declarada es diferente de observarla.

DELETE `/cases/<cid>` exige `{base_version:<actual>}` y borra el expediente íntegro. Rechaza versión obsoleta o job running. El Store mantiene sus triggers de inmutabilidad para actualizaciones y borrados aislados; `erase_case` abre una excepción transaccional limitada al expediente completo. Un callback interno `before_erase(cid)` permite al montaje autenticado conservar primero el ledger de borrado. No existe endpoint para insertar esos marcadores ni eliminar selectivamente una versión.

`TwinService.recover_jobs()` solo puede llamarse con exclusividad de lifecycle y sin ejecutor activo, como después de adquirir el lock del tenant en beta. Nunca corre automáticamente al construir la app o el servicio: un segundo objeto no debe interrumpir un cálculo ajeno. El lanzador local `python -m genius_twin` adquiere un lock exclusivo de la ruta canónica de SQLite, recupera una vez y mantiene el lock mientras atiende solicitudes sin threads; un segundo lanzamiento sobre la misma base termina con código 2 antes de recuperar o escuchar. Al salir, el sistema libera el lock; la terminación del padre también termina al compilador aislado. Tras recuperación se permite reintento explícito, sin borrar el job interrumpido. El montaje beta es responsable del aislamiento, retención, exportación de cuenta, ledger, borrado y restauración de todos los archivos del tenant.

## Errores y acceso M2M

Errores estables: `{error:{code,message,details}}`; 400 para estructura/JSON/modelo inválido, 404 para objeto ausente en el Store autorizado, 409 para conflictos, 415 sin JSON, 422 para reconocimiento/perfil de operación no admitido. JSON estricto rechaza claves repetidas, floats, no finitos y Unicode inválido; cantidades son texto exacto. No se descargan URLs ni ejecuta código recibido.

En beta, cookies necesitan el CSRF existente y los agentes usan Bearer revocable a nombre del usuario. Los tokens existentes no tienen scopes por operación: no se declara delegación granular implementada. La interfaz stdio `genius-protocols/1.0` sigue independiente; esta API no se declara MCP/A2A. La publicación del servicio, el comportamiento de retención/restauración y el transporte autenticado se reciben por sus pruebas de integración, no por esta especificación.
