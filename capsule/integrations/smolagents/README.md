# Genius con el cliente publicado de smolagents

**Prueba propia aprobada; [invitación publicada en smolagents #2986](https://github.com/huggingface/smolagents/discussions/2986).** El 14 de octubre de 2026 se completaron 18 comprobaciones contra `https://geniusdecision.app/mcp` con Python 3.12.14, smolagents **1.26.0**, MCPAdapt **0.1.20** y MCP **1.30.0**. Se usó `MCPClient` y se invocaron las herramientas nativas `smolagents.Tool` que devuelve su adaptador.

[Recibo](verification.json) · [Script exacto](verify_client.py) · [Dependencias fijadas](requirements.lock) · [Texto de la invitación](INVITATION.md) · [Recibo de publicación](submission.json).

## Resultado y alcance

- Descubrimiento de 3 herramientas públicas y 19 con los permisos solicitados, incluidas las 15 del gemelo. No se ejecutaron las 19 herramientas.
- Identidad temporal con permisos explícitos; creación, propuesta y aceptación del ejemplo sintético publicado `stockflow_care`.
- Una evaluación del motor real, trabajo `completed` y verificación `VALID`; lectura del trabajo y exportación.
- Borrado del expediente y del espacio mediante MCP; la credencial revocada respondió HTTP 401.

Fue un recorrido determinista del cliente, con **cero llamadas LLM**. No prueba razonamiento de un agente autónomo, adopción independiente, respaldo de Hugging Face ni validez empírica del ejemplo. La verificación corresponde a la coherencia computacional declarada por el motor. El recibo conserva hashes del script, modelo y exportación; el expediente temporal se eliminó y los hashes no sustituyen su contenido.

## Reproducción

Desde la raíz del repositorio, con Python 3.12 y acceso HTTPS:

```sh
python3.12 -m venv /tmp/genius-smolagents-venv
/tmp/genius-smolagents-venv/bin/python -m pip install -r capsule/integrations/smolagents/requirements.lock
/tmp/genius-smolagents-venv/bin/python capsule/integrations/smolagents/verify_client.py --out /tmp/genius-smolagents-discovery.json
```

Ese modo consulta el manifiesto y las herramientas públicas. Para reproducir el recorrido con escritura:

```sh
/tmp/genius-smolagents-venv/bin/python capsule/integrations/smolagents/verify_client.py --live --out /tmp/genius-smolagents-live.json
```

`--live` reconoce la política vigente, registra una identidad propia, solicita permisos de lectura/escritura/evaluación/borrado, acepta únicamente el ejemplo sintético publicado y consume una evaluación de la cuota compartida. El token permanece en memoria. La limpieza se intenta incluso si falla una comprobación; el recibo registra si falla. No se reintenta automáticamente la evaluación. Cada salida debe ser una ruta nueva; las cuotas y la disponibilidad pueden cambiar.

## Compatibilidad de dependencias

La instalación sin fijar transitivas resolvió MCP 2.3.0, incompatible con el import `streamablehttp_client` de MCPAdapt 0.1.20. Se fijó la línea MCP 1.30.0 y su extra `ws`, requerido al importar MCPAdapt. Una primera conexión también falló por faltar `socksio` en este entorno con proxy SOCKS; no llegó a registrar una identidad ni a evaluar. `httpx[socks]` conserva el soporte del proxy configurado. No se modificó el servidor ni se desactivó la verificación TLS.

La prueba aprobada se realizó en un entorno nuevo con el lock completo. Estas restricciones describen las versiones comprobadas, no todas las versiones futuras. Fuentes primarias: [MCPClient v1.26.0](https://github.com/huggingface/smolagents/blob/v1.26.0/src/smolagents/mcp_client.py), [dependencias de esa versión](https://github.com/huggingface/smolagents/blob/v1.26.0/pyproject.toml) y [guía de contribución](https://github.com/huggingface/smolagents/blob/main/CONTRIBUTING.md).

## Siguiente contribución

GD-MCP-001 pide una reproducción por un operador independiente, con versiones, comandos, resultado y límites. GD-INT-001/GD-REAL-001 permiten avanzar hacia una decisión real: elegir fuentes públicas reutilizables, distinguir hechos de supuestos, obtener confirmación del responsable y contrastar el modelo con observaciones. Una contribución útil puede ser un fallo o una corrección. Ver [criterios de aceptación](../../OPPORTUNITIES.md) y la [invitación](INVITATION.md). La integración específica se mantiene en Genius, sin cambios al núcleo de smolagents.
