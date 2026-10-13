# Revisión deductiva de la integración M0–MVII

Fuente: S1, Entrega 10 completa, P03264–P03675. Se leyó el tramo en S1_READABLE.md y se localizó en S1_EXTRACTED.txt. Se contrastaron en el DOCX original/OMML los componentes del registro integrado, el producto de padres de 10.1, el descenso funcional, la unión/intersección CAG y los cuatro criterios de 10.2. La fuente S1 queda preservada. La Specification aplica las enmiendas explícitas de S2.

Tipo de revisión: comprobación deductiva de tres teoremas, sus hipótesis y puentes entre módulos, dos definiciones, dos contraejemplos y un testigo sintético integrado. No constituye prueba mecanizada, test de un Kernel, validación de utilidad ni revisión de originalidad. Es una revisión del formalizador, sujeta al auditor independiente y al Integrador.

## 1. Inventario y dictamen

| Elemento | Fuente | Resultado revisado |
|---|---|---|
| Definición 10.1, instancia integrada | P03271–P03305 | Tipada; exige Pi finita no vacía y datos de los módulos con misma instancia |
| Ruta de escenarios | P03307–P03323 | H común; Xi no vacío; una hoja por escenario y política, cobertura verificada contra MV |
| Definición 10.2, registro por política | P03326–P03338 | Conserva kappa,Q,F,CAG,O,W,V,ley,VProb,hard con claves y testigos |
| Contraejemplo 10.1, mezcla de políticas | P03339–P03348 | Válido; dos existenciales separados no justifican un testigo conjunto |
| Teorema 10.1, determinación por DAG | P03360–P03377 | Correcto para los constructores funcionales totales sobre registros que declara la fórmula; ver §3 |
| Parcialidad por componente | P03379–P03395 | Compatible con determinación: el objeto diagnóstico puede estar determinado y el valor fuera de dominio |
| Teorema 10.2, ensamblaje | P03397–P03516 | Correcto bajo dominios y coberturas de todos los constructores; FP1 incluye guardas explícitas, incluida reparación de 8.6; ver §4 |
| Contraejemplo 10.2, resumen funcional | P03519–P03533 | Válido: suficiencia para O no implica suficiencia para Phi |
| Teorema 10.3, terminación efectiva | P03535–P03550 | Correcto con tablas finitas efectivas y operaciones terminantes, sin código arbitrario; ver §5 |
| Testigo agua/hábitat | P03552–P03639 | Consistente al fijar protocolo canónico y palabras exógenas; resultados calculados en §6 |
| Raíz indecidida y PVS definida | P03641–P03656 | Correcto: hojas decididas no obligan a raíz semánticamente constante |
| Alcance del cierre | P03658–P03675 | Formal, condicional y relativo a la familia objetivo; no implica elección única, originalidad ni adequación empírica |

La revisión respalda tres conclusiones distintas: unicidad de los registros bajo constructores puros; corrección de los resultados cuando se satisfacen sus guardas; terminación de la presentación efectiva. Ninguna sustituye a las otras.

## 2. Dependencias y requisitos del ensamblaje

El DAG suficiente del perfil puede expresarse con las dependencias siguientes. Las primitivas se mantienen congeladas durante el cálculo; una flecha significa dependencia de datos, no secuencia física de acontecimientos.

