# Iniciativa local y gemelo distribuido

Este experimento incorpora un ciclo local a los nodos existentes. Una vez que
el operador declara el mundo, el foco, los pares y un presupuesto, cada proceso
consulta por iniciativa propia, integra evidencia compartible y recompone su
vista. El coordinador no ordena cada sincronización ni elige la secuencia de
mensajes. Cada nodo ejecuta el kernel cuando obtiene un modelo nuevo calculable.

Es una política común y fija (`LOCAL_EVIDENCE_INQUIRY_V1`), sin reglas de agua,
energía o comunidad en el controlador. No aprende causalidad, genera rutas
nuevas, modifica código ni demuestra vida artificial. Las identidades, los
mecanismos numéricos y las dos rutas del ejemplo siguen siendo interpretaciones
manuales. La pertenencia a la red y el objetivo de observación están configurados.

## Ciclo de cada nodo

1. Proyectar sus vistas del mundo y conservar los vacíos y contradicciones.
2. Registrar el motivo: modelo incompleto, evidencia por revisar o actualización.
3. Consultar el índice de un par inscrito, en rotación por ID. Esta política de
   turnos no aprende qué par es más competente ni optimiza el valor de información.
4. Solicitar vistas sólo si aparecen hashes desconocidos del mundo observado.
   Un índice sin cambios evita transferir nuevamente los documentos completos.
5. Validar e incorporar el lote de forma atómica bajo los límites existentes.
6. Recomponer el modelo. Si está completo y es nuevo, calcular y verificar con
   el kernel; si falta información o hay conflicto, conservar el bloqueo.
7. Persistir el motivo, par, resultado, lecturas HTTP, hashes y resultado actual.

La consulta utiliza únicamente `GET /view-index` y, cuando hace falta, `GET
/views` sobre puertos locales inscritos. Ningún texto de fuente se interpreta
como una dirección para contactar ni como instrucciones ejecutables. El índice
incluye sólo hashes y mundos de vistas compartibles. El segundo GET transmite
el conjunto compartible acotado del par; se importan sólo los hashes solicitados
del mundo de interés. Un índice y un cuerpo incompatibles se rechazan.

Todos los nodos siguen sirviendo lecturas mientras su ciclo consulta a otros;
el ciclo corre en un hilo separado del servidor. SQLite conserva la atomicidad
de importación. Las respuestas de estado son instantáneas persistidas con
`as_of`; un cambio posterior se procesa en el próximo ciclo. El índice no
atestigua autoría: se conserva el supuesto del laboratorio de un solo operador.

## Contrato y límites

| Operación | Autoridad y contenido |
|---|---|
| `GET /view-index` | Lectura: `genius-view-index/1`, ID del nodo, pares hash/mundo compartibles. |
| `POST /initiative-start` | Operador: `id`, `world_id`, `focus`, `cycles`, `interval_ms`. |
| `POST /initiative-status` | Operador: `{id}`; devuelve recibo persistente sin credenciales. |
| `POST /initiative-stop` | Operador: `{id}`; solicita parada al terminar el ciclo en curso. |

Hay una iniciativa activa por proceso, hasta cuatro ejecuciones por memoria,
1–64 ciclos por ejecución y una pausa de 100–30000 ms entre ciclos. Cada ciclo
consulta como máximo un par y realiza hasta dos lecturas HTTP, cada una con
timeout de dos segundos. Hasta 128 lecturas de pares por ejecución; los sondeos
del operador no forman parte de esa métrica. Se mantienen ocho pares, ocho vistas
y los límites anteriores del constructor y del kernel. No se añaden proveedores,
dependencias, procesos públicos, gastos ni trabajo programado permanente.

Los ID de ejecución no se reutilizan. `BUDGET_EXHAUSTED` significa que terminó
el presupuesto, no que se resolvió el problema. Los demás estados son `RUNNING`,
`STOPPED`, `INTERRUPTED` y `ERROR`. La parada puede responder `STOP_REQUESTED`
mientras termina un ciclo; solicitar parar una ejecución anterior no afecta a
otra activa. Al reiniciar se marca cualquier ejecución pendiente `INTERRUPTED`;
no se restauran credenciales ni se reanuda actividad de red automáticamente.

