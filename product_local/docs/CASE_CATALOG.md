# R2 — casos de conformidad del consumidor local

Autor: `/root/r2_conformance`, supervisión autoral `/root/r2_b_supervisor`. Estos casos son trabajo de autoría; su ejecución no sustituye XG/XT/XU no autoras. El estado ejecutado y las revisiones de fallos se registran en `TEST_RESULTS` de la entrega y en los logs conservados. Este catálogo no declara aprobación antes de ejecutar.

## Qué representa cada fuente

`examples/b01_diagnostic_expectations.json` transcribe clasificación y límites de R0 `analysis/DOMAIN_EVIDENCE.md` §§2/4, con identidad del ZIP recibido. No abre ni recuenta calendarios hospitalarios. D1/horas se prueban con un registro sintético de créditos contractuales; consentimiento, historia, personas, CAG y tarea siguen dependencias explícitas. H13/H14/D4 reutilizan sólo el diagnóstico documentado para su alcance inspeccionado.

`examples/fdq/{historical,welfare,priority,none,unique}/{input,original_result}.json` conserva bytes de R1. Sus certificados de prueba restringen de forma declarada Γ a los extremos primero/último (o conservan la Γ2 recibida). La familia se define desde entradas. `PROVENANCE.json` registra copias y mutaciones; no acredita pertenencia de un caso físico ni produce probabilidades sobre Γ. La variante adicional `infeasible` modifica explícitamente recursos y límite en un Input sintético: p/s consumen 1, q consume 2, y el límite es 0. Su Result original se genera con el Kernel recibido exclusivamente como artefacto de entrada requerido por FDQ; la expectativa de refutación de toda Π se fija mediante el argumento independiente 1>0 y 2>0, descrito en `EXPECTED_PROOF.json`.

`tests/test_acceptance.py` ejecuta la CLI pública en expedientes temporales nuevos. Las respuestas esperadas están fijadas por ejemplos aritméticos y contratos, sin importar módulos de producción para obtenerlas. `tests/independent_client.py` tampoco importa el Kernel ni `genius_local`: verifica capas, variantes de ausencia, referencias y bytes del historial. Es un consumidor adversarial finito, no un validador completo de toda gramática ni autenticador empírico.

## Matriz de comportamiento

| Familia | Testigo esperado y límite |
|---|---|
| Horas exactas | 13/2 + 15/2 = 14/1; exceso/déficit 0/1. Créditos contractuales no prueban descanso físico, presencia ni consentimiento. |
| Exactitud grande | 9007199254740993/1 + 1/3 = 27021597764222980/3, sin paso por float. |
| Ausencia | Crédito desconocido conserva `PV_UNKNOWN`, razones y obligación; no se reemplaza por cero. |
| D1 reutilizable | Puntero al valor recibido, permisos declarados y cinco ejes; se conservan la copia parcial original y la fuente sintética, ambas por bytes. |
| Cinco ejes | Un desajuste de identidad, unidad, período, población o método impide sustitución aunque los otros cuatro coincidan y el cliente escriba MATCH. |
| Incertidumbre de fuente | Método sin base produce `SC_UNRESOLVED`; permisos UNKNOWN impiden uso; un conflicto conserva ambas fuentes y no calcula promedio. |
| Nueve causas | Registro separado de las nueve causas recibidas, sin cierre por etiqueta y sin pedir al consumidor producir matemática terminada. |
| D4/H13/H14 | Diagnóstico recibido ligado por hash y propósito `RECEIVED_DIAGNOSIS_ONLY`; una consulta hospitalaria futura no hereda esa irrelevancia. |
| Hechos y norma | Consentimiento, historia, identidad física, falta irrecuperable y preferencia generan dependencia/pregunta local con opción desconocido, sin contacto real. |
| Modelo CAG/origen/tarea | Ampliar una descripción conserva pendientes; no admite catálogo, cero inicial ni predicado por prosa. |
| FDQ positivo | Consulta exacta sobre Γ2, entrada/Result intactos, suficiencia externa condicional. El Result parcial mantiene RELATIVE y selector OUTSIDE_DOMAIN. |
| FDQ adversos públicos | Familia vacía, alternativa factible omitida, claim falsa, índice/constraint inexistentes, calibración que rompe orden, query distinta: sin decisión favorable ni inviabilidad fabricada. |
| Ataques de dependencias congeladas | Mutaciones de calibración común, traducción, soporte, interfaz, ley conjunta y norma se conservan como fixtures adversarios del contrato R1. R2 no tiene parámetro de miembros libres; su rechazo por formato evita una extensión silenciosa. La suite R1 ejecutada por recepción verifica esos ataques sobre el verificador recibido. |
| Selector y frontera | Frontera fija no basta para elegir cuando cambia norma. Las familias none/unique/priority conservan la diferencia y el conjunto no obliga a inventar preferencia. |
| Ausencia de selector | La consulta exacta de selector none/unique puede responder `PR_JUSTIFIED_RESULT` con OUTSIDE_DOMAIN y causa SELECTION_DISABLED/SELECTION_NOT_UNIQUE. Ese estado producto no fabrica una política seleccionada ni una frontera no solicitada. |
| Inviabilidad positiva | La variante sintética de presupuesto cero verifica refutación de p/q/s en ambos miembros, con cobertura de Γ y testigos; ninguna frontera vacía ni fallo operacional sustituye esa evidencia. |
| Cierre y DAG | Sólo el predicado operacional recibido puede cerrar una obligación; una frase de utilidad empírica o una dependencia de modelo abierta conserva el pendiente. |
| Presupuesto/cancelación | Presupuesto cero y cancelación cooperativa explican falta de ejecución; ninguno prueba inviabilidad. |
| Reinicio/continuación | Nuevo proceso reconstruye HEAD/cadena/bytes y serializaciones por chunks; una corrupción no se ignora. Un nuevo turno sin novedad no autoriza recálculo; un crédito antes ausente permite nueva revisión ligada. |
| Reutilización entre revisiones | Nueva consulta independiente permite continuar; el resultado anterior exacto se recupera con LOCAL_RECEIPT_REUSE y `new_computation:false`. Un cambio de crédito invalida ese recibo y produce el nuevo valor exacto. |
| Respuesta parcial útil | Créditos conocidos y objetivo desconocido conservan assigned=14/1 y desconocidos para exceso/déficit, con PR_PARTIAL. Un presupuesto agotado después de horas no borra la respuesta independiente ya verificada. |
| Cliente adversarial | Rechaza score global, inviabilidad sin cobertura/testigos, decisión ligada a consulta inexistente, desconocido con valor y versión de respuesta no soportada. |

