# D1 · Recorrido humano del gemelo dinámico

La aplicación local implementa la propuesta v2 con HTML, CSS y JavaScript sin dependencias de interfaz, CDN, llamadas externas ni contenido generado por un proveedor remoto. El navegador recibe los datos del adaptador Flask del mismo origen. El laboratorio se identifica de forma permanente como sintético; no promete interpretar cualquier decisión ni estimar supervivencia empírica.

## Recorrido implementado

1. **Entrada.** Un relato libre se conserva en el expediente. El botón «Usar relato de ejemplo» solo completa texto; no inyecta resultados. El servicio decide la admisión. Un dominio no admitido muestra la obligación de modelización y mantiene el relato, sin inventar un gemelo.
2. **Revisión.** Presenta la propuesta, cambios materiales, portadores, frontera, horizonte, recursos y políticas. Se requieren tres confirmaciones de alcance, carácter sintético y disponibilidad estipulada. La confirmación autoriza usar el modelo, sin convertir sus hipótesis en observaciones.
3. **Gemelo.** Mapa y lista describen los mismos participantes, recursos y relaciones. No hace falta usar un grafo para completar el recorrido. Se explica el monitor persistente de fallos y se puede solicitar la evaluación de la versión confirmada.
4. **Futuros.** Lee `canonical_results.policies` de la evaluación. Muestra ley conjunta, PVS y masas exactas, CAG acc posible/robusto y tiempos A/B por escenario. Política, escenario y día son seleccionables. Hay estados destacados de los días 10, 11 y 14 y una tabla completa de los días 0–14. El bienestar se presenta como condiciones por portador/día, sin sumar minutos como bienestar total.
5. **Conclusión.** Usa `canonical_results.decision`: factibilidad, frontera, selección, norma y modo de CAG. Una selección nula se conserva. La interfaz no fuerza un ganador. Una versión que requiere revisar una discrepancia muestra recomendación suspendida, incluso después de recalcular.
6. **Cambios.** Admite propuesta de relevo E→E′ en lenguaje natural, preferencias explícitas, corrección estructurada de la ley y restauración. Cada aceptación crea versión; se reevalúa íntegramente antes de mostrar resultados. La comparación muestra E/E′, PVS, CAG, agua y carga A/B en HA, además de las conclusiones de cada versión. Las advertencias de revisión se conservan por lado.
7. **Evidencia.** Se registra una observación de agua con política, escenario, día, fecha/hora, valor exacto, fuente y contexto. Se confirma su carácter declarado. El contraste muestra predicción congelada, dato declarado, diferencia exacta, versión y temporalidad. No se recalibra ni se valida el modelo por una coincidencia.
8. **Continuidad y consumidores.** El expediente puede descargarse como JSON; el resultado canónico y los metadatos son inspeccionables. La vista humana utiliza los mismos datos del consumidor estructurado. El identificador del último expediente se guarda opcionalmente en el almacenamiento local del navegador para recuperarlo. Los expedientes, versiones y resultados pertenecen al servicio local, no al almacenamiento del navegador.

## Contrato de presentación

| Dato | Origen de la pantalla |
|---|---|
| Políticas y horizonte | Versión confirmada del modelo |
| Ley conjunta | `model.law` |
| PVS exacta | `policies[id].pvs.value` |
| Éxito, fallo, indecisión | `policies[id].pvs.masses` |
| CAG acc posible/robusto | `policies[id].cag` |
| Tiempo, agua y monitor diarios | `policies[id].trajectories[scenario].daily` |
| Totales por portador | `policies[id].trajectories[scenario].totals` |
| Evento terminal | `policies[id].endpoint_probability.value` |
| Factibilidad, frontera y selección | `canonical_results.decision` |
| Suspensión | Metadatos `review_required` de la versión y admisión del trabajo |
| Contraste | Registro de observación y su `comparison` |

Los textos de entidades y relaciones son explicaciones del único perfil admitido. No hay resultados numéricos precargados en el JavaScript. Las magnitudes mostradas vienen del servidor; los identificadores de días destacados y la prosa de ejemplo son decisiones de presentación. Las fracciones permanecen exactas. Un valor ausente se distingue de cero y `null` se muestra explícitamente cuando corresponde. `PV_UNKNOWN` se explica como estado de valor del producto, diferente de PVS desconocida y de una celda FP1.

La interfaz selecciona resultados por `case.current_version`, nunca por «el último trabajo» sin verificar su versión. Una respuesta HTTP satisfactoria tampoco basta para mostrar éxito: `job.status` debe ser `completed` y debe existir un resultado canónico. El fallo técnico no se interpreta como inviabilidad.

## Interacción, seguridad y accesibilidad

- Tuteo; contraste de tinta y verde sobre fondos claros. Controles y etiquetas nativos, foco visible, enlace para saltar al contenido, avisos `role=status` y errores `role=alert`.
- Navegación por etapas con estado actual, tablas con título y encabezados, mapa/lista equivalentes, formularios etiquetados. No se necesita color, arrastre o hover para comprender un resultado.
- Diseño adaptable a móvil: una columna, botones envolventes, navegación desplazable y tablas con desplazamiento interno. Respeta la preferencia de movimiento reducido. Estilo de impresión disponible.
- Todo relato, fuente, resultado y error se inserta con nodos de texto/`textContent`. No se usa `innerHTML`, ejecución dinámica, manejadores inline ni HTML del usuario. Scripts y estilos externos son compatibles con la CSP local.
- Los errores conservan los campos. Ante conflicto de versión se ofrece actualizar y revisar de nuevo; no se sobreescribe silenciosamente. La aceptación y las observaciones incluyen clave de idempotencia conservada para reintentar la misma solicitud.
- «Nueva exploración» cambia la vista y el identificador recordado; no elimina expedientes. «Restaurar» crea una nueva revisión mediante propuesta confirmable.

## Límites y recepción

El alcance funcional es un perfil sintético, con edición acotada. La corrección de hechos disponible es la ley conjunta; otras modificaciones demandan ampliar el modelo. No hay adquisición externa, coordinación real de cuidadores, mensajería, acciones físicas ni publicación.

La interfaz no convierte las pruebas de navegación en comprensión humana medida. El protocolo de contraste empírico y las pruebas con participantes autorizados siguen separados de la ejecución matemática y de la inspección del navegador. Las verificaciones de integración y capturas ejecutadas por el integrador constituyen la evidencia de recepción técnica; no son validación empírica.
