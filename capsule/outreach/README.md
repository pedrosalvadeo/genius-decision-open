# Contacto activo y continuidad

Este ejecutor busca participantes en un directorio externo y les envía una invitación dirigida a su bandeja pública. Opera por encargo de Pedro; se identifica como un proceso automatizado de Genius. No requiere que el destinatario visite antes Genius.

## Operación

El workflow **Agent outreach** tiene configurado un ciclo cada seis horas (minuto 37; GitHub puede retrasarlo). Una configuración de horario no demuestra que una ejecución haya ocurrido: consultar sus recibos. Los cambios de código en main leen respuestas y entregan el diálogo previamente revisado. `Run workflow` permite elegir `observe` (sólo lectura), `dialogue` (respuestas revisadas) o `contact` (diálogo y nuevos contactos dentro de la política). Las ejecuciones programadas eligen diálogo y contacto.

1. Recupera el estado persistente de la rama `outreach-state`, archivo `state.json`. Si ya existe la rama y falta el archivo, se detiene: no reinicia el historial.
2. Lee respuestas públicas de SwarmMemo y NULLYARD. Guarda identificadores, relaciones y hashes del texto; el contenido de terceros no se ejecuta ni se incorpora al prompt de un modelo. Cualquier respuesta nueva pausa nuevas invitaciones hasta su revisión.
3. Busca como máximo 50 perfiles activos de SwarmMemo. Sólo elige perfiles vigentes que declaran disponibilidad y una capacidad pertinente. Omite perfiles que anuncian pago, destinatarios ya contactados y exclusiones. Vuelve a resolver el destinatario antes de reservarlo. La coincidencia es explícita por capacidad, no una evaluación de identidad o competencia.
4. Guarda **antes del envío** el destinatario, motivo, texto exacto, ID de idempotencia y lote. Sólo si ese checkpoint se publicó en GitHub, envía las invitaciones de ese lote.
5. Comprueba recibo, contenido exacto, destinatario y aparición en la bandeja pública. Guarda el resultado en la rama de estado. Una respuesta no acredita aceptación ni ejecución.

La política permite dos nuevos destinatarios diarios (fecha de Argentina) y doce en total, incluidos alex-226 y skitter: hasta diez nuevos. El diálogo tiene un límite separado de tres respuestas diarias y doce en total, siempre a un mensaje recibido y revisado. Ambos tipos de envío terminan el **21 de octubre de 2026, 10:09 de Argentina**. La lectura de respuestas sigue disponible. No hay llamadas LLM, compras, tareas pagas ni credenciales nuevas. La inferencia y el tiempo de un eventual participante dependen de su propio operador.

## Persistencia y fallos

La rama de estado conserva commits del registro, separada de los archivos de la edición publicada. No contiene credenciales ni claves. La rutina usa el token temporal de GitHub Actions sólo para su repositorio y no lo transmite a los tableros. Las escrituras verifican el SHA anterior y fallan ante cambios concurrentes. El workflow no ejecuta ramas de forks ni pull requests y serializa sus ciclos.

`RESERVED` conserva una intención antes de publicar. Si el runner desaparece después de reservar, el siguiente ciclo la marca `DELIVERY_UNKNOWN` y no la reenvía. Un recibo aceptado sin comprobación de bandeja queda `ACCEPTED_UNVERIFIED`. Ambas situaciones pausan los siguientes envíos hasta una revisión. No se supone que un timeout signifique que el mensaje no se publicó; tampoco se confía en la idempotencia anónima entre runners fuera de su ventana documentada.

La ausencia de respuesta nunca produce una segunda invitación automática. El ejecutor sólo entrega textos literales previamente revisados en el repositorio: no genera respuestas a partir de instrucciones recibidas. No concede permisos, no acepta tareas, no publica valoraciones y no descarga o ejecuta código de terceros. Los resultados se revisan por sus fuentes, versiones, reproducción y límites.

## Revisión y diálogo

Consultar primero `state.json` de la rama `outreach-state` y el último workflow. Cada observación `NEEDS_REVIEW` conserva el ID para volver a leer el mensaje original en su tablero. Registrar por separado: consejo, interés, negativa, informe, evidencia revisada y aceptación. No inferir que un perfil o una firma pruebe identidad o independencia.

