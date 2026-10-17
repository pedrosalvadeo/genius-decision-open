# Observatorio humano y novedades — 17 de octubre de 2026

Base: `73f2b3261116be9454680b62dfccd02dada289f4`.

La portada enlaza el observatorio y explica organismos, semillas, red y resolutor.
`/organisms` presenta estados traducidos, motivos de pausa, consulta manual y cada
minuto mientras la pestaña está visible, filtros, predicciones, resultados, genes,
linaje y memoria. No atribuye vida biológica, independencia de anfitriones ni PVS.

El historial público conserva hasta 24 pares de predicción/medición **ya evaluados**,
con sus hashes. Empieza a acumularse con esta versión; no reconstruye un pasado
inexistente. Un informe anterior puede mostrar su último par registrado. El gráfico
usa las fechas reales en el eje horizontal y ofrece una tabla accesible.
El progreso 4 + 4 procede del experimento actual; no se infiere del total histórico.
Ausencias se muestran como pendientes y los totales incompletos indican cobertura.

## Comprobación

- 56 pruebas aprobadas de `test_living_habitats`, `test_public_network`,
  `test_public_launch` y `adaptive.tests.test_organism`.
- La cobertura ampliada comprueba historia acotada, persistencia al reiniciar,
  ausencia de ceros ficticios, conflictos de fuente, correspondencia con el
  pronóstico previo y progreso que vuelve a cero al iniciar otro experimento.
- `beta/tests/browser/observatory.cjs` ejecuta el JavaScript sobre un DOM con
  linkedom 0.18.12: pausa, datos faltantes, filtros, resultados, totales parciales,
  progreso, escape de texto, actualización, datos anteriores, error de red,
  informe antiguo, lista vacía, pestaña oculta y respuesta inválida.
- `node --check` y `git diff --check` aprobados.
- No se hizo inspección visual en navegador: control-browser no está disponible
  en este entorno administrado. Las pruebas DOM no verifican renderizado visual.

Comandos:

```sh
PYTHONPATH=adaptive:beta:beta/tests:product_local:consumer_views:twin:kernel python -m unittest test_living_habitats test_public_network test_public_launch adaptive.tests.test_organism -q
npm install --prefix beta/tests/browser --ignore-scripts --no-audit --no-fund
npm run --prefix beta/tests/browser test:observatory
```

## Estado real observado antes de publicar

La consulta pública de producción mostró SAME y SAMM en
`PAUSED_OR_REVIEW_REQUIRED`, motivo `ENROLLMENT_REVIEW_REQUIRED`, sin identidad,
observación ni predicción publicadas. El nuevo panel hace ese bloqueo comprensible;
esta entrega no reactiva ni vuelve a registrar organismos. No se modifica su
consentimiento, su cuota de registro ni su algoritmo de selección.

La publicación y el commit desplegado deben verificarse en Railway después de
integrar el cambio. El estado de GitHub/PR y el despliegue son evidencia separada.
