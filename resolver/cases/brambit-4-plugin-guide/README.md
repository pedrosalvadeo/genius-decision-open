# Primera solución externa preparada: guía de plugins Brambit

**Estado: SOLUTION_PREPARED. No enviada, no aplicada, no aceptada por Brambit.**

El resolutor encontró el pedido público
[morethanrealio/brambit #4](https://github.com/morethanrealio/brambit/issues/4).
La documentación disponible describía el contrato del cargador, pero el solicitante
pedía un recorrido completo y un ejemplo ejecutable. Se fijaron cuatro criterios
antes de preparar la solución; están en la memoria del resolutor.

## Entrega

- [Guía para autores](files/docs/plugins.md): separación núcleo/plugin, carga,
  ciclo de vida, trece puertos, rutas, herramientas, páginas, idiomas y pruebas.
- [Plugin de ejemplo](files/examples/hello-plugin/index.mjs): ruta pública de
  lectura, herramienta sin efectos y página traducida a inglés, portugués y español.
- [Pruebas](files/tests/hello-plugin.test.mjs): cargador real, registro de rutas,
  contrato de herramientas y renderizador de traducciones de Brambit.
- [Parche aplicable](solution.patch), con enlaces desde README y nota de cambios.
- [Evidencia de validación](validation.json), con base, hashes, comandos y límites.

Los enlaces relativos de la guía y sus imports están diseñados para el árbol de
Brambit después de aplicar el parche, no para ejecutarlo dentro de Genius.

Base revisada: `fb684453d95fb0d5ebb762ff9fc5fb9af766fbd4`.
Se comprobaron cuatro pruebas de integración, el control de catálogos y el control
que impide añadir pruebas basadas en leer el código de producción como texto.
El verificador de catálogos imprime avisos de fallback porque compara el catálogo
parcial del plugin también con claves del núcleo; no son fallos del ejemplo. El
control específico de sus tres catálogos no encuentra claves faltantes ni errores.
El parche pasa `git apply --check` en una copia limpia de la base.

No se arrancó el servidor completo, Postgres ni una sesión con un modelo. Las
pruebas se ejecutaron con entorno mínimo, sin claves de proveedor o cuenta.
La dependencia de pruebas `i18next@26.4.2` se instaló sin scripts de instalación.

## Pendiente de entrega y adopción

Brambit requiere asignación por un mantenedor y aceptar un CLA para un primer PR,
según su CONTRIBUTING.md. No se solicitó asignación, se envió un mensaje, se abrió
un PR externo ni se aceptó un contrato en nombre de Pedro. La guía está lista para
revisión; la adopción y el resultado para usuarios siguen sin evidencia.

La selección fue una decisión operativa por necesidad explícita y verificabilidad.
No se ejecutó el kernel Genius: este caso documental no aportaba un modelo
cuantitativo adecuado. No se atribuyen bienestar, CAG, PVS ni un problema externo
resuelto a las pruebas locales.

## Licencia y atribución

Propuesta original preparada por Codex, agente resolutor de Genius, por encargo de
Pedro Salvadeo. Los archivos de propuesta de esta carpeta y el parche se ofrecen
bajo **AGPL-3.0-only**, compatible con el destino declarado por Brambit; se incluye
[el texto de la licencia](LICENSE-AGPL-3.0.txt). El código de Brambit usado para
validar conserva sus autores y licencia en el repositorio original. El núcleo del
resolutor en `resolver/genius_resolver` mantiene la licencia Apache-2.0 de Genius.
Esta preparación no implica relación comercial ni aval de los mantenedores.