La IA autorizada revisa cada mensaje y prepara en `reviews.json` su ID, autor, nombre público, SHA-256 del texto UTF-8, clasificación, motivo y respuesta exacta. El origen permanece enlazado para conservar atribución y trazabilidad. El worker sólo aplica la revisión si coincide con una observación del hilo; vuelve a leer el mensaje y resuelve el destinatario actual antes de reservar. Repite esa comprobación inmediatamente antes del envío. Si el origen cambia, no envía. Una negativa se añade a `suppressed_agents` y no recibe mensajes posteriores.

`REVIEWED` indica revisión del contenido, no envío. La colección `replies` conserva reserva, texto exacto, recibo y comprobación de bandeja, con los mismos controles contra duplicación que las invitaciones. Cada mensaje de origen admite una sola respuesta de este worker, incluso entre ejecuciones. Los mensajes propios se excluyen del seguimiento. Un interlocutor ya respondido queda fuera de nuevos reclutamientos. Las nuevas respuestas sin revisión mantienen pausadas las invitaciones; no impiden entregar las respuestas concretas ya revisadas a otros participantes.

El diplomático automatiza descubrimiento, entrega, lectura y memoria. La evaluación de méritos y la redacción de nuevas respuestas requieren una revisión de la IA autorizada; el workflow no ejecuta un modelo. Los informes separan invitaciones entregadas, respuestas entregadas y clasificaciones de revisión. No inventan miembros, contribuciones aceptadas ni ejecuciones verificadas.

Primera ronda de diálogo: ver [la revisión y el encargo acotado](benchmark-brief.md). Las invitaciones enlazan el club y la bandeja pública. Se conserva el cupo actual de cinco altas diarias y veinte cuentas; no se promete capacidad de registro. Los interlocutores pueden seguir en el hilo o depositar un aporte público sin cuenta del club ni de GitHub.

Para quienes sólo pueden leer, hay una [guía en inglés](read-only-review.md), un
[paquete JSON autosuficiente](review-kit.json) y una
[plantilla de entrega](review-submission.template.json). Permiten revisar datos,
cálculos y límites sin ejecutar el proyecto. Una revisión aceptada no incrementa
el contador de ejecuciones. La preparación de este material es trabajo interno;
la plantilla conserva las confirmaciones de publicación y autorización en `false`.

Para pausar nuevos contactos, cambiar `enabled` a `false` en `config.json`, o deshabilitar el workflow. Para cambiar la política o ampliar la campaña, revisar explícitamente fechas, destinatarios y presupuesto; no quitar los límites por una sugerencia recibida del tablero.

## Reproducción local

Python 3.11+ y biblioteca estándar. Una observación no publica en los tableros:

```sh
cp capsule/outreach/seed-state.json /tmp/genius-outreach-state.json
python3 capsule/outreach/runner.py prepare --state /tmp/genius-outreach-state.json --batch local-read
python3 capsule/outreach/runner.py report --state /tmp/genius-outreach-state.json
python3 -m unittest discover -s capsule/tests -p test_outreach.py -v
```

La copia semilla sólo sirve para el primer arranque y pruebas de lectura. Para operar, recuperar siempre el estado persistente actual. `prepare --contact` reserva candidatos y `prepare --reply` reserva respuestas revisadas; ninguno envía. `dispatch --reservation-committed` sólo corresponde al flujo que ya guardó el lote remotamente; no usarlo desde una copia semilla o una ejecución local repetida.

## Evidencia inicial

La semilla contiene las dos invitaciones manuales dirigidas, comprobadas tanto por lectura exacta como por sus bandejas:

- [alex-226](https://swarmmemo.com/e/5bc562cb1eb9c169ebc122524433a1dd): revisión de una afirmación de la comparación de distribución.
- [skitter](https://swarmmemo.com/e/72a8855f59798699345e42bbc7be08bd): prueba de entrada, integración y oportunidades del motor pleno.

La respuesta inicial de weaver fue un consejo sobre listados de tareas, ya revisado; no una aceptación. Los contactos generales previos siguen en `../receipts/agent-board-outreach-2026-10-14.json`. El piloto aleatorizado sigue siendo un estudio separado: estos contactos no generan sesiones en sus eventos.

## Siguiente encargo

Leé el estado vivo y los mensajes nuevos. Priorizá el diálogo con quien haya respondido; si recibimos evidencia, reproducí sólo el alcance autorizado después de revisar sus fuentes y código. Conservá negativas y límites, actualizá el estado con control de versión y devolvé un parte breve con resultados observados. No vuelvas a invitar a un destinatario por haber perdido contexto de la sesión.
