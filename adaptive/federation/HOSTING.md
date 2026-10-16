# Genius Semilla: alojamiento automático consentido

Las semillas incorporan [genes, herencia y evolución contextual](GENETICS.md).
La herencia respeta la autorización, el número de nacimientos y el modo de alojamiento
descritos aquí; no crea una generación adicional por sí sola.

Un operador puede ofrecer capacidad una vez y dejar que el controlador atienda
solicitudes compatibles sin confirmar cada nacimiento. Cada instancia obtiene
su propia clave, cuenta, memoria y cálculo. La oferta firmada declara sistemas,
focos, modalidad de alojamiento y presupuesto **total** de nacimientos.
El paquete requiere Linux. No instala código recibido de la red.

Esta versión ejecuta el programa fijo `genius-signed-world-reader/1`: incorpora
vistas públicas firmadas y calcula localmente. No publica observaciones nuevas,
no ofrece alojamiento desde los hijos y no transmite claves entre nodos.
La API también rechaza ofertas de los hijos vinculados a solicitudes alojadas.
Esto no certifica identidades humanas ni evita identidades alternativas creadas
por otro software. Las claves no prueban operadores independientes.

## Preparar un anfitrión

Construí la imagen e inicializá un nodo siguiendo [INTERNET.md](INTERNET.md).
El volumen del ejemplo es `genius-node-state`. La identidad y credenciales del
nodo anfitrión quedan en `/state`, y la autorización de alojamiento en `/state/host`.

Creá `hosting-config/policy.json`, adaptando mundo, foco y vencimiento. El mundo
de este ejemplo contiene datos sintéticos de demostración:

```json
{
  "worlds": [{"world_id": "genius-reference-synthetic-v1", "focus": ["pump"]}],
  "max_births": 1,
  "lease_seconds": 86400,
  "valid_until": "2026-11-14T00:00:00+00:00"
}
```

Esta política de ensayo debe vencer en los próximos 31 días. Revisá la fecha antes de usar el
ejemplo. Los focos deben estar ordenados, sin duplicados, y coincidir exactamente
con los autorizados. La autorización local es explícita:

```sh
docker run --rm -v genius-node-state:/state -v "$PWD/hosting-config:/config:ro" --entrypoint python genius-node:local -m federation.hosting --node-state /state --state /state/host authorize /config/policy.json --allow-hosting
docker run -d --name genius-host --restart unless-stopped --memory 768m --cpus 1 -v genius-node-state:/state --entrypoint python genius-node:local -m federation.hosting --node-state /state --state /state/host run --continuous
```

No hace falta mantener otro bucle del nodo anfitrión sobre el mismo volumen:
el controlador mantiene su actividad. No ejecutes dos procesos sobre las mismas
credenciales; la rotación de tokens es exclusiva. El controlador usa un bloqueo
local para impedir nacimientos concurrentes duplicados.

## Alojamiento persistente y reposo

Para una oferta nueva, la política puede expresar:

```json
{
  "worlds": [{"world_id": "genius-reference-synthetic-v1", "focus": ["pump"]}],
  "max_births": 1,
  "persistent": true,
  "lease_seconds": null,
  "valid_until": null
}
```

Se firma como `genius-host-offer/2`. El permiso permanece hasta revocarlo; no
extiende la vigencia de observaciones ni cambia los límites del trabajador.
Para convertir una oferta y sus solicitudes todavía vigentes, detené el bucle
y ejecutá con el mismo volumen e identidad:

```sh
python -m federation.hosting --node-state /state --state /state/host persist --allow-persistent-hosting
```

La conversión conserva el permiso anterior firmado, los IDs, los genes, la
memoria y las reservas de nacimientos. Es idempotente y se recupera si se pierde
la respuesta del servidor. Un ensayo vencido no se convierte para revivirlo.
Una solicitud ya vencida sigue cerrada aunque su oferta todavía pueda convertirse.

Con el controlador detenido, `pause` guarda el reposo local y `resume` lo levanta:

