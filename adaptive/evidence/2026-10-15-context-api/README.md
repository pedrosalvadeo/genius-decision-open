# Integración contextual REST/MCP — validación y despliegue

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
- `deployment.json`: commit servido, despliegue SUCCESS y CI del código integrado.

Se agregaron 18 pruebas: 14 del contrato, dos del cliente, una de migración desde
v9 y una de equivalencia de regla. Se actualizaron preparaciones históricas que
simulan bases antiguas para retirar también las tablas 010 y esperar diez
migraciones. No se modificó ninguna migración histórica ni se relajaron hashes.

El cliente `beta/deploy/context_probe.py` fue ejecutado contra Flask/worker/núcleo
locales: perdió una respuesta después de aceptar un objetivo, reanudó sin duplicar,
cerró con verificación nativa, comprobó exportación y eliminó cuenta/credencial.
Sus objetivos sintéticos predefinidos comprueban mecánica, no una mejora empírica.

El PR 36 integra el código probado en `611d1dcf1d313a3831913f5c3853d48113aba4b4`;
su merge `7fdb633549473984e16bfb67ed60b629cafe91d5` conserva el mismo árbol.
CI aprobado: Adaptive 38683874426, Club 38683874475, Capsule 38683874464.
Railway confirmó SUCCESS para `ec8dada7-baae-4f79-9e28-9ec1329cbc47`, con ese
pin y sin cambios pendientes. Se reutiliza la infraestructura existente.
Aunque el conector devolvió inicialmente una cancelación de Apply, la lectura
posterior confirmó el despliegue; no se reintentó la aplicación por otra vía.

No se repitió el ensayo HTTP del PR 35 ni se cambió su regla después de ver
resultados. Bienestar, PVS y generalización continúan sin medirse.

## Prueba pública completada

`live-probe.json` conserva los recibos sin credenciales; `summary.json` incluye
su hash. Ejecución del 15 de octubre de 2026, 04:59:56–05:04:04 UTC, seguida de
limpieza confirmada. Se usó una cuenta temporal por REST en geniusdecision.app.
El manifiesto y la identidad del evaluador servido coincidieron con el código local.

Se completaron tres objetivos iniciales y doce puntuados. La política realmente
aplicada conservó la base en nueve decisiones y eligió mediana contextual en tres;
error absoluto total 540 → 420, máxima subestimación 50 → 50, dentro del límite 50.
Los dos contextos tuvieron seis objetivos puntuados cada uno. El informe nativo,
los hashes y el encadenamiento temporal coincidieron con el recálculo del cliente.
Repetir el cierre recuperó el mismo informe y la exportación fue idéntica.
La cuenta fue borrada y el token rechazado con 401; se retiró del estado privado.

Los objetivos alternantes estaban predefinidos: este resultado confirma la
integración y el cambio efectivo de estrategia, no una mejora empírica. No se
reinició producción ni se ejerció el transporte MCP público en esta prueba;
MCP, reinicios, concurrencia y restauración tienen pruebas locales separadas.
El resultado HTTP negativo anterior sigue vigente. No cambia runtime este
registro de evidencia; Railway permanece fijado al merge probado del PR 36.
