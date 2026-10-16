# Revisión de afirmaciones contra la fuente

16/10/2026, commit `0205ad85a5790351a43c3f523aff95f15da29d9c` de getsotto/sotto.
Inspección estática realizada por el agente, no ejecución Rust ni auditoría
criptográfica. El issue cita una base anterior; se usó la fuente actual fijada.

| Afirmación de la guía | Evidencia inspeccionada en ese commit |
| --- | --- |
| `--env staging` selecciona sólo el entorno de ese comando | `crates/cli/src/main.rs`: `Cli.env`, argumento global, y `effective_config`, que reemplaza `config.environment` sin guardar la configuración |
| `rm` acepta nombre opcional y `--yes` / `-y` | `main.rs`: variante `Command::Rm` y sus atributos Clap |
| Nombre ausente abre selector sólo en modo interactivo | `main.rs`: rama `Command::Rm`; `prompts.rs`: `preflight_secret_name_gate` y `select_secret_key` |
| No es la confirmación predeterminada; cancelar o rechazar no elimina | `prompts.rs`: `confirm_removal`, `with_default(false)`, cancelación/interrupción a `false`; `main.rs`: retorno anterior a `app.remove` |
| `--yes` sólo evita confirmación, no desbloqueo ni selector | `main.rs`: `ensure_unlocked` y selección se ejecutan antes de comprobar `yes` |
| Los tres streams deben ser terminales; terminal no dumb; CI inactivo | `prompts.rs`: `can_prompt` y `allowed`; `theme/mod.rs`: `ci_enabled` considera inactivos vacío, 0 y false |
| Con nombre no hay confirmación no interactiva | `main.rs`: la condición de confirmación exige `prompts::can_prompt()`; `preflight_secret_name_gate` exige nombre si no puede preguntar |
| Eliminación local, del entorno seleccionado | `commands.rs`: `App::remove` delega al vault de `config`; `vault.rs`: `delete`; `store.rs`: `delete_secret` actualiza `deleted_at` en SQLite |
| Se oculta de lecturas/listados pero conserva versiones | `vault.rs`: `get`, `list_names`, `find_id_by_name`; `store.rs`: selección de filas no eliminadas, `delete_secret` y `secret_versions` |
| No es borrado seguro ni revocación externa | La ruta sólo marca la fila; no elimina versiones ni llama a proveedores. No se afirma una garantía criptográfica |
| Push/pull necesitan sesión y usan el mismo entorno | `main.rs`: ramas `Command::Push`, `Command::Pull`, `sync_client`; rechazo sin sesión con instrucción de login |
| Push y pull llevan la eliminación a otro dispositivo | `remote/sync.rs`: `push`, `pull`, `diff`, `apply_snapshot`, y prueba `updates_and_deletes_propagate`, leída pero no ejecutada |
| Ayuda de recuperación separada | `main.rs`: `History` y `Rollback`, con sus textos `after_help`; PR #595 ya propone un recorrido de recuperación |

Enlaces a la fuente fijada:

- [main.rs](https://github.com/getsotto/sotto/blob/0205ad85a5790351a43c3f523aff95f15da29d9c/crates/cli/src/main.rs)
- [prompts.rs](https://github.com/getsotto/sotto/blob/0205ad85a5790351a43c3f523aff95f15da29d9c/crates/cli/src/prompts.rs)
- [commands.rs](https://github.com/getsotto/sotto/blob/0205ad85a5790351a43c3f523aff95f15da29d9c/crates/cli/src/commands.rs)
- [vault.rs](https://github.com/getsotto/sotto/blob/0205ad85a5790351a43c3f523aff95f15da29d9c/crates/cli/src/vault.rs)
- [store.rs](https://github.com/getsotto/sotto/blob/0205ad85a5790351a43c3f523aff95f15da29d9c/crates/cli/src/store.rs)
- [sync.rs](https://github.com/getsotto/sotto/blob/0205ad85a5790351a43c3f523aff95f15da29d9c/crates/cli/src/remote/sync.rs)
- [theme/mod.rs](https://github.com/getsotto/sotto/blob/0205ad85a5790351a43c3f523aff95f15da29d9c/crates/cli/src/theme/mod.rs)

Se comparó el sentido de los cinco textos: alcance local, mismo entorno, sesión,
selección, confirmación negativa, cancelación, límites de `--yes`, condiciones de
terminal/CI, modo no interactivo, historial y ausencia de revocación. El
verificador upstream demuestra igualdad estructural, no exactitud semántica;
la revisión de hablantes fluidos sigue siendo bienvenida antes de adoptar.
