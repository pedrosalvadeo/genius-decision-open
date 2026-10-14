# Puente de aportes del Club Genius — preparación 14/10/2026

Autoría: Codex por encargo de Pedro Salvadeo. Continúa #17 y #19.
Base: `1f4b716061748cf05ea915b4fad30cd2ba504231`.
Este registro acredita implementación y comprobaciones locales. CI, fusión y
producción se acreditan mediante sus recibos separados, después de verificarlos.

## Cambio

Selección de versiones propias, previsualización privada, confirmación de
publicación ligada al SHA-256, depósito público y enlace privado atómicos,
atribución opcional, reintentos, exportación y entregas corregidas vinculadas.
Consulta acotada de revisiones públicas de GitHub sin credenciales, con caché y
verificación de PR fusionado y ascendencia antes de mostrar `ACCEPTED`.
Se conserva el contrato y cuotas de la bandeja pública. No se amplían permisos.
Migración 007 aditiva y cinco herramientas MCP adicionales.

## Comprobación local ejecutada

101 pruebas PASS: puente, bandeja, club social, archivos, acceso, MCP, respaldos
R2 y recuperación local. Incluyen aislamiento entre miembros, consentimiento,
hash de publicación, versiones originales, concurrencia y reintentos, errores
atómicos, cuota compartida, rechazo de referencias GitHub ajenas, aceptación sólo
tras comprobar fusión e historia, caché desactualizada explícita y conservación
del depósito público al borrar los enlaces privados.

```sh
PYTHONPATH=beta:beta/tests:product_local:consumer_views:twin:kernel \
  python -B -m unittest test_club_contributions test_contributions test_club_social test_club test_direct_agents test_agent_access test_mcp_access test_r2_backup beta/deploy/test_recovery.py -v
```

Los tests de revisión usan respuestas sintéticas y no realizan llamadas de red.
Una consulta separada de sólo lectura al recibo público `807279909b2da33155065a729110084c9034a8f6b82330e270fe5c6f2ea78b7b` no obtuvo respuesta de GitHub desde el entorno local: devolvió `UNKNOWN`, `integrated: false`, `stale: true`, `refresh_error: github_unavailable`. No acredita conectividad en producción; se debe verificar tras el despliegue.
CI ejecuta las pruebas del club y bandeja en el contenedor aislado existente,
sin red ni credenciales persistidas. Las limitaciones históricas de la suite beta
amplia continúan en [CLUB_RELEASE.md](CLUB_RELEASE.md); no se declara aprobada
toda esa suite ni se altera el motor para ocultar sus fallos.

## Publicación prevista y límites

Reutilizar servicio, volumen, respaldo y presupuesto Railway existentes; fijar
el commit integrado después de CI. Si la plataforma exige aprobación, dejar la
actualización preparada. Comprobar salud, contrato y consulta de fuentes públicas.
Una prueba con entrega pública se debe identificar expresamente como verificación
interna: ese original es inmutable, no una contribución independiente de terceros.

No enviar invitaciones, crear un diplomático, ejecutar aportes, aumentar gastos
ni alterar la automatización integradora en esta entrega. La consulta muestra
lo registrado; no sustituye al revisor. [Contrato completo](CLUB_CONTRIBUTIONS.md).
