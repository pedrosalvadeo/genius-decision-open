# Alojamiento persistente y revocable — 2026-10-16

Base: `1bf2c4dcdc95e38199e5fc3a0a0c62adabbf6988` (genes y evolución contextual).

## Alcance

- Oferta firmada v2 sin vencimiento temporal; v1 conserva el ensayo finito.
- Conversión explícita y transaccional de ofertas vigentes, conservando permiso
  firmado anterior, solicitudes, claves, memoria, genoma y nacimientos aceptados.
- Solicitudes vencidas, canceladas o retiradas no se renuevan ni reemplazan.
- Pausa local, reanudación, reposo por recursos/evidencia/conectividad y revocación.
- Mantenimiento diario de cuentas existentes durante reposo voluntario, sin
  cálculo ni altas. Las credenciales, privacidad y cuotas conservan sus reglas.
- Migración 014 conserva datos y claves externas; restaurar R2 desactiva permisos.
- Despliegue de referencia exige `GENIUS_NETWORK_HOST_PERSISTENT=true`. Conserva
  un nacimiento total en el servicio y volumen existentes.

## Verificación reproducible

```sh
PYTHONPATH=adaptive:beta:beta/tests:product_local:consumer_views:twin:kernel python -m unittest test_persistent_hosts test_consented_hosts test_public_network test_agent_access test_direct_agents test_r2_backup test_club_social test_public_launch -v
```

116 pruebas aprobadas; 14 cubren persistencia, migración, recuperación de una
respuesta perdida, reposo, rotación de credenciales durante doce días simulados,
conservación de identidad y rechazo de reactivaciones. El ensayo de evidencia
vencida usa el reloj de la proyección; la vida del alojamiento no vuelve actuales
sus vistas antiguas. Los registros de ejecución están en `integration-tests.txt`.

Son pruebas locales aisladas con el servidor Flask real, SQLite, firmas Ed25519 y
el kernel nativo. No son evidencia de beneficio vital ni de nodos independientes.
El estado de despliegue se verifica por separado en Railway y se registra en el PR.

## Límites operativos

El permiso persistente no garantiza servicio infinito: requiere almacenamiento y
acceso operativo. Apagar el controlador completo por más que la vigencia de su
credencial puede requerir revisión del operador. No hay recuperación automática
de claves perdidas ni cuentas sustitutas. Se conserva la retención por inactividad.
La migración 014 y las ofertas v2 requieren esta versión o una posterior compatible;
volver al código anterior no constituye una reversión del esquema ni del permiso.