| Constructor/objeto | Recibe | Garantía requerida |
|---|---|---|
| Validación de instancia | Bytes, versiones, tipos, tablas y premisas | Referencias, dominios y clases de diagnóstico separados |
| Inicialización y MV | Init, B, U, A_exec, A_adm, Pi, H | Todos los nodos/hojas, políticas legítimas y ocurrencias completas |
| Escenarios | Todas las hojas y sus palabras u; Xi | Imagen común exacta; cada fibra singleton; e_pi derivada |
| MI y descenso M0 | Puntos alcanzados, mediciones, calibraciones, Psi | Perfiles requeridos; dominio saturado y valores constantes en fibras |
| MII | Consultas causales y relación conjunta, vistas, demandas | Recombina exactamente R; cantidades completas para certificados fuertes |
| MIII | Todas las trazas y traducciones, identidad/orden, receta | Traducir antes de receta y agregado; misma pi, todos los escenarios |
| MIV | Nodos/hojas, E,S,I,D,w y calibraciones | Reloj causal, soporte común, mediciones completas en ruta fuerte |
| MVI semántica | Todas las completaciones, Jtask, Phi, protocolo | Unión completa, cobertura, no vaciedad, dominio, constancia |
| Ley y masas | Árbol completo, filas racionales y V parcial | Ley legítima; partición foliar; PVS solo si M?=0 |
| Hard | Datos completos o testigos decididos del alcance solicitado | Restricciones separadas del árbol; refutaciones no borran hojas |
| MVII | CAG,O,W,PVS y hard de la misma instancia/pi | Bloque compatible, producto de preórdenes, frontera y alcance |
| Selector | Frontera y regla explícita | Valor solo dentro del dominio de la regla; FP1 requiere alcance exhaustivo |

La receta CAG no puede recibir como entrada un conjunto de hojas filtrado por la tarea cuyo significado dependa del propio CAG. El evaluador puede consumir un CAG ya construido si se declara ese DAG, pero FP1 usa la tarea tabulada fijada como primitiva y no necesita ese ciclo potencial.

La cobertura de consultas de MII/MIV/semántica se comprueba sobre las salidas de MV, que a su vez se verifican contra las filas causales. No se demuestra cobertura de mundo real; se demuestra cobertura del modelo declarado.

## 3. R-INT-01 — Teorema 10.1: determinación por dependencias acíclicas

**Enunciado revisado.** Sea G=(N,E) un DAG finito. Para cada v, sea F_v un constructor funcional definido sobre los registros de sus padres que puedan alcanzarse, y sea fijo todo dato primitivo. Si F_v no depende del orden de visita ni de estado externo mutable, existe una única asignación r_v=F_v((r_u)_{u∈pa(v)}). Cualquier orden topológico la produce.

La fórmula P03363 usa una flecha total. En FP1 se interpreta sobre registros enriquecidos: la ausencia de un valor se representa por un registro de dominio/diagnóstico determinado. No se interpreta como una función parcial que pueda carecer incluso de registro para una tupla alcanzada. La ausencia de valor y la ausencia de resultado del constructor son diferentes.

### Prueba revisada

1. Todo DAG finito tiene una enumeración topológica v1,…,vn. La existencia se obtiene eliminando sucesivamente un nodo sin predecesores: si no existiera ninguno, seguir predecesores dentro de un conjunto finito repetiría un nodo y formaría un ciclo.
2. Para cada nodo sin padres, F_v recibe únicamente primitivas fijas. Su resultado existe y es único por la hipótesis de función definida.
3. Supónganse determinados los registros de los primeros k nodos. Todos los padres de v_{k+1} están entre ellos. El argumento completo de F_{v_{k+1}} está determinado y su resultado existe y es único. La inducción construye una asignación para todos los nodos.
4. Si r y r' satisfacen las mismas ecuaciones, coinciden en los nodos sin padres. Repetir la inducción topológica da igualdad en cada nodo. La asignación es única.
5. Cualquier otro orden topológico también produce una asignación que satisface esas ecuaciones; por unicidad es la misma.

### Necesidad de conservar las hipótesis

- Con un constructor parcial sin registro en la tupla alcanzada, la existencia falla aunque el grafo sea un solo nodo. Registrar explícitamente «valor fuera de dominio» resuelve el problema a nivel de registros, sin inventar el valor.
- Si un nodo consulta un reloj externo o un contador mutable compartido, dos órdenes de cálculo pueden dar resultados distintos aunque el DAG sea el mismo.
- Un ciclo puede tener cero soluciones (`r=1−r` sobre bits) o varias (`r=r`); la prueba no aplica. No se afirma que todo sistema cíclico sea irresoluble, solo que la aciclicidad da esta garantía suficiente.
- Determinismo no implica corrección: un constructor que siempre devuelve «éxito» también es determinista. Los teoremas modulares y las guardas son requisitos adicionales.

