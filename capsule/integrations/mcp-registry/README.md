# Genius publicado en el MCP Registry oficial

**Estado: activo; versión 0.2.0 publicada el 14 de octubre de 2026 a las 10:32:10 UTC.** Nombre: `io.github.pedrosalvadeo/genius-decision`. [Consultar la entrada oficial](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.pedrosalvadeo/genius-decision) · [Recibo y metadata recuperada](publication.json) · [Ficha publicada](server.json).

La publicación fue autorizada por Pedro y se autenticó desde su repositorio mediante GitHub OIDC, siguiendo el [procedimiento oficial](https://modelcontextprotocol.io/registry/github-actions). No se solicitó contraseña ni se creó un token personal de GitHub. El token temporal del runner fue eliminado al finalizar.

## Evidencia

- `mcp-publisher` **1.8.1**, distribución oficial Linux amd64 con SHA-256 comprobado.
- Validación, autenticación y publicación: pasos aprobados en [la ejecución inicial](https://github.com/pedrosalvadeo/genius-decision-open/actions/runs/38550230162).
- La consulta de comprobación de ese workflow agotó 30 segundos; la publicación ya había terminado. No se repitió el alta.
- Una consulta pública posterior devolvió HTTP 200, una única versión 0.2.0 y estado `active`, `isLatest: true`. Se comprobó toda la metadata contra la ficha aprobada. El registro omite el campo opcional `isRequired: false`, conservando su significado.

El [recibo de validación anterior](validation.json) conserva el estado histórico previo al alta. La versión 0.2.0 corresponde al servidor MCP (`beta/genius_beta/mcp_access.py`), distinta de la versión de la cápsula. La entrada permite descubrir el servicio; no demuestra que un agente independiente lo haya usado ni que la comunidad respalde el proyecto.

## Acceso declarado

MCP Streamable HTTP: `https://geniusdecision.app/mcp`. Página de configuración: `https://geniusdecision.app/agents`. No requiere un paquete npm/PyPI.

Authorization es opcional para el descubrimiento público; las herramientas privadas requieren `Bearer <token>` y permisos explícitos. La ficha no contiene credenciales. El servicio no ofrece OAuth: esto es distinto de la autenticación OIDC usada para publicar la ficha. El registro por defecto no incluye permisos del gemelo.

Se conservaron enlaces al manifiesto y la cápsula, permisos y política de datos sintéticos o no personales. Las evaluaciones consumen cuota compartida y los resultados dependen del modelo declarado.

## Verificar y actualizar

El [workflow manual](../../../.github/workflows/publish-mcp-registry.yml) está limitado a `main`, este repositorio y el actor `pedrosalvadeo`. Por defecto sólo verifica la entrada. Para tolerar demoras transitorias, las consultas GET tienen 60 segundos y hasta tres intentos. No se reintenta la publicación.

Publicar requiere seleccionar expresamente `publish`. El archivo debe coincidir con el hash revisado; antes de una versión futura, actualizar la versión y el hash tras revisar y autorizar sus metadatos. El workflow no se ejecuta por pushes, PRs, etiquetas ni horarios. Usa `contents: read` e `id-token: write` sólo en el job; no obtiene el token OIDC cuando se ejecuta en modo de verificación.

La plantilla reproducible se conserva en [capsule/publication](../../publication/mcp-registry-publish.yml). Fuentes oficiales: [quickstart](https://modelcontextprotocol.io/registry/quickstart), [servidores remotos](https://modelcontextprotocol.io/registry/remote-servers), [autenticación](https://modelcontextprotocol.io/registry/authentication) y [GitHub Actions](https://modelcontextprotocol.io/registry/github-actions). Referencia documental: `modelcontextprotocol/registry@11b7b0e274d518b6f449c5ee3518a6151d9848b9`; esquema `2025-12-11`.
