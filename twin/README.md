## Sistemas, observaciones y límites — 16/10/2026

La pestaña **Sistemas** registra vistas con fuentes y propone agrupaciones a partir de relaciones declaradas. Permite revisar los límites del sistema, intervención y evaluación, conservar impactos externos y vincular identidades al modelo. Son hipótesis acotadas, no descubrimiento causal ni percepción libre. El cálculo numérico conserva sus reglas; nueva evidencia exige revisar el alcance. [Contrato y pruebas](docs/SYSTEM_RECOGNITION.md).

# Diseño de intervenciones

El gemelo incorpora generación de alternativas mediante transferencias de recursos, apertura/cierre de relaciones y programación de acciones. Acceso humano en **Intervenir**, API y MCP; revisión, confirmación y evaluación con el kernel existente. Ver [contrato, ejemplo y continuidad](docs/INTERVENTION_DESIGN.md). El estado de despliegue y CI se informa en el PR del incremento.

Los apartados siguientes conservan los antecedentes D3/D1.

# Incremento vigente: D3

Genius ahora incorpora un constructor configurable de recursos, acciones y escenarios, además del semillero. La validación con casos reales se pospone sin bloquear desarrollo. Ver [operación y arranque](docs/D3_OPERATION.md), [API](docs/D3_API.md), [contrato del modelo](docs/STOCKFLOW_CONTRACT.md) y [continuidad](docs/PRODUCT_ROADMAP.md). El montaje autenticado fue probado localmente; D3 todavía no está recibido como despliegue público.

El contenido D1 siguiente se conserva como registro de su incremento original.


# GENIUS · Gemelo dinámico D1

Primer recorrido local de texto a propuesta revisable, modelo temporal, evaluación FP1, edición material, nueva versión y contraste con una predicción congelada. Es un adaptador nuevo y explícito para el **caso sintético de semillero de 14 días**. No modifica el núcleo, el perfil `fdq`, los contratos R2/R3 ni la aplicación beta.

El relato propone una plantilla acotada que debe revisarse; no hay traducción general de lenguaje a cualquier modelo. El caso estipula plantas vivas, estados diarios y una ley conjunta N/H/HA. PVS expresa cumplimiento de la tarea hídrica bajo esas premisas, no supervivencia real estimada. Las observaciones manuales conservan su procedencia declarada y no validan ni recalibran automáticamente el modelo.

## Ejecutar localmente

Python 3.11 o posterior. Desde la raíz del repositorio, con un entorno virtual activado:

```bash
python -m pip install --require-hashes -r beta/requirements.lock
PYTHONPATH=twin:kernel python -m genius_twin --port 8765
```

Abrir `http://127.0.0.1:8765`. El servidor solo enlaza con loopback; no tiene modo público, llamadas a proveedores, CDN ni adquisición externa. Usa Flask como servidor de desarrollo local y SQLite en `twin/local-data/twin.sqlite3`. Puede cambiarse la ubicación con `--database /ruta/privada/expediente.sqlite3`. La base contiene relatos y observaciones: se conserva fuera de Git. Esta herramienta no es un despliegue multiusuario.

## Recorrido

1. Usar el relato de ejemplo o describir una decisión de semillero. Un dominio ajeno conserva el relato y registra la capacidad de modelización pendiente.
2. Revisar las premisas materiales y reconocer el alcance sintético; aceptar crea la primera versión del expediente.
3. Evaluar C/R/E. Explorar estados diarios, tiempo por persona, condición hídrica, CAG posible/robusto y evento de trayectoria.
4. Proponer adelantar formación/verificación al día 9 y relevo de A el día 10. Aceptar crea otra versión con C/R/E′ y exige una evaluación nueva.
5. Comparar versiones, registrar observación contra una evaluación congelada, exportar el expediente o restaurar contenido mediante una revisión nueva.

El diseño llama v2 al caso base y v3 al caso editado; los expedientes de la aplicación empiezan en **versión 1** tras la primera aceptación. Sus revisiones no son números de versión del diseño.

## Contrato y evidencia

- [Dominio](docs/DOMAIN_CONTRACT.md): balances, portadores, firmas, reloj y límites.
- [Compilación](docs/COMPILATION.md): correspondencia al perfil cerrado FP1 y conservación de los bytes y resultados nativos.
- [Experiencia de uso](docs/UX.md): vistas y operaciones equivalentes.
- [Protocolo empírico](docs/EMPIRICAL_PROTOCOL.md): contraste real y comprensión humana pendientes, con responsables e insumos mínimos.
- [Recepción técnica](docs/D1_RECEIPT.md): resultados ejecutados, alcance y limitaciones al cierre.

La API HTTP JSON local sirve el mismo expediente que utiliza la interfaz. `GET /api/capabilities` declara capacidades; `GET /api/cases/{id}/export` entrega versiones, trabajos, resultados canónicos, entradas congeladas, resultados nativos y verificación. Es un contrato nuevo `genius-twin-*`, **no** un recibo R2/RC01 ni un servidor MCP.

## Verificar

```bash
PYTHONPATH=twin:kernel python -m unittest discover -s twin/tests -v
```

Las pruebas ejercitan el oráculo independiente, el compilador real y el núcleo, monitor de incumplimiento, ramas de masa cero, ediciones, idempotencia, concurrencia, observaciones y límites HTTP. Las cifras sintéticas de las pruebas no constituyen datos de campo. La recepción incluye además el recorrido del navegador en escritorio y móvil documentado en el acta.

Para repetir el gate del navegador, instalar Playwright y Chromium como herramientas locales y ejecutar `twin/tests/browser_smoke.cjs` con Node. `PLAYWRIGHT_MODULE` indica la ruta al módulo Playwright; `CHROMIUM_PATH`, su navegador; `PYTHONPATH`, las dependencias Python y `twin:kernel`; `BROWSER_QA_DIR`, una carpeta temporal opcional. El test inicia y cierra su servidor local, usa un expediente sintético propio y no contacta servicios externos. Los binarios de prueba no forman parte del repositorio.
