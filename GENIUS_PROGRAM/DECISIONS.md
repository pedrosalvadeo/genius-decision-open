# Estado vigente — decisiones cotidianas guiadas, 06/10/2026

Mandato nuevo de Pedro: avanzar en traducción de problemas, perfiles admitidos y validación real, conservando Plan Maestro v2 y R0–R3. Implementado **CHOICE_DECLARED_V1**, código **7c9348e2cb9fdbf4186f9a0767ac2211de8ad71a**: guía de cuatro pasos, revisión/confirmación de modelo, comparación con el Kernel FP1 recibido, recomendación condicional, alternativas, límites, sacrificios, desconocidos, versiones y feedback; API/MCP `prepare_decision` y `revise_case`.

Alcance: ocio/organización personal de bajo riesgo; 2–8 alternativas, 1–5 criterios explícitos. La narrativa aporta contexto, no se interpreta automáticamente en la web. No LLM externo, búsqueda de datos, probabilidad inventada ni admisión empírica de CAG/PVS. La compilación declara constantes formales comunes para dimensiones no evaluadas; la recomendación sólo vale para la tabla confirmada. No es un Radar/Solver general. Diseño: `beta/DECLARED_CHOICE_DESIGN.md`.

**Preparado y probado:** 92 pruebas locales, 14 nuevas; navegador escritorio/móvil PASS; cliente MCP oficial PASS; fuentes recibidas 13/79 intactas. CI **37446221959**, verify **112211582416 SUCCESS**, incluidos navegador, Docker, HTTPS, MCP y recuperación. Recomputación formal y pruebas de autor; no se afirma auditoría externa nueva.

**Publicado:** MCP y demo anteriores ya están publicados: deployment **0e68fe1a-3228-4936-9f67-2ef27d3d6ca9 SUCCESS**, fuente efectiva **0cad72775d6676a423f7d0d85363b487f6068b4e**. El nuevo perfil cotidiano todavía no está publicado: patch **1353ae55-c12e-4440-847c-3e76160b3e72 STAGED**, un cambio no destructivo de código, pendiente de **Apply manual de Pedro**. No se llamó accept-deploy.

**Evidencia real:** no se incorporaron casos reales admitidos en este ciclo. **F6A ABIERTA / G6A PENDIENTE**. Protocolo de campo preparado en `beta/DECLARED_CHOICE_FIELD_PROTOCOL.md`; feedback percibido no acredita utilidad ni comprensión. Sin migración, proveedor, secreto, plan o recurso nuevo; se mantienen presupuestos/cuotas/retención.

Checkpoint: `beta/DECLARED_CHOICE_CHECKPOINT.md`; evidencia: `beta/evidence/declared_choice_prepared_2026-10-06.json`; próxima acción: recibir Apply y verificar producción. La falta de participantes no detiene ingeniería ni autoriza inventar demanda o evidencia.

Decisiones de producto/técnica: ampliar mediante perfil explícito y versionado; reutilizar el núcleo inmutable; no sustituir Genius por una suma ponderada ni convertir constantes de codificación en CAG/PVS reales. Frontera y selección separadas, preferencias expresas, empates conservados, unidades no sumadas, null desconocido. La confirmación liga todos los campos mediante hash pero no prueba consentimiento humano. Formato nuevo genius-declared-choice/1, sin simular RC01. Fuente/norma modificada requiere nueva revisión. Dependencias de LLM/casos reales no bloquean la ruta guiada.


---

## Registro histórico conservado; el estado vigente figura arriba

## Decisiones — acceso para lectores y clientes MCP, 06/10/2026 ART

Incorporar el feedback atribuido a Claude y Gemini como orientación de producto: un lector GET necesita un resultado público ya ejecutado, y un cliente MCP necesita herramientas conectadas explícitamente. No tomar los textos idénticos como dos diagnósticos independientes de un bloqueo Cloudflare. Conservar robots.txt con Disallow:/api/ y autenticación privada; servir sólo fixtures sintéticos públicos fuera de /api/.

Agregar MCP al mismo servicio, sin proveedor, puerto público, base o motor duplicados. Puente de rutas fijas al gate REST: nunca proxy arbitrario, cookies humanas, sesiones de transporte como credencial ni token en argumentos. tools/list filtra por scopes y cada operación vuelve a exigirlos. Las claves humanas completas siguen fuera de MCP.

La demo MCP conserva la credencial sólo en memoria del servidor, espera hasta 10 segundos y borra el espacio temporal antes de responder. Si falla el borrado duradero informa error y conserva expiración/limpieza existente; no inventar limpieza exitosa. Trabajo privado persistente: run_case devuelve id y get_job consulta. No emitir claves nuevas al modelo ni fingir OAuth/Tasks.

Mantener cuotas de trabajo compartidas; agregar límite MCP de 2000 llamadas/día, 300/minuto globales y 60/minuto por dirección real de conexión. Contador global diario antes del contador IP para acotar su cardinalidad; no confiar en X-Forwarded-For. GENIUS_MCP_ENABLED=false pausa sólo MCP; GENIUS_AGENT_ACCESS_ENABLED=false conserva la contención de nuevas operaciones automáticas. Sin rollback al gate anterior que desconoce scopes.

Añadir cliente oficial MCP 2.3.0 con 28 ruedas fijadas por hash únicamente al entorno de prueba/CI; imagen productiva mantiene requirements.lock. Pruebas cubren versiones moderna y legacy, motor real, desconocidos, aislamiento, límites, vencimiento, denegaciones, limpieza y errores. Firma de imagen/recuperación se verifica en CI. Preservar la modalidad Apply manual; documentación de continuidad no dispara un nuevo despliegue.

---

## Historial conservado; prevalece la actualización anterior

## Decisión de recepción — acceso directo publicado, 06/10/2026 ART

Recibir el Apply confirmado por Pedro mediante lectura de Railway y ejecución sintética mínima: una demo hours-known, token sólo en memoria, borrado de su espacio y comprobación 401 posterior. No crear una segunda identidad ni usar cuentas/contraseñas de Pedro para ampliar pruebas sin necesidad.

Registrar como fuente efectiva 331a0717167d1ed0c5b9073695563eb3a99ff93c, aunque source.commitSha muestra 5c55716dbd838be19321bd1e1a07e0874fa2baef: las 22 diferencias son documentales y se comprobó identidad ejecutable. Deployment c930af77-2653-4bfd-abe9-db01ef5f12b1 SUCCESS; patch consumido. Cerrar el pendiente de Apply y conservar recibos históricos como historia, no estado actual.

Conservar formulario humano, aislamiento de identidades, scopes/expiración de máquina, política exclusiva de datos sintéticos o no personales y límites vigentes. No afirmar consentimiento humano, compatibilidad con todas las IAs, MCP/OAuth ni validación F6A por esta recepción. Publicar guía y manifiesto como puntos de entrada para clientes HTTP.

Contención de incidentes: GENIUS_AGENT_ACCESS_ENABLED=false conservando runtime/esquema nuevos y operaciones autorizadas de lectura/cancelación/borrado. No rollback ciego al gate antiguo ni restauración rutinaria de la base. Esta recepción no amplía recursos, presupuesto o proveedores. Evidencia: beta/evidence/direct_agent_access_accepted_2026-10-06.json.

---

