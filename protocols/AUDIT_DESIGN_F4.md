# Diseño previo de auditoría separada F4

Autor: función `f4_audit`, distinta de los autores del contrato, adaptador y
consumidor. Autoridad: GENIUS-SPEC-1.0.0, Specification 00–06, S2 con
AM-01–04 y mandato F4. La revisión no modifica Kernel, Benchmark ni baseline.
La aceptación auditora no sustituye recepción separada ni decisión del Integrador.

## Método independiente

Se construye desde cero `tests/audit_fixture.py`, sin importar sujetos, módulos
de los otros autores ni fixtures heredados. La topología H=1 tiene una raíz y
dos hojas que reconvergen al mismo estado e información. Conservan consultas,
escenarios, bienestar y veredictos propios. Se repite la cadena `same` en varios
espacios nominales para comprobar que no se fusionen. Una premisa sintética
incluye caracteres no ASCII y una secuencia Unicode descompuesta. Los racionales
incluyen 9007199254740993/1 y ±9007199254740993/9007199254740992, sin conversión
flotante. Un recurso por ocurrencia vale 1/3 y su cota instantánea es 1/3.

La ley da masa uno a la hoja positiva y cero a la negativa: PVS=1, pero la
hoja negativa permanece en causalidad, evidencia y restricciones universales.
La política única es factible bajo presupuesto y seleccionable en la instancia
completa. Añadir `task_all` la refuta sin borrar futuros; omitir la medición de
bienestar de la hoja nula produce frontera RELATIVE sin selección, manteniendo
PVS y objetos independientes. Omitir la actualización informacional impide
construir hojas terminales, sin inventarlas. Una ley presente de suma incorrecta
bloquea los objetos probabilísticos sin convertirse en presentación inválida.
Estas proyecciones se derivan de las definiciones, no del valor que devuelva
el sujeto.

Los certificados externos se construyen directamente: lectura exacta de cada
hoja, signo 0 o 1, A canónico o superset positivo `{yes,extra}` de Sem=`{yes}`.
Se exige admisión de controles positivos y rechazo de mutaciones de digest,
cobertura, dominio, signo y task rows. El certificado no se copia del evaluador.
Las mutaciones de Result parten de un Result legítimo y contradicen un requisito
concreto: omisión de hoja nula, racional alterado, selección fuera de cobertura,
cambio de versión o digest. El verificador del Kernel sigue compartiendo
constructores con evaluate; su invocación por transporte no se cuenta como
segundo Kernel independiente.

## Contrato wire y congelación

Aún no se fijan expectativas wire en esta revisión inicial: el diseñador está
cerrando nombres, estados y códigos. Antes de ejecutar, este diseño se completará
contra el contrato publicado, identificando negociación, framing, límites,
notificaciones, batches y EOF. Las fuentes, contrato, diseño y pruebas se
hashearán antes/después de cada corrida; una edición concurrente impide usarla
como evidencia final. No se ejecutan cargas durante la reproducción F3 serial.

Los resultados negativos y errores del experimento se conservan en salida nueva;
la discrepancia se clasifica frente a la norma, sin cambiar expectativas para
obtener PASS. No hay aleatoriedad ni medición de rendimiento. El alcance es
finito y local: no prueba ausencia universal de defectos, seguridad de servicio
público, veracidad de premisas ni compatibilidad con protocolos no implementados.

## Revisión 2 — expectativas wire fijadas antes de ejecución

Tras publicarse CONTRACT P01–P09, se fija `tests/audit_blackbox.py` como ejecutor
independiente. Inicia `python -m genius_protocols` en otro proceso con
`PYTHONPATH=kernel:protocols`, escribe/lee bytes y no importa módulos del sujeto.
Cada caso guarda frames completos, stdout/stderr y expected/actual por check en
carpeta nueva. Los SHA-256 antes/después cubren contrato, diseño, pruebas,
adaptador y Kernel. La primera corrida será `validation/audit_runs/AUDIT_DRAFT_01`;
la corrida final deberá quedar congelada y ser reproducible con `--out` nuevo.

