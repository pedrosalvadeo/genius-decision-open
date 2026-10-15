# Genius adaptativo — primer ciclo de observación HTTP real completado

Último ciclo completado el 15 de octubre de 2026 a las 04:07 UTC (01:07 en Argentina).
El servicio del PR 31 sigue activo. Un nuevo observador cliente ejecutó el ciclo
completo con 16 mediciones reales de latencia HTTP. El protocolo pasó; **no hubo
mejora predictiva confirmada**. La cuenta dedicada fue borrada y la credencial
revocada y retirada del estado privado. No repetir este ensayo para buscar un
resultado favorable ni volver a pedir la activación de Railway ya resuelta.

## Observador real incorporado

Código y contrato en [observers/README.md](observers/README.md); evidencia completa
en [evidence/2026-10-15-real-http](evidence/2026-10-15-real-http). Funciona bajo
demanda desde un cliente operador usando la API desplegada: no instala un colector
permanente, no cambia el runtime del servicio y no requiere otro Apply.

Mide el tiempo de `GET /api/health` visto desde este entorno, incluyendo red/proxy,
conexión, lectura y validación local de respuesta. La primera medición separada
aportó base 7835 ms; cinco observaciones entrenaron y tres posteriores comprobaron
una propuesta 7886 ms. Su error fue mayor (1278 frente a 1227), por lo que se
conservó la base. Después de congelarla, cinco mediciones nuevas produjeron error
total 4605 para ambas predicciones, con informe `NO_CONFIRMED_IMPROVEMENT`.
La misión hija propuso 6741 ms usando esos cinco registros ya puntuados; en dos
mediciones nuevas tuvo error 2882 frente a 694 y subestimación máxima 1771, fuera
de la tolerancia 1000. También conservó 7835 ms. No afirmar que el ensayo mejoró
latencia o que esa base sea óptima en general.

El cliente conserva cada intento antes de medir y el resultado antes de enviarlo;
reenviar una observación recibida reusa su ID. Una muestra fallida o incierta no
se sustituye. Se comprobaron recuperación tras perder una respuesta, hashes de
fuente y normalización, cadena temporal, cálculo fijo, procedencia hija, informe
anterior intacto y limpieza. Los resultados desconocidos de alta o borrado tienen
límites explícitos de recuperación. El estado privado nunca se publica.

## Comprobación del PR 31: ensayo sintético previo

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

[2026-10-15-real-http](evidence/2026-10-15-real-http) añade el ensayo real descrito
arriba. Los logs locales y el resumen distinguen pruebas superpuestas; el PR de
`work/real-observer-20261015` conserva CI del código final y su integración.
La evidencia del observador no acredita un sensor independiente ni impacto vital.

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

Ya se usó una fuente real: latencia del propio servicio desde un observador. Sigue
pendiente conectar fuentes pertinentes a condiciones de vida y casos reales de
consumidores, con contexto, unidad, procedencia y criterios explícitos. Las fechas
de evento y procedencia son declaraciones; el servidor comprueba el orden de
recepción. La nueva evidencia operacional no demuestra generalización, ahorro de
agua, bienestar ni probabilidad de vida sostenida. Tampoco prueba que la propuesta
de mediana sea adecuada para la variación temporal observada. No se necesita un
proveedor LLM para continuar con observaciones y comparación de estrategias.

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

> Continuá desde `adaptive/HANDOFF.md`, `adaptive/observers/README.md` y la evidencia
> `2026-10-15-real-http`. El servicio y los ciclos sintéticos previos ya están
> verificados. El nuevo ciclo con 16 mediciones HTTP reales completó el protocolo,
> rechazó dos propuestas peores y conservó la base; cuenta borrada y token revocado.
> No repitas ese ensayo ni pidas otro Apply: el observador usa el servicio existente.
> Avanzá en contexto observable y estrategias adaptativas que puedan contrastarse
> con datos posteriores, y en fuentes reales pertinentes a bienestar/condiciones
> de vida cuando haya datos autorizados adecuados. Elegí el siguiente incremento
> según las dependencias efectivas, sin convertir la espera de datos en un bloqueo
> de ingeniería. Fijá el plan antes de observar, conservá resultados negativos y no
> ajustes tolerancias para aprobar datos ya vistos. Diferenciá medición del cliente,
> verdad de la fuente y efectos causales. Conservá pruebas, evidencia y recuperación
> en Git y entregá el siguiente prompt junto con el resultado.
