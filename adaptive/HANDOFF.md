# Genius adaptativo — aprendizaje activado y comprobado

Estado comprobado el 15 de octubre de 2026 UTC (14 por la noche en Argentina).
El usuario aplicó el cambio en Railway. La calibración de recursos está activa y
la prueba de continuidad por API pasó. No volver a solicitar aquella activación,
reimplementar este incremento ni repetir sus pruebas sin una razón concreta.

## Incremento de comprobación preparado en esta edición

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

El estado de producción debajo corresponde a la calibración del PR 28, **antes de
activar este nuevo incremento**. Consultar el PR de la rama
`work/prospective-validation-20261015` para CI, commit y resultado de despliegue.
No darlo por activo sólo por estar mergeado. Si `accept_deploy` vuelve a cancelarse,
dejar el cambio concreto preparado en el panel, sin intentar otra vía de escritura.

Una vez desplegado, `beta/deploy/prospective_probe.py` permite comprobar por API
la secuencia congelar -> recibir tres registros -> cerrar informe -> aprender en
otra misión. Argumentos: ruta privada nueva para estado temporal, ruta pública de
recibo y `adaptive/examples/resource-calibration.json`. Crea y borra una cuenta
sintética. Compara hashes del código servido, recibos y entregas; nunca publica su
credencial. Este ensayo no certifica sensores ni un beneficio real para la vida.

## Servicio y versiones

- URL: https://geniusdecision.app
- Implementación de aprendizaje: https://github.com/pedrosalvadeo/genius-decision-open/pull/28
- Pin configurado: `c2aa351b05a5e6857435df86a50bf63682b0f3f6`.
- Railway: despliegue `7a88246f-ca8c-4de4-85b8-6c5676e9360b`, `SUCCESS`.
- Creado `2026-10-15T02:40:47.291Z`, exitoso `02:41:32.700Z`.
- Metadatos de despliegue: `93f5be90080db58e821a88581473f8b6a89c6dc8`.
  El pin configurado y los metadatos del proveedor difieren. Se conservaron ambos:
  todos los archivos copiados en la imagen tienen los mismos objetos Git; entre
  esos commits sólo cambiaron metadatos de publicación y registros de revisión.
  No afirmar una identidad única del repositorio completo sin resolver esa diferencia.
- Proyecto `a93aa08c-f3b6-4a5b-accc-9812d6314f00`, entorno
  `1addd5b8-5a47-4301-aeca-d9596bceb4e0`, servicio
  `dafd0be5-61aa-4843-a3a3-3c1f487d9640`.
- Sin cambios pendientes; volumen existente de 500 MB en `/data`, una réplica.
- Salud y respaldo `ok`, servicio no suspendido. Capacidades de aprendizaje
  confirmadas por la API autenticada y ejecución real.

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

La validación actual es retrospectiva: las dos particiones se envían juntas.
La procedencia y fechas son declaraciones, sin certificación de sensores.
Los casos de esta prueba son sintéticos; no demuestran generalización futura,
ahorro de agua, bienestar ni probabilidad de vida sostenida. No se necesita un
proveedor LLM para el siguiente avance.

El incremento preparado implementa la separación temporal de recepción y puntuación.
Aún queda comprobarlo en producción tras activarlo. No identifica observaciones
copiadas manualmente a otras solicitudes, no certifica relojes externos ni evita
que un remitente seleccione u omita datos. La ruta de reutilización del informe
sólo se habilita tras completarlo. La calibración hija conserva sus propias
limitaciones retrospectivas hasta congelar y comprobar su estimación por separado.

Defecto heredado separado: adaptadores FDQ apuntan a `beta/vendor/R0` y `R1`, ausentes.
La selección histórica de 23 pruebas tuvo 5 fallos y 2 errores `PR_DEPENDENCY`.
No se inventaron esas fuentes ni se relajaron sus hashes; las misiones usan el
gemelo y núcleo públicos presentes. Recuperar versiones exactas sigue pendiente.

## Siguiente prompt

> Continuá desde `adaptive/HANDOFF.md` y el PR de `work/prospective-validation-20261015`.
> El aprendizaje del PR 28 ya está activo y verificado; la nueva comprobación
> `resource_forecast_v1` está implementada y probada. Primero confirmá si se aplicó
> el despliegue preparado. Cuando esté activo, ejecutá el ensayo sintético de
> `beta/deploy/prospective_probe.py`, comprobá hashes y secuencia temporal, informe
> inmutable, aprendizaje posterior y borrado de la cuenta. No repitas el desarrollo.
> Después, avanzá hacia la entrada de observaciones de una fuente real autorizada
> con contexto, unidad y procedencia explícitos. Diferenciá el orden de recepción
> comprobado de la veracidad independiente del evento y de efectos de bienestar/PVS.
> Conservá permisos, recuperación y evidencia en Git y entregá el siguiente prompt.
