# Gemelo distribuido: integrar vistas complementarias

Extensión posterior: [Iniciativa local](BOTTOM_UP.md) permite iniciar consultas
y cálculos sin órdenes individuales de sincronización, con pares y presupuesto
declarados. Este documento conserva el contrato y experimento de composición.

Los nodos aportan partes distintas de un sistema. La integración amplía la
cobertura de entidades, relaciones, recursos y afectados, conservando quién
aportó cada fragmento. El cálculo sólo queda disponible cuando la composición
satisface los contratos existentes de sistemas y construcción de modelos.

Esta entrega amplía el [laboratorio local](README.md). No cambia el kernel,
la matemática Genius, el servicio público ni las políticas de actuación.

## Experimento reproducible

```sh
PYTHONPATH=adaptive:twin:kernel python -m federation.world_experiment --out /tmp/genius-distributed-world.json
PYTHONPATH=adaptive:twin:kernel python -m unittest discover -s adaptive/tests -p test_distributed_world.py -v
```

Se ejecutan tres procesos con bases separadas y pares inscritos explícitamente:

| Nodo | Vista declarada |
|---|---|
| Agua | Reserva y entrega, bomba, consumo de bombeo y dos rutas candidatas. |
| Energía/mantenimiento | Electricidad y horas disponibles, reparación y capacidad operativa. |
| Comunidad | Identidad de los destinatarios, relación con el agua recibida y criterio operacional parcial. |

Las interpretaciones e identidades son **manuales y sintéticas**, definidas en
`world_example.py`. El ensamblador `views.py` no contiene nombres de sectores,
activos, URL o reglas de bombeo. Las aristas no se convierten por sí solas en
ecuaciones: cada mecanismo numérico requiere fragmentos explícitos y evidencia.

Las vistas aisladas y la combinación agua+energía quedan incompletas. La vista
comunitaria añade el portador y el criterio faltantes. En conjunto hay ocho
menciones locales que corresponden a seis entidades; se conserva una sola
bomba y un solo recurso de agua entregada. El grafo compuesto conecta recursos,
equipo, suministro y comunidad. Se conservan las hipótesis y los vacíos conocidos.

Sobre tres días, las rutas sintéticas dan estas trayectorias de agua entregada
acumulada (incluido el estado inicial):

- Esperar: `1, 1, 1, 1` litros.
- Restaurar el primer día y luego bombear: `1, 1, 3, 5` litros.

El kernel verifica el cálculo. La ley probabilística sigue siendo `null`; la
selección está en `none`. El equipo físico permanece visible como entidad sin
correspondencia numérica completa, por lo que el recibo de alcance requiere
revisión. Se calculan consecuencias **condicionales al modelo**; no se recomienda
ni ejecuta una intervención real, ni se estima bienestar integral o PVS.

Otro nodo reconstruye el mismo modelo a partir de las vistas compartidas. El
reenvío no aumenta la cobertura; una desconexión conserva la última vista dentro
de su vigencia. Reiniciar un nodo conserva las vistas y permite reconstruir el
modelo. Al finalizar se detienen los procesos y se borran sólo las bases del
experimento temporal. No quedan nodos públicos ni trabajo programado.

## Paquete de vista parcial

`genius-partial-world/1` incluye:

- `world_id`, `view_id`, `owner`, `shareable` y `valid_until`.
- `frame`: instante común del estado inicial, unidad temporal, horizonte y
  `layout`, identificador del contrato de variables/posiciones del modelo.
- `observation`: grafo, fuentes, período observado e incógnitas bajo el contrato
  existente `genius-system-observation/1`.
- `identities`: ID local, ID global propuesto, estado `confirmed`, `proposed` o
  `unknown`, explicación y referencias a evidencia local.
- `denials`: negaciones explícitas de relaciones con evidencia. La ausencia de
  una arista no es una negación ni prueba de que un sistema desapareció.
- `construction`: fuentes, citas, afirmaciones, fragmentos y preguntas del
  constructor general. `scope` debe ser `null`: se compone con las identidades.
- `bindings`: correspondencia entre stocks/portadores del cálculo y entidades
  locales. Las referencias numéricas siguen el contrato `layout` común.

El contrato de posiciones e IDs es explícito y coordinado por los modelizadores.
Esta versión no alinea vocabularios arbitrarios, convierte unidades, infiere
identidades por similitud de nombres ni aprende causalidad de textos.

