# Evaluación portable de ejemplo

La carpeta [water_habitat](water_habitat/) contiene los bytes originales de la instancia sintética F1, el Result completo producido por GENIUS-KERNEL-1.0.0 y su dictamen de verificación. La evaluación se ejecutó con Python 3.12.14, sin presupuestos opcionales; el límite ambiental de recursión quedó declarado antes del cálculo.

Desde `kernel/`, comprobar la pareja recibida:

```bash
python3 -m genius_kernel verify ../examples/water_habitat/input.json ../examples/water_habitat/result.json
```

Para repetir la evaluación, usar un directorio nuevo o vacío:

```bash
python3 -m genius_kernel evaluate ../examples/water_habitat/input.json --out /tmp/genius-water-reproduction
```

Resultado observado: COMPLETE/VALID, 15 ocurrencias causales; PVS de pi_a, pi_h, pi_ah iguales a 3/4, 3/4, 1. Las tres políticas son comparables en B; la restricción de presupuesto excluye pi_ah, y la frontera exhaustiva es {pi_a,pi_h}. La regla none no selecciona. El certificado de integración fuerte está presente. Esto verifica el ejemplo y no acredita adecuación de modelos reales.

La pareja anterior se conserva como evidencia histórica de Kernel1.0.0. La nueva evaluación y verificación con Kernel1.0.1 se guarda en water_habitat_f3; conserva los mismos valores matemáticos.
