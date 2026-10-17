# Resolutor — 16 de octubre de 2026

Primera versión: descubrimiento de issues públicos, memoria versionada, reservas,
criterios fijados antes del trabajo, estados con recibos y reporte humano. El
razonamiento lo ejecuta el agente de Work; no se añadió un modelo o servicio en
Railway. La activación y el PR se verifican al finalizar esta entrega.

Primer ciclo: 20 necesidades públicas recogidas de dos muestras de diez resultados.
Se seleccionó Brambit #4. Paquete en `cases/brambit-4-plugin-guide/`: guía, ejemplo,
traducciones, cuatro pruebas de integración y parche. Validación contra una base
real fijada, sin credenciales ni cambios de producción. El kernel no se ejecutó.
No presentar el estado como resolución externa: la asignación, el CLA, el envío
y la adopción quedan pendientes. No ampliar el permiso de contacto del diplomático.

El paquete de memoria tiene 19 pruebas que cubren deduplicación, fuentes cambiadas
o antiguas, bloqueo concurrente, recuperación, criterios, límites del adaptador y
rechazo de declaraciones de éxito sin la secuencia de evidencias requerida.
Los recibos registran lo verificado por el operador; no certifican por sí mismos
la verdad de la fuente o la independencia de un tercero.

## Segundo ciclo: linux-vitals #149

Se trabajó sobre el registro existente, sin ampliar la muestra. La reserva se
publicó en `genius/resolver-linux-vitals-149` antes de preparar el parche.
`cases/linux-vitals-149-locale/` conserva el parche MIT, criterios, reproducción,
dependencias, arnés sin credenciales y con sockets IPv4/IPv6 bloqueados, y logs.
Antes de corregir: 25 fallos y 28 aprobadas. Después: 266 pruebas locales aprobadas;
las 53 nuevas se repitieron con éxito tras aplicar el parche en una copia limpia.
Estado SOLUTION_PREPARED; no se envió al proyecto ni se aplicó a equipos reales.
Faltan permiso para comentario/PR externos y los controles completos upstream
(incluidos Molecule y la matriz de versiones). No regenerar ni renotificar esta
entrega como nueva. Los fixtures de sondas no equivalen a un host traducido real;
la limitación de los catálogos util-linux está documentada. Kernel no ejecutado.

Rez #2089 queda BLOCKED para evitar duplicar sus PR abiertos #2098/#2222.
Backlot #593 queda NEEDS_INFORMATION: evitar el error 500 no acredita fidelidad
de colación con Drive. Ambos triajes tienen evidencia en `cases/`. Brambit
permanece preparado y pendiente de los mismos pasos externos. Priorizar las
otras tareas detectadas; releer reservas y ramas antes de comenzar.

## Tercer ciclo: Sotto #612

Se atendió otra tarea existente sin ampliar la muestra. Reserva publicada en
`genius/resolver-sotto-612` antes de editar; criterios conservados en el ledger.
`cases/sotto-612-secret-removal/` incluye un parche Apache-2.0 para los cinco README,
guía de aplicación, borrador externo no enviado y evidencia. Siete controles del
caso y trece pruebas del verificador upstream aprobados; los siete se repitieron
tras aplicar el parche en copia limpia. Antes faltaba la sección: seis controles
fallaban y uno pasaba. Las afirmaciones se contrastaron con Rust fijado, no con
ejecución del CLI. No se borraron secretos ni se ejecutó login o sincronización.

Estado SOLUTION_PREPARED, no APPLIED ni VERIFIED. Faltan permiso para PR externo
y decisión del contribuyente sobre el DCO exigido por Sotto; no se firmó nada.
Releer la fuente y los PR documentales antes de presentar. No regenerar ni
renotificar esta entrega como novedad. Kernel no ejecutado: no hay una
representación justificada para esta corrección documental. No se midieron CAG,
PVS ni bienestar. El historial previo y los otros agentes no se modificaron.

## Cuarto ciclo: Soup #1186, sólo ítem 1

