# Diseño de intervenciones sobre recursos y relaciones

`genius-intervention-design/1` genera alternativas para un gemelo aceptado
`STOCK_FLOW_FINITE_V1`. Se usa desde **Intervenir** en el gemelo, por REST y por
MCP. El resultado inicial es una propuesta revisable. La confirmación crea una
versión inmutable; la evaluación utiliza el compilador y el kernel existentes.
El estado de publicación y las verificaciones de este incremento se conservan
en su PR. La presencia del código no acredita un despliegue.

## Qué representa

Una relación es un canal dirigido entre dos depósitos de la misma unidad.
Declara disponibilidad inicial, capacidades necesarias, costos de apertura,
cierre y cada transferencia, y procedencia de esas premisas. Su disponibilidad
se representa mediante la capacidad `relation.<id>`; aparece en los estados y
en las firmas de organización utilizadas por CAG. No es una relación causal
inferida ni una representación universal de vínculos humanos.

Las operaciones son:

| Operación | Efecto en el modelo |
| --- | --- |
| `connect` | Paga los costos y agrega la capacidad que habilita la relación. |
| `disconnect` | Requiere la relación abierta, paga los costos y retira esa capacidad. |
| `transfer` | Requiere la relación abierta y sus capacidades; retira la cantidad y los costos, y deposita la cantidad en destino. |
| `use_action` | Programa una acción ya declarada en el modelo base. |

La transacción conserva las reglas nativas: si falta cualquier retiro o
capacidad, toda la acción falla sin consumo parcial ni creación de recursos.
Los eventos externos continúan y su efecto permanece en la trayectoria.
Los costos son consumo al entorno. Los depósitos que superan capacidad se
registran como derrames. No hay conversión implícita de unidades ni producción
gratuita. Un nuevo intento de apertura ejecuta y paga la acción aunque el canal
ya esté abierto. Cada operación ocupa un paso; no hay simultaneidad implícita.

## Generación y comparación

Cada intervención declara una secuencia de operaciones. `at` contiene momentos
alternativos; `amounts` contiene cantidades alternativas para una transferencia.
Se enumera el producto cartesiano de estas elecciones y se conserva cada variante
con su correspondencia a política y acciones. Los pasos alternativos de distintas
operaciones no pueden solaparse: se rechaza el diseño completo en lugar de omitir
combinaciones incompatibles silenciosamente. `default_action: null` genera una
espera sin intervención en los demás pasos; también puede elegirse una acción base.

Todas las políticas base se conservan. Los recursos y saldos iniciales, portadores,
horizonte, eventos, ley, bienestar, tarea y criterio de selección son iguales para
todas las alternativas de la nueva versión. La disponibilidad inicial de las nuevas
relaciones es una premisa común que debe revisarse. Diseñar una intervención no
corrige datos de partida ni cambia el objetivo para favorecer una alternativa.

Se mantienen los límites del perfil sobre el modelo combinado: 6 políticas,
12 acciones, 8 capacidades, 16 firmas alcanzadas y 256 ocurrencias de estado.
La expansión se cuenta antes de construir las combinaciones. Cualquier exceso
rechaza toda la propuesta; no trunca, muestrea ni fabrica un ganador. La cobertura
`EXHAUSTIVE_DECLARED_COMBINATIONS` se refiere únicamente al conjunto finito
de opciones declaradas, sin afirmar optimalidad global.

La evaluación mantiene las incertidumbres: una ley ausente no recibe pesos
inventados, un umbral desconocido conserva su estado, y una frontera puede quedar
sin selección única. Las tareas operacionales no se renombran PVS de vida.

## API y agentes

Con el prefijo local `/api`, o `/api/twin` en el servicio autenticado:

1. `GET /interventions/schema`: contrato JSON cerrado y límites.
2. `GET /interventions/example`: modelo y diseño sintéticos reproducibles.
3. Crear el expediente, proponer el modelo base y confirmar sus premisas por el
   flujo existente de [D3](D3_API.md).
4. `POST /cases/{id}/proposals`:

