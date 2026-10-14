> Actualización del 2026-10-14: la integración del servicio ya está implementada
> en `beta/docs/ADAPTIVE_MISSIONS.md`: API/MCP por cuenta, worker, checkpoints
> durables, respaldo/restauración y borrado. Las pruebas locales actuales son
> 117 del servicio y 16 del coordinador, correctas. La sección de despliegue de
> este documento describe el estado anterior del prototipo; la activación de
> producción se registra por separado al verificar Railway. El próximo trabajo
> ya no es volver a implementar esta integración.

# Continuidad de Genius adaptativo — 2026-10-14

Este cambio inicia la construcción del plan acordado. Entrega un primer ciclo
persistente de operador, conectado al gemelo y al núcleo, con observaciones
reales y recuperación entre procesos. No completa todavía el despliegue público
del coordinador ni el aprendizaje autónomo.

## Lo construido y probado

- Coordinador con LangGraph Functional API, checkpoints SQLite y diario de
  misiones independiente. Las etapas guardan medición, modelo, evaluación nativa,
  efecto, observación y memoria.
- Identidad de entradas, ejecución y dependencias congelada al iniciar. Un
  cambio impide reinterpretar checkpoints anteriores.
- Intenciones de efectos registradas antes de actuar. Un resultado incierto se
  reconcilia consultando el destino; no se repite a ciegas.
- CLI limitada y ejecutable, dependencias con hashes, imagen aislada y CI.
- Misión real sobre los **460 archivos** del commit público
  `170739625c339e6f77c5ff845ec99d0b2ad7bf80` (7.220.896 bytes de contenido).

| Alternativa | Bytes medidos | Integridad |
|---|---:|---|
| TAR | 7.587.840 | Verificada |
| gzip | 1.674.327 | Verificada |
| ZIP | 1.923.171 | Verificada |

El gemelo seleccionó gzip bajo el criterio explícito de menos bytes con iguales
contenidos y bits ejecutables. La lectura del archivo entregado confirmó los
460 archivos. Diferencia frente a TAR: 5.913.513 bytes (77,93%). No se midió una
transferencia de red ni un efecto sobre bienestar humano o sostenimiento de vida.

La prueba real terminó deliberadamente el proceso después de decidir y antes de
actuar. Un segundo proceso recuperó los mismos recibos, realizó y verificó una
única publicación local. Un tercer proceso reutilizó el resultado sin cambiar
el diario. Máximo RSS informado para los procesos hijos: **86.716 KiB**; esta
medición local no certifica la capacidad de concurrencia de producción.

La evidencia completa está en [evidence/2026-10-14](evidence/2026-10-14), con
inventario, modelos, resultados nativos, recibos e identidad del ejecutor. Se
regenera con `adaptive/probe.py` en el entorno fijado, sobre ese commit y usando
carpetas nuevas. Los tiempos, marcas de observación y RSS pueden variar.

## Verificación y defecto heredado

- 16 pruebas nuevas: recuperación real después de medición y decisión,
  interrupción antes/después del efecto, no repetición incierta, integridad,
  exclusión de escritores, cambio de código y alteración de entradas.
- 65 pruebas del gemelo: correctas.
- 46 pruebas de la cápsula: correctas.
- Instalación limpia sin red desde los 41 wheels descargados, validando todos
  sus hashes; pruebas nuevas repetidas en ese entorno: correctas.
- El Docker de pruebas y su workflow de GitHub Actions están preparados. Docker
  no estaba disponible localmente. Tras resolver el acceso, las verificaciones
  remotas de recuperación y cápsula se iniciaron en el
  [PR 24](https://github.com/pedrosalvadeo/genius-decision-open/pull/24).
  Consultar sus checks para el resultado de la versión exacta que se integre.

Antes de editar, la selección de 23 pruebas `test_adapter`, `test_choice` y
`test_examples` mostró **5 fallos y 2 errores**. Los adaptadores FDQ apuntan a
`beta/vendor/R0` y `beta/vendor/R1`, ausentes del repositorio público, y producen
`PR_DEPENDENCY`. No se reemplazaron esos verificadores ni sus hashes por versiones
inventadas. Resolverlo exige recuperar las fuentes exactas de los pins o declarar
explícitamente esa capacidad como no disponible. Este cambio usa el gemelo y
núcleo públicos presentes y no corrige silenciosamente ese defecto.

## Despliegue observado

Railway seguía en `SUCCESS`, sin cambios preparados, con el servicio público
fijado al commit `8f1e2726ce6ee3fd47338421f06ef03c2b349f7a`, el despliegue
`c3b9bcc3-b2bd-4691-bb17-b117ddd36b34` y el volumen de 500 MB en `/data`.
El coordinador nuevo no está activado allí. Este incremento no modifica el
Dockerfile ni el supervisor del servicio público.

El despliegue del coordinador requiere incorporar sus bases al respaldo y
restauración, aislar las misiones por titular, fijar cuotas persistentes y
retención, integrar el worker y comprobar recuperación en el volumen real.
El prototipo actual es de un solo operador confiable. No requiere proveedor
LLM; conectar generación de hipótesis sí requerirá resolver proveedor y costo.

## Publicación y acceso restablecido

La conexión de GitHub pudo leer el repositorio y reportó permisos `push` y
`admin` para la cuenta, pero rechazó tanto `create-tree` como `create-branch`
con HTTP 403, `Resource not accessible by integration`. La instalación sólo
incluía `genius-decision`; faltaba autorizar `genius-decision-open`. Pedro agregó
ese repositorio el 2026-10-14 y se comprobó la escritura.

El árbol del commit local `ef91a356612254057e7eb0b4e3c296c9262a991d` se publicó
sin diferencias como `28415610ca1863c28b7cd7ae9318cab081c9040c`, en la rama
`work/adaptive-missions-20261014`. El
[PR 24](https://github.com/pedrosalvadeo/genius-decision-open/pull/24) conserva
el cambio, la revisión y la CI. La publicación de código es distinta de activar
el coordinador en el servicio; la integración de producción sigue pendiente.

## Próximo encargo

> Continuá Genius adaptativo desde `adaptive/HANDOFF.md` y la evidencia de
> `adaptive/evidence/2026-10-14` y el PR 24; no reinicies la arquitectura ni
> vuelvas a solicitar el acceso ya restablecido. Integrá el coordinador
> persistente con el worker y el almacenamiento del servicio,
> incluyendo permisos por titular, cuotas, retención y respaldo/restauración.
> Prepará y probá una migración y un despliegue reversible sobre el servicio
> existente. Conservá la conciliación de efectos inciertos y los contratos del
> núcleo. Después de cerrar esa base, avanzá a hipótesis y revisión de modelos
> con observaciones. No presentes almacenar recibos como autoaprendizaje ni la
> misión de archivos como evidencia de bienestar. Entregá Git, pruebas, estado
> real del despliegue y un único próximo encargo.