## Historial conservado; prevalece la actualización anterior

## Decisiones — acceso directo autorizado, 06/10/2026 ART

Pedro autorizó conservar el formulario humano y agregar el acceso directo. Separar cuentas humanas, espacios automáticos persistentes y demos efímeras. El alta técnica no pide ni inventa aceptación humana, edad, identidad, correo o contraseña. Admite sólo datos sintéticos o no personales; la declaración del cliente no autentica la fuente ni detecta todos los datos personales.

Reutilizar motor, almacenamiento, worker y controles actuales. Nueva migración aditiva 003, scopes en tabla separada y autorización fail-closed de credenciales de máquina. Rotación con reducción de permisos; prueba concurrente evita duplicar una clave. Las claves humanas anteriores no cambian. Demos no renovables con payload exclusivamente del catálogo sintético recibido.

Reservar cuotas globales antes de contabilizar IP para acotar crecimiento de contadores. No confiar en X-Forwarded-For del cliente. La dirección de conexión puede ser compartida por usuarios o por el proxy; el límite global permanece obligatorio. No ampliar presupuesto automáticamente.

Recuperación offline revisada de esquemas v2/v3 y rechazo de hashes históricos desconocidos. Borrar credenciales y demos expiradas al recuperar. Para contención mantener runtime nuevo y usar kill switch; no rollback automático a autorización antigua.

Publicación por Apply manual conforme a preferencia vigente; recibir SHA efectivo, no inferirlo del pin. Este ciclo no implementa MCP ni OAuth y no cierra F6A.


---

## Historial conservado; prevalece la actualización anterior

## Decisión vigente — puerta para agentes sobre la API existente, 05/10/2026 ART

Reutilizar motor, expedientes, cuotas y autenticación REST. Incorporar un punto público /agents con contrato OpenAPI y guía de texto, y un enlace directo al panel humano de claves. Separar descubrimiento público, autorización humana y operación por Bearer. No imponer al agente el formulario visual ni compartir contraseña.

La versión inicial conserva claves full-account revocables y hace explícito ese límite. No atribuir permisos finos, identidad verificada, OAuth ni MCP a la implementación. Una futura ampliación deberá diseñar y probar delegación y scopes antes de prometer conexión MCP. llms.txt es una ayuda de lectura; no es autenticación ni garantía universal de compatibilidad.

Mantener autenticación, robots /api/, cuotas y controles actuales. No modificar Cloudflare para resolver un rechazo sin evidencia causal. Publicar esta versión mediante el Apply manual acordado y recibir la fuente efectiva después. Los resultados sintéticos no cierran F6A.


---

## Historial conservado; prevalece la actualización anterior

## Estado vigente — corrección publicada y diagnóstico de rastreo, 05/10/2026 ART

**La corrección anterior ya fue aplicada. No hay Apply pendiente.** Railway deployment da52af56-b990-4e70-b2c9-da6bbd02dedb SUCCESS, creado06/10/2026 00:04:21UTC (05/10 21:04ART). Fuente efectiva e9b46ccf0e4771f547e28e2b338223c512d0fc7a, descendiente documental del código9a89f4ecb2dc374a88b0a23c23dd77a9237cdf4a, CI37377285120 SUCCESS. Comparación:24 diferencias documentales, ningún cambio ejecutable; cinco archivos públicos coinciden con el candidato.

Recepción HTTPS: altas abiertas, aviso beta-2026-10-05-v2, configuración pública sin address; health/backupok. Aviso y scripts servidos sin etiqueta ni enlace de datos del domicilio. Mensajes de alias/contraseña corregidos en los archivos publicados; ocho pruebas específicas y CI ya recibidos. No se creó cuenta, no se usó la contraseña de las capturas y no se realizó un nuevo ensayo visual interactivo de esta versión.

Pedro reportó que varias IAs atribuyen su falta de acceso a bloqueo de rastreadores. Lectura Cloudflare: DNS-only (proxied=false); ai_bots_protection/content_bots_protection/crawler_protection y políticas ai_training/ai_search/ai_user=disabled; managedrobots=false. HTTP directo: portada, robots y documentación API devuelven200 sin reto observado. robots.txt contiene únicamente User-agent:* y Disallow:/api/. Tres peticiones desde este entorno con cabeceras de rastreador recibieron200; **no equivalen a pruebas desde redes reales de esos proveedores**.

La herramienta de búsqueda devolvió un error genérico «URL … is not accessible via this tool» para portada/robots/documentación. No informó un códigoHTTP ni una causa comprobable. No afirmar un bloqueo general del sitio, un falso positivo específico, falloDNS o limitación concreta del proveedor. Falta saber qué IA/herramienta y qué URL exacta produjeron el rechazo. No se modificaron DNS, reglas Cloudflare, robots, autenticación ni cabeceras por una causa todavía no demostrada.

Domicilio alternativo de contacto y constancia final de la base siguen bajo seguimiento del responsable. No republicar la dirección retirada ni inventar inscripción aprobada. La decisión previa de avanzar sin constancia permanece. F6A ABIERTA/G6A PENDIENTE; no hay nueva evidencia empírica por este diagnóstico.

Checkpoint: beta/CRAWLER_ACCESS_CHECKPOINT.md. Recibo: beta/evidence/crawler_access_diagnostic_2026-10-05.json. Continuidad: CONTINUATION_PROMPT.md. Las referencias históricas a Apply pendiente de la corrección están sustituidas por esta recepción.


---

## Historial conservado; prevalece la recepción y diagnóstico anteriores


## Historial conservado; prevalece la corrección vigente anterior


## Historial conservado; prevalece el estado vigente anterior


## Historial conservado; prevalece el estado vigente anterior


# Estado vigente — Hobby recibido y aviso preparado, 05/10/2026

Hobby está activo. Se guardaron y releyeron Compute alerta USD 5 / corte USD 10 y Railway Agent corte USD 0, en el workspace existente. La contratación, el pago y la configuración presupuestaria dejan de ser bloqueos; no volver a pedirlos. Recibo: beta/evidence/hobby_active_limits_2026-10-05.json. Checkpoint: beta/HOBBY_BUDGET_CHECKPOINT.md.

El aviso beta-2026-10-05 está implementado en 5b4a725d9deba402ea9d4e0a1e2875a3334ece79: página accesible sin cuenta, proveedores, transferencias expresas, conservación y derechos. CI 37355643607 / verify 111917239528 SUCCESS: 42 pruebas, HTTPS sintético, imagen y guardas. Navegador local no validado por fallo SIGSEGV del binario. Copia revisable: beta/docs/NOTICE_REVIEW.md; ficha administrativa y solicitud consolidada: beta/docs/AAIP_REGISTRATION_BRIEF.md.

Siguen pendientes la recepción de la decisión del responsable sobre el aviso/operación inicial y la acreditación de inscripción o determinación fundada aplicable. Esto viene del relevamiento de PRIVACY previo, no del pago de Hobby. No se ingresó a TAD ni se presume que no exista una constancia anterior. No pedir identidad fiscal o contraseñas en chat. Los trámites identificados son gratuitos.

