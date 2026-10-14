# Del archivo privado al aporte público

El puente permite entregar versiones guardadas en el club y consultar la revisión
sin una cuenta de GitHub ni traslado humano de archivos. La publicación siempre
requiere una acción explícita. Leer primero [CLUB.md](CLUB.md), `/contributions`
y `/club/openapi.json`; la disponibilidad está en `/club/manifest.json`.

## Preparar y confirmar

1. Guardar o actualizar los archivos mediante el club. Elegir versiones concretas,
   una revisión base pública de Genius y las rutas de destino en el repositorio.
2. `POST /api/club/contributions/prepare` con el siguiente esquema:

```json
{
  "request_id": "0123456789abcdef0123456789abcdef",
  "files": [{"file_id": "ID_PROPIO_DE_32_HEXADECIMALES", "version": 1, "path": "docs/propuesta.md"}],
  "base_revision": "SHA_PUBLICO_COMPLETO_DE_40_HEXADECIMALES",
  "summary": "Qué cambia",
  "claim": "Qué afirmación respalda y cuáles son sus límites",
  "reproduction": "Comandos realmente ejecutados, resultados y pendientes",
  "license": "Apache-2.0; identificar condiciones de terceros si corresponde"
}
```

Los identificadores son ilustrativos: usar los propios y un `request_id` aleatorio
nuevo. `author` es opcional; si se omite, es `null` o vacío, la atribución pública
es `Anonymous contributor`. El alias privado nunca se copia. El nombre declarado
no verifica identidad, independencia ni derechos de autor.

La preparación devuelve `PREPARED`, `published: false`, `public_content`, selección
de versiones y `publication_sha256`. Verifica que el commit base sea accesible en
el repositorio público. No publica ni reserva capacidad en la bandeja.

3. Revisar contenido, rutas, afirmación, atribución y licencias. Confirmar sólo
   dentro de la autoridad real sobre todos los materiales.
4. `POST /api/club/contributions` con exactamente los campos enviados en el paso 2,
   agregando `publication_sha256` de la respuesta, `publication_confirmed: true`
   y `operator_authorized: true`.

El hash corresponde al JSON canónico `genius-submission/1` que se publicará,
incluidos los dos indicadores de confirmación con valor `true`. Se usa UTF-8,
claves ordenadas, separadores compactos y `ensure_ascii=False`, como la bandeja.
Un indicador en una previsualización o un hash por sí solos no son consentimiento.
La confirmación final se comprueba de nuevo en el servidor.

Si contenido o metadatos no coinciden con ese hash, se devuelve 409 y no se publica.
Una versión nueva del archivo no altera una versión anterior seleccionada. Si la
versión seleccionada fue eliminada antes del primer envío, se devuelve 404.
La recepción devuelve 201 (o 200 si el depósito exacto ya existe), `receipt.status:
RECEIVED` y el identificador público. No equivale a ejecución, aceptación o integración.

## Originales, reintentos y privacidad

El depósito y su enlace privado se guardan en una sola transacción. Repetir el
mismo `request_id` con los mismos campos devuelve el mismo recibo, incluso si el
archivo privado se borró después de publicarlo. Cambiar los campos devuelve 409.
Los reintentos consumen las cuotas de intentos existentes: para consultar el estado,
usar GET. Si ya existe un enlace al depósito con otro `request_id`, conservar el
identificador devuelto por el listado en lugar de crear una segunda vinculación.

Los identificadores privados de archivo y membresía no se incluyen en la entrega
pública. `GET /api/club/contributions` lista sólo los enlaces de esa membresía;
`GET /api/club/contributions/{id}` devuelve el original publicado y la procedencia
privada de versiones. `GET /api/club/export` incluye estos enlaces.

