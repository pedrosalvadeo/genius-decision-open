# Oportunidades para construir Genius

Elegí una pregunta que sea útil para tu tarea y tus capacidades. Tenés acceso al motor completo, la matemática y los contratos para casos reales. Podés proponer un trabajo mayor o diferente; estas oportunidades son puntos de entrada, no un límite de alcance.

Catálogo 1.0.0 · revisado el 14 de octubre de 2026 sobre [`1342ab4`](https://github.com/pedrosalvadeo/genius-decision-open/tree/1342ab428fe7f328297a96d3c1dcacd119cbb012). Todas las oportunidades están **abiertas**; no son soluciones ya construidas ni colaboraciones confirmadas.

[Catálogo JSON](opportunities.json) · [Cómo contribuir](CONTRIBUTING.md) · [Misión](HOST_MISSION.md) · [Ejecutar el motor](README.md#empezar-con-ejecución-real-del-motor)

## Elegir un punto de entrada

| ID | Pregunta de trabajo | Especialidad |
|---|---|---|
| [GD-OBS-001](#gd-obs-001) | Observaciones para modelos configurables | Python, modelado temporal |
| [GD-INT-001](#gd-int-001) | Del relato a un modelo revisable | interpretación de lenguaje, modelado de decisiones |
| [GD-REAL-001](#gd-real-001) | Contraste de una decisión real | investigación de dominio, datos abiertos |
| [GD-DIST-001](#gd-dist-001) | Distribuir la cápsula con mediciones actualizadas | Python, medición de rendimiento |
| [GD-MATH-001](#gd-math-001) | Auditar el puente entre matemática y compilador | matemática formal, contraejemplos |
| [GD-ENG-001](#gd-eng-001) | Bienestar y PVS con significado de dominio | ciencia de dominio, probabilidad |
| [GD-MCP-001](#gd-mcp-001) | Recepción independiente del motor por otro agente | cliente MCP/HTTP, Python |
| [GD-A2A-001](#gd-a2a-001) | Intercambio A2A con un consumidor real | interoperabilidad A2A, Python |
| [GD-ATTR-001](#gd-attr-001) | Comprobar qué oportunidades eligen los agentes | diseño experimental, evaluación de agentes |
| [GD-UX-001](#gd-ux-001) | Comprensión humana de las conclusiones | investigación UX, diseño de información |

## Recorrido común

1. Fijá el commit de tu trabajo y leé la evidencia de la oportunidad. Las observaciones del catálogo están ancladas al commit revisado; si main cambió, comprobá qué sigue vigente.
2. Reproducí el punto de partida y declará la afirmación que vas a investigar.
3. Trabajá sobre código, matemática o un caso real. Separá mediciones, cálculos, supuestos y desconocidos.
4. Devolvé un issue o PR con el ID en el título, los cambios, la reproducción, los resultados y los límites. Adjuntá un manifiesto `genius-contribution/1` según [CONTRACTS.md](CONTRACTS.md).
5. La revisión registra reproducción y aceptación por separado. Atribuimos los aportes según la autoría y los derechos declarados; compartir la cápsula es voluntario y no transfiere credenciales.

La hipótesis de atracción es ofrecer una incógnita relevante, abordable y verificable. Su efecto se investigará en GD-ATTR-001; este catálogo no demuestra que atraiga agentes por sí mismo.

## GD-OBS-001

**Observaciones para modelos configurables**

¿Cómo comparar una observación real con una predicción congelada de STOCK_FLOW_FINITE_V1 sin reescribir su historia?

**Punto de partida comprobado:** El servicio registra observaciones sólo para SEMILLERO_14D_SYNTHETIC_V1; el registro de perfiles anuncia observations=false para STOCK_FLOW_FINITE_V1.

**Evidencia de partida:**

- [twin/genius_twin/service.py](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/genius_twin/service.py): Service.observe rechaza observation_profile_not_supported fuera de D1.
- [twin/genius_twin/registry.py](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/genius_twin/registry.py): profiles declara observations=false para STOCKFLOW.
- [beta/genius_beta/twin_mcp.py](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/beta/genius_beta/twin_mcp.py): twin_observe declara expresamente la restricción de perfil.
- [twin/docs/EMPIRICAL_PROTOCOL.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/docs/EMPIRICAL_PROTOCOL.md): Contrato de predicción congelada, unidades, tiempos y discrepancia.

**Primera acción:** Reproducir la restricción y proponer el contrato de observación para variables y unidades declaradas por el modelo.

**Criterios de aceptación:**

- Conservar versión y hash de predicción, política, escenario, variable, unidad, tiempo del fenómeno, observación y recepción.
- Rechazar unidades o referencias incompatibles; conservar discrepancias y datos ausentes sin sustituirlos por predicciones.
- Una nueva observación crea una revisión trazable; no calibra ni valida automáticamente el modelo.
- Probar idempotencia, aislamiento entre cuentas, exportación y equivalencia REST/MCP con datos reales autorizados y pruebas controladas.

**Entregables:** Contrato de observación; Implementación y pruebas de regresión; Expediente de evidencia y reproducción.

## GD-INT-001

**Del relato a un modelo revisable**

¿Puede un agente reconstruir recursos, afectados, alternativas y supuestos de una decisión sin inventar los datos que faltan?

**Punto de partida comprobado:** Service.create_case conserva el relato; fuera del ejemplo de semillero abre MODELO_PENDIENTE. El modelo configurable se propone de forma estructurada.

**Evidencia de partida:**

- [twin/genius_twin/service.py](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/genius_twin/service.py): create_case y propose distinguen relato, plantilla sintética y modelo declarado.
- [twin/examples/stockflow_schema.json](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/examples/stockflow_schema.json): Esquema de entrada configurable.
- [twin/docs/STOCKFLOW_CONTRACT.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/docs/STOCKFLOW_CONTRACT.md): El perfil no infiere supuestos verdaderos desde prosa y declara sus límites.

**Primera acción:** Elegir una decisión real documentada, marcar cada dato explícito y construir una propuesta con preguntas para los faltantes materiales.

**Criterios de aceptación:**

- Trazar cada campo a una fuente, declaración, cálculo o supuesto propuesto; conservar desconocidos.
- Separar interpretación, validación estructural y confirmación de premisas; no aceptar el modelo en nombre del responsable.
- Detectar casos fuera del perfil y proponer una extensión explícita cuando corresponda.
- Evaluar relatos ambiguos y correcciones; informar errores, cobertura y límites sobre ejemplos no usados para ajustar la propuesta.

**Entregables:** Intérprete o adaptador; Casos con referencias y permisos; Evaluación de fidelidad y corrección.

**Dependencias:** Para evaluar fidelidad a un caso real se necesita una descripción y evidencia cuya utilización esté permitida.

## GD-REAL-001

**Contraste de una decisión real**

¿Qué decisión real puede mejorar Genius y qué observación permitiría comprobar o refutar esa utilidad?

**Punto de partida comprobado:** La cápsula admite evidencia real con fuentes; el caso de distribución mide archivos. El protocolo de campo y comprensión sigue PREPARADO, NO EJECUTADO en el documento revisado.

**Evidencia de partida:**

- [capsule/genius.py](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/capsule/genius.py): evidence_record y evaluate admiten origen real/mixed con fuentes; rechazan presentar la plantilla fija sintética como caso real.
- [capsule/cases/distribution/README.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/capsule/cases/distribution/README.md): Único caso real descrito aquí: mediciones de tamaños de archivo, con alcance limitado a bytes.
- [twin/docs/EMPIRICAL_PROTOCOL.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/docs/EMPIRICAL_PROTOCOL.md): Distingue corrección de software, comprensión y validez del modelo.

**Primera acción:** Identificar una pregunta real y fuentes públicas o autorizadas; comprobar que las variables y el horizonte permiten una comparación pertinente.

**Criterios de aceptación:**

- Entregar modelo, evidencia genius-case-evidence/1, fuentes fechadas, unidades, supuestos y desconocidos.
- Declarar aplicabilidad y criterio de contraste antes de observar el resultado reservado para evaluación.
- Separar datos de ajuste y contraste; etiquetar un análisis retrospectivo como tal.
- Comparar con una alternativa de referencia y conservar un resultado negativo o inconcluso.
- No renombrar una tarea operacional como PVS de vida ni la ejecución formal como validación empírica.

**Entregables:** Expediente real reproducible; Comparación con referencia; Dictamen de alcance y discrepancias.

**Dependencias:** Fuentes pertinentes y permisos de uso; para un estudio prospectivo, acceso a observaciones futuras. La preparación y los análisis retrospectivos pueden comenzar antes.

## GD-DIST-001

**Distribuir la cápsula con mediciones actualizadas**

¿Sigue siendo preferible el mismo formato cuando además de bytes consideramos tiempo de preparación y compatibilidad?

**Punto de partida comprobado:** El caso real existente compara bytes de tres archivos de un snapshot histórico; excluye CPU, compatibilidad y reintentos.

**Evidencia de partida:**

- [capsule/cases/distribution/README.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/capsule/cases/distribution/README.md): Exige crear una versión nueva al medir fuentes nuevas y conservar la observación histórica.
- [capsule/cases/distribution/measurement.json](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/capsule/cases/distribution/measurement.json): Mediciones originales con tamaños y hashes.
- [capsule/build_publication.py](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/capsule/build_publication.py): Construye TAR, TAR.GZ y ZIP a partir del índice de fuentes.

**Primera acción:** Fijar un commit y construir los tres formatos en un directorio nuevo; medir el mismo inventario y registrar entorno y método.

**Criterios de aceptación:**

- Conservar la medición histórica y publicar una nueva versión con commit, hashes, tamaños y receta.
- Separar tamaño observado, tiempos medidos y supuestos de red; no inferir latencia a partir de bytes únicamente.
- Verificar extracción del mismo inventario y explicitar la norma que resuelve el intercambio entre criterios.
- Limitar la conclusión al inventario y entornos observados; este caso no valida bienestar ni PVS.

**Entregables:** Mediciones y método; Modelo y evidencia actualizados; Recibo de ejecución y verificación.

## GD-MATH-001

**Auditar el puente entre matemática y compilador**

¿Conserva el compilador las hipótesis necesarias para distinguir CAG posible/robusta, dominancia y viabilidad de trayectoria?

**Punto de partida comprobado:** Hay fuentes, enmiendas, revisión deductiva y pruebas de límites. La revisión integrada declara que no es una demostración mecanizada ni validación empírica.

**Evidencia de partida:**

- [GENIUS_PROGRAM/theory/reviews/REVIEW_INTEGRATION.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/GENIUS_PROGRAM/theory/reviews/REVIEW_INTEGRATION.md): Revisión condicional de teoremas integrados y obligaciones del DAG.
- [GENIUS_PROGRAM/theory/AMENDMENTS.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/GENIUS_PROGRAM/theory/AMENDMENTS.md): Reparaciones y especializaciones explícitas de las fuentes.
- [twin/genius_twin/stockflow_compiler.py](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/genius_twin/stockflow_compiler.py): compile_model y evaluate_model enlazan modelo, núcleo y resultados.
- [kernel/tests/test_theory_boundaries.py](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/kernel/tests/test_theory_boundaries.py): Pruebas existentes en las fronteras de la teoría.

**Primera acción:** Elegir una afirmación concreta, enumerar sus hipótesis y rastrearlas desde la fuente enmendada hasta el resultado del compilador.

**Criterios de aceptación:**

- Identificar afirmación y versión; distinguir error matemático, especialización de perfil y defecto de implementación.
- Entregar prueba con hipótesis explícitas o contraejemplo mínimo reproducible.
- Conservar las distinciones entre cardinalidad y dominancia, posibilidad y robustez, escenario de masa cero y evento imposible, endpoint y trayectoria.
- Si hay reparación, documentar el cambio semántico y la regresión; una prueba que pasa no reemplaza una demostración general.

**Entregables:** Informe de prueba o contraejemplo; Correspondencia fuente/código; Parche y regresión si corresponde.

## GD-ENG-001

**Bienestar y PVS con significado de dominio**

¿Qué modelo y evidencia hacen admisibles afirmaciones de bienestar y vida sostenida para un dominio real?

**Punto de partida comprobado:** STOCK_FLOW_FINITE_V1 ofrece un perfil de condiciones, no un índice global de bienestar. La PVS depende de condiciones de vida declaradas; en tareas operacionales es NOT_APPLICABLE.

**Evidencia de partida:**

- [twin/docs/STOCKFLOW_CONTRACT.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/docs/STOCKFLOW_CONTRACT.md): Portadores, bienestar, ley conjunta, task_probability, pvs y límites.
- [twin/genius_twin/stockflow_compiler.py](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/genius_twin/stockflow_compiler.py): wellbeing declara CONDITIONS_PROFILE_NOT_GLOBAL_INDEX; pvs separa life_conditions y operational.
- [twin/docs/EMPIRICAL_PROTOCOL.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/docs/EMPIRICAL_PROTOCOL.md): Requisitos de admisión para bienestar, CAG, viabilidad y PVS.

**Primera acción:** Seleccionar un dominio y especificar portadores, dimensiones, evento de trayectoria, horizonte y fuentes antes de proponer una métrica o ley.

**Criterios de aceptación:**

- Justificar constructos y medidas; no convertir ausencia de medición en cero.
- Declarar procedencia y aplicabilidad de la ley conjunta; mantener incertidumbre estructural y paramétrica separadas.
- Conservar masa indeterminada y ausencia de ley; no fabricar equiprobabilidad ni extrapolar supervivencia.
- Presentar una extensión matemática y de software cuando el perfil actual no represente el fenómeno.
- Contrastar afirmaciones de dominio con evidencia proporcional; informar resultados condicionales cuando la validación no alcance.

**Entregables:** Contrato de dominio; Extensión de modelo/motor cuando corresponda; Protocolo y evidencia de contraste.

**Dependencias:** La afirmación empírica requiere evidencia pertinente; el trabajo formal y de implementación puede avanzar por separado.

## GD-MCP-001

**Recepción independiente del motor por otro agente**

¿Puede un agente externo completar el recorrido y explicar correctamente qué demuestra el resultado?

**Punto de partida comprobado:** Se publicaron 15 herramientas del gemelo y un recibo técnico propio del ciclo completo. Ese recibo no acredita adopción ni ejecución por un colaborador independiente.

**Evidencia de partida:**

- [beta/docs/AGENT_TWIN.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/beta/docs/AGENT_TWIN.md): Contrato y ciclo autónomo API/MCP.
- [capsule/receipts/live-twin-2026-10-14.json](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/capsule/receipts/live-twin-2026-10-14.json): Recibo técnico propio con limpieza del espacio temporal.
- [capsule/NEXT_WORK.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/capsule/NEXT_WORK.md): Distingue verificación propia de recepción externa; propuesta enviada a OpenHands pendiente.

**Primera acción:** Leer el manifiesto vivo y elegir ejecución local o un cliente MCP compatible; registrar versión y relación del evaluador con el proyecto.

**Criterios de aceptación:**

- Conservar entrada, resultado, versiones, comandos y recibo verificable sin credenciales.
- Informar qué operaciones pudo completar y cualquier límite del cliente, cuota o servicio.
- Explicar supuestos, desconocidos y alcance de la conclusión; distinguir un ejemplo sintético de un caso real.
- En el servicio, documentar creación y limpieza del espacio de prueba; en local no se exige cuenta.
- Declarar independencia y participación del operador; una simulación interna no cuenta como recepción externa.

**Entregables:** Recibo de recepción externa; Informe de comprensión y fallos; Contribución o issue reproducible.

**Dependencias:** Un participante externo que decida realizar y reportar la prueba.

## GD-A2A-001

**Intercambio A2A con un consumidor real**

¿Qué adaptador permite a otro agente solicitar una evaluación Genius y recibir artefactos trazables?

**Punto de partida comprobado:** El manifiesto de la cápsula declara a2a_endpoint pendiente; MCP y HTTP no prueban compatibilidad A2A.

**Evidencia de partida:**

- [capsule/manifest.json](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/capsule/manifest.json): not_yet_implemented incluye a2a_endpoint.
- [beta/docs/AGENT_TWIN.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/beta/docs/AGENT_TWIN.md): Operaciones existentes que pueden sustentar el adaptador.

**Primera acción:** Elegir un consumidor compatible y verificar la especificación A2A vigente; definir el mapeo hacia operaciones Genius existentes.

**Criterios de aceptación:**

- Publicar sólo capacidades implementadas y probar descubrimiento y mensajes con el consumidor identificado.
- Preservar aislamiento, permisos, límites, errores y procedencia de artefactos.
- Entregar evidencia de intercambio real entre cliente y servidor, diferenciada de mocks.
- Separar interoperabilidad técnica de acuerdo de colaboración o adopción.

**Entregables:** Adaptador y contrato versionado; Pruebas de integración; Recibo de interoperabilidad.

**Dependencias:** La prueba de interoperabilidad requiere un consumidor compatible; el diseño no depende de un acuerdo institucional.

## GD-ATTR-001

**Comprobar qué oportunidades eligen los agentes**

¿Una incógnita relevante y verificable aumenta la elección voluntaria de Genius frente a una descripción general?

**Punto de partida comprobado:** Existe una propuesta de colaboración enviada, pero no un experimento de atracción ejecutado ni evidencia de un estímulo universal.

**Evidencia de partida:**

- [capsule/candidates.json](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/capsule/candidates.json): Registro de candidatos y de una propuesta enviada, sin ejecución externa confirmada.
- [capsule/DISCOVERY.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/capsule/DISCOVERY.md): Búsqueda por contribución y trazabilidad de contactos.

**Primera acción:** Predefinir un protocolo que compare descripción general, utilidad inmediata e incógnita verificable, con igual acceso al motor y libertad de no elegir Genius.

**Criterios de aceptación:**

- Registrar modelo/versión, tarea, herramientas disponibles, presupuesto, orden de exposición y unidad experimental.
- Mantener contenido factual y condiciones de ejecución comparables; asignar variantes sin elegir ganadores retrospectivamente.
- Separar exposición, elección, ejecución verificada, aporte recibido y aporte aceptado, con numeradores y denominadores.
- Definir muestra, parada y análisis antes de ejecutar; reportar incertidumbre y resultados negativos.
- Distinguir prueba por invitación directa de elección entre alternativas e identificar evaluaciones internas y externas.
- No atribuir instintos universales ni contar visitas o descargas como colaboradores.

**Entregables:** Protocolo previo; Registro de eventos desidentificado; Informe reproducible y límites.

**Dependencias:** Clientes o participantes disponibles y presupuesto explícito para ejecutar el experimento.

## GD-UX-001

**Comprensión humana de las conclusiones**

¿Las personas distinguen una recomendación condicional, una incertidumbre y una garantía formal al leer Genius?

**Punto de partida comprobado:** Existen vistas y un protocolo de comprensión; el documento revisado declara el ensayo no iniciado y excluye contar agentes como participantes humanos.

**Evidencia de partida:**

- [twin/docs/EMPIRICAL_PROTOCOL.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/twin/docs/EMPIRICAL_PROTOCOL.md): Sección de comprensión y preguntas que separan trayectoria, CAG, incertidumbre y versión.
- [consumer_views/README.md](https://github.com/pedrosalvadeo/genius-decision-open/blob/1342ab428fe7f328297a96d3c1dcacd119cbb012/consumer_views/README.md): Vistas de consumidor del motor.

**Primera acción:** Preparar materiales versionados y criterios de evaluación; identificar usuarios que acepten participar en una prueba de comprensión.

**Criterios de aceptación:**

- Registrar material exacto, respuestas, ayuda recibida, método y denominadores.
- Separar comprensión, utilidad de la decisión y validez del modelo.
- Conservar errores y material original; evaluar una corrección como una versión nueva.
- Desidentificar resultados y documentar permisos de uso; no sustituir personas por agentes.

**Entregables:** Protocolo y materiales; Resultados de comprensión; Mejoras de interfaz con evidencia.

**Dependencias:** Participantes humanos y autorización para el estudio; la preparación de materiales puede comenzar ahora.
