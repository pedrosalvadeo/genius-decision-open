# Integración de Genius con OpenHands

**Estado: enviada como borrador en [PR 772](https://github.com/OpenHands/extensions/pull/772).** La propuesta [OpenHands/extensions#770](https://github.com/OpenHands/extensions/issues/770) recibió clasificación automática `ready-for-dev`. Este paquete implementa sus criterios técnicos sobre el commit `f1919e4e3e02c0bab65c2417761aee775f1ffbaa` de Extensions.

El [parche](genius-decision.patch) añade exactamente una entrada escrita a mano, `integrations/catalog/genius-decision.json`, y regenera `integrations/catalog-index.js` con el generador oficial. Declara MCP Streamable HTTP, Bearer y los permisos de las herramientas del gemelo; no contiene credenciales, OAuth ni cambios al runtime de OpenHands.

## Resultado comprobado

El 14 de octubre de 2026, OpenHands SDK **1.54.0**, instalado desde PyPI, conectó con https://geniusdecision.app/mcp usando `create_mcp_tools`, la validación de argumentos del SDK y su ejecutor de herramientas. Se completaron 18 comprobaciones:

- Descubrimiento de 3 herramientas públicas y 19 con el permiso solicitado, incluidas las 15 del gemelo.
- Registro de una identidad temporal, propuesta y aceptación explícita del ejemplo sintético publicado `stockflow_care`.
- Una evaluación del motor real: trabajo `completed`, verificación `VALID`, sin errores.
- Lectura del trabajo, exportación, borrado del expediente y del espacio por MCP; la credencial eliminada devolvió HTTP 401.

Pasaron **117 pruebas existentes del catálogo** y la comprobación de sincronización. Esta última conserva un aviso no bloqueante ajeno a la entrada: `plugins/issue-duplicate-checker` no aparece en un marketplace. Las URL de aplicación y documentación respondieron HTTP 200.

[Recibo de ejecución](verification.json) · [Validación del catálogo](catalog-validation.json) · [Texto del PR](PR_DRAFT.md) · [Registro de envío](submission.json). La validación del catálogo conserva el estado anterior al envío; `submission.json` registra el estado posterior.

Esta es una prueba propia con un cliente externo publicado. No acredita que un operador independiente haya adoptado Genius, que OpenHands haya aceptado la integración, ni que el modelo sintético describa una decisión real. No se usó un LLM ni se probó el flujo visual de Cloud/GUI/CLI. Se conservan hashes del modelo y exportación; el expediente temporal fue eliminado. Los hashes permiten comparar contenidos disponibles, pero no sustituyen un archivo que no se conservó.

## Reproducir la prueba del cliente

Requiere Python 3.12 y acceso HTTPS a Genius. Desde la raíz del repositorio Genius:

```sh
python3.12 -m venv /tmp/genius-openhands-venv
/tmp/genius-openhands-venv/bin/python -m pip install -r capsule/integrations/openhands/requirements.lock
/tmp/genius-openhands-venv/bin/python capsule/integrations/openhands/verify_client.py --out /tmp/genius-openhands-discovery.json
```

El comando anterior sólo consulta el manifiesto y las herramientas públicas. Cuando el operador autorice la prueba con escritura:

```sh
/tmp/genius-openhands-venv/bin/python capsule/integrations/openhands/verify_client.py --live --out /tmp/genius-openhands-live.json
```

`--live` reconoce la política técnica vigente, crea una identidad propia con permisos explícitos, acepta únicamente el ejemplo sintético, consume una evaluación de la cuota compartida y elimina su espacio. No lee credenciales preexistentes ni las guarda. No repite automáticamente la evaluación; ante un fallo registra el resultado y ejecuta la limpieza. Cada ruta de salida debe ser nueva. Las cuotas y el estado del servicio pueden impedir una reproducción posterior.

Durante la ejecución observamos un aviso de LiteLLM al intentar descargar su tabla pública de precios: utilizó su copia local. También hubo un aviso de obsolescencia de FastMCP para `sse_read_timeout`. No impidieron la prueba y no hubo llamadas a modelos. El script preserva exactamente la versión probada, cuyo SHA-256 figura en el recibo.

## Aplicar y comprobar el parche

En una copia de `OpenHands/extensions` sobre la revisión indicada, aplicar el parche descargado en `/tmp/genius-decision.patch`:

```sh
git switch -c genius-decision-mcp f1919e4e3e02c0bab65c2417761aee775f1ffbaa
git apply --check /tmp/genius-decision.patch
git apply /tmp/genius-decision.patch
npm run build:integrations
/tmp/genius-openhands-venv/bin/python -m pip install -e .
/tmp/genius-openhands-venv/bin/python -m pytest -q tests/test_catalog_schema.py tests/test_catalogs.py tests/test_integration_catalog_in_sync.py
/tmp/genius-openhands-venv/bin/python scripts/sync_extensions.py --check
git diff --check
```

Los archivos de esta carpeta son material de reproducción de Genius; el PR de Extensions sólo debe incluir los dos archivos del parche. Si cambió la rama upstream, revisar y regenerar el índice con su generador actual antes de presentar la propuesta.

## Envío y revisión

El [borrador](PR_DRAFT.md) conserva sin completar la sección `HUMAN` de la plantilla oficial. La plantilla pide mantener el PR como borrador hasta que una persona escriba allí una nota de al menos 20 caracteres visibles; un agente no debe redactarla en su nombre. Esa intervención es necesaria para marcarlo listo para revisión, no para preparar el código o sus pruebas.

Enviado con autorización de Pedro el 14 de octubre de 2026 a las 05:18:53 UTC, vinculado al issue 770. Los dos archivos publicados coinciden con los probados. El título y los artefactos pasaron las validaciones automáticas; tres workflows esperan autorización de un mantenedor por ser una contribución desde un fork.

Siguiente acción: Pedro revisa el resultado y completa la sección HUMAN con su propia nota antes de marcarlo listo para revisión. Los mantenedores de OpenHands deben autorizar los workflows y decidir la incorporación al catálogo. El PR permanece como **draft**; no se ha confirmado aceptación ni ejecución independiente.
