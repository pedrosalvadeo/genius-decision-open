# Genius Kernel — referencia FP1

Implementación local de `GENIUS-SPEC-1.0.0`, perfil `FP1_FINITE_EXACT`, snapshot S2. Código de referencia validado para el alcance FP1 `GENIUS-KERNEL-1.0.1`; el gate vigente está en el informe de aceptación raíz. Usa Python 3.11 o posterior y biblioteca estándar. La ejecución directa no necesita instalación, GitHub ni conexión de red.

Desde esta carpeta:

```bash
python3 -m genius_kernel --version
python3 -m genius_kernel evaluate ../GENIUS_PROGRAM/conformance/WATER_HABITAT.input.json --out /tmp/genius-water-run
python3 -m genius_kernel verify /tmp/genius-water-run/input.json /tmp/genius-water-run/result.json
```

El directorio de salida debe ser nuevo o vacío. Se conservan exactamente los bytes recibidos en `input.json`; `result.json` contiene su SHA-256, valores, dominios, diagnósticos, comprobaciones, testigos, frontera y certificado de integración cuando procede. La pareja de archivos es la unidad portable de una evaluación. Una ejecución parcial legítima no equivale a error de programa.

El ejemplo contiene tres políticas. Las PVS esperadas son 3/4, 3/4 y 1; el presupuesto excluye la política que instala ambos servicios. La frontera factible es `{pi_a,pi_h}` y la regla `none` no selecciona. El ejemplo es sintético, no una recomendación real.

## API de Python

```python
from pathlib import Path
from genius_kernel import evaluate, verify_result, verify_decisive_certificate

raw = Path("input.json").read_bytes()
result = evaluate(raw)
report = verify_result(raw, result)
assert report["valid"] is True

# Un certificado suelto debe conservar su envoltura de identidad.
policy = next(p for p in result["policies"] if p["policy"] == "pi_ah")
cert = next(e["verdict"]["value"] for e in policy["evidence"]
            if e["verdict"]["state"] == "DEFINED")
envelope = {"input_digest": result["input_digest"], "certificate": cert}
certificate_report = verify_decisive_certificate(raw, envelope)
```

`evaluate` recibe bytes UTF-8 originales. El parser rechaza claves repetidas, campos extra, tipos erróneos, referencias imposibles y racionales no canónicos. Las funciones parciales se representan por las claves efectivamente presentes de tablas cerradas. Un dato ausente no se completa con cero.

Los verificadores devuelven `{valid, status, errors}`. `valid=True` / `VALID` significa aceptación de las afirmaciones comprobadas; `False` / `INVALID` señala un rechazo con motivos; `None` / `INCOMPLETE` indica que no se obtuvo un dictamen por límite o por un artefacto que no afirma cálculo completo. El verificador de resultado recomputa los constructores desde Input; no constituye un segundo algoritmo matemático independiente. Los oráculos de prueba y la auditoría se desarrollan por funciones separadas. El verificador decisivo comprueba la lectura completa y admite también un conjunto A mayor que Sem si satisface todas las guardas.

## Límites operativos

```bash
python3 -m genius_kernel evaluate ../GENIUS_PROGRAM/conformance/WATER_HABITAT.input.json --out /tmp/genius-limited-run --limit max_nodes=2
```

La API equivalente es `evaluate(raw, limits={"max_nodes": 2})`. Las opciones son enteros no negativos:

| Nombre | Presupuesto |
|---|---|
| max_nodes | Ocurrencias causales expandidas, no estados distintos |
| max_operations | Puntos de control de operaciones; no instrucciones del procesador |
| max_seconds | Segundos de reloj monotónico, comprobados cooperativamente |
| max_input_bytes | Bytes del Input recibido |
| max_integer_digits | Dígitos de cada componente numeral recibido, sin signo/separador; no limita enteros derivados |

La ausencia de una opción no impone ese límite artificial. El presupuesto ambiental de recursión de Python se captura antes de evaluar y se declara en `execution.limits` como `python_recursion_depth`. Agotamiento produce `LIMITED`, nunca una prueba de infactibilidad ni un cambio de horizonte. La comprobación temporal es cooperativa; una operación indivisible del intérprete puede exceder el intervalo hasta el siguiente control. Fallos internos se registran como `ERROR`.

La aritmética de datos es racional exacta mediante enteros arbitrarios. No se utiliza redondeo en probabilidad, recursos, valores o comparación. La finitud garantiza la terminación del procedimiento ideal descrito; no promete coste práctico uniforme.

## Interfaz y códigos de salida

- `evaluate INPUT --out DIRECTORIO [--limit NOMBRE=N]`: genera la pareja portable.
- `verify INPUT RESULT [--limit NOMBRE=N]`: verifica el Result completo recibido.
- `verify-certificate INPUT ENVELOPE [--limit NOMBRE=N]`: verifica un certificado decisivo ligado al digest.
- `--version`: identidad del código.

Códigos: 0 para operación completada/aceptación, 2 para presentación o artefacto rechazado/error de comando, 3 para límite/dictamen incompleto, 4 para error interno de evaluación. Una evaluación `COMPLETE` y `VALID` puede devolver objetos `OUTSIDE_DOMAIN`, frontera `RELATIVE` o ninguna selección de manera correcta.

Los contratos completos se encuentran en `../GENIUS_PROGRAM/specification/`. No ampliar el formato añadiendo campos de teoría general; cambios de significado requieren enmienda y revisión explícitas.

## Pruebas

Desde la raíz del handoff:

```bash
python3 tools/run_tests.py --output GENIUS_PROGRAM/validation/TEST_EXECUTION_F2.json
```

Desde esta carpeta se puede ejecutar directamente `python3 -m unittest discover -s tests -v`. El informe de la raíz distingue casos FP1 ejecutados, sondeos de teoría general fuera del wire, controles de certificados y límites. El catálogo recibido de F1 conserva su identidad histórica de diseño; la ejecución se registra en documentos F2 separados.

## Parche F3

La versión 1.0.0 recibida permanece en baseline/GENIUS_PHASE_2_HANDOFF. F3 detectó el rechazo de un Check CALIBRATION PASS local verdadero adicional a la prueba completa. La reparación 1.0.1 conserva el contrato y se documenta con bytes antes/después y controles de alcance en validation/FINDINGS_F3.md y validation/KERNEL_PATCH_F3.md. El estado de aceptación de la reparación depende del informe raíz; una versión por sí sola no acredita corrección.
