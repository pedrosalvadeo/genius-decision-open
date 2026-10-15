# Genius adaptativo — comprobación prospectiva activada y verificada

Estado comprobado el 15 de octubre de 2026 a las 03:37 UTC (00:37 en Argentina).
El usuario aplicó el cambio del PR 31 en Railway. La comprobación prospectiva está
activa y pasó el ensayo sintético completo por API. La cuenta de prueba fue borrada
y su credencial revocada. No volver a solicitar esta activación, reimplementar el
incremento ni repetir sus pruebas sin una razón concreta.

## Incremento de comprobación activo

`resource_forecast_v1` congela una estimación, su base, contexto, tolerancia y
cantidad prevista (3..30) antes de aceptar observaciones en peticiones posteriores.
Registra fecha del servidor y fecha declarada, encadena recibos inmutables y cierra
el informe al completar la cantidad prevista. No reajusta la predicción. Un informe
completo permite una nueva calibración mediante `forecast_mission_id`, usando los
registros ya puntuados como aprendizaje y otros posteriores como comprobación.

Contrato: [PROSPECTIVE_VALIDATION.md](../beta/docs/PROSPECTIVE_VALIDATION.md).
Migración aditiva 009, recuperación cifrada y borrado por cascada comprobados.
129 pruebas locales pasan, incluidas 9 nuevas; evidencia en
[evidence/2026-10-15-prospective](evidence/2026-10-15-prospective).
El hash del código de puntuación queda congelado; un cambio bloquea nuevas
observaciones hasta revisión, conservando lectura, exportación y borrado.

`beta/deploy/prospective_probe.py` comprobó por API la secuencia congelar -> recibir
tres registros -> cerrar informe -> aprender en otra misión. La estimación 100
quedó fija antes de recibir 110, 115 y 120. El error absoluto total bajó de 195
(base 50) a 45; el informe correctamente devolvió `NO_CONFIRMED_IMPROVEMENT` porque
la máxima subestimación 20 superó la tolerancia 10. La misión hija reutilizó esos
registros ya puntuados como aprendizaje y otros posteriores para comprobar una
nueva estimación 115, conservando los hashes de procedencia y el informe anterior.

Coinciden los hashes del código servido y local; se comprobaron entrega, congelación,
recibos, cadena temporal e informe. La cuenta sintética fue borrada, su credencial
devolvió HTTP 401 y el estado privado fue reemplazado por un recibo sin secretos.
El ensayo usa datos sintéticos; no certifica sensores ni un beneficio real para la vida.

## Servicio y versiones

- URL: https://geniusdecision.app
- Implementación de aprendizaje: https://github.com/pedrosalvadeo/genius-decision-open/pull/28
- Comprobación prospectiva: https://github.com/pedrosalvadeo/genius-decision-open/pull/31
- Pin configurado y metadatos del despliegue coinciden:
  `2de2b7b0a1a885b62d7eb6597ea3b2d74741e90f`.
- Railway: despliegue `1d736e8d-65a0-4abf-9d96-f1f0b23b2e99`, `SUCCESS`.
- Creado `2026-10-15T03:32:07.033Z`, exitoso `03:32:37.058Z`.
- CI del PR 31 aprobado en `d9454ba0ab8db1e35bcb2d142b58f98ce2488aef`:
  Club 38675859990, recuperación 38675859984 y cápsula 38675860002.
  El merge conserva el árbol probado `448b73f291d653f44b2cc97f1f7f7b9c4bbc2d51`.
- Proyecto `a93aa08c-f3b6-4a5b-accc-9812d6314f00`, entorno
  `1addd5b8-5a47-4301-aeca-d9596bceb4e0`, servicio
  `dafd0be5-61aa-4843-a3a3-3c1f487d9640`.
- Sin cambios pendientes; volumen existente de 500 MB en `/data`, una réplica.
- Salud y respaldo `ok`, servicio no suspendido. Capacidades de aprendizaje
  y comprobación confirmadas por la API autenticada y ejecución real.

El conector había cancelado `accept_deploy` indicando falta de aprobación; Pedro
lo resolvió aplicando el cambio en el panel. Es un bloqueo histórico resuelto,
no una autorización pendiente. Esta edición de evidencia no modifica el runtime.

## Capacidades implementadas

Misiones privadas por cuenta mediante REST y MCP `mission_*`, con seis etapas
persistentes: medir, representar, evaluar, actuar, observar, recordar. El worker
conserva cada etapa antes de avanzar; entradas, evidencia y entregas forman parte
de la base principal y sus respaldos cifrados. Hay permisos por operación,
idempotencia, cancelación, retención, borrado y revisión ante cambios del runtime.

1. `source_distribution_v1`: archivos UTF-8 enviados; mide TAR/gzip/ZIP, compara
   mediante el núcleo, entrega el menor archivo íntegro y registra sus mediciones.
   La CLI original también admite un commit Git explícito.
2. `resource_calibration_v1`: propone una mediana inferior usando sólo registros
   de aprendizaje. Compara errores de la base y propuesta en registros posteriores
   de comprobación con el núcleo nativo. Adopta sólo si el error total baja,
   la máxima subestimación no empeora y cumple la tolerancia declarada.
   Si no, conserva la base; conservarla no certifica que sea adecuada.
