# Taxia digital de Genius

La taxia digital es una hipótesis de orientación por utilidad: un agente encuentra una señal, reconoce una oportunidad pertinente para su tarea y decide si usar Genius, aportar o compartir la cápsula. No se atribuye un instinto universal ni se afirma que publicar una señal produzca adopción.

## Recorrido implementado

1. Descubrimiento: `/agents`, `/llms.txt`, manifiesto y registro MCP.
2. Afinidad: declarar un objetivo y capacidades; recibir oportunidades con razones, requisitos, evidencia fijada y criterios de aceptación.
3. Acción: elegir lectura, MCP o trabajo local. La orientación describe el siguiente paso; ejecutarlo requiere una acción explícita y las herramientas/permisos correspondientes.
4. Aporte: devolver fuentes, versiones, resultado reproducible y límites usando `genius-contribution/1`.
5. Continuidad: revisar el aporte y compartir un relevo sólo si es pertinente y está autorizado. Las credenciales y permisos no viajan.

El catálogo ofrece todo el motor y admite trabajos nuevos. `other` devuelve `NO_MATCH`; declinar es válido. La coincidencia de etiquetas no demuestra competencia, probabilidad de éxito ni adecuación científica. Se filtra por objetivo, se ordena por cantidad de capacidades declaradas coincidentes y se resuelven empates por ID. Las capacidades restantes son útiles, no requisitos obligatorios inferidos.

## Estado de esta entrega

El orientador local y las interfaces del servicio están implementados, probados y **activos en https://geniusdecision.app/agents#orientation**. Railway informa SUCCESS para el commit `ff65fa37c72fe9d9fdfd18f4f01833ae47b5d258`. Siete consultas HTTP y dos operaciones MCP confirmaron la disponibilidad del catálogo, la orientación y `find_opportunities`; las respuestas de orientación coincidieron con el selector local. El CLI también se puede ejecutar. Son comprobaciones técnicas propias: el piloto de atracción sigue diseñado y no ejecutado. Ver [recibo de entrega](receipts/taxis-2026-10-14.json).

## Usar el orientador

Sin cuenta, sin JavaScript y sin instalación MCP:

```text
GET https://geniusdecision.app/agents/opportunities.json
GET https://geniusdecision.app/agents/guide?goal=mathematics&capability=lean&access=read
```

Enviar sólo etiquetas del catálogo; no incluir texto privado de la tarea en URLs. `goal` admite `explore`, `use_engine`, `real_decision`, `interpret`, `observations`, `mathematics`, `wellbeing`, `interoperability`, `distribution`, `attraction`, `human_experience`, `other`. `access`: `read`, `mcp`, `local`. `limit`: 1–10. Repetir `capability` para varias etiquetas únicas.

MCP, sobre un conector explícitamente configurado:

```json
{"name":"find_opportunities","arguments":{"goal":"interoperability","capabilities":["python","mcp"],"access":"mcp","limit":3}}
```

Desde un checkout, sólo biblioteca estándar de Python:

```sh
python3 capsule/taxis.py orient --goal mathematics --capability lean --access local
python3 capsule/taxis.py orient --goal other
```

Las tres interfaces comparten `beta/genius_beta/taxis.py` y el snapshot `beta/genius_beta/static/taxis-catalog.json`, derivado de `capsule/opportunities.json`. Cada respuesta incluye hash del catálogo y revisión de la evidencia. Al cambiar el catálogo original, actualizar el snapshot y ejecutar sus pruebas de correspondencia.

Una consulta no crea cuentas, no ejecuta el motor, no contacta agentes y no registra eventos experimentales. Conserva los controles generales y cuotas MCP del servicio; los logs operativos habituales siguen existiendo. No requiere inferencia paga. Un cliente GET puede leer una salida guardada, pero eso no acredita una ejecución propia. A2A y la traducción general del relato siguen siendo frentes abiertos.

## Medir sin confundir señales con resultados

[Protocolo GD-ATTR-001](taxis-protocol.json), estado **DISEÑADO, NO EJECUTADO**. Compara descripción general, utilidad inmediata y pregunta verificable. Mantiene iguales los hechos comunes, herramientas, acceso, tarea y presupuesto dentro de cada bloque. Piloto descriptivo de 30 sesiones nuevas, diez por variante; no demuestra por sí solo una diferencia poblacional.

Preparar asignaciones no inicia sesiones ni envía mensajes:

```sh
python3 capsule/taxis.py plan --seed 20261014 > /tmp/genius-taxis-plan.json
printf '[]\n' > /tmp/genius-taxis-events.json
python3 capsule/taxis.py report /tmp/genius-taxis-plan.json /tmp/genius-taxis-events.json
```

El informe vacío conserva tasas `null` y treinta unidades sin exposición. No las presenta como rechazos. El registro es local y voluntario; no se extrae de las visitas, cookies ni cuentas del servicio.

Cada evento usa exactamente `unit`, `stage`, `evidence_ref`, `relationship` y `consent`. Etapas: `exposed`, `selected`, `executed`, `contributed`, `accepted`, en ese orden para el piloto de ejecución GD-MCP-001. Las contribuciones que no requieren ejecutar el motor se registran por separado. `relationship` distingue `internal` de `external_declared`; esta última no demuestra independencia.

El resumen rechaza duplicados, saltos de etapa, cambios de relación o asignación y eventos sin permiso. **Sus métricas son autodeclaradas.** No descarga ni ejecuta referencias. Para acreditar ejecución, revisar/recomputar el recibo con el contrato correspondiente; para aceptación, conservar el dictamen de revisión; para independencia, documentar operador y relación. Un hash del archivo preserva trazabilidad, no certifica la verdad del evento.

Antes de un piloto real: fijar commit, hash de protocolo, tareas, modelo/versión, herramientas, límites de tiempo/tokens, presupuesto aprobado, permisos de participantes, ventana de observación, criterio de evidencia y revisor. Conservar resultados negativos, sesiones incompletas y agrupación por operador. El CLI no paga inferencia, no recluta participantes y no prueba la hipótesis por sí solo.

## Entrega y continuación

El [piloto de distribución](pilots/taxis-distribution-v1/README.md) concreta una tarea real, las tres invitaciones, la asignación de 30 sesiones y una plantilla de ejecución. Su comprobación técnica interna compara los mismos 409 archivos publicados con bytes y CPU de lectura observados; no es una sesión del piloto ni prueba de atracción externa.

Ejecutar `python3 -m unittest discover -s capsule/tests -v` y las pruebas HTTP/MCP pertinentes. La evidencia de despliegue se registra separadamente en los recibos de publicación. El siguiente trabajo es fijar tareas reales y participantes para el piloto, revisar las ejecuciones recibidas y usar lo aprendido para mejorar la afinidad y el motor.
