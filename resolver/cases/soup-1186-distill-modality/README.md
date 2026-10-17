# Soup #1186: no ignorar la modalidad en destilación

16/10/2026 (Argentina). **SOLUTION_PREPARED**, sólo el ítem 1 del issue.
No es una resolución completa de #1186 ni una aplicación en Soup.

- [Necesidad y estado actual](https://github.com/MakazhanAlpamys/Soup/issues/1186)
- [Base fijada](https://github.com/MakazhanAlpamys/Soup/tree/3da204fadbd278c01ad5a4b23906b443d15e9dd1)
- Criterios previos en `claim.json`; resultados y límites en `validation.json`.

## Utilidad y alcance

Quien solicita destilar imagen o audio podía cargar una configuración que el
entrenador ejecutaría como texto. El parche rechaza esas combinaciones antes de
cargar modelos, explica el motivo y nombra la alternativa textual. No añade
soporte multimodal ni transforma datos. Los modos token y sequence quedan cubiertos.

La reserva interna se publicó antes de escribir las pruebas y el cambio; su
commit está en `sources.json`. La inspección del hilo fue indispensable: el
defecto del título (backend unsloth) ya fue resuelto por @chiliec en #1193; el
ítem 3 también fue resuelto por terceros. El ítem 1 estaba libre según el último
comentario del mantenedor. **El ítem 2, SFT/unsloth con visión o audio, sigue
pendiente y no está incluido.** No se hizo una nueva búsqueda masiva.

`solution.patch` modifica cuatro archivos: el validador Pydantic existente,
pruebas, la documentación de entrenamiento y un fragmento `fixed`. Se mantiene
la validación anterior de backend y profesor. La revisión de 205 configuraciones
YAML y literales de recetas no encontró ninguna con task=distill; por tanto no
hay una combinación distribuida que requiera una transición previa con avisos.
Esto no afirma nada sobre configuraciones privadas de usuarios. El inventario y
el programa de inspección están conservados.

## Comprobaciones

- Pruebas iniciales antes del cambio: **16 fallos, 9 aprobadas**.
- Primera corrección: 25 aprobadas; luego se añadieron cuatro invocaciones del
  CLI real `doctor --config`, sin sustituir la carga de configuración.
- Regresión final: **129 aprobadas** (29 nuevas y 100 existentes).
- Copia limpia: parche aplicable y las 29 nuevas aprobadas.
- Mutación: quitar sólo las ocho líneas del rechazo produce **20 fallos y 9
  aprobadas**. Restaurarlas vuelve a dar 29 aprobadas.
- Ruff completo sobre `src/soup_cli/ scripts/ tests/ benchmarks/`: aprobado.

Los logs son evidencia del operador, no una revisión independiente. Se usó Linux
y Python 3.12.14, con las versiones de `requirements-validation.txt`. El entorno
de pruebas no contiene torch, transformers, peft, trl ni unsloth. No se descargó
ningún modelo ni se entrenó. El arnés revisado
[`run_no_network.py`](../linux-vitals-149-locale/run_no_network.py) reemplaza el
entorno por seis entradas no secretas y bloquea sockets IPv4/IPv6, también en
procesos hijos; `isolation.txt` registra la comprobación. No hubo credenciales,
cuentas ni acciones de producción. No se ejecutó la suite completa, cobertura
global ni la matriz upstream de sistemas y versiones de Python.

## Reproducción

En una copia de la base fijada, con un entorno Python 3.12 separado y las
dependencias listadas instaladas como wheels (sin instalar el extra `[train]`):

```sh
git apply --check /ruta/al/paquete/solution.patch
git apply /ruta/al/paquete/solution.patch
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest \
  tests/test_config.py tests/test_v0520.py::TestDistillUtils \
  tests/test_v0520.py::TestDistillSchema \
  tests/test_issue1357_unsloth_refused_without_setup.py \
  tests/test_distill_modality.py -o addopts= -p no:cacheprovider -v --tb=short
ruff check src/soup_cli/ scripts/ tests/ benchmarks/
python /ruta/al/paquete/audit_shipped_configs.py .
git diff --check
```

En esta entrega se ejecutó Python a través del arnés sin red y se añadió `src`
a `sys.path` dentro de Python, ya que el arnés limpia PYTHONPATH. `addopts=`
desactiva la configuración global de cobertura para este subconjunto; no equivale
a superar la cobertura completa de Soup. Para reproducir la mutación, retirar
sólo el bloque de ocho líneas marcado `#1186 item 1` del schema en otra copia y
repetir `tests/test_distill_modality.py`: debe fallar en 20 casos.

## Autoridad y continuidad

Se incluyen `LICENSE` Apache-2.0 y `NOTICE` de Soup. El diff identifica las
modificaciones preparadas para Genius con asistencia de Codex. El contrato de
contribución actual no exige CLA ni DCO, pero sí un comentario con plan para
reclamar el trabajo. **No se publicó ese comentario ni un PR externo**. Preparar
una copia no reserva el issue en Soup ni compromete a Pedro como contribuyente.
`UPSTREAM_DRAFT.md` contiene el plan y PR propuestos, ambos sin enviar.

Próximo paso externo: autorización para el comentario de reserva y el PR;
coordinar con el mantenedor, releer fuente/claims y completar sus controles antes
de presentar. El fragmento usa el número del issue provisionalmente; el proyecto
prefiere el número del PR cuando exista. Los PR abiertos que tocan el schema
pueden requerir una nueva base y repetición de las pruebas.

El motor Genius no se ejecutó: no hay representación justificada para calcular
esta corrección de validación. No se inventaron puntuaciones, CAG, PVS ni
bienestar. La integración del paquete en Genius no demuestra adopción externa.
No regenerar ni anunciar este ítem como novedad en un ciclo posterior.
