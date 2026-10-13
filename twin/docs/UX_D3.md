# D3 · Constructor de planes con recursos temporales

La entrada principal conserva un relato general en un borrador persistente. El usuario puede configurar un modelo desde cero o cargar un ejemplo sintético identificado. El relato no se convierte silenciosamente en probabilidades, estados ni reglas: los valores que alimentan el cálculo se revisan en formularios.

## Recorrido implementado

1. **Tus decisiones:** lista y recuperación de expedientes. El servicio conserva los datos; el navegador solo recuerda opcionalmente el último identificador.
2. **Construir:** nombre, horizonte y paso; stocks persistentes/renovables; personas y otros portadores; capacidades y tareas; planes con reglas de estado previo; escenarios con eventos temporales; ley conjunta opcional; condiciones de trayectoria y perfiles materiales por portador.
3. **Revisar:** una propuesta validada muestra la configuración y sus premisas. Confirmar autoriza calcular bajo esas condiciones y crea una versión, sin autenticar hechos.
4. **Futuros:** los resultados proceden del núcleo. Se puede cambiar de política y escenario; la tabla contiene todos los estados del horizonte configurado, recursos, acción elegida/ejecutada y monitores de fallo e indeterminación. Bienestar conserva valores materiales brutos, unidad, portador, momento y dirección preferida. CAG conserva identidades, firmas, receta acc y modalidades.
5. **Conclusión:** selección única o comparación parcial/frontera según el resultado formal. Una tarea operacional se presenta como cumplimiento de tarea; no se etiqueta como PVS de vida. Una ley ausente no se sustituye por pesos uniformes ni por cero.
6. **Historial:** comparación, restauración mediante una propuesta nueva y exportación del expediente canónico. Las revisiones anteriores permanecen accesibles.

El semillero D1 sigue disponible como modo explícito en la entrada y conserva su recorrido original. Los números de D1 no se reutilizan para configurar o calcular D3.

## Presentación de valores y reglas

Los controles permiten escribir cantidades enteras, decimales o fracciones. Las cantidades se normalizan a racionales exactos antes de confirmar; la validación definitiva pertenece al servidor. No hay un editor JSON como única vía para usar el modelo. Los IDs internos se generan al agregar elementos y permanecen estables mientras se editan sus etiquetas.

Los pasos del horizonte y eventos se ajustan al cambiar su longitud; la interfaz pide revisar esas condiciones. Las reglas consultan recursos/capacidades disponibles al comienzo del paso. Los retiros y aportes pertenecen a tareas explícitas, y las entradas y demandas externas pertenecen a escenarios. El servidor rechaza referencias ausentes, incompatibilidad de unidades, recursos insuficientemente declarados y excedentes fuera del contrato.

Un umbral vacío se conserva como desconocido. La comparación usa valores de la versión actual; un resultado anterior sigue siendo histórico. El tiempo, agua u otro recurso no se suman como índice universal de bienestar. Los estados de probabilidad se muestran junto a sus límites, sin transformar ausencia en cero.

## Integración local y autenticada

Los mismos archivos funcionan en `/` con API `/api` y en el montaje `/twin/` con API `/api/twin`. Los assets usan rutas relativas. En el montaje autenticado, las mutaciones obtienen el token CSRF de la sesión mediante `/api/twin/runtime`; se conserva solo en memoria. Una respuesta 401 ofrece volver al inicio de sesión de la beta. La interfaz no almacena credenciales ni crea un servicio público por sí sola.

Todo dato del usuario se inserta con nodos de texto. Se conservan la CSP, formularios etiquetados, controles de teclado, avisos y error explícito. La interfaz permite tablas desplazables internamente y una sola columna móvil; no exige manipular un grafo.

## Límites de recepción

El perfil nuevo opera bajo premisas declaradas. Su registro de observaciones y resolución explícita de discrepancias no están habilitados: se informa ese alcance sin exigir un caso real para continuar con los cálculos. D1 mantiene sus observaciones y la suspensión previa. Un valor calculado o un trabajo terminado no valida empíricamente el modelo.

Los conflictos de borrador conservan los cambios locales. Al recargar se muestra también el borrador guardado; se puede adoptarlo o guardar explícitamente los cambios revisados sobre la revisión vigente.

El gate `twin/tests/browser_d3.cjs` recorre controles reales, persistencia, conflicto concurrente y recuperación, evaluación nativa, edición material, comparación, restauración, lista y exportación, además de un modelo operacional sin ley. Sus capturas y respuestas son evidencia técnica de interfaz, no participantes ni validación del mundo. La recepción concreta se documenta mediante sus resultados ejecutados y los del montaje autenticado del integrador.
