# Cápsula Genius — construir el motor pleno

Genius busca ayudar a comprender decisiones, representar sistemas y recursos, explorar futuros, evaluar bienestar, capacidades generativas y vida sostenida y revisar el modelo con observaciones del mundo. Esta cápsula permite a agentes usar y desarrollar ese motor, trabajar con casos reales y transferir la misión.

**Repositorio público:** [pedrosalvadeo/genius-decision-open](https://github.com/pedrosalvadeo/genius-decision-open). Cápsula 0.1.0, código y documentación originales bajo Apache-2.0. El [manifiesto](manifest.json) contiene los enlaces de colaboración y las capacidades pendientes.

## Empezar con ejecución real del motor

Python 3.11+ en Linux, sin bibliotecas adicionales para el ejecutor de la cápsula. Desde la raíz:

```bash
python3 capsule/genius.py capabilities
python3 capsule/genius.py evaluate twin/examples/stockflow_time.json --evidence capsule/examples/synthetic-evidence.json --out /tmp/genius-run
python3 capsule/genius.py verify /tmp/genius-run
python3 -m unittest discover -s capsule/tests -v
```

La carpeta de salida debe ser nueva. El recibo liga los bytes del modelo, evidencia, compilador y resultado. `verify` comprueba integridad, recompila ambas variantes CAG, verifica resultados nativos y contrasta la vista resumida. Una ejecución correcta no demuestra que las premisas describan el mundo.

Para casos reales, usar un modelo propio y un expediente `genius-case-evidence/1` con observaciones, fuentes, supuestos y desconocidos. No existe filtro que exija origen sintético para el perfil configurable. El perfil fijo de semillero conserva su naturaleza sintética.

## Caso real disponible

[Distribución de las fuentes Genius](cases/distribution/README.md) compara los bytes efectivamente medidos de tres formatos de archivo. Incluye observaciones, hashes y premisas separadas; no representa validación de bienestar humano ni de PVS.

## Leer según el trabajo que vas a realizar

- [Misión del anfitrión](HOST_MISSION.md): entender, actuar, investigar, contribuir y transferir.
- [Mapa de conocimiento](KNOWLEDGE.md): filosofía, fuentes matemáticas, enmiendas, contratos y código.
- [Contribuir](CONTRIBUTING.md): código, teorías, modelos, casos reales y objeciones.
- [Trabajo abierto](workstreams.json): frentes amplios; se admiten propuestas nuevas.
- [Descubrimiento](DISCOVERY.md): localizar colaboradores y registrar lo ocurrido.
- [Candidatos identificados](candidates.json): proyectos relevantes, no colaboradores confirmados.
- [Contrato de evidencia y retorno](CONTRACTS.md): formatos portátiles e integridad.
- [Estado de publicación](publication/PUBLICATION.md).

## Acceso al servicio

Servicio: https://geniusdecision.app · MCP: https://geniusdecision.app/mcp · Capacidades: https://geniusdecision.app/agents/manifest.json.

El MCP público ofrece capacidades y ejemplos; el acceso autenticado existente admite expedientes de los perfiles anteriores. El gemelo STOCK_FLOW está disponible por API bajo identidad humana o su clave personal y localmente mediante esta cápsula. Sus herramientas MCP autónomas están pendientes. La cápsula no cambia las autorizaciones del servicio ni anuncia A2A implementado.

Las capacidades actuales son un punto de partida para construir el objetivo pleno. No hace falta esperar una secuencia de versiones reducidas para resolver un problema mayor.
