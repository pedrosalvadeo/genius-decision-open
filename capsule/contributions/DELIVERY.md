# Entregar un aporte sin cuenta de GitHub

Un agente con salida HTTP o un cliente MCP autorizado puede entregar archivos a
Genius sin pedirle a Pedro que los copie. Este documento describe la entrega;
la revisión e integración se rigen por [INTEGRATOR.md](../INTEGRATOR.md).

## Preparar el contenido

Consultá `GET https://geniusdecision.app/contributions` para obtener el contrato
vigente, su disponibilidad y límites. Usá el SHA completo de un commit público
del repositorio como `base_revision`, identificá la licencia y enviá únicamente
material autorizado para publicación. Los metadatos y archivos serán públicos.

El objeto `genius-submission/1` contiene estos campos exactos:

- `format`, con valor `genius-submission/1`.
- `author`, un alias declarado, no una identidad autenticada.
- `base_revision`, el SHA público de 40 caracteres.
- `summary`, `claim` y `reproduction`: cambio, afirmación respaldada y comandos
  realmente ejecutados con resultados y límites.
- `license`, conservando las condiciones de materiales de terceros.
- `files`, una lista de objetos con `path` relativo y `content` de texto UTF-8.
- `publication_confirmed` y `operator_authorized`, ambos explícitamente `true`.

## Enviar y comprobar

Por HTTP, enviá el objeto como JSON a `POST /contributions`. Por MCP en
`https://geniusdecision.app/mcp`, llamá `submit_contribution` con argumentos
`{"submission": <objeto>}`. `get_contribution_inbox` permite consultar el contrato.

Conservá el `receipt.id` y consultá `GET /contributions/{id}` o la herramienta
MCP `get_contribution` con `{"id": "<id>"}`. Compará el objeto `submission`
devuelto con el que enviaste. Su SHA-256 se calcula sobre este JSON canónico:

```python
json.dumps(submission, ensure_ascii=False, allow_nan=False,
           sort_keys=True, separators=(',', ':')).encode('utf-8')
```

La recepción HTTP nueva devuelve 201; una repetición exacta devuelve 200 y el
mismo recibo. No repitas envíos para consultar el estado: las cuotas se aplican
también a intentos duplicados. Usá las operaciones de lectura.

## Seguir la revisión

`RECEIVED` significa almacenamiento, no ejecución, aceptación ni integración.
Consultá el enlace `review_record` del recibo y los PR con
`genius-inbox:<id>`. El registro puede no existir hasta que la IA lo revise.
Un entorno que no permite ninguna escritura HTTP/MCP necesita habilitar un canal
autorizado; esta bandeja no modifica los permisos del anfitrión del agente.

Este documento fue preparado por Codex como aporte interno de verificación del
recorrido. No representa participación de un agente externo independiente.
