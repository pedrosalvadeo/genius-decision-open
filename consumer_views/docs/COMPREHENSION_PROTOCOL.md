# Material preparado para evaluar comprensión — R3 0.1.0

Estado: **PREPARADO, NO EJECUTADO**. No hay participantes reclutados, respuestas
humanas observadas, métricas calculadas ni conclusión de utilidad. Este
protocolo es un material propuesto para la fase empírica; no reemplaza sus
criterios del Plan Maestro ni constituye aprobación de G6A. Autor: equipo
constructor R3, 2026-10-03. No usar agentes como participantes humanos.

## Pregunta y límites

¿Una persona destinataria puede explicar qué concluye una respuesta Genius,
bajo qué premisas, qué queda pendiente, quién debe aportar qué y por qué esa
respuesta no autoriza una intervención física? La prueba se limita a lectura
y elección de una próxima acción documental. No se mide resultado de una
intervención, rendimiento agronómico, bienestar real o fidelidad causal.

Las pruebas automáticas del cliente verifican conservación de información y
seguridad de presentación. Una persona puede entender mal una vista sin
pérdida; por eso ninguna prueba automatizada satisface esta pregunta humana.
Aplicaciones y agentes tienen pruebas técnicas separadas, sin agregarlas a
un tamaño de muestra de personas.

## Diseño propuesto y material que debe fijarse antes de observar

Sesión individual exploratoria sobre HTML local, sin acceso a redes ni a datos
personales de terceros. **Duración, tamaño y composición de muestra, estrategia
de selección, precisión exigida y umbral de aceptación: PENDIENTES DE
JUSTIFICACIÓN METODOLÓGICA PARA EL CASO ADMITIDO.** El responsable de métodos
debe derivarlos del público concreto, objetivo de observación, variabilidad,
riesgo de error y criterio vigente del Plan Maestro antes del reclutamiento
o la primera observación. No se asignan cifras por disponibilidad ni se
adaptan a los resultados obtenidos. Una muestra exploratoria de conveniencia
no autoriza por sí sola generalización al mercado o afirmación estadística.

No se envían invitaciones con este documento. La ejecución requiere personas
reales disponibles, consentimiento para la actividad y tratamiento de sus
respuestas, y un responsable humano. Registrar códigos P01… sin identificar
personas en el repositorio. Si alguien no consiente, no generar datos en su
nombre. Cualquier grabación requiere consentimiento específico; por defecto
se usan notas textuales desidentificadas. La persona puede retirarse.

Antes de observar se fija: versión/commit del consumidor, SHA-256 de cada
`human.html`, expediente fuente y respuesta, orden de casos, consigna,
preguntas, rúbrica, responsable de observación y evaluación, público objetivo,
criterio vigente del gate y autorización de tratamiento. Dos evaluadores
humanos codifican por separado, o se declara explícitamente que hubo uno.
No se presenta doble codificación si el mismo agente/persona hizo ambas.

## Casos y respuestas esperadas, congelados para el ensayo

Los ejemplos son estipulaciones/ejercicios. El caso real del estudio requiere
el modelo, datos, preferencias y reglas de pertenencia efectivamente
admitidos. No se traslada la conclusión de horas contractuales a descanso
físico ni FDQ a supervivencia de macetas.

| Caso | Pregunta de comprensión | Respuesta conceptualmente correcta |
|---|---|---|
| A. Horas contractuales exactas | ¿Qué se sabe y qué se puede afirmar de la presencia física? | Se conoce la suma bajo la regla contractual; la presencia física no queda probada |
| B. Dato desconocido | ¿Qué valor usarías y qué falta para continuar? | Mantener desconocido, identificar la obligación y responsable; no imputar cero ni inventar probabilidad |
| C. FDQ, conjunto sin selector | ¿Hay un ganador y a qué sistemas aplica el certificado? | Hay conjunto/frontera según la consulta; sin selector no se elige ganador, y la garantía depende de la familia formal declarada |
| D. Conflicto de fuentes | ¿Se puede tomar el número más favorable? | Conservar el conflicto, reconocer la dependencia y revalidar; no elegir por conveniencia |
| E. Resultado previo y operación interrumpida | ¿Qué sigue siendo válido y qué quedó sin terminar? | El recibo previo mantiene su alcance; la otra operación conserva su estado desconocido/cancelado/error/presupuesto |
| F. Cierre local con dependencia | ¿El sistema sigue trabajando y qué reabre el expediente? | No hay proceso automático implícito; un cambio pertinente y revisión enlazada pueden reabrirlo |