Las observaciones y las fuentes no pueden ser posteriores al instante de
referencia. Las vistas deben compartir exactamente el mismo marco; diferencias
de tiempo, unidad, horizonte o contrato producen `FRAME_CONFLICT`. No se mezclan
estados de instantes diferentes suponiendo que sean simultáneos. La vigencia es
una declaración del aportante, no prueba de estabilidad del mundo.

## Composición y revisión

1. Validar cada vista, deduplicarla por hash y conservar su procedencia.
2. Resolver sólo correspondencias declaradas `confirmed`; las demás conservan
   una identidad provisional y bloquean el modelo con `IDENTITY_REVIEW`.
3. Unir entidades compatibles y conservar todos sus alias y fuentes. Tipos
   incompatibles o una unión que colapsa una relación requieren revisión.
4. Unir aristas y negaciones. `A supplies B` y `B depends_on A` se normalizan a la
   misma dependencia. Una afirmación y su negación producen `RELATION_CONFLICT`.
5. Unir fragmentos numéricos idénticos y sus fundamentos. Valores diferentes en
   la misma ruta, superposiciones, unidades incompatibles y correspondencias
   duplicadas impiden construir el modelo; nunca gana el último remitente.
6. Calcular el alcance desde las entidades de interés. La evaluación incluye
   todas las entidades aportadas y conserva las dependencias e impactos
   conocidos. Los afectados sin representación numérica mantienen la revisión.
7. Pasar el documento compuesto al constructor existente. Los campos ausentes
   siguen ausentes; `READY_FOR_REVIEW` acredita coherencia formal para revisar,
   no verdad empírica, causalidad comprobada o permiso de intervención.

El resultado contiene hashes de las vistas, alias, contribuyentes por fragmento,
grafo, hipótesis de agrupación, frontera, cobertura, incógnitas, preguntas y recibo
del constructor. El informe del experimento incorpora las vistas originales para
reproducir las correspondencias. Los hashes identifican contenido, no son firmas.
Compartir una fuente repetidamente no aumenta el número de entidades ni concede
confianza estadística. Este código tampoco pondera consenso como veracidad.

Las distintas versiones de un mismo `(owner, view_id)` se conservan y requieren
revisión; no se elige automáticamente la más reciente. Una vista caducada sigue
visible y bloquea el cálculo en vez de borrar sus afectados. Resolver versiones,
caducidad y contradicciones mediante una revisión explícita es trabajo futuro.
La memoria admite ocho vistas de hasta 24 KiB aproximados (24000 bytes exactos)
cada una; el constructor conserva sus propios límites. Un exceso pide revisión,
sin truncar entidades, fuentes o preguntas. Respuestas de más de 256 KiB se
rechazan. Los datos privados no se exportan; no introducir datos personales en
este laboratorio de un solo operador.

## API local

| Ruta | Autoridad y resultado |
|---|---|
| `GET /views` | Lectura: vistas compartibles completas, con procedencia. |
| `POST /observe-views` | Operador: `{records:[vista]}`, ingreso local atómico; el propietario debe coincidir con el nodo. |
| `POST /sync-world` | Operador: `{node_id:par}`, consulta directa a un par inscrito y conserva las vistas recibidas. |
| `POST /project-world` | Operador: `{world_id, focus:[id_global], mode:"isolated"|"connected"}`, proyección sin modificar las vistas. |

`/hello` anuncia `partial_world_exchange_v1` y capacidad restante. El permiso
de lectura no puede importar vistas, solicitar sincronizaciones ni componer
modelos. Las credenciales, puertos y pares siguen bajo control del operador.
Se usan copias autorizadas en las memorias de los participantes; no existe una
base global obligatoria. El coordinador pide los intercambios y ejecuta la
verificación nativa de los modelos de prueba; no es un organismo autónomo que
descubra pares o actúe en el mundo.

## Lo que falta

La cobertura es relativa a las vistas recibidas, no una medición de cuánto mundo
real se conoce. Falta validar identidades y mecanismos con evidencia externa,
revisar versiones sin perder impactos históricos, incorporar experiencias y
resultados observados, y operar entre responsables distintos con identidades
firmadas y transporte seguro. El paso siguiente debe medir si una nueva vista
agrega una dependencia o un afectado relevante en un caso real y cómo cambia
las predicciones contrastadas, manteniendo incertidumbre y autoridad explícitas.
