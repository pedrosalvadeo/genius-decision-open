# Ejemplo F4 — proceso Node → proceso Python

`water_habitat_f4` contiene los bytes exportados por el consumidor independiente, metadata y capacidades negociadas. `water_habitat_f4_verification` conserva su verificación mediante RPC. `kernel_verification.json` acredita comprobación adicional por CLI Kernel heredada. La frontera es exhaustiva con pi_a/pi_h; selector none deja selection fuera de dominio. Los otros ejemplos conservan origen F2/F3.

Ejecutar desde la raíz con un destino nuevo:

```bash
node protocols/consumer/cli.mjs eval --input GENIUS_PROGRAM/conformance/WATER_HABITAT.input.json --out NUEVO_EJEMPLO
node protocols/consumer/cli.mjs verify --input NUEVO_EJEMPLO/input.json --candidate NUEVO_EJEMPLO/result.json --out NUEVA_VERIFICACION
```

No se sobrescribe una exportación existente. La mera exportación no equivale a validación; el report de verificación informa VALID/INVALID/INCOMPLETE.
