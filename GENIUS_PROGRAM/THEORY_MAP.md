# Mapa de Matemática Genius en F1

Fuente preservada: GENIUS-THEORY-2026-09-23-S1. Capa revisada explícita: S2 mediante [AMENDMENTS](theory/AMENDMENTS.md), sin reescribir el DOCX. Contrato: GENIUS-SPEC-1.0.0, FP1_FINITE_EXACT. La aceptación integrada corresponde al gate G1; este mapa no lo declara por sí mismo.

| Tramo | Objetos y alcance revisados | Contrato de F1 | Revisión deductiva |
|---|---|---|---|
| Fundamentos/M0 | Funciones parciales, dominios, historias, estado/información, descenso y suficiencia | 02; formato 01; AM-01 | [REVIEW_0_III](theory/reviews/REVIEW_0_III.md) |
| MI | Perfiles, calibración, preórdenes y reducción por consulta | 02 y guardas 05 | Mismo informe 0–III |
| MII | Relación conjunta, vistas, recursos, recomposición y consultas reducidas | 02; tablas 01 | Mismo informe 0–III |
| MIII | Identidad generativa, recetas att/hold/acc, cuantificadores, CAG posible/robusto y testigos | 02; receta/modo comunes | Mismo informe 0–III |
| MIV | Reloj, existencia, aplicabilidad, medición, bienestar y reglas poblacionales | [03](specification/03_CAUSAL_AND_WELFARE.md); producto identificado FP1 | [REVIEW_IV_V](theory/reviews/REVIEW_IV_V.md) |
| MV | Init, contexto, políticas, B/U, árboles, escenarios, trazas y monitor | 03; modo pre, ramas completas | Mismo informe IV–V |
| MVI | Referencias, semántica, protocolos/certificados, V parcial, ley, masas y PVS | [04](specification/04_EVIDENCE_AND_DECISION.md); AM-02/03/04 | [REVIEW_VI_VII](theory/reviews/REVIEW_VI_VII.md) |
| MVII | Restricciones, producto, frontera, alcance y selección | 04/05/06; reglas explícitas | Mismo informe VI–VII |
| Integración | Teoremas 10.1–10.3, hipótesis fuertes, DAG y testigo sintético | [05](specification/05_PIPELINE_AND_GUARANTEES.md) | [REVIEW_INTEGRATION](theory/reviews/REVIEW_INTEGRATION.md) |

[FORMAL_INDEX.md](theory/FORMAL_INDEX.md) y su JSON inventarían **152 entradas: 83 definiciones, 6 convenciones, 62 resultados numerados y 1 corolario**, cada una con fuente, estado de revisión e informe/sección. Los resultados reparados conservan esa distinción. La revisión de autores no sustituye auditoría adversarial separada ni demostración mecanizada.

## Reparaciones y límites de lectura

- AM-01 resuelve I-06: la actualización reducida recibe información R(i), acción y observación O(y), con conmutación y dominios tipados.
- AM-02 añade la hipótesis que falta en 8.6: además de lectura exacta, el protocolo admite certificados canónicos para toda consulta decisiva; FP1 los genera para 0 y 1.
- AM-03 restringe el acuerdo de una extensión foliar a F∩D_V.
- AM-04 normaliza guardas, pares y ámbitos de notación sin esconder cambios de contenido.

Los localizadores Pnnnnn de [S1_EXTRACTED](theory/sources/S1_EXTRACTED.txt) sirven para navegar; no preservan todos los operadores. [S1_READABLE](theory/sources/S1_READABLE.md) es auxiliar. Ante ambigüedad se consulta [DOCX original](theory/sources/S1_Matematica_Genius_Modulos_Astra_01.docx) y el registro de enmiendas, no se reconstruye por intuición una fórmula degradada.

## Lectura de cierre

La numeración M0→MVII no constituye cadena computacional: MV precede a CAG, bienestar y evaluación de futuros; MI/MII también consumen ámbitos alcanzados. [DEPENDENCIES](DEPENDENCIES.md) y 05 fijan el DAG. La ruta fuerte es condicional: modelos finitos explícitos, dominios/cobertura completos donde se requieren y premisas identificadas. Los dominios generales más amplios se revisan sin convertirlos en capacidades de FP1.

La mención histórica v6 no es una release recibida. La genealogía anterior permanece no verificada y no se hereda su certificación. La fuente no acredita utilidad empírica, originalidad ni mérito editorial; E-01/E-02 siguen en[BLOCKERS](BLOCKERS.md). El Kernel y otros componentes siguen NOT_CREATED hasta sus fases.
