# Contratos portátiles

El CLI aplica validaciones de estructura y de integridad. Los expedientes de evidencia declaran observaciones; su presencia no prueba por sí sola su verdad.

## Evidencia — genius-case-evidence/1

Campos: case_id, question, context, origin (real/synthetic/mixed), observed_at, data_authority, sources, observations, assumptions, unknowns, empirical_status y publication (public/private).
Cada fuente tiene id, reference y accessed_at. Cada observación tiene statement y source_id. Los orígenes real/mixed requieren fuentes y observaciones identificadas. Cada fuente puede ser una URL o un archivo con procedencia declarada. Usar un contexto real no convierte hipótesis en mediciones.

Estados empíricos: NOT_ASSESSED, PROTOCOL_DEFINED, OBSERVATIONS_COLLECTED, EXTERNALLY_REVIEWED. Son declaraciones del expediente; el ejecutor no los acredita ni los promueve.

## Contribución — genius-contribution/1

Campos de texto: id, author, summary, base_revision, kind, claim, reproduction. artifacts es una lista de {path,sha256} relativa al manifiesto. review_status: PROPOSED/REPRODUCED/ACCEPTED/REJECTED. La validación no ejecuta reproduction ni acepta código. Ver ejemplo generado por las pruebas.

## Transferencia — genius-handoff/1

Campos: mission, host, base_revision, next_work y contributions (rutas relativas de manifiestos de contribución). Puede ampliarse con bitácora, interlocutores, resultados y bloqueos. El validador comprueba cada contribución. Compartir una misión no concede la autoridad del anfitrión anterior.

## Recibo — genius-capsule-run/1

Liga modelo, evidencia y evaluación mediante SHA-256, identidad de código y fecha. El resultado del compilador conserva ambos cálculos CAG y los objetos nativos. La verificación de la cápsula admite actualmente STOCK_FLOW_FINITE_V1 y requiere recompilación y recomputación, no confianza en un marcador valid=true.
