# Genius adaptativo — continuidad y aprendizaje de recursos

Estado comprobado el 15 de octubre de 2026 UTC (14 de octubre por la noche en
Argentina). La integración del coordinador con el servicio está terminada y
activada. No volver a implementar este incremento ni solicitar nuevamente los
accesos ya habilitados.

## Incremento de aprendizaje preparado en esta edición

`resource_calibration_v1` agrega propuestas de estimación, comparación nativa de
error, guardas de subestimación, adopción interna y continuidad por memoria de una
misión propia. Contrato [RESOURCE_CALIBRATION.md](../beta/docs/RESOURCE_CALIBRATION.md),
ejemplo [resource-calibration.json](examples/resource-calibration.json).
No cambia la base de datos, dependencias ni infraestructura; usa el worker y respaldo
existentes. Es una actualización acotada de un parámetro, con validación retrospectiva.
La evidencia local está en [2026-10-15-learning](evidence/2026-10-15-learning).

La versión activa que figura debajo es la última comprobada **antes de desplegar
este incremento**. Consultar el PR de la rama `work/resource-learning-20261015` y
Railway para el estado posterior; no dar por activado un cambio sólo porque esté
mergeado. El despliegue debe fijarse al commit probado de ese PR y conservar el
volumen/configuración. Si el conector vuelve a cancelar `accept_deploy`, dejar el
cambio concreto preparado para aplicar en el panel, sin otra vía de mutación.

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

La calibración implementada aprende un estimador constante mediante mediana de
entrenamiento y contrasta errores en registros posteriores enviados juntos. La
adopción cambia sólo el artefacto privado y la base de un ciclo siguiente autorizado.
No demuestra generalización futura, ahorro de agua, bienestar o PVS. Las fuentes y
fechas son declaraciones del remitente, no certificaciones de sensores. No genera
estructuras arbitrarias ni modifica código por sí misma. Para una comprobación
prospectiva se necesita congelar primero la estimación y recibir registros nuevos
después, sin usarlos para ajustar esa misma predicción. No requiere proveedor LLM.

Defecto heredado separado: los adaptadores FDQ apuntan a `beta/vendor/R0` y `R1`,
ausentes en el repositorio público. La selección previa de 23 pruebas mostró
5 fallos y 2 errores por `PR_DEPENDENCY`. No se inventaron fuentes ni se cambiaron
sus pins para ocultarlo. Recuperar las fuentes exactas o declarar indisponibilidad
sigue pendiente; esta misión usa el gemelo y núcleo públicos presentes.

## Siguiente prompt

> Continuá desde `adaptive/HANDOFF.md` y el PR de `work/resource-learning-20261015`.
> Confirmá primero la versión activa; si el despliegue preparado ya fue aplicado,
> verificá por API dos ciclos sintéticos, la estimación heredada y el borrado de la
> cuenta de prueba. La distribución persistente ya está activa y comprobada. La
> calibración añade propuestas de mediana, evaluación nativa de error, guardas y
> memoria contextual; no la vuelvas a implementar. El próximo incremento útil es
> contrastar una estimación congelada con observaciones recibidas posteriormente,
> antes de usarlas en otro aprendizaje, y conservar esa evidencia prospectiva.
> Separá los resultados sintéticos, los registros declarados y los efectos realmente
> medidos. Conservá permisos, privacidad, recuperación y código en Git; no reinicies
> la arquitectura ni infieras bienestar/PVS a partir del error de estimación.