Se preparó en copia el rechazo al cargar `task: distill` con `modality: vision`
o `audio`; ambos modos de destilación actuales procesan texto. El defecto del
título (backend unsloth) ya era de #1193, y el ítem 3 de #1746/#1782: no atribuirlos
a Genius. El ítem 2 (SFT/unsloth con visión/audio) continúa pendiente y separado.
El hilo vigente confirma que los ítems 1 y 2 están libres; Soup exige comentar un
plan antes de reclamar públicamente. No se envió comentario ni PR externo.

Reserva interna publicada antes de implementar en `genius/resolver-soup-1186-modality`.
Paquete Apache-2.0 con NOTICE en `cases/soup-1186-distill-modality/`. Antes del
cambio: 16 fallos y 9 aprobadas. Regresión final: 129 aprobadas, incluidas 29
nuevas y cuatro invocaciones reales de doctor --config. Al retirar sólo el
rechazo nuevo: 20 fallos; restaurado: 29 aprobadas. Parche comprobado en copia
limpia, Ruff completo aprobado. Inventario de 205 configs sin combinación afectada.
Pruebas sin credenciales y sin sockets IPv4/IPv6; no se entrenó ni descargó modelos.
Suite completa y matriz upstream pendientes. Python 3.12.14, sólo dependencias core.

Estado SOLUTION_PREPARED únicamente para ese ítem, sin aplicación ni adopción.
Próximo paso externo: permiso para comentario de reserva y PR, coordinación con
el mantenedor y controles upstream. No requiere CLA/DCO según CONTRIBUTING leído;
no se aceptaron términos en nombre del usuario. Kernel no ejecutado por no existir
una representación justificada. No regenerar esta entrega ni contar el issue
agregado como resuelto. El historial y las entregas anteriores se conservaron.

## Quinto ciclo: MemWhale #423

Se prepararon cinco secciones breves sobre notas de recuperación: texto idéntico
en Claude Code, Cursor, Codex y Gemini; Rho explícitamente no recibe notas.
Se distingue candidato de confirmación en dos o más episodios, procedencia y
almacén local; el historial no demuestra causalidad. Sin cambios de comandos,
limitaciones ni estado de verificación en vivo. Paquete MIT y parche en
`cases/memwhale-423-recall-guide/`, con reserva publicada antes de editar.

Nueve controles estáticos aprobados y repetidos tras aplicar el parche en copia
limpia. Antes fallaban cinco métodos (18 subcomprobaciones); cuatro pasaban.
Rust y release notes fijados se revisaron, no se ejecutó MemWhale. Tests con
Python 3.12.3 sin credenciales ni sockets IPv4/IPv6. No se instalaron dependencias
ni se abrieron bases de datos personales. Suites completas y clientes en vivo
no comprobados; no confundir coherencia documental con prueba de funcionamiento.

SOLUTION_PREPARED, sin envío ni adopción. Falta permiso para comentar #423 y
enviar PR externo: CONTRIBUTING/#317 exigen coordinación antes de reclamar.
El borrador está listo; releer disponibilidad antes de enviarlo. No CLA/DCO
exigido en la versión leída; no se aceptaron contratos. Kernel no ejecutado,
sin representación justificada ni CAG/PVS/bienestar medidos. No regenerar ni
renotificar esta entrega; avanzar los otros pendientes del registro.

## Siguiente encargo

> Continuá el agente explorador y resolutor desde resolver/AGENT.md, ledger.json,
> REPORT.md y los PR actuales de pedrosalvadeo/genius-decision-open. Comprobá la
> activación real de la tarea y reanudá sólo trabajo pendiente. La primera solución
> está preparada para Brambit #4 y no debe regenerarse ni contarse como adoptada.
> Buscá otra necesidad pública útil y abordable, leé reglas y evidencia, reservá
> el problema y fijá criterios antes de trabajar. Usá Genius cuando haya un modelo
> válido; no fuerces su cálculo ni inventes bienestar o PVS. Entregá una solución
> comprobable, preservá memoria y manifest y comprobá integración por PR. No envíes
> mensajes externos ni aceptes contratos sin autorización específica. Distinguí
> preparación, aplicación y verificación posterior; informá sólo avances nuevos.
