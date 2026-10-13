# Estado vigente — decisiones cotidianas guiadas, 06/10/2026

Mandato nuevo de Pedro: avanzar en traducción de problemas, perfiles admitidos y validación real, conservando Plan Maestro v2 y R0–R3. Implementado **CHOICE_DECLARED_V1**, código **7c9348e2cb9fdbf4186f9a0767ac2211de8ad71a**: guía de cuatro pasos, revisión/confirmación de modelo, comparación con el Kernel FP1 recibido, recomendación condicional, alternativas, límites, sacrificios, desconocidos, versiones y feedback; API/MCP `prepare_decision` y `revise_case`.

Alcance: ocio/organización personal de bajo riesgo; 2–8 alternativas, 1–5 criterios explícitos. La narrativa aporta contexto, no se interpreta automáticamente en la web. No LLM externo, búsqueda de datos, probabilidad inventada ni admisión empírica de CAG/PVS. La compilación declara constantes formales comunes para dimensiones no evaluadas; la recomendación sólo vale para la tabla confirmada. No es un Radar/Solver general. Diseño: `beta/DECLARED_CHOICE_DESIGN.md`.

**Preparado y probado:** 92 pruebas locales, 14 nuevas; navegador escritorio/móvil PASS; cliente MCP oficial PASS; fuentes recibidas 13/79 intactas. CI **37446221959**, verify **112211582416 SUCCESS**, incluidos navegador, Docker, HTTPS, MCP y recuperación. Recomputación formal y pruebas de autor; no se afirma auditoría externa nueva.

**Publicado:** MCP y demo anteriores ya están publicados: deployment **0e68fe1a-3228-4936-9f67-2ef27d3d6ca9 SUCCESS**, fuente efectiva **0cad72775d6676a423f7d0d85363b487f6068b4e**. El nuevo perfil cotidiano todavía no está publicado: patch **1353ae55-c12e-4440-847c-3e76160b3e72 STAGED**, un cambio no destructivo de código, pendiente de **Apply manual de Pedro**. No se llamó accept-deploy.

**Evidencia real:** no se incorporaron casos reales admitidos en este ciclo. **F6A ABIERTA / G6A PENDIENTE**. Protocolo de campo preparado en `beta/DECLARED_CHOICE_FIELD_PROTOCOL.md`; feedback percibido no acredita utilidad ni comprensión. Sin migración, proveedor, secreto, plan o recurso nuevo; se mantienen presupuestos/cuotas/retención.

Checkpoint: `beta/DECLARED_CHOICE_CHECKPOINT.md`; evidencia: `beta/evidence/declared_choice_prepared_2026-10-06.json`; próxima acción: recibir Apply y verificar producción. La falta de participantes no detiene ingeniería ni autoriza inventar demanda o evidencia.

Dependencias de este incremento: código/pruebas/CI resueltos; publicación pendiente de Apply; recepción del nuevo perfil en producción pendiente. Accesos existentes reutilizados; no se requiere reconectar cuentas. Para traducción libre LLM dentro de la web se necesitan propuesta de proveedor/costo/privacidad y credencial de ejecución segura, pero esa dependencia NO bloquea la guía ni la integración mediante un agente existente. Casos reales y admisión de dominio siguen separados del canal operativo.


---

## Registro histórico conservado; el estado vigente figura arriba

## Dependencias vigentes — lectura GET y MCP, 06/10/2026 ART

Resueltos: resultado real guardado legible por GET fuera de /api/, servidor MCP sobre operaciones existentes, prueba interoperable con cliente oficial 2.3.0 en protocolo 2026-07-28 y 2025-11-25, suite 78 PASS y CI 37414933544 SUCCESS. Ninguna nueva cuenta, recurso, dependencia de ejecución, secreto o plan de pago requerido.

Pendiente indispensable para publicar: Apply manual del patch 7918c89a-7a0e-4e88-995c-880a5da91202, un cambio de código en genius-public-beta / production. Después recibir fuente efectiva, archivos GET y contrato MCP por HTTPS; una sola demo sintética MCP con limpieza si hay disponibilidad/cuota. No confundir con el Apply anterior ya recibido.

