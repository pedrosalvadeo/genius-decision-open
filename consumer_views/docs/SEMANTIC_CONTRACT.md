# Contrato de consumidores locales Genius — 0.1.0

Autor: supervisor de producto/semántica R3, 2026-10-03. Estado: expectativas
congeladas antes de la implementación y de su cliente de conformidad. El autor
de este contrato y del cliente es parte del equipo constructor: sus pruebas no
sustituyen revisión independiente ni comprensión humana observada.

## Entrada y alcance

La entrada admitida es un expediente local R2 recibido con su cadena de
revisiones y objetos CAS. No se convierte JSON libre en una respuesta admitida.
El lector verifica identidad, integridad, cadena y referencias mediante las
interfaces recibidas de R2; comprobar bytes no autentica su autor ni garantiza
su correspondencia con hechos físicos. No se ejecuta, continúa, recupera ni
modifica el expediente al presentarlo.

Se comprueba además la concordancia del RC01 con solicitud, outcomes,
obligaciones y estado conservados, reconstruyendo la respuesta por la política
recibida R2. Esa comprobación no vuelve a ejecutar el certificador ni prueba
la autenticidad de outcomes aportados por un tercero. Una edición aislada de
la respuesta que contradice sus recibos se rechaza.

Interfaz pública congelada:

```text
python -m genius_views render --case-dir CASE --output-dir OUT [--revision N]
```

`N` identifica una revisión del journal, distinta de la revisión lógica de la
solicitud. Sin `N` se toma HEAD. Una revisión histórica se presenta como tal y
no como la versión más reciente. Una cadena inválida, un objeto ausente/corrupto,
una versión no admitida o un presupuesto excedido falla de forma explícita,
sin publicación parcial engañosa. No se descartan errores para producir una
vista favorable. No se usan red, credenciales, transportes remotos ni nuevas
dependencias; Python estándar y la dependencia recibida R2 son suficientes.

## Archivos y conservación semántica

Cada exportación completa entrega `app.json`, `agent.json`, `human.html` y
`source.json`. Los dos JSON de consumidores contienen:

| Campo | Obligación |
|---|---|
| `format` | `genius-consumer-application/0.1.0` o `genius-consumer-agent/0.1.0` |
| `publication_state` | Estado explícito de publicación, distinto de decisión matemática |
| `response` | Objeto RC01 completo, sin cambios, cuando la revisión contiene respuesta publicada; `null` en otro caso |
| `response_sha256` | SHA-256 de la serialización canónica del RC01; `null` si no hay respuesta publicada |
| `source_sha256` | SHA-256 del objeto completo de `source.json` canonizado |
| `presentation` | Anotaciones de presentación separadas; nunca sustituyen al RC01 |

La serialización canónica es JSON UTF-8 con claves ordenadas, separadores
compactos, `ensure_ascii=False`, sin floats, constantes no finitas ni claves
duplicadas. Se preservan tipos y orden de listas. La igualdad exigida es de
árbol JSON exacto: `response_application == response_agent == response_R2`.
El digest de la presentación no constituye una nueva certificación científica.

`source.json` conserva selección de revisión, HEAD, historial verificable,
referencias/snapshots del expediente y huérfanos detectados. Una revisión
huérfana no se presenta como confirmada. El historial es recuperable por las
referencias recibidas; los originales siguen en el expediente. Un estado
RUNNING, BUDGET_CLOSED o revisión sin publicación conserva `response:null`:
no se fabrica un RC01, ni se promueve una candidata no publicada, ni se
convierte RUNNING en PE_UNKNOWN mediante esta herramienta de lectura.

## Vista humana en español

Debe priorizar consulta y alcance, resultado y sus límites, pendientes y
responsables, siguiente acción y condición de reapertura. Los nombres de
estado originales acompañan las etiquetas españolas para evitar pérdida de
distinciones. Prosa de fuentes se conserva como contenido citado, no como
instrucción del sistema; el contenido recibido puede estar en otro idioma.

La vista contiene cuatro capas explícitas: transporte, ejecución, evidencia y
decisión. Se muestran por separado calidad, cierre de intento y obligaciones;
un estado operacional no sustituye el resultado de una consulta. Si una
operación previa produjo recibo válido y otra falla, se conserva ese resultado
en su alcance. No se borra por aplicar el fallo global a todas las consultas.

