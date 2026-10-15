# Genius: propuestas de evolución del código

Este componente convierte memoria **ya pública y sintética** en una propuesta de
código Python, la evalúa y conserva una rama de GitHub con un PR borrador cuando
los permisos del repositorio lo permiten. Es un primer generador ejecutable de
estrategias; no es un editor general de su propio programa ni conecta bases privadas.

## Qué hace el ciclo

1. Lee la solicitud activa y verifica hashes de datos, recibos y código.
2. Recalcula el error de la política contextual vigente sobre la memoria declarada.
3. Ajusta programas afines exactos para retardos de uno, dos o tres pasos. Los
   coeficientes se calculan desde los datos; no están escritos para el ejemplo.
4. Elige un único programa usando sólo entrenamiento y congela sus bytes/hash.
5. Ejecuta el Python generado y contrasta sus resultados con aritmética entera
   independiente, en datos de evaluación separados. Cada caso tiene predicciones
   realizadas sólo desde su prefijo anterior; los coeficientes ya están congelados.
6. Conserva todos los resultados, crea una rama inmutable y propone su revisión.
   Los rechazos también se publican. No aprueba ni fusiona su propio PR.

El generador usa ajuste por mínimos cuadrados racionales; el objetivo ponderado
elige entre esos programas ajustados. No se afirma que optimice exactamente toda
función de pérdida posible. Los límites de coeficientes y del lenguaje son explícitos.
No necesita un proveedor LLM ni secretos nuevos. La selección entre familias nuevas,
los cambios de arquitectura y la modificación general de código quedan pendientes.

## Objetivo y evaluación

Cada solicitud declara unidad, base, calentamiento, costo de subestimar y de
sobreestimar, y límites máximos. En este primer ensayo los costos son 1 y 1 en
unidades de prueba, sin interpretación monetaria ni de bienestar.

Para ser `ELIGIBLE_FOR_REVIEW`, un candidato debe mejorar el costo total tanto en
entrenamiento como en evaluación. Además, **cada caso de evaluación** debe tener
costo, máxima subestimación y máxima sobreestimación no peores que la política
actual y cumplir los límites declarados. De lo contrario queda
`REJECTED_BY_EVALUATION`. La elegibilidad abre revisión; no prueba beneficio real
ni autoriza activación de producción. No hay operación de promoción en v1.

Los datos de evaluación son fixtures públicos predeclarados, no un estudio ciego
ni evidencia empírica. Cambiar objetivos o casos después de ver resultados exige
otra solicitud/versionado; los resultados anteriores permanecen conservados.

## Ejecución y registro

`evolution/active-request.json` identifica una solicitud en `evolution/requests`.
La primera parte de los recibos de integración pública del PR 37. El origen se
verifica por hash, encadenamiento, predicciones y recálculo del informe.

```bash
PYTHONPATH=evolution:adaptive python3.12 -B -m unittest discover -s evolution/tests -v
PYTHONPATH=evolution:adaptive python3.12 -B -m genius_evolution prepare \
  --base COMMIT_DE_40_HEXADECIMALES --bundle /tmp/propuesta.json
PYTHONPATH=evolution:adaptive python3.12 -B -m genius_evolution verify --bundle /tmp/propuesta.json
```

`Genius code evolution` se ejecuta al incorporar a main cambios del generador,
solicitud activa o datos declarados; también admite activación manual. En PR sólo
evalúa. No hay sondeo permanente, cron ni lectura automática de las cuentas.
Para iniciar otro ciclo se incorpora un paquete público autorizado y se cambia
la solicitud activa. La conexión automática desde memoria privada requiere otro
contrato de exportación/consentimiento; no está implementada.

En GitHub, el evaluador corre en un contenedor sin red, sin credenciales, sin
capacidades, con repositorio de sólo lectura, 384 MiB, un CPU y límite de procesos.
Cada ejecución de código generado agrega 5 s de tiempo real, 3 s de CPU y 128 MiB.
Sólo se aceptan los bytes exactos que produce el generador; no hay comandos, imports
ni Python arbitrario provenientes de datos. Localmente el hijo conserva esos
límites y entorno limpio; la frontera de red del contenedor se verifica en CI.

El publicador es otro job, con token sólo de GitHub y permisos de contenido/PR.
Recalcula el paquete con aritmética de referencia, sin ejecutar Python descargado.
Sólo puede producir `evolution/candidates/ID.py`, informe/README en
`evolution/proposals/ID/` y el manifiesto de publicación actualizado. Nunca modifica
main, workflows, permisos, producción ni credenciales. La identidad incluye
generador, publicador, tests, workflow y política de referencia.

La rama `genius/evolution/ID` es estable: reintentos recuperan el resultado, no lo
reescriben; un PR cerrado no se reabre. Un main que cambió antes de una primera
publicación detiene la operación. Si GitHub no permite crear el PR, queda la rama,
el enlace de revisión y el estado explícito `BRANCH_PUBLISHED_PR_BLOCKED`; no se
cambian permisos ni se prueba otra identidad. Los workflows de un PR creado con
`GITHUB_TOKEN` pueden requerir aprobación de GitHub antes de ejecutarse.

Referencias de la plataforma:
- https://docs.github.com/en/actions/concepts/security/github_token
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
- https://docs.github.com/en/rest/git/refs

## Primer resultado y estado

La memoria alternante produce automáticamente `110 - valor_anterior`. Mejora
el ajuste a la secuencia de entrenamiento, pero la suite incluye estabilidad,
cambio de régimen, deriva y shocks. El resultado se conserva aunque rechace la
generalización del candidato. El estado verificado del workflow y sus enlaces
se registran en `adaptive/HANDOFF.md` y `evolution/evidence/`.

El runtime público sigue fijado al PR 36. Ningún resultado sintético de este
componente mide bienestar, PVS ni justifica sustituir la política desplegada.
