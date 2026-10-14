# Preparación de Club Genius v1 — 14/10/2026

Autoría: Codex, por encargo de Pedro Salvadeo. Referencia: issue #17.
Base revisada: `3b99da1741ba2f364b4fd52f2dd6205b2a9d04c2`.
Estado de este registro: implementación y comprobación local; CI y despliegue
deben verificarse por sus recibos. No declarar producción a partir de este archivo.

## Cambios

Membresía voluntaria, alias opcional, espacio privado de archivos UTF-8 con
versiones e integridad SHA-256, control de concurrencia, exportación y borrado
duradero. API REST y 12 herramientas MCP (una pública y once privadas).
No se amplían permisos de credenciales ya emitidas. Se conserva el contrato de
la bandeja pública. El contenido nunca se ejecuta ni se publica automáticamente.

Migración aditiva 005; lectores de respaldos reconocen borrados del club y la
actualización fuera de línea de esquemas históricos exactos. Límites iniciales,
retención, límites de recuperación de claves y operación: [CLUB.md](CLUB.md).

## Comprobaciones locales ejecutadas

- Dependencias del runtime existente instaladas desde `beta/requirements.lock`
  con `--only-binary=:all: --require-hashes`; sin cambios en dependencias.
- 62 pruebas PASS: `test_club`, `test_direct_agents`, `test_agent_access`,
  `test_mcp_access`, `test_r2_backup`. Incluyen accesos cruzados, concurrencia,
  reintentos, cuota acumulada por versiones, rotación, retención y restauración
  de originales con respeto a borrados posteriores.
- 3 pruebas PASS: `beta/deploy/test_recovery.py`.
- `git diff --check`: PASS.
- Suite amplia: 130 pruebas ejecutadas; NO está completamente aprobada.
  Cinco fallos y dos errores de FDQ/choice/examples se reproducen también
  en el checkout limpio de la base indicada (23 pruebas de esos módulos).
  No se modificaron el compilador, los cálculos ni sus fixtures para ocultarlos.
  Se observaron referencias históricas a `beta/vendor/R0/sources/repo/kernel`,
  directorio ausente en la edición pública; la reparación general del motor
  requiere su propio cambio y revisión.

Reproducción de las 62 pruebas, con dependencias ya instaladas:

```sh
PYTHONPATH=beta:beta/tests:product_local:consumer_views:twin:kernel \
  python -B -m unittest test_club test_direct_agents test_agent_access test_mcp_access test_r2_backup -v
```

`.github/workflows/club.yml` prepara la ejecución de esas comprobaciones dentro
de un contenedor sin red, sin credenciales persistidas, con montaje de fuente
de sólo lectura y recursos limitados. La preparación del workflow no acredita
que CI haya terminado; consultar el resultado asociado al commit.

## Publicación prevista

Reutilizar `genius-public-beta` en el entorno production del proyecto
`genius-beta-staging`, Dockerfile y volumen de 500 MB existentes. Desplegar
un commit identificado después de revisar CI. No crear servicios, bases,
dominios, billeteras, permisos de repositorio ni campañas de invitación.

Comprobar `/api/health`, `/club`, el manifiesto y el contrato; verificar mediante
una identidad temporal un recorrido de datos sintéticos, y eliminarla al terminar.
La prueba interna no demuestra adopción externa ni autonomía de otros agentes.
Ante una aprobación pendiente de la plataforma, conservar el cambio preparado
y reportar exactamente el estado; nunca eludirla.

## Mitigación y continuidad

Si hay un incidente, `GENIUS_CLUB_ENABLED=false` pausa escrituras y conserva
lectura/exportación/borrado. No volver a lectores de respaldo que desconozcan
`club_member` y `club_file`. Restauraciones permanecen fuera de línea y revocan
credenciales; no prometer recuperación automática de identidad.

Siguiente desarrollo: conversaciones y directorio voluntario, después entrega
explícita de archivos privados al integrador. Recuperación de credenciales,
diplomático, pagos y formatos binarios siguen pendientes.
