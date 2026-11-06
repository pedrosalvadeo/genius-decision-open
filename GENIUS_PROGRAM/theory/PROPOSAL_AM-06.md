# Propuesta AM-06 — Territorio: el mismo modelo zona por zona, comparado zona por zona

Estado: `ACEPTADA`. Pedro la aprobó el 2026-11-06 (opción «Sí, solo zona por zona»), dentro del plan para usar el motor en el mapa 3D de Mendoza de Adelanta.
- No modifica S1 ni el kernel FP1. Agrega una capa que sólo lee resultados del kernel ya verificados, como la federación.
- Implementación: `twin/genius_twin/territory.py`, formato `genius-territory/1`. Caso: `twin/cases/mendoza_arbolado_2027`.

## Problema

Un mapa hace la misma pregunta («¿y si…?») en muchos lugares a la vez: manzanas, radios censales, barrios. Hay dos caminos que fallan:

1. **Un solo modelo FP1 de toda la ciudad.** El árbol es exhaustivo y exacto, y su salida crece más rápido que las ocurrencias. Medido el 2026-11-06 con el caso del arbolado: 20 ocurrencias, 0,4 s y 1,9 MB; 496 ocurrencias, 21 s y 122 MB. Sesenta manzanas con 6 existencias cada una no entran.
2. **Sumar o promediar zonas.** Esconde la zona que pierde, y Homo Genius pide no agregar bienestar entre portadores ni entre tiempos.

La federación (`federation.py`) compone gemelos distintos, pero sus rutas conjuntas son el producto de las rutas de cada miembro: con 60 zonas y 2 rutas serían 2^60 rutas conjuntas.

## Definiciones

Sea $M$ un modelo `STOCK_FLOW_FINITE_V1` (la plantilla) con rutas $\Pi$, escenarios $\Xi$ y ley $\lambda$ (o ninguna). Sea $Z$ un conjunto finito de zonas, $1 \le |Z| \le 128$, partido en $Z_d$ (con dato) y $Z_\varnothing$ (sin dato, con su motivo declarado).

1. **Modelo de zona.** Para $z \in Z_d$ se declaran racionales exactos $k_z > 0$ (tamaño) y $f_{z,s} \ge 0$ (disponibilidad de la existencia $s$). $M_z$ es $M$ con toda cantidad de toda existencia multiplicada por $k_z$ (saldos iniciales, capacidades, retiros y depósitos de acciones, eventos, predicados y umbrales de tarea), y además con lo disponible de $s$ multiplicado por $f_{z,s}$: saldo inicial, renovaciones, entradas externas y capacidad si $s$ es renovable. Las demandas no cambian con $f$. Nada se redondea. Las rutas, los escenarios y la ley de $M_z$ son los de $M$.
2. **Orden de zona.** Para cada $z \in Z_d$ el kernel evalúa y verifica $M_z$ y entrega, para cada par de rutas $(a,b)$ y cada criterio $c \in \{\text{bienestar}, \text{CAG}, \text{PVS}, \text{funcional}\}$, la relación débil $a \succeq^c_z b \in \{1, 0, \bot\}$ y la débil conjunta $a \succeq_z b$. $\bot$ es «no decidido».
3. **Vida conjunta.** Para una ruta $r$ y un escenario $\xi$, la condición de vida vale en el territorio si vale en todas las zonas con dato: falla si falla en alguna, queda indecisa si ninguna falla y alguna queda indecisa. Con ley y sin indecisión, $\mathrm{PVS}_T(r) = \sum_{\xi} \lambda(\xi)\,[\text{vale en } \xi]$: la probabilidad de que la vida se sostenga en todas las zonas a la vez. No es suma ni promedio de las PVS de zona.
4. **Orden del territorio.** Con la conjunción de Kleene $\wedge$ (un 0 conocido decide; si no, un $\bot$ deja $\bot$):