Para cada caso la persona responde en sus palabras: (1) qué consulta recibió,
(2) qué concluye, (3) qué no concluye, (4) qué dato/regla/acción sigue y quién
debe aportarlo, (5) qué evidencia localizaría y (6) si actuaría físicamente
con esa información y por qué. El moderador no corrige durante la primera
respuesta. Puede preguntar «¿En qué parte de la vista te apoyás?» sin señalar
la respuesta correcta. Después se permite una revisión libre y se registra
por separado la respuesta corregida espontáneamente.

## Rúbrica preparada

Por caso y pregunta: `2 = correcta sin ayuda`, `1 = parcialmente correcta o
correcta después de ayuda`, `0 = incorrecta`, `NA = no observada/retiro/fallo
técnico`. Conservar texto literal desidentificado y ubicación consultada.
Tiempo se registra desde apertura hasta primera respuesta completa; no
atribuir a Genius ahorro de tiempo sin comparador y protocolo específico.

Errores críticos: convertir desconocido en cero/probabilidad, interpretar
presupuesto como inviabilidad, fabricar seleccionado desde una frontera,
confundir garantía formal con verdad física/permiso de intervención, o borrar
un resultado recibido porque otra operación falló. Se registran por persona
y caso con testigo textual. Una nota del moderador no reemplaza el testigo.

El umbral de aceptación y la regla para errores críticos quedan **PENDIENTES**
hasta que métodos los justifique para el caso y los vincule al criterio
vigente del gate. Informar numeradores y denominadores, no solo porcentajes.
`NA` no cuenta como acierto; si faltan personas/casos previstos debe declararse
el desvío y aplicarse la regla de datos incompletos fijada antes del ensayo.
Sin esos parámetros definidos no se inicia el reclutamiento ni se declara
aprobación. La rúbrica preparada no crea un criterio nuevo de cierre de F6A.

Si hay un error crítico se abre un defecto de producto, se conserva el HTML y
respuesta originales, se corrige la vista y se repite con material versionado;
no se reescribe el resultado original como aprobado. La exposición previa
es una fuente de aprendizaje: declararla y usar participantes nuevos cuando
se pretenda evaluar comprensión inicial de la versión corregida.

## Plantilla de registro vacía

```text
Estado: NO_EJECUTADO
Sesión / código participante:
Consentimiento constatado / fecha / responsable:
Público y experiencia declarados:
Commit / SHA256 HTML / SHA256 respuesta / revisión expediente:
Caso / orden / pregunta:
Respuesta literal desidentificada:
Ubicación citada en la vista:
Respuesta inicial / ayuda dada / respuesta posterior:
Puntaje inicial / puntaje posterior / evaluador:
Error crítico y evidencia textual:
Tiempo observado y método:
Incidencia técnica / retiro / dato ausente:
```

## Informe posterior requerido

El informe debe indicar participantes reales y exclusiones, muestra prevista
y observada, preguntas válidas, respuestas correctas sin/con ayuda, errores
críticos, desacuerdos de codificación y limitaciones. Publicar solo material
desidentificado autorizado; preservar trazabilidad del consentimiento fuera
del código si contiene datos personales. Separar: comprensión de esta vista,
utilidad de la tarea para ese público y resultados del sistema en el dominio.
No hay inferencia automática entre esas tres cosas.

Un resultado favorable en ejercicios formales únicamente justificaría
continuar evaluando esta interfaz para el contexto efectivamente observado. No acredita
validación física, demanda comercial, adopción, generalización estadística o
cierre de G6A por sí solo. Un estudio de utilidad real necesita, además,
usuarios y caso admitidos, comparador pertinente, objetivos observables y
datos de resultados; no se fabrica ese vínculo para cerrar una fase.
