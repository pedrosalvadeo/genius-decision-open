# Los ocho módulos como componentes, independientes de caso y dominio

Estado al 2026-10-18. Este documento describe cada módulo sólo por lo que recibe, lo que entrega y lo que garantiza. Ningún módulo nombra agua, sangre ni otro dominio: un caso nuevo se arma con un mismo lenguaje (`STOCK_FLOW_FINITE_V1`) y recorre los mismos ocho componentes. Los casos de `twin/cases/` son sólo ejemplos. El detalle con casos está en [MODULES.md](MODULES.md).

## Cómo se conectan

Orden de cálculo (especificación 05 §1): **0 → V → {I, II, III, IV, VI} → VII**.

| Módulo | Recibe | Entrega |
|---|---|---|
| 0 Representación | fuentes y afirmaciones citadas, supuestos | un gemelo: existencias, capacidades, portadores, acciones |
| V Futuros | el gemelo, rutas, escenarios | gemelos proyectados: un par ruta × escenario, con sus trayectorias |
| I Funcionalidad | gemelos proyectados, funciones declaradas | perfil funcional por estado y terminal |
| II Multiescala | gemelos proyectados, subsistemas e interfaces | vista por subsistema, flujo por interfaz, recomposición exacta |
| III Capacidad generativa | gemelos proyectados, capacidades | CAG posible y robusta por ruta |
| IV Bienestar | gemelos proyectados, vínculos portador–dimensión–existencia | historia de bienestar por portador, dimensión, escenario y paso |
| VI Evidencia y PVS | gemelos proyectados, condición de vida, ley | PVS por ruta, rango bajo toda ley, procedencia de la ley |
| VII Decisión | I, II, III, IV y VI | factibles, frontera, mejor ruta por actor y por función, selección explícita |

Todo resultado matemático lo calcula el kernel FP1 y lo verifica su verificador. Los módulos sólo arman la entrada y leen la salida. `modules.py` registra, en cada evaluación, qué encarna cada módulo y si está lleno, neutro o falta.

## Módulo por módulo

### 0 · Representación
- **Contrato.** Un mundo es un conjunto finito de existencias (con unidad, capacidad y tipo persistente o renovable), portadores (personas, seres vivos u organizaciones), capacidades y acciones. Cada número viene de una afirmación con su fuente o de un supuesto declarado con su clase (`MODEL`, `CALIBRATION`, `PROBABILITY`, …).
- **Construcción.** `construction.prepare` arma el modelo desde fragmentos citados y deja huecos visibles. Nada se infiere de la prosa: un relato nuevo siempre empieza como modelo general por declarar, y ninguna palabra lo desvía a una plantilla.
- **Independiente del dominio:** sí.
- **Límites que quedan:** hasta 6 existencias, 6 portadores, 12 acciones y 8 capacidades. Cantidades racionales exactas, sin decimales.

### V · Futuros
- **Contrato.** Cada ruta es una regla que decide con información pasada, nunca futura. Cada escenario es una palabra completa de eventos exógenos. Cada par ruta × escenario produce un gemelo proyectado con su trayectoria exacta. En cada paso entran los flujos, luego la acción y luego los drenajes.
- **Acciones compuestas:** hasta 4 acciones en un mismo paso, con la unión de sus requisitos y la suma de sus flujos. El kernel sigue viendo una acción por paso.
- **Independiente del dominio:** sí.
- **Límites que quedan:** hasta 30 pasos, 6 rutas, 8 escenarios y 256 celdas (rutas × escenarios × estados). Lo medido: 270 celdas tardan 10 s y ocupan 14 MB empaquetados, bajo el límite de producción de 16 MB.

### I · Funcionalidad
- **Contrato.** Una función es un conjunto de condiciones sobre existencias o capacidades que se cumple o no en cada estado. Se mide como «actual» o «acumulada». Cada función sirve a portadores y puede llevar un `kind` del catálogo común (agua, salud, seguridad, energía, alimento, …), para comparar la misma función entre gemelos distintos.
- **Pérdida de capacidades:** por decisión de Pedro, se modela como una función de este módulo, sin una CAG aparte.
- **Independiente del dominio:** sí. El catálogo es neutral y se puede ampliar.

### II · Multiescala
- **Contrato.** Los subsistemas parten las existencias, y una interfaz lleva lo que las acciones mueven de un subsistema a otro. El kernel certifica que el todo se recompone exactamente a partir de las partes.
- **Federación** (`federation.py`). Un gemelo de gemelos une de 2 a 4 gemelos, cada uno evaluado y verificado por separado:
  - los escenarios conjuntos se renombran en cada miembro;
  - un acoplamiento lleva el flujo de una interfaz de un miembro a una existencia de otro;
  - los portadores compartidos mantienen una sola identidad;
  - si un miembro ve la misma realización en varios escenarios conjuntos, la evalúa una vez con la suma de sus masas.
- **Independiente del dominio:** sí.
- **Límite que queda:** un solo nivel de acoplamientos (un destino no puede ser fuente).

### III · Capacidad generativa (CAG)
- **Contrato.** Las capacidades presentes en cada estado forman una organización, que es la firma del estado. La CAG posible y la robusta cuentan qué organizaciones alcanza y conserva cada ruta. Una capacidad puede existir sólo mientras se cumplan condiciones sobre existencias (`holds_when`).
- **Independiente del dominio:** sí.
- **Límite que queda:** hasta 16 firmas alcanzadas.

