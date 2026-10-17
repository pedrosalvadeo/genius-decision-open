# Revisión de fuentes y alcance

Revisadas el 16/10/2026 Argentina; última relectura 17/10/2026 00:21:01 UTC.
Base de todos los archivos:
[07e6ac9](https://github.com/wuisabel-gif/MemWhale/tree/07e6ac952dbbb7b527fe78578271cd57937f0890).

- [#423](https://github.com/wuisabel-gif/MemWhale/issues/423): abierto, sin
  asignados ni comentarios; última modificación 16/10/2026 20:03:42 UTC.
  Capturas inicial/final conservadas. Solicita exactamente cinco guías, texto
  uniforme, menos de diez líneas y enlace a 0.20.0.
- [#317](https://github.com/wuisabel-gif/MemWhale/issues/317), CONTRIBUTING y
  AGENTS leídos. Comentar primero para evitar duplicación. No hubo comentario
  externo; no se declara asignación. CONTRIBUTING no exige CLA/DCO en esta base.
  MIT: copyright 2026 Isabella Wu and MemoryWhale contributors; no NOTICE rastreado.
- PR abiertos inspeccionados: #427 (tests de stats MCP, relacionado pero no
  solapado), #420 y #419 (dependencias), #292 (harness Codewhale). Sin PR de estas
  cinco secciones al revisar. Esto no garantiza exclusividad futura.
- `integrations/TEMPLATE.md`: ocho secciones obligatorias; se preserva su orden.
  `docs/architecture.md`: cambio sólo en Interfaces, sin comportamiento nuevo.
- `crates/mw-cli/src/lib.rs`, `FixCandidate`, `fix_candidates`, `format_hint`,
  `ran_by`: candidato = siguiente comando diferente que pasa, en el mismo cwd
  y ventana de cinco registros; cuenta éxito cuando el comando fallido pasa
  después, dentro de diez registros de la falla. Se ordena por confirmaciones,
  apariciones y recencia. `worked >= 2` produce `confirmed fix:`, cero o uno
  produce `possible fix:`. La identidad proviene de la ejecución más reciente
  del candidato. Las guías sintetizan sin repetir ventanas; enlazan detalles.
- `crates/mw-cli/src/bin/mw-remember.rs`: primero graba, después obtiene feedback.
  `feedback_note` retorna None con `MEMORYWHALE_HOOK_FEEDBACK=0`; por eso silenciar
  no desactiva captura. `run_from_hook` emite feedback para Claude/Codex/Gemini;
  Cursor lo hace en su ruta propia; Rho no. Rho puede aportar registros al almacén,
  pero no debe prometerse que recibe estas notas.
- `docs/releases/0.20.0.md`: confirma umbral, historial cruzado entre agentes y
  terminal, con ejemplos. La correlación de comandos no acredita causalidad;
  conservamos la advertencia de comprobar aplicabilidad. Esa release declara
  Codex, Gemini y Cursor aún no verificados en vivo. No actualizamos ese estado.
- Codex conserva explícitamente los límites de exit desconocido y ausencia de
  nota de éxito después de fallo. No inferimos su funcionamiento real actual.

## Verificación y limitaciones

Nueve pruebas propias leen Markdown: igualdad de cuatro secciones, longitud,
excepción Rho, enlaces locales nuevos, frases obsoletas, ocho títulos, hashes de
bloques de código, hashes de Status, y límite Codex. Antes fallan cinco métodos
con 18 subfallos; después pasan los nueve. Repetidos tras git apply en copia limpia.
`rg -n 'fix that worked' integrations` no encuentra coincidencias (salida 1).
`git diff --check` pasa en ambas copias. No se ejecutaron comandos de las guías.

El arnés revisado elimina el entorno heredado y niega sockets IPv4/IPv6 con
seccomp; `isolation.log` confirma ambas familias. Python 3.12.3, biblioteca
estándar. Esto no es una afirmación de sandbox universal: los tests son lectura
local y el arnés permite Unix sockets y acceso al sistema de archivos.

`mw` y Cargo no están instalados. No se instaló MemoryWhale ni se abrió/migró
una base de datos personal sólo para cumplir la sugerencia de auto-memoria de
AGENTS; se conservan evidencia y memoria en Genius. El script upstream
`scripts/check-doc-references.sh` fue leído pero necesita Cargo y ejecuta mw-mcp:
no se corrió. Tampoco suites completas npm/Rust, build o clientes en vivo.
No se modificó frontend, Rust, workspace, configuración ni la raíz README.

Revisión propia, no independiente. Los recibos validan coherencia del estado,
no certifican verdad ni aceptación del mantenedor. SOLUTION_PREPARED solamente.
