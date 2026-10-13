# Arquitectura local GENIUS R2

Autor: `/root/r2_a_supervisor`. Fecha: 2026-10-03. Capa externa al Kernel conservado. Gramática y firmas: `INTERFACE.md`; límites y fallos: `OPERATIONAL_PROFILE.md`; obligaciones normativas: `CONTRACT_MAPPING.md`.

## Flujo y responsabilidades

La CLI recibe solicitud, expediente y rutas de dependencias explícitas. El controlador valida la solicitud, importa los bytes a almacenamiento por digest y registra el inicio. Ejecuta las fases en orden; cada operación produce un resultado ligado a la consulta exacta. La política construye la respuesta común y cierres desde esas evidencias. Finalmente el almacén publica una revisión completa que puede reconstruirse sin el proceso original.

| Módulo | Responsabilidad | Frontera |
|---|---|---|
| `store.py` | Bytes por SHA-256, revisiones, cadena, publicación atómica y verificación | No decide verdad, compatibilidad o suficiencia |
| `controller.py` | Presupuestos, orden, importación, ejecución, cancelación y continuación | No cambia las matemáticas ni admite modelos por cuenta propia |
| `policy.py` | Gramática estricta, obligaciones/DAG, compatibilidad y sobre de cuatro capas | Una correspondencia documental no autentica hechos físicos |
| `operations.py` | Reutilización, racionales, reglas acotadas y coordinación FDQ | Sólo reglas explícitas; desconocido no es cero |
| `fdq_worker.py` | Aislar el verificador recibido con sus pines y preservar el recibo | No amplía el perfil FDQ ni sintetiza Result al fallar |
| CLI | Frontera local por archivos y salida JSON | No es protocolo remoto, aplicación R3 ni servicio permanente |

## Separación de autoridades

Input y Result FP1 son artefactos inmutables de la instancia recibida. El certificado FDQ es un tercer artefacto con su propio verificador y afirmación condicional. El worker importa sólo una copia temporal limpia de los bytes ejecutables recibidos y comprobados por hash. Las carpetas originales no entran en la ruta de importación. La respuesta de producto enlaza los tres y explica qué consulta respondió cada uno. Una consulta formal suficiente no cambia `RELATIVE`, `OUTSIDE_DOMAIN`, G01–G15 ni el selector del Result original.

Los artefactos del llamador se tratan como entradas, incluidas sus etiquetas. La compatibilidad calcula coincidencias desde valores/base; el certificado se recomputa contra Input/Result; el cierre se deriva de los resultados del motor local. Campos `expected` de casos pertenecen al cliente de pruebas, nunca al expediente como autoridad de decisión.

La admisión de una ley, identidad física, significado de CAG, tarea, preferencia o consentimiento queda en una obligación con evidencia y responsable. Los fixtures sintéticos muestran conformidad operacional; no prueban una ruta de macetas ni utilidad de consumidores.

## Trazabilidad operacional

El almacén liga bytes → solicitud/consulta → operación → resultado → respuesta → revisión. La revisión siguiente enlaza la anterior y el delta pertinente. Cada snapshot conserva la identidad por hash de los siete módulos productores. La reutilización exige el mismo productor; cambiarlo requiere reevaluación explícita en una revisión nueva y conserva la conclusión anterior como historia. La normalización de referencias tipadas sirve para decidir novedad, sin modificar bytes CAS ni los digests usados para reutilizar recibos. La pérdida de una entrega al cliente puede distinguirse de la pérdida del commit. Un fallo antes de terminar deja estado iniciado y última revisión íntegra; no un resultado favorable fabricado.

La interfaz entre autores A/B se acordó antes de escribir módulos dependientes. A posee almacenamiento, controlador, operaciones y worker; B posee validación semántica, composición de respuesta y pruebas de conformidad de producto. La supervisión autoral integra estos módulos y verifica testigos; las revisiones XG/XT/XU posteriores deben ser no autoras del objeto juzgado.
