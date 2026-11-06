# Propuesta AM-08 — Estado inicial incierto como familia de instancias

Estado: `ACEPTADA`. Pedro la aprobó el 2026-11-06, dentro del plan para usar el motor en el mapa 3D de Mendoza de Adelanta.
- No modifica S1 ni el kernel FP1.
- Implementación: zonas con `initial_values` en `twin/genius_twin/territory.py`.

## Problema

FP1 exige una inicialización compartida y única (G02, MV 7.1). Los datos del mapa no la dan:
- el censo del arbolado es de 2011-2012;
- un padrón puede estar incompleto;
- una estimación viene con su rango.

Hay tres salidas que violan las bases:
- elegir un valor central, que esconde la duda;
- poner probabilidades a los valores sin una ley justificada, que confunde incertidumbre con probabilidad;
- tratar el dato faltante como cero.

## Definición

Una zona puede declarar, para hasta 2 existencias, entre 2 y 4 valores exactos del saldo inicial, en las unidades de la zona: $V_s = \{v_{s,1}, \dots\}$, con a lo sumo 8 combinaciones.

1. **Instancias.** Cada combinación $v \in \prod_s V_s$ define una instancia $M_{z,v}$, igual al modelo de la zona salvo esos saldos iniciales. Cada instancia tiene su propia inicialización, única y compartida por todas sus rutas, así que G02 vale en cada una. El kernel evalúa y verifica cada instancia.
2. **Orden de la zona.** Es la conjunción de Kleene sobre las instancias: $a \succeq^c_z b = \bigwedge_v a \succeq^c_{z,v} b$. Es una intersección finita de preórdenes, y la Proposición 1 de AM-06 se aplica igual.
3. **Vida.** Si el estado de la tarea en un escenario es el mismo en todas las instancias, se conserva. Si cambia, queda `depends_on_initial`. La PVS de la zona se informa como un valor cuando coincide en todas las instancias, y como rango $[\min_v, \max_v]$ cuando no.
4. **Territorio.** En un escenario, la vida conjunta es `failure` si alguna zona falla con todos sus valores, y `success` si todas las zonas tienen éxito con todos sus valores. Si no hay `undecided` pero alguna zona depende de su valor inicial, queda `depends_on_initial`. La PVS conjunta pasa a ser un par de cotas exactas: el mínimo es la masa de los escenarios con éxito seguro, y el máximo suma la de los escenarios que dependen del valor inicial. El máximo puede no alcanzarse, porque el valor inicial de una zona es el mismo en todos los escenarios. Comparar dos rutas por PVS conjunta da 1 si el mínimo de una alcanza el máximo de la otra, 0 si su máximo queda debajo del mínimo de la otra, y «no decidido» en otro caso.
5. **Capacidades generativas.** Las capacidades robustas adicionales de la zona son las que aparecen con todos los valores.

## Resultados

**Proposición 1 (no se afirma más que en cada valor).** Si para algún valor declarado una ruta no es al menos tan buena como otra en un criterio, la zona tampoco lo afirma. La conjunción sólo puede convertir un 1 en 0 o en «no decidido», nunca al revés.

**Proposición 2 (sin probabilidad inventada).** Ningún peso se asigna a los valores iniciales. Las cotas de PVS dependen sólo de la ley de escenarios declarada y valen para cualquier valor declarado.

**Límite de lectura.** Las conclusiones valen para los valores declarados, no para todo el intervalo entre ellos. Sin monotonía demostrada, un valor intermedio podría comportarse distinto. El resultado lo rotula en `conditional_on_declared_initial_values`.

## Topes medidos en esta misma tanda (sin cambio)

El plan proponía subir el horizonte a 52 pasos (un año en semanas). Se midió el 2026-11-06 con el arbolado, con 2 rutas, 2 escenarios y 212 ocurrencias:
- tardó 12,5 s;
- dejó 83 MB sin empaquetar y 36 MB empaquetados.

El servicio web admite 16 MB, y la salida crece con ocurrencias × horizonte. Por eso los topes no se subieron. Para el mapa conviene usar meses (12 pasos) o ventanas de 4 semanas por zona.