Para probar Claude, el propietario debe agregar/habilitar el conector remoto en su cliente una vez publicado. Documentación oficial actual admite No sign in para herramientas públicas y Request headers para credenciales fijas. Gemini CLI admite Streamable HTTP; no asumir equivalencia con la app web/móvil. No contamos con prueba en esas cuentas ni con error de conexión concreto: los textos proporcionados son recomendaciones generales.

OAuth sigue sin implementar; clientes que lo exijan para operaciones privadas necesitan otra etapa. Demo pública y clientes con cabeceras no dependen de OAuth. Mantener la autorización administrativa previa y no esperar la constancia final para continuar lo autorizado. F6A mantiene sus requisitos propios. Detalle: beta/MCP_ACCESS_CHECKPOINT.md.

---

## Historial conservado; prevalece la actualización anterior

## Dependencias vigentes — recepción de agentes completa, 06/10/2026 ART

Resueltos Apply manual, identidad ejecutable, HTTPS de descubrimiento, estado de respaldo y prueba productiva acotada del nuevo recorrido. Deployment c930af77-2653-4bfd-abe9-db01ef5f12b1 SUCCESS, fuente efectiva 331a0717167d1ed0c5b9073695563eb3a99ff93c equivalente al candidato 5c55716d. No hay otra acción de Pedro indispensable para este cambio.

Demo sintética: creación 202, motor completed, borrado 204 y acceso revocado 401. Registro persistente, rotación y scopes están publicados y probados localmente/CI; no afirmar que todos esos recorridos fueron ensayados en producción. El formulario humano permanece publicado sin cambios.

La integración externa requiere un cliente capaz de efectuar HTTP y custodiar la credencial. La guía pública está en https://geniusdecision.app/agents y el manifiesto en /agents/manifest.json. Un lector de páginas no adquiere esas capacidades por leer la guía. MCP/OAuth no implementados. Para diagnosticar un rechazo hace falta cliente/herramienta y URL concreta; no es un bloqueo operativo general demostrado.

Conservar límites y seguimiento administrativo existentes, incluida la autorización de avanzar sin constancia final. F6A mantiene requisitos propios; no repetir un ciclo sólo para describir ausencia de participantes. Recibo: beta/evidence/direct_agent_access_accepted_2026-10-06.json.

---

## Historial conservado; prevalece la actualización anterior

## Dependencias actualizadas — acceso autónomo, 06/10/2026 ART

Resueltas: prueba sintética directa, identidad de máquina sin formulario humano, scopes/expiración/rotación para las nuevas claves, cuotas compartidas persistentes, migración aditiva y compatibilidad de recuperación con respaldos del esquema anterior. Código 5c55716dbd838be19321bd1e1a07e0874fa2baef, 66 pruebas y CI 37407139747 SUCCESS. El portal anterior está publicado y recibido en 2549eb0d-b6c6-49d4-8cca-44751ee223f4.

Pendiente indispensable: Apply manual del patch f7f5fb7f-38f9-4a0e-a38d-e921a6c3138b, una actualización de código. Después: recibir fuente efectiva y rutas/contrato nuevos por HTTPS; una prueba sintética acotada del nuevo recorrido, con credencial sólo en memoria y eliminación de su espacio. No solicita cuentas de proveedores, nuevas claves de infraestructura ni contratación.

Para que una IA externa opere necesita un cliente HTTP capaz de custodiar la credencial automáticamente. Un lector web no obtiene esa capacidad por leer llms.txt. MCP y OAuth siguen pendientes; no anunciar /mcp. Permisos finos de claves humanas existentes no fueron implementados, su alcance previo se conserva y está informado.

Mantener las restricciones y seguimientos administrativos previos, sin repetirlos como bloqueos técnicos nuevos. F6A requiere evidencia propia.


---

## Historial conservado; prevalece la actualización anterior

## Dependencias actualizadas — entrada para agentes, 05/10/2026 ART

