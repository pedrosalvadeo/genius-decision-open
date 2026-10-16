# Genius: laboratorio de nodos con memoria independiente

Primera implementación experimental de la propuesta noosfera / Network Tierra /
TPing. Tres procesos ejecutan el mismo programa, cada uno con identidad estable,
SQLite propio y credenciales distintas. Se descubren entre pares previamente
inscritos, intercambian observaciones compartibles y conservan predicciones
congeladas. El experimento compara estimaciones aisladas y conectadas mediante
el kernel existente. **Es un laboratorio local, no una red pública desplegada ni
una demostración de organismos vivos o evolución abierta.**

## Ejecutar

Desde la raíz del repositorio, con el entorno Python del proyecto:

```sh
PYTHONPATH=adaptive:twin:kernel python -m federation.experiment --out /tmp/genius-federation-result.json
PYTHONPATH=adaptive:twin:kernel python -m unittest discover -s adaptive/tests -p test_federation.py -v
```

El destino del informe debe ser nuevo. Se crean tres servidores HTTP en puertos
efímeros de `127.0.0.1`, sin acceso a Internet, proveedores LLM, credenciales de
producción ni acciones externas. Se inicia un cuarto proceso para comprobar el
reinicio de una de las tres identidades. Al finalizar, incluso ante un error,
se detienen los procesos y se elimina **sólo** su almacenamiento temporal. Las
credenciales aleatorias viajan por pipes; nunca se incluyen en el informe.

Para mantener un nodo local entre ejecuciones existe `python -m
federation.transport --state DIRECTORIO --node-id IDENTIDAD`. Recibe por stdin
una línea JSON con `admin_token` y `read_token`, distintos, de 32–128 caracteres
ASCII. Ese operador administra su estado y el ciclo de vida del proceso. Los
tokens y la lista de pares se reintroducen al reiniciar; no se guardan en SQLite.
No habilitar este servidor en Internet: no implementa TLS, firmas públicas,
atestación de origen, defensa Sybil ni operación entre administradores hostiles.

## Contratos y límites

| Operación | Autoridad y comportamiento |
|---|---|
| `GET /hello` | Lectura: identidad, protocolo, capacidades, espacio restante y hash del programa. Equivalente funcional limitado de TPing. |
| `GET /experiences` | Lectura: únicamente observaciones con `shareable: true`, incluida su procedencia original. |
| `POST /observe` | Operador: ingresa observaciones locales en una transacción. |
| `POST /peers` | Operador: reemplaza la lista explícita de hasta ocho pares; sólo puerto local, identidad y token de lectura. |
| `POST /sync` | Operador: descubre un par inscrito y solicita sus observaciones. El receptor decide si las admite. |
| `POST /predict` | Operador: congela una estimación aislada o conectada, el contexto, regla, evidencia y ventana objetivo. |
| `POST /target` | Operador: registra el objetivo posterior y el error, sin reentrenar ni cambiar la predicción. |

La lectura de pares no permite mutaciones. No hay exploración de direcciones,
redirecciones, ejecución de código recibido, replicación, migración automática,
cron ni selección autónoma de misiones. El coordinador solicita los intercambios;
los datos viajan directamente entre servidores. Las cadenas de fuentes son datos
inertes, no destinos de red ni instrucciones.

`genius-node-observation/1` contiene:

- `context`: sistema, variable, unidad, régimen y clase `synthetic` o `reported`.
- `source`: origen, evento y extracto, declarados por el operador.
- `value`: entero no negativo de hasta 1 000 000 unidades declaradas.
- `observed_at`, `valid_until`: fechas con zona; la caducidad es una declaración,
  no una garantía de que el proceso mantenga su distribución.
- `shareable`: decisión explícita de permitir la transmisión.

Límites: 128 registros y 32 predicciones por memoria, ocho pares y 256 KiB por
mensaje; cada observación ocupa como máximo 1600 bytes. Excederlos rechaza el
lote entero, conservando el estado previo. Las llamadas tienen tiempo acotado.
No son presupuestos energéticos ni un sistema de homeostasis completo.

## Duplicados, conflictos y aprendizaje

El hash del contenido identifica la versión exacta. `(source.origin,
source.event)` identifica el evento declarado, conservado al retransmitir.
Un mismo registro recibido de varios pares cuenta una vez. Versiones diferentes
de un evento relevante suspenden la estimación con `CONFLICT_REVIEW`; no se
promedian ni se resuelven por mayoría. Incluso cambios de contexto o caducidad
quedan visibles como conflicto. Esta versión no resuelve conflictos ni modifica
registros previos: requiere una futura revisión explícita del operador.

