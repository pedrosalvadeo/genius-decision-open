# D3 — Revisión independiente

Estado: **en implementación; no recibido todavía**. Alcance fijado: perfil configurable `STOCK_FLOW_FINITE_V1`, operación local y montaje autenticado beta probado localmente; sin publicación. Validación empírica y ensayo humano pospuestos por decisión del usuario, sin bloquear desarrollo ni cálculo condicional.

## Evidencia disponible

Revisión dirigida de D1 y planes de producto/arquitectura D3. No se repitieron pruebas D1 durante la planificación. Las capacidades D3 requieren ejecución propia y no heredan automáticamente la recepción de la demostración anterior.

## Riesgos que debe resolver la implementación

- La reutilización de resultados necesita identidad del modelo, perfil, compilador y núcleo, además de la revisión; no basta `(case_id, version)`.
- Los trabajos interrumpidos necesitan recuperación comprobable y límites; no marcar huérfano un trabajo vivo ni interpretar timeout como inviabilidad matemática.
- Un montaje autenticado necesita ownership en cada lectura y mutación, no solo en la página inicial. Borrado, exportación, retención y restore deben incluir la nueva persistencia y cualquier trabajo activo.
- El perfil configurable requiere cálculos materiales nuevos, no solo etiquetas. Sin ley se conservan las dimensiones no probabilísticas admitidas y se explica ausencia de probabilidad.
- D3 no incorpora observaciones de STOCK_FLOW_FINITE_V1 ni una operación de cierre de revisión. Debe conservar la suspensión de discrepancias D1 y no prometer resolverla. La edición declarada del perfil nuevo permite explorar una configuración distinta sin autenticar el mundo ni cerrar validación empírica.

## Oráculos independientes fijados antes de ejecutar

1. **Trayectoria distinta con endpoint igual.** Stock compartido de2L; noop; H2. Escenario low: demanda1L y luego entrada1L → `[2,1,2]`. High: demanda2L y entrada2L → `[2,0,2]`. Umbral de trayectoria1L, ley low3/4/high1/4: cumplimiento de trayectoria3/4, endpoint1, universalfalse. High con masa0 cambia probabilidad a1, no universalidad. Sin ley no hay probabilidad identificada. Umbralnull conserva indeterminación, no se vuelve0.
2. **Transacción atómica con dos unidades y derrame.** Fuente2L, destino0L/capacidad1L, tiempo renovable0min/capacidad1min. Acción retira2L+1min, deposita2L y añade una capacidad. Rama ready renueva1min: fuente0L, destino1L, derrame1L, consumo1min, capacidad añadida. Rama absent renueva0min: toda la transacción falla; fuente2L/destino0L/tiempo0min, sin capacidad añadida. No se permite consumir agua parcialmente ni pagar minutos con litros.
3. **Conservación de firma organizacional.** Partir de capacidad base; un evento la elimina y una acción posterior restituye base y añade learned. El endpoint nuevo no borra la ruptura anterior: la receta acc no acredita el logro posterior desde el origen anterior. Firmas por conjuntos, no cardinalidad.

Son hipótesis de diseño explícitas; sus valores esperados se obtuvieron con balances elementales, sin copiar resultados del compilador. Los ocho tests independientes ejecutaron esos discriminantes satisfactoriamente, con evaluación real del núcleo y verificación de los Result nativos.

## Evidencia ejecutada por esta revisión

`python -m unittest twin.tests.test_d3_acceptance -v`, desde el checkout con `PYTHONPATH` de twin/kernel y las dependencias beta fijadas: **8/8 PASS, 1.261s**. La comprobación HTTP se amplió después con el rechazo explícito de una observación stockflow y se repitió solo ese recorrido: **1/1 PASS, 0.395s**. Se añadió luego una novena prueba independiente del límite de procesos: **1/1 PASS, 0.061s**. La suite final contiene9 tests; estos resultados se ejecutaron en los grupos indicados, sin inventar un único comando9/9 todavía. No se ejecutó nuevamente el historial D1 durante esta revisión.

