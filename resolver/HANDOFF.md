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