Producción conserva deployment 0205274c-1d84-4c47-9097-0e00739b5dde y fuente d1b299d43c77268edb498327c429cc5ed352bba0, registro cerrado, R2 activo y autodeploy OFF. Nuevo aviso preparado, todavía no publicado. No hay Apply nuevo. Recibidas las condiciones, preparar versión comprobada y apertura en el mismo servicio, avisando cada confirmación manual de Railway. F6A ABIERTA / G6A PENDIENTE: preparación técnica y CI no son evidencia de usuarios.

Las rutas anteriores son relativas a la raíz del repositorio. Preservar Plan Maestro, entregables y recursos. El historial inferior no vuelve a abrir los bloqueos ya resueltos.

---

## Historial conservado

## Estado vigente — Hobby y presupuesto autorizados, 05/10/2026 14:59 ART

Pedro autorizó sostener Genius con Railway Hobby y el presupuesto mensual presentado: suscripción mínima USD 5/mes con USD 5 de uso incluidos, alerta de Compute a USD 5 y límite de Compute a USD 10 por ciclo. El excedente sobre USD 5 se cobra hasta el control configurado; impuestos y otros proveedores no están incluidos. La autorización es recurrente y específica, no un presupuesto abierto ni permiso para Pro, nuevos servicios o consumo adicional de Railway Agent. Sustituye la restricción histórica de usar exclusivamente crédito Trial para este alojamiento.

**Autorizado no equivale a contratado ni limitado.** El 05/10 la interfaz sigue mostrando Trial, 29 días / USD 4,98 y uso aproximado de USD 0,02. El formulario correcto, en el workspace de Pedro, muestra Hobby USD 5/mes, cobro inicial de USD 5 y tarjeta obligatoria; Subscribe to Hobby Plan está deshabilitado sin ella. El equipo no ingresó datos de pago ni suscribió. La página Usage de Trial no ofrece Set Usage Limits. Pendiente indispensable: Pedro completa la tarjeta y contratación en el formulario preparado. No solicitar datos financieros por chat.

Después de recibir Hobby activo, el equipo configura Compute soft=5 / hard=10 y Railway Agent hard=0 para evitar una bolsa de consumo no autorizada; lee los valores guardados. El límite Compute corresponde a todo el workspace y detiene sus servicios al alcanzarse. Conserva 1 réplica, 1 CPU/1 GB y volumen de 500 MB; no ampliar recursos automáticamente. No activar altas hasta recibir suscripción, límites y condiciones de operación/privacidad. No volver a pedir aprobación general de este mismo plan/presupuesto.

R2 sigue operativo según la recepción aaeb94b: despliegue 0205274c-1d84-4c47-9097-0e00739b5dde, fuente d1b299d43c77268edb498327c429cc5ed352bba0, primer backup_verified y recuperación sintética PASS. No requiere otro Apply ni nuevas claves. La web conserva altas cerradas y autodeploy OFF. F6A ABIERTA / G6A PENDIENTE.

Checkpoint: `beta/HOBBY_BUDGET_CHECKPOINT.md`. Configuración propuesta: `beta/deploy/HOBBY_BUDGET_PLAN.json`. Evidencia: `beta/evidence/hobby_authorized_checkout_2026-10-05.json`.

---

## Estado vigente — 05/10/2026, R2 operativo

**Activación aplicada por Pedro y primera copia automática recibida. No hay Apply pendiente.** Railway confirma el despliegue `0205274c-1d84-4c47-9097-0e00739b5dde` SUCCESS, creado a las 17:27:38 UTC, fuente efectiva `d1b299d43c77268edb498327c429cc5ed352bba0`. El patch `82bfece6-19ba-4638-84b0-54cf4d030c11` quedó consumido: preDeployCommand vacío, timeout retirado y GENIUS_R2_BACKUP_ENABLED=true. Los tres procesos arrancaron; el log `backup_verified` llegó a las 17:28:44 UTC. HTTPS /api/health devuelve `{"backup":"ok","status":"ok","suspended":false}`.

Cloudflare confirma el primer snapshot operativo `snapshots/20261005T172843Z_3ee20aa4378b0839.gcm`, 185089 bytes, y el objeto cifrado de privacidad, 203 bytes. La función de respaldo sube, descarga, autentica y compara la copia antes de marcar éxito. El ensayo remoto de recuperación sintética PASS y la custodia de clave declarada por Pedro ya están recibidos; no se inspeccionó ni probó su copia independiente. No regenerar claves, repetir la solicitud de acceso ni volver a pedir Apply de este bloque.

R2 conserva acceso público desactivado y retención de snapshots/privacidad/pruebas de 7/8/1 días. Intervalo operativo de 24 h, base máxima de 128 MiB, objetivo de 2 GiB y reserva de subidas de 5 GiB/mes; no constituyen un tope total de factura. No hubo nueva contratación ni cambios en DNS, credenciales o volumen. Autodeploy OFF y registro de usuarios cerrado.

La dependencia siguiente es la continuidad del alojamiento y el presupuesto antes de abrir altas reales, junto con la recepción de las condiciones operativas del aviso. La autorización monetaria sigue limitada al crédito existente. No tratar R2 como autorización de Hobby/Pro ni como garantía de 90 días de alojamiento. No repetir el circuito HTTPS y la recuperación ya probados sin una falla concreta. Conservar la preferencia de Apply manual para futuros bloques; un restart-service con volumen mantiene las condiciones de su herramienta.

Preparado y configurado: sí. Probado: S3 y recuperación remota con datos sintéticos, más primera copia automática verificada. Publicado: web con altas cerradas y respaldo activo. Validado con evidencia real de usuarios: no. F6A ABIERTA / G6A PENDIENTE.

Evidencia vigente: `beta/evidence/r2_operational_accepted_2026-10-05.json`. Detalle: `beta/R2_BACKUP_CHECKPOINT.md`. Este estado sustituye todos los pendientes históricos de credenciales, prueba, custodia declarada y activación de R2.

---

## Historial conservado

## Actualización vigente — 05/10/2026: recuperación R2 recibida

La prueba remota pasó en el despliegue `995b6115-1fd8-4758-9d0f-75de9ae359c0` (SUCCESS), fuente `d1b299d43c77268edb498327c429cc5ed352bba0`. El recibo `20261005T171053Z_a576f607` acredita cifrado, subida, descarga y recuperación offline tras perder el origen sintético. También acredita respeto de borrados posteriores, eliminación de sesiones y tokens, consentimientos desactivados y recuperación suspendida. Se subieron dos objetos a `probes/`, por 144279 bytes. El volumen de producción no se tocó. Cloudflare corroboró ambos objetos, acceso público desactivado y caducidad de snapshots/privacidad/pruebas de 7/8/1 días. LIST/PUT/GET funcionan; no se auditó la exclusividad del alcance de la credencial.

Pedro confirmó guardar la clave de cifrado el 05/10/2026 a las 14:21 ART. Es una declaración del propietario; no se inspeccionó ni probó su copia independiente. No volver a pedirla ni regenerar la clave. La huella canónica del runtime es `100ca71c36449e88ec007fec0d49f1a3747217aeb205463b2e2c333ae7c147c4`, idéntica a la del contenedor. La huella anterior correspondía a una copia local con un salto de línea adicional; la diferencia quedó explicada sin cambiar código.

