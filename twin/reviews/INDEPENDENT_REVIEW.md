# D1 — Revisión independiente de evidencia y calidad

Revisor: agente `calidad_d1`. Fecha: 12 de octubre de 2026. Base recibida por el integrador: checkout mínimo de `deploy/staging`, SHA `a8af0502a022aa2c3d87c4e7da29be63e50717a6`. Esta revisión no autentica un servicio desplegado ni afirma revisión íntegra del repositorio.

## Dictamen y alcance

**Recorrido de dominio, compilación, núcleo y API local: aprobado en las pruebas ejecutadas.** La recepción integral corresponde al integrador y requiere además comprobar el frontend conectado. No hay comprensión humana ni validación empírica acreditadas. No se produjo recibo R2/RC01: D1 emite un nuevo sobre de producto que conserva los Input/Result FP1 originales y los recibos de verificación.

Se leyeron únicamente el encargo D1 aprobado, las secciones pertinentes del diseño matemático y arquitectura, contratos/código del núcleo relevantes, y el incremento nuevo. Las cifras esperadas se transcribieron de las tablas aprobadas; no se obtuvo el oráculo de las funciones bajo prueba.

## Pruebas ejecutadas

Comando desde la raíz del repositorio, con Flask recibido en el entorno de dependencias:

```bash
PYTHONPATH=/workspace/scratch/1e20f9e887c2/tmp/d1/python_deps:twin:kernel:product_local:consumer_views:protocols python twin/tests/test_acceptance.py
```

Resultado observado: **20 pruebas aprobadas, 0 fallos, 24.276 segundos**. Tiempo incidental de esta ejecución, no benchmark. Las pruebas de servicio reutilizan, dentro del mismo proceso, resultados previamente ejecutados y verificados por el núcleo; la prueba `test_default_evaluator_http_vertical_path_and_lossless_consumers` usa expresamente el compilador real sin inyección. El caché no contiene resultados esperados prefabricados.

| Grupo | Pruebas | Evidencia que discrimina |
|---|---:|---|
| Dominio sintético | 6 | Nueve filas C/R/E y nueve C/R/E′; balance compartido; calendario de formación/verificación; historia común antes de día10; monitor persistente; entradas no admitidas; rama de masa cero |
| Núcleo y compilación | 6 | PVS 1/2,1,5/6 y E′=1; CAG acc por identidades en ambas modalidades; bienestar histórico; frontera con norma y sin norma; byte binding; masa indeterminada positiva |
| Expediente y HTTP | 8 | Camino real v1→v2; export/job/compare equivalentes; confirmación sintética; dos escritores concurrentes; job histórico en vuelo; restauración; observaciones; fallo operacional y JSON/local boundary |

Oráculos sustantivos: E′-HA usa 18 L, A310/B180 min, s10=2, q14=q2; E-HA usa 15 L, A300/B190, s10=0. La suma de tiempos es 490 min en ambas y la tarea cambia: la suma no explica bienestar/seguridad. C-H, C-HA y E-HA recuperan s11=s14=2 sin borrar el fallo de trayectoria.

CAG posible E={q0,q1,q2}; robusto E={q0,q1}. E′ acredita ambos conjuntos {q0,q1,q2}. q0 queda separado del repertorio adicional. Las ramas de probabilidad cero permanecen en las restricciones universales y CAG robusto. Cambiar HA a masa cero permite PVS(E)=1 sin convertir E en universalmente factible.

Con norma universal, solo R resulta factible en la primera familia. Después de la edición, R y E′ son factibles y frontera; no hay selección única. Sin norma universal, la frontera robusta C/R no produce ganador. El perfil histórico C/R es incomparable y R domina E solo en el perfil limitado declarado.

Mutación de semántica E/HA: masa positiva indeterminada de 1/6 se conserva, el vector pasa a (5/6,0,1/6) y PVS queda `OUTSIDE_DOMAIN`. No se renormaliza. El adaptador D1, por su parte, rechaza un modelo sin ley o fuera de su perfil antes de fabricar valores.

Se ejecutaron además tres guardas existentes del núcleo, todas aprobadas: `CF026_positive_undecided_mass_not_renormalized`, `CF027_zero_mass_keeps_failure_mixed_or_absent_leaf` y `test_changed_input_whitespace_changes_digest_and_missing_input_is_not_accepted`. Dos invocaciones iniciales usaron un nombre equivocado de clase de unittest; se corrigió la invocación. No fueron fallos del producto ni se contaron como pruebas aprobadas.

## Hallazgo corregido durante la revisión

**D1-Q01 — Contraste sin predicción congelada (prioridad alta, corregido y probado).** La implementación inicial recalculaba la predicción al recibir la observación y permitía observar sin una evaluación previa. Eso no aportaba una referencia a una predicción congelada.

Corrección del equipo de arquitectura: exigir evaluación `completed` de la versión referida; leer el valor del resultado conservado; registrar `prediction_job_id`, `prediction_input_digest` y `prediction_model_sha256`. Rechaza la operación sin evaluación con `frozen_prediction_required`, sin crear una revisión parcial. La comparación histórica se rotula retrospectiva cuando el tiempo observado antecede al recibo. La prueba preserva el resultado antiguo, registra la discrepancia exacta y suspende la recomendación de la nueva revisión hasta revisar el modelo. Una coincidencia explícitamente no valida el modelo.

Revisión semántica adicional del frontend: se comprobó por lectura que los accesores usan `canonical_results.policies/decision`, que la observación se envía al servicio con fecha explícita y que la vista exige la versión actual al recuperar resultados. Se pidieron y comprobaron dos precisiones: la ayuda de receta acc exige conservación en cada transición hasta el logro, y la comparación antes/después conserva la suspensión por discrepancia en cada lado. Esta lectura no sustituye la ejecución del navegador ni el ensayo humano.

## Límites recibidos y seguimiento

1. D1 es un adaptador local cerrado para el semillero sintético de 14 días. La entrada lingüística reconoce el dominio y propone una plantilla explícita; no reconstruye libremente cualquier realidad ni estima una ley empírica. Relatos externos mantienen obligación de capacidad de producto.
2. El servicio conserva Input/Result FP1, integración y verificación originales, sin extensiones silenciosas a sus esquemas. `rc01_receipt=null` y `NOT_PRODUCED_NEW_FP1_PRODUCT_ENVELOPE` informan que el sobre nuevo no es RC01; ese null pertenece al producto, no a una celda FP1.
3. La verificación nativa recalcula con constructores compartidos con el evaluador. No es una segunda implementación matemática independiente; las tablas del diseño y mutaciones de esta revisión aportan comprobaciones diferentes pero no una prueba universal.
4. La equivalencia técnica se comprobó en las respuestas HTTP de evaluación, recuperación, exportación y comparación. La comprensión por personas, legibilidad móvil y comportamiento real del frontend se reciben por evidencia separada del integrador/UX. Leer el mismo JSON no acredita por sí solo que una persona lo entienda.
5. No hay adquisición externa, intervención física, MCP, despliegue ni publicación por D1. No se alteró el núcleo. Los errores operacionales dejan un job fallido sin valor de evaluación; no se traducen en PVS cero o inviabilidad.
6. Empírico y comprensión: **no ejecutados**. `twin/docs/EMPIRICAL_PROTOCOL.md` prepara ingreso mínimo, responsables, predicciones congeladas, observaciones y criterios. Los datos usados en los tests se identifican como pruebas y no son observaciones de campo.

La revisión no declara completado el plan global ni cierra F6A. El integrador debe conservar esta separación al emitir el acta y el siguiente encargo.
