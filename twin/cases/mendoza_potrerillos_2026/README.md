# Río Mendoza y Potrerillos, temporada 2026/27

Segundo caso real del gemelo dinámico. `world.json` lo genera `build.py` a partir de extractos textuales citados (Irrigación, MDZ, El Sol, Diario Uno). Cada número citado lleva su cita; los demás son hipótesis o decisiones declaradas.

## Situación (fuentes, octubre 2026)

- Potrerillos: 171 hm³ de 395 hm³ (43 %), reservas "extremadamente bajas".
- Pronóstico oficial del río Mendoza 2026/27: 1780 hm³, 129 % de un año medio. En 2025/26 escurrieron 797 hm³.
- Derrames previstos: diciembre 300, enero 320, febrero 250 hm³.
- Usos del año anterior: casi 300 hm³ potable y unos 500 hm³ para el agro.
- Irrigación prevé agua sobrante, menciona las lagunas y advierte riesgo de desbordes.

## Modelo

Unidad hm³, once pasos mensuales (noviembre 2026 a septiembre 2027). Un paso más con tres escenarios y tres opciones supera el límite de salida de 16 MB del gemelo en producción. Lo que excede la capacidad se registra como derrame no controlado.

| Opción | Regla |
|---|---|
| `dry_allocation` | Riego con la dotación del año seco (62,5 hm³ por mes de noviembre a mayo) |
| `reinforced` | Riego reforzado (93,75 hm³ por mes) |
| `reinforced_lagoons` | Reforzado, más 20 hm³ a las lagunas en los meses que empiezan con el embalse en 355 hm³ o más |

Escenarios: pronóstico oficial; por debajo del pronóstico como en 2025/26 (797/845); año como 2025/26 (797 hm³). Tarea operacional: al menos 25 hm³ en el embalse todos los meses. Bienestar: agua entregada a regantes y a las lagunas, y reserva de Potrerillos para Irrigación como organización (representación elegida por el modelizador). Sin ley de probabilidad.

### Hipótesis y decisiones para revisar

- Reparto mensual fuera de diciembre a febrero (propio); octubre de 2026 queda fuera del horizonte.
- Potable 25 hm³ por mes; riego de noviembre a mayo; refuerzo de 1,5 veces.
- Entrega ecológica de 20 hm³ con umbral 355 hm³, y mínimo de 25 hm³ (elecciones del modelizador).
- El escenario "año como 2025/26" es pesimista porque el pronóstico ya se apoya en nieve medida.

## Resultado del kernel

- Sólo `dry_allocation` cumple en los tres escenarios. Las dos reforzadas fallan en el año como 2025/26: en mayo no queda agua para la entrega de riego.
- Con el pronóstico, `dry_allocation` derrama 769 hm³ sin control y las reforzadas 550 hm³. El modelo no representa el daño de esos derrames, así que el kernel no los pesa; es la principal limitación del caso.
- Sin ley de probabilidad no hay frontera ni selección (`selection_status: OUTSIDE_DOMAIN`).

Reproducir: `PYTHONPATH=twin:kernel python -m unittest twin.tests.test_case_mendoza_potrerillos` desde la raíz.

## Predicción congelada y contraste

`prediction.json` congela, el 17/10/2026, la trayectoria del embalse para cada opción y escenario, con su calendario y los hashes del mundo y del modelo. `observations.json` acumula las lecturas reales posteriores con su diferencia exacta frente a cada trayectoria, sin recalibrar el modelo. Registrar una lectura (desde la raíz, con `PYTHONPATH=twin:kernel`):

```bash
python twin/cases/predictions.py contrast <caso> --date AAAA-MM-DD --value <valor> --observed-at <ISO8601> --source "<editor, URL y cita exacta>"
```

`twin.tests.test_predictions` falla si `world.json` cambia sin volver a congelar la predicción.
