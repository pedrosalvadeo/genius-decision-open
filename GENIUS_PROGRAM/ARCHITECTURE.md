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

# Arquitectura de Genius Decision

La Specification GENIUS-SPEC-1.0.0 gobierna el Kernel1.0.0 recibido y la versión corregida Kernel1.0.1 de F3. El original permanece aceptado históricamente por G2, con F3-K-001 registrado; la reparación fue validada mediante evidencia G3. Teoría S2 y perfil FP1_FINITE_EXACT no cambian. El código implementa el contrato; los tests lo contrastan y la auditoría revisa ambos. Estado y aceptación: [MASTER_STATE](MASTER_STATE.md).

## Núcleo local

La entrada es una instancia finita inmutable con modelos y premisas explícitos. El orden efectivo sigue [Specification 05](specification/05_PIPELINE_AND_GUARANTEES.md). Los módulos viven en ../kernel/genius_kernel:

| Archivo | Responsabilidad |
|---|---|
| common.py | Racionales y tipos de salida, checks, diagnósticos, límites y estado de ejecución |
| schema.py | UTF-8/JSON estricto, claves duplicadas, gramática cerrada, tiempos, dominios nominales y tablas |
| causal.py | Ocurrencias sin fusión, acción por información, todas las ramas legítimas y escenarios por palabras u |
| structural.py | Funcionalidad, calibración, suficiencia, joins, recursos, identidad/CAG y bienestar |
| evidence.py | Semántica parcial, certificados decisivos, ley, masas, PVS y restricciones hard |
| decision.py | Bloque común, comparaciones, frontera, cobertura y selección explícita |
| engine.py | DAG completo, presentación, estados operativos e integración |
| verifier.py | Recomputa obligaciones desde Input y controla resultados y certificados recibidos |
| __main__.py | CLI local de evaluación y verificación, exportación portable |

La API ofrece `evaluate(raw, limits=None)`, `verify_result` y `verify_decisive_certificate`. Raw son bytes UTF-8 originales; SHA-256 liga toda salida a esa codificación exacta. La CLI se ejecuta con `python -m genius_kernel` desde kernel. El código usa Python >=3.11 y biblioteca estándar, sin servicios externos.

## Garantías y límites

Las decisiones usan (t,i), nunca el estado oculto como sustituto de información. Cada path conserva una ocurrencia; una rama nula o desfavorable permanece en su árbol. Los escenarios se derivan de las palabras exógenas reales. La reducción funcional no comprime la causalidad. CAG aplica la receta antes de unir o intersectar logros; bienestar conserva historia y soporte; la decisión no inventa pesos ni desempates.

La ruta fuerte requiere G01–G15 sobre toda Pi. Un valor parcial, una guarda fallida y un cómputo interrumpido conservan estados distintos. La acción tabulada permanece disponible aunque no habilite continuación. Un testigo negativo legítimo puede refutar hard sin fingir cobertura positiva completa.

El verificador comparte constructores puros con el evaluador, pero deriva las obligaciones de la entrada y no acepta etiquetas PASS como prueba. Esta arquitectura necesita oráculos de tests separados, mutaciones de certificados y auditoría adversarial. No constituye verificación formal mecanizada ni dos implementaciones independientes.

Los límites operativos se declaran en execution.limits; su agotamiento produce LIMITED y no selección. El presupuesto ambiental de recursión del intérprete se registra antes de evaluar. Las opciones max_nodes, max_operations, max_seconds, max_input_bytes y max_integer_digits son adicionales. Los algoritmos exactos pueden crecer exponencialmente; el tiempo cooperativo no interrumpe una operación indivisible del intérprete.

## Capas futuras

Benchmark1.0.0 fue aceptado para su alcance en F3 y contrasta conformidad/límites con generadores y oráculos independientes. Protocols1.0.0 se implementa en F4 con genius-protocols/1.0 sobre stdio. Consumidor Node y adaptador Python son procesos separados; el contrato está en [CONTRACT](../protocols/CONTRACT.md). Infrastructure sigue NOT_CREATED; F5 no iniciada. No hay escucha de red ni servicios externos.

Fuera de FP1: tiempo infinito o continuo, terminación anticipada, fibras de escenario múltiples para comparación fuerte, código aportado como oráculo, matching poblacional general, optimización aproximada y probabilidades inferidas. Las premisas causales, semánticas, normativas y empíricas siguen externas. Diversidad Universal, Radar, Solver y negocio no forman parte de F2.


## Capa experimental F3

benchmark/dynamics.py deriva lenguaje de palabras y masas por productos de caminos; structure.py contrasta reducción, proyecciones mediante enumeración de asignaciones y recetas temporales; adversarial.py muta resultados/certificados con controles positivos; performance.py varía seis parámetros bajo presupuestos declarados; audit_probes.py añade enumeración semántica independiente. harness.py sólo registra llamadas y comparaciones. Ninguno de esos oráculos importa constructores del Kernel ni fixtures F2. El auditor examina diseño y evidencia; el receptor repite desde la entrega.
