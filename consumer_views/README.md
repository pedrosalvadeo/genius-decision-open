# Consumidores locales Genius R3 — 0.1.0

Una misma respuesta RC01 recibida se presenta en español (`human.html`), para aplicación (`app.json`) y para agente (`agent.json`). Las tres preservan el objeto completo, valores exactos, cuatro capas, calidad separada, obligaciones, dependencias y límites. Es una presentación local de resultados recibidos; no ejecuta el motor ni autoriza acciones.

Requiere Python 3.12, POSIX y el árbol recibido `../product_local`, conforme al entorno de la dependencia R2 recibida y las pruebas ejecutadas. No requiere paquetes nuevos, red, servicios ni JavaScript.

```bash
PYTHONPATH=code/consumer_views:code/product_local python -B -m genius_views render --case-dir /ruta/caso --output-dir /ruta/salida-nueva
```

`--revision N` selecciona la revisión **del Store** (no la revisión lógica del request). HEAD se usa si no se especifica. El destino debe ser nuevo, con padre existente, fuera del expediente. No se sobrescriben exportaciones. La operación no recupera ni cambia el expediente fuente. Un RC01 no publicado produce `response:null`, nunca una respuesta inventada; los recibos previos permanecen accesibles mediante las referencias y `--revision`.

`source.json` conserva todos los sobres históricos, huérfanos identificados, referencias y snapshot seleccionado; `witnesses/<sha256>.txt` contiene los bytes originales en base64 con digest y tamaño. Estos son datos para descarga local, sin enlaces tomados de texto no confiable. `manifest.json` identifica todos los archivos de salida salvo sí mismo. Descodificar un testigo y verificar su SHA-256 recupera el original. Los temporales del escritor se enumeran, sin interpretarlos ni promocionarlos.

El HTML incluye una tabla de hojas JSON Pointer → literal JSON que permite verificar la equivalencia completa de tipos y valores; también muestra objetos y listas vacíos. Las secuencias Unicode se escapan para hacer visibles los controles y caracteres bidireccionales. La vista visible explica transporte/ejecución/evidencia/decisión por separado, sin inventar selección por frontera ni inviabilidad por presupuesto.

## Verificación y alcance

Se reutilizan `Store.load_chain`, `Store.get_bytes` y las interfaces públicas de `genius_local.policy`. Se valida el inventario, cada hash, manifest lógico, request y vinculación de artefactos. Se comprueba que la respuesta seleccionada persistida coincida con `policy.build_response` aplicada a los **mismos recibos**, sin recalcular FDQ ni generar evidencia nueva. En todas las revisiones históricas y huérfanas se admiten formato/fase de snapshot, versiones de request/RC01/contratos e identidad/composición de manifests estructurados; no se regeneran respuestas históricas. La lectura exige las versiones exactas recibidas; una nueva versión desconocida se rechaza aunque no corresponda a la revisión seleccionada. Una identidad de bytes no autentica al productor ni prueba verdad física. El administrador local sigue fuera del modelo de amenaza recibido.

Los límites adicionales del consumidor son: un expediente, 128 revisiones, 2048 objetos, 2048 temporales, 64 MiB agregados de archivos, 32 MiB RC01 y 120 MiB exportados. Se conserva el máximo R2 de 8 MiB por objeto/revisión, y 1024 bytes por archivo raíz de control. Tiempo: 10 s cooperativos para la operación completa; CLI POSIX con límite de 60 s. Exceso, corrupción o formato desconocido rechaza la presentación con código 2 sin publicar una exportación parcial. Los límites son operacionales, no pruebas de inviabilidad matemática. Un SIGKILL/corte externo puede dejar un directorio temporal no publicado; nunca se usa como resultado.

La detección de cambios concurrentes compara HEAD e inventario antes/después de leer; no promete protección frente a un administrador malicioso ni snapshot transaccional frente a mutación externa concurrente. No se crean locks de escritura. El API Python ofrece el límite cooperativo; el CLI añade el límite duro.

## Ejemplos y pruebas

Los ejemplos son estipulaciones sintéticas. El generador usa el constructor de fixtures recibido R2 y después ejecuta operaciones R2 reales, incluyendo FDQ contra dependencias recibidas. No acredita comprensión, utilidad, adopción ni validación física.

```bash
python -B code/consumer_views/examples/generate_cases.py --output /ruta/ejemplos-nuevos --r0 /ruta/R0 --r1 /ruta/R1
GENIUS_R0_BASELINE=/ruta/R0 GENIUS_R1_BASELINE=/ruta/R1 PYTHONPATH=code/consumer_views:code/product_local python -B -m unittest discover -s code/consumer_views/tests -v
```

El cliente independiente invoca la CLI y verifica por sí mismo hashes, JSON, HTML, valores exactos y no mutación; no importa ninguna transformación `genius_views`. Las pruebas autorales añaden casos FDQ ejecutados, huérfanos, testigos recuperables y límites. `docs/SEMANTIC_CONTRACT.md` define equivalencia y pérdida de información; `docs/COMPREHENSION_PROTOCOL.md` sólo prepara decisiones para una evaluación humana futura. Ninguna prueba automática se presenta como evidencia humana.
