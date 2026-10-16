# Organismos Genius frente a observaciones reales

## Experiencia inicial

Dos observadores independientes en identidad y memoria, sobre el mismo anfitrión:

| Organismo | Entorno observado | Fuente | Ritmo |
|---|---|---|---|
| SAME | Estación Mendoza / El Plumerillo | METAR público de Aviation Weather Center | Una consulta por hora |
| SAMM | Estación Malargüe | METAR público de Aviation Weather Center | Una consulta por hora |

No están instalados en los aeropuertos: observan sus reportes desde un servidor.
Tampoco representan dos operadores independientes. Cada uno usa su propia cuenta,
clave, memoria y genoma; sus contextos y resultados se mantienen separados.

La API real respondió el 16/10/2026. La captura y el arranque aislado reproducible
están en `beta/evidence/2026-10-16-living-habitats/`. La captura prueba acceso a
observaciones reales; no prueba todavía mejora prospectiva en producción.

## Qué hacen y qué entregan

1. Consumen únicamente temperatura de una estación expresamente habilitada.
2. Conservan fecha de observación, informe METAR, origen y hash. La temperatura
   se representa exactamente como centikelvin: `(Celsius + 273.15) × 100`.
3. Usan hasta 18 horas de reportes disponibles como historia inicial; esto no
   cuenta como resultados futuros ni valida retrospectivamente sus genes.
4. Congelan una predicción usando el reloj posterior a la recepción de datos.
   Esperan el primer reporte observado después de esa predicción, dentro de dos
   horas. Una falta de reporte se registra como ausencia, no como cero.
5. Comparan las variantes de estimador y ventana ya definidas en GENETICS.md.
   Cuatro resultados nominan una variante; otros cuatro la confirman. El kernel
   verifica la comparación antes de adoptar un cambio. Si no mejora, no cambia.
6. Archivan el experimento completo, conservan el genoma y comienzan otro.
   El historial, las predicciones y los errores son resultados observables.

El organismo no controla el clima ni recomienda operaciones de vuelo. La mejora
se refiere al error de una tarea de predicción, no al bienestar ni a PVS. Los datos
son observaciones reportadas por una fuente pública, no sensores propios ni una
verificación independiente de su exactitud. Genius no está afiliado a NOAA/NWS.

## Seguirlos

- Página pública: `https://geniusdecision.app/organisms`.
- Estado para personas y agentes: `https://geniusdecision.app/network/organisms.json`.
- Directorio de identidades: `https://geniusdecision.app/network/nodes`.

El informe muestra la última medición, predicción, error posterior, resultados
puntuados y mejoras confirmadas. Si lleva más de tres horas sin actualizarse,
se marca como antiguo; una predicción anterior no demuestra actividad actual.
Las claves, cuentas privadas y rutas locales no se publican.

## Continuidad, memoria y control

El permiso no tiene vencimiento temporal. Pausa, revocación, credenciales,
retención de cuentas y disponibilidad del anfitrión siguen aplicándose. Un
controlador en reposo mantiene su cuenta por las operaciones normales, sin
consultar la fuente ni hacer nuevas predicciones. No se reemplaza automáticamente
una cuenta inaccesible mientras se conserva su estado local.

La memoria de trabajo mantiene sus límites de 128 observaciones y 32 pronósticos.
Sólo se liberan experimentos terminados, después de guardar todas sus predicciones,
resultados y evidencia referenciada. Se conservan 64 archivos completos de historia
por organismo y contadores acumulados con una cadena de hashes. Los archivos más
antiguos se retiran al superar ese límite: no se promete auditoría ilimitada.
La memoria reciente retiene al menos los 48 registros más nuevos y todas las
versiones de sus eventos, además de evidencia de pronósticos aún guardados.

Se mantiene el límite de generación 32. Llegar a ese límite requiere revisión de
la política experimental; no crea una cuenta ni otro organismo. Los conflictos de
fuente también requieren revisión. La fuente se consulta como máximo una vez por
hora y los errores 403/404 suspenden consultas hasta revisar el acceso.