```json
{
  "base_version": 1,
  "kind": "intervention_design",
  "text": "Explorar redistribución entre depósitos",
  "structured": {
    "design": {
      "format": "genius-intervention-design/1",
      "name": "Conectar y redistribuir agua",
      "relations": [
        {
          "id": "pipe",
          "label": "Conexión entre depósitos",
          "source": "source",
          "target": "target",
          "initially_open": false,
          "requires": [
            "operate"
          ],
          "open_costs": {
            "time": "1/1"
          },
          "close_costs": {},
          "transfer_costs": {},
          "provenance": "Relación hipotética; apertura cuesta un minuto y la transferencia no añade costos dentro del modelo."
        }
      ],
      "interventions": [
        {
          "id": "redistribute",
          "label": "Abrir conexión y transferir",
          "default_action": "wait",
          "operations": [
            {
              "operation": "connect",
              "relation": "pipe",
              "at": [
                1
              ]
            },
            {
              "operation": "transfer",
              "relation": "pipe",
              "at": [
                2
              ],
              "amounts": [
                "1/1",
                "2/1"
              ]
            }
          ]
        }
      ]
    }
  }
}
```

El modelo base completo está en [stockflow_distribution.json](../examples/stockflow_distribution.json).

5. Revisar la propuesta y confirmar mediante `/proposals/{id}/accept` con
   `confirmed`, `acknowledge_declared` y clave de idempotencia. La confirmación
   sigue refiriéndose al modelo, no a validar hechos ni autorizar acciones físicas.
6. Evaluar la versión por `/cases/{id}/evaluate`, inspeccionar trayectorias,
   comparar versiones y exportar el expediente.

MCP ofrece `twin_intervention_schema`, `twin_intervention_example` y
`twin_design_interventions` (`case_id`, `base_version`, `text`, `design`). Las dos
lecturas requieren `twins:read`; generar requiere `twins:write` y usa exactamente
la ruta de propuestas, con sus límites y control de versión. La evaluación exige
`twins:evaluate` y consume el presupuesto compartido existente. Los permisos no se
amplían. El borrado, retención y aislamiento por cuenta siguen vigentes.

El recibo guarda el diseño exacto, hashes del modelo base/diseño/modelo generado
y código generador, relaciones→capacidades, alternativas→operaciones y versión
base. Forma parte de los metadatos de la propuesta/versión, evaluación y exportación.
Una edición manual no hereda un recibo incompatible; restaurar una versión conserva
su recibo original. Proponer no evalúa, no acepta y no modifica la versión base.
Las acciones previamente declaradas pueden reutilizarse con `use_action`.

## Interfaz humana

En **Intervenir** se eligen origen/destino, requisitos, costos, fuente de la
declaración, secuencias, momentos y cantidades. **Generar alternativas** guarda
la propuesta; **Revisar** muestra las variantes antes de confirmar y explorar.
Una propuesta guardada puede recuperarse tras recargar la página. Los cambios
del formulario aún no generados viven solamente en la pestaña. Un borrador no
confirmado del constructor no cambia la base de la intervención.

El ejemplo abre un expediente distinto, pide confirmar su modelo y deja preparado
el diseño. Parte de 4 L en origen, 2 L en destino y 3 minutos disponibles. La
demanda es 1 L por día durante tres días; se exige conservar al menos 1 L en cada
estado. Abrir cuesta 1 minuto en el primer paso; en el segundo se comparan 1 y 2 L.
Los recorridos del destino son: referencia `2,1,0,0`; transferir 1 L `2,1,1,0`;
transferir 2 L `2,1,2,1`. El kernel selecciona la última bajo esas premisas.
Es evidencia de funcionamiento del software con datos sintéticos.

## Alcance y continuidad

Se implementan generación, revisión, evaluación y trazabilidad de intervenciones.
No se conectan actuadores, compras, mensajes ni APIs de efectos externos. El
registro de observaciones y calibración del perfil stockflow continúa pendiente;
no se presenta este incremento como aprendizaje autónomo o cambio de código.
Los efectos reales sobre bienestar y sostenimiento de la vida requieren evidencia
del dominio. Relaciones generales, producción, conversiones de unidades y cambios
de población requieren contratos explícitos adicionales.

Reproducir pruebas: `PYTHONPATH=twin:kernel python -m unittest discover -s twin/tests -v`.
El contrato de navegador está en `twin/tests/browser_interventions.cjs`; CI ejecuta
ese recorrido y el general D3 en escritorio y pantallas de 390/320 px, con servicio
local propio. Ninguna prueba técnica sustituye comprensión humana o datos de campo.

Siguiente encargo: verificar publicación del incremento y, conservando el contrato,
conectar una observación stockflow a una predicción congelada. Definir qué variables
y relaciones se observan, unidad y procedencia; contrastar sin reescribir resultados
anteriores y sin confundir discrepancia con recalibración ya validada.
