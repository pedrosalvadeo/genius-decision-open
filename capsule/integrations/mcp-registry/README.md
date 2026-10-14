# Ficha para el MCP Registry oficial

**Preparada y validada; todavía no publicada ni autenticada.** [server.json](server.json) propone el nombre `io.github.pedrosalvadeo/genius-decision` y la versión del servidor MCP `0.2.0`. Esta versión proviene de `beta/genius_beta/mcp_access.py`; es distinta de la versión de la cápsula.

El comando oficial `mcp-publisher validate` de la versión **1.8.1** aprobó la ficha contra `https://registry.modelcontextprotocol.io`. [Recibo de validación](validation.json). Se verificó el SHA-256 del archivo de distribución Linux amd64 contra el digest del asset de la release oficial. Validar no reserva el nombre, autentica al propietario ni registra el servidor.

## Qué declara

Servidor remoto Streamable HTTP en `https://geniusdecision.app/mcp`, repositorio Apache-2.0 y página de configuración. No requiere un paquete npm/PyPI. El encabezado Authorization es opcional para el descubrimiento público; las herramientas privadas requieren el valor completo `Bearer <token>` obtenido mediante registro y permisos explícitos. No hay valores de credenciales ni OAuth en la ficha. Los permisos de gemelo no están incluidos en el registro por defecto.

La metadata adicional conserva los enlaces al manifiesto y cápsula, el registro, los permisos y la política de datos sintéticos o no personales. Las evaluaciones consumen cuota compartida y sus resultados dependen del modelo declarado. El registro facilita descubrir metadatos; no obliga a agentes a visitar o usar Genius.

## Publicación pendiente

Después de revisar y autorizar el alta, desde la raíz del repositorio y con el [publisher oficial](https://github.com/modelcontextprotocol/registry/releases/tag/v1.8.1) instalado:

```sh
mcp-publisher validate capsule/integrations/mcp-registry/server.json
mcp-publisher login github
mcp-publisher publish capsule/integrations/mcp-registry/server.json
```

El flujo GitHub verifica el namespace de la cuenta `pedrosalvadeo` mediante autorización de dispositivo. No hay credenciales guardadas por esta preparación. Antes de publicar, comprobar si ya existe el nombre y su versión; después, recuperar la entrada oficial y conservar el resultado del alta. Si el nombre o URL ya están registrados, resolver el conflicto con el registro antes de intentar otro nombre. No se afirma que este nombre esté reservado o disponible.

Fuentes oficiales revisadas el 14 de octubre de 2026: [quickstart](https://modelcontextprotocol.io/registry/quickstart), [servidores remotos](https://modelcontextprotocol.io/registry/remote-servers) y [autenticación](https://modelcontextprotocol.io/registry/authentication). Referencia del repositorio de documentación: `modelcontextprotocol/registry@11b7b0e274d518b6f449c5ee3518a6151d9848b9`; esquema `2025-12-11`.