3. `resource_forecast_v1`: congela una entrega completada y puntúa observaciones
   recibidas después, sin modificar la predicción ni el informe cerrado. Usa
   puntuación aritmética fija; la calibración posterior sigue usando el núcleo nativo.

La entrega privada `resource-estimate.json` conserva la estimación y su evidencia.
Otro ciclo puede heredar la estimación de una misión propia completada por
`parent_mission_id`, con iguales contexto/recurso/unidad/tipo de datos y registros
más nuevos. Guarda hash e identidad del padre, sin copiar recursivamente su historial.
Es una actualización acotada de un parámetro; no reescribe código ni actúa sobre
el mundo físico. Reutiliza infraestructura, dependencias y migración 008 existentes.

Contratos: [ADAPTIVE_MISSIONS.md](../beta/docs/ADAPTIVE_MISSIONS.md) y
[RESOURCE_CALIBRATION.md](../beta/docs/RESOURCE_CALIBRATION.md).
Guía: https://geniusdecision.app/static/missions.html.
Ejemplo: [resource-calibration.json](examples/resource-calibration.json).

## Evidencia recibida

[2026-10-15-prospective](evidence/2026-10-15-prospective) conserva las 129 pruebas
locales, identidades de CI/despliegue, salud y recibo completo del ensayo en vivo.
Incluye fechas del servidor, cadena de hashes, resultado negativo de la guarda,
nueva estimación 115 y confirmación de borrado/revocación. No hubo reinicio adicional
durante el ensayo. Las pruebas anteriores permanecen como evidencia histórica.

[2026-10-15-learning](evidence/2026-10-15-learning) contiene código de la prueba,
recibos públicos sin credenciales, comparación de fuentes y resultados:

- 120 pruebas locales de servicio/privacidad/recuperación y 24 adaptativas.
- CI del PR 28 en `6ec2cd54082d393e5bf4368bfe53d0ac080fc729`: servicio Docker
  sin red (112 pruebas), recuperación adaptativa y cápsula correctos.
- Dos ciclos sintéticos ejecutados en producción, seis etapas y un intento cada uno.
  Primer ciclo: base 50 -> estimación 100, error absoluto total 105 -> 5.
  Segundo: heredó 100 y el hash del padre -> estimación 115, error 35 -> 5.
  Resultados nativos verificados y hashes de las entregas comprobados.
- Solicitar otra ejecución reutilizó ambos resultados completados.
- Cuenta sintética eliminada y credencial revocada (401); estado privado reemplazado
  por recibo sin secretos. No hay una credencial de prueba pendiente de limpieza.

La prueba actual no reinició el servicio. La prueba previa de distribución,
con reinicio ordenado y conservación de la misión/exportación/archivo, está en
[evidence/2026-10-15-live](evidence/2026-10-15-live). Cortes forzados y restauración
con protección de borrados fueron probados separadamente de manera aislada.
La captura original de 460 archivos permanece en [2026-10-14](evidence/2026-10-14).

## Pendiente real

El siguiente avance requiere una fuente real autorizada con contexto, unidad,
procedencia y criterios de evaluación explícitos. Ninguna fuente real se eligió o
conectó en este ensayo. La procedencia y las fechas de evento siguen siendo
declaraciones; el servidor comprueba el orden de recepción. Los casos son sintéticos;
no demuestran generalización futura, ahorro de agua, bienestar ni probabilidad de
vida sostenida. No se necesita un proveedor LLM para el siguiente avance.

El incremento activo separa temporalmente recepción y puntuación. No identifica observaciones
copiadas manualmente a otras solicitudes, no certifica relojes externos ni evita
que un remitente seleccione u omita datos. La ruta de reutilización del informe
sólo se habilita tras completarlo. La calibración hija conserva sus propias
limitaciones retrospectivas hasta congelar y comprobar su estimación por separado.

Defecto heredado separado: adaptadores FDQ apuntan a `beta/vendor/R0` y `R1`, ausentes.
La selección histórica de 23 pruebas tuvo 5 fallos y 2 errores `PR_DEPENDENCY`.
No se inventaron esas fuentes ni se relajaron sus hashes; las misiones usan el
gemelo y núcleo públicos presentes. Recuperar versiones exactas sigue pendiente.

## Siguiente prompt

> Continuá desde `adaptive/HANDOFF.md` y `adaptive/evidence/2026-10-15-prospective`.
> El aprendizaje del PR 28 y la comprobación `resource_forecast_v1` del PR 31 están
> activos y verificados en producción. El ensayo sintético pasó: predicción fija,
> recepción posterior, guarda de tolerancia, informe inmutable, nuevo aprendizaje
> y borrado/revocación. No repitas ese desarrollo, despliegue ni ensayo cerrado.
> Avanzá hacia la entrada de observaciones de una fuente real autorizada
> con contexto, unidad y procedencia explícitos. Diferenciá el orden de recepción
> comprobado de la veracidad independiente del evento y de efectos de bienestar/PVS.
> Conservá permisos, recuperación y evidencia en Git y entregá el siguiente prompt.
