# Compatibilidad de Genius Protocols 1.0

Esta matriz distingue soporte contractual, evidencia ejecutada y exclusiones. La aceptación de F4 corresponde al informe raíz; no se deriva del número de versión. [CONTRACT](CONTRACT.md) define mensajes y límites; [TRACEABILITY_F4](TRACEABILITY_F4.md) enlaza los reportes finales examinados y sus límites. PASS significa solo el alcance de esos ensayos.

| Dimensión | Combinación declarada | Comportamiento y límite |
|---|---|---|
| Producto/protocolo | `GENIUS-PROTOCOLS-1.0.0` / `genius-protocols/1.0` | El primero identifica software; el segundo el contrato negociado. No son intercambiables. |
| Kernel | `GENIUS-KERNEL-1.0.1` | Único sujeto de esta candidata. El adaptador usa sus API públicas sin modificar sus bytes. La evidencia heredada no se recuenta como experimento nuevo. |
| Specification/teoría | `GENIUS-SPEC-1.0.0` / `GENIUS-THEORY-2026-09-23-S2` | Autoridad conservada. El handshake no prueba conformidad matemática por sí mismo. |
| Perfil/formatos | `FP1_FINITE_EXACT`; `genius-fp1/1.0`; `genius-fp1-result/1.0` | No se aceptan campos de teoría general ni transformaciones implícitas. Una versión FP1 incorrecta dentro de input se conserva para diagnóstico del Kernel. |
| Evidencia lógica | `FP1_EXACT_ENUM_V1` | Capacidad lógica heredada; no es nombre del transporte ni certificación empírica. |
| Formato de certificado suelto | `{input_digest,certificate}` del Kernel | Candidate exige ByteEnvelope y el Input completo aparte. No se añade format al envelope interno. |
| Versiones wire no soportadas | Oferta sin `genius-protocols/1.0` | `-32001`; sesión permanece sin inicializar. Oferta mixta con versión soportada puede negociar exactamente esa. |
| Capacidades no soportadas | Cualquier requerida fuera de evaluate/verify_result/verify_certificate | `-32001`, sin simular una capacidad ausente. |
| Kernel 1.0.0 histórico | Baseline F2 y ejemplo histórico | No es backend negociable del servidor. Conserva su identidad y el defecto F3-K-001 documentado; no hereda la reparación 1.0.1. |
| JSON-RPC | Mensajes 2.0 con perfil explícito stdio/LF | Batches hasta 16, IDs string ASCII/entero seguro/null, errores y notificaciones delimitados. No es afirmación de soporte sin restricciones para toda implementación JSON-RPC. |
| Consumidor de referencia | Node en proceso separado; Requests individuales con IDs string | No importa Kernel/Python para serializar ni interpretar transporte. Que el consumidor use un subconjunto no elimina las obligaciones batch/IDs del servidor. |
| Adaptador de referencia | Python 3.11+ declarado por Kernel; biblioteca estándar | CPython 3.12.14 es entorno observado. No se afirma matriz ensayada de todos los Python/SO. |
| Runtime consumidor | Node v24.19.0 observado; biblioteca estándar | Documentación oficial de rama 24 consultada. No se afirma que la versión de una página mutable haya sido ejecutada. |
| Otros transportes | MCP, A2A, HTTP/OpenAPI, red remota | NOT_IMPLEMENTED. Ni JSON ni stdio conceden sus etiquetas de conformidad. |
| Cancelación | Terminar el proceso de la sesión | No hay cancelación selectiva ni confirmación de aborto. Operaciones pendientes sin respuesta completa producen fallo de transporte. |

## Conservación y diferencias permitidas

| Situación | Decisión contractual |
|---|---|
| Input con whitespace, orden de miembros o escapes diferentes pero objeto equivalente | Los bytes y digest distintos se conservan. No se intercambian certificados por una equivalencia presunta. |
| Unicode compuesto/descompuesto o escapes equivalentes | Sin normalización de bytes; interpretación de strings conforme a los escalares recibidos. |
| Result serializado con distinto whitespace u orden no semántico | Su blob tiene otro digest. Solo se compara significado conforme a Set/List/tablas y gramática FP1; no se deduce invalidez por serialización distinta. |
| Input blob correcto pero JSON/UTF-8 inválido | Evaluate entrega los bytes originales al Kernel. Result preserva presentación INVALID o estado operativo aplicable. |
| Candidate con claves duplicadas/JSON inválido | Report INVALID/CANDIDATE_SYNTAX antes de crear un objeto que pierda duplicados. |
| Candidate con numbers JSON, aunque sean pequeños/exactos | Report INVALID/CANDIDATE_TYPE: FP1 codifica esos datos como strings. No se transforma un number en Nat/Q. |
| Base64 no canónico o digest incorrecto | Error RPC de params; el payload no llega al Kernel. |
| Resultado LIMITED, ERROR, UNRESOLVED o Cell OUTSIDE_DOMAIN/BLOCKED | Se preserva la categoría; no se convierte en error genérico de transporte, false ni cero. |
| Respuesta excede máximo | Error de transporte; el cálculo pudo ocurrir. No se fabrica un Result parcial. |

La compatibilidad está limitada por las capacidades y presupuestos publicados antes del cálculo. No cubre entradas arbitrariamente grandes, memoria ilimitada, autenticidad, adecuación de premisas, rendimiento universal, equivalencia entre modelos ni operaciones de teoría general ajenas a FP1. Una nueva implementación/versión requiere evidencia y revisión; no puede asumirla por copiar estos identificadores.

## Estado de evidencia

Los reportes finales de TRACEABILITY_F4 registran 74 casos/972 checks PASS del auditor separado en tres baterías, y 25 casos/79 aserciones PASS del consumidor Node. La reproducción de 3338 llamadas F3 tiene 3336 identidades completas de objeto y 2 rechazos de parser CANDIDATE_TYPE declarados: no se presenta como 3338 identidades completas ni como un segundo oráculo matemático. Los borradores y reparaciones permanecen conservados.

La preservación de ERROR se probó con un fixture de forma y mediante inyección en el límite de la API, sin provocar un fallo interno real del Kernel. El umbral real de salida 32 MiB se comprobó con payloads inyectados, no con una instancia matemática enorme. La auditoría también termina procesos peer sintéticos durante una solicitud y verifica fallo de transporte del consumidor; no afirma haber interrumpido un cálculo real del Kernel, cancelación selectiva ni conclusión matemática del cálculo interrumpido. La rama RecursionError de parser no tiene un ensayo focal independiente y conserva esa limitación de evidencia.

La inspección estática de contrato frente a `genius_protocols/server.py` y `wire.py` verificó nombres/campos/códigos, transmisión íntegra de raw, ausencia de transformación matemática y separación parser candidate/API Kernel. Es revisión del diseñador, distinta de la auditoría independiente. Recepción, integridad final y aceptación de fase se consultan en los documentos raíz, sin concederlas desde esta matriz.
