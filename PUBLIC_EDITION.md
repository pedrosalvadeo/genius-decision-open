# Edición pública: qué falta y qué deja de funcionar

Este repositorio es una extracción del paquete de trabajo original. Algunas
carpetas recibidas nunca se publicaron, ni en el historial de git. Producción
(Railway) se construye desde este repositorio, así que hereda las mismas
ausencias.

## Carpetas ausentes

| Ruta esperada | Qué contenía | Qué deja sin funcionar |
|---|---|---|
| `beta/vendor/R0`, `beta/vendor/R1` | Paquetes recibidos R0 (copia del kernel) y R1 (verificador FDQ: `research/verify_fdq.py`, `research/fdq_oracle.py`) | El perfil FDQ. La API lo rechaza con `FDQ_VERIFIER_NOT_IN_PUBLIC_EDITION`. El kernel de R0 se sustituye por `kernel/`, que tiene los mismos bytes fijados en `product_local/genius_local/fdq_worker.py`. |
| `baseline/GENIUS_PHASE_1_HANDOFF` | Corpus de conformidad (`GENIUS_PROGRAM/conformance`) e historial de fases | 7 pruebas de `kernel/tests/test_conformance.py` y `kernel/tests/run_suite.py` |
| `baseline/R1`, `baseline/received_baseline/R0` | Las mismas líneas base R0/R1 | Las pruebas FDQ y de alcance recibido de `product_local/tests` y `consumer_views/tests` |
| `PHASE_5_*.md`, `ACCEPTANCE_REPORT.md`, `DECISIONS.md`, `KNOWN_LIMITATIONS.md`, `validation/` (raíz) | Documentos de fase citados desde `GENIUS_PROGRAM/*.md` | Enlaces rotos en esos documentos |

## Qué sí funciona y se prueba en CI desde un clon limpio

- El gemelo (`twin/`), con los casos reales: workflow `twin-tests.yml`.
- Todo `beta/tests`, incluidos los perfiles de horas y de elección: workflow `club.yml`.
- El navegador del gemelo y de las intervenciones: workflow `interventions.yml`.

Las pruebas que dependen de las carpetas ausentes vuelven a ejecutarse
completas en cuanto esas carpetas existan. Ninguna se borró.