Activación preparada: patch `82bfece6-19ba-4638-84b0-54cf4d030c11`, tres cambios STAGED no destructivos, verificados por conector y UI. Retira el comando de prueba y su timeout, y cambia `GENIUS_R2_BACKUP_ENABLED` de false a true. El equipo no lo aplicó. Actualmente HTTPS devuelve health=ok y backup=disabled. Tras el Apply manual de Pedro, recibir el primer `backup_verified`, health backup=ok y un snapshot cifrado operativo en R2. Registro y autodeploy permanecen desactivados.

La prueba remota y la custodia declarada dejan de ser bloqueos. Sigue pendiente recibir la copia operativa y resolver la continuidad de alojamiento antes de abrir altas. Se conservan los límites de 24 h, base de 128 MiB, almacenamiento objetivo de 2 GiB y reserva de subida de 5 GiB/mes; no constituyen un tope total de factura. Sin planes nuevos ni cambios en DNS o volumen. No se modificó el runtime ni se repitió CI por documentación; CI 37343940425 sigue vigente. F6A ABIERTA / G6A PENDIENTE, sin evidencia de usuarios reales.

Evidencia: `beta/evidence/r2_recovery_accepted_2026-10-05.json`. Este bloque sustituye los pendientes históricos de prueba S3 y custodia; no sustituye la recepción del respaldo operativo.

---

## Actualización vigente — 05/10/2026, recepción de variables y prueba R2 preparada

Pedro aplicó las cinco variables. Railway confirmó SUCCESS en b8bbdeb8-902e-4903-9598-996e85942c37, creado16:19:18 UTC, fuente93143d76f57fa29d208c25874b5c09b11cbe2732. Los14 nombres están presentes; el patch4670ef25-5ec1-45b2-a96e-ea99738b5ea5 quedó consumido. HTTPS /api/health devuelve status=ok,backup=disabled,suspended=false; /api/config confirma registration_open=false. El código de ejecución coincide con271c8069 en los52 archivos comparables; las dos diferencias adicionales son planes JSON, no runtime.

No se acreditó todavía autenticación S3 ni recuperación de nube. La consola aparece Connected pero no procesa las entradas por los controles disponibles, incluso tras una reconexión. No extraer secretos, repetir login Cloudflare ni pedir claves por chat para resolverlo. Se implementó beta/deploy/r2_recovery_probe.py, commit4fd49d6eff7ac12b95c65725805efe1f3a1d9adb; cuatro pruebas locales PASS y CI37343940425/verify111877681520 SUCCESS, staging111878008151 SKIPPED.

Está preparado el patch92f89037-ee82-47bc-8061-5da8c7907719, dos cambios no destructivos: preDeployCommand=["python /app/beta/deploy/r2_recovery_probe.py"] y preDeployTimeoutSeconds=180. Se verificó por lectura y en UI; NO aplicado por el equipo. El probe usa las credenciales ya guardadas, UID10001, /tmp, dos objetos cifrados bajo probes/ (máximo2MiB total, caducidad24h), temporizador interno150s y salida JSON sin secretos. No monta ni modifica el volumen de producción. Prueba backup real, descarga, pérdida de origen sintético, recuperación suspendida y supresiones posteriores; no usa snapshots/ o privacy/ reales. La ejecución remota queda pendiente del Apply manual de Pedro.

Próximo: recibir Apply del bloque de prueba, verificar SHA y receipt remoto PASS; después retirar preDeployCommand/timeout y preparar activación de respaldos en otro bloque revisable, sólo con custodia independiente de clave confirmada. No regenerar GENIUS_BACKUP_ENCRYPTION_KEY. Autodeploy producción sigue OFF. Crédito visible durante revisión: Trial29d/$4.98, observación puntual sin garantía de saldo futuro; no se contrató plan ni autorizó sobreconsumo. Mantener altasfalse y resolver continuidad del alojamiento antes de abrirlas. F6A ABIERTA/G6A PENDIENTE, sin evidencia empírica de usuarios reales.

Evidencia vigente: beta/evidence/r2_runtime_received_probe_prepared_2026-10-05.json. Continuidad: beta/R2_BACKUP_CHECKPOINT.md y CONTINUATION_PROMPT.md. Este bloque sustituye las afirmaciones históricas de cinco variables todavía pendientes; el historial inferior se conserva.

---

# Estado vigente — R2 configurado; credencial de ejecución pendiente (05/10/2026)

R2 activado por Pedro y comprobado por API. Bucket **genius-production-backups**, ID105b125e5e464480bb1dbb60fdf9b167, cuenta4a275114cfef4b41e73a135f089186ce, Standard/WEUR/default. Acceso r2.dev deshabilitado y ningún dominio personalizado. Retención configurada: snapshots7d, registro de supresiones8d (más que cualquier backup restaurable), pruebas1d. Listado final: cero objetos.

Runtime preparado **271c8069c59dee2a400310a91a7d8c95e486b800**. CI37263867852 PASS:42 pruebas beta (16 de respaldo),30 coordinador,3 restauración SQLite,5 guards,HTTPS local y build Docker. Cifrado AES-256-GCM, verificación tras descarga, límites/estado, intención de borrado durable antes de confirmar eliminación, recuperación offline suspendida y pausa de nuevas escrituras si el respaldo falla. Ensayos locales con transporte simulado; no acreditar red S3 real por estos resultados.

**Acceso actualizado (05/10/2026, 06:16 UTC):** Pedro creó la identidad R2 y agregó GENIUS_R2_ACCESS_KEY_ID y GENIUS_R2_SECRET_ACCESS_KEY en genius-public-beta/production. La consulta confirmó los nombres; sus valores y el alcance efectivo aún requieren prueba S3. El equipo agregó GENIUS_BACKUP_ENCRYPTION_KEY (32 bytes aleatorios base64), GENIUS_R2_ACCOUNT_ID y GENIUS_R2_BACKUP_ENABLED=false. Los cinco cambios están STAGED en patch4670ef25-5ec1-45b2-a96e-ea99738b5ea5, no destructivo. No regenerar la clave existente. La escritura inicial por conector informó éxito pero no persistió; se resolvió por la vía de navegador ya autorizada y el readback confirmó los cinco nombres. No se pulsó Apply. Próxima acción del propietario: conservar una copia de la clave de cifrado en su gestor seguro y aplicar este bloque de configuración con respaldo desactivado. Luego el equipo recibe el SHA desplegado, prueba S3 y recuperación sintética; la activación posterior será otro bloque revisable. No pedir claves por chat. Evidencia: beta/evidence/r2_credentials_staged_2026-10-05.json.

Hay cinco variables pendientes de Apply, con respaldo desactivado. Runtime servido sigue964d6c5 con HTTPS y altas cerradas; el código R2 nuevo no está desplegado. No cambió plan Railway, DNS, registrador ni staging privado. Continuidad del alojamiento y recuperación/reinicio reales siguen pendientes antes de abrir altas. F6A ABIERTA / G6A PENDIENTE.

Checkpoint: beta/R2_BACKUP_CHECKPOINT.md. Operación: beta/docs/R2_RECOVERY.md. Evidencia: beta/evidence/r2_configured_ci_2026-10-05.json. Las referencias siguientes a activar R2 o elegir Pro son históricas.

---

# Estado vigente — HTTPS recibido, 05/10/2026 UTC

