# Backlot #593: falta evidencia de colación

Revisión del 16/10/2026 del [issue #593](https://github.com/brekkylab/backlot/issues/593),
abierto, sin asignar, actualizado a las 16:21:28 UTC del mismo día.

El informe distingue dos problemas: el error 500 al convertir determinados
dígitos Unicode, y el orden natural que realmente devuelve Google Drive. Cambiar
`isdigit()` por `isdecimal()` evita esa conversión inválida, pero el propio
reporte muestra que no reproduce el orden observado para superíndices y números
circulados. Once nombres no determinan la colación general de Drive.

Estado: NEEDS_INFORMATION. No se preparó ni contó un arreglo completo. La
medición de Drive del 10/10/2026 pertenece al reportante y no fue repetida por
Genius. Hace falta evidencia oficial suficiente de colación o una matriz de
comparación autorizada antes de afirmar fidelidad. No se crearon cuentas ni se
hicieron llamadas autenticadas; no se ejecutó el kernel. El caso #611 de Backlot
también se leyó, pero quedó DETECTED: se priorizó un fallo comprobable sin API
de un proveedor. No se amplió la muestra ni se llenó la memoria con búsquedas.