## Reproducción portable

Desde el directorio de implementación, proporcionar las dos dependencias recibidas por variables de entorno:

```bash
GENIUS_R1_BASELINE=/ruta/R1 GENIUS_R0_BASELINE=/ruta/R0 python3 -B -m unittest discover -s tests -p test_acceptance.py -v
```

Los directorios temporales se eliminan al finalizar cada caso; los logs de ejecución completos se conservan en la entrega. Los ejemplos FDQ pueden reconstruirse sólo desde R1 mediante:

```bash
python3 examples/build_fdq_fixtures.py /ruta/R1 /carpeta/nueva/fdq
```

Para reconstruir también la variante sintética de inviabilidad se agrega `/ruta/R0` como tercer argumento. Esto genera el Result de entrada con el Kernel recibido; no obtiene expectativas de R2. Los dos ejemplos completos `examples/hours/request.json` y `examples/fdq_selector/request.json` se ejecutan con `python3 -B -m genius_local run --request <ruta_del_request> --case <carpeta_nueva> --r1 /ruta/R1 --baseline /ruta/R0` desde el directorio de implementación.

## Historia de desarrollo de esta autoría

El último ensayo autoral ejecutó **31 métodos públicos, todos PASS**, el 2026-10-03, en 10,015 segundos. Log: `acceptance_development_03.log` (conservado en los resultados de integración). Son 31 métodos con subcasos parametrizados explícitos; no se suman sus asserts como pruebas independientes ni se confunden con usuarios o evaluaciones empíricas. La corrida final integrada del supervisor y la recepción no autora se registran por separado.

- `acceptance_development_01.log`: 22 métodos, un fallo real del sobre. Una operación de horas desconocidas devolvía dependencia, pero su celda y razones se perdían al filtrar los providers no positivos. Se reparó conservando `observed_values`, sin ascender unknown a respuesta acreditada.
- `acceptance_development_02.log`: 29 métodos, dos fallos de desarrollo. El cliente buscaba el ledger en el payload anterior y se adaptó para reconstruir referencias CAS por bytes/digest. El primer fixture de inviabilidad usó límite −1, fuera de la presentación FP1 admitida: el rechazo de producción fue correcto. La propuesta y su resultado se conservaron en `infeasible_probe`; el fixture válido usa consumos 1/2 y límite 0.
- `acceptance_development_03.log`: 31 métodos PASS después de las correcciones y de vincular la descripción de FDQ al Input completo y la consulta exacta. No se relajó la expectativa de preservar desconocidos. Los cambios de contrato operacional y las correcciones autorales ocurrieron antes de congelar la candidata para revisión independiente.

Límite de independencia: estas pruebas son autorales y el cliente es independiente de los módulos de producción por código/imports y expectativas. El constructor de un Result FP1 sintético usa el Kernel recibido como exige el contrato de entrada; el juicio esperado se fija aparte. Ninguna de estas propiedades convierte esta autoría en auditoría no autora.

Las expectativas del cliente son deliberadamente limitadas: no prueban autenticidad de una fuente, veracidad de permisos declarados, calidad empírica, comprensión humana, adopción o utilidad. Tampoco implementan un adaptador agronómico, transporte R3, UI ni aprobación G6A.
