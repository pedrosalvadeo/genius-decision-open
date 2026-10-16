# Construcción de modelos con un proceso común

Formato `genius-world-construction/1`. Un mismo ensamblador recibe una
interpretación estructurada, comprueba sus fuentes textuales, construye el
modelo numérico y lo vincula a los sistemas observados. No contiene listas de
sectores, URL de un dominio, palabras clave ni alternativas predeterminadas.

La interpretación de documentos y relatos corresponde a la **IA conectada por
MCP o al modelizador humano**. El servidor publica instrucciones y esquemas;
no llama a un LLM ni convierte por sí solo prosa libre en conocimiento causal.
Esta entrega generaliza la construcción y revisión dentro de las dinámicas
admitidas, sin afirmar aplicación validada a cualquier dominio.

## Recorrido completo

1. Leer `twin_world_contract`. Incluye el protocolo, el esquema de construcción,
   el del modelo numérico y el de observaciones de sistemas.
2. Crear el expediente con `profile: STOCK_FLOW_FINITE_V1`. Así no se utiliza
   la heurística histórica del ejemplo semillero.
3. La IA interpreta la situación y propone entidades, relaciones, identidades
   y límites, distinguiendo hechos declarados de inferencias. Registra la vista
   con `twin_observe_system` y revisa agrupaciones, dependencias e impactos.
4. Construir fuentes, afirmaciones y fragmentos del modelo. Cada cantidad,
   estructura y elección debe quedar bajo afirmaciones explícitas. Si falta
   información, omitir el campo y describir la pregunta en `unresolved`.
5. `twin_prepare_world`, con `case_id` y `payload: {base_version, construction}`,
   devuelve el borrador, preguntas, errores del modelo y recibos. No escribe
   propuestas o versiones. Revisar y repetir sólo lo que requiera corrección.
6. `twin_propose_world`, con `case_id`, `base_version`, `text` y `construction`,
   vuelve a preparar la construcción contra la última observación y conserva
   una propuesta completa de modelo y límites en una sola operación.
7. Confirmar mediante `twin_accept` dentro de la autoridad ya otorgada por el
   responsable. Evaluar con `twin_evaluate`; conservar el recibo nativo, el
   de construcción y las limitaciones. Exportar o revisar con el flujo existente.

REST: `GET /api/twin/world/contract`,
`POST /api/twin/cases/{id}/world/prepare` y la ruta existente de propuestas con
`kind: world_model`, `structured: {construction: ...}`. En el servidor local
el prefijo es `/api`. La lectura requiere `twins:read`; preparar/proponer exige
`twins:write`; evaluar mantiene `twins:evaluate` y la cuota de cómputo existente.
No se amplían permisos ni se agregan servicios, variables, tablas o dependencias.

## Contenido de la construcción

| Campo | Contenido |
|---|---|
| `sources` | Hasta 8 extractos de 6000 caracteres, con ID, origen y fecha con zona horaria. |
| `claims` | Hasta 64 afirmaciones: `reported`, `measurement`, `hypothesis`, `decision`, `definition` o `synthetic`; incertidumbre, citas y premisas. |
| `fragments` | Hasta 128 fragmentos no superpuestos del modelo, cada uno con ruta, valor y referencias a afirmaciones. |
| `scope` | Fronteras y correspondencias contra una revisión explícita de las observaciones; `null` mientras falta completarlas. |
| `unresolved` | Preguntas por datos ausentes, conflictos, mecanismos no admitidos o supuestos pendientes. Bloquean la propuesta completa. |

Ejemplo de fragmento: `{"path":"/stocks/0/initial","value":"6/1","claim_ids":["reading"]}`.
También puede suministrarse `/stocks/0` con todo el recurso. Las citas se asocian
al fragmento entero: usar fragmentos menores cuando sus campos tienen fundamentos
distintos. No se permite una asignación a la raíz del modelo ni superponer un
fragmento con sus descendientes; cada conflicto debe resolverse explícitamente.

