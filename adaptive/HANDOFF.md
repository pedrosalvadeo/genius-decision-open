# Genius adaptativo — continuidad después del despliegue

Estado comprobado el 15 de octubre de 2026 UTC (14 de octubre por la noche en
Argentina). La integración del coordinador con el servicio está terminada y
activada. No volver a implementar este incremento ni solicitar nuevamente los
accesos ya habilitados.

## Versión activa

- URL: https://geniusdecision.app
- PR de implementación: https://github.com/pedrosalvadeo/genius-decision-open/pull/25
- Commit desplegado: `40086349dbcde45c292434dedea70612171fd6fc`.
- Railway: despliegue `4fcdf600-7473-4dea-bb3f-e6330905f18e`, estado `SUCCESS`.
- Proyecto `a93aa08c-f3b6-4a5b-accc-9812d6314f00`, entorno
  `1addd5b8-5a47-4301-aeca-d9596bceb4e0`, servicio
  `dafd0be5-61aa-4843-a3a3-3c1f487d9640`.
- `GENIUS_ADAPTIVE_ENABLED=true`; sin cambios pendientes en Railway.
- Se reutilizan el volumen de 500 MB en `/data`, una réplica y los límites existentes.

Pedro aplicó los dos cambios preparados en el panel después de que el conector
cancelara dos intentos de activación, incluso tras autorización explícita. El
reinicio posterior sí pudo ejecutarse mediante el conector, con autorización.
No repetir aquella solicitud de permiso ni confundir ese bloqueo histórico con
el estado actual, que ya está activo.

## Lo que puede hacer

Misiones privadas por cuenta mediante REST y herramientas MCP `mission_*`.
La primera operación recibe archivos UTF-8, compara TAR/gzip/ZIP, construye y
evalúa su modelo con el gemelo y núcleo existentes, entrega el archivo privado,
verifica contenido y registra memoria empírica. Las entradas de la API se
identifican como instantáneas enviadas; la CLI también admite commits Git explícitos.

El worker existente conserva cada etapa antes de permitir la siguiente. Los
checkpoints, entradas, evidencia y entrega están en la base principal, incluidos
en sus respaldos cifrados y en el borrado por cuenta. Hay permisos separados para
crear, ejecutar, leer y borrar; cuotas persistentes, cancelación, retención y
revisión ante cambios de identidad de ejecución. Contrato y límites:
[ADAPTIVE_MISSIONS.md](../beta/docs/ADAPTIVE_MISSIONS.md).
Guía pública: https://geniusdecision.app/static/missions.html.

## Evidencia

- 117 pruebas locales de servicio, recuperación y privacidad; 16 del coordinador.
  Registros en [2026-10-14-service](evidence/2026-10-14-service).
- CI del PR 25 sobre `83881b5bf096e390576efe496e81cfb39c7f3fae`:
  servicio Docker sin red (109 pruebas), recuperación adaptativa y cápsula: correctas.
  El árbol del merge desplegado coincide con ese código probado.
- Prueba de producción en [2026-10-15-live](evidence/2026-10-15-live): una misión
  sintética completó seis etapas en un intento; gzip de 263 bytes conservó los dos
  archivos enviados frente a TAR de 20.480 bytes. Estos tamaños corresponden al
  contenido repetitivo de la prueba, no a una estimación general de ahorro.
- Reinicio ordenado real del servicio: cierre de procesos a las 00:10:17 UTC y
  nueva inicialización a las 00:10:19–20. La misión, exportación y hash de entrega
  quedaron iguales; pedir ejecutar de nuevo reutilizó el resultado.
- La cuenta sintética fue eliminada; su credencial quedó revocada. El estado
  temporal se sustituyó por un recibo sin secretos y no forma parte del repositorio.
- Salud y respaldo después del reinicio: `ok`, servicio no suspendido.

La prueba en producción comprueba conservación de una misión completada durante
un reinicio ordenado. El corte forzado durante etapas activas y la restauración
con filtrado de borrados se comprobaron separadamente en pruebas aisladas.
El script de prueba respeta el proxy HTTPS del entorno y rechaza redirecciones.
Su corrección y esta evidencia no modifican los módulos del runtime desplegado;
Railway permanece fijado a `4008634`.

La misión original sobre los 460 archivos del repositorio sigue documentada en
[evidence/2026-10-14](evidence/2026-10-14): 7.220.896 bytes de contenido,
TAR 7.587.840, gzip 1.674.327 y ZIP 1.923.171, con integridad comprobada.

## Pendientes reales

La memoria conserva observaciones y reutiliza resultados bajo igual contexto.
Todavía no genera hipótesis, modifica modelos o código por sí misma ni realiza
acciones externas. Bienestar humano y PVS permanecen sin medir. No se necesita
proveedor LLM para la operación actual; agregar inferencia requiere una decisión
de proveedor y costo, sin bloquear el desarrollo que no la necesite.

Defecto heredado separado: los adaptadores FDQ apuntan a `beta/vendor/R0` y `R1`,
ausentes en el repositorio público. La selección previa de 23 pruebas mostró
5 fallos y 2 errores por `PR_DEPENDENCY`. No se inventaron fuentes ni se cambiaron
sus pins para ocultarlo. Recuperar las fuentes exactas o declarar indisponibilidad
sigue pendiente; esta misión usa el gemelo y núcleo públicos presentes.

## Siguiente prompt

> Continuá Genius adaptativo desde `adaptive/HANDOFF.md`. La integración del
> servicio y la prueba de persistencia en Railway ya están completas. Conservá
> esa base y avanzá hacia un ciclo que use observaciones para proponer y evaluar
> mejoras: ampliar el registro de misiones, comparar resultados con el objetivo,
> registrar propuestas y contrastarlas antes de adoptarlas. Elegí una aplicación
> útil alineada con bienestar y sostenimiento de la vida, separando sus hipótesis
> de efectos realmente medidos. No reinicies la arquitectura ni repitas las
> verificaciones cerradas. Implementá un incremento verificable, preservá sus
> cambios y evidencia en Git y entregá el próximo prompt de continuidad.
