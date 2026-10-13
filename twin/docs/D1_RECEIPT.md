# D1 — Acta del integrador

Cierre técnico: 13 de octubre de 2026, UTC. Trabajo iniciado el 12 de octubre. Base exacta: `a8af0502a022aa2c3d87c4e7da29be63e50717a6`, rama `deploy/staging` de `pedrosalvadeo/genius-decision`. Se recibió una copia mínima verificada por objetos Git; no se presupone un clon completo ni se acredita el estado del servicio desplegado.

**Dictamen: incremento recibido técnicamente para el caso sintético local.** Comprensión humana y validación empírica siguen sin ejecutarse. No es una recepción global del programa ni el cierre de F6A.

## Qué se implementó

Todo el cambio está dentro de `twin/`. El dominio genera las trayectorias mediante transiciones y balances; el compilador entrega bytes nuevos al núcleo FP1 existente y verifica sus resultados. No hay cambios al núcleo, beta, infraestructura, dependencias recibidas ni automatización de despliegue.

El servicio local conserva propuestas, confirmaciones materiales, versiones inmutables, trabajos, observaciones y claves de idempotencia en SQLite. El frontend HTML/CSS/JavaScript sin proveedores externos usa ese mismo servicio. Las seis etapas son revisión, gemelo, futuros, conclusión, cambios y evidencia. El mapa tiene representación textual equivalente; los controles temporales conservan el monitor de incumplimiento.

El relato es una entrada acotada a una plantilla explícita: no hay un traductor general de lenguaje a cualquier dominio. La confirmación admite premisas sintéticas para analizar; no autentica hechos ni autoriza intervenciones. Un relato externo conserva una obligación de modelización y no produce un resultado inventado.

Cada modalidad CAG se ejecuta como una entrada FP1 distinta. Se conservan el Input original, Result, texto serializado, verificación y manifiesto. D1 usa el sobre `genius-twin-evaluation/0.1.0`; **no produce RC01** y no amplía silenciosamente el perfil `fdq` H=1 ni los esquemas cerrados FP1. El campo `rc01_receipt=null` pertenece al sobre nuevo, nunca a una celda formal.

## Resultados sustantivos recibidos

| Política | PVS de tarea | CAG acc posible | CAG acc robusto |
|---|---|---|---|
| C | 1/2 | {q0} | {q0} |
| R | 1 | {q0,q1} | {q0,q1} |
| E | 5/6 | {q0,q1,q2} | {q0,q1} |
| E′, revisión | 1 | {q0,q1,q2} | {q0,q1,q2} |

La ley conjunta N/H/HA es 1/2,1/3,1/6, estipulada. El horizonte contiene 14 pasos diarios y el estado inicial. La vitalidad de P1/P2 se presupone; la condición discriminante es hídrica. El éxito de trayectoria exige la condición en todos los estados diarios. La probabilidad terminal es 1 para las tres políticas iniciales y no sustituye aquel evento.

Con la restricción universal confirmada, solo R resulta factible en C/R/E. La revisión sustituye E por E′ y conserva E en el historial. En HA, E′ usa 18 L adicionales, 310 min de A y 180 min de B; mantiene 2 L el día 10. La frontera pasa a {R,E′}: menor carga temporal de R y capacidad adicional de E′ no se convierten en un ganador automático. La suma de minutos no es bienestar agregado.

El fallo del día 10 persiste en C-H, C-HA y E-HA aunque la bandeja recupere 2 L el día 11. Las ramas de masa cero permanecen en CAG robusto y restricciones universales. El núcleo conserva masa indecidida positiva y no emite PVS formal en ese caso; el adaptador D1 aún admite únicamente su modelo completo y cerrado.

## Evidencia ejecutada sobre el incremento

| Verificación | Resultado | Archivo conservado |
|---|---|---|
| Suite conjunta de dominio, compilación, servicio y aceptación independiente | 39/39; 49.077 s; cero fallos | `reviews/UNIT_TESTS.txt` |
| Navegador real, recorrido completo | 41 comprobaciones; PASS | `reviews/BROWSER_EVIDENCE.json` |
| Exportación descargada: digest del expediente y cuatro parejas Input/Result | Cuatro verificaciones válidas | `reviews/EXPORT_REPLAY.json` |
| Código recibido | Hashes SHA-256 de fuentes y tests | `reviews/SOURCE_HASHES.json` |
| Revisión independiente y guardas pertinentes del núcleo | 20 tests propios incluidos en los 39; tres guardas adicionales aprobadas por el revisor | `reviews/INDEPENDENT_REVIEW.md` |