**Dictamen.** Válido bajo la lectura funcional expresada por S1. No requiere reparar el enunciado matemático. La Specification debe conservar un constructor determinista de registros y distinguir `NOT_EVALUATED` operativo de un registro semántico de fuera de dominio.

## 4. R-INT-02 — Teorema 10.2: ensamblaje correcto

### Hipótesis operativas completas

Se verifican todas las siguientes para la conclusión fuerte. Una presentación parcial puede producir resultados modulares útiles sin satisfacerlas todas.

| Grupo | Hipótesis que se utiliza efectivamente |
|---|---|
| Identidad | M,beta,gamma,c0,H fijos; Pi objetivo finita y no vacía; todas las referencias preservan pi y ocurrencias |
| Causalidad | Inicialización realizada formalmente; información legítima; políticas localmente admitidas; B/U completas en todos los nodos usados; todas las hojas llegan a H |
| Escenarios | Xi común no vacío; palabras exógenas reales y distintas; cada pi tiene exactamente una hoja por palabra; ninguna hoja omitida |
| Funcionalidad | Perfiles requeridos definidos y calibrados; índices comunes; Psi cubre D_f; D_f saturado y f constante en cada fibra |
| Multiescala | Relación conjunta sobre todas las consultas; vistas y puertos tipados; unión natural exacta; identidades de demanda y unidades comunes |
| Recursos | Todas las cantidades necesarias para los certificados fuertes están definidas sobre todas las consultas, incluso raíz y políticas luego refutadas |
| CAG | Identidades, significado y traducciones requeridos definidos; orden de conservación correcto para receta; traducir antes de operar; pi singleton; Xi no vacío |
| Bienestar | Reloj 0…H, E/S/I/D separados; soporte/calibraciones comunes; D=I y mediciones completas de todas las hojas |
| Evidencia | Jtask parcial a conjuntos no vacíos, tarea parcial; protocolo declarado correcto; en FP1 lector exacto y admisión de certificados canónicos de ambos valores |
| Probabilidad | Ley legítima por política, sin derivarla de causalidad; PVS definida para toda pi, equivalente a M?=0 con esa ley |
| Hard | Restricciones fijadas y decididas sin contradicción para todas las políticas; no filtran retroactivamente árboles ni mediciones |
| Comparación | Cuatro criterios definidos en el bloque común Pi; receta y modo CAG comunes, funcionalidad y bienestar con índices fijos, PVS comparable |
| Alcance | Pi es exactamente la familia objetivo enumerada; no se infiere cobertura de estrategias no enumeradas |

La fila Recursos explicita el dominio de la suma de MII Definición 4.6. Decidir hard no implica por sí solo que todas las demandas estén definidas: un exceso conocido basta para refutar una política aunque otra consulta tenga datos ausentes. Por eso la promesa fuerte «certificados de recursos sobre todas las consultas» exige la cobertura adicional. Esto es una explicitación conservadora de los dominios modulares invocados por 10.2; no se utiliza el criterio hard como sustituto de su guarda.

### Dependencia precisa de la reparación de 8.6

S1 Teorema 8.6 necesita la enmienda F1-ED-01 de `REVIEW_VI_VII.md`: disponer de un lector exacto no obliga al protocolo a admitir todos sus certificados canónicos. Un protocolo que solo admite certificados positivos, con Sem(h)={p,q} y Phi(p)=Phi(q)=0, tiene h∈D* pero h∉D_V. La semántica es decisiva; el veto protocolario impide la conclusión DV=D*.

La prueba general de 10.2 puede operar con un evaluador parcial legítimo sin postular DV=D*: si ya se acreditan todas sus restantes hipótesis, incluida PVS definida, basta consistencia de los certificados efectivamente admitidos. Sin embargo, **la efectividad y dominio exacto prometidos por FP1** usan 8.6 reparado. `FP1_EXACT_ENUM_V1` admite y genera A=Sem(h) para cada h∈D*, con v=0 o v=1 según su imagen. Así:

1. Todo certificado aceptado implica ∅≠Sem(h)⊆A⊆D_Phi y Phi[A]={v}; luego h∈D*.
2. Si h∈D*, A=Sem(h) satisface esas guardas y está expresamente admitido; el constructor lo genera y entrega V(h)=v.
3. Por ambas inclusiones, DV=D*. El procedimiento no depende de que un usuario aporte voluntariamente un certificado.

