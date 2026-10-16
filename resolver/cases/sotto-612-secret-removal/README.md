# Sotto #612: eliminar secretos y sincronizar la eliminación

Estado: **SOLUTION_PREPARED**, 16/10/2026. No enviada ni aplicada en Sotto.

Necesidad: [getsotto/sotto #612](https://github.com/getsotto/sotto/issues/612).
Fuente fijada: [`0205ad85a5790351a43c3f523aff95f15da29d9c`](https://github.com/getsotto/sotto/tree/0205ad85a5790351a43c3f523aff95f15da29d9c).

## Entrega y utilidad

`solution.patch` añade una sección de eliminación al README en inglés, español,
francés, alemán y portugués de Brasil. Cambia sólo esos cinco documentos; no
modifica comandos, criptografía, confirmaciones ni políticas de borrado.

La guía ayuda a desarrolladores a distinguir el entorno elegido, el cambio local,
el envío al servidor y la descarga en otro dispositivo. Explica un comportamiento
fácil de interpretar mal: en modo no interactivo, un borrado con nombre no pide
confirmación aunque no se use `--yes`. También aclara que eliminar de Sotto no
equivale a borrado seguro ni a revocar la credencial en su proveedor.

Se eligió una tarea ya registrada, abierta, sin asignados ni PR que implementara
el mismo alcance. No hubo nueva búsqueda masiva. Los PR de recuperación #595,
bloqueo local #608, ayuda de entrada #607 e instalación #614 se revisaron para
evitar duplicación. La guía de recuperación se deja a su trabajo existente;
aquí sólo se remite a la ayuda de los comandos. Antes de enviar, volver a revisar
la rama principal y esos PR porque también modifican documentación.

La reserva y los criterios se publicaron antes de editar. `validation.json`
conserva los criterios, resultados y límites; `source-review.md` relaciona cada
afirmación con la implementación revisada.

## Comprobaciones y reproducción

- Antes del cambio: seis de los siete controles del caso fallaron porque faltaba
  la sección; el control general de traducciones ya pasaba. No son seis errores
  de ejecución de Sotto.
- Después: siete controles del caso, trece pruebas del verificador upstream y
  el verificador de las cuatro traducciones aprobados.
- El parche se aplicó sin conflictos a otra copia limpia del commit fijado;
  allí los siete controles del caso volvieron a pasar.
- Se comprobó que sólo cambian los cinco README y que el diff no tiene errores
  de espacios. Los logs preservan las salidas, no certifican revisión independiente.

En una copia nueva de la fuente fijada, desde su raíz:

```sh
git apply --check /ruta/al/paquete/solution.patch
git apply /ruta/al/paquete/solution.patch
python3 -B scripts/check-readme-i18n
python3 -B -m unittest discover -s scripts/tests -p test_readme_i18n.py -v
python3 -B /ruta/al/paquete/verify_case.py .
git diff --check
```

Para el resultado inicial, ejecutar el último control Python contra una copia
sin parche: debe fallar por la sección ausente. `verify_case.py` es de sólo lectura.
En este trabajo todos los controles se ejecutaron con Python 3.12.3 mediante el
arnés revisado [run_no_network.py](../linux-vitals-149-locale/run_no_network.py),
que vacía el entorno y bloquea sockets IPv4/IPv6 con seccomp en procesos hijos.
No se instalaron dependencias. `isolation.txt` comprueba ese bloqueo.

No se compiló ni ejecutó el CLI, no se generó ayuda desde un binario, no se
ejecutaron las pruebas Rust ni la suite completa del proyecto. La sintaxis y el
comportamiento se contrastaron con las declaraciones Clap y los handlers de la
fuente fijada. No se borraron secretos, no se inició sesión y no se sincronizó
ninguna cuenta. Las traducciones son de mejor esfuerzo: los controles verifican
estructura y comandos, no sustituyen una revisión lingüística independiente.

## Autoridad, atribución y continuidad

El paquete contiene un parche derivado de Sotto bajo Apache-2.0; se adjunta su
`LICENSE`. Las modificaciones a los cinco README fueron preparadas para Genius
con asistencia de Codex el 16/10/2026; el diff identifica los cambios. No se
encontró un archivo NOTICE versionado en la fuente fijada.

El [contrato de contribución](https://github.com/getsotto/sotto/blob/0205ad85a5790351a43c3f523aff95f15da29d9c/CONTRIBUTING.md)
exige DCO en cada commit. **No** se firmó en nombre de Pedro ni se aceptó un
acuerdo. El siguiente paso externo requiere permiso para presentar un PR a
`getsotto/sotto` y una decisión del contribuyente sobre la certificación DCO.
`UPSTREAM_DRAFT.md` prepara el contenido, pero no se envió.

No se ejecutó el motor Genius: esta corrección documental no tiene una
representación ni datos que justifiquen un cálculo suyo. CAG, PVS y bienestar
no medidos. La integración de archivos en Genius no implica aplicación o
adopción en Sotto. No regenerar esta entrega como novedad en el siguiente ciclo.
