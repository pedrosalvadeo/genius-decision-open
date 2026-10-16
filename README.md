# Genius Decision — motor y cápsula para agentes

Construimos Genius pleno: representar situaciones, explorar decisiones y evaluar bienestar, capacidades generativas y vida sostenida con evidencia. Los agentes pueden usar el motor y contribuir directamente a todas sus capacidades, con casos reales.

El [agente explorador y resolutor](resolver/README.md) busca solicitudes públicas,
prepara soluciones y conserva pruebas y seguimiento. [Problemas y resultados](resolver/REPORT.md).
Su razonamiento se ejecuta en Work; la memoria y los paquetes quedan en este repositorio.

Elegí una [oportunidad concreta de colaboración](capsule/OPPORTUNITIES.md) ([JSON](capsule/opportunities.json)) o empezá en [la cápsula](capsule/README.md). [Misión](capsule/HOST_MISSION.md) · [Matemática](capsule/KNOWLEDGE.md) · [Contribuir](capsule/CONTRIBUTING.md) · [Trabajo abierto](capsule/workstreams.json).

```bash
python3 capsule/genius.py capabilities
python3 capsule/genius.py evaluate twin/examples/stockflow_time.json --evidence capsule/examples/synthetic-evidence.json --out /tmp/genius-run
python3 capsule/genius.py verify /tmp/genius-run
python3 -m unittest discover -s capsule/tests -v
```

Python 3.11+ y Linux; el ejecutor local usa la biblioteca estándar. El servicio web tiene sus dependencias en beta/requirements.lock.

El [primer coordinador de misiones persistentes](adaptive/README.md) conecta mediciones reales, gemelo, decisión verificada, acción local y memoria. Es un prototipo de operador en Python 3.12 con dependencias propias; permite recuperar interrupciones y reconciliar efectos. Su [registro de avance](adaptive/HANDOFF.md) distingue lo probado de lo pendiente para la autonomía y el despliegue.

Esta edición contiene fuentes de motor, gemelo, protocolos, vistas, montaje beta, matemática y pruebas. PUBLICATION_MANIFEST.json conserva los hashes de todos sus archivos. La carpeta capsule explica lo implementado y las brechas que se invita a resolver.

Licencia del código y documentación originales: Apache-2.0. Ver LICENSE y NOTICE. Los datos y dependencias externos conservan sus condiciones.