El testigo agua/hábitat de S1 dice solo que se admite el lector exacto (P03615). Para usarlo como testigo de la Specification efectiva se añade expresamente esta capacidad de certificación canónica. No se afirma que la admisión del lector por sí sola la pruebe.

### Prueba revisada por componentes

**1. Causalidad y portadores de procedencia.** Teoremas 7.3–7.4 dan árboles finitos correctos y completos, con al menos una hoja por política y completaciones no vacías de cada consulta. La guarda de escenarios construye una biyección e_pi:Xi→F_pi. Toda referencia posterior a `(pi,xi,t)` se resuelve en una única ocurrencia del árbol de pi. Dos políticas conservan RunKey distintos aunque los datos físicos coincidan. La suficiencia causal real permanece como premisa de interpretación del modelo.

**2. Funcionalidad sin sustitución causal ilegítima.** En los puntos alcanzados P, se tiene f:P⇀O y Psi:P⇀Z con D_f⊆D_Psi. Definir D_bar=Psi(D_f) y f_bar(Psi(p))=f(p). Constancia hace único el valor; saturación impide que un punto fuera de D_f comparta imagen con un punto dentro. Por tanto D_f=Psi^{-1}(D_bar) y f=f_bar∘Psi como funciones parciales. Los estados originales permanecen disponibles; la factorización solo conserva f en P, no cualquier tarea ni dinámica.

**3. Relación conjunta y recursos.** Las vistas son proyecciones del mismo R_pi con claves compartidas. La igualdad comprobada con su unión natural excluye filas espurias y pérdida de correlaciones. Cada cantidad de demanda entra una sola vez por identidad y en su unidad. La completitud de recursos permite calcular todas las sumas locales y compararlas con cada presupuesto requerido. Una violación modifica factibilidad, no R_pi, Q_pi, F_pi ni las mediciones.

**4. Capacidad generativa.** Para cada traza común e_pi,xi la receta r produce Ach_r(e_pi,xi), con sus testigos temporales. Para modo posible, se toma la unión sobre Xi; para modo robusto, la intersección sobre Xi. Xi no vacío evita garantía universal vacía. La traducción se aplica antes de esas operaciones porque, en general, imagen de una intersección no equivale a intersección de imágenes. Se añade el origen según la definición canónica, sin fabricar un testigo de logro futuro para esa inclusión estructural. Todos los testigos pertenecen a la misma pi.

**5. Bienestar.** Las mediciones por nodo generan registros completos de hoja conservando E,S,I,D,w. La comparación usa el producto de las escalas comunes sobre `(xi,carrier,t,dimension)`; por 6.2 es un preorden. Su dominio no cambia entre parejas. El registro completo distingue trayectorias con idéntico final y daños intermedios distintos. Soporte vacío puede producir equivalencia vacua; no acredita existencia.

**6. Evidencia y probabilidad.** Para cada consulta, la semántica se construye solo cuando todas sus completaciones tienen referencias, y es no vacía. Un certificado con cobertura y constancia acredita un único v; dos certificados correctos no pueden discrepar, porque comparten al menos un significado de Sem. La lectura/certificación canónica FP1 da exactamente el dominio D*. Una ley legítima propaga masa desde la raíz y conserva suma uno. F+={hojas con V=1}, F−={hojas con V=0}, F?={hojas fuera de DV} particionan F_pi; por aditividad M++M−+M?=1. PVS está definida precisamente cuando M?=0 y entonces vale M+. Las hojas nulas siguen existiendo y pueden tener V=0 o fuera de dominio; ninguna inferencia universal se obtiene solo de PVS=1.

**7. Producto, factibilidad y frontera.** Sobre el bloque completo, inclusión de CAG, producto funcional terminal por escenarios, producto de bienestar y orden racional de PVS son preórdenes. Su conjunción es reflexiva porque cada componente lo es; es transitiva porque cada comparación encadenada usa las mismas coordenadas y preórdenes. Su parte estricta es irreflexiva y transitiva. Con todos los hard decididos, Pi_feas queda exactamente determinada. Evaluar todos los pares y conservar los elementos sin dominador estricto produce exactamente Fr(Pi_feas).