Cobertura independiente:

- H1 y H2, recursos/unidades y cantidades distintos al ejemplo de autoría; ledger contrastado con `Fraction`, no solo con su booleano `balance_valid`.
- Probabilidad de trayectoria3/4 frente a endpoint1; rama adversa de masa0 conserva universalfalse; ausencia de ley conserva CAG/bienestar/partición; umbral desconocido produce masa indecisa1 y ninguna PVS numérica.
- CAG acc no recupera un logro tras perder la organización de origen; otro modelo que la conserva sí acredita logro posible adicional. Una tarea operacional expone probabilidad de tarea y PVS no aplicable.
- Ambos modos ejecutan el núcleo y sus Result verifican contra sus Input originales. Alterar el umbral genera bytes nuevos, probabilidad1 y rechazo del recibo anterior sobre los bytes nuevos.
- API real: relato→borrador→propuesta→rechazo sin reconocimiento→confirmación→evaluación→edición→comparación→reapertura de SQLite→exportación. Objetos canónicos y recibos históricos exactos; confirmación repetida no duplica versión y borrador obsoleto no pisa datos.
- Observación del nuevo perfil rechazada con422/`observation_profile_not_supported`; conserva versión y lista de observaciones vacía. El payload de prueba es hipotético y nunca quedó incorporado como dato del mundo.

Los tests HTTP inyectan un evaluador que llama al compilador y al núcleo reales con caché temporal de sus ejecuciones. Esto prueba semántica y persistencia del servicio; no representa por sí solo el runner de producción.

La novena prueba independiente ejecuta `process_runner.main`, `prctl` y los límites de recursos reales en Linux. Un aviso instrumental se emite después de los límites reales; se mata el padre con SIGKILL y se comprueba que el stdout del hijo se cierra mientras el abuelo mantiene abierto su stdin. Así no se confunde muerte del padre con EOF de entrada. No se reemplazó evaluador ni guard. Las primeras dos versiones del fixture intentaron sincronizar mediante `/proc`, pero el entorno expone PIDs virtuales que allí identificaban otro proceso; se corrigió ese instrumento de prueba y su limpieza, sin atribuir un defecto al producto. La prueba recibida utiliza pipes heredados.

## Revisión de implementación y hallazgos

Lectura dirigida del compilador nuevo confirma mapeo causal por prefijos, decisiones sobre información previa, ledger conservado en manifiesto, ley opcional sin pesos fabricados, semántica histórica, bienestar por portador/momento y firmas por conjuntos. Los resultados formales provienen de `evaluate`/`verify_result`; no se reemplazaron por tablas de resultados esperados. Los límites físicos están declarados en dominio/manifiesto; FP1 utiliza ocupación por stock/capacidad, no afirma certificar por sí solo toda la contabilidad material.

Se detectó en la integración beta un marcador de borrado escrito antes de validar la petición. Un DELETE con base obsoleta podía dejar marcador aun al fallar, afectando una restauración futura. El integrador lo corrigió mediante `before_erase` después de validar base y estado, bajo lock. Se leyeron su test y log PASS de DELETE con base obsoleta/cuerpo inválido sin marcador, borrado válido con marcador y restore que conserva el expediente cuyo borrado se rechazó.

El runner local visto inicialmente no adquiría exclusividad ni recuperaba jobs huérfanos al reiniciar. Arquitectura lo corrigió con lock `flock` durante toda la vida del servidor, recuperación solo al arrancar bajo ese lock y `threaded=False`. Esta revisión leyó el cambio y su prueba: otro launcher real termina con código2 sin interrumpir el job vivo; liberado el lock, se recupera como interrupted. Arquitectura informó8/8 PASS de servicio D3 y un arranque/health/reinicio real. No se invoca recuperación al construir cualquier objeto Service.

