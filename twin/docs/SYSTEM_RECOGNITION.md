# Sistemas, observaciones y límites revisables

16 de octubre de 2026. Esta capa reconoce **hipótesis de agrupación en un grafo declarado** y las vincula con el modelo stockflow. Registra entidades, relaciones y fuentes, conserva identidades entre vistas, propone agrupaciones y comprueba qué dependencias y afectados quedan fuera del sistema. No identifica objetos en imágenes, interpreta relatos libremente ni acredita causalidad empírica.

La formulación fuente S1 (Módulo IV, elección de portadores y frontera; Módulo VI, interpretación de PVS) exige declarar el alcance. Esta entrega hace esa declaración revisable y trazable; no modifica los criterios del kernel, CAG, bienestar ni la regla de selección. El diseño de intervenciones sigue generando alternativas sobre las reglas numéricas previamente declaradas.

## Observaciones e identidad

`GET /systems/schema` publica `genius-system-observation/1`. Cada vista contiene:

- Nombre y ventana de observación con comienzo/fin ISO8601 y zona horaria. Esa ventana no es el horizonte predictivo.
- Hasta 32 entidades con ID estable en el expediente, nombre, tipo (recurso, elemento físico, persona, ser vivo u organización) y referencias a fuentes.
- Hasta 32 registros de evidencia: fecha dentro de la ventana, fuente, contenido, incertidumbre y origen (`reported`, `measurement`, `inference`, `synthetic`). Son declaraciones del remitente: la plataforma no autentica la fuente ni convierte una medición declarada en un hecho verificado.
- Hasta 64 relaciones dirigidas, con identidad, extremos, tipo y referencias a evidencia.
- Entre 1 y 16 cuestiones desconocidas. No se inventan probabilidades de certeza.

Las fuentes se conservan como texto: no se ejecutan instrucciones ni se descargan URLs de su contenido. No se suman saldos a partir del grafo. Cada identidad conserva su tipo; las etiquetas pueden cambiar sin crear otra entidad. Una identidad puede participar en hipótesis anidadas o superpuestas. No hay resolución automática de duplicados entre IDs diferentes o expedientes.

`POST /cases/{id}/systems` recibe `base_version`, `observation_revision`, `idempotency_key` y `observation`. Es válido antes del modelo numérico, con versión 0. Se comprueban las dos revisiones bajo transacción. El registro es inmutable y la repetición idéntica devuelve el mismo recibo incluso al alcanzar la cuota. Una clave reutilizada con otro contenido falla.

Cada vista es una nueva declaración completa sobre su ventana. **Omisión no equivale a desaparición.** Se conserva toda la historia y se detectan entidades/relaciones de cualquier vista anterior que falten, así como cambios de extremos/tipo bajo un mismo ID de relación. Estas diferencias suspenden la recomendación de una hipótesis vinculada. No se resuelven automáticamente por ausencia repetida. Una nueva vista que vuelva a incluir los elementos permite revisar las omisiones; contradicciones e invalidaciones temporales necesitan aún un protocolo explícito de resolución. No se infieren nacimientos ni muertes.

El límite local es 64 vistas. En beta se usa el menor entre 64 y la cuota de revisiones vigente de la cuenta. Se reutilizan el almacenamiento privado, bloqueo de ciclo de vida, presupuesto de disco, exportación, retención y borrado de observaciones existentes; no hay migración de tablas ni aumento de cuotas.

## Reconocimiento reproducible

El algoritmo propone componentes conexas bajo dos interpretaciones:

1. `organization_components`: conexiones `organizes`, interpretadas simétricamente.
2. `interaction_components`: todas las conexiones, sin dirección para esta agrupación más amplia.

Las agrupaciones repetidas se deduplican y las entidades aisladas permanecen como candidatas. El ID de una agrupación depende de sus miembros, no de su orden de entrada. Son **hipótesis heurísticas**, sin clasificación por certeza ni prueba de exhaustividad sobre sistemas posibles. No se presupone que una componente conexa sea un organismo real ni una unidad funcional validada.

La evaluación de límites sí conserva la dirección:

| Relación | Significado declarado | Propagación de posible impacto |
|---|---|---|
| `organizes A→B` | A y B participan de una organización conjunta | A↔B |
| `supplies A→B` | A suministra a B | A→B; B depende de A |
| `depends_on A→B` | A depende de B | B→A; A depende de B |
| `affects A→B` | A puede afectar a B | A→B; no implica suministro |

