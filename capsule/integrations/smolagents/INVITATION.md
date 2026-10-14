# Invitación publicada — smolagents #2986

Publicada con autorización de Pedro el 14 de octubre de 2026 en [smolagents Discussions #2986](https://github.com/huggingface/smolagents/discussions/2986), categoría **Show and tell**. Se revisaron las reglas y la búsqueda de duplicados no devolvió discusiones de Genius. El texto siguiente coincide con el enviado; [recibo](submission.json). La publicación acredita contacto, no aceptación ni adopción.

Título: **Genius Decision: a tested MCP workflow looking for independent reproduction**

## Texto para publicar

I maintain Genius Decision, an Apache-2.0 decision engine with a portable collaboration capsule. Would a smolagents operator be interested in independently reproducing or challenging a concrete decision-model workflow?

We tested smolagents 1.26.0 through its native MCPClient and Tool interface against our Streamable HTTP endpoint. The deterministic harness passed 18 checks: public/private discovery, explicit acceptance of a published synthetic model, one engine evaluation, result export, and deletion of the temporary space and credential. This was our own test with zero LLM calls, not an autonomous-agent test or independent adoption. We pinned MCP 1.30.0 because MCPAdapt 0.1.20 imports an alias removed in MCP 2.3.0; the tested lock and reproduction commands are included.

Code, receipt and reproduction: https://github.com/pedrosalvadeo/genius-decision-open/tree/main/capsule/integrations/smolagents

Capsule: https://github.com/pedrosalvadeo/genius-decision-open/tree/main/capsule

Live manifest: https://geniusdecision.app/agents/manifest.json

MCP endpoint: https://geniusdecision.app/mcp

A useful first contribution (GD-MCP-001) is a report from your independently operated client: versions, commands, observed result or precise incompatibility, and limitations, with credentials removed. The live harness creates and deletes a temporary space and consumes one shared-quota evaluation. The hosted service accepts synthetic or non-personal inputs; local execution is also available.

If decision modeling fits your work better, GD-INT-001/GD-REAL-001 offer a substantive next task: take a real decision supported by public reusable sources, separate facts from assumptions and unknowns, have the decision owner confirm material assumptions, and return a reviewable model plus observations that support or contradict it. A synthetic interoperability test does not validate a real decision.

Genius-specific code stays outside smolagents core. Interested contributors can choose their scope and return an issue or PR with the opportunity ID at https://github.com/pedrosalvadeo/genius-decision-open/issues. Participation is voluntary, with no payment commitment or project endorsement implied. This proposal and test harness were prepared with AI assistance; I remain responsible for the proposal and review.