- Resuelta: base técnica REST/Bearer existente y portal público de descubrimiento implementado en d4e747ab54752487754c7e8bab97e7b75f5d9a90; no requiere otro proveedor, dominio, base de datos ni paquete de ejecución.
- Resuelta: 49 pruebas locales, sintaxis JS y CI 37402269451 SUCCESS; uso del motor con datos sintéticos, aislamiento y revocación.
- Pendiente operativo: Apply manual del patch c377c6e0-6720-444f-838b-556583525d09, un cambio no destructivo; luego recibir deployment efectivo y rutas públicas HTTPS. No pedir de nuevo autorización general de publicación ni pago Hobby.
- Pendiente por integración: cliente capaz de llamadas HTTP autenticadas, cuenta de la persona responsable y clave colocada en su gestor de secretos. No solicitarla por chat ni asumir que un navegador de búsqueda puede usarla.
- Extensiones no implementadas: scopes/expiración por clave y OAuth/MCP. Las claves actuales son full-account; la documentación lo declara.
- El diagnóstico de rechazo por IAs requiere nombre de herramienta y URL concreta; no es evidencia de bloqueo general ni condición para conservar la nueva documentación.
- F6A sigue abierta por sus requisitos propios; no equivale al hito técnico.


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

# Dependencias vigentes — apertura pública, 04/10/2026

Acceso GitHub/Railway/Cloudflare disponible; dominio geniusdecision.app active sin registros DNS en lectura propia. CI existente usa su secreto sin nueva intervención. Alta/UI/motor/expedientes/TLS local y Docker verificados en runtime bfd937c3; no son pendientes de construcción.

Pendientes indispensables: identidad/domicilio/contacto público del responsable y condiciones de privacidad/continuidad dentro del crédito; luego configuración y recepción de producción, DNS/TLS externo y backups diarios. Esas tareas técnicas son del equipo. Supabase/PostHog/Resend no son requisitos del alcance actual. Ver `beta/PUBLIC_BETA_CHECKPOINT.md` y `beta/docs/PUBLIC_LAUNCH.md` (ajustar rutas según documento).


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

# Actualización vigente — materialización comprobada, 04/10/2026

Servicio y volumen Railway **creados y verificados**: 500 MB en `/data`, Amsterdam. El parche antiguo vacío ya fue aplicado por Pedro. Nuevo parche `9c653409-d8a5-4e80-be78-de88d98fd85d`: **17 cambios staged, no destructivos, sin aplicar**, para límites y runner interno.

Railway no pudo acceder a `pedrosalvadeo/genius-decision`; GitHub confirmó la rama en el commit recibido `38dda312eacaf39f68b28f12cf451d64c7378936`. Falta comprobar/habilitar la instalación Railway sobre ese repositorio. **Sin fuente adjunta, build, deployment, endpoint ni evidencia empírica.** F6A abierta/G6A pendiente. Config as Code fue rechazado; se prepararon campos explícitos del servicio. Código y pruebas recibidos no cambian.

Checkpoint completo y siguiente acción: `beta/TRIAL_CHECKPOINT.md`, `beta/NEXT_PHASE_INPUT.md`; evidencia `beta/evidence/trial_materialization_2026-10-04.json`. No reconstruir R0–R3, recrear recursos ni solicitar Gmail. Las secciones siguientes quedan como historia y no gobiernan la próxima acción.

---

# Actualización Trial vigente — 04/10/2026

Autorización general de ensayo gratuito concedida, panel Railway comprobado (Trial USD5/30d mostrados, corte por agotamiento, sin tarjeta). Proyecto privado/entorno creados; servicio/volumen sólo staged. accept_deploy cancelado por confirmación obligatoria no aprobada. No fuente, build ni publicación; F6A sigue abierta. Detalle y próxima acción: [../beta/DEPENDENCIES.md](../beta/DEPENDENCIES.md). Las secciones siguientes son históricas y no revierten este estado.

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

# Dependencias y orden de construcción

F2 implementa el DAG normativo de [Specification 05](specification/05_PIPELINE_AND_GUARANTEES.md). La numeración M0–MVII es expositiva; no fija un orden serial de cálculo. Los objetos de entrada permanecen congelados.