Para los miembros elegidos se recorren por separado las cadenas de dependencia y de posible impacto, conservando ciclos y relaciones inciertas. El alcance mínimo es la unión de miembros, dependencias alcanzables e impactos alcanzables **en el grafo suministrado**. No es una prueba de cierre causal del mundo ni identifica signos, magnitudes, probabilidades o efectos de una intervención particular. Las hipótesis amplias permiten explorar además otros alcances; el usuario puede proponer miembros personalizados.

El recibo conserva el hash de la observación y el código de reconocimiento, candidatos, relaciones que cruzan el límite y desconocidos. `GET /cases/{id}/systems` devuelve el contexto actual sin escribir.

## Tres límites y conexión con el cálculo

`GET /systems/scope-schema` publica `genius-system-scope/1`. La propuesta utiliza el flujo existente:

```json
{
  "base_version": 1,
  "kind": "system_scope",
  "text": "Fundamento de los límites",
  "structured": {"scope": "Objeto conforme a /systems/scope-schema"}
}
```

El campo `scope` real es un objeto, no la cadena descriptiva del esquema anterior. `GET /systems/example` ofrece una carga completa reproducible.

- **Sistema:** miembros de la unidad estudiada.
- **Intervención:** subconjunto sobre el que se propone actuar; declararlo no concede autoridad ni ejecuta acciones.
- **Evaluación:** incluye al menos las dependencias e impactos identificados. Una propuesta que los excluya se rechaza.
- **Correspondencias:** cada stock y portador del modelo se vincula exactamente una vez a una entidad del tipo apropiado. El mismo recurso no puede duplicarse como dos saldos ni el mismo sujeto como dos portadores. Los portadores requieren condiciones de bienestar explícitas.

Las entidades incluidas en la evaluación que todavía carecen de correspondencia numérica permanecen visibles. La propuesta puede confirmarse y calcularse, pero su recomendación queda suspendida por alcance incompleto. Un mapa completo es sólo una declaración de correspondencias: no acredita las ecuaciones, umbrales, bienestar o probabilidades del mundo real.

Confirmar genera una versión nueva aunque el modelo numérico sea idéntico. Se conservan la vista de evidencia, el alcance, correspondencias, fundamento y hashes del modelo y del alcance. La aceptación vuelve a comprobar que no llegó una vista posterior. Evaluaciones, exportaciones y comparación conservan el recibo; el certificado nativo sigue certificando la instancia formal del modelo, no el grafo observado.

Al agregar evidencia o cambiar el modelo, un alcance anterior deja de estar vigente y se exige revisarlo antes de recalcular. Los resultados anteriores siguen disponibles por su ID y no se reescriben. La interfaz muestra la revisión pendiente incluso si hay un resultado histórico. Comparar versiones con fronteras diferentes no demuestra mejora sobre un alcance común.

## Interfaz y agentes

La pestaña **Sistemas** del gemelo general permite registrar fuentes, entidades, relaciones, incertidumbre, revisar candidatos, ajustar tres límites y sus correspondencias. Los cambios no registrados duran mientras la pestaña permanezca abierta; registrar los conserva en el servicio. Las propuestas de alcance se recuperan después de recargar. Hay un ejemplo explícitamente sintético que abre otro expediente.

Se añaden seis herramientas MCP bajo permisos existentes:

- Lectura: `twin_system_schema`, `twin_system_scope_schema`, `twin_system_example`, `twin_system_context`.
- Escritura: `twin_observe_system`, `twin_propose_system_scope`.

El segundo comando de escritura utiliza la ruta de propuestas y su cuota. La confirmación y evaluación siguen usando `twin_accept` y `twin_evaluate`. No hay acceso a otro tenant, elevación de autoridad ni herramientas externas nuevas.

## Verificación y pendientes

`test_systems.py` usa oráculos independientes para dirección, ciclos, agrupaciones anidadas, identidad, límites de impacto, omisiones, errores de esquema y tiempo; ejercita idempotencia, historial inmutable, conflictos, reapertura, borrado y resultado del kernel sin cambios numéricos. `test_agent_twin.py` comprueba permisos, cuota, aislamiento, REST/MCP, cálculo nativo, exportación y revocación. `browser_systems.cjs` recorre el formulario, evidencia anterior al modelo, edición de hipótesis, recuperación tras recarga, cálculo, suspensión por afectados no representados, nueva evidencia y exportación en escritorio y móvil. Datos exclusivamente sintéticos.

Pendiente: percepción o extracción desde entradas no estructuradas; adquisición de fuentes; resolución contrastada de entidades; vigencia temporal y refutación de relaciones; evaluación predictiva comparada de hipótesis; observaciones stockflow contra predicciones congeladas; traducción contrastada de nuevas relaciones a dinámica; calibración con datos de campo. Esta entrega no afirma tener esas capacidades.
