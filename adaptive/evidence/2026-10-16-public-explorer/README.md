# Primera exploración pública — agua en Mendoza

Ejecución real del 16 de octubre de 2026, 06:05 UTC. El adaptador consultó dos
páginas oficiales mediante HTTPS; ambas devolvieron HTTP 200. El
[recibo completo](exploration.json) incluye fechas, tamaños, hashes, hechos
extraídos, reconocimiento de sistemas y expediente de investigación.
[Observación compatible con el gemelo](observation.json).

## Condición identificada

El [informe de Irrigación del 2 de octubre](https://www.irrigacion.gov.ar/web/2026/10/02/informe-de-la-situacion-hidrica-a-partir-del-pronostico-de-escurrimientos-temporada-2026-2027/)
informa 797 hm³ para el río Mendoza en 2025–2026 y prevé 1780 hm³ en Guido
para 2026–2027, equivalentes al 129% de la media histórica. La
[presentación de esa temporada](https://www.irrigacion.gov.ar/web/2026/10/02/pronostico/)
describe reservas iniciales bajas y aclara que la previsión anual no determina
el volumen disponible cada día. No se extrapoló como actual el pronóstico de
sequía de la temporada anterior.

La diferencia aritmética es 983 hm³ y la razón es 1780/797. Comparan una previsión
con un volumen anual informado: no son un beneficio obtenido, agua libre ni una
probabilidad de sostenimiento de vida.

## Investigación preparada

Objetivo: estudiar cómo sostener abastecimiento y condiciones de vida durante
esa transición. El adaptador propone un grafo de siete entidades: agua del río,
almacenamiento, distribución, organismo informante, comunidades, agroecosistemas
y vida aguas abajo. Las relaciones son hipótesis explícitas, no hallazgos
causales ni un inventario verificado de infraestructura, personas o especies.

El reconocedor calcula agrupaciones y conserva los tres grupos vivos dentro
del alcance de evaluación de la infraestructura. Las rutas propuestas son:
operación vigente; reparación localizada de pérdidas si existen; y cambios
en tiempos de almacenamiento/distribución. Ninguna se ha seleccionado.

Estado: **investigación preparada; cálculo pendiente de datos**. Faltan series
operativas, capacidades, pérdidas y retornos, efectos, condiciones de los
portadores, escenarios y responsables. No se ejecutó el kernel con parámetros
inventados ni se realizaron intervenciones o contactos. El comando no queda
corriendo ni programado por guardar este expediente.

Próximo trabajo concreto: escoger con un responsable un tramo o instalación,
conseguir esas mediciones en intervalos comunes, contrastar la topología y
proponer el modelo. Luego se podrán calcular y comparar las rutas con Genius,
autorizar una intervención delimitada y medir sus consecuencias.

Reproducción: ver [comando y límites](../../explorers/README.md). El adaptador
relee los informes seleccionados; no recorre toda la web ni demuestra que éste
sea el problema de mayor prioridad. El resultado depende de las fuentes y reglas
revisadas, y puede pedir revisión si su contenido cambia.