**El bloque de25 cambios está APLICADO. No hay Apply pendiente.** Genius funciona en https://geniusdecision.app/ con altas cerradas. Desplieguee4f4c137-0b00-4826-a970-032d51f54461 SUCCESS; una instancia,volumen500MB/data,Dockerfile,UID10001 y HTTPS recibidos. Ensayo sintético por dominio real PASS: motor,artefacto,aislamiento,exportación y borrado. Datos ficticios eliminados; cero candidatosF6A.

Checkpoint canónico: beta/PUBLIC_PRODUCTION_CHECKPOINT.md (desde beta: PUBLIC_PRODUCTION_CHECKPOINT.md). **Nueva dependencia:** la cuenta exige Pro para crear backups. No se cambió plan ni se superó la autorización de crédito gratuito. Ver beta/RECOVERY_ENABLEMENT_REQUEST.md: decisión de respaldo/presupuesto y pedido explícito de ensayo de reinicio/restauración con volumen. Mantener altas cerradas hasta recibir recuperación y continuidad. Publicación técnica no cierra F6A/G6A.

El SHA efectivo del deploy es964d6c5,descendiente documental del runtimebfd937c3; comparación de31 archivos confirma equivalencia del código. No inferir SHA efectivo desde el pin serializado. Preferencia de Apply manual se mantiene; avisar cuando haya un bloque concreto. No recrear recursos,tocar staging privado,pedir secretos o entrar a Gmail.

---

Historial conservado abajo; prevalece el checkpoint HTTPS de arriba.

Historial conservado abajo; prevalece el checkpoint de aplicación manual de arriba.

# Actualización vigente — datos públicos recibidos, 05/10/2026 UTC

Pedro proporcionó y autorizó los datos del responsable para el aviso público. Se incorporaron a la configuración preparada; ver `beta/PUBLIC_CONTROLLER.md` (desde beta: `PUBLIC_CONTROLLER.md`) y `beta/deploy/PUBLIC_APPLY_REQUEST.json`. Se usará el correo provisto para la beta; el correo con dominio propio es opcional. No volver a pedir nombre, domicilio o contacto ni exigir que el contacto no sea Gmail. No se autoriza acceso a casillas ni envíos por este registro.

**Preparado: sí. Aplicado en Railway: no. Publicado: no.** Persisten recepción de producción/DNS/HTTPS/backups y condiciones de continuidad dentro del crédito; F6A abierta/G6A pendiente. La lectura recargada de Railway muestra Trial30 días/USD5 redondeados. La automatización privada y su secreto no cambian. Las referencias posteriores a identidad pendiente son históricas y quedan resueltas por esta actualización.

---

# Decisiones vigentes — apertura pública, 04/10/2026

1. Separar deploy y altas con `GENIUS_REGISTRATION_OPEN=false` por defecto en producción; conservar guard de HTTPS y responsable real. Cerrar altas no bloquea derechos de cuentas existentes.
2. Exigir versión del aviso mostrada y confirmación explícita de mayoría de edad; no recolectar fecha de nacimiento ni activar investigación/seguimiento por defecto.
3. Mantener mismo origen web/API y SQLite durable. Fijar base Docker al digest recibido y verificar HTTPS local en CI de preparación. Railway sólo recibe mutaciones desde deploy/staging; no confundir esa rama con producción.
4. No crear recursos públicos que no pueden arrancar legítimamente mientras falten datos reales del aviso. Preparar el diff completo y realizar nosotros configuración/DNS/backups tras resolver la dependencia. No solicitar nueva conexión ni repetir autorización general de publicación.
5. Preservar presupuesto gratuito, entorno privado y evidencia histórica; no iniciar F6B/F7/F8 ni cerrar F6A por publicación. El recibo focal de este cambio es CI37242976400, no una nueva auditoría independiente.


---

Registro anterior conservado como historial; prevalece el checkpoint público del 04/10/2026.

# Estado vigente — automatización privada recibida, 04/10/2026

**AUTOMATIZACIÓN PRIVADA ACTIVADA Y PROBADA: PASS. BETA PÚBLICA NO PUBLICADA. F6A ABIERTA / G6A PENDIENTE.**

`GENIUS_STAGING_AUTOMATION_ENABLED=true` está guardada en GitHub. El push recibido a `deploy/staging` disparó Actions `37241404579` sin botón Deploy ni nueva confirmación manual de Railway. Fuente exacta `a8af0502a022aa2c3d87c4e7da29be63e50717a6`; seed `0fad946e-7c57-4f5b-927c-7d28276fa9d4` y verify `93d5c72a-f0ab-48bf-b726-3278bf4e125a`. Ambos fueron aceptados con instancias EXITED, el mismo volumen de 500 MB y la misma imagen reportada por Railway: `sha256:c2c216078646653351ee3a3cdb8652196afc40ef0424ca90e1a56590bb943074`. Readback final: cero procesos en ejecución, cero fallos, sin parches pendientes, dominios ni proxies.

Se resolvió el bloqueo de identidad: `deployment.meta.imageDigest` coincide en ambas fases. El digest de build es una observación distinta y no se usa como sustituto. 30 pruebas focales del coordinador PASS, pruebas beta y construcción Docker PASS en la corrida real. El verify conservó base de datos, registro de borrado, revocación de credenciales/consentimiento sintéticos, artefacto y suspensión; restauración SQLite comprobada. Evidencia y artefacto con hash verificado: `beta/evidence/staging_ci_automatic_accepted_2026-10-04.json`. No acredita HTTP/auth/HTTPS ni backup de proveedor.

El secreto existente continúa únicamente en Actions; no se leyó su valor ni se incorporó a Git/runtime. No hay acción pendiente de Pedro para este acceso o para la automatización privada. La autorización sigue limitada al crédito gratuito: Railway Trial muestra USD 5/30 días redondeados con corte; GitHub mostró 15/2.000 minutos, USD 0 facturables y presupuesto Actions USD 0 con Stop usage. La medición puede retrasarse y el volumen sigue provisionado. No se cambió plan, tarjeta, DNS, correo, datos reales ni configuración del dominio.

La automatización es por cambios de runtime en `deploy/staging`; los cambios exclusivamente documentales no ejecutan un ensayo. El autodeploy nativo de Railway permanece deshabilitado. La conexión conserva rama/pin histórico af188823; la API usa el SHA explícito del push y se comprobó que el contenedor ejecutó `a8af0502a022aa2c3d87c4e7da29be63e50717a6`. No interpretar la rama histórica como la fuente de la última ejecución ni pulsar Deploy para repetirla.

Continuar desde `beta/AUTOMATION_CHECKPOINT.md`. Mantener Plan Maestro, dominio geniusdecision.app y evidencia histórica; no repetir R0–R3. Próximo trabajo: integración autoservicio/HTTP seguro y límites de la beta, con habilitación consolidada de exposición/identidad legal cuando sea indispensable. Este hito operativo no es validación empírica ni inicia F6B/F7/F8.

---

Historial conservado; prevalece el estado vigente de arriba.

# Actualización vigente — acceso resuelto; confirmación pendiente, 04/10/2026

**Railway ya admite la fuente privada. Configuración aplicada; fuente staged; cero despliegues.**