| Productor → consumidor | Objeto y obligación |
|---|---|
| S1 + enmiendas S2 → Specification | Fuente preservada, perfil FP1 explícito y contrato aceptado en G1 |
| Bytes → schema | UTF-8/JSON, SHA-256, tipos, tablas, referencias y variantes |
| Inicialización/modelo/políticas → causal | Información legítima y todas las ocurrencias hasta H, sin fusiones |
| Árboles → escenarios | Imagen exacta de palabras u y fibras singleton |
| Árboles/tablas → structural | Perfiles, suficiencia, proyecciones/joins, recursos, CAG y bienestar |
| Árboles/referencias/tarea → evidence | Completaciones, semántica parcial y certificados canónicos 0/1 |
| Árboles/ley → masas/PVS | Todas las ramas, incluidas masas cero; PVS exige masa indecidida cero |
| Recursos/veredictos → hard | Cobertura positiva completa o refutación certificada |
| Cuatro valoraciones/hard → decision | Ámbito común B0/B, pares, frontera y cobertura |
| G01–G15/frontera → selección/integración | Selector solo en su dominio y ausencia de selección correctamente justificada |
| Input/resultado → verifier | Recomposición de obligaciones, valores, cobertura y digest |

No hay una dependencia que permita a bienestar, tarea, hard o selección borrar futuros. Una dependencia incompleta conserva resultados independientes cuando su contrato lo permite; no convierte datos ausentes en cero o falsedad.

## Entorno efectivo

El código de referencia usa Python >=3.11 y biblioteca estándar. CPython 3.12. 14 es el entorno de ejecución observado en F2; no se afirma validación en otras plataformas. `fractions.Fraction` y enteros arbitrarios realizan aritmética exacta. El reloj operativo usa monotonic, sin introducir flotantes en los valores matemáticos.

Para evaluar y ejecutar pruebas desde kernel no se requieren red, instalación, GitHub, API externa ni credenciales. La instalación mediante pyproject es opcional si las herramientas de construcción ya están disponibles. Leer la fuente original requiere además un lector DOCX/OMML; consumir los contratos y derivados no exige convertirla de nuevo.

Sin opciones se registra el límite ambiental de recursión y no se impone otro presupuesto artificial. El tope decimal implícito de Python está desactivado. Las opciones operativas son max_nodes, max_operations, max_seconds, max_input_bytes y max_integer_digits. Esta última cuenta dígitos de numerales recibidos, sin signo ni separador, y no limita enteros derivados. El límite ambiental python_recursion_depth se captura antes de evaluar y figura en la salida. Un agotamiento devuelve LIMITED; el control de tiempo es cooperativo. El sistema operativo puede agotar memoria: no se promete interrupción dura ni rendimiento universal.

## Evidencia y continuidad

F1 está congelada en [baseline](../baseline/GENIUS_PHASE_1_HANDOFF); su ZIP original está en [history](../history/GENIUS_PHASE_1_HANDOFF.zip). Los 36 casos diseñados de F1 permanecen intactos. La evidencia F2 enlaza los 26 casos FP1 con tests; los casos de teoría general conservan sus límites documentales.

La recomputación del verificador comparte código de construcción. Tests con oráculos independientes, auditoría separada y receptor sin historia son dependencias de aceptación G2, no servicios del runtime. F3 fue abierta después de G2 con mandato propio; Benchmark y oráculos independientes ya fueron ejecutados.

Todo cambio de dependencia registra versión, dominio, motivo, riesgos y criterio de aceptación en [DECISIONS](DECISIONS.md) y [VERSIONING](VERSIONING.md). No altera silenciosamente Specification ni reescribe históricos.


## Dependencias activadas F3

G2 e integridad F2 fueron recibidos y reproducidos. Benchmark1.0.0 está aceptado para su alcance. G3 se sustentó en oráculos independientes, corpus exacto, clasificación de defectos, regresiones de Kernel1.0.1, medidas de seis ejes, auditoría y receptor separados. Estas dependencias de aceptación no agregan dependencias de runtime: Python/biblioteca estándar y archivos incluidos bastan. F4 está activada por el propietario. Añade Node para el consumidor, sin bibliotecas de terceros; versiones observadas Python3.12. 14 y Node24.19.0. G4 depende del expediente actual y F5 no se inicia por inferencia.
