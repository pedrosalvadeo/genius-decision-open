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

- `resume_may` falla: en invierno seco el almacenamiento llega a 42 %.
- `keep_ban` y `resume_if_70` cumplen la tarea en los tres escenarios. `resume_if_70` entrega 6 puntos de riego en invierno normal o húmedo y nada en seco.
- Sin ley de probabilidad la cobertura es relativa: el kernel no establece frontera ni selección entre las dos factibles (`selection_status: OUTSIDE_DOMAIN`). Una ley sobre los inviernos permitiría la comparación completa.

Reproducir: `PYTHONPATH=twin:kernel python -m unittest twin.tests.test_case_denver_water` desde la raíz, o `python twin/cases/denver_water_2026/build.py` para regenerar el caso.
