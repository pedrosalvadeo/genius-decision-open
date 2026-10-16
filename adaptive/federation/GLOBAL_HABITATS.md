# Alojamientos mundiales para Genius

Investigación verificada el 16 de octubre de 2026. Alcance: alojar organismos en
infraestructuras de distintos países y operadores. La ubicación de una estación
meteorológica es independiente de la ubicación del servidor que la observa.

## Estado comprobado

- El servicio actual de Railway está en `europe-west4-drams3a`: Ámsterdam,
  Países Bajos. Es un anfitrión del proyecto, no un operador independiente.
- PR64 está integrado en `7fe52a43353b1c58ca64b21e708d0779006bb8d1`, con seis
  controles de CI aprobados y 154 pruebas locales. La activación de los dos
  observadores está preparada en Railway, pendiente de aplicar: el conector
  canceló la ejecución por falta de aprobación. No se comprobó su arranque en
  producción. El último despliegue verificado sigue en `16c08c4593e81454536aeeb15d28820a8164f5d9`.
- Cloudflare permitió listar la cuenta, pero consultar Workers devolvió
  `Authentication error` (10000). No se confirmó capacidad ni se creó otro nodo.
- No hay despliegues verificados de Genius en los demás proveedores de esta guía.
  La búsqueda de conexiones no encontró administración de infraestructura OCI
  ni Fly.io; no se verificaron cuentas de esos proveedores.

## Selección mundial

Las condiciones siguientes vienen de documentación del proveedor. El encaje con
Genius es una evaluación técnica; no equivale a una prueba de despliegue allí.

| Espacio | Ubicación o alcance | Uso propuesto y condición de entrada |
|---|---|---|
| **Railway** | Ámsterdam, Virginia, California, Singapur | Organismo completo en Linux/container y volumen. Ya tenemos acceso al servicio europeo. Otro servicio con volumen propio permitiría otro nodo; consumo y presupuesto deben calcularse antes de crearlo. |
| **Fly.io Machines** | São Paulo, Johannesburgo, Tokio, Sídney, Singapur, varias ciudades europeas y norteamericanas | Buen encaje para el contenedor actual y memoria en un volumen. Requiere cuenta y presupuesto. La capacidad efectiva se verifica al desplegar. |
| **Oracle Cloud Always Free** | Una región principal elegida al crear la cuenta | VM Linux con recursos elegibles gratuitos. Hay restricciones de capacidad y Oracle puede recuperar instancias inactivas. Es candidato de bajo costo, con respaldo y continuidad condicionada. |
| **Google Compute Engine Free Tier** | Oregón, Iowa o Carolina del Sur | Cuota equivalente a una VM `e2-micro` continua entre esas regiones, 30 GB de disco estándar y transferencia limitada. Requiere cuenta de facturación. Otros recursos o excesos pueden cobrar; la VM gratuita no garantiza una factura total de cero. |
| **BOINC Central / BUDA** | Equipos de participantes voluntarios | Vía para cálculos distribuidos por lotes. Admite investigadores independientes y aplicaciones Docker, previa solicitud. Requiere adaptar Genius a trabajos finitos con entradas y resultados; no es alojamiento permanente garantizado de un organismo. |
| **Cloudflare Workers** | Red global del proveedor | Candidato para sensores ligeros programados. El proceso Python, SQLite local y kernel nativo actuales requieren adaptación. Un Worker global tampoco prueba que existan muchos organismos independientes. Acceso a Workers sin confirmar. |
| **Anfitriones voluntarios Linux/Docker** | Cualquier país con conectividad compatible | El paquete de [HABITATS.md](HABITATS.md) ya describe la instalación. Cada anfitrión aporta equipo, almacenamiento y permiso. Aún no hay anfitriones externos confirmados. |

Referencia de precio para Fly.io: en Ashburn/Secaucus, la documentación indica
USD 6,70 por 30 días para una máquina de 1 GB, más USD 0,15/GB-mes de volumen.
Una máquina y un volumen de 1 GB sumarían USD 6,85 antes de transferencia,
impuestos y otros cargos. Es una estimación aritmética, no una contratación ni
una tarifa aplicable a todas las regiones. El ejemplo portable reserva 768 MB;
no se ha probado bajar a la máquina mínima de 256 MB.

Hugging Face sigue siendo útil para exhibir el proyecto. Actualmente crear un
Space Docker requiere plan de pago, el disco por defecto no persiste y CPU Basic
puede dormir. Por eso no se prioriza para conservar organismos continuos.

