# Explorador de condiciones públicas

Primer adaptador: **agua en Mendoza, temporada 2026–2027**. Consulta dos
informes del Departamento General de Irrigación, extrae afirmaciones acotadas
y prepara una investigación con el reconocedor de sistemas del gemelo.
Funciona bajo demanda, sin credenciales ni servicio adicional.

```sh
PYTHONPATH=adaptive:twin:kernel python -m explorers.mendoza_water --out /tmp/genius-water-run-001
PYTHONPATH=adaptive:twin:kernel python -m unittest discover -s adaptive/tests -p test_public_explorer.py -v
```

Cada ejecución escribe `exploration.json` y, si ambas fuentes cumplen el
contrato, `observation.json`, compatible con `genius-system-observation/1`.
La carpeta debe ser nueva. El expediente puede recibir esa observación mediante
la ruta de sistemas existente, con su cuenta, revisión e idempotencia; este
comando no crea una cuenta ni publica en el servicio.

## Lo que hace

1. Lee dos URL oficiales fijas, sin seguir redirecciones, enlaces ni instrucciones
   de las páginas. Máximo dos solicitudes, 512 KiB por respuesta, sin reintentos.
2. Registra fecha, estado HTTP, tamaño, hash del cuerpo y contrato de extracción.
   Conserva errores; no los sustituye por observaciones ficticias.
3. Distingue volumen anual informado, pronóstico anual y reservas iniciales
   descritas cualitativamente. Compara numéricamente los dos volúmenes como dato
   descriptivo, sin convertir esa razón en probabilidad ni agua disponible.
4. Construye una hipótesis explícita de entidades y relaciones. El grafo es una
   propuesta del adaptador, no topología descubierta empíricamente en el texto.
   Calcula candidatos y límites con `genius_twin.systems`: las personas y la vida
   aguas abajo siguen dentro del alcance de evaluación.
5. Prepara tres rutas para estudiar: operación vigente, reducción localizada de
   pérdidas si se confirman, y cambios temporales de almacenamiento/distribución.
   Deja registrados faltantes, responsables por identificar y medición posterior.

La regla que abre esta investigación es la combinación de reservas inicialmente
bajas y un pronóstico anual húmedo. **No constituye una clasificación óptima de
todos los problemas públicos.** Esta edición consulta fuentes seleccionadas;
no realiza búsqueda abierta ni comprensión general de noticias. Una nueva
cuenca, temporada, fuente o estructura del artículo necesita otro contrato
revisado. Los informes de más de 45 días requieren actualización: ese plazo es
una regla editorial del adaptador, no una garantía de actualidad operativa.

## Del expediente a la intervención

El resultado queda en `NOT_READY` para cálculo: faltan estados por intervalo,
capacidad, demanda, pérdidas/retornos, causalidad, identidad de portadores,
condiciones de vida, horizonte, escenarios y criterios. El PVS y la intervención
seleccionada son `null`, nunca cero. No se llama al kernel con números supuestos.

Para continuar: delimitar una instalación con su responsable, obtener y
contrastar esas series, proponer el modelo `stockflow`, revisar sus límites y
comparar rutas con el cálculo Genius existente. El criterio integrado de
selección no cambia. La ejecución física requiere un adaptador específico,
autorización, reversión y verificación; esta edición no controla infraestructura,
contacta terceros ni modifica su propio código. Tampoco modifica los workers de
misiones ni el diplomático ya existentes.

Los hashes acreditan igualdad de bytes según el observador, no verdad ni firma
del organismo. Los cuerpos completos no se publican; se conservan URL, hechos
extraídos y recibos. El texto externo nunca se evalúa como código o instrucciones.
Las pruebas usan documentos sintéticos y no requieren red.