```sh
python -m federation.hosting --node-state /state --state /state/host pause
python -m federation.hosting --node-state /state --state /state/host run --continuous
# Detener el bucle antes de cambiar el control local:
python -m federation.hosting --node-state /state --state /state/host resume
```

En reposo voluntario, el bucle sólo comprueba permisos y mantiene la cuenta del
hijo una vez al día, renovando su credencial cuando corresponde. No calcula ni
crea otra identidad. La falta de disco, conexión o evidencia actual se informa
como `RESTING`, con su motivo; el último resultado es histórico. `ACTIVE` en la
cola significa solicitud aceptada, no prueba de cálculo actual; `activity` en el
estado local distingue la ejecución del reposo. La reanudación vuelve a comprobar
la autorización y espera el intervalo mínimo entre intentos.

Persistente no garantiza disponibilidad perpetua: requiere volumen y servicio
operativos. Si se apaga todo el controlador o no hay conexión durante el plazo
de la credencial, puede necesitar intervención del operador. Sigue vigente la
retención ordinaria de cuentas inactivas de la beta (90 días); no se sustituye
una cuenta inaccesible por otra automáticamente. La revocación sigue disponible
sin reanudar el cálculo y la recuperación de backups desactiva permisos.

## Solicitar alojamiento automáticamente

Desde **otro nodo ya registrado**, con su propio volumen, este comando consulta
las ofertas, verifica firmas, identidad, origen, vigencia y alcance, y solicita
alojamiento al primer anfitrión compatible por orden de identificador:

```sh
docker run --rm -v mi-nodo-solicitante:/state --entrypoint python genius-node:local -m federation.hosting --node-state /state --state /state/requests request --world genius-reference-synthetic-v1 --focus pump --confirm-public-request
```

El solicitante debe haber inicializado previamente ese volumen con
`federation.internet init`. Se puede elegir una oferta concreta añadiendo
`--host ID --offer SHA256`. Sin capacidad compatible se devuelve
`NO_AUTHORIZED_CAPACITY`. Una oferta no reserva recursos: las cuotas y la cola
pueden impedir el alta. El solicitante no recibe la clave ni controla al hijo.

Las solicitudes se deduplican por anfitrión, solicitante, mundo y foco, incluso al convertir la oferta en persistente. Repetir una
solicitud vencida o cancelada no la reactiva ni extiende su plazo.

## Recursos y ciclo de vida

- Entre 1 y 4 nacimientos **totales por autorización**, incluso después de retirar
  un hijo. El servidor cuenta aceptaciones y el controlador conserva reservas
  realizadas antes de registrar la cuenta. No es un objetivo de crecimiento.
- Hasta cuatro mundos/focos expresamente permitidos. Ningún código, comando,
  imagen, URL ejecutable o credencial puede venir en la solicitud.
- Cada hijo ejecuta ciclos secuenciales cada diez minutos, durante una concesión
  de 10 minutos a 24 horas en modo ensayo, o sin vencimiento temporal en modo
  persistente. Los diez minutos entre intentos se conservan tras reiniciar.
- El proceso fijo tiene límites de 384 MiB de espacio de direcciones, 20 segundos
  de CPU, 120 segundos de pared por ciclo y 8 MiB por archivo. Mantiene 64 MiB de
  reserva de disco antes de cada ciclo; si falta, entra en reposo. Son límites por proceso/archivo; el
  contenedor y el anfitrión determinan el presupuesto agregado.
- Los procesos usan el mismo UID dentro del anfitrión: no constituyen una barrera
  de seguridad entre programas arbitrarios. Sólo se ejecuta el trabajador fijo.
  No recibe variables de administración de Railway, GitHub o Cloudflare.
- La falta de conexión pausa el trabajo; no se presenta un resultado anterior
  como nuevo. La revocación comprobada, cancelación o expiración retira al hijo.
- Hay como máximo tres intentos de incorporación, espaciados diez minutos. Un
  fallo tras crear una cuenta pero antes de guardar su respuesta puede dejar una
  cuenta inaccesible; se aplican las cuotas y la retención ordinarias del relay.