**8. Existencia de un maximal, sin selección tácita.** Si Pi_feas es finito no vacío y no hubiera maximal, desde cualquier elemento se podría seguir a un dominador estricto, luego a otro, indefinidamente. La finitud obligaría a repetir un elemento; la transitividad estricta daría que un elemento domina estrictamente a sí mismo, contradicción. Por tanto la frontera no es vacía. Puede contener varios elementos, incluso equivalentes; no se deduce selección única. Si Pi_feas es vacío, su frontera es vacía y no se crea una política factible.

**9. Simultaneidad de conclusiones.** Las dependencias son acíclicas y comparten la misma instancia inmutable. Todas las conclusiones anteriores conservan kappa, política, escenario, ocurrencia, dominio y regla. Teorema 10.1 hace determinada su composición; los argumentos modulares hacen correctos sus valores bajo las respectivas guardas. No se intercambia un testigo entre componentes para producir un resultado conjunto más favorable.

### Contraejemplos a generalizaciones no autorizadas

- C(pi_a)=1,W(pi_a)=0 y C(pi_b)=0,W(pi_b)=1 satisfacen dos existenciales separados, pero ninguna pi satisface ambos. El registro integrado no puede mezclar sus testigos.
- Dos estados `(1,0,regular)` y `(1,0,estres)` comparten el resumen funcional (1,0); una tarea que exige ambos servicios en estrés da respectivamente 1 y 0. Su suficiencia para O no se transporta a Phi.
- Tener una tabla bijectiva de IDs de escenario y hojas no prueba que los escenarios sean sus palabras exógenas. La verificación debe usar las secuencias u de MV, sin crear IDs por rama para ocultar fibras múltiples.
- Un conjunto vacío de realizaciones volvería trivial un universal y eliminaría el significado de garantía robusta; Pi, Xi y las completaciones no vacías son hipótesis activas.
- Evaluar únicamente políticas sin excedente presupuestario antes de construir bienestar no acredita la conclusión fuerte de registros completos de toda Pi.
- Si falta PVS para una política, una frontera entre las restantes puede ser relativa; no recibe automáticamente la etiqueta exhaustiva de la familia objetivo.

**Dictamen.** Correcto con las hipótesis y dominios explicitados. Para FP1, la prueba usa expresamente la reparación de 8.6 y la cobertura de recursos; no se aplica el original de 8.6 como si lector exacto implicara admisión de certificados.

## 5. R-INT-03 — Teorema 10.3: terminación relativa a presentación efectiva

**Hipótesis.** Todos los datos que utiliza el procedimiento tienen tablas finitas explícitas y dominios decidibles; igualdad, orden y operaciones son efectivas y terminantes. Si se agrega una construcción, su terminación debe demostrarse. El DAG contiene un número finito de nodos y se usa la expansión causal de profundidad H finita con ramificación finita.

### Prueba revisada

1. Cada política genera un número finito de nodos por inducción de nivel. Hay un número finito de políticas. Un bloqueo produce un diagnóstico finito de la obligación faltante; no se exige ejecutar un programa del usuario para decidir si la fila aparecerá en el futuro.
2. Cada validación de tabla, cobertura, referencia, fibra, comparación o correspondencia usa recorridos de conjuntos finitos. Igualdad nominal es decidible; racionales canónicos permiten comparación exacta mediante productos cruzados de enteros.
3. La unión natural puede enumerarse mediante un producto cartesiano finito y filtrado de claves; no se necesita asumir rendimiento polinomial. Las recetas usan tiempos y ventanas finitos; referencias semánticas son conjuntos finitos, y sus imágenes por Phi se enumeran completamente.
4. La ley usa multiplicaciones y sumas de racionales finitos en un árbol finito. Las comparaciones y búsqueda de dominadores usan a lo sumo todos los pares del bloque finito.
5. El DAG compone un número finito de procedimientos terminantes. Por inducción topológica, termina el cálculo de los registros alcanzables. Bajo las guardas de 10.2, los valores obtenidos son los correctos por esa prueba.