### IV · Bienestar
- **Contrato.** El bienestar es un perfil de condiciones, no un índice global: cada portador tiene dimensiones atadas a una existencia, con su dirección (más es mejor, o menos es mejor), por escenario y por paso. Nunca se suma entre portadores.
- **Independiente del dominio:** sí.
- **Límite que queda:** hasta 12 celdas de bienestar por estado.

### VI · Evidencia y PVS
- **Contrato.** La condición de vida es un conjunto de umbrales sobre existencias que deben cumplirse en toda la trayectoria. La PVS es su probabilidad bajo una ley de escenarios legítima. Si la ley falta, la PVS queda indefinida y se informa su rango bajo toda ley.
- **Leyes empíricas** (AM-02 y AM-02.1, aprobadas). La ley se deriva de la historia de uno, dos o tres conductores exógenos:
  - se usan los últimos 30 períodos;
  - cada período se compara con candidatas fijadas de antemano, con calibración exacta y puntuación propia;
  - se admite sólo con 30 resultados o más;
  - se rotula como retrospectiva hasta que la confirmen contrastes prospectivos.
- **Observatorio:**
  - el nodo de historia, en GitHub Actions, cosecha series públicas y verifica citas;
  - las lecturas periódicas contrastan predicciones congeladas con la realidad, sin recalibrar nada de forma automática.
- **Independiente del dominio:** sí.
- **Límite que queda:** la ley es por escenario completo; las leyes imprecisas (intervalos) siguen fuera del perfil.

### VII · Decisión
- **Contrato.** Una ruta es factible si cumple la condición de vida en todo escenario. Entre las factibles, la frontera usa el orden producto sobre funciones, CAG, bienestar y PVS, sin sumar criterios distintos. Se informa la mejor ruta para cada actor y para cada tipo de función. Sólo se selecciona una ruta si queda una sola en la frontera, o si la regla de selección declarada lo permite. Si la ley es frágil, ningún orden se apoya sólo en ella.
- **Acceso:**
  - API REST y herramientas MCP para agentes;
  - la aplicación web para personas;
  - el sobre de evaluación se empaqueta sin pérdida y se reconstruye idéntico al leerlo.
- **Ventana de decisión** (`decision_window.py`). Cada decisor tiene su propio tiempo para decidir y su propia velocidad de cálculo, y la realidad sigue mientras calcula:
  - el decisor declara en segundos su ventana, la duración real de un paso, cuánto falta para la primera acción, cuánto tarda en aplicar una decisión y su costo medido por celda;
  - los pasos cuya acción ocurre antes de que la decisión pueda actuar quedan comprometidos con la ruta que se sigue ahora; las rutas que sólo se diferenciaban en esos pasos dejan de ser una opción;
  - el resultado es un modelo declarado común, que se evalúa como cualquier otro.
- **Gemelo que cambia durante el cálculo.** Cada cálculo queda fijado a la evidencia con la que empezó y nunca se reescribe. `GET /jobs/<id>/freshness` lo informa: si se observó la realidad durante el cálculo o después, el resultado describe un estado anterior, y el gemelo vivo (`living.reanchor`) recalcula desde la observación nueva, con menos pasos por delante.
- **Independiente del dominio:** sí.
- **Cuando el cálculo completo no entra en la ventana** (AM-05, aprobada; `anytime.py`). Los escenarios se evalúan de a uno, primero los más probables, hasta que se cierra la ventana. Se entregan las rutas refutadas y la PVS como intervalo exacto; lo no evaluado nunca se rellena. Sólo se selecciona una ruta si el modelo lo permite y queda una sola no refutada ([PROPOSAL_AM-05](../../GENIUS_PROGRAM/theory/PROPOSAL_AM-05.md)).
- **Búsqueda de rutas** (`route_search.py`). Un proponente escribe rutas nuevas en el lenguaje del gemelo: acciones declaradas, pasos y cantidades que el modelo ya declara. Cada tanda pone las rutas de élite junto a 3 nuevas, y el kernel las compara exactamente; la frontera de la tanda pasa a ser la élite. Una ruta nueva sólo reemplaza a una de élite si la domina estrictamente. Cada veredicto queda como fila de datos (`genius-route-verdicts/1`) para entrenar, más adelante, un proponente aprendido. Primera prueba, 2026-10-18: de 48 rutas nuevas en el banco de sangre y en Denver, 47 fueron factibles y ninguna dominó ni quedó dominada. Con varios portadores cuyos intereses chocan, el orden producto deja casi todo en la frontera.

## Lo que todavía depende de algo particular

1. **El perfil D1 (semillero).** Es la plantilla sintética original; queda sólo como ejemplo de prueba y se usa si se pide por nombre.
2. **Los límites de tamaño** de 0, V, III y IV. Son límites medidos de cómputo, no del dominio. Subirlos más exige medir de nuevo tiempo, memoria y salida. Medido el 2026-10-18: los cinco casos de campo tardan de 2,9 a 4,7 s, entre 29 y 44 ms por celda.
3. **Las series reales.** Cada dominio necesita sus propias fuentes. El nodo de historia cosecha cualquier serie pública, pero alguien debe nombrarla. Faltan, por ejemplo, el caudal anual del río Mendoza en Guido y la temporada de gripe 2026/27 para admitir esa ley.
