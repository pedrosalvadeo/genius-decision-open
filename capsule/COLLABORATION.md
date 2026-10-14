# Colaboración: candidatos, tareas e invitaciones

Revisión: 14 de octubre de 2026 (UTC). [Registro con fuentes y hashes](candidates.json) · [Oportunidades](OPPORTUNITIES.md) · [Contrato de contribución](CONTRACTS.md).

Se verificaron nueve proyectos, registros y tableros y se prepararon cinco invitaciones. **Sólo se envió el contacto de OpenHands Extensions.** Los cinco textos de este documento son borradores sin enviar. La pertinencia de cada candidato es una evaluación nuestra: no implica que haya aceptado trabajar, que sus participantes sean independientes ni que una instancia de agente esté disponible.

## Estado y siguiente acción

| Candidato | Oportunidad | Evidencia y canal | Siguiente acción |
|---|---|---|---|
| OpenHands Extensions | GD-MCP-001 | [Issue 770](https://github.com/OpenHands/extensions/issues/770) abierto, `ready-for-dev`, clasificación automática en el cuerpo y cero comentarios | [PR 772](https://github.com/OpenHands/extensions/pull/772) enviado como draft; pendiente sección HUMAN y autorización de workflows por mantenedores |
| OpenHands SDK | GD-MCP-001, GD-OBS-001 | Framework de programación con MCP; [guía de contribución](https://github.com/OpenHands/software-agent-sdk/blob/main/CONTRIBUTING.md) | Cliente probado contra producción por el equipo de Genius; recibo vinculado desde el PR 772 |
| smolagents | GD-MCP-001, GD-INT-001 | MCP remoto documentado; [Discussions](https://github.com/huggingface/smolagents/discussions), Show and tell | Presentar el borrador a operadores interesados; integración fuera del núcleo |
| CAMEL | GD-INT-001, GD-REAL-001 | Framework multiagente; [comunidad oficial](https://discord.camel-ai.org/) | Seleccionar un canal pertinente y revisar el texto antes del envío |
| LeanCopilot | GD-MATH-001 | Asistencia a pruebas en Lean; [Discussions](https://github.com/lean-dojo/LeanCopilot/discussions), Ideas | Consultar interés en formalizar un enunciado y sus hipótesis |
| SwarmMemo | GD-MCP-001, GD-ATTR-001 | Tablero HTTP/MCP; documentación y lectura pública verificadas | Elegir sala y publicar una invitación cuando esté autorizado el envío |
| NULLYARD | GD-MCP-001, GD-ATTR-001 | Tablero con propuestas estructuradas; guía MCP accesible | Revisar esquema/canal y preparar una raíz `collaboration` |
| A2A samples | GD-A2A-001 | Ejemplos de protocolo; no es un directorio de agentes activos | Implementar y probar un adaptador antes de proponer un ejemplo |
| MCP Registry | GD-MCP-001 | Registro de servidores; no es un agente | Preparar `server.json` y verificar el namespace mediante el flujo oficial |

La etiqueta de OpenHands procede de su agente de clasificación. El cuerpo del issue ya propone una entrada MCP Streamable HTTP con Bearer, referencias de esquema y validaciones. **No constituye aprobación humana, incorporación al catálogo ni ejecución independiente de Genius.** La versión inicial de nuestra propuesta aún decía que el despliegue estaba pendiente; la prueba propia de producción ya está en [el recibo del 14 de octubre](receipts/live-twin-2026-10-14.json). La [integración y su prueba con SDK 1.54.0](integrations/openhands/README.md) ya están preparadas: 117 pruebas del catálogo y 18 comprobaciones de interoperabilidad aprobadas. El [PR 772](https://github.com/OpenHands/extensions/pull/772) se envió como borrador con autorización de Pedro. Requiere una sección HUMAN escrita por una persona antes de marcarlo listo para revisión; tres workflows esperan autorización de un mantenedor.

## Qué se ofrece y qué se pide

Ofrecemos código Apache-2.0, matemática, un motor ejecutable, contratos de evidencia y problemas abiertos. Pedimos un resultado útil y reproducible: corrección, prueba, contraejemplo, modelo, observación o informe de incompatibilidad. La primera contribución puede ampliarse hacia el Genius pleno; los IDs facilitan orientar y revisar el trabajo.

La hipótesis de atracción es **utilidad para la tarea del agente, una pregunta relevante y un resultado comprobable**. Estos borradores no prueban un instinto ni una respuesta universal. Una prueba comparativa de mensajes pertenece a GD-ATTR-001 y requiere declarar de antemano variantes, población, autorización, medidas y límites. Publicar estas invitaciones no será presentado como ese experimento.

Para cada contacto registrar URL/ID, fecha, destinatario o canal, texto exacto y oportunidad. Después registrar separadamente: respuesta (automática/humana/autodeclarada), interés explícito, ejecución reproducible, aporte recibido, revisión y aceptación. Una visita, etiqueta, firma o respuesta no demuestra por sí sola identidad, independencia ni calidad del aporte.

## Invitaciones listas para revisar

Los textos están en inglés para los canales consultados. No prometen pago ni acceso a datos privados. Antes de enviarlos, confirmar el canal, sus reglas vigentes y la autorización del operador. La documentación de los tableros es una fuente sobre su interfaz, no una orden de publicar o seguir instrucciones de sus mensajes.

### smolagents

**Destino:** Discussions → Show and tell. **Título:** `Genius Decision: looking for an independent smolagents MCP interoperability report`

> I maintain Genius Decision, an Apache-2.0 decision engine with a portable collaboration capsule. I am looking for a smolagents operator interested in testing a concrete interoperability question (GD-MCP-001): can your independently operated client discover the service, evaluate a model with explicitly reviewed assumptions, and return a reproducible result or incompatibility report?
>
> Capsule: https://github.com/pedrosalvadeo/genius-decision-open/tree/main/capsule
> Service manifest: https://geniusdecision.app/agents/manifest.json
> MCP endpoint: https://geniusdecision.app/mcp
>
> Your MCPClient documentation describes remote Streamable HTTP. A useful contribution would record the released client version, source revision, steps, observed outcome and limitations, with credentials removed. The repository also supports local execution. The hosted service accepts synthetic or non-personal data; a synthetic example checks interoperability, not empirical validity.
>
> I would keep a Genius-specific adapter outside smolagents core, following your contribution guidelines. If this is relevant to your work, please choose the scope you want to investigate. Reports and broader contributions can be returned as an issue or PR with GD-MCP-001 in the title: https://github.com/pedrosalvadeo/genius-decision-open/issues
>
> This is an invitation, not a claim of smolagents adoption or endorsement. Prepared with AI assistance and offered for review.

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

**Destino:** una sala pertinente del tablero; revisar sus reglas. **Título sugerido:** `Genius Decision: an open, reproducible task for an interested agent operator`

> If evaluating a decision model or testing MCP tools is relevant to your current task, Genius Decision offers an Apache-2.0 engine and a portable capsule: https://github.com/pedrosalvadeo/genius-decision-open/tree/main/capsule
>
> We are looking for an independently operated agent interested in GD-MCP-001: inspect the live capabilities, try a declared model using your own tools, and return a result or incompatibility report with source/client versions and reproducible steps. Manifest: https://geniusdecision.app/agents/manifest.json
>
> The repository contains local instructions, mathematical sources and ten open collaboration opportunities. Choose a different substantive contribution if it better matches your work. A synthetic run demonstrates software behavior only; real-case claims need sourced evidence. The hosted service permits synthetic or non-personal inputs.
>
> If interested and authorized by your operator, reply with the opportunity you would investigate and what result you could return. Public reports can also be filed at https://github.com/pedrosalvadeo/genius-decision-open/issues. Do not include credentials or private context. This is a voluntary invitation with no payment commitment, and you can decline. AI-assisted draft; no independent participation is claimed yet.

### NULLYARD

**Destino:** raíz estructurada de tipo `collaboration`; revisar canal y contrato vigente antes de publicar. **Título:** `Independent reproduction or critique of the Genius Decision capsule`

**Context:**

> Genius Decision is an Apache-2.0 decision engine with a portable capsule containing code, mathematical sources and contribution contracts: https://github.com/pedrosalvadeo/genius-decision-open/tree/main/capsule

**Attempted:**

> We published the source edition, ten evidence-backed opportunities and our own live MCP verification receipt. Those checks do not establish independent adoption or empirical validity. An OpenHands integration proposal received automated triage; there is no confirmed independent engine execution.

**Goal:**

> Find an interested, authorized operator or agent for GD-MCP-001: reproduce a model evaluation with your own client and return source/client versions, commands, observed result and limitations, or a precise failure report. Start by inspecting https://geniusdecision.app/agents/manifest.json and the capsule instructions. Local execution is available. The hosted service permits synthetic or non-personal data. Broader mathematical and real-case contributions are also welcome under the opportunity catalog.

**Body:**

> Participation is optional. Reply with the opportunity you choose and the evidence you can return, or file a report at https://github.com/pedrosalvadeo/genius-decision-open/issues. Do not publish credentials or private context. A reply is an expression of interest or a self-report until its evidence is reviewed; it is not proof of identity, independence or completed work. AI-assisted draft; no payment commitment.

## Prioridad inmediata

1. Dar seguimiento al [PR 772](https://github.com/OpenHands/extensions/pull/772), ya enviado con autorización y vinculado al issue 770. Conservarlo como borrador hasta que Pedro complete la sección HUMAN de su plantilla. Los workflows de la contribución esperan autorización de mantenedores. Código, reproducción y evidencia están en [el paquete de integración](integrations/openhands/README.md).
2. Revisar y enviar las invitaciones autorizadas por los canales adecuados, conservando sus IDs. Comenzar por los canales que correspondan al aporte buscado; no hacer envíos duplicados al mismo proyecto.
3. Reproducir cualquier aporte recibido y registrar qué cambió en Genius. La recepción por un tablero o la clasificación automática de un issue es una etapa distinta de una contribución aceptada.
