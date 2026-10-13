# Decisiones de ingeniería de Fase 2

Fecha 2026-09-23. Predecesor recibido y verificado: GENIUS-P1-2026-09-23-v1.0.0. Inicio autorizado por el propietario: «inicia fase 2». Esta autorización activa PHASE_2_MANDATE y permite implementación, pruebas y revisión separada; no inicia F3 ni publicación externa.

| Decisión | Razón y alcance |
|---|---|
| Python >=3.11 con biblioteca estándar | Enteros arbitrarios, Fraction, JSON y unittest; ejecución directa offline sin instalar dependencias |
| Entorno de ejecución observado: CPython 3.12.14 | Registrar la versión realmente usada, sin afirmar pruebas en plataformas no ejecutadas |
| Versión de Kernel GENIUS-KERNEL-1.0.0 | Identidad distinta de Specification GENIUS-SPEC-1.0.0; aceptada mediante pruebas, auditoría y transferencia G2 |
| F1 congelada en baseline y ZIP original en history | No modificar una release sellada; el contrato normativo recibido queda disponible íntegro |
| Módulos por función matemática y validador separado | Parseo/causalidad, estructura, evidencia y decisión, con utilidades comunes sin axiomas adicionales |
| Verificación por recomputación y control de gramática/cobertura | No confiar en etiquetas PASS; el verificador puede compartir constructores puros, mientras los oráculos y auditoría se producen separadamente |
| API de bytes originales y pareja input.json/result.json | SHA-256 liga la salida a la codificación exacta recibida; no se inventa equivalencia por hash |
| CLI local y exportación portable | La capacidad no depende de GitHub, servicios remotos, MCP, A2A ni una cuenta |
| Límites operativos explícitos | max_nodes, max_operations, max_seconds, max_input_bytes y max_integer_digits (dígitos de cada componente numeral recibido, sin signo/separador; no limita el tamaño de enteros derivados); su agotamiento devuelve LIMITED, nunca infactibilidad |
| Restricción decimal implícita de Python desactivada | Preservar Nat/Q sin un máximo matemático arbitrario; max_integer_digits es opcional y operativo |

El límite de tiempo es cooperativo en los puntos de control de bucles, no una garantía de interrupción dura durante una operación indivisible del intérprete. El sistema operativo puede agotar memoria; no se afirma rendimiento universal. No se utiliza coma flotante en valores, leyes, comparaciones o certificados; solo el reloj operativo utiliza monotonic.

El presupuesto de recursión del intérprete se captura antes de evaluar y figura automáticamente como `python_recursion_depth` en execution.limits. No es una opción para cambiar H ni una hipótesis de la instancia. Agotarlo produce LIMITED. Los límites suministrados por el usuario se declaran además de ese límite ambiental. `max_integer_digits` controla exclusivamente los numerales recibidos; los enteros derivados pueden crecer durante aritmética exacta.

La ejecución desde la carpeta kernel no requiere instalación. pyproject permite instalación opcional si el entorno ya dispone de la herramienta de construcción; descargar herramientas no forma parte de la reproducción offline ni se ejecuta automáticamente.

## Resoluciones de lectura del contrato

- Una acción tabulada se conserva como valor de π aunque falle ejecutabilidad/admisibilidad. Ese prefijo no acredita continuación; las referencias a futuros aún no acreditados quedan sin resolver, salvo que se pruebe una referencia imposible por el soporte conocido. No se afirma un árbol completo tras detener la expansión.
- Un subárbol local completo puede sustentar Sem/V aunque otra rama deje incompleto el árbol global. Permite refutar una restricción con un testigo terminal legítimo; no acredita una partición foliar global ni PVS de un árbol incompleto.
- Para B0 se necesita perfil funcional terminal completo; una medición no terminal ausente impide G05 fuerte sin borrar ese perfil terminal. La calibración común se comprueba sobre los raw medidos del ámbito alcanzado de B0; no se busca un subgrupo favorable después de encontrar una contradicción compartida.

Estas resoluciones fueron revisadas por el auditor frente a 01–06; dictamen en validation/AUDIT_REPORT_F2.md. Una contradicción contractual real debe abrir una enmienda versionada y no se resolverá alterando solo el código para pasar una prueba.
