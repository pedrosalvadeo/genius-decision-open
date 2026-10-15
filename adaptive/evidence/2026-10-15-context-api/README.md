# Integración contextual REST/MCP — comprobaciones locales

Implementación `resource_context_forecast_v1`, migración aditiva 010 y cinco
herramientas MCP. Contrato: `beta/docs/CONTEXT_FORECASTS.md`.

- `service-tests.txt`: 139 pruebas aprobadas con API, worker y proceso nativo
  reales locales; incluye privacidad, cuotas, respaldo/recuperación y contratos previos.
- `adaptive-tests.txt`: 46 pruebas aprobadas, incluida equivalencia por prefijos
  con la regla del observador v1, cuyos archivos permanecen sin modificar.
- `probe-tests.txt`: nueva comprobación de las dos pruebas del cliente de
  despliegue tras reforzar verificaciones del recibo final. Se superponen con las
  139 anteriores; no se suman como dos casos independientes.
- `summary.json`: alcance y recuentos.

Se agregaron 18 pruebas: 14 del contrato, dos del cliente, una de migración desde
v9 y una de equivalencia de regla. Se actualizaron preparaciones históricas que
simulan bases antiguas para retirar también las tablas 010 y esperar diez
migraciones. No se modificó ninguna migración histórica ni se relajaron hashes.

El cliente `beta/deploy/context_probe.py` fue ejecutado contra Flask/worker/núcleo
locales: perdió una respuesta después de aceptar un objetivo, reanudó sin duplicar,
cerró con verificación nativa, comprobó exportación y eliminó cuenta/credencial.
Sus objetivos sintéticos predefinidos comprueban mecánica, no una mejora empírica.

Esta evidencia no afirma despliegue público. El PR conserva CI del commit exacto
y el pin de Railway; hay que observar SUCCESS y ejecutar la prueba pública para
confirmar activación. No se repitió el ensayo HTTP del PR 35 ni se cambió su regla
después de ver resultados. Bienestar, PVS y generalización continúan sin medirse.
