# Río Mendoza y Potrerillos, temporada 2026/27

Segundo caso real del gemelo dinámico. `world.json` lo genera `build.py` a partir de extractos textuales citados (Irrigación, MDZ, El Sol, Diario Uno). Cada número citado lleva su cita; los demás son hipótesis o decisiones declaradas.

## Situación (fuentes, octubre 2026)

- Potrerillos: 171 hm³ de 395 hm³ (43 %), reservas "extremadamente bajas".
- Pronóstico oficial del río Mendoza 2026/27: 1780 hm³, 129 % de un año medio. En 2025/26 escurrieron 797 hm³.
- Derrames previstos: diciembre 300, enero 320, febrero 250 hm³.
- Usos del año anterior: casi 300 hm³ potable y unos 500 hm³ para el agro.
- Irrigación prevé agua sobrante, menciona las lagunas y advierte riesgo de desbordes.

## Modelo

Unidad hm³, doce pasos mensuales (noviembre 2026 a octubre 2027). Lo que excede la capacidad se registra como derrame no controlado.

| Opción | Regla |
|---|---|
| `dry_allocation` | Riego con la dotación del año seco (500 hm³ en la temporada) |
| `reinforced` | Riego reforzado (750 hm³) |
| `reinforced_lagoons` | Reforzado, más 20 hm³ a las lagunas en los meses que empiezan con el embalse en 355 hm³ o más |

Escenarios: pronóstico oficial; por debajo del pronóstico como en 2025/26 (797/845); año como 2025/26 (797 hm³). Tarea operacional: al menos 25 hm³ en el embalse todos los meses. Bienestar: agua entregada a regantes y a las lagunas. Sin ley de probabilidad.

### Hipótesis y decisiones para revisar

- Reparto mensual fuera de diciembre a febrero (propio).
- Potable 25 hm³ por mes; temporada de riego noviembre a mayo y octubre; refuerzo de 1,5 veces.
- Entrega ecológica de 20 hm³ con umbral 355 hm³, y mínimo de 25 hm³ (elecciones del modelizador).
- El escenario "año como 2025/26" es pesimista porque el pronóstico ya se apoya en nieve medida.

## Resultado del kernel

- Sólo `dry_allocation` cumple en los tres escenarios. Las dos reforzadas fallan en el año como 2025/26 (el embalse termina en 11,8 hm³ y falla una entrega).
- Con el pronóstico, `dry_allocation` derrama 843 hm³ sin control y las reforzadas entre 605 y 625 hm³. El modelo no representa el daño de esos derrames, así que el kernel no los pesa; es la principal limitación del caso.
- Sin ley de probabilidad no hay frontera ni selección (`selection_status: OUTSIDE_DOMAIN`).

Reproducir: `PYTHONPATH=twin:kernel python -m unittest twin.tests.test_case_mendoza_potrerillos` desde la raíz.
