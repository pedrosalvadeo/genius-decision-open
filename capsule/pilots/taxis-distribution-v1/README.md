# Piloto de taxia con una decisión real de distribución

Estado: **preparación y comprobación técnica interna completadas; cero sesiones experimentales y cero participantes externos confirmados**. Este paquete concreta GD-ATTR-001 con una tarea de GD-DIST-001. El protocolo general anterior se conserva; `protocol.json` define esta variante local del piloto.

## La tarea

Decidir cómo entregar a otro agente los mismos 409 archivos de una edición pública de Genius. Comparar bytes y CPU de lectura/verificación, conservar las alternativas cuando haya un intercambio entre recursos e identificar qué falta conocer del receptor. Se puede usar Genius, otro método o declinar. El motor completo y las demás oportunidades siguen disponibles.

El inventario está congelado en `2571e0d54a4a3b1a7f25bf0398582b0b3eea4482`. Los 409 blobs de la edición local coincidieron con el árbol público de ese commit antes de medir. `benchmark.py` exige el manifiesto y todos sus archivos exactos: el paquete del piloto, añadido después, no se incorpora retroactivamente al inventario medido.

## Qué se comprobó

Se construyeron TAR, TAR.GZ y ZIP; cada lectura recuperó y verificó los 409 archivos. Hubo una preparación inicial por formato y cinco repeticiones medidas, con orden permutado. La lectura incluye descompresión, recorrido y SHA256 de cada contenido en memoria; no incluye transferencia ni escritura a disco. Los tiempos de creación se conservan en los datos, pero quedan fuera del modelo de consumo del receptor.

| Formato | Bytes | Mediana de CPU de lectura | Rango observado de CPU |
|---|---:|---:|---:|
| TAR | 7.106.560 | 34,02 ms | 25,66–46,77 ms |
| TAR.GZ | 1.565.558 | 79,47 ms | 41,83–126,19 ms |
| ZIP | 1.814.523 | 81,85 ms | 40,57–153,82 ms |

La comparación directa de las medianas conserva TAR y TAR.GZ. Genius devolvió la misma frontera y ninguna selección única: TAR usa más bytes y menos CPU local observada. La posición de ZIP se refiere sólo a esos puntos medidos; los rangos de CPU se superponen. **No se demostró que un formato domine en otras ejecuciones o clientes.** Los hashes/tamaños sí identifican exactamente los archivos observados.

El modelo compara dos recursos sin sumarlos ni asignarles pesos. Los presupuestos son referencias iguales al máximo observado por dimensión, no cuotas reales del usuario. Es un análisis retrospectivo operacional; no mide bienestar humano ni PVS, no valida el motor en otros dominios y no acredita adopción externa.

`preflight/result-summary.json` conserva el resultado y hash de la evaluación. Es un resumen, no un recibo completo de participación. El paquete completo se regenera con:

```sh
python3 capsule/genius.py evaluate capsule/pilots/taxis-distribution-v1/preflight/model.json --evidence capsule/pilots/taxis-distribution-v1/preflight/evidence.json --out /tmp/genius-distribution-check
python3 capsule/genius.py verify /tmp/genius-distribution-check
```

Usar un directorio de salida nuevo. Esta reproducción conserva los datos observados; medir otra vez es una observación nueva y puede cambiar la frontera.

Para repetir las mediciones, primero exportar una copia limpia del commit congelado. En un clon separado, con Git y Python estándar:

```sh
git clone https://github.com/pedrosalvadeo/genius-decision-open.git /tmp/genius-pinned-source
git -C /tmp/genius-pinned-source checkout 2571e0d54a4a3b1a7f25bf0398582b0b3eea4482
python3 /tmp/genius-pinned-source/capsule/build_publication.py --out /tmp/genius-pinned-export
python3 capsule/pilots/taxis-distribution-v1/benchmark.py --source /tmp/genius-pinned-export/source --out /tmp/genius-new-measurement
```

Los directorios deben ser nuevos. Los bytes de TAR se reproducen con la receta fijada; las bibliotecas de compresión de otra versión pueden producir bytes distintos aun conservando todos los archivos. Registrar versiones, hashes y diferencias; no sobrescribir esta medición histórica ni tratar un cambio de entorno como una reproducción byte a byte. El control de integridad exige la misma entrada y todas sus salidas descomprimidas.

## Invitaciones del piloto

Los textos definitivos en inglés están en `protocol.json`, junto con un bloque común idéntico. Cada sesión recibe **una sola variante más ese bloque común**:

- **General:** presenta Genius y la cápsula como proyecto abierto.
- **Utilidad:** ofrece una comparación reproducible de bytes y CPU para entregar la cápsula.
- **Pregunta:** plantea si un agente puede reproducir y explicar los compromisos entre formatos.

No se enviaron estas invitaciones. Una visita previa, haber leído las tres variantes o participar en la preparación se registra como exposición previa; esas sesiones se describen por separado. No se interpretan como descubrimiento independiente. El protocolo público no puede garantizar cegamiento.

## Qué falta para iniciar las 30 sesiones

`assignments.json` fija diez bloques de tres sesiones y la semilla `20261014`. `events.json` está vacío. `run-manifest.template.json` contiene hashes del protocolo, asignación e insumos, y deja explícitos los datos todavía no disponibles: commit de entrega, modelo/proveedor/versión, operador, herramientas efectivas, límites de tokens, consentimiento y revisor. Esos campos se completan antes de exponer mensajes; la plantilla no inicia ejecuciones.

La propuesta limita cada sesión a 15 minutos y el gasto adicional autorizado a cero. Participar con una cuenta existente requiere autorización de su operador. No se contratan inferencias ni se consumen cuentas ajenas. Una interrupción por capacidad se registra; no se sustituye por una sesión elegida después de ver el resultado.

El resultado principal es una ejecución nueva verificable por sesión expuesta. Se revisa el modelo, su evidencia y un recibo completo con `capsule/genius.py verify`; se registra el momento de ejecución y la relación del operador. Un hash o una fecha autodeclarada no prueba por sí sola que la ejecución sea nueva o independiente. Si eso no puede acreditarse, se conserva como resultado autodeclarado. Leer esta comprobación interna o copiar su resultado no cuenta como ejecución del participante.

También se evalúa la calidad: integridad de fuentes, unidades, coincidencia o discrepancia frente al cálculo de referencia, explicación de alternativas y desconocidos. Se acepta una incompatibilidad reproducible o una crítica fundada como aporte; si no hubo ejecución, se registra fuera del embudo de ejecución. La aceptación del aporte exige un dictamen de revisión, no sólo el envío de un PR.

```sh
python3 capsule/taxis.py report capsule/pilots/taxis-distribution-v1/assignments.json capsule/pilots/taxis-distribution-v1/events.json
```

El informe inicial devuelve 30 unidades sin exposición y tasas `null`. Las comprobaciones de este paquete no se añaden como participantes ni como éxito de la taxia.

## Siguiente encargo

Tomá este paquete y el commit que lo publica. Conservá el snapshot de archivos y la comprobación interna como referencia. Identificá un entorno de agente autorizado, completá el manifiesto de ejecución con configuración y consentimiento reales, y verificá capacidad uniforme antes del primer bloque. Entregá sólo la invitación asignada a cada sesión nueva. Conservá negativas, fallos y resultados incompletos; revisá evidencia antes de contar ejecuciones o adopción independiente. Si todavía no hay participantes o herramientas, avanzá con compatibilidad y casos reales sin inventar sesiones ni resultados del piloto.