| IDs | Obligación y oráculo previo |
|---|---|
| AUD4-SEM-001/002 | Proyección sintética completa, hoja nula, parcialidad de bienestar, ley inválida frente a presentación, causalidad incompleta |
| AUD4-ID-001 | Input compacto/pretty matemáticamente equivalente, digest distinto, rechazo de certificado vinculado a otros bytes |
| AUD4-NEG-001 | Negociación antes de Kernel, versión/capacidad incompatibles, oferta mixta compatible, identidades completas y renegociación prohibida |
| AUD4-NOT-001 | Notification initialize no cambia sesión; otras no ejecutan ni responden; objeto sin id inválido produce Invalid Request |
| AUD4-BAT-001 | Batch vacío, 16/17 elementos, mezcla de Requests/notificaciones/elementos inválidos y correlación por id |
| AUD4-RPC-001–010 / REQ-001–003 | IDs exactos permitidos/prohibidos; exponentes y floats no se convierten; estructura cerrada |
| AUD4-PAR-001–009 | Duplicados incluso escapados, UTF-8, BOM, NaN/Infinity, surrogate aislado, sintaxis y recuperación al próximo LF |
| AUD4-FRM-001 | CRLF, fragmentación, EOF sin LF aunque JSON completo, frame exactamente 16 MiB y exceso con cierre |
| AUD4-BLOB-001–006 | Base64 canónico incluidos padbits, padding/whitespace, digest exacto/minúscula y campos extra |
| AUD4-LIM-001–009 | LimitMap tipos/canonicalidad, cinco límites cooperativos, nodos 2/3, bytes exactos y topes wire input 2 MiB/candidate 8 MiB |
| AUD4-INP-001–006 | Blob correcto con bytes FP1 inválidos conserva exactitud y llega como Result INVALID, no error RPC |
| AUD4-CER-001/002 | Certificados handmade positivos y negativos; sintaxis antes que tipo numérico; numeral 100001 dígitos sin convertirlo |
| AUD4-RES-001 | Result completo positivo; mutaciones de digest, formato, hojas nulas, racional, cobertura y premisas rechazadas |

La política de notificaciones es una restricción explícita de este perfil
basado en estructuras JSON-RPC 2.0; no se acredita un servidor JSON-RPC genérico.
La auditoría compara exactamente los códigos/mensajes de P08. Los fallos de
transporte no fabrican Result ERROR ni LIMITED. La cancelación por terminación
y el límite agregado de respuesta serán revisados también en el consumidor;
no se reclama cobertura ejecutada hasta disponer de resultados específicos.

## Revisión 3 — pares adversariales del consumidor

Antes de ejecutar `tests/audit_consumer.mjs` se añaden AUD4-CON-001–015: decoder
base64 canónico hasta 2 MiB; parser UTF-8, duplicados, BOM, surrogate y entero
inseguro; control positivo de transmisión de ERROR como estado de Result; peer
local con versión/capacidad incorrecta que no debe recibir ninguna instancia;
echo, digest de blob o binding Result alterado; response con duplicate keys,
id extranjero, UTF-8 inválido o EOF sin LF; cancelación y timeout local mientras
el peer mantiene la solicitud pendiente. Los dos últimos deben terminar sesión
y conservar categoría de fallo de transporte, sin fabricar Result LIMITED.

El peer sintético del auditor no ejecuta Kernel. Su Result ERROR de control sirve
solo para revisar la envoltura y preservación del estado; no se presenta como
certificado matemático válido. El consumidor hace validaciones de envoltura y
forma mínima; la verificación sustantiva de un Result requiere verify_result.
Este diseño no exige implementar un segundo Kernel dentro del consumidor.

## Revisión 4 — fallo controlado y cota de salida real

Se preregistra `tests/audit_faults.py`, AUD4-FAULT-001–005. Inyecta respuestas o
excepción en la API Kernel que consume el adaptador, conservando su código:
RuntimeError debe dar -32603; un objeto artificial con execution.ERROR permanece
dentro del resultado RPC; carga de serialización exactamente 33554432 bytes se
entrega, tres caracteres de payload adicionales producen -32003; batch de
catorce resultados amplios, una notificación y un elemento inválido excede la
cota agregada y sustituye todas las respuestas por -32003 conservando IDs/null.
El contador confirma que la notificación no invocó API; tras cota la sesión
permanece READY. Esta evidencia verifica los límites y traducción de errores
**por inyección explícita**, no un fallo real del Kernel ni el coste de resolver
una instancia grande. No se mezcla con los tests negros de significado.
