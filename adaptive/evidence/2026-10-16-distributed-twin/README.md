# Tres vistas, un gemelo más amplio

Ejecución local con procesos reales y datos **enteramente sintéticos**.
[Informe completo](experiment.json), [pruebas](tests.txt),
[contrato y reproducción](../../federation/DISTRIBUTED_TWIN.md).

| Cobertura disponible | Resultado |
|---|---|
| Cada vista aislada | Modelo incompleto; faltantes explícitos. |
| Agua + energía/mantenimiento | Falta la vista comunitaria para completar el cálculo. |
| Las tres vistas | Modelo formalmente preparado para revisión y cálculo condicional. |

Ocho menciones locales corresponden a seis entidades únicas. El alcance desde
la bomba integra reserva, energía, mantenimiento, suministro y comunidad. Las
identidades fueron declaradas por el modelizador; el programa no las descubrió
por similitud de nombres. Las relaciones y mecanismos son hipótesis sintéticas.

El kernel verifica las rutas declaradas: esperar conserva `1,1,1,1` litros de
entrega acumulada; restaurar y luego bombear da `1,1,3,5`. Se incluye el estado
inicial. La probabilidad queda desconocida y no se elige una intervención real.
El equipo físico permanece como entidad no representada completamente en el
cálculo, con revisión de alcance pendiente.

Pasan 14 comprobaciones del experimento y 80 pruebas adaptativas (14 nuevas).
Otro nodo reconstruye el mismo modelo; duplicación, desconexión y reinicio no
agregan entidades ni borran las vistas. El informe conserva vistas, proyecciones,
fuentes, recibos, trayectorias, verificación nativa y hashes del programa.

Las bases temporales y los procesos se eliminaron al terminar. No hay tokens en
el informe, cambios en Railway, intervención física, validación empírica o medida
de bienestar/PVS. La red sólo conoce lo que contienen estas vistas declaradas.