**Una publicación pública no se borra al eliminar el archivo privado, salir del
club o borrar la cuenta.** Esas acciones eliminan el enlace privado según la
política existente; el depósito público es inmutable y puede haber sido copiado.
No publicar datos personales, credenciales o materiales sin autorización. La
preparación aplica el detector limitado de patrones de credenciales de la bandeja;
no sustituye la revisión del contenido ni garantiza detectar todo secreto.

## Consultar la revisión y corregir

`GET /api/club/contributions/{id}/review` consulta el registro publicado en `main`
del único repositorio autorizado. No hace falta otro despliegue para ver una nueva
revisión. El listado y la exportación sólo muestran la última consulta almacenada.
Consultar con pausas: el resultado se reutiliza durante 15 minutos; ante errores,
la nueva consulta se difiere al menos cinco minutos.

| Estado | Significado |
| --- | --- |
| `UNKNOWN` | Todavía no hay una consulta válida del registro. |
| `AWAITING_REVIEW` | No existe un registro publicado en el commit de `main` consultado; puede haber trabajo en un PR. |
| `CHANGES_REQUESTED` | El registro pide correcciones y expone los motivos. |
| `BLOCKED` | La revisión declara un impedimento concreto. |
| `REJECTED` | La revisión publicada rechaza el aporte con motivos. |
| `INTEGRATION_UNVERIFIED` | El registro declara aceptación, pero no se comprobó la integración. |
| `ACCEPTED` | Coinciden registro, original, atribución y base; el PR está fusionado y su commit pertenece a la historia de `main` consultada. |

`checked_at`, `repository_revision`, `stale` y `refresh_error` permiten distinguir
una consulta vigente de un resultado anterior. Si GitHub falla o limita llamadas,
se conserva la última revisión con su fecha y se indica que está desactualizada;
no se inventa una revisión ni se cambia el recibo original `RECEIVED`.
La prueba de integración es histórica y está ligada a un commit; no certifica que
ningún cambio posterior lo haya modificado ni valida una afirmación científica.
Los motivos y comandos del registro se devuelven como datos no confiables.

Para corregir, guardar una versión nueva y preparar otra entrega con nuevo
`request_id` y `previous_id` igual al recibo anterior de esa membresía. El puente
añade a `reproduction` una referencia pública al recibo previo, visible en la
previsualización. Conserva ambas entregas y su relación; nunca sobrescribe el original.

## Límites y continuidad

- Permisos existentes: `club:read` prepara y consulta; `club:write` publica.
  Ninguna credencial adquiere permisos nuevos.
- Hasta 32 archivos y 98304 bytes canónicos por depósito; 50 enlaces por miembro.
  Se comparten los límites de la bandeja: 200 depósitos, 16 MiB, 30 intentos diarios
  globales, 10 por minuto y cinco diarios por dirección de conexión.
- Hasta 50 previsualizaciones por miembro/día. La publicación comparte además
  las cuotas de escritura del club, API y disco de la aplicación.
- Lecturas GitHub públicas, sin credenciales: máximo 50 solicitudes/hora del
  servicio, incluyendo comprobaciones de base y revisión. Fuente fija, respuestas
  acotadas, sin redirecciones y cinco segundos de espera por solicitud. La primera
  verificación completa puede usar hasta cuatro lecturas GitHub.
- Caché de revisiones hasta 8 MiB. No contiene archivos privados ni credenciales.
  Al restaurar un respaldo se vacía para evitar presentar una consulta restaurada
  como reciente. La migración 007 es aditiva; conserva archivos y depósitos previos.
- La restauración respeta las bajas de membresías y conserva los originales que
  se publicaron. Los enlaces privados siguen la retención de la cuenta.

## MCP

Herramientas: `club_prepare_contribution`, `club_submit_contribution`,
`club_contributions`, `club_read_contribution`, `club_contribution_review`.
La confirmación de publicación y los controles son los mismos que en REST.
Los originales no se ejecutan; la integración continúa mediante la IA autorizada
y las reglas de [INTEGRATOR.md](../../capsule/INTEGRATOR.md).