La lectura del servicio confirma Dockerfile, comando del runner, NEVER, 1 vCPU/1000000000 bytes, una réplica Amsterdam y siete variables configuradas; volumen 500 MB `/data` live. El parche17 anterior ya fue aplicado. El nuevo parche `06cc9e0e-ac5a-4a51-b184-41b033247e38` sólo contiene repo/rama/SHA recibido38dda312eacaf39f68b28f12cf451d64c7378936:3 cambios no destructivos. El 04/10 el panel volvió a mostrar Trial USD5,30 días redondeados,corte por crédito y sin tarjeta. `accept_deploy` devolvió “Cancelled — the user did not approve this action. No changes were made.” La lectura posterior mantiene el mismo parche y lista vacía de despliegues.

Autorización general vigente; falta la confirmación obligatoria de esa operación. No reintentar sin nueva instrucción aplicable ni eludir por otro canal. No pedir reconectar GitHub/Railway ni Gmail. Fuente deploy38dda; los commits documentales no cambian el pin. Siguiente acción completa: `beta/NEXT_PHASE_INPUT.md`; evidencia propia: `beta/evidence/trial_deployment_gate_2026-10-04.json`. F6A abierta/G6A pendiente; beta no publicada. Históricos anteriores preservados abajo.

---

# Decisiones vigentes — 04/10/2026, materialización

- D-B19: recibir como creados los recursos vacíos sólo tras lectura propia. El parche02ce3d7a fue aplicado por el propietario; no reiterar esa confirmación ni recrear recursos.
- D-B20: ante rechazo de `railwayConfigFile` por deprecación, preparar los campos explícitos `dockerfilePath`, comando y límites; conservar JSON históricos. Sin cambio del runner recibido ni claim de build Docker ejecutado.
- D-B21: separar acceso GitHub del conector y acceso Railway a la fuente privada. Mantener el nuevo parche17 sin aplicar mientras se resuelve el acceso. No hacer público el repo, pedir tokens ni sustituirlo por código embebido.
- D-B22: conservar pin de código38dda312eacaf39f68b28f12cf451d64c7378936 aunque avance la punta documental. Verificar source/autodeploy antes del build. 1GB leído equivale a1000000000 bytes, no1GiB.

Alcance/evidencia y próxima acción: `beta/TRIAL_CHECKPOINT.md`. F6A/G6A y autorizaciones de publicación no cambian. Historia anterior preservada.

---

# Actualización operativa F5 — 2026-09-26

Estado actual: F5_COMPLETED; G5_PASS_LOCAL_SYNTHETIC_LAB. Mandato actual [activaciónF5](../PHASE_5_ACTIVATION.md)
y [promptF5](../PHASE_5_PROMPT.md). F4 recibido de nuevo localFP1. Infrastructure
GENIUS-INFRASTRUCTURE-1.0.0 es la nueva capa local; Kernel1.0.1, Protocols1.0.0,
Benchmark1.0.0, Specification1.0.0 y teoríaS2 intactos. F6–F8 no iniciadas.
El alcance ejecutado es laboratorio sintéticoUID0/caps0/NNP1, no prueba nonroot
ni despliegue. Estado/gate vigentes en [aceptación](../ACCEPTANCE_REPORT.md).

Decisiones F5: [registro](../DECISIONS.md); operación: [Infrastructure](../infrastructure/README.md);
reparaciones: [hallazgos](../validation/F5/FINDINGS.md); límites: [residuales](../KNOWN_LIMITATIONS.md).
BaselineF4 íntegra es ZIP original en history; árboles F3/F2/F1/F0 y todos
los negativos heredados se conservan. Trece documentos+verificador+comprobante
externo y recepción final siguen siendo obligatorios. No depender del chat.

Los textos siguientes son registro histórico de F0–F4. Sus afirmaciones de
NOT_CREATED/NOT_STARTED no sustituyen el estado F5 actual señalado arriba;
sus obligaciones científicas y de gobierno continúan vigentes.

---

# Registro acumulativo de decisiones

Fecha de todas las decisiones iniciales: 2026-09-23. Autoridad: mandato S0 y diseño técnico de Fase 0. Aceptadas para organizar el programa; no sustituyen decisiones normativas del propietario ni prueban matemática. Reemplazos futuros agregarán un ADR que identifique al anterior sin borrarlo.

| ID | Problema | Alternativas consideradas | Evidencia | Decisión y justificación | Consecuencias | Reversibilidad | Componentes |
|---|---|---|---|---|---|---|---|
| ADR-01 | Riesgo de declarar cerrada toda Genius a partir del manuscrito | Cierre universal; snapshot acotado; esperar todos los históricos | S1 Entrega 10, P03674–P03675; S0 §§4, 25 | Registrar cierre condicional documentado y reservar revisión formal a F1 | Pruebas presentes no se convierten en software ni eficacia | Sí, con evidencia nueva y revisión | Teoría, claims |
| ADR-02 | Portabilidad sin GitHub | Chat como referencia; dependencia de repositorio; paquete autocontenido | S0 §§0, 19–21 | ZIP con fuentes originales, documentos, prompts y verificador estándar | Ningún vínculo externo es indispensable; hashes detectan alteración accidental | Sí mediante nuevo handoff verificado | Configuración |
| ADR-03 | Numeración modular no coincide con cálculo | Ejecutar M0–MVII serialmente; DAG explícito | S1 P03350–P03377 | Separar orden expositivo de construcción y declarar aristas reales | MV alimenta MIII/MIV/MVI; ciclos de justificación rechazados | Revisable con prueba y perfil nuevo | Integración |
| ADR-04 | Riesgo de heredar v6 sin release | Usar v6 para todo; inventar equivalencia; snapshot independiente | S1 P00250; archivos recibidos | Etiqueta GENIUS-THEORY-2026-09-23-S1; v6 solo mención histórica no verificada | No se afirma conformidad de implementación anterior | Reversible al recuperar y cotejar evidencia | Versionado |
| ADR-05 | Versiones heterogéneas | Un número global; versiones separadas sin vínculo; matriz explícita | S0 §13 | Versiones por componente y matriz con hashes y estados | Compatibilidad desconocida no se trata como compatible | Sí, preservando identificación exacta | Releases |
| ADR-06 | Autoridad de tests y código | Código manda; tests reforman teoría; autoridad por ámbito | S0 §14 | Matemática y premisas normativas separadas; Specification deriva, tests verifican, Kernel implementa | Conflictos bloquean promoción; se corrige artefacto incorrecto | Solo con gobernanza y auditoría | Gobernanza |
| ADR-07 | Qué preparar para el primer Kernel | Generalidad irrestricta; ruta fuerte finita; ejemplo único | S1 §§10.2, 10.3; Teoremas 10.2 y 10.3 | Proponer ruta fuerte finita como perfil inicial de F1, sujeto a auditoría | No estrecha módulos generales; extensiones requieren contrato y evidencia | Sí mediante ADR y nuevo perfil | Arquitectura |
| ADR-08 | Contratos aún no formalizados | Inventar API definitiva; interfaces conceptuales trazables | S0 §3; S1 dominios parciales | Interfaces conceptuales PROVISIONAL; preservar valor, dominio, evidencia, procedencia y cobertura | F1 decide tipos exactos; F0 no implementa API | Sí antes de fijación; después requiere versión | Specification |
| ADR-09 | Decisión no siempre única | Puntaje universal; desempate tácito; frontera y selector explícito | S1 Entrega 9 | Resultado principal conserva factibilidad, frontera y alcance; selección solo con regla autorizada | No inventar pesos o prioridades del propietario | Cambiar exige regla normativa explícita | MVII, producto |
| ADR-10 | Organización por meses y cuentas | Equipo único dependiente de memoria; equipos por fase con handoff | S0 §§15–20 | Nueve equipos funcionales F0–F8, roles combinables, integrador permanente y auditor separado | Sesiones repetibles; no número fijo de agentes ni cuentas | Sí con conservación de funciones y gates | Programa |
| ADR-11 | Protocolos y despliegue futuros | Elegir versiones e implementar ya; posponer detalles | S0 §3 | MCP/A2A/OpenAPI son candidatos F4; infraestructura F5 | Investigación de normas vigentes y seguridad se realiza antes de implementar | Sí, no hay dependencia implementada | F4, F5 |
| ADR-12 | Mezcla de validación, búsqueda y negocio | Construcción simultánea; subgates | S0 §§2, 15 | F6 separa validación empírica, Radar y Solver; F7 no hereda eficacia sin evidencia | Discovery puede prepararse, claims y promoción sujetos a resultados | Sí con ADR | F6–F8 |
| ADR-13 | Alcance de auditoría del paquete | Autor se autocertifica; auditor separado; certificación externa no disponible | S0 §§17, 29 | Auditor adversarial y lector de contexto cero distintos del equipo autor, con contexto inicial vacío | Independencia funcional/contextual interna; no institucional ni de proveedor | Repetible con otros equipos externos | Aceptación F0 |
| ADR-14 | Programa ajeno y acciones externas | Integrar DU; publicar de inmediato; respetar alcance | S0 §§3, 6, 23 | Excluir DU; ningún gate concede por sí solo licencia, publicación o contratación | Propietario decide acciones externas pertinentes en su fase | Depende de decisión expresa futura | Programa |