Un hash verifica identidad de contenido, **no veracidad ni firma del emisor**.
Cambiar maliciosamente el identificador de una fuente puede ocultar dependencia;
no se afirma independencia estadística de los eventos o nodos. La procedencia
remota declarada no se convierte en observación local. Datos privados sólo
participan en cálculos de su nodo y nunca se exportan. Un permiso de exportación
no puede retirar copias ya recibidas; no introducir datos personales en este lab.

La regla experimental es la mediana inferior de eventos con contexto exactamente
igual y vigencia que cubra toda la ventana objetivo. Sin evidencia, la estimación
es `null`. Una desconexión conserva los datos previos, sujetos a su vigencia.
`isolated` considera únicamente registros ingresados localmente; `connected`
incluye los importados. No hay reglas por sector, inferencia semántica de
compatibilidad, aprendizaje causal ni federación de pesos de un LLM.

La predicción almacena sus dependencias antes del objetivo. `target_after: null`
significa después del instante de congelación; `target_before` fija el cierre.
El objetivo debe tener el mismo contexto, un evento nuevo y fecha posterior,
dentro de la ventana y no futura respecto de la recepción. Se registra una vez.
Repetir un ID idéntico recupera el recibo; cambiarlo produce conflicto. Una
regresión del reloj impide congelar evidencia recibida aparentemente en el futuro.
El reloj y la clasificación siguen bajo el mismo operador: no son un tercero
que certifique la medición. Los objetivos no se incorporan al entrenamiento.

## Qué mide el experimento

Dos situaciones sintéticas declaradas por adelantado:

1. Datos locales `alpha=[20]`, `beta=[80,100]`, `gamma=[100,120]`, objetivo 100.
   Compartir lleva las tres estimaciones a 100 y reduce el error total de 100 a 0.
2. Datos locales `alpha=[0]`, `beta=[100]`, `gamma=[100]`, objetivo 0.
   Compartir lleva las tres estimaciones a 100 y aumenta el error de 200 a 300.

El caso adverso muestra por qué compatibilidad declarada y más datos no bastan.
Se conservan las dos comparaciones, sin adoptar automáticamente una política.
El modelo de comparación existente verifica con el kernel la aritmética del
error: elige `connected` en la primera situación e `isolated` en la segunda.
Esto es un criterio operacional acotado y no modifica la matemática de bienestar,
CAG, PVS, regulación ni las políticas previamente rechazadas.

Hay **dos objetivos sintéticos**, cada uno evaluado por tres nodos y dos modos;
los tres errores de una situación no son tres observaciones independientes.
Las predicciones se congelan antes de entregar los objetivos a los procesos,
pero los valores están visibles en el código del experimento. No es un estudio
ciego, una validación prospectiva de campo ni evidencia de mejora universal.
El informe incluye también duplicación, privacidad, contradicción, desconexión,
continuidad local y persistencia tras reiniciar. No mide acciones físicas,
bienestar, probabilidad de vida, evolución de código ni consumo energético.

## Relación con lo construido y siguiente etapa

Se reutilizan el modelo de comparación y el kernel actuales. Este módulo está
separado del servicio web y no añade rutas MCP, tablas de producción, servicios
Railway o costos de API. El constructor general de modelos sigue disponible;
este experimento sólo comparte observaciones escalares y conserva resultados
localmente. Compartir modelos y experiencias completas es una etapa posterior.

Próximo paso: acordar contextos verificables y reglas de admisión de evidencia,
resolver contradicciones con trazabilidad, compartir recibos de modelos y
resultados, y contrastar una tarea con datos posteriores independientes. Para
operadores distintos harán falta identidades firmadas, autorización y transporte
seguro. Recién entonces ampliar a máquinas voluntarias, presupuestos medidos y
acciones autorizadas. La continuidad de un nodo permanece subordinada al
responsable de su infraestructura y al propósito del proyecto.

Inspiración, sin reutilizar código de Tierra:

- [Network Tierra FAQ, Tom Ray](https://tomray.me/tierra/netfaq.html): hábitats
  instalados por sus participantes y organismos dentro de esa red.
- [Network Ancestor, Tom Ray](https://tomray.me/pubs/complexity/node4.html): TPing
  como percepción de condiciones en otros nodos.
- Noosfera se usa aquí como metáfora operacional de conocimiento compartido,
  no como afirmación de conciencia colectiva.