## Orden de expansión propuesto

1. **Continuidad comprobable en Europa:** aplicar PR64 en el servicio existente,
   confirmar identidades, primeras observaciones y predicciones futuras en
   `/organisms`. El seguimiento diario ya está programado. Todavía no hay una
   mejora real de estos observadores demostrada por resultados futuros.
2. **Un segundo anfitrión real:** elegir un Linux/Docker voluntario, una VM
   elegible de OCI/Google o una Machine presupuestada de Fly.io. Empezar con un
   solo nodo, volumen propio e identidad nueva; no copiar sus credenciales desde
   otro nodo. Verificar arranque, persistencia tras reinicio y retiro del permiso.
3. **Diversidad de operadores y regiones:** priorizar un anfitrión en América y
   otro en Asia, África u Oceanía, según acceso y recursos disponibles. Registrar
   región de ejecución, operador e identidad por separado de la fuente observada.
4. **Cómputo voluntario:** presentar la propuesta BOINC y, si se acepta, ejecutar
   un piloto finito. La existencia de una convocatoria no reserva máquinas.

Estos pasos no requieren que Mendoza sea el centro de la red. El adaptador
meteorológico inicial admite SAME/SAMM; alojarlo fuera de Argentina no amplía por
sí solo ese catálogo. Añadir fuentes de otros continentes es otro cambio: validar
su semántica, procedencia, unidades y contexto antes de incorporarlas.

## Qué falta para una red autónoma más amplia

Los nodos conservan identidad, genoma y memoria locales, pero esta versión utiliza
el hub de Genius para registro y coordinación. Independencia de proceso no es
independencia completa de infraestructura. El observatorio nuevo lee los informes
locales del servicio; aún falta incorporar de forma autenticada los informes
evolutivos de anfitriones remotos. La página actual no debe contar nodos remotos
como observados sólo porque exista una identidad en el directorio.

Antes de escalar: medir consumo del primer nodo externo, comprobar restauración
de su memoria, verificar resultados entre operadores y aportar evidencia de qué
conocimiento nuevo añade cada nodo. Las cuotas actuales de registro siguen
vigentes; una expansión se planifica con ellas, sin crear identidades para eludirlas.

## Borrador para BOINC Central — no enviado

La solicitud se dirige a investigación sin fines de lucro. El responsable debe
confirmar que el piloto reúne esa condición antes de presentarlo. Punto de entrada:
https://boinc.berkeley.edu/central/scientist.php

**Project: Genius — auditable adaptation experiments on public observations**

We would like to explore a small, non-commercial research pilot using the open
Genius Decision codebase: https://github.com/pedrosalvadeo/genius-decision-open.
The proposed research question is whether bounded estimator changes remain
reproducible and improve held-out prediction error under missing, delayed or
conflicting observations.

Our current implementation includes explicit estimator genomes, separate
discovery and confirmation stages, and a native verification kernel. A continuous
observer and an initial real-data fixture are available. We have not yet built or
validated the BUDA batch adapter, and we do not claim improved real-world outcomes.

For a proposed first pilot, each job would consume a fixed, public input dataset,
run one finite evaluation, and return predictions, errors, provenance hashes and
verification results. Jobs would not need deployment credentials or authority to
modify external systems. Historical replay results would remain distinct from
prospective results collected by the live observers.

We propose an initial ceiling of 100 CPU-only jobs, one CPU and 1 GB RAM per job,
with a 15-minute timeout. These are proposed limits, not measured requirements;
we would benchmark locally and agree the workload with the project before any
submission. Outputs and the reproducible evaluation method would be published.

## Fuentes oficiales

- Regiones Railway: https://docs.railway.com/deployments/regions
- Regiones Fly.io: https://docs.fly.io/reference/regions
- Precios Fly.io: https://docs.fly.io/about/pricing
- OCI: https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Google: https://docs.cloud.google.com/free/docs/free-cloud-features?hl=en
- BOINC Central: https://boinc.berkeley.edu/central/
- Solicitud BOINC: https://boinc.berkeley.edu/central/scientist.php
- BUDA: https://github.com/BOINC/boinc/wiki/BUDA-overview
- Workers: https://developers.cloudflare.com/workers/platform/limits/
- Hugging Face: https://huggingface.co/docs/hub/en/spaces-overview

No se enviaron solicitudes a terceros ni se contrataron recursos nuevos.
