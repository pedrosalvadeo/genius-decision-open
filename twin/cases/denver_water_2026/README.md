# Denver Water, sequía 2026/27

Primer caso real del gemelo dinámico. `world.json` lo genera `build.py` a partir de extractos textuales citados (Denver Water, Denver Gazette, Denver7, resolución del directorio). Cada número citado lleva su cita exacta; los demás son hipótesis declaradas.

## Situación (fuentes, octubre 2026)

- Embalses al 67 % el 12/10/2026, frente a 90 % promedio para la fecha.
- Riego de césped y aspersión prohibidos desde el 1/10/2026 (Etapa 1 enmendada). La empresa espera mantenerlo "hasta bien entrada la primavera de 2027".
- Proyección oficial: 55–60 % antes del deshielo. Mínimo histórico: 50 % en 2003.
- Deshielo 2026: 22 % de lo normal. Para llenar hace falta una nieve mayor a 150 % de lo normal.

## Modelo

Unidad: puntos de capacidad de los embalses de suministro. Doce pasos mensuales (mediados de noviembre 2026 a mediados de octubre 2027).

| Opción | Regla |
|---|---|
| `keep_ban` | Mantener la prohibición todo el horizonte |
| `resume_may` | Riego de Etapa 1 de mayo a septiembre |
| `resume_if_70` | Riego de Etapa 1 sólo en los meses que empiezan con 70 % o más |

Escenarios: invierno seco (deshielo como 2026), normal y húmedo. Tarea operacional: almacenamiento ≥ 50 % en todos los meses. Bienestar: agua entregada a riego exterior para la población servida, y reserva de los embalses para Denver Water como organización (representación elegida por el modelizador). Sin ley de probabilidad.

### Hipótesis para revisar

- Invierno: −1,5 puntos/mes con la prohibición (67 → 58, centro del rango oficial).
- Mayo a octubre: −2 puntos/mes de uso interior y evaporación.
- Riego de Etapa 1: −2 puntos/mes adicionales.
- Deshielo neto mayo/junio/julio: seco 2/3/1, normal 8/14/6, húmedo 12/20/12.
- Umbral de 50 %: referencia elegida por el modelizador, no regla de Denver Water.

Los pronósticos mensuales seco/normal/húmedo de Denver Water deberían reemplazar estas cifras cuando estén disponibles.

## Resultado del kernel

Revisión del 17/10/2026: la tarea es una condición de vida (guardar siempre un año de agua de uso de invierno, 21,5 % de la capacidad, según el Water Watch Report del 12/10/2026) y la ley declarada es un tercio por invierno, sin respaldo empírico todavía.

Revisión del 18/10/2026 (módulo VI): la ley es empírica y está admitida por AM-02. Con la nieve del 1 de abril de 1991 a 2026 en 12 estaciones SNOTEL del NRCS (`twin/history/denver_snow/`), cada año se asigna al invierno del modelo que más se le parece: 3 secos (2002, 2012, 2026), 27 normales y 6 húmedos. Un tercio cada uno queda descalibrado; la ley admitida es seco 4/39, normal 28/39, húmedo 7/39. Revisión del 18/10/2026: con la regla de ventana de AM-02 (los últimos 30 años, 1997 a 2026) quedan 3 secos, 23 normales y 4 húmedos, y la ley es seco 4/33, normal 8/11, húmedo 5/33. Ningún año llegó a 150 % de la mediana (el máximo fue 146,8 % en 2011), así que el húmedo del modelo es un extremo.

- PVS = 1 en las tres opciones y con cualquier ley: el mínimo es 42 % (`resume_may`, invierno seco), lejos de 21,5 %. El mínimo histórico de 50 % (2003) queda como referencia.
- Bienestar: reanudar el riego da agua a jardines y árboles a cambio de reserva. En invierno seco `keep_ban` y `resume_if_70` son iguales; en el resto, ninguna opción es mejor para todos. La frontera tiene las tres y no hay selección.

Reproducir: `PYTHONPATH=twin:kernel python -m unittest twin.tests.test_case_denver_water` desde la raíz, o `python twin/cases/denver_water_2026/build.py` para regenerar el caso.

## Predicción congelada y contraste

`prediction.json` congela, el 17/10/2026, la trayectoria del embalse para cada opción y escenario, con su calendario y los hashes del mundo y del modelo. `observations.json` acumula las lecturas reales posteriores con su diferencia exacta frente a cada trayectoria, sin recalibrar el modelo. Registrar una lectura (desde la raíz, con `PYTHONPATH=twin:kernel`):

La predicción se congeló con la revisión anterior del mundo (tarea operativa, sin ley), que se conserva byte a byte en `frozen_world.json`. La revisión actual cambia la tarea y la ley, no las trayectorias, así que el contraste sigue valiendo.

```bash
python twin/cases/predictions.py contrast <caso> --date AAAA-MM-DD --value <valor> --observed-at <ISO8601> --source "<editor, URL y cita exacta>"
```

`twin.tests.test_predictions` falla si `world.json` cambia sin volver a congelar la predicción.
