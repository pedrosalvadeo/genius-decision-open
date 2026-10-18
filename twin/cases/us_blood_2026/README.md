# Sangre tipo 0 en EE. UU., invierno 2026/27

Primer caso real fuera del agua. Usa los mismos ocho módulos, el mismo kernel y el mismo catálogo de funciones que los casos de agua. `world.json` lo genera `build.py` a partir de extractos citados. El nodo de historia comprobó cada cita contra la página viva (`twin/history/source_quotes.py` con `twin/history/blood_2026/quotes.json`). Cada número citado lleva su cita; los demás son hipótesis o decisiones declaradas.

## Situación (fuentes, enero a octubre de 2026)

- 27/07/2026: la Cruz Roja declaró su segunda crisis nacional de sangre, con menos de un día de 0 positivo, y limitó la distribución de tipo 0 a las emergencias que amenazan la vida.
- El tipo 0 es cerca del 60 % de lo que distribuye la Cruz Roja, y esta debe recolectar más de 13.000 donaciones por día.
- Enero de 2026, en la temporada de gripe más alta del registro (pico de ILINet de 8,30 %): la reserva cayó cerca de 35 % en un mes.
- Septiembre: la crisis había cedido, pero el suministro sigue vulnerable. Octubre: fondo de 300 millones de dólares para la base de donantes.

## Modelo

La unidad es mil unidades de glóbulos rojos tipo 0. Hay ocho pasos quincenales, del 1 de noviembre de 2026 al 20 de febrero de 2027.

| Opción | Regla |
|---|---|
| `as_usual` | Seguir igual |
| `defer_below_two_days` | Postergar las cirugías programadas cuando la reserva baja de 2 días |
| `campaign` | Campaña de donantes en noviembre y la primera quincena de diciembre (+5 %) |
| `campaign_and_defer` | Campaña y postergación |

Los escenarios son gripe leve, moderada y grave, anclados en los picos de 2015/16, 2004/05 y 2025/26. La ley es un tercio cada uno, declarada: AM-02 sobre los picos de gripe tiene 29 temporadas y exige 30, así que se admitirá con la temporada 2026/27.

- **Condición de vida:** la reserva nunca baja de un día (7,8 mil unidades) para los pacientes de trauma y emergencias.
- **Bienestar:** la sangre que reciben los pacientes de cirugías programadas, la reserva de la Cruz Roja y las donaciones extra que no se piden a los donantes.
- **Funciones (módulo I):** abastecer a los hospitales con 2 días o más (`health`) y sostener la reserva de un día (`safety`).

### Hipótesis para revisar

- La distribución de tipo 0 es de 7,8 mil unidades por día (60 % de 13.000).
- El 15 % de esa distribución va a cirugías que se pueden postergar.
- La reserva inicial es de 2,5 días. La Cruz Roja no publica la reserva, y esta es la hipótesis que más pesa en el resultado.
- La gripe grave repite la caída de enero de 2026 (35 % de la reserva inicial por mes, del 13/12 al 6/2); la moderada, la mitad.
- La campaña suma 5 % a la recolección durante tres quincenas.

## Resultado del kernel

- **Condición de vida:** `as_usual` la incumple con gripe grave, porque la reserva baja a 5,85 mil unidades (0,75 días) a fines de enero. Su PVS es 2/3 con la ley declarada y va de 0 a 1 según la ley. Las otras tres opciones mantienen PVS = 1 con cualquier ley.
- **Postergar** protege la reserva a cambio de 16,38 mil unidades menos para cirugías programadas con gripe moderada o grave.
- **La campaña** sostiene la reserva sin postergar nada y pide 16,38 mil donaciones extra; con ella, la postergación nunca se activa.
- **Por actor:** pacientes de emergencias y de cirugías y la Cruz Roja prefieren la campaña; los donantes prefieren postergar. No hay selección única: elegir entre pedir más a los donantes o postergar cirugías es una decisión de valores.
- **Funciones:** la campaña domina a postergar en el abastecimiento a hospitales, y las tres opciones viables dominan a seguir igual.

Reproducir: `PYTHONPATH=twin:kernel python -m unittest twin.tests.test_case_us_blood` desde la raíz.
