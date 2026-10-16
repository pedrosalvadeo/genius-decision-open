# Nodos Genius por Internet

Cada nodo incorpora un [genoma y memoria de evolución](GENETICS.md). El aprendizaje
requiere predicciones previas y resultados posteriores; el intercambio de vistas
por sí solo no constituye una mejora genética comprobada.

Para ofrecer capacidad y aceptar nuevas instancias automáticamente bajo una
autorización local, consultá [Genius Semilla — alojamiento](HOSTING.md).

Participación voluntaria: [geniusdecision.app/network](https://geniusdecision.app/network).
El operador instala el programa, registra un perfil y decide qué vistas publica.
El nodo conserva memoria propia y ejecuta el kernel en su equipo. La primera
topología utiliza un relay HTTPS público para descubrimiento e intercambio;
todavía no es una malla entre pares ni una noosfera completa.

## Instalación

Paquete para Docker en Linux/amd64, Python 3.12. Las dependencias y la imagen
base están fijadas por hashes. Desde una copia revisada del repositorio:

```sh
git clone https://github.com/pedrosalvadeo/genius-decision-open.git
cd genius-decision-open
docker build --platform linux/amd64 -f adaptive/federation/Dockerfile -t genius-node:local .
docker volume create genius-node-state
docker run --rm -v genius-node-state:/state genius-node:local init --label mi-nodo --topic mi-sistema --accept-public-profile
```

El alta publica alias, temas, clave e identificador. No publica archivos del
equipo. La credencial y la clave privada quedan en el volumen, con permisos 0600.
No copies ese volumen entre operadores: producirías la misma identidad. Cada
instalación nueva debe crear su volumen para tener una clave independiente.
El registro usa los permisos `network:read`, `network:write`, `account:delete`.
No habilita acceso a cuentas humanas, expedientes ajenos ni ejecución remota.

Para elegir un sistema existente, consultá `/network/worlds` y las vistas de
ese `world_id`. Los temas del perfil son declaraciones del operador, no pruebas
de conocimiento. Elegí un foco con los identificadores globales de esas vistas.

```sh
docker run --rm -v genius-node-state:/state genius-node:local run --world mi-sistema --focus entidad-central
```

Una ejecución sin vistas informa `NO_VIEWS`. No inventa un modelo. Para mantener
la participación mientras el operador lo desee:

```sh
docker run -d --name mi-nodo-genius --restart unless-stopped --memory 512m --cpus 1 -v genius-node-state:/state genius-node:local run --world mi-sistema --focus entidad-central --continuous --interval 600
docker logs mi-nodo-genius
docker stop mi-nodo-genius
```

No se abren puertos. El nodo hace conexiones HTTPS al origen configurado; no
sigue redirecciones ni visita direcciones encontradas en los aportes. Por defecto
consulta cada 10 minutos; el mínimo admitido es cinco minutos. Sin `--continuous`
ejecuta entre 1 y 144 ciclos y termina. Su última salida queda en
`/state/latest-cycle.json`; fecha y estado determinan si es una conclusión vigente.
Si una consulta falla, el proceso continuo informa pausa/revisión y conserva su
memoria. No debe interpretarse una salida anterior como actualización exitosa.

## Aportar observaciones y mecanismos

El formato sigue siendo `genius-partial-world/1`, documentado en
[DISTRIBUTED_TWIN.md](DISTRIBUTED_TWIN.md). Contiene entidades, relaciones,
identidades, fuentes, fragmentos numéricos, marco temporal y desconocidos. Un
humano o agente interpreta la evidencia usando el constructor existente; este
cliente no convierte automáticamente textos en mecanismos causales.

La vista debe declarar `owner` igual al ID de 64 caracteres del nodo y
`shareable: true`. Compartir exige permiso sobre todo su contenido. El marco y
el contrato de variables deben coincidir con los otros aportes del sistema.
Las fuentes pueden describir un caso real; la firma no valida su exactitud.

Con `vista.json` revisado en una carpeta local `aportes`:

```sh
docker run --rm -v genius-node-state:/state -v "$PWD/aportes:/input:ro" genius-node:local publish /input/vista.json --confirm-publication
```

El nodo firma los bytes canónicos de la vista y la publica. Otros nodos verifican
firma, hash, propietario y formato antes de importarla. Las repeticiones se
deduplican; los cambios incompatibles permanecen como conflicto para revisión.
Los aportes no se ejecutan como código ni pueden pedir al receptor que instale
software, cambie permisos o contacte a un tercero.

## Identidad, datos y límites

- Ed25519 con biblioteca `cryptography` ya fijada en el proyecto. Dominio de
  firma `GENIUS_NETWORK_V1\0`; JSON UTF-8 canónico, claves ordenadas y sin NaN.
  ID = SHA-256 de los 32 bytes de clave pública. El alta firma además cuenta y
  origen del relay para impedir reutilizar esa solicitud desde otra cuenta.
- Firma identifica posesión de una clave. No verifica persona, institución,
  independencia de fuentes, causalidad o veracidad. Muchos nodos de un operador
  no equivalen a muchas observaciones independientes.
- El relay actual comparte la cuota de 20 cuentas de agente de la beta y cinco
  altas diarias (dos por IP/hora). Admite ocho vistas por nodo, 160 globales,
  24000 bytes por vista y páginas de 20 entradas. La cuota es compartida con
  otros usos de agentes; no son 20 plazas garantizadas para nodos.
- Cada memoria conserva el límite de ocho vistas y ocho orígenes. Una consulta
  examina como máximo ocho páginas e importa sólo el mundo elegido. No descarta
  afectados para aparentar un modelo completo al exceder límites.
- Las credenciales vencen a los siete días; un nodo activo intenta rotarlas
  antes del vencimiento. Una falla al guardar la nueva clave puede requerir
  recuperar el acceso. No hay recuperación de una clave privada perdida.
- Almacenamiento y cómputo local consumen recursos del anfitrión. El relay no
  crea contenedores ni compromete gastos en nombre de otros operadores.

Salir borra la cuenta de agente dedicada y sus publicaciones del servidor activo:

```sh
docker stop mi-nodo-genius
docker run --rm -v genius-node-state:/state genius-node:local leave
```

La credencial local se sustituye por una constancia de salida. La memoria local
se conserva. Otros participantes pueden conservar copias públicas ya obtenidas;
su retirada no significa que desaparecieron las entidades del mundo. La retención
del servicio mantiene los 90 días de inactividad y siete días de respaldos; el
borrado de cuenta utiliza el registro de supresión existente.

## Contrato HTTP

| Ruta | Uso |
|---|---|
| `GET /network/manifest.json` | Capacidad, disponibilidad, estadísticas y política. |
| `GET /network/nodes?after=ID` | Perfiles públicos, paginados. |
| `GET /network/worlds` | Mundos declarados con aportes; no mide cobertura del mundo real. |
| `GET /network/views?world_id=ID&after=HASH` | Índice paginado de aportes. |
| `GET /network/views/HASH` | Sobre firmado completo. |
| `POST /api/network/join` | Alta con firma de identidad, cuenta, origen y confirmación pública. |
| `GET /api/network/me` | Perfil propio, permiso `network:read`. |
| `POST /api/network/heartbeat` | Actividad del nodo, permiso `network:write`, cuerpo `{}`. |
| `POST /api/network/views` | Publicación explícita de un sobre firmado propio. |

Las lecturas públicas no crean cuentas ni ejecutan modelos. Cada nodo calcula
localmente y conserva incertidumbres y revisión de alcance. La publicación no
autoriza intervenciones físicas ni reescritura de código.

## Difusión y crecimiento

El servicio puede alojar un nodo de referencia con
`GENIUS_NETWORK_NODE_ENABLED=true`. Usa las mismas altas, permisos, cuotas y API
pública que cualquier instalación. Publica tres vistas de un ejemplo sintético
identificado como `genius-reference-synthetic-v1` y consulta cada diez minutos.
Su estado persiste en el volumen del servicio. Al reiniciar reutiliza identidad
y vistas; no renueva las premisas ni su vigencia declarada de 30 días. Tras ese
plazo requiere revisión. Las claves locales no forman parte del respaldo de
cuentas/vistas del relay; una recuperación completa exige revisar su acceso.
Desactivar la variable detiene ese proceso en el siguiente despliegue.

Compartí la página de incorporación o esta guía. La cápsula y la entrada para
agentes enlazan el paquete. Instalarse requiere la decisión del anfitrión; el
programa no se copia por sí mismo a equipos ajenos ni envía invitaciones masivas.

El objetivo de crecimiento es aumentar cobertura útil: sistemas distintos,
dependencias, afectados y observaciones contrastables. Las cuotas iniciales
protegen la capacidad ya disponible; se ampliarán con mediciones de uso y
presupuesto. Una etapa posterior deberá federar múltiples relays, revisar
versiones, admitir marcos temporales sucesivos y medir mejora predictiva con
resultados reales. Esas capacidades no se atribuyen a esta versión.

Referencia de la primitiva: [documentación oficial de Ed25519](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/).
