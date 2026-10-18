# Propuesta AM-02.1 — Ley empírica con varios conductores

Estado: `ACEPTADA`. Pedro la aprobó el 2026-10-18 («Apruebo»).
- Redactada el 2026-10-18 a pedido de Pedro, que eligió «Sí, prepárala» en la tarjeta «¿Preparo la enmienda de AM-02 para leyes con dos o más factores?».
- Extiende AM-02 (`PROPOSAL_AM-02.md`) y conserva sus once reparaciones. No modifica S1 ni el kernel.
- Código: `twin/genius_twin/driver_law.py` (`joint_certificate`), servido en `POST /laws/driver/joint` y en la herramienta MCP `twin_joint_driver_law`. La federación del Colorado ya la usa.

## Problema

AM-02 certifica una ley a partir de un solo conductor exógeno: la nieve, la afluencia a un embalse o la gripe. Cada período pasado se asigna al escenario cuyo valor de anclaje quedó más cerca. Muchos sistemas reales tienen dos o más incertidumbres a la vez:
- un banco de sangre ante la gripe y ante la cantidad de donantes;
- una ciudad y un embalse que dependen de cuencas distintas;
- una red eléctrica ante la demanda y el viento.

Hoy un gemelo así tiene dos salidas, y ninguna sirve:
- **Declarar la ley a mano.** Sin una ley legítima la PVS queda indefinida (S1, Definición 8.11).
- **Suponer que los factores se mueven juntos.** La federación del Colorado (`twin/cases/colorado_basin_2027`) declara `SharedHydrology`: el invierno de Denver y el año de Powell siempre coinciden. Su procedencia dice «Sin estudio de correlación todavía». El registro la refuta (ver «Primera aplicación»).

## Propuesta

### A. Conductores y escenarios

1. **Conductores.** Se declaran 2 o 3 conductores. Cada uno tiene su serie, de 2 a 8 categorías con un anclaje cada una y una categoría de desempate. Cada conductor cumple las condiciones de AM-02: no depende de las rutas comparadas y sus períodos no se superponen. Además, una misma etiqueta de período significa el mismo período para todos los conductores.
2. **Celdas.** Una celda es una combinación de categorías, una por conductor. Cada período común cae en la celda de sus anclajes más cercanos, uno por conductor, con la regla de cercanía de AM-02.
3. **Escenarios.** Los escenarios del gemelo, de 2 a 8, forman una partición de **todas** las celdas: cada celda está en exactamente un escenario. Así la ley queda sobre realizaciones completas (reparación 1 de AM-02), y el modelizador no puede dejar fuera combinaciones incómodas.
   - La partición se fija desde el gemelo y su tarea antes de mirar el registro conjunto.
   - Un escenario de varias celdas declara su celda representativa, y la PVS vale sólo para ella.
4. **Ventana.** Rige la regla de AM-02 del 2026-10-18: se usan los 30 períodos comunes más recientes.

### B. Candidatas fijadas de antemano

1. **Masas iguales** por escenario.
2. **Frecuencia conjunta suavizada:** $(k_s+1)/(n+S)$, donde $k_s$ cuenta los períodos anteriores que cayeron en el escenario $s$, $n$ es el número de períodos anteriores y $S$ el número de escenarios.
3. **Conductores independientes:** el producto de las frecuencias marginales suavizadas de cada conductor, $\prod_j (k_{j,c_j}+1)/(n+C_j)$, sumado sobre las celdas de cada escenario. Aquí $C_j$ es el número de categorías del conductor $j$.

La candidata 3 es la única que supone independencia entre conductores. Con pocos datos aprovecha mejor la evidencia, porque estima cada conductor por separado. Si los conductores dependen entre sí, su calibración conjunta o su puntuación lo muestran.

### C. Comprobación y admisión

Iguales a AM-02:
- pronóstico precuencial: cada período se pronostica sólo con los anteriores;
- calibración por escenario con intervalos exactos de Clopper–Pearson y corrección de Bonferroni;
- puntuación logarítmica media;
- se elige la mejor puntuación entre las candidatas calibradas;
- se admite sólo con al menos 30 resultados independientes y ningún rechazo; los escenarios con menos de 5 observaciones se listan como de poca potencia;
- el rótulo es `RETROSPECTIVE_PREQUENTIAL` hasta los contrastes prospectivos.

El certificado agrega:
- la tabla conjunta de celdas observadas;
- la celda y el escenario de cada período;
- los anclajes de cada conductor.

### D. Lo que la candidata independiente no prueba

Que la candidata 3 quede calibrada no demuestra que los conductores sean independientes: con 30 períodos la prueba tiene poca potencia (reparación 4 de AM-02). Por eso:
- el certificado nombra la independencia como supuesto cuando esa candidata es la elegida;
- un resultado bajo esa ley lo dice en su rótulo.

## Primera aplicación: la cuenca del Colorado

`twin/history/colorado_joint_law.py` produce `twin/history/colorado_joint_law.json`. Usa los mismos anclajes que las leyes ya admitidas:
- **Denver:** nieve del 1 de abril como fracción de la mediana 1991–2020. Seco = 2026 (34,4 %), normal = 100 %, húmedo = 150 %.
- **Powell:** afluencia no regulada del año hidrológico, con los anclajes del estudio de octubre de 2026 (4,07 / 7,80 / 15,10 millones de acre-pies).

Años hidrológicos 1996–2025 (los 30 más recientes de 35 en común), en filas Denver y columnas Powell:

