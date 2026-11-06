# Propuesta AM-07 — Conversiones de unidades declaradas, y observación parcial en el perfil

Estado: `ACEPTADA`. Pedro la aprobó el 2026-11-06, dentro del plan para usar el motor en el mapa 3D de Mendoza de Adelanta.
- No modifica S1 ni el kernel FP1. Cambia el perfil `STOCK_FLOW_FINITE_V1` (`twin/genius_twin/stockflow.py` y su compilador).
- Un modelo sin `conversions` ni `observable` compila byte a byte igual que antes.

## A. Conversiones de unidades (AM-07)

**Problema.** El perfil prohíbe que una acción deposite en una unidad más de lo que retira en esa misma unidad: así nada aparece de la nada. Pero cuando dos existencias miden la misma magnitud en unidades distintas, por ejemplo el turno de riego en litros y las tazas de los árboles en m3, la regla rechaza un riego legítimo. Los datos del mapa vienen en unidades distintas según la fuente.

**Definición.** Un modelo puede declarar hasta 8 conversiones $(u, v, c, \text{fuente})$ con $c \in \mathbb{Q}_{>0}$ y $u \ne v$, que significan $1\,u = c\,v$. El grafo de unidades con estas aristas, cada una en los dos sentidos ($1\,v = c^{-1}\,u$), se parte en clases. En cada clase se elige como raíz la primera unidad en orden alfabético y se asigna a cada unidad $w$ el factor exacto $\phi(w)$ con $1\,w = \phi(w)\,\text{raíz}$, recorriendo el grafo.

- **Consistencia.** Si un ciclo da dos factores distintos para la misma unidad, el modelo se rechaza. Una conversión declarada dos veces también se rechaza.
- **Conservación.** Para cada acción y cada clase $K$: $\sum_{s \in \text{dep},\,u(s) \in K} \phi(u(s))\,d_s \le \sum_{s \in \text{ret},\,u(s) \in K} \phi(u(s))\,r_s$. Sin conversiones, cada unidad es su propia clase y la regla es la de siempre.

**Lo que no cambia.**
- Cada existencia conserva su unidad, su saldo y su libro mayor. Ninguna conversión reescribe un saldo.
- En el kernel cada existencia sigue siendo su propio recurso (MII Def 4.6, Prop 4.5): las sumas de recursos siguen siendo por identidad y dentro de una misma unidad, así que G08 no cambia.
- Una dimensión de bienestar sigue exigiendo una sola unidad y dirección. Comparar bienestar en unidades convertidas requeriría transportar valores nativos entre celdas, y eso no se hace.

**Resultado.** Si las cantidades de un modelo se expresan en otra unidad de su clase y se declara la conversión, la factibilidad de cada acción, las trayectorias, la PVS y la frontera no cambian. Es así porque la conservación es la misma desigualdad multiplicada por un racional positivo. La prueba `test_units_observation.py` lo verifica con el turno de riego en litros.

## B. Observación parcial (sin enmienda)

**Problema.** El perfil supone que el controlador ve todas las existencias y capacidades. En el mapa eso es falso: un vecino ve sus horas y si existe la red de padrinos, pero no el agua que queda en las tazas.

**Fundamento.** MV ya separa el estado $x$ de la información $i$, y AM-01 fija la actualización $i' = U(t, i, a, y)$ con la observación $y$. Lo que faltaba era usarlo en el perfil.

**Definición.** El modelo puede declarar `observable: {stocks, capabilities}`.
- Las reglas de las rutas sólo pueden leer lo observable; si no, el modelo se rechaza.
- En cada paso la observación es $y = O(x)$: los saldos observables y las capacidades observables presentes del estado alcanzado.
- La información es la historia de acciones elegidas y observaciones.
- El compilador sigue exigiendo una sola decisión por información en cada ruta, y el kernel lo verifica (G03). Dos ramas que el controlador no puede distinguir comparten información, y por lo tanto la misma decisión.

**Lo que no hace.**
- No modela errores de medición: lo observable se ve exacto.
- No cambia el árbol causal, que sigue usando la historia completa.