El recibo `current` contiene estado, fecha, hashes, códigos de preguntas y
alcance. Los detalles de las preguntas siguen disponibles en `/project-world`.
`calculations` conserva hash del modelo y de trayectorias, verificación nativa,
selección y stocks finales. `last_calculated_model` es historia para auditoría:
si `current.model_sha256` es nulo, aquel cálculo no es una conclusión actual.
Cada resultado sigue condicionado a los supuestos del modelo; la revisión de
alcance y la autoridad de intervención no se sustituyen por un cálculo válido.

Una desconexión mantiene evidencia vigente. Al vencer su vigencia, la proyección
se bloquea sin borrar sus entidades o afectados. Una nueva versión incompatible
también bloquea: no se elige automáticamente el último valor ni una mayoría.
Resolver esas discrepancias con evidencia y revisión explícita queda pendiente.

## Experimento reproducible

```sh
PYTHONPATH=adaptive:twin:kernel python -m federation.bottom_up_experiment --out /tmp/genius-bottom-up.json
PYTHONPATH=adaptive:twin:kernel python -m unittest discover -s adaptive/tests -p test_bottom_up.py -v
```

Se crean tres procesos y bases independientes, y se inscriben sus pares. El
coordinador inicia una ejecución en cada nodo y observa sus recibos. No invoca
`/sync` ni `/sync-world`. Sus únicas inyecciones posteriores son datos del caso:

1. Inicialmente cada nodo tiene una parte del mismo sistema. Las vistas se
   intercambian por iniciativa local, pero falta la disponibilidad energética.
2. Llega al nodo de energía un informe sintético: hay 1, 0 y 1 kWh en los tres
   días. Es una llegada tardía de información sobre una interrupción declarada,
   no detección sensorial ni actualización automática de un estado físico real.
3. Los pares descubren el informe y completan el mismo modelo. Cada nodo ejecuta
   el kernel; la ruta de reparar y luego bombear entrega `1,1,1,3` litros
   acumulados. Esperar da `1,1,1,1`. El segundo día no puede bombear por falta de
   energía; el tercero entrega dos litros adicionales.
4. Se apaga el nodo de energía. Los otros continúan con sus copias vigentes.
5. Llega al nodo de agua otro informe que afirma disponibilidad constante. Los
   pares descubren la contradicción y suspenden el cálculo actual. La historia
   calculada permanece en auditoría, sin presentarse como una recomendación.
6. Los dos ciclos restantes terminan por su presupuesto. Todos los procesos se
   detienen y se eliminan únicamente sus bases temporales.

El informe incluye fuentes, vistas, instantáneas, trazas de consultas, hashes
de código, cálculo reproducible y 14 comprobaciones. Las pruebas adicionales
cubren datos privados, índices incompatibles, caducidad, reinicio, límites,
parada y separación entre permisos de lectura y operación.

La mejora comprobada es pasar de evidencia insuficiente a un cálculo coherente
con el escenario declarado. El objetivo final sintético de 3 litros está
declarado en el programa; no es un ensayo ciego ni una medición independiente.
La predicción de base es nula, por lo que no puede estimarse una reducción de
error predictivo. La ley probabilística sigue desconocida, la selección en
`none` y el equipo físico sin representación numérica completa mantiene la
revisión de alcance. No se mide PVS ni bienestar integral.

## Próxima etapa

Incorporar un contraste entre predicciones congeladas y observaciones reales,
y un procedimiento explícito para revisar versiones sin borrar afectados.
Evaluar estrategias de consulta según evidencia anterior, comparando calidad,
coste de intercambio y efectos sobre otros sistemas. Mantener los mismos
contratos de matemática y procedencia. La autonomía demostrada aquí se limita
a buscar, componer y calcular con pares ya admitidos dentro del laboratorio.
