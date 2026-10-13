# Genius Decision Specification

Identificador: **GENIUS-SPEC-1.0.0**. Perfil: **FP1_FINITE_EXACT**. El dictamen de aceptación del handoff determina su estado de release. Este contrato especifica una implementación futura; F1 no contiene Genius Kernel. La fuente base es S1 preservada, con las enmiendas explícitas de [AMENDMENTS](../theory/AMENDMENTS.md). La instantánea resultante se identifica como GENIUS-THEORY-2026-09-23-S2 y no borra S1.

## Autoridad y alcance

Las palabras DEBE y NO DEBE expresan obligaciones de conformidad de esta Specification. Las reglas matemáticas se fundamentan en S1 y en los argumentos de revisión. Los nombres de campos, selección del perfil y diagnósticos son decisiones de ingeniería explícitas. Ninguna comprobación de tablas acredita por sí misma que esas tablas describan el mundo. Las conclusiones del perfil se refieren a la instancia formal recibida, bajo sus premisas de interpretación.

Orden de lectura: este archivo → [tipos y formato](01_TYPES_AND_WIRE.md) → [M0–MIII](02_REPRESENTATION_FUNCTION_COMPOSITION_CAG.md) → [MV y MIV](03_CAUSAL_AND_WELFARE.md) → [MVI y MVII](04_EVIDENCE_AND_DECISION.md) → [ensamblaje](05_PIPELINE_AND_GUARANTEES.md) → [salidas](06_OUTPUT_AND_DIAGNOSTICS.md). Los contratos modulares expresan objetos matemáticos; 01 vincula esos objetos a un formato concreto. Si discrepan, la release se rechaza y se corrige: no se concede al formato autoridad para cambiar la matemática.

## Perfil implementable

FP1 usa conjuntos y tablas finitas cerradas, tiempo discreto 0,…,H, identificadores nominales, racionales exactos y funciones parciales cuyo dominio es la lista de claves presente. No recibe programas arbitrarios como comparadores, lectores o leyes. La familia objetivo Π es la lista explícita de políticas del problema: la exhaustividad se refiere a esa lista, nunca a todas las políticas concebibles.

La ruta fuerte exige: inicialización realizada; árboles completos; políticas informacionales localmente admitidas; todas las hojas en H; escenarios comunes que son secuencias exógenas y tienen exactamente una hoja por política; reducción funcional suficiente; recomposición multiescalar exacta; CAG traducido y definido; bienestar completo en soporte común; leyes legítimas; PVS definida para cada política; restricciones hard decididas; criterios compatibles. Estas son las guardas de la conclusión conjunta de S1 10.2. No son supuestos ocultos de toda la teoría.

FP1 admite tablas parcialmente definidas y produce diagnósticos por componente. Puede obtener objetos independientes aunque otra guarda falle. Una frontera sobre un bloque menor se identifica como relativa; no se presenta como la frontera exhaustiva de Π. Que un valor quede legítimamente fuera de dominio no es un fallo de ejecución. Una presentación contradictoria o una fila probabilística inválida tampoco es una medición simplemente ausente.

| Objeto general de S1 | Instanciación FP1 | Razón y límite |
|---|---|---|
| Estados/historias e inicialización | Modelo finito tabulado y testigo inicial singleton declarado | Suficiencia interna por construcción; adecuación causal externa sigue como premisa |
| Políticas | Tablas (tiempo, información) → acción | No acceso a estados ocultos; familia objetivo enumerada |
| Escenarios | Palabras de entradas exógenas de longitud H | La ruta fuerte verifica imagen común y fibras singleton |
| Valores funcionales | Racionales calibrados y orden usual; índice común | Subclase de los espacios ordenados generales |
| Multiescala | Relación finita y proyecciones declaradas; unión natural exacta comprobada | No supone independencia de marginales |
| Identidad generativa | Firmas nominales ya cocientadas; significados finitos y órdenes tabulados | Equivalencia por igualdad de ID; no implica identidad causal |
| Traducción generativa | Mapa de identidad nativa a identidad común | Subclase de traducción estatal general; fidelidad y pares comprobados |
| CAG | Recetas att, hold,L y acc; modos posible y robusto, por política singleton | Origen incluido separadamente; conserva testigos y tiempos |
| Bienestar | Soporte de portadores y aplicabilidad común a políticas/escenarios; valores racionales por ocurrencia | Comparación identificada producto; no incluye matching anónimo ni poblaciones variables entre políticas |
| Evidencia | Universo semántico finito, referencias por hoja y tarea parcial tabulada; lector exacto | Revisión verificable de cobertura y constancia; no oráculos semánticos |
| Ley | Masas racionales por ramas de cada ocurrencia | No se infieren de causalidad ni se eliminan ramas nulas |
| Restricciones | Presupuesto instantáneo por recurso y, si se declara, tarea universal sobre consultas u hojas | Se mantienen separadas de Φ y del modelo causal |
| Decisión | Producto de cuatro criterios; frontera relativa o exhaustiva bajo guardas | Ninguna escalarización ni prioridad implícita |
| Selección | none, unique o lista de prioridad explícita | El modo forma parte de la instancia; no promete equivarianza respecto de datos que la prioridad rompe |

Fuera del perfil: horizonte infinito/continuo, código arbitrario para primitivas, terminación anticipada, múltiples hojas de un mismo escenario en la ruta fuerte, traducciones relacionales generales, modelos probabilísticos imprecisos mezclados sin ley, matching poblacional general, y optimización aproximada. Los resultados generales correspondientes se revisan sin convertirlos en capacidades de FP1. Su soporte requiere otra versión/perfil, no un comportamiento silencioso.

## Contrato de eficacia

La implementación DEBE construir los resultados cuando sus guardas estén satisfechas, con operaciones exactas y recursos suficientes. No cumple el contrato un programa que siempre devuelve «no certificado». Los límites operativos pueden detener el cálculo con RESOURCE_EXHAUSTED; ese estado no prueba fuera de dominio, inexistencia, inviabilidad ni frontera vacía. El costo combinatorio puede ser grande y F1 no promete rendimiento práctico.

Cada resultado conserva: bytes de entrada identificados, versiones, ámbito formal, política, ocurrencias, escenarios, dominios, receta/regla pertinente, premisas externas y evidencias recomputables. Se prohíbe recuperar datos mutables o preferencias del entorno durante el cálculo. El expediente distingue las observaciones aportadas de las conclusiones derivadas.

## Requisitos de aceptación del contrato

R-01 tipos y dominios; R-02 identidad y procedencia; R-03 causalidad/información; R-04 escenarios; R-05 funcionalidad; R-06 suficiencia; R-07 composición; R-08 recursos; R-09 CAG; R-10 bienestar; R-11 evidencia; R-12 probabilidad; R-13 restricciones; R-14 comparación/frontera; R-15 selección; R-16 efectividad/diagnósticos; R-17 trazabilidad; R-18 transferencia. Su detalle y casos se fijan en [TRACEABILITY.md](../conformance/TRACEABILITY.md). Las pruebas diseñadas de conformidad no son pruebas ejecutadas de un Kernel inexistente.