Las identidades, memorias y archivos están en el volumen local del operador.
Necesitan su propia estrategia de respaldo: no forman parte del backup R2 de la
base transaccional de la beta. Antes de recuperar un volumen perdido, el operador
debe deshabilitar el inicio automático y revisar qué identidades puede restaurar.

## Instalarlo en otro lugar autorizado

El paquete funciona en Linux con Docker, almacenamiento persistente y salida
HTTPS. Sirven un equipo propio, una Raspberry Pi compatible o un VPS/container de
un anfitrión que acepte participar. No requiere puertos entrantes ni acceso de
administración a otros equipos.

Desde una copia del repositorio, construir la imagen y crear el volumen:

```sh
docker build -f adaptive/federation/Dockerfile -t genius-node:local .
docker volume create genius-mendoza
```

Autorizar y ejecutar un observador de SAME (cambiar a SAMM para Malargüe):

```sh
docker run -d --name genius-observador --restart unless-stopped --memory 768m --cpus 1 -v genius-mendoza:/state --entrypoint python genius-node:local -m federation.habitat --state /state --station SAME --hub https://geniusdecision.app --allow-observation --continuous
```

Ver el informe y detener el proceso:

```sh
docker logs --tail 10 genius-observador
docker stop -t 40 genius-observador
```

Guardar reposo local o revocar la cuenta (con el proceso detenido):

```sh
docker run --rm -v genius-mendoza:/state --entrypoint python genius-node:local -m federation.habitat --state /state --station SAME --control pause
docker run --rm -v genius-mendoza:/state --entrypoint python genius-node:local -m federation.habitat --state /state --station SAME --control resume
docker run --rm -v genius-mendoza:/state --entrypoint python genius-node:local -m federation.habitat --state /state --station SAME --control revoke
```

Después de `pause` o `resume`, reiniciar el contenedor para que mantenga o reanude
su actividad. Una revocación no se reactiva. El alta comparte las cuotas existentes
de la beta; no reserva capacidad ni obtiene permisos de reproducción.

## Despliegue en la cuenta actual

`GENIUS_LIVING_HABITATS=SAME,SAMM` habilita dos observadores lógicos en el servicio
Railway ya existente. Sus directorios son `living-habitats/SAME` y
`living-habitats/SAMM` bajo `GENIUS_DATA_DIR`. No se crean servicios ni volúmenes
adicionales. El supervisor sólo les pasa las variables necesarias para el nodo;
no les entrega credenciales de administración o respaldo.

Quitar esa variable detiene el proceso, pero no revoca cuentas. La suspensión
global de la beta impide el heartbeat previo a cada consulta y pausa observación.

## Otros espacios evaluados

La búsqueda mundial actualizada, con regiones, costos, condiciones y una propuesta
para BOINC Central, está en [GLOBAL_HABITATS.md](GLOBAL_HABITATS.md). La experiencia
inicial en Mendoza/Malargüe no restringe la ubicación de futuros anfitriones.

| Espacio | Encaje de esta versión |
|---|---|
| Railway ya contratado | Primer hábitat continuo; mismo servicio y volumen. |
| Linux/Docker de un anfitrión voluntario | Paquete instalable anterior; capacidad y presupuesto del operador. |
| Hugging Face Spaces | Admite Docker, pero el almacenamiento por defecto no es persistente y puede dormir; requiere resolver continuidad y condiciones de su plan. No se ha instalado allí. |
| Cloudflare Workers | Adecuado para un futuro sensor ligero. El trabajador Python y el kernel nativo actuales requieren una adaptación; no se presenta como alojamiento ya disponible del organismo completo. |

Fuentes oficiales consultadas el 16/10/2026:

- https://aviationweather.gov/data/api/
- https://www.weather.gov/disclaimer
- https://huggingface.co/docs/hub/en/spaces-overview
- https://huggingface.co/docs/huggingface_hub/en/guides/manage-spaces
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/workers/platform/pricing/

No se han contactado terceros ni instalado procesos en recursos ajenos.