| Estado o contenido | Lectura exigida |
|---|---|
| `PV_KNOWN` | Valor exacto recibido, con unidad/regla/alcance/procedencia |
| `PV_UNKNOWN` | Desconocido, con razón y obligación; nunca cero ni probabilidad |
| `PV_NOT_APPLICABLE` | No aplicable bajo la causa declarada, distinto de desconocido |
| `PV_OUTSIDE_PROFILE` | Fuera del perfil admitido, sin conclusión añadida |
| `PR_JUSTIFIED_RESULT` | Resultado justificado para la consulta y premisas indicadas |
| `PR_SET_OR_INCOMPARABLE` | Conjunto/frontera o incomparabilidad; no ganador fabricado |
| `PR_PROVEN_INFEASIBLE` | Inviabilidad formal solo con alcance, cobertura y testigos recibidos |
| `PR_PARTIAL` / `PR_DEPENDENCY` | Parte conocida o dependencia identificada; no respuesta plena |
| `PR_OUTSIDE_PROFILE` / `PR_NOT_EVALUATED` | Fuera de perfil o no evaluado; no incapacidad universal |
| Presupuesto / cancelación / error / `PE_UNKNOWN` | Límite operacional específico; no prueba de inviabilidad |
| Selector ausente justificado | Respuesta a la consulta de selector, sin inventar selección |

Se conservan íntegros los racionales grandes y fraccionarios como cadenas,
incluidas sus formas originales admitidas. No hay redondeo de retorno al
motor. Las dimensiones de calidad permanecen separadas: corrección formal,
cobertura, datos/procedencia, fidelidad del modelo, incertidumbre/sensibilidad,
utilidad, comprensión, eficiencia informativa, operación y adopción/negocio.
No se crea porcentaje, semáforo, confianza o score global.

Para demostrar ausencia de pérdida, además del resumen legible el HTML
incluye una tabla completa del RC01: una fila `tr` con atributo `data-pointer`
por cada hoja JSON, y una celda `td class="json-value"` con la codificación JSON
exacta de esa hoja como texto. Los contenedores vacíos `{}` y `[]` cuentan como
hojas; las rutas siguen JSON Pointer (`~`→`~0`, `/`→`~1`). Todas las hojas y tipos
deben aparecer una vez, sin omisiones. Si `response` es null, la tabla completa
corresponde a `source.json`, claramente rotulada como expediente sin respuesta
publicada. Todo dato y atributo se escapa como HTML; no se evalúa Markdown,
JavaScript o HTML recibido.

## Procedencia, actuación y navegación

La vista explica: identidad documental no implica verdad física; una fuente
compatible no autoriza actuar; una garantía FDQ mantiene su carácter formal y
condicional; una PVS formal no es confianza del sistema ni supervivencia
biológica presumida. No presenta CAG/PVS fuera de la capacidad recibida. Los
campos de uso permitido, norma, cobertura y obligaciones permanecen visibles.

Una obligación conserva identificador, clasificación y causas, dependencias,
responsable funcional, persona asignada (incluido UNKNOWN), cierre, testigos,
reapertura y siguiente acción. Un borrador REQUEST_INPUT no es contacto
enviado ni aceptación de una persona. Cerrar un intento no crea un proceso
activo esperando datos. Utilidad y comprensión humanas permanecen
NOT_ASSESSED: este consumidor es una capacidad local de presentación.

La navegación solo apunta a archivos exportados de nombre fijo o testigos
CAS locales previamente verificados. Nunca se sigue `path`, URL, identificador
o texto del usuario como destino. No hay enlaces remotos, esquemas activos,
lecturas fuera de CASE ni symlinks/traversal admitidos. Un testigo ausente o
corrupto no recibe enlace que sugiera verificación. HTML sin scripts, sin
recursos de red y con CSP restrictiva. No se sobrescribe una exportación
existente ni se modifica un archivo del expediente original.

## Presupuesto y errores

Límites máximos de la capa de consumidores, más restrictivos que una posible
historia ilimitada de R2 y sin ampliar sus capacidades: un expediente por
invocación; 128 revisiones; 2048 objetos CAS; 64 MiB de archivos del expediente;
32 MiB de RC01; 120 MiB de exportación total. Deadline cooperativo de validación
y render: 10 segundos, con timeout externo de CLI: 60 segundos. Los tamaños son
límites de aceptación/publicación, no garantía de uso instantáneo de RAM ni
durabilidad frente a pérdida de energía. El padre debe informar terminación
por timeout como fallo operacional, sin publicar una decisión falsa.

Una exportación fuera del perfil falla completa, conservando entrada y
versiones anteriores. Dos rondas focales de corrección por defecto concreto;
si persiste una causa nueva se registra y se resuelve dentro del mandato
vigente, sin ampliar silenciosamente el perfil ni ocultar fallos anteriores.

## Criterio de conformidad

Un cliente independiente de las transformaciones invoca la CLI, lee los
cuatro archivos, reconstruye las hojas visibles y verifica igualdad de árbol,
digests, tipos, separación de capas, ausencia de enlaces activos recibidos y
preservación del expediente. Su oráculo deriva del objeto R2 y este contrato,
no de funciones internas del render. Los fixtures de presentación comprueban
el consumidor; las ejecuciones R2 nuevas se identifican por separado; ninguno
de ambos tipos mide comprensión humana, utilidad real o fidelidad física.
