# Preparación del directorio y conversaciones — 14/10/2026

Autoría: Codex por encargo de Pedro Salvadeo. Continúa issue #17 y PR #18.
Base: `b7a666bf1e7939a28e4b5d2d727c35e2622d7b28`.
Este registro acredita implementación y comprobaciones locales; la publicación,
CI y el despliegue deben verificarse mediante sus recibos independientes.

## Alcance

Directorio público voluntario, nombre público opcional separado del alias privado,
solicitud y aceptación de conversaciones privadas, mensajes originales con hashes,
consulta incremental, exportación, bloqueo y borrado duradero. REST y MCP usan
los mismos controles. Los datos recibidos nunca se ejecutan. [Contrato](CLUB_SOCIAL.md).
Migración 006 aditiva; no modifica las cinco migraciones publicadas. Cuotas de
mensajes y archivos comparten el almacenamiento global existente.

## Verificación local ejecutada

76 pruebas PASS: `test_club_social`, `test_club`, `test_direct_agents`,
`test_agent_access`, `test_mcp_access`, `test_r2_backup`. Incluyen aislamiento entre
tres miembros, aceptación, retirada de publicación, alias privado, permisos,
concurrencia, reintentos, cuotas compartidas, exportación, baja, bloqueo y
restauración fuera de línea después de borrados. La actualización desde esquema
005 conserva archivos y aplica bloqueos posteriores al respaldo.
Además, las tres pruebas de `beta/deploy/test_recovery.py` pasan: 79 en total.

```sh
PYTHONPATH=beta:beta/tests:product_local:consumer_views:twin:kernel \
  python -B -m unittest test_club_social test_club test_direct_agents test_agent_access test_mcp_access test_r2_backup -v
```

CI amplía el contenedor existente sin red, sin credenciales persistidas,
con fuente de sólo lectura, usuario sin privilegios y recursos acotados.
Las limitaciones preexistentes de la suite amplia siguen documentadas en
[CLUB_RELEASE.md](CLUB_RELEASE.md); no se declara aprobada toda la suite beta.
Estas comprobaciones no demuestran adopción por terceros ni evidencia científica.

## Publicación y mitigación

Reutilizar el servicio Railway, volumen, respaldo y presupuesto existentes,
sin crear recursos ni ampliar permisos. Publicar el commit revisado después de
CI y comprobar salud, manifiesto, contrato, directorio y un recorrido sintético
permitido por las cuotas reales. Borrar las identidades temporales al terminar.

Si la plataforma requiere aprobación, preservar el cambio preparado y esperar
esa aprobación. No presentar la preparación como integración o despliegue real.
Ante un incidente, pausar escrituras con `GENIUS_CLUB_ENABLED=false`; no regresar
a lectores que desconozcan eventos de privacidad de esta versión. Recuperaciones
siguen fuera de línea, revocan claves, ocultan fichas y cierran conversaciones.
