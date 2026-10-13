# Estado vigente — decisiones cotidianas guiadas, 06/10/2026

Mandato nuevo de Pedro: avanzar en traducción de problemas, perfiles admitidos y validación real, conservando Plan Maestro v2 y R0–R3. Implementado **CHOICE_DECLARED_V1**, código **7c9348e2cb9fdbf4186f9a0767ac2211de8ad71a**: guía de cuatro pasos, revisión/confirmación de modelo, comparación con el Kernel FP1 recibido, recomendación condicional, alternativas, límites, sacrificios, desconocidos, versiones y feedback; API/MCP `prepare_decision` y `revise_case`.

Alcance: ocio/organización personal de bajo riesgo; 2–8 alternativas, 1–5 criterios explícitos. La narrativa aporta contexto, no se interpreta automáticamente en la web. No LLM externo, búsqueda de datos, probabilidad inventada ni admisión empírica de CAG/PVS. La compilación declara constantes formales comunes para dimensiones no evaluadas; la recomendación sólo vale para la tabla confirmada. No es un Radar/Solver general. Diseño: `beta/DECLARED_CHOICE_DESIGN.md`.

**Preparado y probado:** 92 pruebas locales, 14 nuevas; navegador escritorio/móvil PASS; cliente MCP oficial PASS; fuentes recibidas 13/79 intactas. CI **37446221959**, verify **112211582416 SUCCESS**, incluidos navegador, Docker, HTTPS, MCP y recuperación. Recomputación formal y pruebas de autor; no se afirma auditoría externa nueva.

**Publicado:** MCP y demo anteriores ya están publicados: deployment **0e68fe1a-3228-4936-9f67-2ef27d3d6ca9 SUCCESS**, fuente efectiva **0cad72775d6676a423f7d0d85363b487f6068b4e**. El nuevo perfil cotidiano todavía no está publicado: patch **1353ae55-c12e-4440-847c-3e76160b3e72 STAGED**, un cambio no destructivo de código, pendiente de **Apply manual de Pedro**. No se llamó accept-deploy.

**Evidencia real:** no se incorporaron casos reales admitidos en este ciclo. **F6A ABIERTA / G6A PENDIENTE**. Protocolo de campo preparado en `beta/DECLARED_CHOICE_FIELD_PROTOCOL.md`; feedback percibido no acredita utilidad ni comprensión. Sin migración, proveedor, secreto, plan o recurso nuevo; se mantienen presupuestos/cuotas/retención.

Checkpoint: `beta/DECLARED_CHOICE_CHECKPOINT.md`; evidencia: `beta/evidence/declared_choice_prepared_2026-10-06.json`; próxima acción: recibir Apply y verificar producción. La falta de participantes no detiene ingeniería ni autoriza inventar demanda o evidencia.


---

## Registro histórico conservado; el estado vigente figura arriba

# Genius · beta autoservicio acotada

Este hito complementa el Plan Maestro v2. Web/API persistentes para créditos formales y verificación FDQ de bytes/certificados aportados. **No está publicado** hasta habilitar y recibir infraestructura real. F6A abierta y G6A pendiente; no Radar/Solver, ni validación de eficacia real.

## Preparación local

Linux x86_64, CPython3.12. Desde la raíz del repositorio:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: --require-hashes -r beta/requirements.lock
export PYTHONPATH=beta:product_local:consumer_views
export PYTHONDONTWRITEBYTECODE=1
export GENIUS_DATA_DIR=/ruta/privada/genius-dev
export GENIUS_PUBLIC_URL=http://127.0.0.1:8080
.venv/bin/python -B beta/tools/verify_runtime.py
.venv/bin/python -B -m unittest discover -s beta/tests -p 'test_*.py' -v
```

En dos terminales del mismo entorno:

```sh
.venv/bin/python -B -m gunicorn --bind 127.0.0.1:8080 --workers 1 --threads 4 'genius_beta.app:create_app()'
.venv/bin/python -B -m genius_beta.worker
```

Abrir `http://127.0.0.1:8080`. Crear alias y contraseña, leer alcance/privacidad, cargar un ejemplo sintético o datos autorizados, guardar y ejecutar. Los ejemplos nunca aceptan condiciones ni se envían automáticamente. Cuenta/expedientes se conservan fuera de la conversación. La API usa sesión/CSRF o clave Bearer; documentación pública en `/static/api.html`. No copiar claves al chat.

La configuración de desarrollo escucha sólo localhost. Producción exige HTTPS, responsable/contacto configurados, recepción y las comprobaciones de `docs/OPERATIONS.md`. No exponer Gunicorn de desarrollo como una beta pública aceptada.

## Pruebas y operación

- `tests/test_adapter.py`, `test_examples.py`, `test_backend.py`: perfiles y servicio.
- `deploy/test_recovery.py`: recuperación y borrado.
- `tools/benchmark.py`: cargas sintéticas declaradas, no F6A.
- `tools/run_browser_test.py` y `tests/browser_e2e.cjs`: navegador contra Gunicorn+worker reales en una misma red local; requiere Playwright y `GENIUS_BROWSER_PATH` externo. Capturas en `GENIUS_BROWSER_OUTPUT`.
- `.github/workflows/beta-verify.yml`: verificación manual preparada; su existencia no significa ejecución de CI ni autoriza consumo adicional.
- `deploy/Dockerfile`, `deploy/railway.json`: artefactos de integración. Construcción/despliegue en nube aún pendientes.

`STATE.md`, `ACCEPTANCE_REPORT.md`, `TEST_RESULTS.md` y acta receptora externa fijan la entrega comprobada. `docs/INFRASTRUCTURE.md` concentra accesos, presupuesto, datos y autorización necesarios; `NEXT_PHASE_PROMPT.md` permite retomar desde el commit recibido.