Los índices de arrays empiezan en cero. Las posiciones ausentes se conservan
como faltantes y bloquean la propuesta. No se rellenan con cantidades cero.
Las cantidades usan racionales exactos del perfil; no se aceptan floats.
El documento completo está limitado a 96000 bytes, 24 niveles y 8192 nodos.

Una cita contiene `source_id`, `start`, `end`, `quote`. Los desplazamientos se
miden en puntos de código Unicode, comienzo inclusivo y fin exclusivo, sobre
`source.content`. Se comprueba coincidencia exacta. Una afirmación reportada o
de medición exige cita; las premisas deben existir y no pueden ser circulares.
`measurement` describe la clasificación del remitente, no una medición
autenticada por el servicio. Orígenes y contenido son datos inertes: nunca se
descargan URLs, ejecutan scripts ni siguen instrucciones incluidas en fuentes.

## Qué se comprueba y qué permanece abierto

El ensamblador comprueba estructura, referencias, valores exactos, restricciones
de unidades y balances del perfil, tamaño finito del cálculo, correspondencias
de identidad y cobertura de dependencias/impactos declarados. El reconocedor y
el kernel conservan su comportamiento y sus criterios matemáticos.

`NEEDS_REVISION` conserva borrador y preguntas; `model` permanece `null`.
`READY_FOR_REVIEW` permite proponer, sin aceptar automáticamente. Los afectados
sin correspondencia numérica siguen visibles en el recibo de alcance y suspenden
la recomendación según las guardas de sistemas existentes.

Una ley explícita `null` o un umbral permitido `null` no equivale a un campo
olvidado: el modelo puede calcular con ese desconocimiento. El constructor no
crea probabilidades ni cambia a cero lo desconocido. Las limitaciones del perfil
de existencias y flujos siguen vigentes: conversiones físicas, dinámica continua,
identidades nuevas o desapariciones no se habilitan por describirlas en texto.

La coincidencia literal no prueba que una cita implique el valor propuesto.
`semantic_entailment`, `causal_validation` y `empirical_validation` quedan en
`NOT_ASSESSED`. Las derivaciones numéricas desde la prosa requieren revisión:
este contrato no las certifica. Contrastar predicciones con mediciones y ampliar
la representación son trabajos posteriores; no se sustituye esa evidencia por
una explicación convincente de un LLM.

## Memoria y revisiones

La propuesta conserva fuentes, afirmaciones, fragmentos, preguntas y hashes del
modelo, observación y ensamblador. La versión aceptada y su evaluación/exportación
retienen el recibo completo. Cambiar evidencia puede producir una versión con
el mismo modelo numérico y nueva justificación. Las anteriores permanecen
inmutables. Una nueva observación invalida la aceptación de una propuesta
pendiente; los límites deben revisarse antes de recalcular.

Un cambio numérico por otra vía elimina el recibo de construcción heredado de
ese modelo; permanece en su versión original. Restaurar recupera el recibo de
la versión restaurada, sujeto a la revisión del alcance frente a la evidencia
actual. Actualizar un modelo no modifica código, permisos ni evidencia pasada.

## Prueba entre dominios

Tres expedientes sintéticos incluyen relato, interpretación explícita,
construcción, observación y una trayectoria esperada independiente:

- [Agua](../examples/world/water.json): transferencia entre existencias y demanda.
- [Taller](../examples/world/workshop.json): tiempo renovable, transformación de
  pendiente a terminado en la misma unidad y cambio de capacidad organizativa.
- [Energía](../examples/world/energy.json): entradas por escenario y políticas de
  consumo, con ley probabilística desconocida.

Las pruebas usan el mismo ensamblador, cambian los nombres sin seleccionar una
plantilla y ejecutan el kernel real. Son pruebas de construcción, trazabilidad
y cálculo condicional. No son un ensayo de comprensión automática de relatos,
un dominio oculto al modelizador ni validación empírica de transferencia.

```sh
PYTHONPATH=twin:kernel python -m unittest discover -s twin/tests -p test_construction.py -v
```

Próximo trabajo: incorporar búsqueda de evidencia y revisión semántica al agente
intérprete, contrastar modelos competidores con predicciones congeladas y datos
posteriores, y ampliar los mecanismos representables cuando un caso lo exija.
