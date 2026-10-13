# Actualización operativa F5 — 2026-09-26

Estado actual: F5_COMPLETED; G5_PASS_LOCAL_SYNTHETIC_LAB. Mandato actual [activaciónF5](../PHASE_5_ACTIVATION.md)
y [promptF5](../PHASE_5_PROMPT.md). F4 recibido de nuevo localFP1. Infrastructure
GENIUS-INFRASTRUCTURE-1.0.0 es la nueva capa local; Kernel1.0.1, Protocols1.0.0,
Benchmark1.0.0, Specification1.0.0 y teoríaS2 intactos. F6–F8 no iniciadas.
El alcance ejecutado es laboratorio sintéticoUID0/caps0/NNP1, no prueba nonroot
ni despliegue. Estado/gate vigentes en [aceptación](../ACCEPTANCE_REPORT.md).

Decisiones F5: [registro](../DECISIONS.md); operación: [Infrastructure](../infrastructure/README.md);
reparaciones: [hallazgos](../validation/F5/FINDINGS.md); límites: [residuales](../KNOWN_LIMITATIONS.md).
BaselineF4 íntegra es ZIP original en history; árboles F3/F2/F1/F0 y todos
los negativos heredados se conservan. Trece documentos+verificador+comprobante
externo y recepción final siguen siendo obligatorios. No depender del chat.

Los textos siguientes son registro histórico de F0–F4. Sus afirmaciones de
NOT_CREATED/NOT_STARTED no sustituyen el estado F5 actual señalado arriba;
sus obligaciones científicas y de gobierno continúan vigentes.

---

# Versionado y compatibilidad F4

Release aceptada para su alcance: GENIUS-P4-2026-09-23-v1.0.0. [Estado efectivo](MASTER_STATE.md). El predecesor GENIUS-P3-2026-09-23-v1.0.0 se conserva íntegro en baseline/history; sus estados son historia, no el estado actual.

| Objeto | Versión F4 | Cambio |
|---|---|---|
| Teoría | GENIUS-THEORY-2026-09-23-S2 | Ninguno |
| Specification | GENIUS-SPEC-1.0.0 | Ninguno |
| Formatos | genius-fp1/1.0; genius-fp1-result/1.0 | Ninguno |
| Perfil/protocolo lógico | FP1_FINITE_EXACT / FP1_EXACT_ENUM_V1 | Ninguno |
| Kernel | GENIUS-KERNEL-1.0.1 | Ninguno |
| Benchmark | GENIUS-BENCH-1.0.0 | Ninguno; baseline F3 |
| Protocols | GENIUS-PROTOCOLS-1.0.0 | Nuevo; wire genius-protocols/1.0 |
| Infrastructure | Sin versión | NOT_CREATED |

La negociación compara versiones wire por igualdad explícita. Un parche posterior que mantenga contrato cambia versión de producto y evidencia. Cambios incompatibles de campos/significado requieren versión wire distinta. La política completa y restricciones están en [CONTRACT](../protocols/CONTRACT.md) y [COMPATIBILITY](../protocols/COMPATIBILITY.md). Ninguna compatibilidad se infiere de nombres o del éxito de un test.

Una release distribuida no cambia bajo su misma identidad. MANIFEST fija todos los archivos excepto sí mismo, .git, __pycache__ y *.pyc. SHA-256 detecta bytes, no autoría, verdad o adecuación empírica. Toda matemática modificada requiere enmienda/instantánea; cualquier cambio de contrato exige revisar dependientes. Migración GitHub requiere repositorio autorizado, identificación del paquete y commit, verificación y ADR; no es requisito del handoff.
