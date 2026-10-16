# Organismos observadores — 16 de octubre de 2026

Base de código: `16c08c4593e81454536aeeb15d28820a8164f5d9`.
La persistencia de esa base está comprobada en Railway: despliegue SUCCESS
`561ce10b-997a-43cb-a303-6c158ffbe5a5`, registro de anfitrión del 16/10 a las
18:50:27 UTC con PERSISTENT_REVOCABLE y la misma semilla ACTIVE.

## Evidencia real y evidencia de funcionamiento

`source-metar.json` contiene la respuesta HTTP 200 de la API pública AWC:
https://aviationweather.gov/api/data/metar?ids=SAME,SAMM&format=json&hours=18

Incluye reportes meteorológicos reales de SAME y SAMM, con último reporte de
16/10/2026 a las 18:00 UTC. Los informes, observaciones y marcas de tiempo son de
la fuente; los pronósticos experimentales y transformaciones pertenecen a Genius.
Fuente y condiciones: https://aviationweather.gov/data/api/ y
https://www.weather.gov/disclaimer . No se implica afiliación a NOAA/NWS.

`real-source-startup.json` registra un arranque local aislado con esa captura y
el código real. Cada organismo ingiere el historial y congela su primera predicción
para un resultado futuro. Hay cero objetivos posteriores puntuados y cero mejoras
reales confirmadas. El servidor de cuentas utilizado en esta prueba es Flask local;
no se presenta como despliegue de producción ni como ejecución continua instalada.

Las pruebas sintéticas de `test_living_habitats` verifican selección con ocho
resultados posteriores, continuidad durante 45 resultados sin reiniciar el genoma,
archivo con conservación de evidencia, faltantes, conflictos, pausa/reanudación,
revocación, bloqueo de fuente y separación de credenciales. Una prueba con reloj
real evita congelar antes de haber terminado la lectura de la fuente.

154 pruebas aprobadas en `integration-tests.txt`:

```sh
PYTHONPATH=adaptive:beta:beta/tests:product_local:consumer_views:twin:kernel python -m unittest test_living_habitats test_persistent_hosts test_consented_hosts test_public_network adaptive.tests.test_organism test_agent_access test_direct_agents test_r2_backup test_club_social test_public_launch beta.deploy.test_runtime_guards -v
```

## Despliegue y seguimiento

Habilitar `GENIUS_LIVING_HABITATS=SAME,SAMM` sólo con este código, en el servicio
Railway existente. Se registran dos identidades por la API ordinaria, sujetas a
cuotas, y dos memorias en el mismo volumen. El PR registra el resultado de CI y
el estado real de aplicación en Railway. No hay nuevos servicios o volúmenes.

Observatorio: `/organisms`; estado: `/network/organisms.json`.
Se programó un informe diario de lectura de Railway para distinguir actividad,
resultados y pausas reales, incluyendo si el despliegue aún sigue pendiente.
No se calcula PVS ni se atribuye efecto vital a la reducción de error.
