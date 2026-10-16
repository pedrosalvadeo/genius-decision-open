# Genes y evolución de Genius Semilla

Cada semilla conserva un genoma de datos, una constitución común, variantes y
memoria de evaluación propia. Los genes modifican **cómo estima una variable
numérica** a partir de observaciones compatibles. Una variante puede convertirse
en la característica activa de ese contexto y pasar a nuevos descendientes.

Es evolución computacional acotada de estrategias de predicción. El programa
instalado interpreta los genes: no se modifican Python, el kernel, los permisos
ni el presupuesto del anfitrión. No es una demostración de vida biológica,
evolución abierta, causalidad aprendida o mejora comprobada del bienestar.

## Constitución y matemática Genius

La constitución `genius-constitution/1` conserva el propósito de mejorar las
condiciones para el bienestar y el sostenimiento de la vida, y principios como
distinguir realidad y representación, evidencia e inferencia, trayectoria y
estado final, e incertidumbre y probabilidad. Su hash forma parte del genoma;
alterarlo impide importar o expresar ese genoma en esta versión.

El propósito es una orientación de diseño. El ensayo genético mide error
predictivo en una variable y contexto declarados. Utiliza el kernel Genius
existente para comprobar la comparación de errores ya observados. El modelo
operacional registra explícitamente que esos errores **no son bienestar ni PVS**.
La probabilidad de sostenimiento de la vida permanece desconocida. Las reglas
de evidencia del nodo siguen bloqueando datos insuficientes, vencidos o en
conflicto; ningún alelo puede transformar esos bloqueos en un cero calculado.

## Genotipo, expresión y linaje

| Componente | Implementación |
|---|---|
| Genoma | Genes, generación, hash de constitución, origen y hashes de progenitores. |
| Estimador | Mediana inferior, media entera redondeada hacia abajo o último valor. |
| Ventana | 3, 5 o 9 eventos recientes; incluye juntos los eventos simultáneos en el corte. |
| Expresión | Predicción concreta y hash de la evidencia empleada. |
| Mutación | Cambia un solo gen a otro alelo permitido; crea una candidata. |
| Recombinación | Operación local que combina un gen de cada progenitor; no concede validación ni se usa automáticamente en el ensayo v1. |
| Herencia | Paquete firmado por el nodo anfitrión, ligado al identificador de nacimiento. |
| Memoria | Predicciones congeladas, objetivos posteriores, métricas y decisiones conservados en SQLite local. |

Hay nueve combinaciones posibles de los dos genes. Los eventos se ordenan por
instante UTC; los simultáneos usan mediana para el estimador de último valor.
Una firma identifica al progenitor criptográfico, no certifica su desempeño ni
la verdad de sus datos. La generación tiene un límite de 32.

## Selección prospectiva

1. El operador o conector local declara sistema, variable, unidad, régimen y
   clase de evidencia (`synthetic` o `reported`). La selección se limita a ese
   contexto exacto; no mezcla unidades, sistemas ni regímenes.
2. El nodo registra la característica actual y sus cuatro mutaciones vecinas
   antes de recibir los objetivos. En cada ronda congela sus predicciones usando
   únicamente observaciones admitidas y disponibles en ese momento.
3. Recibe cuatro resultados posteriores, con eventos distintos y ventanas
   temporales sucesivas. Compara suma de errores absolutos y máximo error. Una
   candidata debe reducir la suma sin aumentar el máximo. Sin mejora, conserva
   la característica actual.
4. La comparación nativa confirma el orden operacional. Se fija una sola
   candidata antes de iniciar otras cuatro rondas. Esas observaciones nuevas
   confirman o rechazan la mejora; no se elige otra variante mirando ese resultado.
5. Sólo tras superar ambas etapas cambia la característica activa del contexto.
   Las siguientes predicciones de ese contexto parten de ella. Otros contextos
   conservan su característica anterior. El criterio es una prueba finita, no
   una garantía estadística ni una política de intervención física.