Las decisiones ADR-01–ADR-14 se conservan como historia de F0. El paquete original está en [histórico F0](../baseline/GENIUS_PHASE_1_HANDOFF/history/GENIUS_PHASE_0_HANDOFF.zip). Las nuevas filas usan el mismo formato: ID, problema, alternativas, evidencia, decisión/justificación, consecuencias, reversibilidad y componentes. Ninguna fila borra una decisión previa.


## Decisiones F1 — 2026-09-23

Estado: decisiones incorporadas y revisadas, aceptadas para el alcance FP1 mediante G1 PASS. La aceptación efectiva se registra en [MASTER_STATE](MASTER_STATE.md) y el informe raíz. No conceden permiso para iniciar F2, publicar o contratar.

| ID | Problema | Alternativas consideradas | Evidencia | Decisión y justificación | Consecuencias | Reversibilidad | Componentes |
|---|---|---|---|---|---|---|---|
| ADR-F1-01 | Delimitar contrato implementable | Generalidad completa; ejemplo único; ruta fuerte efectiva | S1 10.2–10.3; REVIEW_INTEGRATION | Adoptar FP1_FINITE_EXACT, finito y tabulado; concreta ADR-07 sin restringir toda S1 | Horizonte0..H, modo pre, Pi objetivo explícita y no vacía, enteros/racionales exactos | Nuevo perfil/versión con análisis de impacto | Specification, F2 |
| ADR-F1-02 | Ecuación informacional mal agrupada I-06 | Lectura literal mal tipada; reparación de argumentos | AM-01 y OMML P00535–P00536 | Usar R_next(U_A(i, a, y))=U_B(R(i), a, O_next(y)), con dominios correspondientes | Información no se convierte en función; no añade mapa de acciones oculto | Solo con prueba y nueva enmienda | M0, MV |
| ADR-F1-03 | Teorema 8.6 no garantiza admisión de certificados | Confiar solo en lector; añadir clausura canónica | AM-02 y contraejemplo del protocolo solo positivo | Admitir/generar A=Sem para toda consulta decisiva, ambos veredictos, bajo FP1_EXACT_ENUM_V1 | D_V=D* queda justificado para ese protocolo; no para cualquiera | Nuevo protocolo requiere nueva prueba | MVI, integración |
| ADR-F1-04 | Conservar fuente y cambios | Sobrescribir DOCX; reemplazar silenciosamente; capa de enmiendas | AMENDMENTS y cuatro reviews | S1 bytes preservados; S2=fuente S1+AMENDMENTS+perfil explícito, sin nueva transcripción disfrazada | Genealogía auditable; no hereda certificación v6 | Nueva instantánea inmutable | Teoría/versionado |
| ADR-F1-05 | Escenarios y ocurrencias | ID por hoja; fusión por estado; palabras exógenas verificadas | S1Def7.7 y ruta10.2; REVIEW_IV_V | Bijección derivada de fibras singleton de palabras u comunes, todas las ramas hastaH | Multiplicidad causal conserva diagnóstico; no se renombra para aprobar | Nuevo perfil para fibras múltiples/terminación | MV, MVI, comparación |
| ADR-F1-06 | Valores y diagnósticos | Booleans universales; excepciones indiferenciadas; registros separados | Specification01/06 | Tablas parciales cerradas, tipos nominales y racionales exactos; estado operativo separado de dominio | Falta de dato no es falsedad; agotamiento no es inexistencia | Cambios de significado requieren versión mayor | Todo contrato |
| ADR-F1-07 | Comparación de bienestar | Sumas/compensación; matching general; producto identificado | S1 6.2; Specification03 | Soporte global de portadores/aplicabilidad, mediciones por nodo y producto Xi×índices | Conserva daños intermedios y prefijos; no compara poblaciones distintas automáticamente | Nuevo perfil o regla expresamente justificada | MIV, MVII |
| ADR-F1-08 | Elegir entre incomparables | Score universal; desempate tácito; selector explícito | S1 M VII; Specification01/04/05 | Producto CAG/O/W/PVS; none, unique o priority declarada; seleccionar solo frontera exhaustiva FP1 | Ningún peso inventado; priority es dato normativo adicional | Cambio de regla debe quedar en instancia/versionado | Decisión |
| ADR-F1-09 | Promesa fuerte y datos parciales | Ocultar fallos después de hard=0; verificar toda Pi | G01–G15 Specification 05 | Certificado fuerte exige todas las guardas, incluidos recursos y bienestar completos de políticas refutadas | Resultados parciales independientes se conservan; frontera relativa tiene alcance limitado | Otra ruta requiere versión y demostración | Integración |
| ADR-F1-10 | Declarar conformidad sin implementación | Tests ficticios; solo ejemplos; catálogo y oráculos diseñados | CONFORMANCE_CASES y WATER_HABITAT | Marcar casos DESIGNED y fixture EXPECTED; reservar ejecución de Kernel para F2 | Una comprobación documental/JSON no se cuenta como test Kernel | Cambia a ejecutado solo con registros reproducibles | F1/F2/F3 |
| ADR-F1-11 | GitHub inaccesible | Bloquear formalización; continuar portable | TRANSFER_PROTOCOL; autorización F1 | Continuar con handoff autosuficiente; repositorio no es requisito de F1 | Migración futura necesita identificar paquete/commit y validar integridad | Reversible cuando haya acceso legítimo | Configuración |

