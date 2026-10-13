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

# Protocolo de transferencia de Genius

Cada fase entrega un paquete que permite reconstruir y continuar solo con archivos. Chat, memoria, cuenta de origen, enlaces privados y conexiones externas no son dependencias admisibles del conocimiento indispensable. El protocolo F0 se conserva y aplica aquí a **GENIUS_PHASE_4_HANDOFF/** y su ZIP externo homónimo.

## Unidad y documentos obligatorios

La unidad es el paquete completo: `GENIUS_PROGRAM/`, fuentes, código/contratos, revisiones, conformidad, historial y herramientas offline. Enviar solo un prompt o una Specification aislada no satisface transferencia. Las rutas indispensables son relativas e internas.

| Archivo raíz | Contenido mínimo |
|---|---|
| RELEASE.md | ID, fecha, fase, alcance, inventario, snapshot, versiones, componentes ausentes y verificación |
| STATE.md | Estado operativo y vínculo al MASTER_STATE canónico |
| ARCHITECTURE.md | Capas, límites y arquitectura canónica |
| DECISIONS.md | Decisiones, reservas y sustituciones explícitas |
| INVARIANTS.md | Restricciones preservadas y registro canónico |
| DEPENDENCIES.md | Dependencias lógicas, matemáticas, computacionales; inputs disponibles/ausentes |
| TEST_RESULTS.md | Comprobaciones realmente ejecutadas, entradas/resultados y exclusiones |
| ACCEPTANCE_REPORT.md | Gate, criterios, hallazgos, correcciones, roles, evidencia y dictamen |
| KNOWN_LIMITATIONS.md | Límites científicos, documentales, técnicos y de revisión |
| BLOCKERS.md | Severidad, dependencia afectada, estado, responsable y cierre verificable |
| OPEN_QUESTIONS.md | Preguntas no resueltas que no se convierten en supuestos |
| NEXT_PHASE_INPUT.md | Insumos admitidos, trazabilidad, precondiciones y resultado siguiente |
| NEXT_PHASE_PROMPT.md | Instrucción ejecutable sin contexto, límites de autonomía y gate siguiente |

Los documentos raíz pueden resumir y enlazar registros de GENIUS_PROGRAM, pero deben aportar contexto suficiente y no contradecirlos. STATE y MASTER_STATE deben coincidir con el informe de aceptación. Los prompts auxiliares, por ejemplo PHASE_3_MANDATE o PHASE_4_PROMPT, se identifican por README/manifiesto; su presencia no significa que una fase posterior haya empezado.

## Preparación, revisión y sellado

1. Fijar candidata, fase, alcance, fuentes y estado de componentes. Excluir secretos, tokens y credenciales.
2. Actualizar estado, mapa, invariantes, dependencias, decisiones, bloqueadores, versiones y roadmap. Mantener límites y faltantes de fases posteriores.
3. Preparar los trece documentos, fuentes, contratos y prompts. Comprobar todos los enlaces internos indispensables.
4. Ejecutar comprobaciones documentales y de integridad; conservar comandos/procedimientos, entradas, resultados y límites. Un caso histórico DESIGNED de F1 se vincula a un resultado F2 separado; no se cambia su historia por reenviarlo.
5. Auditor separado revisa candidata y correcciones. Receptor sin historia del proyecto realiza prueba de continuación solo con paquete. Conservar hallazgos, respuestas y configuración de roles; independencia interna no se presenta como institucional.
6. Registrar dictamen motivado y sincronizar estado. Sin revisión suficiente, gate queda pendiente aunque todos los archivos existan.
7. Generar manifiesto final y ZIP fuera de la carpeta comprimida. Si cambian premisas de una revisión, repetir partes afectadas antes de sellar.
8. Extraer ZIP en carpeta nueva y verificar esa copia. Entregar identificación y modo de retomar. Una revisión distribuida no se modifica bajo el mismo ID.

## Integridad offline

La raíz incluye `MANIFEST.sha256` y `tools/verify_package.py`. El manifiesto enumera SHA-256 y ruta relativa de los archivos de la entrega, salvo sí mismo para evitar autorreferencia. El ZIP no se incluye en su propio manifiesto; el ZIP F2 histórico figura como archivo ordinario de F3 y conserva la genealogía F1/F0.

Desde la raíz extraída ejecutar:

```bash
python3 tools/verify_package.py
```

El verificador comprueba documentos obligatorios, rutas contenidas en raíz, hashes, faltantes y adicionales no declarados. Exclusiones exactas están visibles en script y RELEASE; `.git` no pertenece al conjunto documental cuando corresponda. Una discrepancia impide tratar bytes como la entrega identificada. No regenerar hashes sobre bytes desconocidos para ocultarla: recuperar copia íntegra o documentar nueva candidata revisada.

Hashes no autentican autoría ni validan ciencia. El paquete F2 de history y su copia baseline se conservan byte por byte; F1/F0 siguen preservadas en su genealogía. No se convierten los estados históricos en estados actuales editando sus bytes.

## Prueba de continuidad sin contexto

El receptor no debe depender del chat ni de notas privadas. Con documentos recibidos debe poder identificar y justificar:

- Objetivo, fase, gate real y componentes NOT_CREATED.
- Fuente S1, capa S2, reparaciones y qué documento resuelve cada dominio/operación.
- Perfil FP1, escenarios/políticas, límites, no vacuidad y guardas fuertes.
- Estados de valor, dominio, validez, evidencia, cómputo, cobertura.
- Qué se revisó o ejecutó y qué solo está diseñado; límites de independencia.
- Invariantes, bloqueadores, pendientes empíricos/históricos y siguiente acción exacta.
- Cómo reproducir Kernel/Protocols y comenzar operación controlada F5, si y solo si G4 y el mandato correspondiente lo habilitan.

Registrar preguntas/respuestas o tareas realizadas con citas internas, fallos y correcciones. No sustituirlo por un «entendido» del receptor. Esta prueba comprueba continuidad técnica del paquete, no originalidad ni eficacia real.

## Recepción y reanudación

Leer README/RELEASE; verificar antes de editar; leer STATE, MASTER_STATE, aceptación y límites; revisar Specification y fuentes según tarea; reconstruir gate y acción siguiente. Si G4 no está aprobado, completar exclusivamente sus pendientes dentro del mandato F4. Si G4 está aprobado, el prompt F5 y autorización correspondiente determinan la fase siguiente; no se deduce del nombre del ZIP.

Conservar recibida una copia intacta y trabajar sobre nueva candidata. No se necesita GitHub para leer/verificar/continuar F4. La futura migración exige identidad de paquete y commit, ADR y verificación según VERSIONING; ningún permiso externo se transfiere automáticamente al cambiar cuenta.

## Rechazo y reparación

Rechazar aceptación si faltan fuentes/documentos, hay enlaces indispensables rotos, versiones ambiguas, integridad discrepante, dependencia del chat, claims desproporcionados, pendientes sin dependencia/criterio de cierre, falta de revisión separada o un prompt que salte gates/mezcle Diversidad Universal. Registrar el motivo y reparación. Rechazar un gate no implica borrar trabajo útil ni historia.