Los tiempos son incidentales, no benchmarks. Entorno de integración: Python 3.12.14; Flask 3.1.2 y dependencias exactas del lock existente; Node 24.19.0; Chromium 133 con Playwright. El navegador se usa como herramienta de verificación, no como dependencia de la aplicación.

Se recorrieron las seis vistas a 390×844 y 320×844, además de escritorio 1440×1000. Se revisaron capturas y se comprobó ausencia de desborde de página; las tablas anchas conservan desplazamiento propio. El gate ejercitó confirmación incompleta, evaluación inicial, edición y comparación, exportación, discrepancia, reevaluación, recarga, restauración y dominio ajeno. No hubo excepciones JavaScript sin capturar ni solicitudes externas. Esto acredita la ejecución comprobada, no un estudio de accesibilidad, todos los navegadores ni comprensión por personas.

El JSON de demostración entregado se exportó antes de añadir la observación de prueba y contiene las dos primeras versiones evaluadas. El gate posterior registró una observación claramente marcada como sintética, contrastó la predicción previa y comprobó suspensión persistente. Ningún dato del ensayo es una medición de campo.

## Hallazgos cerrados

1. La primera implementación de observación recalculaba la predicción al recibir el dato. Ahora exige un trabajo previo finalizado, toma su valor congelado y conserva versión, job, digest y relación temporal. La observación retrospectiva no se presenta como validación prospectiva.
2. Lecturas SQLite dejaban conexiones sin cierre explícito. Se corrigió; cien lecturas mantuvieron cuatro descriptores abiertos en la comprobación focal.
3. El checkbox de observación desbordaba a 390 px; a 320 px también desbordaban campos de edición y se estrechaba el historial. Se corrigieron los tamaños mínimos y la disposición. El gate completo final pasó ambos anchos. El enlace de salto queda oculto visualmente hasta recibir foco.
4. Se precisaron la conservación por transición de CAG acc y la suspensión por lado al comparar versiones. La selección formal histórica permanece visible, separada de una recomendación suspendida.

Una aserción inicial del navegador buscaba una frase distinta a la que realmente mostraba la obligación de dominio. Se corrigió el selector del test; no se contabiliza aquella ejecución como aprobada. Las dos fallas previas de diseño móvil sí fueron defectos y se repararon.

## Límites y obligaciones abiertas

- Adaptador local, sintético y cerrado: no se admite automáticamente otro dominio, horizonte, ley ausente, evidencia incompleta ni modelo biológico real. La implementación distingue capacidad ausente de dato ausente.
- API HTTP local equivalente para consumidores; sin MCP, autenticación multiusuario, adquisición externa ni recibo RC01. No se recibió para exposición pública. El servidor es de desarrollo y enlaza con loopback.
- Evaluación síncrona. No hay cola distribuida, recuperación automática de un job interrumpido por caída del proceso, migraciones generales ni gestión de conservación multiusuario. Son trabajo de endurecimiento antes de cualquier servicio persistente público.
- Una observación discrepante suspende la recomendación; recalcular o restaurar no levanta esa suspensión. Resolver/admitir un modelo corregido requiere trabajo explícito posterior: D1 no incluye una operación que certifique su revisión empírica.
- Identificar caso real, responsable y observaciones autorizadas corresponde a Pedro y al responsable de dominio que designe. El protocolo mínimo está preparado en `docs/EMPIRICAL_PROTOCOL.md`; no se inventaron participantes, datos ni calibración.
- La comprensión por usuarios permanece no evaluada. La revisión de agentes y el navegador no cuentan como personas participantes.

No quedan hallazgos bloqueantes conocidos dentro del alcance técnico comprobado. Las dependencias empíricas y humanas siguen abiertas y no se ocultan bajo una aprobación técnica.