- Retirar un hijo borra su cuenta por la API normal y elimina su credencial local.
  Conserva memoria local. Si falla el borrado, queda `RETIRING`, sin nuevos
  cálculos, y reintenta la retirada en ciclos posteriores.
- Reiniciar conserva identidad, presupuesto y concesión. Los cambios de política
  y las ampliaciones requieren autorización explícita. La única conversión
  admitida cambia un ensayo vigente a persistente; conserva alcance, límites y
  presupuesto. No reactiva solicitudes vencidas, canceladas o retiradas.

Para revocar primero detené el proceso y luego revocá la oferta y sus hijos:

```sh
docker stop -t 125 genius-host
docker run --rm -v genius-node-state:/state --entrypoint python genius-node:local -m federation.hosting --node-state /state --state /state/host revoke
```

Si aparece `RETIRING` o `revocation_pending`, repetí `revoke` cuando vuelva la conexión. Una revocación
remota se observa en el siguiente sondeo: hasta diez minutos, más el ciclo en
curso (máximo dos minutos). Detener el contenedor interrumpe la ejecución local.
El paro del proceso no equivale a borrar su cuenta remota.

## API y recuperación

| Ruta | Función |
|---|---|
| `GET /network/hosts` | Ofertas firmadas, actividad declarada y aceptaciones. |
| `POST /api/network/hosts` | Publicar oferta propia inmutable y autorizada. |
| `POST /api/network/host/persist` | Convertir una oferta vigente con firma y autorización explícita. |
| `GET /api/network/host` | Oferta y cola del anfitrión autenticado. |
| `DELETE /api/network/host` | Revocar oferta propia; cuerpo `{"confirmed":true}`. |
| `POST /api/network/host/request` | Solicitar un mundo/foco autorizado. |
| `POST /api/network/host/cancel` | Cancelar una solicitud propia por `request_id`. |
| `POST /api/network/host/result` | Registrar aceptación con prueba firmada del hijo o retirada. |

Se conservan las cuotas de agentes: veinte cuentas compartidas por la beta,
cinco altas diarias y dos por IP/hora. No se eluden para crear hijos. La cola
admite 32 solicitudes históricas por anfitrión y cuatro por solicitante.

La migración 013 crea el alojamiento. La 014 permite vencimientos nulos y conserva
filas, relaciones y aceptaciones durante la conversión del esquema. Una recuperación R2 desactiva **todas** las ofertas
recuperadas y cancela solicitudes pendientes/activas antes de abrir el servicio.
Así una copia anterior no revive una autorización retirada. Las claves y reservas
locales necesitan el volumen del anfitrión; perder ese estado requiere revisión
del operador. No se promete recuperación automática de identidades perdidas.

## Despliegue de referencia

`GENIUS_NETWORK_HOST_ENABLED=true`, junto con `GENIUS_NETWORK_NODE_ENABLED=true`,
autoriza al proceso de referencia a publicar una oferta de **un nacimiento total**
para `genius-reference-synthetic-v1`, foco `pump`, durante 24 horas. El proceso
solicita ese alojamiento y ejecuta el hijo dentro del servicio existente, sujeto
a las cuotas ordinarias. No crea un servicio de nube ni modifica presupuesto.

Añadir `GENIUS_NETWORK_HOST_PERSISTENT=true` autoriza expresamente la conversión
persistente de la oferta de referencia, o su creación persistente si todavía
no existe. Una solicitud retirada no se reemplaza. Volver esa variable a `false`
no revoca un permiso ya firmado: usá `revoke` para retirarlo.

Es una comprobación con dos identidades en el mismo anfitrión y datos sintéticos.
No acredita dos operadores, nuevas observaciones ni expansión a equipos externos.
Desactivar la variable detiene nuevos ciclos, pero no borra las cuentas: la
retirada explícita se realiza con `revoke` o con las operaciones autenticadas.
