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

# Gobernanza del programa Genius

Norma heredada de F0–F2 y aplicada a F3. Fuente de objetivo: [S0](theory/sources/S0_FASE_0_MANDATE.md); mandato actual: [PHASE_4_MANDATE](../PHASE_4_MANDATE.md). Las reglas de proceso no agregan axiomas ni convierten una revisión documental en demostración matemática.

## Autoridad por ámbito

| Ámbito | Autoridad | Límite |
|---|---|---|
| Objetivo, alcance y decisiones reservadas | Mandato del propietario | No convierte una proposición falsa en verdadera |
| Validez matemática | Definiciones, hipótesis y pruebas de la instantánea identificada | Un rótulo de cierre no sustituye argumento; S1 preservada, cambios en AMENDMENTS |
| Estado del programa | MASTER_STATE con informes y registros vinculados | Resume evidencia; no modifica fuentes ni concede aceptación por sí solo |
| Contrato computacional | Specification versionada aceptada y perfil | Un alcance de ingeniería más estrecho debe declararse; no reforma teoría tácitamente |
| Conformidad | Casos derivados de cláusulas y resultados reproducibles | Un test puede estar mal; pasar tests no redefine el contrato |
| Software | Implementación y expediente de ejecución | Kernel es una realización, no una definición retroactiva de matemática |
| Protocolos/productos | Contratos compatibles con versiones | No amplían garantías científicas |
| Claims empíricos | Datos, protocolo, métodos y resultados | Sintéticos y prueba formal no acreditan utilidad real |
| Aceptación de fase | Informe de aceptación con auditoría y recepción | Solo para criterios y alcance revisados |

La relación de refinamiento es teoría→Specification→implementación→interfaces/productos. Pruebas y gobernanza verifican ese refinamiento; no se sitúan por encima de la matemática. Si un resumen contradice su fuente o dos contratos discrepan, registrar y resolver: no elegir automáticamente el más reciente o favorable.

## Roles y separación de aceptación

| Función | Responsabilidad |
|---|---|
| Propietario | Objetivos, preferencias no recuperables, titularidad/licencia, publicación, inversiones y compromisos externos |
| Integrador | Estado maestro, coherencia, gates, invariantes, versiones y handoff; no autocertifica toda su entrega |
| Formalizadores | Pruebas, contraejemplos, tipos y contrato; distinguen notación, reparación e hipótesis |
| Conformidad/implementación | Casos, algoritmos y reproducción según fase; no alteran autoridad del contrato |
| Custodio | Identificadores, manifiestos, compatibilidad e historia inmutable |
| Auditor separado | Refuta candidata, clasifica hallazgos y revisa correcciones; no es autor principal del objeto auditado |
| Receptor sin historia | Comprueba continuidad usando solo paquete y puede rechazar insumos insuficientes |

Roles de creación compatibles pueden combinarse. La auditoría y recepción deben estar funcionalmente separadas del equipo autor. Agentes del mismo entorno aportan independencia funcional/contextual interna, no revisión externa institucional ni independencia de proveedor; el informe registra configuración y límites. El gate requiere evidencia revisora y decisión motivada del Integrador, no solo «terminado» del autor.

## Estados y evidencia

CONFIRMED significa verificado **para un alcance explícito**; PROVISIONAL es propuesta con restricciones; UNRESOLVED conserva un vacío; EMPIRICAL exige observación; DEPRECATED desaconseja uso nuevo; SUPERSEDED identifica sustitución. «La fuente contiene una prueba» difiere de «la prueba fue revisada», y ambas difieren de «una implementación pasó casos». Existencia del componente, compatibilidad y aceptación de fase son ejes distintos.

F4 requiere consumidor independiente, pruebas de intercambio, auditoría separada y recepción sin historia; el estado efectivo G4 reside en [MASTER_STATE](MASTER_STATE.md) y el informe raíz. Los valores definidos, pertenencia al dominio, conocimiento, validez de presentación, evidencia, ejecución y cobertura siguen separados por el contrato 06. Un booleano «fiel» no demuestra adecuación empírica.

## Proceso de cambio y discrepancia

1. Registrar problema, fuentes, versiones, testigo/contraejemplo y dependencias afectadas.
2. Clasificar en BLOCKERS: BLOCKER con gate concreto, MAJOR ISSUE, MINOR ISSUE, OPEN QUESTION o EMPIRICAL UNKNOWN. Una extensión fuera de FP1 no bloquea su contrato si queda explícita.
3. Congelar solo claims y dependencias afectados; conservar evidencia anterior.
4. Analizar alternativas y registrar ADR con fecha, evidencia, decisión, consecuencias y reversibilidad.
5. Si cambia matemática, registrar en AMENDMENTS y nueva instantánea; si cambia contrato, versionar Specification. Nunca reparar silenciosamente DOCX o tests para que encajen.
6. Actualizar trazabilidad, casos, compatibilidad y documentos dependientes. Repetir comprobaciones cuya premisa cambió.
7. Auditor separado revisa la reparación; Integrador decide efecto sobre gate. Desacuerdo técnico persistente permanece abierto y puede requerir tercera revisión; no se cierra por votación o autoridad del modelo.

Un fallo de código se corrige en código salvo que se demuestre fallo del contrato. Un fallo de benchmark no se esconde cambiando métricas después del resultado. La selección normativa pertenece a la regla declarada; ningún software añade pesos, prioridades o compensación entre portadores sin autorización.

## Autonomía, reservas y continuidad

El mandato F4 autoriza diseñar y ejecutar experimentos, intentar refutar, reparar, integrar, auditar y preparar archivos portables. Decisiones técnicas reversibles dentro de ese alcance se resuelven y registran sin pedir permiso repetido. La aparición de un bloqueador exige trabajar en su reparación, no abandonar la fase automáticamente.

El cierre G4 no inicia por inercia F5 ni autoriza publicación, licencia, contratación, pagos, despliegue o acciones sobre terceros. Esas acciones se rigen por mandato aplicable y permisos reales. Las preguntas normativas no imprescindibles pueden quedar como parámetros explícitos. GitHub no es requisito para F4; su eventual migración debe registrar evidencia y conservar el histórico.

Diversidad Universal sigue separada. No se atribuye originalidad sin revisión específica, ni utilidad empírica sin datos. Hallazgos negativos, limitaciones y reparaciones acompañan cada release conforme a [VERSIONING](VERSIONING.md) y [TRANSFER_PROTOCOL](TRANSFER_PROTOCOL.md).
