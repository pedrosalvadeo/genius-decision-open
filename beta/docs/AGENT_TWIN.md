# Acceso autónomo al gemelo: REST y MCP

Esta edición implementa 15 herramientas MCP sobre la API autenticada existente.
El estado del despliegue se consulta en `/agents/manifest.json`: `twin.available`
debe ser verdadero y `registration.available_scopes` debe contener `twins:read`.
La publicación del código por sí sola no acredita su despliegue en el servicio.

Cada agente se registra en `POST /api/agents/register` reconociendo la política
vigente obtenida del manifiesto, con `data_policy_acknowledged: true` y permisos
explícitos en `scopes`. No necesita una cuenta humana ni acceso a sus datos.
Los permisos nuevos son `twins:read`, `twins:write`, `twins:evaluate` y
`twins:delete`; `account:delete` permite borrar el espacio completo. Los permisos
por defecto y las demos anteriores no obtienen acceso al gemelo. La rotación
permite reducir permisos; para ampliarlos hace falta un nuevo registro.

La credencial se envía únicamente en `Authorization: Bearer ...`, nunca como
argumento MCP, URL ni archivo del repositorio. MCP usa `POST /mcp`, encabezados
`Accept: application/json, text/event-stream` y
`MCP-Protocol-Version: 2025-11-25`, con JSON-RPC 2.0 `tools/list` o `tools/call`.
El servicio también mantiene las versiones de protocolo que anuncia su manifiesto.

## Ciclo de trabajo

1. `twin_capabilities`, `twin_schema` y `twin_example`: conocer perfiles, contratos
   y límites. Un ejemplo no constituye evidencia del caso propio.
2. `twin_create_case`: `payload` contiene `text`, y opcionalmente `title` y
   `profile`. Para existencias y flujos usar `STOCK_FLOW_FINITE_V1`.
3. `twin_save_draft`: `case_id`, `payload` con `base_version`, `draft_revision`,
   `text` y `model` (objeto o null). No acepta ni evalúa premisas.
4. `twin_propose`: `case_id`, `payload` con `base_version`,
   `kind: "declared_model"`, `text` y `structured: {"model": ...}`.
5. Revisar cambios materiales. `twin_accept`: `proposal_id`, `payload` con
   `base_version`, `idempotency_key`, `confirmed: true` y
   `acknowledge_declared: true` (o `acknowledge_synthetic` para el semillero).
   Confirmar requiere autoridad del dueño de la decisión; no se inventa ni
   equivale a autenticar fuentes, validar hechos o autorizar acciones físicas.
6. `twin_evaluate`: `case_id`, `version` aceptada. Devuelve el recibo del motor,
   su verificación y sus límites. `twin_get_job` lo recupera por `job_id`.
7. `twin_get_case`, `twin_compare` (`before`, `after`) y `twin_export` conservan
   el historial. `twin_observe` admite únicamente el contrato del semillero en
   [D3_API](../../twin/docs/D3_API.md); las observaciones de stockflow siguen abiertas.
8. `twin_delete_case`: `case_id`, `base_version`, `confirm: true`.
   `delete_agent_space` con `confirm: true` elimina también los expedientes
   del gemelo y revoca la cuenta. Exportar antes cuando se necesite conservarlos.

Las rutas REST equivalentes están en [D3_API](../../twin/docs/D3_API.md) y en
`twin/genius_twin/http_api.py`. Todas las herramientas usan esas mismas rutas;
no existe un proxy de URLs suministradas por el cliente.

## Límites y evidencia

Solo datos sintéticos o no personales en el servicio de agentes actual.
Las cantidades se expresan como cadenas exactas, sin floats JSON.
El relato no se transforma en parámetros por inferencia automática. El cálculo
es condicional al modelo declarado y no acredita validación empírica general.
Estas fronteras describen el estado actual, no limitan el programa de desarrollo.

Las evaluaciones del gemelo y los trabajos tradicionales comparten los contadores
diarios por agente y globales de agentes. Los intentos rechazados después de la
reserva y las consultas de evaluación repetidas también consumen cuota; no
reintentar automáticamente. Hay un único compilador de gemelos simultáneo.
Los límites de casos se aplican por familia (casos tradicionales / gemelos),
y las versiones por expediente; todos comparten el presupuesto de almacenamiento.
Los bloqueos de ciclo de vida impiden borrar una cuenta durante una operación.
La eliminación registra primero la intención durable y después elimina los datos.

## Verificación reproducible

Instalar las dependencias de `beta/requirements.lock` en Python 3.12 y ejecutar:

```sh
PYTHONPATH=beta:twin:kernel:protocols python3 -m unittest discover -s beta/tests -p 'test_agent_twin.py' -v
PYTHONPATH=beta:twin:kernel:protocols python3 -m unittest discover -s beta/tests -p 'test_mcp_access.py' -v
PYTHONPATH=beta:twin:kernel:protocols python3 -m unittest discover -s beta/tests -p 'test_twin_integration.py' -v
```

La prueba nueva ejecuta el motor real, verifica su recibo, comprueba aislamiento,
permisos explícitos, rotación sin ampliación, cuotas compartidas y borrado.
Es evidencia de funcionamiento del software, no de adopción por agentes externos.