La garantía incluye construir valores cuando sus guardas se satisfacen. Un programa que devuelve siempre «no certificado» no realiza el procedimiento demostrado. A la inversa, terminar con una respuesta no basta para demostrar que esa respuesta es correcta.

### Límites

- Una descripción textual finita puede incluir un programa que no termina. La mera finitud del archivo no prueba efectividad ni decidibilidad de su código.
- El número de ramas puede crecer exponencialmente con H y la aritmética exacta puede requerir enteros grandes. No hay garantía de tiempo o memoria prácticos.
- Un límite operativo de recursos puede interrumpir una implementación. `RESOURCE_EXHAUSTED` no significa que el objeto matemático esté fuera de dominio, que no exista una alternativa o que la frontera sea vacía.
- El teorema no incluye horizonte infinito, incertidumbre estructural no enumerada, algoritmos aproximados ni comparadores de oráculo. Cada extensión requiere hipótesis propias.

**Dictamen.** Válido dentro de la presentación efectiva. FP1 satisface esa presentación con tablas y racionales, siempre condicionado a recursos computacionales suficientes; F1 especifica el procedimiento y no ha ejecutado el Kernel.

## 6. Testigo integrado agua/hábitat

La comprobación siguiente es algebraica sobre el ejemplo sintético S1. No es evidencia empírica y no se registra como test ejecutado.

Se fijan H=2; políticas pi_a, pi_h y pi_ah que instalan respectivamente B={a}, {h} y {a,h}, y después mantienen. Cada instalación produce dos ramas, regular r y estrés s. Para la serialización FP1 se deben declarar explícitamente palabras exógenas distintas de longitud dos, por ejemplo `(r,keep)` y `(s,keep)`; el segundo input keep es una entrada formal de mantenimiento. No se infiere una palabra de longitud H a partir de un mero nombre r o s.

Cada política tiene 1 raíz, 2 nodos intermedios y 2 hojas, con reloj {0,1,2}. El conjunto Pi completo tiene 15 ocurrencias identificadas; la raíz física igual no fusiona las tres raíces de políticas distintas. Las observaciones intermedias pueden ser iguales porque la segunda acción de las tres políticas es mantenimiento en ambas ramas.

El perfil es `(1[a∈B],1[h∈B])`, cero en la raíz, calibración identidad. Depende solo de Sigma(x)=B, de modo que el descenso funcional es exacto. La equivalencia generativa es igualdad de conjuntos de servicios y la conservación es inclusión; la traducción es identidad. Para la receta hold,1, la traza `(∅,B,B)` acredita B con inicio t=1 y ventana hasta t=2. Ambos escenarios producen la misma identidad, por lo que el CAG robusto es `{∅,B}`. La identidad `{a,h}` no contiene, como elementos de su CAG, las identidades `{a}` y `{h}` por simple inclusión interna de servicios.

Los portadores l1,l2 existen durante todo el reloj; w_l1 es indicador de agua y w_l2 indicador de hábitat. La plantilla tiene seis índices `(carrier,t,dimension)` y medición completa. Las demandas d_a y d_h son esos mismos indicadores de servicio y el presupuesto instantáneo es d_a+d_h≤1, incluso en raíz. Pi_ah tiene demanda 2 después de instalar, de modo que es refutada sin borrar sus dos ramas ni sus mediciones.

Cada hoja tiene referencia singleton `(B,xi)`. Phi exige B no vacío en regular y ambos servicios en estrés. El protocolo efectivo admite y genera los certificados canónicos de ambos valores, conforme a 8.6 reparado. Las probabilidades de las ramas iniciales son 3/4 y 1/4; mantenimiento tiene peso 1.

| Política | CAG robusto | Funcionalidad terminal | Bienestar de l1 y l2 | Veredictos (r,s) | PVS | Presupuesto |
|---|---|---|---|---|---|---|
| pi_a | {∅,{a}} | (1,0) | (0,1,1) y (0,0,0) | (1,0) | 3/4 | Cumple |
| pi_h | {∅,{h}} | (0,1) | (0,0,0) y (0,1,1) | (1,0) | 3/4 | Cumple |
| pi_ah | {∅,{a,h}} | (1,1) | (0,1,1) y (0,1,1) | (1,1) | 1 | Refutado |