$$a \succeq^c_T b = \bigwedge_{z \in Z_d} a \succeq^c_z b, \qquad a \succeq_T b = \Big(\bigwedge_{z \in Z_d} a \succeq_z b\Big) \wedge [\mathrm{PVS}_T(a) \ge \mathrm{PVS}_T(b)]$$

   donde la comparación de $\mathrm{PVS}_T$ es $\bot$ si alguna de las dos no está definida. La estricta es $a \succ_T b$ si $a \succeq_T b = 1$ y $b \succeq_T a = 0$.
5. **Factibles y frontera.** Una ruta es factible en el territorio si el kernel la declara factible en cada zona con dato. La frontera son las factibles que ninguna otra factible domina estrictamente con relación conocida. Una relación $\bot$ nunca saca a una ruta de la frontera.
6. **Cobertura.** `EXHAUSTIVE` si y sólo si $Z_\varnothing = \varnothing$, cada zona tiene cobertura `EXHAUSTIVE` y verificación `VALID`, y todas las estrictas entre rutas están decididas. En otro caso `RELATIVE`, y si hay zonas sin dato el resultado se rotula relativo a las zonas con dato. Sólo con `EXHAUSTIVE` y frontera de un elemento se informa `selected`.

## Resultados

**Proposición 1 (preorden).** Si cada $\succeq_z$ restringido a sus valores conocidos es reflexivo y transitivo, $\succeq_T$ también lo es donde está decidido. Reflexividad: cada zona da $a \succeq_z a = 1$ y $\mathrm{PVS}_T(a) \ge \mathrm{PVS}_T(a)$. Transitividad: si $a \succeq_T b = 1$ y $b \succeq_T c = 1$, cada conjunción vale 1, por lo tanto en cada zona $a \succeq_z b = b \succeq_z c = 1$, de donde $a \succeq_z c = 1$, y $\ge$ entre racionales es transitiva. Es la intersección de preórdenes de MVII, Teo 9.2, sobre un índice finito.

**Proposición 2 (sin transporte).** Ninguna comparación cruza instancias: cada $\succeq_z$ compara rutas dentro de una misma instancia $M_z$, ya verificada. El territorio sólo conjuga resultados. No se usa el transporte entre modelos que FP1 excluye (spec 02 §2.4).

**Proposición 3 (ninguna zona pierde en silencio).** Si $a \succ_T b$, entonces en ninguna zona con dato $b$ es estrictamente mejor que $a$ en ningún criterio, y la vida conjunta de $a$ no es menos probable. La recíproca no vale: una ruta que mejora 59 zonas y empeora una queda incomparable, y el resultado nombra esa zona.

**Proposición 4 (dato ausente no es cero).** Una zona sin dato no se evalúa, no aporta valores y no se rellena. Toda conclusión queda relativa a $Z_d$ y la etiqueta lo dice. Agregar después una zona sólo puede volver $0$ o mantener cada conjunción; nunca convierte en 1 un 0 ya conocido.

**Costo.** $|Z_d|$ evaluaciones independientes de tamaño $|M|$: lineal en zonas. Caso Mendoza, 60 manzanas: 24 s en una máquina y 0,1 MB de resultado.

## Qué no hace

- **No compara anónimamente.** La dominancia anónima de MIV 6.4–6.5 permite que una zona pierda si otra gana lo mismo. Pedro decidió no usarla en el mapa público.
- **No acopla zonas.** Agua que baja de una zona a otra requiere una instancia por ruta en la zona de destino, y entonces las rutas de esa zona ya no se comparan dentro de una instancia. Necesita su propia enmienda.
- **No escala funciones, subsistemas ni interfaces** de la plantilla: V1 los rechaza en vez de escalarlos mal.
- **No valida los supuestos.** Los factores de tamaño y disponibilidad son supuestos declarados; el resultado sigue siendo `DECLARED_ASSUMPTIONS_ONLY`.
