# Primera red pública de nodos Genius

Propósito: permitir instalaciones voluntarias en equipos de distintos
anfitriones, sumar vistas complementarias y calcular localmente con el motor.
Contrato e instalación: [INTERNET.md](../../adaptive/federation/INTERNET.md).

La entrega añade un relay y directorio al servicio existente. Cambios aditivos:
tablas `network_nodes` y `network_views`, rutas de lectura pública, permisos de
agente específicos, alta ligada a clave/cuenta/origen y publicación explícita.
No añade servidores pagos ni amplía los recursos del contenedor existente.

La clave privada nunca llega al relay. Los nodos verifican firma y hash de cada
sobre antes de importarlo. Esto acredita la clave firmante, no la verdad ni la
independencia de las fuentes. El kernel conserva las mismas restricciones.

Se mantienen las cuotas de admisión de agentes existentes y se limita el
almacenamiento nuevo a 160 vistas de hasta 24000 bytes. Ocho por nodo. La página
publica capacidad, participantes recientes y mundos aportados, sin equiparar
estas cifras a cobertura del mundo real. No hay replicación ni contacto masivo.

La migración 012 es aditiva y no toca datos anteriores. Se amplía la lista
explícita de migraciones admitidas por recuperación a esta versión; las pruebas
de esquemas históricos mantienen la verificación de hashes y rechazan cambios
desconocidos. Se prueba que el borrado posterior de una cuenta elimina su nodo
y sus vistas al recuperar un respaldo anterior.

Validación local: 79 pruebas de integración aprobadas (incluidas 13 específicas
de red) y 91 pruebas adaptativas aprobadas. [Evidencia](../evidence/2026-10-16-public-network/README.md).
CI construye el contenedor del nodo e invoca su CLI sin red, además de construir
y verificar la beta. El PR registra commits, resultados y despliegue observado.

Despliegue previsto: fijar el servicio `genius-public-beta` a un commit probado,
con el mismo volumen, dominio y límites. Comprobar estado terminal SUCCESS,
lecturas públicas y un intercambio de datos sintéticos por HTTPS usando altas
normales sujetas a sus cuotas. Las cuentas de comprobación se borran al terminar.
Si las cuotas impiden la prueba, informar ese límite sin eludirlas.

Se habilita un nodo de referencia supervisado en el mismo servicio, usando el
alta ordinaria. Conserva estado local en el volumen y comparte un ejemplo
sintético; no equivale a un participante externo ni a una observación real.

La publicación habilita incorporación; no demuestra adopción externa. El próximo
paso de crecimiento es sumar anfitriones reales, medir aportes nuevos y revisar
la capacidad. La federación entre varios relays y la evolución de marcos/estados
siguen pendientes.