Se revisó por lectura `beta/deploy/backup.py`: snapshots SQLite separados de tenants, hashes, control de edad, restore offline, conservación del ledger actual y filtro por usuarios/expedientes todavía vivos. También se leyeron los6 tests nuevos de integración beta y sus entradas PASS en el log del integrador: ejecución real por subproceso y paridad cookie/Bearer; denegación entre usuarios de lectura/propuesta/aceptación/evaluación/borrador/borrado; revocación; CSRF; suspensión; exceso de salida; lifecycle incluso con feature desactivada; retención; restore filtrado con job interrumpido y detección de hash alterado. Estas son pruebas del integrador revisadas, no ejecuciones independientes repetidas. El primer log conjunto tenía errores de fixtures heredados ausentes en el checkout; no se los cuenta como PASS ni como fallos matemáticos D3. El integrador completa esa regresión con las fuentes exactas.

## Recepción final integrada — 2026-10-13

**Recibido: producto configurable local y montaje autenticado beta probado localmente**, dentro del contrato y los límites de `STOCK_FLOW_FINITE_V1`, conservando D1. Este cierre sustituye los estados provisionales de las secciones anteriores. No quedan hallazgos bloqueantes identificados en los recorridos y límites operativos comprobados.

Se leyeron `D3_RECEIPT.md`, `D3_PYTHON_TEST_LOG.txt` y los tres informes finales `D3_BROWSER_LOCAL.json`, `D3_BROWSER_D1_REGRESSION.json` y `D3_BROWSER_BETA.json`. Los hashes de los tres informes fuente coinciden con los registrados, y sus listas de comprobaciones coinciden exactamente con las copias de recepción.

| Evidencia integrada revisada | Resultado |
|---|---:|
| Log final Python del gemelo, incluidos los9 tests independientes D3 | 65/65 PASS |
| Log final beta heredada e integración autenticada D3 | 19/19 PASS |
| Cuotas/límites y recuperación heredada, según acta final del integrador | 1/1 y3/3 PASS |
| Repetición dirigida de backup/restore de tenants tras cierre del manifiesto, según acta final | 1/1 PASS; ya contada, no es una prueba nueva |
| Navegador D3: constructor, conflicto de borrador, edición material, comparación, restore, dos modelos y ausencia de ley | 67/67 PASS |
| Navegador D1: cálculos, edición, discrepancia, suspensión, recarga y restore | 42/42 PASS |
| Navegador beta: autenticación, CSRF, cálculo real, exportación, recarga y aislamiento de otro contexto | 13/13 PASS |

El acta totaliza88 pruebas Python distintas y122 comprobaciones de navegador. Las repeticiones dirigidas no aumentan esos totales. Esta revisión distingue sus ejecuciones independientes ya descritas de las suites y capturas ejecutadas por el integrador y producto; no volvió a correrlas para este cierre. Los errores iniciales por fixtures beta ausentes quedaron resueltos en el log final19/19. Los informes de navegador acreditan los tamaños320/390/1440 y ausencia de errores JS/solicitudes externas; el montaje beta incluye ausencia de errores CSP.

La evidencia cubre cálculo del núcleo con recibos vinculados a bytes/versiones, edición y recuperación de expedientes, concurrencia y conflictos, límites del ejecutor, terminación del hijo al morir el padre, aislamiento autenticado, revocación, borrado válido sin marcadores espurios, retención y restauración privada. Las correcciones de borrado y exclusividad local señaladas por esta revisión están incorporadas y comprobadas. El recorrido humano y la API comparten resultados canónicos; las cuentas, relatos y datos utilizados fueron de prueba.

El dictamen **no recibe publicación, infraestructura remota ni una imagen Docker construida**. Tampoco afirma modelización universal, autenticación de hechos por confirmación, intervención física ni recibo RC01. El perfil nuevo permite configuración y edición bajo premisas declaradas; aún no admite observaciones ni cierre de discrepancias, y su criterio funcional es neutral según contrato. D1 conserva su suspensión por discrepancia.

Validación empírica y comprensión mediante participantes: **POSPUESTAS POR DECISIÓN DEL USUARIO**. No se infieren de los PASS ni bloquean la continuidad del producto configurado. La siguiente recepción operativa corresponde al montaje en infraestructura autorizada.