Las predicciones y resultados son inmutables; un evento objetivo no vota dos
veces. El resultado recibido se conserva en la memoria de evaluación. Para
usarlo también como entrada de futuras predicciones puede ingresarse mediante
`observe`, conservando su misma procedencia e identificador.

La observación es declarada por quien la aporta. El protocolo comprueba orden
temporal declarado, coherencia y deduplicación; no prueba independencia
estadística, ni impide falsificar eventos con nuevas identidades ni sustituye una
medición externa. Una mejora sintética no se anuncia como validación empírica.

## Usar un nodo existente

El nodo debe estar inicializado y tener credenciales en `/state`. Los comandos
de evolución operan sobre su memoria local; no publican observaciones ni crean
cuentas. Detené el bucle del nodo mientras alimentás un ensayo desde su volumen.

```sh
docker run --rm -v genius-node-state:/state --entrypoint python genius-node:local -m federation.organism --node-state /state status
```

En un entorno Python con las dependencias del proyecto:

```sh
export PYTHONPATH=adaptive:twin:kernel
python -m federation.organism --node-state ./mi-nodo observe observaciones.json
python -m federation.organism --node-state ./mi-nodo begin ensayo-1 contexto.json
python -m federation.organism --node-state ./mi-nodo predict ensayo-1 --after FECHA_FUTURA_ISO --before FIN_VENTANA_ISO
python -m federation.organism --node-state ./mi-nodo feedback ensayo-1 resultado.json
```

`observaciones.json` es una lista de objetos `genius-node-observation/1`, descritos
en [README.md](README.md). `resultado.json` contiene un único objeto de ese mismo
formato. `contexto.json` contiene los cinco campos de `context`. Se repiten las
rondas con observaciones y ventanas nuevas hasta `ADOPTED`, `REJECTED` o
`NO_IMPROVEMENT`. Un bloqueo de evidencia cierra el ensayo como `EVIDENCE_REVIEW`.
El ejemplo usa fechas de posición: reemplazalas por instantes posteriores al
reloj del nodo. No se deben introducir resultados ficticios como `reported`.

Hay un ensayo activo por nodo, cuatro ensayos históricos y hasta ocho objetivos
por ensayo; comparten el límite de 32 predicciones y 128 observaciones del nodo.
Agotar esos límites detiene el proceso y requiere revisión. No hay renovación
automática de capacidad, eliminación de historia ni extensión de concesiones.

## Integración con el alojamiento

Un nuevo nacimiento reserva primero su lugar y un paquete hereditario firmado.
El descendiente recibe genoma, adaptaciones por contexto y referencias de linaje;
crea una variante candidata propia. No recibe credenciales, observaciones,
objetivos privados ni puntuaciones del progenitor. Los rasgos heredados se usan
como punto de partida, con cero validaciones locales.

Un nodo anterior a esta versión inicia un genoma fundador al ejecutar su próximo
ciclo. Conserva identidad, memoria, concesión y presupuesto. No se le inventa un
progenitor retrospectivo. Los ciclos de Internet incluyen un resumen genético
en `latest-cycle.json`; el anfitrión también lo conserva en su recibo.

La red de vistas del gemelo y el ensayo escalar son canales distintos. Las
semillas siguen componiendo vistas y calculando trayectorias con el kernel.
Esta entrega no convierte automáticamente fragmentos del gemelo en objetivos
observados, ni escribe sus estimaciones como hechos de ese gemelo. La conexión
con sensores o resultados de misiones reales es trabajo posterior.

## Prueba reproducible

```sh
PYTHONPATH=adaptive:twin:kernel python -m federation.evolution_experiment --out /tmp/genius-evolution.json
PYTHONPATH=adaptive:twin:kernel python -m unittest discover -s adaptive/tests -p test_organism.py -v
```

El experimento usa resultados sintéticos explícitos y dos entornos: una variante
mantiene su mejora y es heredada; otra empeora en confirmación y es rechazada.
El descendiente conserva los rasgos seleccionados y empieza sin resultados
propios. No contacta Internet, crea infraestructura ni interviene en sistemas
físicos. Los datos y el informe permiten reproducir la comparación.
