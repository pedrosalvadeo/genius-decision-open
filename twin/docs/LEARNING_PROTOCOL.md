# Protocolo de aprendizaje del organismo Genius (borrador para revisión)

La matemática de Genius es finita y exacta, y no define una operación de aprendizaje o de revisión de modelos. Lo más cercano son la conmutación de las actualizaciones de información con la representación (AM-01) y el refinamiento de evaluaciones (definición 8.12). Este protocolo propone cómo aprende el organismo **fuera del kernel**, sin cambiar lo que el kernel calcula. Necesita la revisión de Pedro antes de considerarse parte de Genius.

## Qué aprende

El organismo aprende **cómo construir mejores gemelos**, no reglas de bienestar. Su genoma son datos acotados, nunca código (`executable_mutation: False`, como en `adaptive/federation/genetics.py`). El primer genoma (`twin/history/hindcast.py`) decide cómo corregir una proyección oficial con sus errores pasados:

| Gen | Alelos |
|---|---|
| `correction` | `none`, `median`, `mean` del error pasado al mismo plazo |
| `window` | últimos 12, 36 o 120 errores conocidos |

## Con qué aprende

1. **Historia antes que espera.** Toda proyección pasada cuyo mes ya ocurrió es un contraste disponible hoy. Por ejemplo, los 24-Month Study de Reclamation desde 2009 dan miles de contrastes, sin esperar lecturas nuevas.
2. **Sólo el pasado publicado.** Para juzgar una proyección emitida en el mes *s*, el organismo usa sólo errores de meses anteriores a *s* cuyo valor real ya estaba publicado en *s*.
3. **Mediciones cruzadas.** Un valor real que estudios posteriores corrigen queda registrado como revisión (`revisions`). Cuando haya más de una fuente para la misma variable, las discrepancias marcan lecturas dudosas en lugar de aceptarlas.

## Cómo selecciona

Se usa la misma regla que los organismos de los hábitats, en fases cronológicas disjuntas:

1. **Descubrimiento:** se prueban los mutantes de un solo gen sobre un bloque de objetivos. Es elegible el que tenga menor error absoluto total sin empeorar el error máximo.
2. **Confirmación:** el elegido debe repetir la mejora sobre el bloque siguiente, que no vio. Sólo entonces se adopta.

El criterio es `OBSERVED_ABSOLUTE_ERROR_NOT_WELLBEING_OR_PVS`. Acertar más no es más bienestar ni más probabilidad de vida sostenida; sólo mejora la información con la que el kernel calcula.

## Qué puede cambiar y qué no

- **Nunca cambia** el kernel, una predicción congelada ni un gemelo ya confirmado.
- **Sí puede proponer** un escenario nuevo para un gemelo (por ejemplo, "mínimo de Reclamation corregido por su error histórico"). Lo marca con procedencia `LEARNED_FROM_HINDCAST` y el genoma, los objetivos y las fases que lo justifican. Como cualquier mundo, entra al gemelo sólo con la confirmación de quien decide (`twin_accept`).
- **Nunca actúa** en el mundo ni contacta a terceros por su cuenta.

## Próximos genes

- Elegir qué fuentes usar y cómo ponderarlas cuando discrepan.
- Ensanchar el rango de escenarios según cuántas veces la realidad cayó fuera.
- Construir escenarios a partir del registro histórico propio cuando no hay proyección oficial.

Cada gen nuevo se agrega con su prueba sintética y su contraste histórico antes de usarse.
