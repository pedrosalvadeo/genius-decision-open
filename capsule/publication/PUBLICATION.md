# Edición pública Genius

Repositorio: https://github.com/pedrosalvadeo/genius-decision-open
Estado: edición de fuentes publicada en la rama main. El commit del checkout identifica la versión exacta; PUBLICATION_MANIFEST.json permite verificar sus archivos.
Visibilidad: pública. Licencia: Apache-2.0 para originales del proyecto, preservando condiciones de terceros.

Esta edición contiene motor, matemática original con enmiendas, contratos, casos, pruebas, cápsula y montaje disponible. Es una instantánea separada; no publica el historial Git ni los expedientes y registros operativos privados. El alcance del motor pleno está en HOST_MISSION.md y workstreams.json.

## Reconstruir

Desde la raíz, con Python 3.11+:

```bash
python3 capsule/build_publication.py --out /tmp/genius-public-edition
```

La salida debe ser una carpeta nueva. El índice de fuentes comprueba SHA-256; los archivos adaptados para la edición conservan hashes de origen. El índice exportado describe los bytes exportados, por lo que la edición puede reconstruirse desde sí misma. PUBLICATION_MANIFEST.json liga el contenido del paquete; build-receipt.json registra los hashes de los archivos comprimidos. Las salidas son reproducibles con el mismo entorno de Python y compresión.

La cápsula identifica capacidades actuales y pendientes. Publicar el código no demuestra que un agente externo ya lo haya utilizado, que las hipótesis estén validadas ni que el motor pleno esté terminado.
