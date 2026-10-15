# Observación privada de la regulación

`beta/tools/regulation_observation.py` resume la memoria operativa ya persistida.
Es una herramienta del operador, no un endpoint ni una tarea automática del worker.
No modifica la política, ejecuta misiones, cambia cuotas ni propone/promueve código.
Su objetivo es describir la evidencia disponible antes de diseñar otro ensayo.

## Lectura y privacidad

Necesita una ruta explícita a la base privada existente. Abre SQLite con URI
`mode=ro`, `query_only=ON` y una única transacción de lectura; incluye los datos
confirmados del WAL y no usa `immutable=1`. No llama al inicializador, migraciones,
purga o recuperación. Limita a 513 filas la lectura del diario para detectar un
exceso del máximo de 512; limita cada JSON a 16 KiB y el presupuesto de lectura
a 20 millones de instrucciones de SQLite. Una base ocupada/incompatible produce
un error, no un informe vacío presentado como saludable.

Sólo consulta el estado/diario de regulación y `status,count(*)` de misiones.
La salida se construye por una lista explícita de campos: no incluye entradas,
resultados, artefactos, IDs de cuentas/misiones, el marcador aleatorio activo,
credenciales, direcciones de clientes ni rutas. Tampoco copia recibos crudos.
El archivo sigue siendo **privado**: contiene actividad agregada del servicio.
Se crea exclusivamente con permisos 0600, sin sobrescribir ni seguir un enlace
preexistente; la consola sólo confirma escritura o un código de error fijo.
No se debe agregar un informe real, la base o su WAL a GitHub.

Ejecutar en un entorno autorizado con acceso a la base o a un respaldo consistente
ya restaurado de forma privada. Reemplazar `INICIO_UNIX` y `FIN_UNIX` por segundos
Unix enteros; el final no puede estar en el futuro:

```sh
PYTHONPATH=beta python -B beta/tools/regulation_observation.py \
  --database /ruta/privada/genius.sqlite3 \
  --since INICIO_UNIX --until FIN_UNIX \
  --output /ruta/privada/observacion.json
```

`source.declared=production` es una declaración del operador, no una verificación
del origen. `--source synthetic` declara un ensayo. La herramienta no descarga
bases, accede a Railway, busca credenciales ni envía archivos. Este incremento
no se desplegó en el servicio: ejecutar el informe sobre la base real sigue
pendiente de un entorno con acceso autorizado a esa base.

## Qué significan los números

| Campo | Interpretación exacta |
| --- | --- |
| `retained_window_events` | Eventos retenidos cuya fecha está en `[inicio, fin)`: arranques, finales por categoría, interrupciones desconocidas y transiciones. Son intentos registrados, no usuarios ni misiones únicas. |
| `recorded_elapsed_seconds` | Segundos enteros registrados por finales en esa ventana. Incluye la duración completa aunque el arranque sea anterior al inicio. Mínimo, máximo y percentiles por rango más próximo; sin muestras devuelve `null`, no cero. No son percentiles HTTP ni tiempos de cola. |
| `interrupted_unknown` | Intentos recuperados tras reinicio sin resultado conocido. No son éxitos, fallos operativos confirmados ni muestras de duración. |
| `current_snapshot` | Estados de las misiones que siguen almacenadas al leer y estado persistido del regulador. Es una fotografía actual, independiente de la ventana histórica; no se reconstruyen estados pasados con `updated_at`. |
| `active_age_seconds` | Edad del marcador persistido al leer. No prueba que el proceso siga vivo ni que progrese. La habilitación efectiva del runtime no está en la base: se devuelve `null`. |
| `coverage` | Tamaño/fechas del diario retenido, huecos visibles de secuencia, prefijo borrado detectable, llegada al límite y ventana anterior a siete días. Nunca certifica cobertura completa. |

El diario retiene hasta 512 eventos y siete días; la poda, los borrados, periodos
deshabilitados y arranques previos pueden dejar observaciones ausentes. Ni siquiera
un diario vacío demuestra ausencia de trabajo. Los huecos detectables no prueban
que otros huecos no existan. No se estima tiempo por modo a partir de transiciones
dispersas ni se suman señales de cola como si fueran muestreo periódico completo.

El programa valida todos los eventos retenidos antes de emitir métricas. Rechaza
política/protocolo/modo/tipo de evento desconocidos, JSON inválido o excesivo,
relojes incoherentes, categorías de resultado y duraciones inválidas. No salta
silenciosamente esas filas para producir una tasa aparente de éxito. Un estado
antiguo conserva su modo persistido con `freshness=stale`, sin certificar salud.

No están instrumentados: espera en cola por intento, llegadas/rechazos completos,
área de tareas pendientes en el tiempo, disponibilidad continua, mejora causal
frente a otra política ni bienestar/PVS. `eligible_for_policy_promotion=false`.
Las métricas HTTP de Railway son otra fuente y no sustituyen esos resultados.

## Validación y siguiente paso

Trece pruebas nuevas usan SQLite/WAL y las transiciones del regulador real con
reloj/sensores sintéticos. Cubren los significados anteriores, lectura durante una
transacción escritora no confirmada, conservación de la base/WAL, límites, errores,
salida privada y reproducción exacta del ejemplo. El workflow Club las incluye.

Ejemplo reproducible y publicable **sólo porque todos sus datos son sintéticos**:

```sh
PYTHONPATH=beta python -B beta/experiments/regulation-observation/example.py \
  --output /tmp/genius-observacion-sintetica.json
```

El archivo de destino debe ser nuevo. Recibo esperado:
[`synthetic.json`](../../adaptive/evidence/2026-10-15-regulation-observation/synthetic.json).
Contiene un final completado, un fallo operativo, un resultado neutro y una
interrupción desconocida; las tres filas actuales de misión son una fotografía
independiente. La prueba pública autenticada continúa pendiente del límite de
registro. Tras esa prueba y una lectura privada real, decidir qué instrumentación
de admisión/cola hace falta antes de ampliar la búsqueda de reglas. Los dos
ensayos sintéticos anteriores y sus rechazos se conservan intactos.