La factibilidad es exactamente {pi_a,pi_h}. Sus CAG son incomparables por inclusión; sus perfiles y bienestar mejoran coordenadas distintas; sus PVS coinciden. Ninguna domina estrictamente a la otra. La frontera exhaustiva de esta Pi es {pi_a,pi_h}. No hay una elección única sin regla adicional.

En la raíz de pi_a y pi_h, Sem reúne un significado con veredicto 1 y otro con 0. No es constante, por lo que V de la raíz queda fuera de dominio aunque todas las hojas tengan veredicto y la PVS sea 3/4. En la raíz de pi_ah, ambos significados tienen veredicto 1, por lo que el certificado canónico A=Sem entrega V=1 aun sin seleccionar una única realización. Esto muestra de forma concreta la separación entre lectura semántica exacta, unicidad de realización y unicidad de veredicto.

La coherencia de este testigo demuestra no vacuidad formal de la ruta fuerte. No constituye prueba de originalidad del programa ni de que el criterio integrado sea adecuado para una aplicación real.

## 7. Normalización explícita del testigo fuente

Durante el contraste adversarial se detectaron dos agrupaciones defectuosas en las fórmulas del ejemplo original, y se cotejaron los delimitadores OMML correspondientes. P03581 agrupa incorrectamente los componentes del perfil de indicadores; P03584 agrupa la aplicación Sigma y el par estado–tiempo de manera que no representa claramente la pareja anunciada. No se corrige el DOCX silenciosamente.

La lectura tipada adoptada es:

`O(x,t) = (1[a∈Sigma(x)], 1[h∈Sigma(x)])`,

`psi(x,t) = (Sigma(x), t)`.

P03582 exige dos espacios de valores binarios, y P03583 afirma que el perfil depende únicamente de Sigma(x); estas dos frases y la construcción completa del ejemplo determinan la interpretación. La primera expresión debe ser un vector de exactamente dos indicadores, no una tupla que incluya una constante y una concatenación. La segunda debe conservar organización y tiempo, no recibir la función Sigma como coordenada ni fusionar x con t.

La normalización repara la agrupación de notación y deja inalteradas las funciones y resultados usados en la prueba escrita y en el fixture de conformidad: perfil de raíz (0,0), perfiles terminales (1,0),(0,1),(1,1) y reducción a organización/tiempo. No añade un supuesto científico ni cambia las PVS o la frontera calculadas. Se incorpora a la capa explícita de enmiendas S2; la fuente S1 queda intacta.

## 8. Precisiones entregadas al Integrador

1. **Constructor de registros total.** Mantener el sentido funcional de 10.1; una guarda fallida produce un registro de diagnóstico, no un valor inventado ni una ausencia silenciosa de constructor.
2. **Cobertura de recursos fuerte.** Exigir todos los valores por consulta y demanda para la conclusión completa, aunque una refutación hard ya esté disponible en otro punto.
3. **Reparación 8.6 propagada.** `FP1_EXACT_ENUM_V1` debe admitir/generar certificados canónicos para 0 y 1. El testigo sintético y la igualdad DV=D* dependen de ello.
4. **Modos CAG comunes.** La prueba del producto admite CAG posible o robusto cuando el modo y la receta se mantienen fijos en el bloque. No declarar «robusto obligatorio» si el formato admite ambos.
5. **Selección y alcance alineados.** La regla general de selección puede tener otro dominio, pero la versión FP1 solo selecciona sobre frontera exhaustiva conforme a su formato. Una frontera relativa conserva su resultado sin convertirse en elección global.
6. **Suficiencia limitada.** El descenso funcional y recomposición relacional no certifican automáticamente suficiencia causal, semántica ni probabilística. Mantener las claves y originales necesarios para cada consulta.

Estado de este tramo: inventario y revisión deductiva de integración completados; tres teoremas respaldados bajo las hipótesis explicitadas; límites y dependencias registrados. La aceptación de F1, la auditoría separada y la continuidad del paquete se determinan fuera de este informe.
