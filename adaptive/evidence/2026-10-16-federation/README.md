# Recibo del laboratorio de tres nodos

Ejecución real de procesos locales con **datos enteramente sintéticos**.
[Informe completo](experiment.json), [pruebas](tests.txt) y
[contrato/reproducción](../../federation/README.md).

| Situación | Error absoluto total aislado | Conectado | Resultado del kernel |
|---|---:|---:|---|
| Datos compartidos útiles para el objetivo | 100 | 0 | `connected` |
| Datos compartidos no representativos del objetivo | 200 | 300 | `isolated` |

Cada total suma tres predicciones sobre **un mismo objetivo sintético**. No son
tres mediciones independientes. La regla y los objetivos están declarados en
el programa: no hay selección de ejemplos después de ejecutar ni estudio ciego.
Los procesos reciben los objetivos después de congelar sus predicciones.

Diez comprobaciones del experimento pasan: tres procesos y bases separados,
duplicados, privacidad, conflictos, desconexión, continuidad sin un par,
persistencia tras reiniciar y los dos resultados comparativos. El kernel
verifica las dos comparaciones. 66 pruebas adaptativas pasan, 13 de federación.

El informe conserva predicciones, objetivos, evidencia compartible, recibos,
modelos de comparación e identidad del código. No contiene tokens ni bases
privadas. Las bases temporales se eliminaron al finalizar. No hubo cambios
en producción ni acciones físicas. Los resultados no acreditan aprendizaje
causal, mejora universal, bienestar, PVS ni vida artificial en sentido biológico.