| Denver \ Powell | seco | normal | húmedo |
|---|---|---|---|
| seco | 2 | 0 | 0 |
| normal | 6 | 11 | 6 |
| húmedo | 0 | 2 | 3 |

**1. La alineación queda refutada.** Coinciden 16 de 30 años y 14 no. Basta un año desalineado para refutar el supuesto `SharedHydrology` de la federación («siempre se alinean»). Cuántos años se desalinean depende de los anclajes: el húmedo de Powell está en el 194 % de su normal y el de Denver en el 150 %. La correlación de Pearson entre los valores crudos de los dos conductores es 0,605.

**2. Qué ley gana depende de la partición.** La partición principal sigue una regla que no mira el registro conjunto. Son los tres años alineados más un desacople en cada dirección:
- Powell más seco que Denver, representado por Denver normal con Powell seco;
- Powell más húmedo que Denver, representado por Denver normal con Powell húmedo.

Con ella las tres candidatas quedan calibradas y gana la frecuencia conjunta: 3/35, 12/35 y 4/35 para los alineados, 9/35 para Powell más seco y 1/5 para Powell más húmedo. Gana por apenas 0,0017 de puntuación logarítmica sobre las masas iguales.

Se probaron cuatro particiones y todas están en el certificado:

| Partición | Candidata elegida |
|---|---|
| por dirección (principal) | frecuencia |
| primer borrador (elegido después de ver la tabla) | frecuencia |
| por categoría de Powell | masas iguales |
| alineados o no | masas iguales |

Como la elección cambia, el certificado dice `SELECTION_FRAGILE_UNDER_PARTITION`. Bajo la reparación 7 de AM-02, esta ley no sostiene ninguna recomendación por sí sola.

**3. Hay poca evidencia por escenario.** Los escenarios alineado seco y alineado húmedo tienen 2 y 3 años. El certificado los lista en `low_power`.

**Consecuencia para la federación (aplicada tras la aprobación).** La federación ahora tiene cinco escenarios: los tres alineados y los dos desacoples, cada uno calculado en su celda representativa, con la ley conjunta admitida.
- Un gemelo miembro que ve la misma realización en varios escenarios conjuntos (Denver normal aparece en tres) la evalúa una sola vez, con la suma de sus masas.
- Resultado: con la regla «reanudar el riego al 70 %», Denver riega en su año normal pero no en el seco. En el año desacoplado, Denver normal con Powell mínimo, desvía 17.000 acre-pies de un Powell que ya está en su mínimo, y Powell termina en 4.055 mil acre-pies en vez de 4.072.
- Las seis rutas conjuntas siguen cumpliendo la condición de vida en los cinco escenarios, la frontera no cambia y la mejor ruta para cada actor tampoco. Como la ley es frágil, ningún orden se apoya sólo en ella.

## Revisión adversarial separada (2026-10-18)

Una sesión independiente leyó la propuesta, AM-02, el código y el certificado. Su dictamen fue `ACCEPT_WITH_REPAIRS`. Comprobó que no hay filtración de datos futuros, que los denominadores de Laplace son correctos, que la validación de la partición funciona y que todas las cifras coinciden con el JSON. Las reparaciones ya están incorporadas:

1. **Partición elegida después de ver los datos.** El primer borrador agrupaba los desacoples más vistos. Ahora la partición se fija desde el gemelo y su tarea antes de mirar el registro conjunto, y el llamador lo declara. Se reportan todas las particiones probadas, y si la candidata elegida cambia entre ellas el resultado es frágil.
2. **Escenarios agrupados.** Un escenario de varias celdas declara su celda representativa, la realización que el gemelo calcula. La PVS bajo la ley vale sólo para esa representativa (reparación 2 de AM-02).
3. **Poca potencia.** Los escenarios con menos de 5 observaciones se listan. Con 30 períodos, no rechazar es poca evidencia.
4. **Orden de períodos.** Todos los conductores deben listar los períodos comunes en el mismo orden, y los períodos sin todos los conductores se informan.
5. **Categorías.** Deben ser textos no vacíos.
6. **Prueba.** La masa de la candidata independiente se recalcula de forma independiente en la prueba.
7. **Correlación.** Se declara la variable usada, los valores crudos, y la cifra figura en el certificado.
8. **Presión sobre Mead.** Se marca como hipótesis.
9. **Anclajes.** Se dice que la magnitud del desacople depende de ellos.
10. **Independencia de los años.** Que los años sucesivos sean independientes sigue siendo una declaración del llamador. Las sequías de varios años la debilitan, igual que en AM-02.

## Invariantes que no cambian

- El ideal de bienestar y cuidado de la vida es el fin del cálculo.
- La PVS bajo una ley conjunta sigue debajo de CAG y del bienestar, y su rótulo completo (reparación 10 de AM-02) nombra todos los conductores.
- El kernel FP1 no cambia: la ley entra por el campo `law` existente, como en AM-02.

## Impacto

- **Kernel:** sin cambios.
- **Gemelos:** un gemelo puede tener escenarios definidos por varios factores, en cualquier dominio. El límite de 8 escenarios obliga a agrupar celdas; los grupos quedan declarados y certificados.
- **Federaciones:** la ley conjunta reemplaza a los supuestos de alineación que hoy se declaran a mano.

## Hecho al aprobar (2026-10-18)

1. Se sirve en `POST /laws/driver/joint` y en la herramienta MCP `twin_joint_driver_law`.
2. La federación del Colorado se rehízo con los escenarios desacoplados y la ley conjunta admitida.
3. El estado quedó como `ACEPTADA` en `AMENDMENTS.md`.
