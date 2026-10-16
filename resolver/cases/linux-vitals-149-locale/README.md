# LinuxVitals #149: sondas y certificados independientes del idioma

Estado: **SOLUTION_PREPARED**, sólo en copia. Fecha: 16 de octubre de 2026.

Necesidad pública: [linux-vitals #149](https://github.com/sameeralam3127/linux-vitals/issues/149).
Fuente fijada: [`086d99a7877f9d70bcae06dd2bcb2ade1816ecb5`](https://github.com/sameeralam3127/linux-vitals/tree/086d99a7877f9d70bcae06dd2bcb2ade1816ecb5).
El issue seguía abierto y sin asignados, sin PR abiertos en el repositorio, en
la relectura del 16/10/2026. No se contactó a sus responsables.

## Utilidad y alcance

Los operadores de equipos Linux con idiomas distintos del inglés podían recibir
una falsa alerta de accesos fallidos, y el lector de certificados podía dejar sin
interpretar la fecha de vencimiento. Es un fallo digital reproducible, sin requerir
credenciales, equipos de terceros ni una decisión operativa sobre certificados.
La prioridad es juicio de ingeniería sobre evidencia y factibilidad, no un puntaje
Genius. No se ejecutaron el kernel ni misiones: no hay aquí una representación y
criterio del motor que permita calcular un resultado válido. CAG, bienestar y PVS
siguen sin medir.

La [reserva publicada](https://github.com/pedrosalvadeo/genius-decision-open/commit/2d319b11daf0e31b21c452b485af018bf04ec0c6)
fijó los criterios antes de modificar la fuente. Se preservan en `ledger.json`
y `validation.json`.

## Entrega

`solution.patch` cambia 14 archivos de la fuente fijada:

- Fija `LC_ALL=C` en las sondas de comandos del escáner y de estado de servicios.
- Interpreta los doce meses ingleses de OpenSSL con una tabla fija y validación
  de fecha, sin cambiar el idioma del proceso.
- Conserva las fechas originales. Una fecha ausente o inválida produce
  `cert_scan_unavailable`, `status: unknown`, con la causa y el dato original.
  Una fecha final conocida y vencida sigue generando `cert_expired`, aunque no
  pueda interpretarse la fecha inicial.
- Incluye regresiones, fixtures, changelog y documentación de la nueva causa
  del hallazgo existente. No introduce un identificador de hallazgo nuevo.

Los resultados y límites están en `validation.json`, con las salidas completas
de las pruebas. La ejecución inicial de las 53 nuevas comprobaciones dio
**25 fallos y 28 aprobadas** antes de la corrección. Los mismos casos se prueban
después; no se cambian los criterios para hacerlos pasar.

## Reproducción local

Requiere Linux, Python 3.12, git, OpenSSL, libseccomp, `localedef` y las fuentes de
locales alemán/francés. Los comandos siguientes sólo operan sobre una copia nueva.
Descargar dependencias es una fase separada de ejecutar el código revisado.

En un directorio de prueba vacío, copiar `run_no_network.py`,
`requirements-validation.txt` y `solution.patch` de este paquete y ejecutar:

```sh
python3.12 -m venv vitals-env
vitals-env/bin/python -m pip install --only-binary=:all: -r requirements-validation.txt
mkdir vitals-locales
localedef -i de_DE -f UTF-8 vitals-locales/de_DE.UTF-8
localedef -i fr_FR -f UTF-8 vitals-locales/fr_FR.UTF-8
git clone https://github.com/sameeralam3127/linux-vitals.git source
cd source
git checkout --detach 086d99a7877f9d70bcae06dd2bcb2ade1816ecb5
git apply --check ../solution.patch
git apply ../solution.patch
../vitals-env/bin/python ../run_no_network.py python -m pytest \
  tests/test_locale.py tests/test_cert_facts.py tests/test_scan_task_size.py -q
../vitals-env/bin/python ../run_no_network.py python -m pytest \
  tests/test_golden_findings.py tests/test_self_healing.py \
  tests/test_service_status.py tests/test_finding_severity.py \
  tests/test_numeric_coercion.py -q
```

Para reproducir el fallo inicial, en otra copia limpia aplicar únicamente
`tests/test_locale.py` y `tests/fixtures/locale_probe_outputs.json` del parche
con las opciones `git apply --include=...`, y ejecutar `tests/test_locale.py`.
El resultado esperado es un código de salida distinto de cero; `baseline.txt`
conserva los detalles originales.

El arnés elimina las variables del entorno y sólo entrega seis variables
explícitas sin credenciales. Seccomp rechaza la creación de sockets IPv4 e IPv6,
también en los procesos hijos; se comprobó la restricción antes de las pruebas.
Permite sockets Unix locales usados por Ansible. No se arrancan servicios,
reinician unidades, escanean servidores ni leen historiales reales de accesos.
Las pruebas de servicios usan un `systemctl` ficticio; los certificados son
fixtures públicos o certificados sintéticos creados en directorios temporales.

## Límites y siguiente paso externo

La interpretación de fechas se comprobó con locales glibc reales alemán y francés.
Las sondas `lastb`/`who` se ejercitaron como tareas Ansible reales, con ejecutables
de prueba que emiten fixtures localizados según `LC_ALL`; su salida debe producir
exactamente el golden saludable existente. Este entorno no trae los catálogos
de traducción de util-linux: el intento adicional con `lastb` nativo produjo inglés
en los tres idiomas. **No** se presenta como reproducción en un host alemán real.
`native-lastb.txt` conserva esa observación.

No se ejecutó toda la matriz upstream, pre-commit, ansible-lint ni Molecule en
hosts systemd de las cuatro distribuciones, ni la matriz de ansible-core 2.16 y
la versión más nueva. Eso queda pendiente antes de una contribución upstream;
las pruebas focalizadas no sustituyen esos controles ni demuestran despliegue.
El cambio no aborda todos los otros caminos desconocidos de #39/#119 ni cambia
la política de renovación, revocación o reinicio de servicios.

[CONTRIBUTING.md](https://github.com/sameeralam3127/linux-vitals/blob/086d99a7877f9d70bcae06dd2bcb2ade1816ecb5/.github/CONTRIBUTING.md)
pide reclamar el issue mediante un comentario y ejecutar sus controles antes del
PR. Hace falta autorización específica de Pedro para enviar ese comentario y un
PR a `sameeralam3127/linux-vitals`. No se enviaron, no se aceptó ningún contrato,
y no hay evidencia de aplicación ni adopción. `UPSTREAM_DRAFT.md` deja preparada
la acción concreta para revisión.

El parche y sus fixtures derivan de software **MIT**, copyright 2026 Sameer Alam;
se conserva `LICENSE`. Los cambios y el arnés fueron preparados con asistencia
de Codex para Genius. Los recibos validan coherencia del registro, no verdad ni
independencia de las observaciones.
