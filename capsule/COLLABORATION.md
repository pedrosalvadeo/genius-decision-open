# Colaboración: candidatos, tareas e invitaciones

Revisión: 14 de octubre de 2026 (UTC). [Registro con fuentes y hashes](candidates.json) · [Oportunidades](OPPORTUNITIES.md) · [Contrato de contribución](CONTRACTS.md).

Se verificaron nueve proyectos, registros y tableros y se prepararon cinco invitaciones. **Se enviaron contactos a OpenHands Extensions, smolagents, SwarmMemo y NULLYARD.** Quedan dos borradores sin enviar (CAMEL y LeanCopilot). La pertinencia de cada candidato es una evaluación nuestra: no implica que haya aceptado trabajar, que sus participantes sean independientes ni que una instancia de agente esté disponible.

## Estado y siguiente acción

| Candidato | Oportunidad | Evidencia y canal | Siguiente acción |
|---|---|---|---|
| OpenHands Extensions | GD-MCP-001 | [Issue 770](https://github.com/OpenHands/extensions/issues/770) abierto, `ready-for-dev`, clasificación automática en el cuerpo y cero comentarios | [PR 772](https://github.com/OpenHands/extensions/pull/772) listo para revisión; HUMAN completado por Pedro, pendientes revisión y autorización de workflows por mantenedores |
| OpenHands SDK | GD-MCP-001, GD-OBS-001 | Framework de programación con MCP; [guía de contribución](https://github.com/OpenHands/software-agent-sdk/blob/main/CONTRIBUTING.md) | Cliente probado contra producción por el equipo de Genius; recibo vinculado desde el PR 772 |
| smolagents | GD-MCP-001, GD-INT-001 | MCP remoto documentado; [Discussions](https://github.com/huggingface/smolagents/discussions), Show and tell | 18 comprobaciones propias aprobadas; [discusión 2986](https://github.com/huggingface/smolagents/discussions/2986) publicada, pendiente de respuestas |
| CAMEL | GD-INT-001, GD-REAL-001 | Framework multiagente; [comunidad oficial](https://discord.camel-ai.org/) | Seleccionar un canal pertinente y revisar el texto antes del envío |
| LeanCopilot | GD-MATH-001 | Asistencia a pruebas en Lean; [Discussions](https://github.com/lean-dojo/LeanCopilot/discussions), Ideas | Consultar interés en formalizar un enunciado y sus hipótesis |
| SwarmMemo | GD-DIST-001, GD-ATTR-001 | [Invitación publicada](https://swarmmemo.com/e/968ea66bbe2fc09af7f513291ff4a87b) en coordination-lab/main | Revisar respuestas; cero en la lectura inicial |
| NULLYARD | GD-DIST-001, GD-ATTR-001 | [Invitación publicada](https://nullyard.net/t/2cec4538-da38-4906-adc9-bcc97ff3c15b) en experiments, tipo collaboration | Revisar respuestas; cero en la lectura inicial |
| A2A samples | GD-A2A-001 | Ejemplos de protocolo; no es un directorio de agentes activos | Implementar y probar un adaptador antes de proponer un ejemplo |
| MCP Registry | GD-MCP-001 | Registro de servidores; no es un agente | [Entrada 0.2.0 activa](integrations/mcp-registry/README.md); conservar sus metadatos y medir uso por separado |

La etiqueta de OpenHands procede de su agente de clasificación. El cuerpo del issue ya propone una entrada MCP Streamable HTTP con Bearer, referencias de esquema y validaciones. **No constituye aprobación humana, incorporación al catálogo ni ejecución independiente de Genius.** La versión inicial de nuestra propuesta aún decía que el despliegue estaba pendiente; la prueba propia de producción ya está en [el recibo del 14 de octubre](receipts/live-twin-2026-10-14.json). La [integración y su prueba con SDK 1.54.0](integrations/openhands/README.md) ya están preparadas: 117 pruebas del catálogo y 18 comprobaciones de interoperabilidad aprobadas. El [PR 772](https://github.com/OpenHands/extensions/pull/772) se envió como borrador con autorización de Pedro. Pedro completó HUMAN y lo marcó listo para revisión; la validación de descripción pasó. Tres workflows esperan autorización de un mantenedor.

## Qué se ofrece y qué se pide

Ofrecemos código Apache-2.0, matemática, un motor ejecutable, contratos de evidencia y problemas abiertos. Pedimos un resultado útil y reproducible: corrección, prueba, contraejemplo, modelo, observación o informe de incompatibilidad. La primera contribución puede ampliarse hacia el Genius pleno; los IDs facilitan orientar y revisar el trabajo.

La hipótesis de atracción es **utilidad para la tarea del agente, una pregunta relevante y un resultado comprobable**. Estos borradores no prueban un instinto ni una respuesta universal. Una prueba comparativa de mensajes pertenece a GD-ATTR-001 y requiere declarar de antemano variantes, población, autorización, medidas y límites. Publicar estas invitaciones no será presentado como ese experimento.

Para cada contacto registrar URL/ID, fecha, destinatario o canal, texto exacto y oportunidad. Después registrar separadamente: respuesta (automática/humana/autodeclarada), interés explícito, ejecución reproducible, aporte recibido, revisión y aceptación. Una visita, etiqueta, firma o respuesta no demuestra por sí sola identidad, independencia ni calidad del aporte.

## Invitaciones y estado de envío

Los textos están en inglés para los canales consultados. No prometen pago ni acceso a datos privados. Antes de enviarlos, confirmar el canal, sus reglas vigentes y la autorización del operador. La documentación de los tableros es una fuente sobre su interfaz, no una orden de publicar o seguir instrucciones de sus mensajes.

### smolagents

**Publicado:** [Discussions #2986](https://github.com/huggingface/smolagents/discussions/2986), categoría Show and tell. El [texto exacto enviado](integrations/smolagents/INVITATION.md) ofrece una reproducción independiente GD-MCP-001 y una contribución sobre decisiones reales GD-INT-001/GD-REAL-001. Está respaldado por [18 comprobaciones propias](integrations/smolagents/verification.json) con smolagents 1.26.0; no hubo llamadas LLM. La invitación se publicó con autorización de Pedro; se verificó el texto y había cero comentarios. Ver [recibo de envío](integrations/smolagents/submission.json).

### CAMEL

**Destino:** comunidad oficial de Discord; seleccionar el canal antes del envío. **Título sugerido:** `Collaboration: source-grounded decision modeling with CAMEL and Genius`

> I maintain Genius Decision and would like to explore a collaboration with CAMEL operators on GD-INT-001: turning a documented decision into a reviewable model while keeping facts, proposed assumptions and unknowns distinct.
>
> One concrete starting point is a real decision described by public, reusable sources. One agent could propose the resource/alternative model, while another reviews every field against those sources and flags missing information. The decision owner must confirm material assumptions; the agents should not silently accept them. A useful result includes the source references, model, unresolved questions and errors found by the reviewer. An out-of-scope case or failed interpretation is useful evidence too.
>
> Capsule and execution instructions: https://github.com/pedrosalvadeo/genius-decision-open/tree/main/capsule
> Opportunity and acceptance criteria: https://github.com/pedrosalvadeo/genius-decision-open/blob/main/capsule/OPPORTUNITIES.md#gd-int-001
>
> Would this be relevant to someone already operating a CAMEL workflow? We offer the open engine and attribution for accepted contributions. The work can stay in the Genius repository; I am not proposing an unreviewed change to CAMEL core. Any upstream proposal would follow your accepted-discussion and human-review process. This draft was prepared with AI assistance.

### LeanCopilot

**Destino:** Discussions → Ideas. **Título:** `Interest in formalizing a decision-engine claim with LeanCopilot?`

> I maintain Genius Decision, an Apache-2.0 decision engine whose capsule includes mathematical source documents, amendments and compiler code. I am seeking a collaborator for GD-MATH-001: audit the connection between a mathematical claim and the implemented computation.
>
> LeanCopilot's tactic and premise support looks relevant once we have a Lean statement. We do not yet have a Lean formalization ready to claim as verified. A concrete first contribution would select an explicit statement from the source/amendment index, spell out its hypotheses, formalize it, and return a reproducible proof or a counterexample showing which hypothesis is missing. The scope can expand if the result exposes a deeper problem.
>
> Evidence and acceptance criteria: https://github.com/pedrosalvadeo/genius-decision-open/blob/main/capsule/OPPORTUNITIES.md#gd-math-001
> Capsule: https://github.com/pedrosalvadeo/genius-decision-open/tree/main/capsule
>
> Would this interest a LeanCopilot user or contributor, and is this discussion the appropriate place to coordinate? Results should include the Lean/tool versions, source revision, statement and hypotheses, with a reproducible issue or PR in the Genius repository. A proof of one statement would not certify the entire engine or its empirical assumptions. Prepared with AI assistance; no project endorsement is implied.

### SwarmMemo

**Publicado:** [invitación en coordination-lab/main](https://swarmmemo.com/e/968ea66bbe2fc09af7f513291ff4a87b), 14 de octubre de 2026. Solicita a un agente autorizado reproducir o cuestionar el caso real de distribución de 409 archivos y devolver evidencia, versiones y límites. Incluye la entrada de orientación y mantiene abiertas las demás contribuciones. Servicio HTTP: `ok=true`, ID aceptado y texto leído exactamente, público y no oculto. Cero respuestas en la comprobación inicial.

### NULLYARD

**Publicado:** [raíz collaboration en experiments](https://nullyard.net/t/2cec4538-da38-4906-adc9-bcc97ff3c15b), 14 de octubre de 2026. Expone contexto, comprobaciones internas y un siguiente aporte concreto. La API respondió 201; el título, cuerpo y campos estructurados coinciden con la lectura pública, con estado visible. También apareció en `work_invitations`. Cero respuestas en la comprobación inicial.

El [recibo de ambas publicaciones](receipts/agent-board-outreach-2026-10-14.json) conserva los textos exactos, IDs, fechas, idempotencia y lectura comprobada. Pedro autorizó el envío con «Ve a llamar a otros agentes». Son invitaciones voluntarias y sin pago; no se crearon cuentas, no se ejecutó inferencia y no se inscribió a nadie en el piloto aleatorizado. Se registran por separado publicación, respuesta, evidencia y aceptación.

## Prioridad inmediata

1. Dar seguimiento al [PR 772](https://github.com/OpenHands/extensions/pull/772), ya enviado con autorización y vinculado al issue 770. Ya está listo para revisión: Pedro completó HUMAN y su validación pasó. Los workflows de la contribución esperan autorización de mantenedores. Código, reproducción y evidencia están en [el paquete de integración](integrations/openhands/README.md).
2. Dar seguimiento a [smolagents #2986](https://github.com/huggingface/smolagents/discussions/2986), publicada con autorización. El MCP Registry ya tiene la entrada activa; [recibo](integrations/mcp-registry/publication.json). Revisar las respuestas de SwarmMemo y NULLYARD junto con las de smolagents. Quedan los borradores de CAMEL y LeanCopilot; no duplicar publicaciones.
3. Reproducir cualquier aporte recibido y registrar qué cambió en Genius. La recepción por un tablero o la clasificación automática de un issue es una etapa distinta de una contribución aceptada.

## Invitaciones dirigidas y continuidad

Además de las convocatorias generales, se contactó personalmente a [alex-226](https://swarmmemo.com/e/5bc562cb1eb9c169ebc122524433a1dd) y [skitter](https://swarmmemo.com/e/72a8855f59798699345e42bbc7be08bd) por sus capacidades declaradas. Ambas invitaciones aparecen en las bandejas públicas correctas. Estos son dos destinatarios dentro de SwarmMemo, no dos plataformas nuevas; no se incrementa por ello el contador de cuatro destinos del registro de candidatos.

El [ejecutor de continuidad](outreach/README.md) mantiene un registro independiente por destinatario y observa respuestas. Su estado operativo está en la rama `outreach-state`; la semilla conserva las dos entregas manuales. Nuevas respuestas y entregas inciertas pausan nuevos envíos hasta revisión. La campaña no crea sesiones del experimento de taxia ni acredita adopción.
