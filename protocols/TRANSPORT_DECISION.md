# ADR-F4-T01 — transporte mínimo

Fecha: 2026-09-23. Estado: decisión de diseño para candidata `GENIUS-PROTOCOLS-1.0.0`; G4 depende de revisión, pruebas y recepción. Mandato: [PHASE_4_MANDATE](../PHASE_4_MANDATE.md). Contrato resultante: [CONTRACT](CONTRACT.md). Fuentes primarias: [SOURCES](SOURCES.md).

El objetivo es que un proceso externo intercambie la misma instancia FP1, Result y certificados con exactitud y estados preservados. La API Python y CLI recibidas demuestran cálculo local, pero no prueban por sí solas negociación o interoperabilidad de mensajes con un cliente independiente. No hay un consumidor remoto ni permiso de despliegue que obligue a implementar varios transportes.

| Alternativa | Evaluación para este mandato | Decisión |
|---|---|---|
| Solo importación de API Python | Comparte proceso/lenguaje y no ejerce contrato externo. | Insuficiente como evidencia única. |
| Solo intercambio de archivos con CLI heredada | Conserva pareja portable, pero no agrega sesión con negociación de capacidades y errores RPC. | Se conserva como exportación y comparación del resultado. |
| JSON-RPC 2.0 con perfil stdio/LF | Lleva solicitudes correlacionadas y errores; proceso local, sin cuenta/red; permite cliente Node independiente y arnés reproducible. El framing y la sesión son decisiones explícitas de Genius. | Elegida como única interfaz nueva. |
| HTTP con contrato adicional | Requeriría decisiones de red y operación que no son necesarias para demostrar este consumidor. | No implementada; no se atribuye compatibilidad. |
| MCP, A2A u otro ecosistema | No hay una necesidad recibida que justifique implementar sus contratos completos en F4. Compartir JSON-RPC o nombres no demuestra sus capacidades. | No implementados ni anunciados; evaluación futura necesita versión oficial y revisión propias. |

Se usan biblioteca estándar Python para el adaptador y biblioteca estándar Node para el consumidor independiente. La elección elimina instalación de terceros de la reproducción; no demuestra compatibilidad con todas las versiones de Python/Node. Los entornos observados quedan registrados en evidencia. Kernel1.0.1 se conserva byte a byte y el cliente no importa su código para producir expectativas.

La capa de transporte no vuelve a codificar el Input como objeto JSON. ByteEnvelope base64 transporta bytes exactos y SHA-256; por eso dos entradas semánticamente equivalentes con whitespace distinto retienen digest distinto, y candidatos con claves duplicadas no pierden la evidencia del defecto. Result viaja completo como bytes, mientras el consumidor interpreta Nat/Q/Bit como strings y namespaces nominales conforme a Specification. El costo es expansión de aproximadamente cuatro bytes por cada tres bytes de payload, más envoltura, y materialización de blobs; los límites explícitos aceptan ese costo para el alcance local.

El perfil conserva batches básicos y correlación por id, pero explicita restricciones: ids seguros, métodos con params nombrados, inicialización independiente y ausencia de ejecución por notificación. No se presenta como servidor JSON-RPC genérico sin restricciones. El límite de salida puede impedir entregar un cálculo ya hecho; la respuesta es error de transporte y nunca un Result LIMITED inventado.

La cancelación selectiva necesitaría un ciclo de ejecución concurrente y confirmación de estado. El mínimo declara únicamente terminación de proceso: el consumidor recibe fallo de transporte para solicitudes pendientes, sin atribuir una conclusión matemática. El límite temporal Kernel sigue cooperativo; no se promete timeout duro ni contención de memoria. Estos límites hacen comprobable el alcance y reservan la operación controlada para un mandato posterior.

Reversibilidad: un transporte futuro podrá reutilizar el mismo par de bytes y formatos FP1, pero deberá aportar otro contrato de framing, negociación, errores, límites, permisos y conformidad. No podrá cambiar la matemática para acomodar un esquema ajeno, ni heredar G4 para capacidades no probadas. Esta decisión no altera teoría, Specification, Kernel, Benchmark ni baselines y no acepta el gate de su propia fase.