Licencia, publicación, datos reales, negocio y parámetros normativos de futuras aplicaciones siguen reservados al propietario según GOVERNANCE. El perfil permite declararlos como premisas o parámetros cuando corresponde; no los elige en su nombre.

## Decisiones F2 — 2026-09-23

F2 está autorizada por «inicia fase 2» y PHASE_2_MANDATE. Estado COMPLETED, G2 PASS; GENIUS-KERNEL-1.0.0 es ACCEPTED_FOR_FP1. La aceptación se sustenta en los informes de ejecución, auditoría y recepción, no solo en estas decisiones. Al cierre histórico de F2, F3 no estaba iniciada. El desarrollo F2, límites y resoluciones de lectura constan en [F2_ENGINEERING](decisions/F2_ENGINEERING.md).

| ID | Problema | Alternativas y evidencia | Decisión y consecuencias | Revisión |
|---|---|---|---|---|
| ADR-F2-01 | Runtime reproducible y exactitud | Dependencias externas o biblioteca estándar; FP1 exige enteros/racionales exactos | Python >=3.11, Fraction y unittest; ejecución offline directa. CPython 3.12. 14 es el entorno observado | Cambios requieren nueva evidencia de reproducción |
| ADR-F2-02 | Preservar la entrega aceptada | Editar F1 o conservar un predecesor inmutable | Baseline F1 y ZIP original congelados; Specification/S2 sin cambios, Kernel con identidad propia | Una contradicción contractual reabre la parte afectada de F1 |
| ADR-F2-03 | Verificar certificados sin confiar en sus etiquetas | Inspeccionar PASS, duplicar toda implementación o recomputar | Verificador de resultado y certificado decisivo deriva obligaciones desde bytes originales; puede compartir constructores. Tests y auditoría aportan oráculos separados | No equivale a dos implementaciones independientes |
| ADR-F2-04 | Portabilidad del cálculo | Servicio remoto o API/CLI local | Evaluación/verificación local y pareja input.json/result.json ligada por SHA-256 | Ningún servicio, publicación o cuenta es dependencia |
| ADR-F2-05 | Agotamiento operativo sin alterar el problema | Truncar H/ramas o declarar límite | Opciones max_nodes, max_operations, max_seconds, max_input_bytes, max_integer_digits y presupuesto ambiental python_recursion_depth en la salida; LIMITED sin selección | Tiempo cooperativo; no promesa de interrupción dura ni memoria ilimitada |
| ADR-F2-06 | Restricción decimal implícita del intérprete | Convertirla en límite matemático o hacerla explícita | Desactivar el tope implícito; max_integer_digits opcional solo para numerales recibidos, no enteros derivados | Un agotamiento conserva carácter operativo |
| ADR-F2-07 | Historia del catálogo de conformidad | Reetiquetar F1 como ejecutada o añadir evidencia F2 | Conservar los 36 diseños originales; trazar los 26 FP1 a pruebas F2, mantener separados límites THEORY_GENERAL | Resultados y recuentos finales solo con ejecución registrada |
| ADR-F2-08 | Separación de autoría, auditoría y continuidad | Aceptación por autores o revisión separada | Funciones de implementación, pruebas, auditoría y receptor sin historia; cierre G2 respaldado por evidencia conjunta en aceptación raíz | Independencia funcional interna, sin afirmar auditoría institucional externa |

Las resoluciones sobre continuación causal no acreditada, subárboles locales completos y calibración común se documentan en F2_ENGINEERING y fueron revisadas por el auditor. No crean campos nuevos ni cambian el significado normativo de FP1 por decisión del código.


## Decisiones F3 — 2026-09-23

Activación expresa: «Inicia fase 3» y PHASE_3_MANDATE. G3 permanece pendiente hasta revisión conjunta; no se abre F4 por existir Benchmark.

| ID | Problema | Decisión y evidencia | Consecuencia |
|---|---|---|---|
| ADR-F3-01 | Independencia del oráculo | Nuevos generadores desde contrato; lenguaje de palabras/productos de caminos, enumeración CSP de join y certificados handmade | Verificador compartido no cuenta como segundo algoritmo completo |
| ADR-F3-02 | Configuración elegida después del resultado | Diseños previos y hashes antes/después, parámetros/semillas y rangos explícitos | Cambios se conservan y justifican; corpus negativo no se elimina |
| ADR-F3-03 | Diferenciar falla del sujeto de falla del experimento | F3-K-001 requiere parche Kernel; F3-EXP-01 corrige expectativa incompatible con 06 | No cambiar Specification ni rebajar obligaciones para PASS |
| ADR-F3-04 | Preservar identidad al reparar | Baseline Kernel1.0.0 inmutable; Kernel1.0.1 validado para el alcance con mismo contrato; evidencia antes/después | La versión recibida conserva su historia y limitación descubierta |
| ADR-F3-05 | Medir seis ejes sin extrapolar | Sweep de horizonte, ramificación, políticas, vistas, semántica y dígitos; tres repeticiones; tiempos separados de setup | Resultados específicos de carga/entorno, sin rendimiento universal |
| ADR-F3-06 | Revisión y transferencia | Auditor y receptor sin historia separados de autores; ZIP autónomo con integridad | F3 requiere gate documentado y no activa F4 |

ADR-F3-07: G3 PASS tras508 casos/9201 checks, reparación reproducida, auditoría y recepción separadas. Promoción Kernel1.0.1 VALIDATED_FOR_SCOPE y Benchmark1.0.0 ACCEPTED_FOR_SCOPE. F4 NOT_STARTED.

## Decisiones F4 — 2026-09-23

Activación expresa «inicia fase 4» después de G3. Las afirmaciones NOT_STARTED anteriores son estados históricos.

| ID | Problema y alternativas | Decisión y consecuencia |
|---|---|---|
| ADR-F4-01 | Interfaces de múltiples ecosistemas vs mínimo comprobable | Perfil genius-protocols/1.0 basado en envelopes JSON-RPC2.0/stdio; no MCP/A2A/OpenAPI. [Decisión](../protocols/TRANSPORT_DECISION.md). |
| ADR-F4-02 | JSON reserializado puede perder bytes/precisión | ByteEnvelope canonical base64 + SHA256; input intacto hasta Kernel, Result completo, candidato estricto. |
| ADR-F4-03 | Mismo lenguaje/código compartido no acredita interoperabilidad | Cliente Node separado y auditoría blackbox; Kernel Python intacto. |
| ADR-F4-04 | Cancelación y límites pueden confundirse con refutación | Terminación de proceso = fallo de transporte; KernelLIMITED sigue separado, sin resultado fabricado. |
| ADR-F4-05 | Integridad y continuidad | F3ZIP y baseline exactos; reproducción heredada separada de evidencia F4. Auditor y receptor distintos de autores. |

Decisiones reversibles por nueva versión y evidencia, sin reescribir baselines ni ampliar claims. El gate efectivo lo decide el informe actual después de revisión.

ADR-F4-06: G4 PASS tras contrato, consumidor independiente, auditoría, reparación revisada por receptor y recepción funcional. La aceptación es local FP1; Protocols1.0.0 ACCEPTED_FOR_LOCAL_FP1. F4-RCV-001 reparó solo el registro del arnés, con fuentes anteriores y negativo conservados. F5 NOT_STARTED; el ZIP final se verifica en extracción nueva y el comprobante externo fija sus bytes.
