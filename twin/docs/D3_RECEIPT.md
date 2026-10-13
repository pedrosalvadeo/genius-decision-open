# Recepción D3 — producto configurable y operación local

Fecha: 2026-10-13 UTC. Rama: `work/d3-producto-operativo-2026-10-13`, derivada de D1 `dbd73fae4a3a7f326d2e2e9c0d382220d1f4d92a`.

**Recibido dentro del alcance local y de montaje autenticado probado localmente.** La validación real queda pospuesta y no bloquea el avance hacia la puesta en marcha. No se desplegó D3 ni se modificaron servicios o variables remotas. La rama staging no forma parte de esta entrega.

## Qué funciona

El constructor permite configurar un modelo finito de recursos, actores, capacidades, acciones, planes, escenarios y condiciones temporales. Los ejemplos de cuidado y asignación de tiempo usan horizontes, unidades y tareas diferentes. Las transiciones calculan balances y condiciones; la traducción ejecuta y verifica el núcleo real. Se conserva bienestar por portador/momento, CAG por firmas de capacidades y cumplimiento de la tarea durante la trayectoria. Falta de ley, indeterminación, masa cero e incomparabilidad mantienen sus estados propios.

La persona puede guardar un borrador, revisar y confirmar premisas, evaluar, cambiar condiciones, comparar, restaurar mediante otra versión, reabrir y exportar. La API entrega los mismos resultados canónicos y recibos nativos. El semillero D1 conserva su recorrido y su suspensión por discrepancia. La UI maneja conflictos de borrador sin perder los cambios locales.

El montaje beta agrega acceso con cuenta/CSRF o clave Bearer, aislamiento por usuario, límites, recuperación, exportación de cuenta, borrado, retención y restauración privada de las nuevas bases. El lanzador local mantiene exclusividad sobre la base; un segundo proceso no interrumpe un trabajo vivo. Los compiladores hijos tienen límites y terminan si muere su padre.

## Evidencia ejecutada

| Comprobación | Resultado |
|---|---:|
| Suite Python del gemelo, D1 + D3 | 65 / 65 |
| Suite beta heredada + integración D3 | 19 / 19 |
| Nueva prueba posterior de cuotas y límites anunciados | 1 / 1 |
| Recuperación SQLite heredada | 3 / 3 |
| Repetición dirigida de backup/restore de gemelos tras cierre del manifiesto | 1 / 1, incluida ya entre las pruebas anteriores |
| Navegador D3, edición/conflicto/restore y dos modelos | 67 / 67 |
| Navegador D1, regresión | 42 / 42 |
| Navegador autenticado beta, cookies/CSRF/API/recarga | 13 / 13 |

Los grupos Python cubren 88 pruebas distintas; las repeticiones dirigidas no aumentan ese total. Los navegadores cubren 122 comprobaciones y tamaños de 320, 390 y 1440 px, sin desbordes de página ni errores JS o solicitudes externas. El montaje autenticado también pasó sin errores de CSP. Se inspeccionaron capturas del constructor y de resultados en escritorio/móvil.

Los oráculos independientes comprueban conservación, atomicidad, trayectoria frente a endpoint, ley ausente, masa cero adversa, umbral desconocido, conservación CAG, diferencia entre tarea operacional y vida, certificados nativos y flujo HTTP. La prueba real de muerte del padre mantiene la entrada del hijo abierta desde otro proceso para evitar confundir el cierre de entrada con la terminación por `prctl`.

Los fallos detectados durante la recepción se resolvieron: tombstone anterior a validación de DELETE, recuperación local sin exclusividad, nodos de navegación incorrectos, ancho de selector en móvil, conflictos de borrador y patrón HTML de usuario incompatible con el navegador usado. Los errores iniciales de la regresión beta se debían a fixtures ausentes en el checkout; se repusieron desde el commit exacto, sin alterar sus bytes. Se adaptaron dos expectativas D1 que correspondían a la antigua ausencia del constructor, conservando sus cálculos y controles.

Evidencia de navegador y log Python en `twin/reviews/D3_BROWSER_*.json` y `D3_PYTHON_TEST_LOG.txt`; revisión independiente en `D3_INDEPENDENT_REVIEW.md`. Los tests conservados permiten repetir las comprobaciones. Los fixtures, cuentas, claves y relatos usados son de prueba.

## Límites conservados

No se construyó la imagen Docker en este entorno ni se recibió un despliegue nuevo. El empaquetado y arranque están preparados para la siguiente recepción en infraestructura. No hay validación empírica, estudio con participantes ni datos de campo. STOCKFLOW aún no tiene observaciones/revisión de discrepancias y el criterio funcional permanece neutral, según su contrato. El lenguaje natural conserva intención; la persona configura y confirma las reglas. No se afirma modelización universal, acción física ni recibo RC01.

Próximo trabajo: recibir este montaje en el entorno autorizado y continuar ampliando la revisión y construcción asistida, conforme a `PRODUCT_ROADMAP.md`. El caso real no es una condición de esa continuidad.
