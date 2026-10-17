# MemWhale #423 — notas de recuperación con evidencia explícita

Estado: **SOLUTION_PREPARED**, 16/10/2026 en Argentina (17/10 UTC).
No enviado, aplicado ni verificado en MemWhale. Integrar este paquete en Genius
no equivale a adopción por el proyecto externo.

Necesidad: [issue #423](https://github.com/wuisabel-gif/MemWhale/issues/423).
Los usuarios de agentes necesitan distinguir una solución candidata de una
observada en dos o más episodios, sin interpretar correlación como causalidad.
Se priorizó esta solicitud existente, abierta y sin asignación, por su alcance
acotado y verificable; no se amplió la muestra de búsqueda.

## Entrega

`solution.patch` modifica sólo cinco README sobre la base upstream
`07e6ac952dbbb7b527fe78578271cd57937f0890`. Cuatro secciones idénticas de nueve
líneas (incluidos título y blanco interior, sin separador final) explican los
dos niveles, procedencia, almacén local compartido y cómo silenciar las notas
sin desactivar captura. Rho tiene una sección de tres líneas: no emite notas.
Se elimina la certeza obsoleta de Cursor, Codex y Gemini. No cambian código,
comandos de instalación, limitaciones ni declaraciones de verificación previa.
Licencia upstream MIT conservada en `LICENSE.upstream`.

Reserva y criterios publicados antes de editar:
[6b18a73](https://github.com/pedrosalvadeo/genius-decision-open/commit/6b18a73e623be6f2f1298a16c64cc49da18715a0).
`claim.json` conserva los criterios; `source-review.md` contrasta las afirmaciones.

## Comprobación reproducible

En un checkout de MemWhale fijado a la base anterior, con Python 3.12 y git:

```sh
# MW_CASE debe ser la ruta absoluta a este directorio dentro del checkout Genius.
git apply --check "$MW_CASE/solution.patch"
git apply "$MW_CASE/solution.patch"
git diff --check
python3 -B "$MW_CASE/verify_case.py" .
```

El verificador sólo lee Markdown; no ejecuta los comandos documentados.
El contrato de hashes se capturó antes de editar. Para repetir el aislamiento
Linux utilizado, ejecutar desde la raíz de Genius, con libseccomp disponible:

```sh
python3 -B resolver/cases/linux-vitals-149-locale/run_no_network.py \
  /usr/bin/python3 -B resolver/cases/memwhale-423-recall-guide/verify_case.py \
  /ruta/al/checkout/memwhale
```

Antes: cinco métodos fallan (18 subcomprobaciones), cuatro pasan. Después:
**nueve controles aprobados**, repetidos en copia limpia con el parche aplicado.
Logs: `baseline.log`, `acceptance.log`, `portability.log`, `isolation.log`.
Los controles verifican texto/estructura, no prueban por sí solos la semántica;
ésta se revisó contra Rust y release notes fijados. Ningún binario de MemWhale,
base de datos personal, sesión real de agente o instalación fue ejecutado.
Las suites npm/Rust y el script de referencias que necesita Cargo no se corrieron;
no se afirma verificación integral upstream ni de clientes en vivo.

## Paso externo pendiente

Se necesita permiso específico de Pedro para comentar en #423 y enviar el PR
externo. CONTRIBUTING y #317 piden comentar antes de reclamar trabajo: la reserva
de Genius es sólo interna. `UPSTREAM_DRAFT.md` contiene textos listos, no enviados;
releer disponibilidad y coordinar antes de presentarlos. No se aceptó CLA/DCO ni
ningún contrato. Si entretanto otro contribuyente se ocupa, no duplicar el trabajo.

El motor Genius no se ejecutó: esta corrección documental no tiene una
representación matemática justificada dentro de su dominio. No se inventaron
puntuaciones, CAG, PVS ni bienestar. Lección conservada: distinguir evidencia
observada, capacidad documentada y verificación en vivo, y conservar excepciones
como Rho y la salida desconocida de Codex.
