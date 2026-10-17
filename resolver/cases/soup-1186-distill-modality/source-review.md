# Revisión de fuente y límites

Fuente fijada: `3da204fadbd278c01ad5a4b23906b443d15e9dd1`, leída el 16/10/2026
en Argentina. El último contraste remoto fue 17/10/2026 00:00:26 UTC.

| Afirmación / decisión | Evidencia |
| --- | --- |
| El título no identifica el trabajo pendiente | Hilo completo de #1186: #1193 ya rechazó backend unsloth; #1746/#1782 resolvieron el aviso. El comentario final del mantenedor libera los ítems 1 y 2 |
| No duplicar el ítem 2 | El mantenedor pide PR separados para destilación y SFT/unsloth; sólo se prepara el primero |
| La destilación actual procesa texto | `trainer/distill.py::DistillTrainerWrapper.setup` usa AutoTokenizer, AutoModelForCausalLM, formateo SFT y, en sequence, generación textual. No lee `modality` |
| El lugar de rechazo compartido | `config/schema.py::SoupConfig._validate_distill_compat` es llamado por las cargas de archivo y string; el helper existente ya valida backend y teacher |
| Doctor no debe dar conformidad a esa configuración | `commands/doctor.py::_check_config_support` llama al loader y convierte su SystemExit(1) en typer.Exit(2); los tests invocan esa ruta y el CLI completo |
| Rechazo inmediato, no aviso transitorio | Inspección estática de 205 configs en recipes, templates, src/soup_cli/templates y examples; ninguna task=distill. No cubre archivos privados |
| No ampliar soportes accidentalmente | Controles preservan texto explícito/por defecto, ambos modos, SFT vision/audio, y los rechazos backend/teacher existentes |
| La regresión detecta la ausencia del cambio | 16 fallos antes; tras añadir también el CLI, retirar únicamente el bloque nuevo causa 20 fallos. Restaurarlo produce 29 aprobadas |
| Licencia y coordinación | AGENTS.md, CONTRIBUTING.md completos, LICENSE y NOTICE leídos. Claim con plan requerido; no CLA/DCO en la versión inspeccionada. No se envió nada |

Enlaces fijados:

- [Schema](https://github.com/MakazhanAlpamys/Soup/blob/3da204fadbd278c01ad5a4b23906b443d15e9dd1/src/soup_cli/config/schema.py)
- [Entrenador](https://github.com/MakazhanAlpamys/Soup/blob/3da204fadbd278c01ad5a4b23906b443d15e9dd1/src/soup_cli/trainer/distill.py)
- [Loader](https://github.com/MakazhanAlpamys/Soup/blob/3da204fadbd278c01ad5a4b23906b443d15e9dd1/src/soup_cli/config/loader.py)
- [Doctor](https://github.com/MakazhanAlpamys/Soup/blob/3da204fadbd278c01ad5a4b23906b443d15e9dd1/src/soup_cli/commands/doctor.py)
- [Contribución](https://github.com/MakazhanAlpamys/Soup/blob/3da204fadbd278c01ad5a4b23906b443d15e9dd1/CONTRIBUTING.md)

Revisión propia, no auditoría independiente. No se ejecutó setup, entrenamiento,
descargas ni inferencia. La fuente sostiene el diagnóstico; las pruebas ejecutan
la aceptación/rechazo de configuración, no la calidad de un modelo. La lista de
PR abiertos se conserva en sources.json; #1948 inspeccionado es una mejora de
tests de configuración, no una implementación de este rechazo. Antes de enviar,
revisar otra vez los PR que cambien schema y los comentarios de asignación.
