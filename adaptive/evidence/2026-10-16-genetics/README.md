# Verificación de genes y evolución — 16 de octubre de 2026

- 119 pruebas de integración correctas, incluidas 17 pruebas genéticas y las rutas de alojamiento, red, acceso, recuperación y lanzamiento.
- 108 pruebas del módulo adaptativo correctas.
- Experimento local sintético: candidata confirmada y heredada; candidata que empeora rechazada.
- En cuatro resultados de confirmación, error absoluto acumulado 80 → 0. En el entorno que cambia, la candidata da 80 frente a 0 de la característica anterior y no se adopta.
- La comparación de ambos casos ejecuta y verifica el kernel nativo.
- Herencia firmada, linaje, independencia de memoria, ausencia de puntuaciones heredadas, contexto exacto, recuperación tras interrupción y conservación de concesiones cubiertos.

Reproducción y límites: [GENETICS.md](../../federation/GENETICS.md).
El fixture es explícito y no ciego: no demuestra generalización, impacto real ni PVS.
La identidad criptográfica de cada ejecución cambia; se reproducen comportamientos y métricas, no los bytes de las claves.
Publicación y resultado de CI/despliegue se registran en el PR de esta entrega.
