**Matemática Genius**

**Exposición matemática autocontenida de Genius, que permita seguir las definiciones, las demostraciones y la integración sin depender del código.**

**El contenido:**

**1. Fundamentos y lenguaje común. Propósito de la teoría, supuestos, notación, tipos de objetos y distinciones esenciales: realidad y representación; posibilidad y probabilidad; capacidad, bienestar y viabilidad; falsedad e indefinición.**

**2. Desarrollo completo de los ocho módulos.**

  -------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Módulo**                         **Contenido**
  ---------------------------------- --------------------------------------------------------------------------------------------------------------------------
  **0 --- Representación**           **Estados, historias, información y condiciones que permiten representar o reducir un sistema sin perder lo necesario.**

  **I --- Funcionalidad**            **Funciones, perfiles funcionales, calibración y comparación mediante órdenes.**

  **II --- Multiescala**             **Sistemas y subsistemas, interfaces, recursos compartidos y condiciones de composición.**

  **III --- Capacidad generativa**   **Identidad organizacional, origen, generación, conservación, acumulación y CAG posible o robusta.**

  **IV --- Bienestar**               **Portadores, dimensiones, tiempo, mediciones y reglas explícitas de comparación.**

  **V --- Futuros**                  **Inicialización, políticas, información disponible, escenarios y trayectorias causales.**

  **VI --- Evidencia y PVS**         **Significado, fidelidad, evaluación, incertidumbre, leyes probabilísticas y Probabilidad de Vida Sostenida.**

  **VII --- Decisión**               **Restricciones, comparación conjunta, alternativas maximales y condiciones para seleccionar.**
  -------------------------------------------------------------------------------------------------------------------------------------------------------------

**Cada módulo tendría: interpretación conceptual, definiciones formales, hipótesis, ecuaciones, proposiciones, demostraciones y condiciones de aplicación.**

**3. Teoremas de integración. Cómo se conectan los módulos, qué información intercambian y por qué la composición conserva dominios, significados, políticas y testigos compatibles.**

**4. Ejemplo completo. Una misma instancia recorrida desde su representación hasta su frontera de alternativas, mostrando los cálculos y las razones de cada resultado.**

**5. Contraejemplos esenciales. Casos que demuestran por qué son necesarias las condiciones: perder correlaciones, mezclar políticas, ignorar daños intermedios o confundir probabilidad uno con garantía universal.**

**6. Dictamen de cierre. Qué está demostrado, bajo cuáles hipótesis, qué cubre la implementación finita y cuáles son resultados legítimamente parciales o incomparables.**

**Por su extensión, lo dividiría en entregas numeradas, manteniendo una notación y una numeración de teoremas comunes.**

**Entrega 1 --- Fundamentos y lenguaje común de Matemática Genius**

Matemática Genius estudia cómo representar sistemas, describir sus funciones y organizaciones, construir sus futuros posibles y comparar alternativas atendiendo a capacidad generativa, bienestar y condiciones de vida sostenida.

Su estructura permite relacionar esas preguntas manteniendo el significado propio de cada una. Una organización puede ofrecer más posibilidades generativas y, al mismo tiempo, producir peores condiciones para determinados portadores de bienestar. Una trayectoria puede alcanzar un destino favorable después de haber atravesado estados perjudiciales. Una política puede funcionar con probabilidad uno sin garantizar el resultado en todas las trayectorias posibles.

La formalización debe permitir expresar esas diferencias y demostrar cuándo pueden combinarse sus resultados.

Esta primera entrega establece el lenguaje que utilizarán los módulos 0--VII. La numeración pertenece a esta exposición: introducir una definición o numerar una proposición aquí no supone atribuirle originalidad matemática.

**El punto de partida: cuatro niveles de justificación.**

Una aplicación de Genius relaciona cuatro niveles:

  ------------------------------------------------------------------------------------------------------------------------------------
  **Nivel**    **Qué contiene**                                                       **Cómo se justifica**
  ------------ ---------------------------------------------------------------------- ------------------------------------------------
  Matemático   Conjuntos, funciones, relaciones, órdenes y medidas                    Definiciones y demostraciones

  Semántico    Qué representan los objetos y qué significa satisfacer una condición   Interpretaciones y correspondencias explícitas

  Empírico     Dinámica, observaciones, recursos y efectos de un sistema concreto     Evidencia y contrastación

  Normativo    Condiciones exigidas, daños inadmisibles y reglas de elección          Criterios declarados
  ------------------------------------------------------------------------------------------------------------------------------------

Por ejemplo, una demostración puede establecer que cierto algoritmo encuentra todas las alternativas maximales de una relación. Aplicar ese resultado a un bosque requiere, además, justificar qué representan las alternativas, cómo se obtuvieron sus datos y qué criterios autorizan compararlas.

Cada afirmación llevará consigo las hipótesis de las que depende. Las propiedades de una instancia deberán comprobarse o declararse como premisas; asignarles un nombre no las demuestra.

Los principios que siguen son reglas de construcción de la teoría. No se presentan como una axiomatización mínima ni lógicamente independiente.

**Convención 1.1. Objetos y ámbitos de interpretación.**

Trabajamos con conjuntos o tipos explícitamente declarados. Cada variable pertenece a un conjunto determinado, y cada operación especifica sobre cuáles entradas puede utilizarse.

La notación básica será:

  --------------------------------------------------------------------------------
  **Símbolo**        **Significado**
  ------------------ -------------------------------------------------------------
  $$\mathfrak{M}$$   Marco de representación

  $$\beta$$          Modelo del proceso, con sus hipótesis y parámetros

  $$\gamma$$         Contexto efectivo, incluidas las intervenciones pertinentes

  $$c_{0}$$          Condición inicial declarada

  $$H$$              Horizonte considerado

  $$x_{t}$$          Estado causal en el instante $t$

  $$\iota_{t}$$      Información disponible para el decisor

  $$\Sigma_{t}$$     Descripción estructural u organizacional

  $$\pi$$            Política o regla de actuación

  $$\xi$$            Escenario de entradas externas

  $$\mathbf{e}$$     Ejecución o trayectoria concreta
  --------------------------------------------------------------------------------

Estas distinciones tienen consecuencias operativas. La política actúa utilizando información disponible:

$$\theta_{t} = \pi_{t}\left( \iota_{t} \right).$$

Su información puede ser insuficiente para determinar completamente $x_{t}$. A su vez, $\Sigma_{t}$puede conservar aspectos organizacionales y omitir información necesaria para predecir la evolución.

El módulo 0 establecerá cuándo una representación conserva lo necesario para una pregunta. El módulo V comprobará las condiciones de legitimidad de las políticas y de construcción de las ejecuciones.

**Definición 1.1. Función parcial.**

Una función parcial de $A$en $B$, escrita

$$f:A \rightharpoonup B,$$

está determinada por:

$$D_{f} \subseteq A,\ \widetilde{f}:D_{f} \rightarrow B.$$

El conjunto $D_{f}$es su **dominio efectivo**. Escribimos $f(a)$cuando $a \in D_{f}$.

El dominio forma parte del objeto matemático. Por tanto, dos funciones parciales $f,g:A \rightharpoonup B$son iguales exactamente cuando:

$$D_{f} = D_{g}\ \text{y}\ \forall a \in D_{f}:\text{~}f(a) = g(a).$$

La coincidencia de valores donde ambas funciones están definidas no basta para establecer su igualdad.

Por ejemplo, consideremos:

$$A = \left\{ a,b \right\},\ D_{f} = \left\{ a \right\},\ D_{g} = \left\{ a,b \right\},$$

con:

$$f(a) = g(a) = 0,\ g(b) = 0.$$

Aunque coinciden en su dominio compartido, $f \neq g$. La función $g$atribuye a $b$un valor que $f$no proporciona.

Esta diferencia será decisiva al reducir representaciones, transportar evaluaciones y comparar alternativas.

**Definición 1.2. Registro de dominio y valor.**

Para conservar explícitamente la diferencia anterior, introducimos una etiqueta $\dagger_{f}$ajena a $B$y definimos:

$$\widehat{f}(a) = \left\{ \begin{matrix}
\left( definido,f(a) \right), & a \in D_{f}, \\
\left( fuera\text{~}de\text{~}dominio, \dagger_{f} \right), & a \notin D_{f}.
\end{matrix} \right.\ $$

Este registro permite describir la situación de cualquier $a \in A$.

La etiqueta $\dagger_{f}$no tiene valor numérico ni recibe un orden de calidad. Por ejemplo, una medición de bienestar ausente no adquiere por ello el valor cero.

También debemos distinguir tres situaciones:

-   Se ha establecido que $a \notin D_{f}$.

-   Todavía no sabemos si $a \in D_{f}$.

-   Los datos suministrados no constituyen una presentación válida del objeto.

La segunda describe nuestro conocimiento; la tercera impide aplicar correctamente el contrato. Ninguna equivale a un valor definido de $f$.

La definición matemática de $\widehat{f}$tampoco garantiza que exista un algoritmo capaz de calcularla en cualquier presentación. **Definir un objeto y disponer de un procedimiento efectivo para obtenerlo son obligaciones diferentes.**

**Proposición 1.1. Dominio de una composición parcial.**

Sean:

$$f:A \rightharpoonup B,\ g:B \rightharpoonup C.$$

La composición $g \circ f$tiene dominio:

$$D_{g \circ f} = \left\{ a \in D_{f}:f(a) \in D_{g} \right\},$$

y, en ese dominio:

$$(g \circ f)(a) = g\left( f(a) \right).$$

**Demostración.** Para obtener $g\left( f(a) \right)$, primero debe existir $f(a)$, lo que exige $a \in D_{f}$. Después, ese resultado debe pertenecer al dominio de $g$. Si ambas condiciones se cumplen, la composición tiene un valor determinado; si alguna falla, la evaluación indicada no está definida. $\square$

Esta regla acompañará todas las cadenas entre módulos. Que exista una descripción estructural no acredita todavía que una función, traducción o evaluación posterior pueda aplicarse a ella.

**Proposición 1.2. Dominio de una evaluación conjunta.**

Sea una familia de funciones parciales sobre un mismo conjunto $A$:

$$f_{i}:A \rightharpoonup B_{i},\ i \in I.$$

El registro conjunto de todos sus valores es:

$$F(a) = \left( f_{i}(a) \right)_{i \in I}.$$

Su dominio es:

$$\boxed{D_{F} = \bigcap_{i \in I}^{}D_{f_{i}}.}$$

**Demostración.** El registro contiene un valor para cada componente requerida. Por tanto, existe exactamente cuando $a$pertenece al dominio de todas ellas. $\square$

Es posible construir, por separado, el registro de diagnósticos:

$$\widehat{F}(a) = \left( {\widehat{f}}_{i}(a) \right)_{i \in I}.$$

Este segundo objeto conserva cuáles componentes están definidas y cuáles no. Disponer de él no significa disponer del registro completo $F(a)$.

En el módulo I, esta distinción impedirá eliminar una función faltante para presentar como completo un perfil funcional.

Si se permite una familia vacía de componentes, su producto vacío sólo registra que no se han exigido componentes. No acredita por sí mismo ninguna propiedad sustantiva del sistema.

**Definición 1.3. Predicado parcial y certificación positiva.**

Un predicado parcial es una función:

$$P:A \rightharpoonup \left\{ 0,1 \right\}.$$

Dentro de su dominio, $1$representa satisfacción y $0$representa incumplimiento de la condición declarada.

Definimos el gate de certificación positiva:

$${Cert}_{1}\lbrack P\rbrack(a) = \left\{ \begin{matrix}
1, & a \in D_{P}\text{~y~}P(a) = 1, \\
0, & \text{en~otro~caso}.
\end{matrix} \right.\ $$

La pertenencia al dominio se comprueba antes de evaluar $P(a)$.

  -------------------------------------------------------------------------------
  **Situación**                               **Predicado**   **Gate positivo**
  ------------------------------------------- --------------- -------------------
  Condición satisfecha dentro del dominio     $$P(a) = 1$$    $$1$$

  Condición incumplida dentro del dominio     $$P(a) = 0$$    $$0$$

  Entrada fuera del dominio                   Sin valor       $$0$$
  -------------------------------------------------------------------------------

Por tanto:

$${Cert}_{1}\lbrack P\rbrack(a) = 0$$

no permite distinguir, por sí solo, entre incumplimiento e indefinición. El diagnóstico debe conservarse aparte.

Además, este gate es una definición matemática total; su computabilidad requiere hipótesis adicionales. Un programa no demuestra la condición por recibir un booleano que diga que está certificada.

Para dos predicados parciales, la conjunción que exige evaluar ambos se define sobre:

$$D_{P \land Q} = D_{P} \cap D_{Q}.$$

La conjunción de sus gates es otro objeto. Confundir ambos permitiría convertir una ausencia de certificación en una falsedad que no ha sido establecida.

**Definición 1.4. Ámbito experimental y testigo.**

Para identificar el ámbito de una evaluación, escribiremos:

$$\kappa = \left( \mathfrak{M},\beta,\gamma,c_{0},\pi,H \right).$$

Esta tupla registra el marco, modelo, contexto, condición inicial, política y horizonte pertinentes. Su mera escritura no acredita la validez de esos datos.

Una ocurrencia completa conserva además el escenario y la ejecución:

$$\left( \kappa,\xi,e \right),\ e \in {Runs}_{H,\gamma}\left( c_{0};\pi;\xi \right).$$

El término $Runs$representa una familia de realizaciones: un mismo escenario puede admitir más de una ejecución.

Cuando una afirmación requiera una receta generativa, un protocolo de evidencia o una regla de comparación, esas referencias también deberán conservarse. Dos resultados con números iguales pueden pertenecer a ámbitos incompatibles.

Comparar políticas distintas es legítimo cuando la comparación declara qué cambia y qué referencias permanecen comunes.

**Proposición 1.3. Dos éxitos separados no acreditan un éxito conjunto.**

Sean $A$y $B$propiedades de ejecuciones de una familia $\mathcal{F}$. Entonces:

$$\exists e\mathcal{\in F:}A(e) \land B(e)$$

implica:

$$\left( \exists e\mathcal{\in F:}A(e) \right) \land \left( \exists e\mathcal{\in F:}B(e) \right).$$

La implicación inversa es falsa.

**Demostración.** Una ejecución que satisface ambas propiedades sirve como testigo de cada existencia separada.

Para refutar la inversa, consideremos:

$$\mathcal{F =}\left\{ e_{1},e_{2} \right\},$$

con los siguientes valores:

  -----------------------------------------------------------------------
  **Ejecución**                                      $$A$$     $$B$$
  -------------------------------------------------- --------- ----------
  $$\mathbf{e}_{1}$$                                 $$1$$     $$0$$

  $$\mathbf{e}_{2}$$                                 $$0$$     $$1$$
  -----------------------------------------------------------------------

Existe una ejecución que satisface $A$y otra que satisface $B$, pero ninguna satisface ambas. $\square$

En Genius, esto impide combinar el logro generativo de una trayectoria con el bienestar de otra y atribuir el resultado conjunto a una sola realización.

Cuando una afirmación involucre varios componentes, deberán conservarse sus relaciones y testigos compatibles. Las listas separadas de resultados no contienen necesariamente esa información.

**Convención 1.2. Posibilidad, garantía y existencia de realizaciones.**

Sea $A$una propiedad definida sobre todas las ejecuciones de $\mathcal{F}$.

La posibilidad de satisfacerla se expresa mediante:

$$Poss\left( A;\mathcal{F} \right)\text{\:\,} \Longleftrightarrow \text{\:\,}\exists e\mathcal{\in F:}A(e).$$

Para expresar una garantía sobre una familia efectivamente realizable, usamos:

$$Rob\left( A;\mathcal{F} \right)\text{\:\,} \Longleftrightarrow \text{\:\,}\mathcal{F \neq \varnothing \land \forall}e\mathcal{\in F:}A(e).$$

La condición de no vacuidad es explícita. Aunque un universal sobre el conjunto vacío sea verdadero en lógica clásica, no acredita la existencia de una ejecución.

Cuando la familia se organiza por escenarios, también deben comprobarse las condiciones de existencia de realizaciones en cada escenario requerido. Una fibra vacía no se elimina para producir una garantía favorable.

Si $A$es parcial, su dominio debe comprobarse sobre las ejecuciones exigidas por la afirmación.

**Proposición 1.4. El orden de los cuantificadores modifica la capacidad afirmada.**

Sobre conjuntos fijados de políticas $\mathcal{P}$y escenarios $\Xi$:

$$\exists\pi \in \mathcal{P}\text{~}\forall\xi \in \Xi:A\left( \pi,\xi \right)$$

implica:

$$\forall\xi \in \Xi\text{~}\exists\pi \in \mathcal{P:}A\left( \pi,\xi \right).$$

La inversa no vale en general.

**Demostración.** Una política válida para todos los escenarios sirve para cada escenario particular.

Para la inversa, tomemos dos políticas y dos escenarios. La primera política funciona únicamente en el primer escenario, y la segunda únicamente en el segundo. Cada escenario tiene una política favorable, pero no existe una política favorable para ambos. $\square$

Una política puede responder a observaciones durante la ejecución. Lo que se mantiene fijado es la regla de respuesta y la información que puede utilizar. Escoger retrospectivamente una política diferente después de conocer el escenario no acredita que exista una política implementable que garantice el resultado.

El módulo III utilizará esta distinción al definir capacidad generativa robusta.

**Definición 1.5. Comparación mediante un preorden.**

Un preorden sobre un conjunto $C$es una relación $\succeq$que satisface:

$$\forall a \in C:\text{~}a \succeq a$$

y:

$$a \succeq b \land b \succeq c \Longrightarrow a \succeq c.$$

Son las propiedades de reflexividad y transitividad.

Su interpretación se declara para cada criterio. A partir de él definimos:

$${a \sim b\text{\:\,} \Longleftrightarrow \text{\:\,}a \succeq b \land b \succeq a,
}{a \succ b\text{\:\,} \Longleftrightarrow \text{\:\,}a \succeq b \land \neg(b \succeq a).}$$

Dos elementos del bloque comparativo son incomparables cuando:

$$\neg(a \succeq b) \land \neg(b \succeq a).$$

La equivalencia bajo un criterio no exige identidad entre los objetos originales.

La incomparabilidad tampoco equivale a falta de información. Por ejemplo, bajo el orden componente a componente:

$$a = \left( 1,0 \right),\ b = \left( 0,1 \right),$$

ambos perfiles pueden estar completamente determinados y ser incomparables.

En cambio, si falta una componente requerida o no existe calibración común, la comparación puede estar fuera de dominio. Son situaciones distintas que deberán conservar diagnósticos distintos.

Esto permitirá relacionar criterios heterogéneos sin imponer una magnitud universal ni inventar pesos para resolver todos los conflictos.

**Convención 1.3. Forma de las afirmaciones de cierre.**

Los resultados se enunciarán mediante hipótesis explícitas:

$$\text{hip}\overset{ˊ}{\text{o}}\text{tesis~de~la~instancia}\  \Longrightarrow \ \text{conclusi}\overset{ˊ}{\text{o}}\text{n~matem}\overset{ˊ}{\text{a}}\text{tica}.$$

Para cada construcción distinguiremos:

-   Su definición y dominio.

-   Las propiedades demostradas.

-   Las condiciones que permiten calcularla.

-   El alcance de su implementación.

-   Las premisas semánticas, empíricas o normativas de su aplicación.

La integración v6 auditada dispone de una ruta efectiva para la clase finita declarada. Los resultados más generales conservan sus propias hipótesis; por ejemplo, una prueba sobre continuaciones finitas no se extiende automáticamente a restricciones de aceptación de trayectorias infinitas.

Las funciones parciales, las alternativas incomparables y las fronteras con varios elementos son objetos legítimos de esta arquitectura. Sus condiciones de aparición deben quedar definidas y justificadas.

La próxima entrega desarrollará el **Módulo 0: representación, estado, historia y suficiencia**, comenzando por la pregunta que fundamenta las reducciones posteriores: **¿cuándo una descripción conserva exactamente la información necesaria para la consulta que queremos resolver?**

**Entrega 2 --- Módulo 0: representación, estado y suficiencia**

El Módulo 0 establece las condiciones que permiten utilizar una descripción de un sistema para responder preguntas sobre él. Su problema central es determinar **qué información puede omitirse sin modificar las respuestas que necesitamos conservar**.

Una representación puede ser suficiente para medir una función presente y resultar insuficiente para estudiar la evolución del sistema. También puede conservar los futuros posibles y perder información necesaria para calcular sus probabilidades o implementar una política.

Por eso, en Genius, toda afirmación de suficiencia debe indicar **para qué objeto, consulta o proceso se demuestra**.

**Definición 2.1. Historia y estado representado.**

Fijados un marco, un modelo y un contexto, sea:

$$\mathcal{H}_{t}$$

el conjunto de historias causales admisibles hasta el instante $t$.

Una historia contiene los antecedentes que la presentación del sistema considera pertinentes: acontecimientos, interacciones, entradas externas y demás información causal especificada por el modelo.

Una representación del estado es una función:

$$\Gamma_{X,t}^{hist}:\mathcal{H}_{t} \longrightarrow \mathcal{X}_{t},$$

y el estado correspondiente a una historia $h_{t}$es:

$$x_{t} = \Gamma_{X,t}^{hist}\left( h_{t} \right).$$

La función es total sobre las historias admisibles declaradas: toda historia del ámbito tiene un estado representado.

Esta totalidad no prueba todavía suficiencia. Debe demostrarse que las historias identificadas por el mismo estado conservan las propiedades requeridas.

Tampoco acredita que el conjunto $\mathcal{H}_{t}$incluya todos los antecedentes relevantes de un sistema real. La adecuación empírica del modelo conserva su propia obligación de justificación.

Si un efecto relevante atraviesa la frontera elegida para el sistema, debe quedar incorporado en la descripción causal pertinente, por ejemplo como una entrada externa. Omitirlo requiere una justificación de irrelevancia para las preguntas consideradas.

**Convención 2.1. Estado causal, información y organización.**

Conservamos tres objetos con funciones distintas:

$$x_{t},\ \iota_{t},\ \Sigma_{t}.$$

El estado $x_{t}$debe contener la memoria necesaria para la evolución causal que se pretende representar.

La información $\iota_{t}$contiene aquello que el decisor puede utilizar legítimamente.

La descripción $\Sigma_{t}$expresa los aspectos estructurales u organizacionales seleccionados:

$$\Sigma_{t} = \Gamma_{\Sigma,t}\left( x_{t} \right),$$

cuando esa descripción está definida.

La política actúa mediante:

$$\theta_{t} = \pi_{t}\left( \iota_{t} \right).$$

Por tanto, conocer matemáticamente $x_{t}$al describir un experimento no autoriza a una política a utilizar información que no está disponible en $\iota_{t}$.

El estado causal e informacional conjunto puede registrarse como:

$$\zeta_{t} = \left( x_{t},\iota_{t} \right).$$

Esta separación permite distinguir dos clases de memoria: la necesaria para continuar físicamente el proceso y la utilizada por el decisor para actuar.

Una configuración instantánea puede sustituir a una historia cuando se demuestra que conserva la información requerida. La sustitución depende de esa prueba.

**Definición 2.2. Representación suficiente para una consulta.**

Sean:

$$\psi:A \rightharpoonup Q$$

una representación posiblemente parcial, y:

$$f:A \rightharpoonup B$$

la consulta que queremos conservar.

Decimos que $\psi$es **funcionalmente suficiente para** $f$, abreviado $FSuf\left( \psi;f \right)$, cuando existe:

$$\overline{f}:Q \rightharpoonup B$$

tal que:

$$\boxed{f = \overline{f} \circ \psi}$$

como igualdad de funciones parciales.

Esto exige igualdad de dominios y de valores.

La ecuación expresa que podemos responder la consulta utilizando la representación, sin volver a distinguir los objetos originales que ella identifica.

Para cada $q \in {im}\psi$, definimos su fibra:

$$F_{q} = \left\{ a \in D_{\psi}:\psi(a) = q \right\}.$$

La fibra reúne todos los objetos representados mediante la misma descripción.

**Teorema 2.1. Caracterización exacta de la suficiencia funcional.**

Existe un factor $\overline{f}$con:

$$f = \overline{f} \circ \psi$$

si y solo si se cumplen las tres condiciones siguientes.

**Primera: cobertura de los argumentos definidos.**

$$D_{f} \subseteq D_{\psi}.$$

Todo argumento donde la consulta tiene valor debe estar representado.

**Segunda: saturación del dominio.**

Para cada fibra $F_{q}$:

$$F_{q} \subseteq D_{f}\ \text{o~bien}\ F_{q} \cap D_{f} = \varnothing.$$

Una fibra no puede mezclar argumentos donde la consulta está definida con otros donde no lo está.

**Tercera: constancia de los valores.**

En cada fibra incluida en $D_{f}$:

$$\forall a,b \in F_{q}:\text{~}f(a) = f(b).$$

Los objetos que la representación identifica deben recibir la misma respuesta.

**Demostración de necesidad.**

Supongamos:

$$f = \overline{f} \circ \psi.$$

Por la definición de composición parcial:

$$D_{f} = \left\{ a \in D_{\psi}:\psi(a) \in D_{\overline{f}} \right\}.$$

Se obtiene inmediatamente $D_{f} \subseteq D_{\psi}$.

Si dos argumentos pertenecen a la misma fibra, sus imágenes por $\psi$coinciden. Por tanto, ambos pertenecen a $D_{f}$, o ninguno pertenece: la pertenencia depende de que esa imagen común esté en $D_{\overline{f}}$. Esto demuestra saturación.

Cuando ambos pertenecen al dominio:

$$f(a) = \overline{f}\left( \psi(a) \right) = \overline{f}\left( \psi(b) \right) = f(b).$$

Así se obtiene constancia.

**Demostración de suficiencia.**

Supongamos ahora las tres condiciones.

Definimos:

$$D_{\overline{f}} = \psi\left( D_{f} \right).$$

Para $q \in D_{\overline{f}}$, elegimos cualquier $a \in F_{q}$y establecemos:

$$\overline{f}(q) = f(a).$$

La saturación garantiza que todos los integrantes de esa fibra pertenecen a $D_{f}$. La constancia garantiza que el valor no depende del representante.

Si $a \in D_{f}$, entonces $\psi(a) \in D_{\overline{f}}$.

Recíprocamente, si $a \in D_{\psi}$y $\psi(a) \in D_{\overline{f}}$, existe algún $b \in D_{f}$en su misma fibra. Por saturación, también $a \in D_{f}$.

Por tanto:

$$D_{\overline{f} \circ \psi} = D_{f}.$$

En ese dominio, la construcción proporciona:

$$\overline{f}\left( \psi(a) \right) = f(a).$$

La igualdad de funciones parciales queda demostrada. $\square$

El factor construido es único si exigimos:

$$D_{\overline{f}} \subseteq {im}\psi.$$

Fuera de la imagen representada podrían existir extensiones adicionales que no alterasen la composición. La unicidad no se afirma sobre esas extensiones.

**Contraejemplo 2.1. Conservar los valores conocidos no basta.**

Sean:

$$A = \left\{ a,b \right\},\ \psi(a) = \psi(b) = q.$$

Supongamos:

$$D_{f} = \left\{ a \right\},\ f(a) = 7.$$

Todos los valores conocidos de la fibra coinciden, porque solamente conocemos uno. Sin embargo, el dominio no está saturado.

Si definiéramos:

$$\overline{f}(q) = 7,$$

la composición también atribuiría el valor $7$a $b$:

$$\left( \overline{f} \circ \psi \right)(b) = 7.$$

Esto ampliaría indebidamente el dominio de $f$.

Si dejáramos $\overline{f}(q)$indefinido, perderíamos la respuesta existente para $a$.

Ninguna elección permite satisfacer:

$$f = \overline{f} \circ \psi.$$

La representación identifica una distinción de dominio que la consulta necesita conservar.

**Proposición 2.2. Dominio representado seguro máximo.**

Cuando falla la suficiencia global, podemos identificar las fibras donde sí existe una respuesta inequívoca para todos sus representantes.

Definimos:

$$D_{seg} = \left\{ q \in {im}\psi:F_{q} \subseteq D_{f}\text{~} \land \text{~} \mid f\left\lbrack F_{q} \right\rbrack \mid = 1 \right\}.$$

En ese dominio, establecemos:

$$f_{seg}(q) = \text{el~}\overset{ˊ}{\text{u}}\text{nico~elemento~de~}f\left\lbrack F_{q} \right\rbrack.$$

Esta función es segura: su respuesta coincide con $f$en todos los representantes de cada clase admitida.

Además, su dominio es máximo entre los dominios representados que satisfacen esa exigencia.

**Demostración.**

Sea $g$otra función segura definida en algún $q \in {im}\psi$.

Para que su respuesta coincida con $f$en todos los representantes de $q$, deben cumplirse:

$$F_{q} \subseteq D_{f}$$

y:

$$\forall a \in F_{q}:\text{~}f(a) = g(q).$$

Por tanto, $f\left\lbrack F_{q} \right\rbrack$es un singleton y $q \in D_{seg}$. Todo dominio seguro queda incluido en el construido. $\square$

Este resultado conserva la parte legítimamente evaluable de la representación. **No acredita FSuf para la consulta original completa.**

Deben mantenerse registrados tanto las fibras rechazadas como los argumentos definidos de $f$que la representación parcial no cubre.

**Teorema 2.3. Representación menos discriminante para una familia de consultas.**

Sea $\mathcal{H}$un conjunto de historias y sea $\mathcal{T}$una familia fijada de consultas parciales:

$$f\mathcal{:H \rightharpoonup}B_{f}.$$

Utilizamos los registros de dominio y valor de la entrega anterior y definimos:

$$h \sim_{\mathcal{T}}h^{'}\text{\:\,} \Longleftrightarrow \text{\:\,}\forall f \in \mathcal{T:}\widehat{f}(h) = \widehat{f}\left( h^{'} \right).$$

Dos historias son equivalentes cuando todas las consultas requeridas coinciden tanto en su dominio como en sus valores.

Sea:

$$q_{\mathcal{T}}\mathcal{:H \longrightarrow H/} \sim_{\mathcal{T}}$$

la proyección que asigna a cada historia su clase.

Entonces:

1.  Todas las consultas de $\mathcal{T}$descienden por $q_{\mathcal{T}}$.

2.  Si otra representación **total**:

$$\psi\mathcal{:H \longrightarrow}Z$$

permite el descenso exacto de todas esas consultas, existe una única función:

$$r:\psi\left( \mathcal{H} \right)\mathcal{\longrightarrow H/} \sim_{\mathcal{T}}$$

tal que:

$$\boxed{q_{\mathcal{T}} = r \circ \psi.}$$

**Demostración.**

La igualdad de todos los registros define una relación reflexiva, simétrica y transitiva. Por tanto, $\sim_{\mathcal{T}}$es una equivalencia.

Para cada consulta, su dominio es unión de clases y sus valores son constantes en las clases donde está definida. El Teorema 2.1 proporciona su descenso.

Ahora supongamos que $\psi(h) = \psi\left( h^{'} \right)$. Como todas las consultas factorizaron exactamente por $\psi$, deben coincidir sus registros en ambas historias. Luego:

$$h \sim_{\mathcal{T}}h^{'}.$$

Podemos definir:

$$r\left( \psi(h) \right) = \lbrack h\rbrack_{\mathcal{T}}.$$

La implicación anterior garantiza que esta definición no depende de la historia elegida. Su unicidad se sigue de que cada elemento de $\psi\left( \mathcal{H} \right)$tiene un representante. $\square$

La totalidad de $\psi$es relevante: el teorema compara representaciones de **todas** las historias de $\mathcal{H}$. Si $\psi$fuera parcial, habría que restringir expresamente el ámbito.

"Menos discriminante" significa que conserva exactamente las distinciones exigidas por las consultas. No afirma que sea la representación más sencilla de calcular.

Construirla a partir de respuestas desconocidas puede ser tan difícil como resolver las propias consultas.

Además, si ampliamos la familia:

$$\mathcal{T \subseteq}\mathcal{T}^{'},$$

entonces:

$$h \sim_{\mathcal{T}^{'}}h^{'} \Longrightarrow h \sim_{\mathcal{T}}h^{'}.$$

Las nuevas preguntas pueden exigir distinguir historias que antes podían agruparse.

**Ejemplo 2.1. Una representación suficiente para el presente e insuficiente para la evolución.**

Consideremos un modelo sintético de una parcela con estado:

$$x = \left( b,m \right)\mathbb{\in N \times}\left\{ 0,1 \right\},$$

donde $b$representa biomasa y $m$una condición del suelo.

Para este ejemplo matemático fijamos la evolución:

$$\left( b,m \right) \longmapsto \left( b, + mm \right).$$

La ecuación es una regla ilustrativa, no una ley empírica sobre bosques.

Tomemos la representación:

$$\psi\left( b,m \right) = b.$$

Para la consulta de biomasa presente:

$$f_{actual}\left( b,m \right) = b,$$

existe el factor:

$${\overline{f}}_{actual}(b) = b.$$

Por tanto, $\psi$es suficiente para esa consulta.

Pero la biomasa siguiente es:

$$f_{siguiente}\left( b,m \right) = b + m.$$

Los estados:

$$x_{1} = \left( 10,0 \right),\ x_{2} = \left( 10,1 \right)$$

tienen la misma representación:

$$\psi\left( x_{1} \right) = \psi\left( x_{2} \right) = 10,$$

y respuestas futuras diferentes:

$$f_{siguiente}\left( x_{1} \right) = 10,\ f_{siguiente}\left( x_{2} \right) = 11.$$

La consulta futura no es constante en esa fibra. No puede obtenerse exactamente a partir de $b$solo.

Si necesitamos continuar esta dinámica, el estado debe conservar también $m$, o alguna información equivalente para ese propósito.

**Definición 2.3. Presentación dinámica conjunta.**

Para formular una condición local de suficiencia dinámica, consideramos un sistema discreto:

$$\mathcal{S =}\left( S,A,Y,E,B,T \right),$$

con los siguientes componentes:

  -------------------------------------------------------------------------------------------------------
  **Objeto**                                     **Significado**
  ---------------------------------------------- --------------------------------------------------------
  $$S$$                                          Estados

  $$A$$                                          Entradas que etiquetan las transiciones

  $$Y$$                                          Observaciones

  $$E(s) \subseteq A$$                           Entradas habilitadas en $s$

  $$B\left( s,a \right) \subseteq S \times Y$$   Resultados conjuntos de estado siguiente y observación

  $$T \subseteq S$$                              Estados de terminación declarada
  -------------------------------------------------------------------------------------------------------

Cuando corresponda, una entrada puede incluir tanto la acción como la entrada externa:

$$a = \left( \theta,\xi \right).$$

El tiempo y la memoria pertinente deben mantenerse en los argumentos o incorporarse explícitamente al estado.

Para la clase generativa que consideramos aquí, exigimos:

$$E(s) = \varnothing\text{\:\,} \Longleftrightarrow \text{\:\,}s \in T.$$

Para toda entrada habilitada, $B\left( s,a \right)$está definido y es no vacío.

Estas condiciones delimitan la presentación estudiada. Una fila desconocida o un bloqueo no declarado no se interpretan automáticamente como terminación.

**Definición 2.4. Suficiencia dinámica de un paso.**

Sean mapas totales sobre los conjuntos presentados:

$$\psi:S \rightarrow Q,\ o:Y \rightarrow Z.$$

La representación de estados $\psi$y la representación de observaciones $o$satisfacen la condición conjunta ${DSuf}_{step}$cuando, para cualesquiera $s,t$tales que:

$$\psi(s) = \psi(t),$$

se cumplen:

$${E(s) = E(t),
}{s \in T\text{\:\,} \Longleftrightarrow \text{\:\,}t \in T,}$$

y, para cada entrada habilitada $a$:

$$\boxed{\begin{aligned}
 & \left\{ \left( \psi,\left( s^{'} \right)o(y) \right):\left( s^{'},y \right) \in B\left( s,a \right) \right\} \\
 & \  = \left\{ \left( \psi,\left( t^{'} \right)o(y) \right):\left( t^{'},y \right) \in B\left( t,a \right) \right\}.
\end{aligned}}$$

Se preservan los **pares completos** de estado siguiente representado y observación representada.

Bajo la convención anterior sobre terminación, la igualdad de entradas habilitadas ya implica igualdad de condición terminal. Se mantiene esta última explícita para hacer visible su papel.

El sistema reducido tiene estados en:

$$\overline{S} = {im}\psi,$$

y observaciones en ${im}o$.

Sus transiciones se definen mediante:

$$\overline{B}\left( \psi,(s)a \right) = \left\{ \left( \psi,\left( s^{'} \right)o(y) \right):\left( s^{'},y \right) \in B\left( s,a \right) \right\}.$$

La condición de suficiencia garantiza que esta definición no depende del representante $s$elegido.

**Teorema 2.4. Conservación exacta de continuaciones finitas.**

Sea $L_{n}(s)$el conjunto de trazas generadas desde $s$al avanzar $n$pasos, deteniéndose antes solamente si se alcanza una terminación declarada.

Cada paso registra:

$$\left( a,s^{'},y \right),$$

y su traducción registra:

$$\left( a,\psi,\left( s^{'} \right)o(y) \right).$$

Si se cumple ${DSuf}_{step}$, entonces, para todo $n\mathbb{\in N}$y todo $s \in S$:

$$\boxed{{map}_{\psi,o}L_{n}(s) = {\overline{L}}_{n}\left( \psi(s) \right).}$$

La igualdad afirma exactitud de las trazas **después de las traducciones declaradas**.

**Demostración por inducción sobre** $n$**.**

Para $n = 0$, ambos sistemas producen únicamente la traza vacía. La igualdad se cumple.

Supongamos que el resultado vale para horizonte $n$desde cualquier estado.

Consideremos el horizonte $n + 1$.

Si $s$es terminal, su estado representado también lo es. Ambos sistemas terminan sin añadir transiciones.

Si $s$no es terminal, una traza original comienza con alguna entrada habilitada $a$y algún resultado:

$$\left( s^{'},y \right) \in B\left( s,a \right).$$

La igualdad conjunta de un paso garantiza:

$$\left( \psi,\left( s^{'} \right)o(y) \right) \in \overline{B}\left( \psi,(s)a \right).$$

Por la hipótesis inductiva, el sufijo desde $s^{'}$se traduce exactamente a un sufijo del sistema reducido. Esto demuestra una inclusión.

Para la inclusión inversa, tomemos una traza reducida. Su primer paso pertenece a:

$$\overline{B}\left( \psi,(s)a \right).$$

Por la igualdad de filas, existe un resultado original $\left( s^{'},y \right)$que realiza ese paso **desde el representante actual** $s$.

La hipótesis inductiva, aplicada a ese $s^{'}$, permite levantar el sufijo restante.

Cada paso continúa desde el estado donde terminó el anterior. No se cambia arbitrariamente de representante entre transiciones.

Ambas inclusiones prueban la igualdad para $n + 1$. $\square$

Esta demostración vale para todo horizonte finito. La enumeración de algunos horizontes sirve para comprobar una implementación, pero la justificación general es la inducción.

**Contraejemplo 2.2. Las marginales no conservan la dinámica conjunta.**

Consideremos dos relaciones de resultados:

$${B_{1} = \left\{ \left( 0,0 \right),\left( 1,1 \right) \right\},
}{B_{2} = \left\{ \left( 0,1 \right),\left( 1,0 \right) \right\}.}$$

En ambas:

$${{proj}_{estado}\left( B_{i} \right) = \left\{ 0,1 \right\},
}{{proj}_{observaci\overset{ˊ}{o}n}\left( B_{i} \right) = \left\{ 0,1 \right\}.}$$

Las posibilidades marginales coinciden.

Sin embargo, en $B_{1}$la observación coincide con el estado y en $B_{2}$es opuesta.

Si una regla posterior elige una acción igual a la observación:

$$\theta = y,$$

esa acción coincide con el estado en todos los resultados de $B_{1}$y en ninguno de $B_{2}$.

Conservar por separado los estados posibles y las observaciones posibles habría perdido la dependencia que determina el comportamiento de la regla.

Por eso la condición dinámica se formula sobre pares conjuntos.

**Convención 2.2. Condiciones adicionales para conservar políticas.**

El Teorema 2.4 estudia las continuaciones del sistema generativo presentado. Para transportar un proceso controlado también debe comprobarse cómo se representa la información del decisor.

Sean:

$$R_{t}:I_{t}^{A} \rightarrow I_{t}^{B}$$

los mapas de información entre dos presentaciones, y:

$$O_{t + 1}:Y_{t + 1}^{A} \rightarrow Y_{t + 1}^{B}$$

los mapas de sus observaciones.

Si la información se actualiza mediante funciones $U_{t}^{A},U_{t}^{B}$, se exige, en los argumentos pertinentes, con dominios compatibles:

$$\boxed{R_{t + 1}\text{ }\left( U_{t}^{A}\left( i,\theta,y \right) \right) = U_{t}^{B}\text{ }\left( R_{t},(i),\theta O_{t + 1}(y) \right).}$$

Actualizar y después representar debe producir el mismo resultado que representar y después actualizar.

Para políticas correspondientes se exige:

$$\pi_{t}^{B}\left( R_{t}(i) \right) = \pi_{t}^{A}(i),$$

junto con inicializaciones compatibles, preservación de los dominios pertinentes de acción y pertenencia efectiva a las familias de políticas admitidas.

Cuando se comparan familias completas, debe declararse la dirección de transporte y demostrarse la cobertura requerida. Una fórmula que define una política candidata no demuestra que esa política sea admitida.

Estas obligaciones se desarrollarán al construir los futuros y las políticas en el módulo V.

**Alcance del contrato del Módulo 0.**

La suficiencia funcional conserva consultas, incluyendo dominios y valores. La suficiencia dinámica demostrada conserva las continuaciones finitas generadas por la relación conjunta.

Las propiedades adicionales requieren sus propias condiciones:

  -------------------------------------------------------------------------------------------------------------------
  **Propiedad que se quiere conservar**             **Obligación pertinente**
  ------------------------------------------------- -----------------------------------------------------------------
  Una consulta parcial                              Cobertura, saturación y constancia

  Continuaciones finitas                            Entradas, terminación y resultados conjuntos

  Políticas implementables                          Información, actualización, inicialización y familias admitidas

  Probabilidades                                    Leyes y transporte de medidas

  Trayectorias infinitas con aceptación adicional   Conservación del lenguaje de aceptación
  -------------------------------------------------------------------------------------------------------------------

Dos modelos pueden tener los mismos futuros posibles y asignarles probabilidades diferentes. También pueden compartir sus transiciones locales y adoptar restricciones distintas sobre qué trayectorias infinitas admiten.

Cuando una aplicación reúna varias suficiencias, la expresión **GSuf** indicará esa combinación, especificando cuáles se exigen. Una abstracción posterior tampoco recupera por sí sola memoria causal que ya haya sido eliminada.

El Módulo 0 proporciona así un criterio verificable para cada reducción: qué conserva, sobre qué dominio y mediante qué demostración. En la siguiente entrega desarrollaremos el **Módulo I: funciones, perfiles funcionales, calibración y comparación**, utilizando estas condiciones para construir evaluaciones bien definidas.

**Entrega 3 --- Módulo I: funciones, perfiles funcionales y comparación**

El Módulo I describe qué funciones presenta un sistema, cómo se evalúan y bajo qué condiciones sus resultados pueden compararse.

Una evaluación funcional conserva el significado de cada componente: qué función se está examinando, en qué estado y entorno, cómo se expresa su resultado y qué relación de orden corresponde utilizar.

El resultado principal será un **perfil funcional**, acompañado de un dominio preciso y de las condiciones que permiten compararlo con otros perfiles.

**Definición 3.1. Ámbito de evaluación funcional.**

Fijamos un marco, un modelo, un contexto y un entorno de evaluación $\mathcal{A}$.

Sean:

$$X$$

el conjunto de estados considerados,

$$T$$

el conjunto de tiempos, e:

$$I$$

el conjunto de índices funcionales.

Cada $i \in I$identifica una función con significado declarado. Una aplicación podría distinguir, por ejemplo, retención de agua, regulación térmica o provisión de hábitat.

La elección de $I$determina el alcance del perfil. Evaluar todas sus componentes significa evaluar todas las funciones **de esa familia declarada**; no demuestra que se hayan identificado todas las funciones posibles del sistema.

Un punto de evaluación es:

$$p = \left( x,t \right) \in X \times T.$$

La descripción estructural procede del módulo 0:

$$\Sigma:X \rightharpoonup S.$$

**Definición 3.2. Componente funcional.**

Para cada índice $i$, declaramos:

$$F_{i}:S \times X \times \left\{ \mathcal{A} \right\} \rightharpoonup Y_{i},$$

donde $F_{i}$obtiene un resultado funcional a partir de la estructura, el estado y el entorno.

Cuando sus argumentos están en dominio:

$$y_{i}(x) = F_{i}\left( \Sigma,(x),x\mathcal{A} \right).$$

El estado $x$permanece como argumento independiente de $\Sigma(x)$. Dos sistemas con la misma descripción estructural pueden encontrarse en condiciones diferentes de desgaste, disponibilidad o funcionamiento.

La igualdad de estructuras no obliga, por sí sola, a la igualdad de resultados funcionales.

Para expresar el resultado en un espacio comparable declaramos:

$$u_{i}:Y_{i} \times X \times T \rightharpoonup \mathcal{O}_{i}.$$

La componente evaluada es:

$$\boxed{o_{i}\left( x,t \right) = u_{i}\text{ }\left( F_{i},\left( \Sigma,(x),x\mathcal{A} \right),xt \right).}$$

El conjunto $\mathcal{O}_{i}$está equipado con un preorden:

$$\left( \mathcal{O}_{i}, \preceq_{i} \right).$$

La relación:

$$a \preceq_{i}b$$

indica que $b$alcanza al menos el nivel de $a$según la propiedad funcional $i$.

Los elementos de $\mathcal{O}_{i}$pueden ser números, categorías ordenadas u otros objetos. El módulo no requiere que todas las componentes sean escalares ni que utilicen las mismas unidades.

**Definición 3.3. Dominio de una componente.**

La expresión anterior se evalúa siguiendo sus dependencias.

Primero debe cumplirse:

$$x \in D_{\Sigma}.$$

Después:

$$\left( \Sigma,(x),x\mathcal{A} \right) \in D_{F_{i}}.$$

Finalmente:

$$\left( F_{i},\left( \Sigma,(x),x\mathcal{A} \right),xt \right) \in D_{u_{i}}.$$

Definimos:

$$D_{i}^{F} = \left\{ \left( x,t \right), \in X \times T:x \in D_{\Sigma}\text{~}\left( \Sigma,(x),x\mathcal{A} \right) \in D_{F_{i}} \right\},$$

y:

$$D_{i} = \left\{ \left( x,t \right) \in D_{i}^{F}:\left( y_{i},(x),xt \right) \in D_{u_{i}} \right\}.$$

La componente es entonces una función parcial:

$$o_{i}:X \times T \rightharpoonup \mathcal{O}_{i}$$

con dominio $D_{i}$.

Estas condiciones mantienen separados tres posibles problemas: falta de descripción estructural, falta de evaluación funcional y falta de una expresión ordinal válida.

Un valor cero es legítimo si pertenece al espacio de resultados y fue obtenido dentro del dominio. La ausencia de una evaluación conserva su diagnóstico propio.

**Definición 3.4. Perfil funcional completo.**

El perfil de un punto $p = \left( x,t \right)$es:

$$\boxed{O(p) = \left( o_{i}(p) \right)_{i \in I}.}$$

Su espacio de valores es:

$$\prod_{i \in I}^{}\mathcal{O}_{i},$$

y su dominio:

$$\boxed{D_{O} = \bigcap_{i \in I}^{}D_{i}.}$$

Por tanto:

$$O:X \times T \rightharpoonup \prod_{i \in I}^{}\mathcal{O}_{i}.$$

**Justificación.** Un perfil completo contiene un valor para cada componente requerida. Existe exactamente cuando todas esas componentes están definidas, como se demostró para los registros conjuntos en la entrega 1. $\square$

Una componente faltante no se elimina del índice para presentar el perfil como completo. Si se decide estudiar una subfamilia $J \subseteq I$, se está definiendo otro perfil, cuyo alcance debe identificarse.

Si $I = \varnothing$, el producto contiene un único valor, la tupla vacía:

$$\prod_{i \in \varnothing}^{}\mathcal{O}_{i} = \left\{ () \right\}.$$

El perfil vacío está definido en todo $X \times T$, sin necesitar la evaluación de una componente. Este caso registra que no se exigió ninguna función; no acredita propiedades físicas o funcionales tácitas.

**Definición 3.5. Bloque de comparación con calibración común.**

Que dos perfiles existan no basta para justificar su comparación semántica.

Sea:

$$\mathcal{B \subseteq}D_{O}$$

un conjunto de puntos que queremos comparar utilizando el mismo índice funcional y los mismos órdenes de componentes.

Para cada $i$, declaramos un espacio de referencia:

$$\left( \mathcal{R}_{i}, \leq_{i}^{R} \right),$$

una referencia semántica parcial:

$$r_{i}:X \times T \rightharpoonup \mathcal{R}_{i},$$

definida en todo $\mathcal{B}$, y un mapa ordinal:

$$h_{i}:\mathcal{R}_{i} \rightharpoonup \mathcal{O}_{i},$$

definido en todos los valores alcanzados:

$$r_{i}\left\lbrack \mathcal{B} \right\rbrack \subseteq D_{h_{i}}.$$

Exigimos dos propiedades.

La primera es una factorización común:

$$\boxed{o_{i}(p) = h_{i}\left( r_{i}(p) \right)\ \left( p\mathcal{\in B} \right).}$$

La segunda es preservación y reflexión del orden:

$$\boxed{a \leq_{i}^{R}b\text{\:\,} \Longleftrightarrow \text{\:\,}h_{i}(a) \preceq_{i}h_{i}(b)\ \left( a,b \in r_{i}\left\lbrack \mathcal{B} \right\rbrack \right).}$$

El mapa $h_{i}$es **el mismo para todos los puntos del bloque**.

Estas condiciones acreditan que las distintas evaluaciones expresan una misma referencia ordinal, dentro del alcance de los valores examinados.

La referencia debe tener un significado declarado independientemente de la comparación que se desea obtener. La comprobación algebraica de estas condiciones no demuestra, por sí sola, que una referencia empírica sea correcta.

**Contraejemplo 3.1. Compartir rango no acredita calibración común.**

Consideremos dos valores de una misma magnitud de referencia:

$$r(p) = 8,\ r(q) = 9.$$

Supongamos que se utilizan las normalizaciones:

$$u_{p}(y) = \frac{y}{10},\ y \in \left\lbrack 0,10 \right\rbrack,$$

y:

$$u_{q}(y) = \frac{y}{100},\ y \in \left\lbrack 0,100 \right\rbrack.$$

Ambas son crecientes y tienen rango $\left\lbrack 0,1 \right\rbrack$. Sin embargo:

$$u_{p}(8) = 0.8,\ u_{q}(9) = 0.09.$$

Así:

$$8 < 9,\ 0.8 > 0.09.$$

Las salidas invierten la comparación de las cantidades originales.

Pueden tener una interpretación coherente como fracciones de máximos propios diferentes. Pero esa pregunta es distinta de comparar directamente las cantidades absolutas $8$y $9$.

La aplicación debe declarar qué significado pretende conservar.

Una normalización dependiente del estado o del tiempo puede admitirse cuando satisface la referencia común y la factorización exigidas. Su dependencia contextual no la invalida automáticamente.

**Definición 3.6. Dominancia funcional dentro de un bloque.**

Sobre un bloque $\mathcal{B}$con perfiles completos y calibración común, definimos:

$$\boxed{p \succeq_{DFR}q\text{\:\,} \Longleftrightarrow \text{\:\,}\forall i \in I:o_{i}(q) \preceq_{i}o_{i}(p).}$$

La relación significa que $p$alcanza al menos el nivel de $q$en cada componente declarada.

La equivalencia funcional es:

$$p \sim_{DFR}q\text{\:\,} \Longleftrightarrow \text{\:\,}p \succeq_{DFR}q \land q \succeq_{DFR}p.$$

La dominancia estricta es:

$$p \succ_{DFR}q\text{\:\,} \Longleftrightarrow \text{\:\,}p \succeq_{DFR}q \land \neg\left( q \succeq_{DFR}p \right).$$

Para una familia finita de componentes, esto equivale a no empeorar en ninguna y mejorar estrictamente en alguna.

No exige mejorar estrictamente en todas.

Dos puntos del bloque son incomparables cuando:

$$\neg\left( p \succeq_{DFR}q \right) \land \neg\left( q \succeq_{DFR}p \right).$$

Esta última situación supone que la comparación está admitida. Una falta de perfil o de calibración común es un problema de dominio, no una prueba de incomparabilidad.

**Teorema 3.1. La dominancia funcional es un preorden.**

La relación $\succeq_{DFR}$es reflexiva y transitiva sobre $\mathcal{B}$.

**Demostración.**

Para cualquier $p\mathcal{\in B}$, la reflexividad de cada componente proporciona:

$$o_{i}(p) \preceq_{i}o_{i}(p).$$

Por tanto:

$$p \succeq_{DFR}p.$$

Supongamos ahora:

$$p \succeq_{DFR}q,\ q \succeq_{DFR}r.$$

Para cada $i$:

$$o_{i}(r) \preceq_{i}o_{i}(q) \preceq_{i}o_{i}(p).$$

La transitividad del orden componente implica:

$$o_{i}(r) \preceq_{i}o_{i}(p).$$

Como esto vale para todas las componentes:

$$p \succeq_{DFR}r.$$

Quedan demostradas ambas propiedades. $\square$

La prueba exige mantener las mismas componentes y sus órdenes en todas las comparaciones involucradas.

**Proposición 3.2. La calibración común conserva la comparación semántica.**

Bajo las condiciones de la Definición 3.5:

$$\boxed{p \succeq_{DFR}q\text{\:\,} \Longleftrightarrow \text{\:\,}\forall i \in I:r_{i}(q) \leq_{i}^{R}r_{i}(p).}$$

**Demostración.**

Por la factorización común:

$$o_{i}(q) = h_{i}\left( r_{i}(q) \right),\ o_{i}(p) = h_{i}\left( r_{i}(p) \right).$$

La preservación y reflexión del orden proporcionan:

$$o_{i}(q) \preceq_{i}o_{i}(p)\text{\:\,} \Longleftrightarrow \text{\:\,}r_{i}(q) \leq_{i}^{R}r_{i}(p).$$

Tomando la conjunción sobre todas las componentes obtenemos el resultado. $\square$

La comparación de perfiles queda así vinculada a las referencias que fundamentan su significado.

**Teorema 3.3. Equivalencia, dominancia estricta y orden entre clases.**

La dominancia mutua $\sim_{DFR}$es una relación de equivalencia. Su cociente:

$$\mathcal{B/} \sim_{DFR}$$

admite un orden parcial definido por:

$$\lbrack p\rbrack \succeq \lbrack q\rbrack\text{\:\,} \Longleftrightarrow \text{\:\,}p \succeq_{DFR}q.$$

Además, $\succ_{DFR}$es irreflexiva y transitiva.

**Demostración.**

La equivalencia es reflexiva por la reflexividad del preorden y simétrica por su definición.

Si $p \sim q$y $q \sim r$, la transitividad de las dominancias en ambos sentidos da $p \sim r$.

Para comprobar que el orden de clases no depende de los representantes, supongamos:

$$p \sim p^{'},\ q \sim q^{'},\ p \succeq q.$$

Entonces:

$$p^{'} \succeq p \succeq q \succeq q^{'},$$

por lo que $p^{'} \succeq q^{'}$. El argumento inverso es análogo.

La reflexividad y la transitividad pasan al cociente. Si:

$$\lbrack p\rbrack \succeq \lbrack q\rbrack\ \text{y}\ \lbrack q\rbrack \succeq \lbrack p\rbrack,$$

entonces $p \sim q$, de modo que $\lbrack p\rbrack = \lbrack q\rbrack$. Así se obtiene antisimetría.

La estricta es irreflexiva porque no puede cumplirse simultáneamente:

$$p \succeq p\ \text{y}\ \neg(p \succeq p).$$

Si $p \succ q$y $q \succ r$, tenemos $p \succeq r$. Si también $r \succeq p$, se seguiría:

$$r \succeq p \succeq q,$$

contradiciendo $q \succ r$. Por tanto, $p \succ r$. $\square$

La equivalencia funcional identifica resultados comparativos bajo las funciones seleccionadas. No identifica físicamente los estados ni acredita igualdad de sus futuros.

**Teorema 3.4. Cambio exacto de espacios de valores.**

Para cada componente, sea:

$$k_{i}:\mathcal{O}_{i} \rightharpoonup \mathcal{O}_{i}^{'}$$

un mapa hacia otro preorden $\left( \mathcal{O}_{i}^{'}, \preceq_{i}^{'} \right)$.

Supongamos que:

$$o_{i}\left\lbrack \mathcal{B} \right\rbrack \subseteq D_{k_{i}},$$

y que, para todos los valores $a,b$alcanzados en el bloque:

$$a \preceq_{i}b\text{\:\,} \Longleftrightarrow \text{\:\,}k_{i}(a) \preceq_{i}^{'}k_{i}(b).$$

Definimos los perfiles transformados mediante:

$$o_{i}^{'}(p) = k_{i}\left( o_{i}(p) \right),\ p\mathcal{\in B.}$$

Entonces se conservan exactamente, dentro de $\mathcal{B}$:

-   La dominancia.

-   La equivalencia.

-   La dominancia estricta.

-   La incomparabilidad.

**Demostración.**

La cobertura de $D_{k_{i}}$garantiza que todas las componentes transformadas existen en el bloque.

Para cada pareja $p,q\mathcal{\in B}$:

$$o_{i}(q) \preceq_{i}o_{i}(p)\text{\:\,} \Longleftrightarrow \text{\:\,}o_{i}^{'}(q) \preceq_{i}^{'}o_{i}^{'}(p).$$

La conjunción sobre $i$conserva la dominancia. Aplicando la misma equivalencia en sentido inverso, se conservan también las combinaciones que definen equivalencia, estricta e incomparabilidad. $\square$

Si se desea transformar toda la función parcial $o_{i}$, conservando su dominio original $D_{i}$, se requiere cobertura de toda su imagen:

$$o_{i}\left\lbrack D_{i} \right\rbrack \subseteq D_{k_{i}}.$$

Una prueba limitada al bloque $\mathcal{B}$no acredita esa propiedad fuera de él.

Tampoco se exige inyectividad literal cuando los espacios son preórdenes: dos etiquetas distintas que ya sean equivalentes pueden compartir imagen. Lo que debe conservarse es su estructura de orden.

**Contraejemplo 3.2. La monotonía sola puede borrar distinciones.**

Tomemos:

$$\mathcal{O =}\left\{ 1,2 \right\},\ 1 < 2,$$

y la transformación:

$$k(1) = k(2) = 0.$$

La función es monótona: una comparación válida en el origen sigue siendo válida en el destino.

Sin embargo, la distinción estricta entre $1$y $2$desaparece.

Además:

$$k(2) \leq k(1)$$

es verdadero, mientras que:

$$2 \leq 1$$

es falso.

La transformación preserva el orden, pero no lo refleja. Por ello no satisface el contrato de transporte exacto.

**Contraejemplo 3.3. Elegir componentes diferentes para cada pareja puede destruir la transitividad.**

Consideremos tres perfiles completos:

$$a = \left( 2,0,1 \right),\ b = \left( 1,2,0 \right),\ c = \left( 0,1,2 \right).$$

Ahora introduzcamos una regla defectuosa que escoge qué componente mirar según la pareja:

  ------------------------------------------------------------------------------------
  **Pareja**                 **Única componente utilizada**
  -------------------------- ---------------------------------------------------------
  $$\left\{ a,b \right\}$$   Primera

  $$\left\{ b,c \right\}$$   Segunda

  $$\left\{ c,a \right\}$$   Tercera
  ------------------------------------------------------------------------------------

La misma componente se utiliza para ambos sentidos de cada pareja, y cada elemento se compara consigo mismo reflexivamente.

Esta regla produce:

$$a \succ b,\ b \succ c,\ c \succ a.$$

En particular:

$$a \succeq b,\ b \succeq c,$$

pero:

$$a \succeq \not{}c.$$

La transitividad falla.

Los datos estaban completos. El problema fue cambiar de criterio entre comparaciones.

Por eso el módulo exige un índice funcional común dentro del bloque. Una subfamilia puede estudiarse legítimamente si se declara de antemano y se mantiene durante toda la comparación pertinente.

**Ejemplo 3.1. Perfiles completos, incomparabilidad y falta de dominio.**

Consideremos una instancia sintética con dos funciones:

$$I = \left\{ \text{retenci}\overset{ˊ}{\text{o}}\text{n~de~agua},\text{provisi}\overset{ˊ}{\text{o}}\text{n~de~h}\overset{ˊ}{\text{a}}\text{bitat} \right\}.$$

Para cada una declaramos niveles:

$$0 \preceq 1 \preceq 2.$$

Suponemos que los niveles tienen referencias semánticas y calibraciones comunes. Los registros disponibles son:

  -------------------------------------------------------------------------
  **Punto**   **Retención de agua**         **Provisión de hábitat**
  ----------- ----------------------------- -------------------------------
  $$p$$       $$2$$                         $$1$$

  $$q$$       $$1$$                         $$2$$

  $$r$$       $$2$$                         $$2$$

  $$s$$       $$2$$                         Sin evaluación
  -------------------------------------------------------------------------

Los primeros tres perfiles son:

$$O(p) = \left( 2,1 \right),\ O(q) = \left( 1,2 \right),\ O(r) = \left( 2,2 \right).$$

Dentro del bloque:

$$\mathcal{B =}\left\{ p,q,r \right\},$$

obtenemos:

$$r \succ_{DFR}p,\ r \succ_{DFR}q.$$

En cambio, $p$y $q$son incomparables: cada uno supera al otro en una componente.

El punto $s$no tiene perfil completo para esta familia. No se concluye que sea inferior, superior o incomparable con los demás.

Tampoco podría afirmarse que la comparación ha cubierto los cuatro puntos. El resultado corresponde al bloque explícitamente admitido.

En este ejemplo, $r$fue supuesto como un punto existente de la presentación. La existencia de $p$y $q$**no demostraría por sí sola** que exista un estado realizable con perfil $\left( 2,2 \right)$.

Formalmente:

$${im}O \subseteq \prod_{i \in I}^{}\mathcal{O}_{i},$$

y esa inclusión puede ser estricta. El producto permite escribir combinaciones de valores cuya realización conjunta aún debe justificarse.

El Módulo I deja definidas las condiciones para obtener perfiles completos, admitir bloques comparativos y conservar sus órdenes bajo cambios de representación.

La dominancia obtenida tiene el alcance de las funciones y referencias declaradas. Relacionarla con bienestar, capacidad generativa o vida sostenida requiere los puentes correspondientes de los demás módulos.

La siguiente entrega desarrollará el **Módulo II: sistemas, subsistemas, interfaces y composición multiescalar**, donde estableceremos cuándo los resultados de componentes diferentes pertenecen a una realización conjunta y cómo conservar sus dependencias y recursos compartidos.

**Entrega 4 --- Módulo II: sistemas, subsistemas, interfaces y composición multiescalar**

El Módulo II establece cómo integrar descripciones de distintas partes o escalas de un sistema conservando sus dependencias.

El Módulo I permitió construir perfiles funcionales. Ahora debemos determinar cuándo los valores atribuidos a distintas unidades pueden pertenecer a una misma configuración, ejecución o alternativa.

La cuestión central es que **la posibilidad de cada componente por separado no demuestra la posibilidad de su realización conjunta**.

Los contraejemplos de esta entrega mostrarán usos incorrectos que las condiciones del módulo permiten detectar. **No describen problemas matemáticos pendientes.**

**Definición 4.1. Unidad representada en una escala.**

Una unidad $j$, considerada en una escala $k$, se presenta mediante:

$$Q_{j}^{(k)} = \left( \mathcal{E}_{j}^{(k)},\mathcal{X}_{j}^{(k)},x_{j}^{(k)},\Sigma_{j}^{(k)} \right),$$

donde:

  --------------------------------------------------------------------------------
  **Componente**              **Significado**
  --------------------------- ----------------------------------------------------
  $$\mathcal{E}_{j}^{(k)}$$   Entidad o ámbito representado

  $$\mathcal{X}_{j}^{(k)}$$   Espacio de estados de esa presentación

  $$x_{j}^{(k)}$$             Estado considerado

  $$\Sigma_{j}^{(k)}$$        Descripción estructural u organizacional
  --------------------------------------------------------------------------------

El índice de escala identifica el nivel de descripción. No determina automáticamente una cantidad de entidades, un grado de complejidad o un valor funcional.

La condición de **subsistema** se establece mediante las relaciones estructurales declaradas por el modelo: qué entidad forma parte de otra, cómo se corresponden sus estados y cuáles son sus interfaces.

Cuando esas estructuras sean conjuntos, pueden utilizarse inclusiones. Cuando sean redes u otras estructuras, deberán emplearse las correspondencias pertinentes.

No se presupone que toda organización $\Sigma$sea un conjunto cuyos elementos puedan intersectarse. Tampoco se deduce independencia de que dos unidades reciban nombres diferentes.

**Definición 4.2. Puertos e interfaces tipadas.**

Un puerto identifica una variable que una unidad presenta o comparte con otras.

Para cada identidad de puerto $s$, declaramos un conjunto de valores:

$$V_{s}.$$

Su descripción incluye el significado de la variable y, cuando corresponde:

-   La entidad y el instante a los que pertenece.

-   Su papel como estado, observación, intercambio o recurso.

-   Su unidad de medida.

-   La identidad del recurso compartido.

Dos apariciones de un mismo puerto representan la misma variable y deben coincidir en valor.

Dos variables distintas pueden tener valores iguales sin convertirse por ello en un mismo puerto.

Por ejemplo, dos demandas de agua de seis unidades siguen siendo demandas diferentes. En cambio, una misma demanda registrada desde dos escalas debe conservar una identidad común para evitar contarla dos veces.

Una interfaz entre unidades contiene los puertos que ambas comparten. Si las presentaciones utilizan identificadores o unidades diferentes, la correspondencia debe declararse y validarse antes de componerlas.

**Definición 4.3. Relación conjunta.**

Sea $S$un conjunto de identidades de puertos. Una asignación completa de valores es un elemento:

$$z \in \prod_{s \in S}^{}V_{s}.$$

Sea $W$un conjunto de identificadores comunes, con el ámbito experimental pertinente.

Una relación conjunta es:

$$\boxed{R \subseteq W \times \prod_{s \in S}^{}V_{s}.}$$

Cada fila:

$$\left( w,z \right) \in R$$

registra una combinación admitida por esa relación.

Debemos distinguir dos usos.

**Registros de ejecuciones completas.** Si $w$identifica una ejecución completa y todos sus valores están determinados, existe como máximo una asignación $z$por identificador.

**Relaciones de completaciones.** Si se representan posibilidades compatibles con una base o un registro parcial, pueden existir varias filas para el mismo $w$. Son completaciones alternativas; no se afirma que todas ocurran simultáneamente.

En este segundo uso, coincidir en $w$no basta para demostrar una realización conjunta. También deben conservarse las restricciones entre sus valores.

En ambos casos, el significado y alcance de $w$deben estar declarados. Compartir una etiqueta no acredita por sí solo compatibilidad física.

**Definición 4.4. Proyección de una relación.**

Para un conjunto de puertos $U \subseteq S$, definimos:

$$\boxed{\pi_{U}R = \left\{ \left( w,z \mid_{U} \right):\left( w,z \right) \in R \right\}.}$$

La expresión $z \mid_{U}$es la restricción de la asignación a los puertos de $U$.

La proyección conserva el identificador $w$.

Esta operación produce una vista parcial de una relación conjunta. Puede perder restricciones que involucren simultáneamente columnas que ya no aparecen juntas.

**Definición 4.5. Composición mediante interfaces comunes.**

Consideremos una familia no vacía de relaciones locales:

$$L_{1},\ldots,L_{m},$$

con esquemas de puertos:

$$S_{1},\ldots,S_{m}.$$

Suponemos que los puertos compartidos tienen tipos y significados compatibles. Sea:

$$S = \bigcup_{j = 1}^{m}S_{j}.$$

Definimos su **unión natural**, denotada por $\bowtie$:

$$\boxed{\bowtie_{j = 1}^{m}L_{j} = \left\{ \left( w,z \right),:\forall j\text{~}\left( w,z \mid_{S_{j}} \right) \in L_{j} \right\}.}$$

Aquí $z$asigna valores a todos los puertos de $S$.

La operación exige coincidencia del identificador común y de todos los puertos compartidos. Su símbolo $\bowtie$no representa una unión ordinaria de conjuntos.

El resultado contiene las combinaciones compatibles con las relaciones locales suministradas. Para afirmar que reproduce una relación global determinada, hace falta comprobar esa igualdad.

**Proposición 4.1. Leyes de proyección y cobertura.**

Si:

$$U \subseteq V \subseteq S,$$

entonces:

$$\pi_{U}\left( \pi_{V}R \right) = \pi_{U}R.$$

Además, si los esquemas locales cubren todos los puertos:

$$S = \bigcup_{j}^{}S_{j},$$

se cumple:

$$\boxed{R \subseteq \bowtie_{j}\pi_{S_{j}}R.}$$

**Demostración.**

Restringir primero una asignación a $V$y después a $U$produce su restricción directa a $U$. Ambas operaciones conservan $w$.

Para la segunda afirmación, toda fila de $R$tiene cada una de sus restricciones en la proyección correspondiente. Por definición, satisface todas las condiciones de la unión natural. $\square$

La inclusión asegura que las proyecciones no excluyen las filas originales al recomponerse. Pero la recomposición puede introducir combinaciones adicionales.

Si no existe cobertura completa, la comparación debe hacerse sobre los puertos efectivamente cubiertos, sin inventar valores para los restantes.

**Teorema 4.2. Criterio exacto de recomposición por interfaz.**

Consideremos dos vistas de una relación global.

Escribimos una fila como:

$$\left( \eta,a,b \right),$$

donde:

-   $\eta$reúne el identificador común y todos los valores de la interfaz compartida.

-   $a$contiene las columnas exclusivas de la primera vista.

-   $b$contiene las columnas exclusivas de la segunda.

Entonces:

$$\boxed{R = \pi_{\eta,a}R \bowtie \pi_{\eta,b}R}$$

si y solo si se cumple:

$$\boxed{R\left( \eta,a,b^{'} \right) \land R\left( \eta,a^{'},b \right) \Longrightarrow R\left( \eta,a,b \right)}$$

para todos los argumentos pertinentes.

La condición afirma que, dentro de una misma fibra de interfaz, las partes que se recombinan no están sometidas a una restricción adicional que impida esa combinación.

**Demostración de necesidad.**

Supongamos que la recomposición es exactamente $R$.

Las dos premisas proporcionan:

$$\left( \eta,a \right) \in \pi_{\eta,a}R$$

y:

$$\left( \eta,b \right) \in \pi_{\eta,b}R.$$

Su combinación pertenece a la unión natural y, por la igualdad supuesta, pertenece a $R$.

**Demostración de suficiencia.**

Tomemos una fila $\left( \eta,a,b \right)$de la unión natural.

Por pertenecer a ambas proyecciones, existen $b^{'}$y $a^{'}$tales que:

$$R\left( \eta,a,b^{'} \right),\ R\left( \eta,a^{'},b \right).$$

La condición del teorema implica:

$$R\left( \eta,a,b \right).$$

Así, la recomposición está incluida en $R$. La inclusión contraria procede de la Proposición 4.1. $\square$

Esta propiedad se denomina **rectangularidad por fibra de interfaz**. Es una condición sobre conjuntos de posibilidades; no presupone independencia probabilística.

Cuando cada identificador completo determina una única fila global, conservarlo en todas las proyecciones hace exacta la recomposición por una cubierta. El criterio anterior también contempla relaciones con varias completaciones por identificador.

**Proposición 4.3. Auditoría de una descomposición declarada.**

Sean $R$una relación global y $L_{j}$las relaciones locales propuestas.

La afirmación:

"Estas relaciones locales son las proyecciones de $R$y permiten reconstruirla exactamente"

exige tres comprobaciones:

  ---------------------------------------------------------------------------------------------------
  **Comprobación**     **Condición**
  -------------------- ------------------------------------------------------------------------------
  Cobertura y tipado   Todos los puertos globales están cubiertos y los tipos compartidos coinciden

  Exactitud local      $L_{j} = \pi_{S_{j}}R$para cada $j$

  Exactitud conjunta   $$\bowtie_{j}L_{j} = R$$
  ---------------------------------------------------------------------------------------------------

**Justificación.** Las dos primeras condiciones identifican las vistas que realmente corresponden al global. La tercera comprueba que su composición no pierde filas ni introduce otras. Juntas expresan exactamente la afirmación que se pretende certificar. $\square$

En una presentación finita, estas condiciones se comprueban mediante proyecciones, composición y diferencias de conjuntos.

Una declaración verbal de compatibilidad no sustituye esas comprobaciones.

**Teorema 4.4. Existencia de una relación global compatible con las vistas locales.**

Supongamos ahora que se suministran las relaciones locales, pero todavía no una relación global.

Definamos:

$$J = \bowtie_{j}L_{j}.$$

Existe alguna relación $G$cuyas proyecciones sean exactamente las relaciones locales:

$$\pi_{S_{j}}G = L_{j}\ \text{para~todo~}j,$$

si y solo si:

$$\boxed{\pi_{S_{j}}J = L_{j}\ \text{para~todo~}j.}$$

**Demostración.**

Si existe $G$, toda fila de $G$satisface las restricciones locales. Por tanto:

$$G \subseteq J.$$

Al proyectar:

$$L_{j} = \pi_{S_{j}}G \subseteq \pi_{S_{j}}J.$$

Pero la definición de $J$garantiza:

$$\pi_{S_{j}}J \subseteq L_{j}.$$

Se obtiene la igualdad.

Recíprocamente, si todas esas igualdades se cumplen, basta tomar:

$$G = J.$$

Sus proyecciones son las requeridas. $\square$

El teorema acredita existencia matemática de una relación global con esas vistas. No demuestra su adecuación física ni su igualdad con otro global declarado independientemente.

La existencia de una realización requiere además:

$$J \neq \varnothing.$$

**Contraejemplo de uso incorrecto 4.1. Confundir compatibilidad local con realización global.**

Consideremos tres variables binarias $a,b,c$, bajo una misma base de comparación, y las relaciones:

$${L_{ab} = \left\{ \left( 0,0 \right),\left( 1,1 \right) \right\},
}{L_{bc} = \left\{ \left( 0,0 \right),\left( 1,1 \right) \right\},
}{L_{ac} = \left\{ \left( 0,1 \right),\left( 1,0 \right) \right\}.}$$

Cada interfaz de una variable admite los valores:

$$\left\{ 0,1 \right\}.$$

Además, cualquier pareja de estas relaciones puede satisfacerse conjuntamente.

Pero las tres relaciones simultáneas exigirían:

$$a = b,\ b = c,\ a \neq c.$$

Las dos primeras implican $a = c$, contradiciendo la tercera. Por tanto:

$$L_{ab} \bowtie L_{bc} \bowtie L_{ac} = \varnothing.$$

**Interpretación:** el ejemplo refuta la regla incorrecta "si las partes son compatibles por parejas, existe una realización global".

El Módulo II evita esa conclusión comprobando la composición completa y la conservación de todas las vistas.

**Definición 4.6. Recursos compartidos.**

Para cada fondo de recursos $\rho$, declaramos:

-   Una unidad común.

-   Una capacidad o presupuesto $C_{\rho} \geq 0$.

-   Un conjunto $D_{\rho}$de identidades de demanda.

-   La cantidad $c_{d}(r)$correspondiente a cada demanda $d$, en cada fila $r$.

Cuando todas las cantidades están definidas y son compatibles, el uso total es:

$$\boxed{U_{\rho}(r) = \sum_{d \in D_{\rho}}^{}c_{d}(r).}$$

La condición presupuestaria es:

$$U_{\rho}(r) \leq C_{\rho}.$$

Cada demanda se cuenta una vez por su identidad.

Dos referencias al mismo consumo se identifican antes del cálculo. Dos demandas distintas dirigidas al mismo fondo se suman.

Esta suma contabiliza cantidades aditivas del mismo recurso y unidad. No agrega funciones heterogéneas ni produce una medida universal de valor.

Las diferencias de tiempo también importan: un presupuesto instantáneo se comprueba por instante. Un presupuesto acumulado requiere una interpretación temporal explícita de las cantidades que se suman.

**Proposición 4.5. Certificación presupuestaria sobre una relación.**

Una relación $R$cumple todos los presupuestos declarados exactamente cuando:

$$\boxed{\forall r \in R\text{~}\forall\rho:U_{\rho}(r) \leq C_{\rho}.}$$

En una tabla finita, un registro completo de las desigualdades incumplidas está vacío si y solo si se cumple ese universal.

La no vacuidad se comprueba por separado:

$$R \neq \varnothing.$$

Un universal verdadero sobre una relación vacía no demuestra la existencia de una alternativa realizable.

La evaluación presupuestaria tampoco elimina retrospectivamente las filas que incumplen una restricción. Estas permanecen identificadas en la relación de partida y en el diagnóstico.

**Ejemplo 4.1. Dos sectores que comparten un presupuesto de agua.**

Consideremos dos sectores que pueden solicitar cero o seis unidades de agua.

En este ejemplo sintético, las solicitudes causalmente posibles son:

$$C = \left\{ \left( 0,0 \right),\left( 6,0 \right),\left( 0,6 \right),\left( 6,6 \right) \right\}.$$

Fijamos un presupuesto autorizado de diez unidades:

$$a + b \leq 10.$$

La relación de solicitudes admisibles es:

$$R_{adm} = \left\{ \left( 0,0 \right),\left( 6,0 \right),\left( 0,6 \right) \right\}.$$

El caso $\left( 6,6 \right)$permanece en $C$, pero incumple el presupuesto:

$$6 + 6 = 12 > 10.$$

Las proyecciones individuales de la relación admisible son:

$${\pi_{a}R_{adm} = \left\{ 0,6 \right\},
}{\pi_{b}R_{adm} = \left\{ 0,6 \right\}.}$$

Si conserváramos solamente estas dos listas, su recomposición incluiría nuevamente:

$$\left( 6,6 \right).$$

Cada solicitud de seis unidades es admisible por separado, pero no ambas conjuntamente.

**Este es un uso incorrecto que el módulo detecta:** las proyecciones individuales perdieron la restricción del fondo compartido.

La composición exacta conserva también esa restricción:

$$R_{adm} = \left( \pi_{a}R_{adm} \bowtie \pi_{b}R_{adm} \right) \cap \left\{ \left( a,b \right):a + b \leq 10 \right\}.$$

Hemos omitido en la escritura la base común, que permanece fijada.

Las variables representan solicitudes y el límite es un presupuesto. Si representaran cantidades físicamente entregadas y el límite expresara conservación física, esa interpretación y su integración con la dinámica deberían declararse en el modelo.

**Definición 4.7. Reducción multiescalar relativa a consultas.**

Una vez construida la relación conjunta, puede ser conveniente utilizar una descripción más compacta.

Sea:

$$H = R$$

el conjunto de filas fuente, y sea una representación total:

$$\psi:H \rightarrow Z.$$

Fijemos una familia de consultas parciales:

$$\mathcal{Q,\ }q:H \rightharpoonup Y_{q}.$$

Como en el módulo 0, cada consulta conserva su dominio y valor mediante:

$$\widehat{q}(h) = \left\{ \begin{matrix}
\left( definido,q(h) \right), & h \in D_{q}, \\
\left( fuera\text{~}de\text{~}dominio, \dagger_{q} \right), & h \notin D_{q}.
\end{matrix} \right.\ $$

La representación será suficiente para esta familia cuando todas las consultas puedan evaluarse sobre ella preservando esos registros.

**Teorema 4.6. Criterio exacto de reducción suficiente.**

Existen consultas reducidas sobre $\psi(H)$que conservan dominio y valor de todas las consultas de $\mathcal{Q}$si y solo si:

$$\boxed{\psi(h) = \psi\left( h^{'} \right) \Longrightarrow \forall q \in \mathcal{Q:}\widehat{q}(h) = \widehat{q}\left( h^{'} \right).}$$

**Demostración de necesidad.**

Si cada consulta se obtiene mediante una función de $\psi(h)$, dos filas con la misma representación deben producir el mismo registro de dominio y valor.

**Demostración de suficiencia.**

Para $z \in \psi(H)$, elegimos cualquier $h$de su fibra.

Para cada consulta, asignamos al representante reducido el registro:

$$\widehat{q}(h).$$

La condición del teorema garantiza que este registro es independiente de la fila elegida.

En particular, cada fibra está completamente incluida en $D_{q}$o completamente fuera de él. En las fibras definidas, los valores son constantes.

Por tanto, existe una consulta parcial reducida $q^{red}$con:

$$D_{q^{red}} = \psi\left( D_{q} \right),$$

y:

$$q = q^{red} \circ \psi.$$

La consulta reducida es única sobre la imagen representada. $\square$

Si también se quieren conservar los motivos de indefinición, esos motivos se incluyen entre los observables que deben permanecer constantes. En caso contrario, sólo se conserva la condición de dominio y un diagnóstico genérico.

**Convención 4.1. Procedencia y contenido de la representación.**

La procedencia de una fila debe mantenerse para auditar sus fuentes. Pero esa información no se introduce automáticamente como una variable observable de la reducción.

Consideremos:

$${h_{1} = \left( w_{1},a, = 0b = 0 \right),
}{h_{2} = \left( w_{2},a, = 0b = 1 \right).}$$

Si la representación solicitada conserva únicamente $a$:

$$\psi(h) = a(h),$$

entonces:

$$\psi\left( h_{1} \right) = \psi\left( h_{2} \right) = 0.$$

La consulta:

$$q(h) = b(h)$$

tiene respuestas diferentes:

$$q\left( h_{1} \right) = 0,\ q\left( h_{2} \right) = 1.$$

Por tanto, esta representación no es suficiente para consultar $b$.

Añadir silenciosamente $w_{1},w_{2}$a la representación impediría comparar esas dos filas y ocultaría la pérdida de información. Se habría cambiado la representación que se pretendía certificar.

La distinción es:

-   **Al recomponer registros**, se conservan las identidades comunes para evitar mezclar ocurrencias incompatibles.

-   **Al verificar una reducción**, se examinan exactamente los observables que esa reducción declara conservar.

-   **En la auditoría**, se retienen todas las filas originales como procedencia.

**Proposición 4.7. Conservación de resultados conjuntos.**

Si la recomposición auditada es exactamente $R$, conserva cualquier afirmación existencial o universal sobre esas mismas filas completas.

Además, si todas las consultas de $\mathcal{Q}$descienden por $\psi$, entonces:

$$\boxed{\left\{ \left( \widehat{q}(h) \right)_{q \in \mathcal{Q}}:h \in H \right\} = \left\{ \left( \widehat{q^{red}}(z) \right)_{q \in \mathcal{Q}}:z \in \psi(H) \right\}.}$$

La igualdad es entre conjuntos de **vectores conjuntos de resultados**.

**Demostración.**

Una recomposición exacta permite sustituir el conjunto de filas por otro igual en cualquier cuantificador sobre ellas.

Para la segunda afirmación, tomemos $h \in H$y definamos $z = \psi(h)$. Todas las ecuaciones de descenso se aplican a esa misma fila, por lo que conservan el vector completo.

Recíprocamente, para $z \in \psi(H)$, existe una fila $h$de su fibra. Las mismas ecuaciones reconstruyen todo el vector a partir de ese único testigo.

No se utiliza una fila distinta para justificar cada componente. Los registros de dominio también forman parte del vector. $\square$

La igualdad no afirma que se conserve el número de ejecuciones ni sus probabilidades.

Si existe una ley probabilística sobre las filas originales, su transporte requiere sumar la masa de las fibras correspondientes. La composición y la reducción relacional no inventan esa ley.

El Módulo II establece tres garantías diferentes: **compatibilidad de interfaces, exactitud de la recomposición y suficiencia de las reducciones**. Cada una tiene una condición explícita y una demostración propia.

En las presentaciones finitas declaradas, esas condiciones pueden verificarse sobre las tablas completas, manteniendo tanto las dependencias como los diagnósticos. Una etiqueta como "reducción dinámica" o "composición adecuada" no sustituye la comprobación de los objetos que debe conservar.

La siguiente entrega desarrollará el **Módulo III: identidad organizacional y capacidad generativa**, donde distinguiremos qué organizaciones pueden alcanzarse, mantenerse o acumularse, y bajo qué políticas y realizaciones se acredita cada capacidad.

**Entrega 5 --- Módulo III: identidad organizacional y capacidad generativa**

Este módulo formaliza **qué organizaciones puede generar un sistema, mediante qué políticas y bajo qué exigencias de alcance, conservación o acumulación**.

La construcción distingue tres preguntas:

-   ¿Qué organización está presente?

-   ¿Qué organizaciones pueden alcanzarse o garantizarse?

-   ¿Qué logros pueden obtenerse mediante una misma política?

Estas preguntas requieren objetos diferentes. Un repertorio de posibilidades, por sí solo, no demuestra que todas puedan realizarse conjuntamente.

Desarrollaremos las tres recetas básicas con un reloj discreto y un horizonte finito. Los contraejemplos estarán identificados como **usos incorrectos que las condiciones del módulo excluyen**.

**1. Identidad organizacional**

**Definición 5.1. Firma e identidad generativa.**

Sea $X$el espacio de estados causales del sistema. Fijado un propósito generativo, se declara una función de firma:

$$\Gamma_{G}:X \longrightarrow S_{G}.$$

La firma recoge los aspectos organizacionales relevantes para ese propósito.

Sobre las firmas alcanzadas se declara una relación de equivalencia:

$$\equiv_{G}\text{~} \subseteq \Gamma_{G}(X) \times \Gamma_{G}(X).$$

Esta relación debe ser reflexiva, simétrica y transitiva. El espacio de identidades generativas es:

$$\mathcal{Q}_{G} = \Gamma_{G}(X)/ \equiv_{G}.$$

La identidad generativa de un estado es:

$$q_{G}(x) = \left\lbrack \Gamma_{G}(x) \right\rbrack_{\equiv_{G}}.$$

Dos estados tienen la misma identidad cuando sus firmas pertenecen a la misma clase:

$$q_{G}(x) = q_{G}(y)\text{\:\,} \Longleftrightarrow \text{\:\,}\Gamma_{G}(x) \equiv_{G}\Gamma_{G}(y).$$

La identidad queda vinculada al propósito declarado. Una equivalencia adecuada para estudiar la organización de un sistema puede resultar insuficiente para estudiar su evolución causal.

En particular:

$$q_{G}(x) = q_{G}(y)$$

**no implica automáticamente que** $x$**e** $y$**tengan los mismos futuros**. Esa afirmación necesita la suficiencia dinámica del Módulo 0.

**Significado de las clases.**

Si cada firma $s$recibe un significado $J_{G}(s)$, para atribuir un significado único a su clase se exige:

$$s \equiv_{G}s^{'} \Longrightarrow J_{G}(s) = J_{G}\left( s^{'} \right).$$

Entonces:

$${\bar{J}}_{G}\left( \lbrack s\rbrack \right) = J_{G}(s)$$

está bien definido: cualquier representante de la clase produce el mismo significado.

Los significados utilizados en la comparación deben estar definidos y ser no vacíos. Su fundamentación pertenece a los datos semánticos del modelo; no se obtiene del resultado generativo que se desea demostrar.

**2. Conservación organizacional**

**Definición 5.2. Preorden de conservación.**

Sobre $\mathcal{Q}_{G}$se declara un preorden:

$$\trianglelefteq \text{~} \subseteq \mathcal{Q}_{G} \times \mathcal{Q}_{G}.$$

La expresión:

$$g \trianglelefteq h$$

significa que la organización $h$conserva aquello que el protocolo exige conservar de $g$.

Por ser un preorden:

$$g \trianglelefteq g,$$

y:

$$g \trianglelefteq h,\ h \trianglelefteq k \Longrightarrow g \trianglelefteq k.$$

No se exige que conservar una organización signifique mantener exactamente la misma identidad. Una organización ampliada puede conservar una anterior.

Tampoco se identifica conservación con aumento de tamaño. Si, en un ejemplo concreto, las organizaciones son conjuntos de componentes:

$$\left\{ a,b \right\} \longrightarrow \left\{ b,c \right\},$$

la cantidad de componentes permanece igual, pero se pierde $a$.

La relación $\trianglelefteq$debe representar la conservación pertinente: componentes, interfaces, capacidades u otras propiedades expresamente declaradas. No incorpora automáticamente conservación del bienestar o de los recursos.

**3. Experimentos, políticas y realizaciones**

**Definición 5.3. Ámbito generativo.**

Fijamos:

-   un modelo y un contexto causal;

-   un testigo inicial $w$, con una inicialización realizada $b_{\gamma}(w)$;

-   una familia de políticas permitidas $\Pi$;

-   un horizonte $H\mathbb{\in N}$;

-   una identidad generativa y una receta de evaluación.

Para cada política $\pi$, se declara una familia de escenarios:

$$\Xi\left( w,\pi \right).$$

Cada escenario puede admitir varias realizaciones:

$$Runs_{H,\gamma}\left( b_{\gamma};(w);\pi\xi \right).$$

Por tanto, un escenario no se sustituye por una única trayectoria salvo que se haya probado su unicidad.

Conservamos las ocurrencias como pares:

$$\mathcal{O}_{\pi}(w) = \left\{ \left( \xi,e \right),:\xi \in \Xi\left( w,\pi \right)\text{~}e \in Runs_{H,\gamma}\left( b_{\gamma};(w);\pi\xi \right) \right\}.$$

Cada ejecución mantiene su procedencia: inicialización, contexto, política, escenario y rama causal.

En la presentación discreta, una ejecución tiene estados:

$$x_{0},x_{1},\ldots,x_{T_{e}},\ 0 \leq T_{e} \leq H.$$

Una terminación causal antes del horizonte conserva su longitud real. No se inventan estados posteriores para completar una exigencia de persistencia.

La política utiliza únicamente su información legítima. Evaluar posteriormente todas las realizaciones no concede al controlador conocimiento anticipado del escenario.

**4. Traducción a un marco común**

**Definición 5.4. Traducción generativa funcional.**

Sean $X_{A}$y $X_{c}$los espacios de estados del marco nativo y del marco común. Consideremos una traducción parcial:

$$T_{A \rightarrow c}:X_{A} \rightharpoonup X_{c}.$$

Cuando está definida, la identidad común correspondiente a $x$es:

$$g_{c}(x) = q_{G,c}\left( T_{A \rightarrow c}(x) \right).$$

Para los estados requeridos por la receta se exige cobertura de traducción y fidelidad de significado:

$$⟦q_{G,A}(x)⟧_{A} = ⟦q_{G,c}\left( T_{A \rightarrow c}(x) \right)⟧_{c} \neq \varnothing.$$

Si la receta utiliza conservación, también deben preservarse y reflejarse los pares pertinentes:

$$q_{G,A}(x) \trianglelefteq_{A}q_{G,A}(y)\text{\:\,} \Longleftrightarrow \text{\:\,}g_{c}(x) \trianglelefteq_{c}g_{c}(y).$$

La dirección de izquierda a derecha conserva las afirmaciones nativas. La dirección inversa impide que la traducción introduzca una conservación que no estaba acreditada.

La trayectoria traducida es:

$$g_{0},g_{1},\ldots,g_{T_{e}},\ g_{t} = q_{G,c}\left( T_{A \rightarrow c}\left( x_{t} \right) \right).$$

**Las recetas se evalúan sobre estas trayectorias comunes antes de agregar resultados entre realizaciones.**

En las definiciones siguientes suponemos que los datos requeridos están definidos. Más adelante precisaremos el dominio completo de la construcción.

**5. Las tres recetas básicas**

**Definición 5.5. Alcance:** $att$**.**

Una identidad se alcanza cuando aparece en algún tiempo estrictamente posterior al inicial:

$$Ach_{att}(e) = \left\{ g_{t}:1 \leq t \leq T_{e} \right\}.$$

El tiempo cero no cuenta como logro futuro.

Esta receta registra aparición. No exige duración posterior.

**Conservación durante una ventana:** $hold,L$**.**

Para $L\mathbb{\in N}$:

$$Ach_{hold,L}(e) = \left\{ g_{t}:\begin{matrix}
1 \leq t,\ t + L \leq T_{e}, \\
\forall s \in \left\{ t,\ldots,t + L \right\},\ g_{t} \trianglelefteq g_{s}
\end{matrix} \right\}.$$

Se acredita $g_{t}$cuando su organización queda conservada durante los $L$pasos posteriores, incluido todo el intervalo.

La identidad posterior puede cambiar. Lo exigido es que conserve la organización acreditada.

**Acumulación desde el origen:** $acc$**.**

Definimos:

$$Ach_{acc}(e) = \left\{ g_{t}:\begin{matrix}
1 \leq t \leq T_{e}, \\
\forall s \in \left\{ 1,\ldots,t \right\},\ g_{s - 1} \trianglelefteq g_{s}
\end{matrix} \right\}.$$

Una identidad se acredita por acumulación cuando toda la cadena desde el origen hasta su aparición conserva sucesivamente las organizaciones anteriores.

Si la cadena pierde esa propiedad, los logros ya acreditados permanecen registrados. Las identidades posteriores dejan de incorporarse mediante esta receta.

Esto no afirma que una organización posterior sea imposible; afirma que no fue obtenida conservando toda la cadena desde el origen fijado.

**Teorema 5.1. Relaciones entre las recetas.**

Sobre una misma trayectoria, con el mismo preorden de conservación:

$${Ach_{hold,0} = Ach_{att},
}{Ach_{hold,L + 1} \subseteq Ach_{hold,L} \subseteq Ach_{att},}$$

y:

$$Ach_{acc} \subseteq Ach_{att}.$$

Además, si $g_{t}$se acredita mediante $acc$, entonces:

$$\forall j \in \left\{ 0,\ldots,t \right\},\ g_{j} \trianglelefteq g_{t}.$$

**Demostración.**

Para $L = 0$, la única conservación exigida es $g_{t} \trianglelefteq g_{t}$, verdadera por reflexividad.

Una ventana de longitud $L + 1$contiene la ventana de longitud $L$con el mismo inicio. Por tanto, conservar durante la primera implica conservar durante la segunda.

Tanto $hold$como $acc$requieren una aparición en tiempo positivo, lo que prueba sus inclusiones en $att$.

Finalmente, en una cadena acumulativa:

$$g_{j} \trianglelefteq g_{j + 1} \trianglelefteq \cdots \trianglelefteq g_{t}.$$

La transitividad da $g_{j} \trianglelefteq g_{t}$. $\square$

Estas propiedades no afirman conservación después del intervalo o del hito acreditado.

**Ejemplo 5.1. Alcanzar, conservar y acumular son propiedades distintas.**

En este ejemplo, las identidades son conjuntos de componentes y:

$$g \trianglelefteq h\text{\:\,} \Longleftrightarrow \text{\:\,}g \subseteq h.$$

Consideremos:

  -----------------------------------------------------------------------
  **Tiempo**                 **Organización**
  -------------------------- --------------------------------------------
  $$0$$                      $$\varnothing$$

  $$1$$                      $$\left\{ a \right\}$$

  $$2$$                      $$\left\{ a,b \right\}$$

  $$3$$                      $$\left\{ b \right\}$$

  $$4$$                      $$\left\{ b,c \right\}$$

  $$5$$                      $$\left\{ b,c \right\}$$
  -----------------------------------------------------------------------

Entonces:

$$Ach_{att} = \left\{ \left\{ a \right\},\left\{ a,b \right\},\left\{ b \right\},\left\{ b,c \right\} \right\}.$$

Para una ventana de un paso:

$$Ach_{hold,1} = \left\{ \left\{ a \right\},\left\{ b \right\},\left\{ b,c \right\} \right\}.$$

La organización $\left\{ a \right\}$queda conservada en $\left\{ a,b \right\}$. En cambio, $\left\{ a,b \right\}$no queda conservada en el paso siguiente, porque se pierde $a$.

Para acumulación:

$$Ach_{acc} = \left\{ \left\{ a \right\},\left\{ a,b \right\} \right\}.$$

La cadena acumulativa se interrumpe en:

$$\left\{ a,b \right\} \longrightarrow \left\{ b \right\}.$$

Los logros anteriores permanecen acreditados, pero los posteriores no cumplen la condición de acumulación desde ese origen.

El ejemplo también muestra que, en general:

$$Ach_{acc} \subseteq \not{}Ach_{hold,1},$$

y:

$$Ach_{hold,1} \subseteq \not{}Ach_{acc}.$$

Son exigencias temporales diferentes.

**6. Posibilidad y robustez**

**Definición 5.6. Logros de una política.**

Sea $r$una de las recetas anteriores.

Para una política $\pi$, sus logros posibles son:

$$P_{\pi}^{r,poss}(w) = \bigcup_{\left( \xi,e \right) \in \mathcal{O}_{\pi}(w)}^{}Ach_{r}(e).$$

Una identidad pertenece a este conjunto si alguna realización de esa política la acredita.

Sus logros robustos son:

$$P_{\pi}^{r,rob}(w) = \bigcap_{\left( \xi,e \right) \in \mathcal{O}_{\pi}(w)}^{}Ach_{r}(e),$$

bajo las condiciones:

$$\Xi\left( w,\pi \right) \neq \varnothing$$

y:

$$\forall\xi \in \Xi\left( w,\pi \right),\ Runs_{H,\gamma}\left( b_{\gamma};(w);\pi\xi \right) \neq \varnothing.$$

La cobertura debe incluir todas esas realizaciones.

No basta que exista una realización en algún escenario si otro escenario declarado tiene su fibra vacía o sin acreditar.

Los repertorios brutos de la familia de políticas son:

$${G_{r}^{poss}(w) = \bigcup_{\pi \in \Pi}^{}P_{\pi}^{r,poss}(w),
}{G_{r}^{rob}(w) = \bigcup_{\pi \in \Pi}^{}P_{\pi}^{r,rob}(w).}$$

**Teorema 5.2. Significado exacto de los cuantificadores.**

Dentro del dominio certificado:

$$g \in G_{r}^{poss}(w)$$

equivale a que existan una política, un escenario y una realización que acrediten $g$.

Por su parte:

$$g \in G_{r}^{rob}(w)$$

equivale a que exista **una misma política** cuyas realizaciones acrediten $g$en todos sus escenarios.

Para la receta de alcance, la segunda afirmación tiene la forma:

$$\exists\pi \in \Pi\text{~}\forall\xi \in \Xi\left( w,\pi \right)\text{~}\forall e \in Runs\left( w;\pi;\xi \right)\text{~}\exists t \in \left\{ 1,\ldots,T_{e} \right\}:g_{t} = g,$$

junto con las condiciones de no vaciedad anteriores.

El tiempo de logro puede depender de la realización.

Además:

$$G_{r}^{rob}(w) \subseteq G_{r}^{poss}(w).$$

**Demostración.**

Pertenecer a una unión equivale a pertenecer a alguno de sus conjuntos. Pertenecer a una intersección equivale a pertenecer a todos.

Esto produce los cuantificadores indicados.

Si una política garantiza $g$, la no vaciedad de sus realizaciones permite elegir una de ellas. Esa realización acredita $g$, por lo que $g$también es posible. $\square$

La robustez no utiliza probabilidades. Una realización causal de probabilidad cero continúa incluida en su cuantificación.

**Ejemplo 5.2. Una familia de capacidades no equivale a una política que las realice todas.**

Utilizamos $att$, horizonte $2$, origen $o$, políticas permitidas $\Pi = \left\{ p,q \right\}$y dos escenarios.

Supongamos exactamente una realización por cada combinación:

  -----------------------------------------------------------------------------------------
  **Política**    **Escenario**       **Trayectoria**            **Logros**
  --------------- ------------------- -------------------------- --------------------------
  $$p$$           $$\xi_{1}$$         $$\left( o,u,z \right)$$   $$\left\{ u,z \right\}$$

  $$p$$           $$\xi_{2}$$         $$\left( o,u,u \right)$$   $$\left\{ u \right\}$$

  $$q$$           $$\xi_{1}$$         $$\left( o,v,v \right)$$   $$\left\{ v \right\}$$

  $$q$$           $$\xi_{2}$$         $$\left( o,v,z \right)$$   $$\left\{ v,z \right\}$$
  -----------------------------------------------------------------------------------------

Las cuatro identidades $o,u,v,z$son distintas.

Por intersección:

$$P_{p}^{att,rob} = \left\{ u \right\},\ P_{q}^{att,rob} = \left\{ v \right\}.$$

Por tanto:

$$G_{att}^{rob} = \left\{ u,v \right\},$$

mientras que:

$$G_{att}^{poss} = \left\{ u,v,z \right\}.$$

La identidad $z$puede alcanzarse, pero ninguna política permitida la garantiza en ambos escenarios.

**Contraejemplo de uso incorrecto 5.1. Intercambiar los cuantificadores.**

En el ejemplo:

$$\forall\xi\text{~}\exists\pi:\text{la~pol}\overset{ˊ}{\text{ı}}\text{tica~}\pi\text{~alcanza~}z\text{~en~}\xi.$$

Sin embargo:

$$\neg\exists\pi\text{~}\forall\xi:\text{la~pol}\overset{ˊ}{\text{ı}}\text{tica~}\pi\text{~alcanza~}z\text{~en~}\xi.$$

Para $\xi_{1}$sirve $p$; para $\xi_{2}$sirve $q$. Eso no proporciona una misma política robusta.

La definición del módulo excluye esta inferencia al mantener la política elegida fuera de los cuantificadores universales.

**7. Traducción antes de agregar robustez**

**Contraejemplo de uso incorrecto 5.2. Traducir después de intersectar.**

Consideremos el caso particular en que existe una función bien definida entre identidades:

$$h:\mathcal{Q}_{A} \longrightarrow \mathcal{Q}_{c},$$

con:

$$h(a) = h(b) = c,\ a \neq b.$$

Supongamos que dos realizaciones alcanzan, respectivamente:

$$A_{1} = \left\{ a \right\},\ A_{2} = \left\{ b \right\}.$$

Si primero intersectamos los logros nativos:

$$A_{1} \cap A_{2} = \varnothing,$$

y después traducimos:

$$h\left\lbrack A_{1} \cap A_{2} \right\rbrack = \varnothing.$$

Pero al traducir cada realización antes de agregar:

$$h\left\lbrack A_{1} \right\rbrack = \left\{ c \right\},\ h\left\lbrack A_{2} \right\rbrack = \left\{ c \right\},$$

obtenemos:

$$h\left\lbrack A_{1} \right\rbrack \cap h\left\lbrack A_{2} \right\rbrack = \left\{ c \right\}.$$

Por tanto:

$$h\left\lbrack A_{1} \cap A_{2} \right\rbrack \neq h\left\lbrack A_{1} \right\rbrack \cap h\left\lbrack A_{2} \right\rbrack.$$

La identidad común $c$está garantizada, aunque no haya una identidad nativa idéntica en ambas realizaciones.

La condición que evita este uso incorrecto es explícita: **traducir las trayectorias y evaluar la receta en el marco común antes de formar las intersecciones robustas**.

En este ejemplo, la identificación de $a$y $b$debe ser legítima para el significado común declarado. La mera conveniencia del resultado no justifica identificar organizaciones.

**8. Origen y capacidad generativa canónica**

**Definición 5.7. Origen representado.**

Cuando la traducción inicial está definida, el origen común es:

$$g_{0}(w) = q_{G,c}\text{ }\left( T_{A \rightarrow c}\left( x_{0}(w) \right) \right).$$

Este objeto se obtiene de la inicialización. Su definición no requiere conocer qué organizaciones se alcanzarán después.

La fidelidad del origen es una obligación para certificar la comparación, pero su representación inicial puede permanecer disponible aunque una obligación futura no se cumpla.

**Definición 5.8. CAG y repertorio adicional.**

Fijados la receta $r$y el cuantificador:

$$\diamond \in \left\{ poss,rob \right\},$$

definimos:

$$CAG^{r, \diamond , +}(w) = G_{r}^{\diamond}(w) \smallsetminus \left\{ g_{0}(w) \right\},$$

y:

$$CAG^{r, \diamond}(w) = \left\{ g_{0}(w) \right\} \cup CAG^{r, \diamond , +}(w).$$

El signo $+$identifica el repertorio adicional respecto del origen.

**Proposición 5.3. Separación entre origen y logros futuros.**

Se cumplen:

$${g_{0}(w) \in CAG^{r, \diamond}(w),
}{CAG^{r, \diamond , +}(w) = CAG^{r, \diamond}(w) \smallsetminus \left\{ g_{0}(w) \right\},}$$

y, para $g \neq g_{0}(w)$:

$$g \in CAG^{r, \diamond}(w)\text{\:\,} \Longleftrightarrow \text{\:\,}g \in G_{r}^{\diamond}(w).$$

**Demostración.**

La primera afirmación resulta de la unión con el singleton del origen. Al retirarlo queda exactamente el repertorio adicional. Para cualquier identidad distinta del origen, añadir o retirar ese singleton no cambia su pertenencia. $\square$

La pertenencia estructural de $g_{0}$al CAG **no acredita retorno, conservación ni acumulación futura del origen**.

Si una trayectoria vuelve a $g_{0}$, ese logro permanece registrado en $G_{r}^{\diamond}$y en sus testigos temporales. Simplemente no se cuenta como otra identidad adicional.

En el ejemplo anterior:

$$CAG^{att,rob} = \left\{ o,u,v \right\},$$

aunque ninguna trayectoria vuelve a $o$.

Una identidad adicional tampoco implica por sí sola innovación beneficiosa. Pasar de $\left\{ a,b \right\}$a $\left\{ a \right\}$cambia la identidad, pero representa una pérdida de componentes.

**9. Certificación de una política común**

**Definición 5.9. Políticas que garantizan un conjunto de demandas.**

Para un conjunto de identidades $D \subseteq \mathcal{Q}_{G,c}$, definimos:

$$Joint_{r}\left( w,D \right) = \left\{ \pi \in \Pi:D \subseteq P_{\pi}^{r,rob}(w) \right\}.$$

Entonces:

$$Joint_{r}\left( w,D \right) \neq \varnothing$$

significa que existe una política permitida que acredita todas las identidades de $D$en cada una de sus realizaciones.

**Proposición 5.4. Caracterización exacta.**

Una política pertenece a $Joint_{r}\left( w,D \right)$si y solo si:

$$\forall\xi\text{~}\forall e \in Runs\left( w;\pi;\xi \right)\text{~}\forall g \in D:g \in Ach_{r}(e),$$

con la cobertura y no vaciedad requeridas.

**Demostración.**

Se desarrolla la inclusión:

$$D \subseteq \bigcap_{\left( \xi,e \right) \in \mathcal{O}_{\pi}(w)}^{}Ach_{r}(e).$$

Esto equivale a que todo miembro de $D$pertenezca a los logros de cada realización. $\square$

En el ejemplo 5.2:

$$\left\{ u,v \right\} \subseteq G_{att}^{rob},$$

pero:

$$Joint_{att}\left( w,\left\{ u,v \right\} \right) = \varnothing.$$

Cada identidad tiene una política robusta, pero no comparten una.

Incluso cuando $Joint_{r}\left( w,D \right)$es no vacío, los instantes de logro pueden diferir entre identidades. Para acreditar coexistencia o conservación conjunta se necesita una receta que exija expresamente esa propiedad.

Los testigos se conservan por política y realización. La unión exterior de repertorios no los fusiona.

**10. Dominio de la construcción y cobertura**

**Definición 5.10. Dominio generativo certificado.**

Primero debe comprobarse que la presentación esté bien formada: tipos, equivalencias, preórdenes y datos causales coherentes.

Para esa presentación, el CAG funcional se construye sobre los testigos donde se acreditan:

1.  **Inicialización:** existe una condición inicial realizada y el origen común pertinente.

2.  **Ámbito:** están fijados contexto, políticas, escenarios, horizonte y receta.

3.  **Cobertura causal:** se incluyen todas las realizaciones requeridas.

4.  **No vaciedad:** cada escenario declarado de cada política utilizada tiene realizaciones.

5.  **Cobertura de traducción:** todos los registros requeridos tienen traducción.

6.  **Fidelidad:** se conservan los significados y las relaciones utilizadas por la receta.

7.  **Suficiencia de lectura:** los observables disponibles determinan todos los logros que se van a agregar.

Estas obligaciones se comprueban desde los datos previos al CAG.

En una presentación causal finita, la cobertura se obtiene expandiendo todas las ramas permitidas hasta el horizonte o la terminación causal. La inducción sobre la profundidad demuestra que ninguna realización generada queda fuera.

Los requerimientos de lectura se derivan de la receta:

-   $att$utiliza las identidades en los tiempos positivos.

-   $hold,L$utiliza las identidades y los pares de conservación de sus ventanas.

-   $acc$utiliza las identidades y los pares consecutivos de toda la traza.

En el contrato finito adoptado se comprueban todas las identidades de las trazas. Para $acc$, también se comprueban los pares posteriores a una pérdida temprana: el resultado desfavorable de una comparación no autoriza a ocultar datos ausentes.

**Ausencia de logros y ausencia de información.**

Si todas las realizaciones requeridas están cubiertas y ninguna acredita una identidad adicional, puede obtenerse:

$$CAG^{r, \diamond , +}(w) = \varnothing.$$

Si falta una traducción requerida, no se sustituye el resultado por el conjunto vacío. La construcción queda fuera de su dominio certificado, conservando el diagnóstico.

Una familia de políticas explícitamente vacía produce:

$$G_{r}^{\diamond}(w) = \varnothing,$$

y puede dejar únicamente el origen representado. Esto no acredita robustez ni demuestra ausencia de futuros fuera de esa familia.

Si se utiliza una traducción relacional, deben conservarse todas sus interpretaciones conjuntas compatibles. Un resultado funcional exige que estén cubiertas y determinen un mismo resultado; de otro modo, la salida conserva su multiplicidad.

**11. Descenso a clases iniciales**

El Módulo 0 estableció cuándo una representación conserva una función parcial. Aquí aplicamos ese principio al CAG.

**Definición 5.11. Equivalencia inicial y función generativa.**

Sea $W$el conjunto declarado de testigos iniciales y sea:

$$\equiv_{P}^{0}$$

una equivalencia suministrada por el protocolo $P$.

Su fundamento debe proceder de las historias, firmas y relaciones operacionales pertinentes. La coincidencia nominal de estados o modelos no acredita esa equivalencia.

Escribamos:

$$f:W \rightharpoonup \mathcal{P}\left( \mathcal{Q}_{G,c} \right),\ f(w) = CAG^{r, \diamond}(w).$$

Su dominio $D_{f}$es el dominio certificado anterior.

Para admitir una clase $C \in W/ \equiv_{P}^{0}$, exigimos:

$$C \subseteq D_{f},$$

un mismo ámbito comparativo, un origen constante:

$$\forall w,v \in C,\ g_{0}(w) = g_{0}(v),$$

y un valor constante:

$$\forall w,v \in C,\ f(w) = f(v).$$

**Teorema 5.5. Descenso seguro.**

Sobre las clases admitidas, la definición:

$$CAG(C) = f(w),\ w \in C,$$

es independiente del representante. También descienden el origen y el repertorio adicional.

**Demostración.**

Toda clase de equivalencia es no vacía. Todos sus miembros están en $D_{f}$, por lo que sus valores existen.

La constancia de $f$garantiza que cualquier representante produce el mismo CAG. La constancia de $g_{0}$garantiza un mismo origen. Por tanto:

$$CAG^{+}(C) = CAG(C) \smallsetminus \left\{ g_{0}(C) \right\}$$

también es independiente del representante. $\square$

Este es el máximo dominio seguro de **clases enteras** bajo esas exigencias.

Para factorizar toda la función parcial original, además se requiere que $D_{f}$sea una unión de clases y que $f$sea constante en cada clase definida. Admitir algunas clases seguras solo factoriza la restricción correspondiente.

**Contraejemplo de uso incorrecto 5.3. Elegir un representante favorable.**

Supongamos:

$$w \equiv_{P}^{0}v,$$

pero el CAG de $w$está certificado y el de $v$carece de una traducción requerida.

No puede asignarse a la clase el resultado de $w$como si representara a todos sus miembros.

La condición:

$$C \subseteq D_{f}$$

excluye exactamente esa operación.

Asimismo, la igualdad del conjunto CAG no permite trasladar automáticamente los testigos de política de un representante a otro. Esos testigos conservan su procedencia.

**12. Comparación de capacidades generativas**

**Definición 5.12. Dominancia por inclusión.**

Dentro de un bloque comparativo autorizado:

$$A \succeq_{CAG}B\text{\:\,} \Longleftrightarrow \text{\:\,}CAG(B) \subseteq CAG(A).$$

El bloque fija el significado común de las identidades, la receta, el horizonte y las condiciones del experimento. Las variables que se comparan deben declararse.

Por ejemplo:

-   Para comparar condiciones iniciales, se mantiene la misma familia de políticas y el mismo protocolo.

-   Para comparar políticas, se mantiene la misma inicialización, el mismo proceso y el mismo marco de evaluación; cambia la política seleccionada.

No basta que dos modelos o políticas tengan nombres coincidentes.

**Teorema 5.6. Estructura de orden del CAG.**

La relación $\succeq_{CAG}$es un preorden.

La equivalencia:

$$A \sim_{CAG}B\text{\:\,} \Longleftrightarrow \text{\:\,}CAG(A) = CAG(B)$$

produce un orden parcial sobre las clases correspondientes.

**Demostración.**

La inclusión es reflexiva:

$$CAG(A) \subseteq CAG(A).$$

También es transitiva:

$$CAG(C) \subseteq CAG(B)\ \text{y}\ CAG(B) \subseteq CAG(A)$$

implican:

$$CAG(C) \subseteq CAG(A).$$

La inclusión mutua equivale a igualdad de conjuntos. Al identificar las condiciones con igual CAG, se obtiene antisimetría. $\square$

La dominancia estricta corresponde a:

$$CAG(B) \subsetneq CAG(A).$$

La incomparabilidad corresponde a que ninguno de los repertorios contenga al otro, estando ambos definidos y siendo comparables en el ámbito declarado.

Tener la misma cantidad de identidades no prueba equivalencia. Los repertorios:

$$\left\{ o,u \right\},\ \left\{ o,v \right\},\ u \neq v,$$

tienen igual cardinalidad y son incomparables por inclusión.

Esta dominancia expresa una relación entre repertorios generativos. No demuestra por sí sola mayor bienestar, mayor probabilidad de viabilidad ni preferencia normativa.

**Integración del Módulo III**

El Módulo III queda articulado con los anteriores mediante condiciones precisas:

-   Del **Módulo 0** recibe estados suficientes y el criterio de descenso de funciones parciales.

-   Del **Módulo I** conserva la distinción entre identidad organizacional y desempeño funcional.

-   Del **Módulo II** recibe organizaciones, interfaces y dependencias conjuntas: una colección de capacidades locales necesita compatibilidad para constituir una organización realizable.

-   Del modelo causal recibe todas las realizaciones de cada política, manteniendo sus escenarios y su información legítima.

Su salida conserva el origen, el repertorio adicional, la receta, el cuantificador y los testigos que justifican cada logro. Así puede distinguirse entre una organización posible, una organización garantizada y un conjunto de organizaciones garantizadas por una misma política.

**La siguiente entrega es el Módulo IV: bienestar, tiempo y poblaciones.**

**Entrega 6 --- Módulo IV: bienestar, tiempo y poblaciones**

El Módulo IV formaliza **cómo registrar el bienestar de sus portadores a lo largo del tiempo y bajo qué condiciones pueden compararse dos historias**.

Las dimensiones pueden describir condiciones materiales, relacionales, energéticas, informacionales o temporales. Cada una requiere un significado, un dominio de aplicación y un criterio de comparación explícitos.

La construcción conserva cinco elementos diferentes:

$$\boxed{\text{tiempo,~existencia,~dimensiones,~mediciones~y~valores}}$$

Esta separación permite distinguir una medición ausente de la inexistencia de un portador, y una mejora individual de una transformación de la población.

**1. El registro de bienestar**

**Definición 6.1. Reloj de una ejecución.**

Sea $e$una ejecución causal. Su dominio temporal es:

$$E_{e}^{T}: = D_{e}.$$

Este conjunto pertenece a la ejecución. Se conserva aunque durante algún intervalo no existan portadores de bienestar dentro de la frontera estudiada.

En una ejecución discreta finita puede tener la forma:

$$E_{e}^{T} = \left\{ 0,1,\ldots,T_{e} \right\}.$$

Una terminación causal temprana conserva su tiempo real de terminación. No se agregan tiempos ficticios hasta completar el horizonte previsto.

**Definición 6.2. Soporte de existencia.**

Sea $L_{\mathcal{B,}e}(t)$el conjunto de portadores existentes en el tiempo $t$, dentro de la frontera $\mathcal{B}$.

Definimos:

$$S_{e}^{L} = \left\{ \left( \mathcal{l},t \right),:t \in E_{e}^{T}\text{~}\mathcal{l} \in L_{\mathcal{B,}e}(t) \right\}.$$

El conjunto de portadores presentes en algún momento es:

$$L_{H}(e) = \left\{ \mathcal{l},:\exists t\text{\:\,}\left( \mathcal{l},t \right) \in S_{e}^{L} \right\}.$$

Las identidades deben conservarse entre tiempos y escalas. Una misma persona no se transforma en varias por pertenecer simultáneamente a una familia, una organización y una comunidad.

La elección de portadores y de frontera forma parte del modelo. Las comparaciones no quedan restringidas por definición a seres humanos, pero cada tipo de portador necesita una interpretación adecuada de sus dimensiones.

**Definición 6.3. Dimensiones aplicables.**

Para cada par existente $\left( \mathcal{l},t \right)$, se declara un conjunto de dimensiones:

$$J_{\mathcal{l},t,e}.$$

El conjunto de índices de bienestar es:

$$I_{e}^{W} = \left\{ \left( \mathcal{l},t,j \right),:\left( \mathcal{l},t \right) \in S_{e}^{L}\text{~}j \in J_{\mathcal{l},t,e} \right\}.$$

Cada índice $i = \left( \mathcal{l},t,j \right)$dispone de un espacio de valores ordenado:

$$\left( \mathcal{W}_{i}, \preceq_{i} \right).$$

No se exige que todas las dimensiones sean numéricas ni que compartan una unidad.

**Definición 6.4. Mediciones y valores.**

El dominio de mediciones válidas es:

$$D_{e}^{W} \subseteq I_{e}^{W}.$$

Para cada índice medido:

$$w_{e}(i) \in \mathcal{W}_{i},\ i \in D_{e}^{W}.$$

El registro enriquecido es:

$$\boxed{\widetilde{W}(e) = \left( E_{e}^{T},S_{e}^{L},I_{e}^{W},D_{e}^{W},w_{e} \right).}$$

Cada campo responde a una pregunta diferente:

  --------------------------------------------------------------------------------------
  **Campo**                **Pregunta**
  ------------------------ -------------------------------------------------------------
  $$E_{\mathbf{e}}^{T}$$   ¿Qué tiempos pertenecen a la ejecución?

  $$S_{\mathbf{e}}^{L}$$   ¿Quién existe en cada tiempo?

  $$I_{\mathbf{e}}^{W}$$   ¿Qué dimensiones se aplican a cada portador y tiempo?

  $$D_{\mathbf{e}}^{W}$$   ¿Cuáles tienen una medición válida?

  $$w_{\mathbf{e}}$$       ¿Qué valores tienen las dimensiones medidas?
  --------------------------------------------------------------------------------------

El registro conserva además sus referencias, calibraciones y la identidad completa de la ejecución de la que procede.

**2. Existencia, aplicabilidad y medición**

Para soportes identificados, las condiciones de coherencia son:

$${S_{e}^{L} \subseteq L_{H}(e) \times E_{e}^{T},
}{I_{e}^{W} \subseteq \left\{ \left( \mathcal{l},t,j \right):\left( \mathcal{l},t \right) \in S_{e}^{L} \right\},
}{D_{e}^{W} \subseteq I_{e}^{W},\ dom\left( w_{e} \right) = D_{e}^{W}.}$$

Estas inclusiones también tienen consecuencias transitivas. Por ejemplo, toda medición debe corresponder a un tiempo de la ejecución, aunque algún campo intermedio todavía no esté identificado.

Para un tiempo perteneciente al reloj, deben distinguirse las siguientes situaciones:

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Situación conocida**                                                                                                   **Significado**
  ------------------------------------------------------------------------------------------------------------------------ ------------------------------------------------------------
  $$\left( \mathcal{l},t \right) \notin S_{\mathbf{e}}^{L}$$                                                               El portador no existe allí.

  $\left( \mathcal{l},t \right) \in S_{\mathbf{e}}^{L}$, pero $\left( \mathcal{l},t,j \right) \notin I_{\mathbf{e}}^{W}$   Esa dimensión no está incluida como aplicable.

  $$i \in I_{\mathbf{e}}^{W} \smallsetminus D_{\mathbf{e}}^{W}$$                                                           La dimensión es aplicable, pero falta una medición válida.

  $i \in D_{\mathbf{e}}^{W}$, $w_{\mathbf{e}}(i) = 0$                                                                      Existe una medición cuyo valor es cero.
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

El significado de cero depende de su espacio de valores. No representa universalmente ausencia de bienestar ni inexistencia.

Si un soporte es desconocido, no puede reemplazarse por el conjunto vacío. Desconocer quién existe no equivale a saber que nadie existe.

**Un registro parcial puede estar correctamente definido.**

Puede existir:

$$\widetilde{W}(e)$$

aunque:

$$D_{e}^{W} \subsetneq I_{e}^{W}.$$

Lo que falta es información para ciertas consultas, no necesariamente el registro entero.

Por otra parte, el desconocimiento no neutraliza contradicciones conocidas. Si:

$$E_{e}^{T} = \left\{ 0 \right\}$$

y consta una medición en $t = 1$, la presentación es incompatible con el reloj, aunque otros soportes sean desconocidos.

**3. Por qué deben conservarse todas las capas**

**Proposición 6.1. Los índices dimensionales no determinan la existencia, y la existencia no determina el reloj.**

En general:

$$I_{e}^{W}\ \text{no~determina}\ S_{e}^{L},$$

y:

$$S_{e}^{L}\ \text{no~determina}\ E_{e}^{T}.$$

**Demostración.**

Para la primera afirmación, fijemos:

$$E^{T} = \left\{ 0 \right\},\ I^{W} = D^{W} = \varnothing.$$

Son compatibles dos registros distintos:

$$S_{1}^{L} = \varnothing$$

y:

$$S_{2}^{L} = \left\{ \left( \mathcal{l},0 \right) \right\},\ J_{\mathcal{l},0} = \varnothing.$$

Ambos tienen el mismo conjunto vacío de dimensiones, pero solo el segundo registra un portador.

Para la segunda afirmación, fijemos:

$$S^{L} = \left\{ \left( \mathcal{l},0 \right) \right\},\ I^{W} = D^{W} = \varnothing.$$

Este soporte puede pertenecer a una ejecución con reloj:

$$E_{1}^{T} = \left\{ 0 \right\},$$

o a otra con:

$$E_{2}^{T} = \left\{ 0,1 \right\}.$$

En la segunda existe un instante adicional sin portadores. El soporte vital no permite reconstruirlo. $\square$

Por eso el reloj se obtiene de la ejecución causal y la existencia se registra directamente. No se reconstruyen retrospectivamente desde las mediciones disponibles.

**4. Consultas de existencia y persistencia**

La existencia puede consultarse separadamente de los valores dimensionales.

Con soporte conocido:

$$\mathsf{HayPortadores}(e)\text{\:\,} \Longleftrightarrow \text{\:\,}S_{e}^{L} \neq \varnothing.$$

Para un conjunto requerido de tiempos $T_{req} \subseteq E_{e}^{T}$:

$$\mathsf{ExistenciaEn}\left( e,T_{req} \right)\text{\:\,} \Longleftrightarrow \text{\:\,}\forall t \in T_{req}\text{\:\,}\exists\mathcal{l}:\text{\:\,}\left( \mathcal{l},t \right) \in S_{e}^{L}.$$

Esta condición admite que el portador sea distinto en cada tiempo.

La persistencia de un portador concreto $\mathcal{l}_{0}$exige:

$$\mathsf{Persistencia}\left( e,\mathcal{l}_{0},T_{req} \right)\text{\:\,} \Longleftrightarrow \text{\:\,}\forall t \in T_{req}:\left( \mathcal{l}_{0},t \right) \in S_{e}^{L}.$$

Por tanto:

$$\forall t\text{\:\,}\exists\mathcal{l}$$

y:

$$\exists\mathcal{l}\text{\:\,}\forall t$$

expresan propiedades diferentes.

Si se pretende acreditar existencia efectiva mediante la primera consulta, se exige:

$$T_{req} \neq \varnothing.$$

El universal sobre tiempos vacíos sigue siendo lógicamente verdadero, pero no demuestra que haya existido un portador.

Estas consultas se incorporan como restricciones cuando la tarea las exige. Una comparación dimensional no introduce por sí sola una condición tácita de existencia, supervivencia o continuidad poblacional.

**5. Comparación con portadores y soportes comunes**

**Definición 6.5. Bloque conservador de comparación.**

Sea $\mathcal{B}_{W}$un conjunto de registros con:

-   el mismo ámbito comparativo y reloj;

-   los mismos portadores identificados en cada tiempo;

-   los mismos índices aplicables;

-   espacios de valores y calibraciones comunes.

Se fija un único conjunto de índices requeridos:

$$K \subseteq I^{W}.$$

Para cada registro del bloque se exige:

$$K \subseteq D_{e}^{W}.$$

La comparación es:

$$e_{A} \succeq_{K}e_{B}\text{\:\,} \Longleftrightarrow \text{\:\,}\forall i \in K:w_{e_{B}}(i) \preceq_{i}w_{e_{A}}(i).$$

Si se requiere el perfil dimensional completo:

$$K = I^{W}.$$

Si:

$$K \subsetneq I^{W},$$

el resultado corresponde al subperfil declarado. No se presenta como comparación completa de la historia.

**Teorema 6.2. Preorden de bienestar sobre un bloque común.**

La relación $\succeq_{K}$es reflexiva y transitiva.

**Demostración.**

Para cada $i \in K$, la reflexividad del espacio de valores da:

$$w_{e}(i) \preceq_{i}w_{e}(i).$$

Por tanto:

$$e \succeq_{K}e.$$

Si:

$$e_{A} \succeq_{K}e_{B},\ e_{B} \succeq_{K}e_{C},$$

entonces, para cada índice del mismo conjunto $K$:

$$w_{e_{C}}(i) \preceq_{i}w_{e_{B}}(i) \preceq_{i}w_{e_{A}}(i).$$

La transitividad de $\preceq_{i}$implica:

$$e_{A} \succeq_{K}e_{C}.$$

$$\square$$

La dominancia mutua define una equivalencia. Su cociente es un orden parcial, como en el Módulo I.

Para $K = \varnothing$, todos los registros del bloque resultan dimensionalmente equivalentes por vacuidad. Esto no acredita existencia ni una comparación sustantiva de dimensiones.

**Contraejemplo de uso incorrecto 6.1. Comparar únicamente lo observado en cada pareja.**

Consideremos tres índices aplicables comunes:

$$I^{W} = \left\{ 1,2,3 \right\},$$

con valores binarios ordenados por $0 < 1$:

  --------------------------------------------------------------------------
  **Registro**   **Índice 1**        **Índice 2**        **Índice 3**
  -------------- ------------------- ------------------- -------------------
  $$A$$          $$1$$               Sin medición        $$0$$

  $$B$$          $$0$$               $$1$$               Sin medición

  $$C$$          Sin medición        $$0$$               $$1$$
  --------------------------------------------------------------------------

Si cada pareja se compara solo en su intersección observada:

-   $A$supera a $B$por el índice $1$.

-   $B$supera a $C$por el índice $2$.

-   $C$supera a $A$por el índice $3$.

Se obtiene un ciclo porque se cambia de criterio entre comparaciones.

Este resultado no contradice el teorema anterior: la regla utilizada incumple su condición de mantener un único $K$dentro del bloque.

El módulo exige fijar ese conjunto previamente y comprobar su cobertura en todos los registros comparados. Una dimensión ausente no se elimina de manera diferente para cada pareja.

**6. La trayectoria completa y sus resúmenes**

**Ejemplo 6.1. Igual bienestar final, distinta historia.**

Consideremos un portador, una dimensión ordinal común y tres tiempos:

  ------------------------------------------------------------------------
  **Historia**             $$t = 0$$       $$t = 1$$       $$t = 2$$
  ------------------------ --------------- --------------- ---------------
  $$A$$                    $$2$$           $$0$$           $$2$$

  $$B$$                    $$2$$           $$2$$           $$2$$
  ------------------------------------------------------------------------

El valor final coincide:

$$w_{A}(2) = w_{B}(2).$$

Sin embargo, sobre la trayectoria completa:

$$B \succ A.$$

El estado final no conserva la información necesaria para distinguir el deterioro intermedio.

Una suma, una media o un descuento temporal también constituye una transformación del registro. Su utilización requiere declarar qué consulta representa y qué información conserva.

**Teorema 6.3. Suficiencia de un resumen de bienestar.**

Sea $\mathcal{H}_{W}$un conjunto de registros y:

$$\Psi:\mathcal{H}_{W} \longrightarrow Z$$

una representación total.

Sea $\mathcal{F}$una familia de consultas parciales sobre esos registros. Cada consulta $f\mathcal{\in F}$factoriza a través de $\Psi$, incluyendo su dominio, si y solo si:

$$\Psi(h) = \Psi\left( h^{'} \right) \Longrightarrow \widehat{f}(h) = \widehat{f}\left( h^{'} \right)\ \text{para~todo~}f\mathcal{\in F.}$$

Aquí $\widehat{f}$distingue el valor definido de la marca de indefinición.

**Demostración.**

Si $f = \overline{f} \circ \Psi$, dos registros con igual representación reciben el mismo estado de definición y, cuando corresponde, el mismo valor.

Recíprocamente, la condición permite definir:

$$\overline{f}\left( \Psi(h) \right) = f(h)$$

en:

$$D_{\overline{f}} = \Psi\left( D_{f} \right).$$

La igualdad de valores y la saturación del dominio en cada fibra garantizan que la definición sea independiente del representante. $\square$

Una representación suficiente para una consulta concreta puede ser insuficiente para reconstruir todo el registro.

La procedencia se conserva además por separado. Igual contenido de bienestar no convierte dos ejecuciones en una misma ejecución ni permite intercambiar sus testigos causales.

**7. Comparación entre poblaciones mediante trayectorias personales**

Cuando cambian las identidades de los portadores, el producto anterior necesita una regla de correspondencia.

Una posibilidad es el anonimato de trayectorias completas.

**Definición 6.6. Perfil personal común.**

Consideremos poblaciones finitas de igual tamaño, con:

-   un reloj común;

-   soportes temporales personales homogéneos;

-   los mismos índices personales $\left( t,j \right)$;

-   mediciones completas y calibradas.

Cada portador tiene un perfil:

$$p_{\mathcal{l}} = \left( w\left( \mathcal{l},t,j \right) \right)_{\left( t,j \right) \in K_{P}},$$

perteneciente a un mismo preorden producto:

$$\left( P, \preceq_{P} \right).$$

La homogeneidad exigida aquí no permite comparar automáticamente duraciones vitales distintas.

**Definición 6.7. Dominancia anónima.**

Para poblaciones $A$y $B$:

$$A \succeq_{an}B\text{\:\,} \Longleftrightarrow \text{\:\,}\exists f:L_{B}L_{A}\ \forall\mathcal{l} \in L_{B}:p_{\mathcal{l}}^{B} \preceq_{P}p_{f\left( \mathcal{l} \right)}^{A}.$$

Se busca una biyección que asigne a cada trayectoria de $B$una trayectoria de $A$que no la empeore.

**La misma biyección debe mantenerse en todos los tiempos y dimensiones.**

El anonimato es una regla normativa explícita: permite que las etiquetas personales se permuten para esta comparación. No se activa automáticamente por disponer de perfiles numéricos.

**Teorema 6.4. Preorden de dominancia anónima.**

La relación $\succeq_{an}$es un preorden.

**Demostración.**

La identidad de $L_{A}$es una biyección y:

$$p_{\mathcal{l}}^{A} \preceq_{P}p_{\mathcal{l}}^{A}.$$

Esto prueba reflexividad.

Supongamos que $f:L_{B} \rightarrow L_{A}$acredita $A \succeq_{an}B$y que $g:L_{C} \rightarrow L_{B}$acredita $B \succeq_{an}C$.

La composición:

$$f \circ g:L_{C} \longrightarrow L_{A}$$

es una biyección. Para cada $\mathcal{l} \in L_{C}$:

$$p_{\mathcal{l}}^{C} \preceq_{P}p_{g\left( \mathcal{l} \right)}^{B} \preceq_{P}p_{f\left( g\left( \mathcal{l} \right) \right)}^{A}.$$

La transitividad personal prueba:

$$A \succeq_{an}C.$$

$$\square$$

Renombrar los portadores y transportar sus perfiles conserva la relación: la biyección testigo se transporta mediante los mismos renombramientos.

**Correspondencias restringidas.**

Si solo se admiten ciertas biyecciones, basta para la prueba anterior que:

1.  estén autorizadas las identidades;

2.  la composición de dos biyecciones autorizadas vuelva a estar autorizada.

Estas son condiciones suficientes. Deben comprobarse para el bloque.

Para conservar además el anonimato, las restricciones deben respetar los renombramientos permitidos. La sola clausura por composición acredita el preorden, pero no esa invariancia adicional.

**Contraejemplo de uso incorrecto 6.2. Cambiar el emparejamiento en cada instante.**

Consideremos dos poblaciones, una dimensión binaria y dos tiempos:

  ------------------------------------------------------------------------
  **Población**            **Portador**          $$t = 0$$    $$t = 1$$
  ------------------------ --------------------- ------------ ------------
  $$A$$                    $$a_{1}$$             $$1$$        $$0$$

  $$A$$                    $$a_{2}$$             $$0$$        $$1$$

  $$B$$                    $$b_{1}$$             $$1$$        $$1$$

  $$B$$                    $$b_{2}$$             $$0$$        $$0$$
  ------------------------------------------------------------------------

En cada instante, ambas poblaciones presentan la misma distribución:

$$\left\{ 0,1 \right\}.$$

Sin embargo, sus trayectorias personales son:

$${A = \left\{ \left( 1,0 \right),\left( 0,1 \right) \right\},
}{B = \left\{ \left( 1,1 \right),\left( 0,0 \right) \right\}.}$$

No se cumple:

$$A \succeq_{an}B,$$

porque ninguna trayectoria de $A$domina a $\left( 1,1 \right)$.

Tampoco se cumple:

$$B \succeq_{an}A,$$

porque ambas trayectorias de $A$necesitarían asignarse a la única trayectoria $\left( 1,1 \right)$de $B$.

Son incomparables bajo la regla de trayectorias completas.

Emparejar nuevamente a los portadores en cada instante corresponde a otra regla temporal. El uso incorrecto consiste en atribuir ese resultado a una regla que exige una única correspondencia para toda la historia.

**8. Un procedimiento finito con certificados verificables**

**Definición 6.8. Grafo de correspondencias que no empeoran.**

Para decidir si $A \succeq_{an}B$, construimos un grafo bipartito:

-   lado izquierdo: $L_{B}$;

-   lado derecho: $L_{A}$.

Existe una arista $\left( b,a \right)$exactamente cuando:

$$p_{b}^{B} \preceq_{P}p_{a}^{A}.$$

Si la regla incluye restricciones locales de correspondencia, la arista también debe estar autorizada por ellas.

Este procedimiento se aplica cuando las biyecciones permitidas son exactamente las que respetan esas aristas.

**Teorema 6.5. Caracterización por emparejamiento perfecto.**

La comparación se cumple si y solo si el grafo contiene un emparejamiento perfecto.

**Demostración.**

Una biyección que no empeora utiliza una arista por cada portador, sin repetir extremos, y cubre ambos lados. Es un emparejamiento perfecto.

Recíprocamente, un emparejamiento perfecto define esa biyección y todas sus parejas satisfacen el no empeoramiento. $\square$

La decisión finita puede construirse mediante caminos aumentantes.

Se comienza con un emparejamiento $M$. Desde los vértices izquierdos libres se recorren alternadamente:

-   aristas que no pertenecen a $M$, hacia la derecha;

-   aristas de $M$, de vuelta a la izquierda.

Si se alcanza un vértice derecho libre, invertir las aristas del camino aumenta el tamaño del emparejamiento exactamente en uno.

Con poblaciones de tamaño $n$, puede haber como máximo $n$aumentos.

**Certificado positivo.**

Un emparejamiento perfecto proporciona directamente la biyección. Se comprueba que:

-   utiliza únicamente aristas del grafo;

-   no repite extremos;

-   cubre todos los portadores.

**Certificado negativo.**

Supongamos que el emparejamiento no es perfecto y una búsqueda exhaustiva no alcanza ningún vértice derecho libre.

Sea $R$el conjunto no vacío de raíces izquierdas libres y $X$el conjunto de vértices izquierdos alcanzados.

Su conjunto de vecinos $N(X)$satisface:

$$\mid N(X) \mid = \mid X \mid - \mid R \mid < \mid X \mid .$$

En efecto, todos los vecinos alcanzados están emparejados, y sus compañeros son exactamente los vértices de $X \smallsetminus R$.

Una biyección necesitaría asignar vecinos distintos a todos los miembros de $X$, pero hay menos vecinos que miembros. Por tanto, no existe un emparejamiento perfecto.

Este déficit es una prueba verificable de imposibilidad.

El certificado debe comprobarse sobre el **grafo completo** determinado por los perfiles y la regla. Una comparación dimensional indefinida no puede tratarse como falsa para borrar una arista.

**9. Cambios de población, duración o dimensiones**

La regla anterior tiene un dominio específico. Cuando cambia el número de portadores, sus duraciones vitales, el reloj o las dimensiones, se necesita una regla que describa esas diferencias.

**Definición 6.9. Regla poblacional general.**

Una regla poblacional se representa mediante:

$$\mathcal{R}_{L} = \left( \mathsf{H}_{W}^{L},D_{L},\mathsf{Corr}_{L}, \succeq_{L},\mathsf{Just}_{L} \right).$$

Sus componentes son:

  ----------------------------------------------------------------------------------------------------------
  **Componente**           **Función**
  ------------------------ ---------------------------------------------------------------------------------
  $$\mathsf{H}_{W}^{L}$$   Historias enriquecidas que la regla contempla.

  $$D_{L}$$                Pares de historias donde autoriza una comparación.

  $$\mathsf{Corr}_{L}$$    Correspondencias entre portadores y registro de quienes carecen de contraparte.

  $$\succeq_{L}$$          Relación de comparación dentro del dominio.

  $$\mathsf{Just}_{L}$$    Regla normativa, temporal y de frontera que fundamenta la comparación.
  ----------------------------------------------------------------------------------------------------------

El dominio es simétrico:

$$\left( A,B \right) \in D_{L}\text{\:\,} \Longleftrightarrow \text{\:\,}\left( B,A \right) \in D_{L}.$$

Esto permite consultar ambos sentidos, pero no exige que las respuestas coincidan.

Las correspondencias no tienen que ser biyecciones. Para una relación:

$$C \subseteq L_{B} \times L_{A},$$

se conservan exactamente los portadores sin contraparte:

$${U_{B} = L_{B} \smallsetminus {pr}_{1}(C),
}{U_{A} = L_{A} \smallsetminus {pr}_{2}(C).}$$

Una correspondencia vacía puede estar perfectamente definida: registra a todos los portadores como no emparejados. Es distinta de no haber aportado ninguna correspondencia.

La regla especifica cómo trata esas situaciones. Los nacimientos, las muertes y las diferencias de duración no desaparecen por omitirlos de una tabla de valores.

**10. Certificación del orden poblacional**

**Teorema 6.6. Criterio de preorden sobre un bloque finito.**

Sea $\mathcal{B}_{L}$un bloque con:

$$\mathcal{B}_{L}^{2} \subseteq D_{L}.$$

Supongamos que están determinados todos los valores de la relación en ese bloque.

Definamos:

$$\Downarrow A = \left\{ C \in \mathcal{B}_{L}:A \succeq_{L}C \right\}.$$

La relación es un preorden si y solo si:

$$A \succeq_{L}A\ \text{para~todo~}A \in \mathcal{B}_{L},$$

y:

$$A \succeq_{L}B \Longrightarrow \Downarrow B \subseteq \Downarrow A.$$

**Demostración.**

La primera condición es reflexividad.

Si la segunda se cumple y:

$$A \succeq_{L}B,\ B \succeq_{L}C,$$

entonces $C \in \Downarrow B$, por lo que $C \in \Downarrow A$. Así:

$$A \succeq_{L}C.$$

Recíprocamente, la transitividad implica precisamente esa inclusión de conjuntos. $\square$

La certificación se obtiene examinando la relación definida por la regla. No basta una declaración que la denomine «preorden».

Un dominio simétrico tampoco asegura transitividad: autorizar la consulta de ambos sentidos no impone ninguna ley sobre sus respuestas.

**11. Qué determina la matemática y qué especifica la regla normativa**

**Proposición 6.7. Los perfiles descriptivos y las leyes de preorden no determinan una única comparación poblacional.**

Consideremos dos historias:

-   $A$: un portador;

-   $B$: dos portadores.

Todos tienen el mismo perfil individual medido.

Sobre el conjunto $\left\{ A,B \right\}$, definamos:

$$\Delta = \left\{ \left( A,A \right),\left( B,B \right) \right\}.$$

Las tres relaciones siguientes son preórdenes:

$${R_{1} = \Delta \cup \left\{ \left( A,B \right) \right\},
}{R_{2} = \Delta \cup \left\{ \left( B,A \right) \right\},
}{R_{3} = \Delta.}$$

La primera prefiere $A$, la segunda prefiere $B$y la tercera los deja incomparables.

**Demostración.**

Las tres contienen las diagonales. Ninguna contiene una cadena de relaciones cuya composición exija agregar un par ausente. Por tanto, son reflexivas y transitivas. $\square$

Los mismos datos descriptivos admiten varias relaciones formalmente coherentes. Elegir una exige una regla normativa adicional.

Esto explica el papel de $\mathsf{Just}_{L}$: especifica qué comparación se está haciendo y cómo se fundamenta. La matemática permite verificar sus dominios, consecuencias y estructura de orden.

Una regla universal de compensación entre vidas no se deduce de las mediciones ni de las inclusiones entre soportes.

**12. Integración con las políticas y los demás módulos**

El bienestar se registra por ejecución, conservando su identidad completa:

$$RunKey(e).$$

Para una política fija, se mantiene la familia de registros de todas sus realizaciones pertinentes:

$$\mathcal{W}_{\pi} = \left( RunKey,(e)\widetilde{W}(e) \right)_{e \in \mathfrak{F}_{H,\gamma}^{poss}\left( c_{0},\pi \right)}.$$

La cobertura de esa familia procede del modelo causal. Un registro de otra política o de otra rama no sustituye a uno requerido.

Si una realización carece de una medición, permanece en la familia con esa ausencia. Si falta su registro entero, se conserva el diagnóstico de cobertura. Ninguna de las dos situaciones autoriza a eliminar la realización.

La integración conserva las siguientes obligaciones:

-   **Módulo 0:** un resumen de bienestar solo sustituye al registro para las consultas cuya suficiencia se haya demostrado.

-   **Módulo I:** cada dimensión mantiene su significado y calibración dentro del bloque.

-   **Módulo II:** los portadores compartidos entre escalas conservan su identidad y no se duplican.

-   **Módulo III:** los logros generativos y las afirmaciones de bienestar que se presentan conjuntamente deben conservar la misma política y los testigos pertinentes.

-   **Módulos V--VII:** las reglas sobre futuros, viabilidad y selección reciben estos registros con sus dominios y soportes completos.

Una mayor capacidad generativa no implica automáticamente mayor bienestar. El Módulo IV aporta el objeto y las condiciones necesarios para comprobar esa segunda afirmación.

**La siguiente entrega es el Módulo V: modelo causal, contexto, políticas y futuros posibles.**

**Entrega 7 --- Módulo V: modelo causal, contexto, políticas y futuros posibles**

El Módulo V construye el conjunto de ejecuciones sobre el que trabajan los demás módulos.

Su pregunta central es:

$$\boxed{\text{¿Qu}\overset{ˊ}{\text{e}}\text{~puede~suceder~desde~esta~inicializaci}\overset{ˊ}{\text{o}}\text{n,~bajo~esta~pol}\overset{ˊ}{\text{ı}}\text{tica~y~en~este~contexto?}}$$

La respuesta debe conservar todas las realizaciones comprendidas en el experimento. Su construcción precede a la evaluación del CAG, el bienestar, la viabilidad y las probabilidades.

Una realización desfavorable o todavía no evaluable continúa siendo parte del modelo causal.

**1. Modelo, contexto e inicialización**

**Definición 7.1. Identidad del experimento.**

Distinguimos los siguientes objetos:

  -------------------------------------------------------------------------------
  **Símbolo**        **Significado**
  ------------------ ------------------------------------------------------------
  $$\mathfrak{M}$$   Marco de representación.

  $$\beta$$          Modelo: estructura causal y parámetros declarados.

  $$\gamma$$         Contexto efectivo del experimento.

  $$\delta$$         Intervención inicial concreta, cuando corresponde.

  $$c_{0}$$          Condición inicial realizada.

  $$\pi$$            Política de actuación.

  $$H$$              Horizonte del experimento.
  -------------------------------------------------------------------------------

El contexto identifica su modelo de base:

$$Base(\gamma) = \beta.$$

El horizonte pertenece al experimento. Cambiar $H$no equivale, por sí solo, a cambiar el modelo $\beta$.

La clave del experimento es:

$$\kappa = \left( \mathfrak{M},\beta,\gamma,c_{0},\pi,H \right).$$

Estas posiciones permanecen separadas. Una intervención no es una condición inicial, y una condición inicial no contiene la política ni sus resultados futuros.

**Definición 7.2. Realización inicial.**

Se declara una relación:

$$RealC0_{\beta} \subseteq \mathcal{I}_{\beta}^{0} \times C_{0,\beta},$$

donde $\mathcal{I}_{\beta}^{0}$es el espacio de intervenciones iniciales y $C_{0,\beta}$el de condiciones iniciales.

La expresión:

$$RealC0_{\beta}\left( \delta,c_{0} \right)$$

afirma que la intervención $\delta$realiza la condición $c_{0}$en el modelo declarado.

No se presupone que esta relación sea una función ni que cada condición inicial tenga una única intervención de origen.

La inicialización del proceso proporciona:

$$Init_{\gamma}\left( c_{0} \right) = \left( x_{0},\iota_{0} \right),$$

con estado causal $x_{0}$e información legítima inicial $\iota_{0}$.

**2. Dos modos de contexto**

El protocolo distingue:

$$Mode(\gamma) \in \left\{ pre,fix \right\}.$$

**Modo** $pre$**.**

La condición inicial y el contexto se fijan antes de comparar las políticas:

$$c_{0}^{\pi} = c_{0},\ \gamma^{\pi} = \gamma\ \text{para~toda~}\pi \in \Pi.$$

La política produce un régimen de actuación dentro de ese contexto. No redefine retrospectivamente la inicialización.

**Modo** $fix$**.**

Se fija una intervención concreta $\delta$, para la cual se exige:

$$RealC0_{\beta}\left( \delta,c_{0} \right),$$

y:

$$Ctx_{\beta}^{fix}(\delta) = \gamma.$$

Si se trabaja entre marcos, esa misma intervención debe corresponder fielmente a la intervención común declarada.

**Contraejemplo de uso incorrecto 7.1. Sustituir la intervención por otra con igual estado inicial.**

Dos intervenciones pueden producir el mismo $x_{0}$y modificar de manera distinta el mecanismo posterior.

Por ejemplo, ambas pueden dejar inicialmente lleno un depósito, pero una puede mantener operativa su alimentación y otra desconectarla.

La igualdad del estado inicial descrito no permite sustituir una intervención por otra sin comprobar el contexto y la suficiencia del estado.

La condición que excluye esa sustitución es conservar la intervención concreta, su realización inicial y el contexto que produce.

**3. Suficiencia de la condición inicial**

**Definición 7.3. Certificado basal suficiente.**

Sea $\mathcal{H}_{0}$un conjunto declarado de historias iniciales. Consideremos mapas definidos sobre todas esas historias:

$${b:\mathcal{H}_{0} \longrightarrow C_{0},
}{s:\mathcal{H}_{0} \longrightarrow X,
}{i:\mathcal{H}_{0} \longrightarrow I.}$$

Para la condición seleccionada $c_{0}$, exigimos:

$$b^{- 1}\left( c_{0} \right) \neq \varnothing,$$

y:

$$\forall h \in b^{- 1}\left( c_{0} \right):\ s(h) = x_{0},\ i(h) = \iota_{0}.$$

Todos los miembros de esa fibra determinan el mismo estado causal y la misma información inicial.

**Teorema 7.1. Suficiencia basal por determinación del estado y la información.**

Supongamos que:

1.  $x_{0}$es un estado causal suficiente en el sentido del Módulo 0;

2.  la información y su actualización conservan la memoria pertinente del controlador;

3.  el contexto, el proceso y la política son los mismos;

4.  se cumplen las condiciones de la fibra anterior.

Entonces todas las historias de esa fibra tienen el mismo conjunto de continuaciones compatibles ante las mismas entradas futuras.

**Demostración.**

Las historias comienzan con el mismo par:

$$\left( x_{0},\iota_{0} \right).$$

La política consulta la misma información y elige la misma acción. La suficiencia causal determina la misma relación de sucesores ante las mismas entradas.

Para cada resultado correspondiente, la actualización informacional produce la información sucesora correspondiente.

Repitiendo el argumento por inducción se obtienen los mismos conjuntos de continuaciones finitas. $\square$

El resultado conserva una **relación de continuaciones**. No establece una única realización salvo que también se haya probado determinismo.

Este certificado es una condición suficiente fuerte. Una representación más reducida puede ser suficiente, pero debe demostrarlo mediante las condiciones de factorización y continuación del Módulo 0.

**4. Estado causal e información del controlador**

**Definición 7.4. Política informacional.**

El proceso distingue:

$$x_{t} \in X,\ \iota_{t} \in I.$$

Una política permitida tiene la forma:

$$\pi_{t}:I \rightharpoonup A,$$

y selecciona:

$$a_{t} = \pi_{t}\left( \iota_{t} \right).$$

La familia de políticas:

$$\Pi$$

se declara antes de evaluar resultados.

La información $\iota_{t}$debe proceder de la inicialización legítima y de la historia observada hasta ese momento. Llamar «información» a una variable no acredita que el controlador pueda conocerla.

**Proposición 7.2. Consistencia de decisión bajo información indistinguible.**

Si dos ocurrencias tienen el mismo tiempo y la misma información:

$$\iota_{t} = \iota_{t}^{'},$$

entonces una política funcional definida en ese argumento elige la misma acción:

$$\pi_{t}\left( \iota_{t} \right) = \pi_{t}\left( \iota_{t}^{'} \right).$$

**Demostración.**

Ambas consultas tienen exactamente el mismo argumento de una misma función. $\square$

Una política puede adaptarse a observaciones nuevas. Lo que no puede hacer es distinguir dos ramas utilizando información que no recibe.

La memoria necesaria para esa adaptación debe estar representada en $\iota_{t}$y en su regla de actualización.

**5. Relación causal y actualización informacional**

**Definición 7.5. Resultados causales de una acción.**

Para un tiempo, estado y acción se declara una fila causal finita:

$$B_{\gamma}\left( t,x,a \right).$$

Cada resultado tiene la forma:

$$\left( \lambda,u,x^{'},y^{'} \right),$$

donde:

-   $\lambda$identifica la rama dentro de la fila;

-   $u$registra la entrada o resultado exógeno declarado;

-   $x^{'}$es el estado sucesor;

-   $y^{'}$es la observación producida.

Las etiquetas $\lambda$son únicas dentro de cada fila.

La información se actualiza mediante:

$$U_{\gamma}\left( t,\iota,a,y^{'} \right) = \iota^{'}.$$

La transición de una ejecución conserva, por tanto:

$$\left( x,\iota \right) \longrightarrow \left( x^{'},\iota^{'} \right),$$

junto con la acción, entrada, observación y etiqueta de rama.

Dos resultados pueden compartir entrada, observación e incluso estado sucesor sin convertirse por ello en una misma ocurrencia.

**Ejecutabilidad y admisibilidad.**

El modelo declara por separado:

$$A_{exec}\left( t,x \right),$$

las acciones físicamente ejecutables, y:

$$A_{adm}\left( t,x \right),$$

las acciones admitidas por las reglas locales del ámbito.

Para certificar una política como admitida, su acción efectiva debe satisfacer ambas condiciones.

Una acción localmente inadmisible no queda demostrada como físicamente imposible. Del mismo modo, una acción localmente admisible puede tener sucesores que incumplan un requisito global de seguridad.

Esos sucesores permanecen en el árbol causal.

**6. Ejecuciones y escenarios**

**Definición 7.6. Ejecución identificada.**

Una ejecución conserva la secuencia completa de estados, información, acciones, observaciones, entradas y ramas.

Su identidad es:

$$RunKey(e) = \left( \kappa,\left( \lambda_{0},\ldots,\lambda_{T_{e} - 1} \right) \right).$$

La clave del experimento evita confundir ramas pertenecientes a políticas, contextos o inicializaciones diferentes.

Repetir un estado físico tampoco repite una ocurrencia: el tiempo y el prefijo recorrido siguen formando parte de la ejecución.

**Definición 7.7. Realizaciones de un escenario.**

La secuencia de entradas declaradas determina el escenario de una ejecución:

$$\xi(e) = \left( u_{0},\ldots,u_{T_{e} - 1} \right).$$

Se mantiene:

$$Runs_{H,\gamma}\left( c_{0};\pi;\xi \right)$$

como un conjunto de realizaciones.

El conjunto de futuros posibles es:

$$\mathfrak{F}_{H,\gamma}^{poss}\left( c_{0},\pi \right) = \bigcup_{\xi \in \Xi_{H,\gamma}\left( c_{0},\pi \right)}^{}Runs_{H,\gamma}\left( c_{0};\pi;\xi \right).$$

Un escenario puede contener varias ejecuciones:

$$\left. \mid Runs_{H,\gamma}\left( c_{0};\pi;\xi \right) \right.\mid > 1.$$

La unicidad debe demostrarse cuando una construcción la necesite. No se obtiene escribiendo $Run$como si fuera una función.

En la presentación finita, los escenarios pueden obtenerse agrupando todas las hojas por su secuencia de entradas. Así, cada escenario enumerado tiene una fibra no vacía y conserva todas sus realizaciones.

**7. Construcción del árbol causal finito**

Fijemos:

$$H\mathbb{\in N.}$$

**Definición 7.8. Árbol del experimento.**

La construcción comienza con la raíz:

$$\left( 0,x_{0},\iota_{0} \right).$$

En un nodo de tiempo $t$:

1.  Si $t = H$, se registra una hoja por horizonte.

2.  Si $t < H$y existe una terminación causal explícita, se registra una hoja por terminación.

3.  En otro caso, se consulta la política.

4.  Se comprueban ejecutabilidad y admisibilidad local.

5.  Se incorpora cada resultado de la fila causal.

6.  Se aplica la actualización informacional a cada resultado.

Para certificar el árbol completo, cada nodo que deba continuar necesita:

-   una decisión definida;

-   una acción ejecutable y admitida;

-   una fila causal presente y no vacía;

-   una actualización informacional definida para cada resultado.

Con $H = 0$, la raíz ya es una hoja. No se requiere una acción.

**Teorema 7.3. Corrección, cobertura y finitud.**

Bajo esas condiciones, el árbol contiene exactamente todos los prefijos causales del experimento y sus hojas son exactamente las realizaciones completas por horizonte o terminación.

Además, el árbol es finito.

**Demostración.**

**Corrección.** La raíz corresponde a la inicialización realizada.

Si un nodo es un prefijo válido, su acción es la indicada por la política. Cada hijo pertenece a la fila causal declarada y recibe la información correspondiente mediante $U_{\gamma}$.

Por inducción sobre la profundidad, todos los nodos generados son prefijos válidos.

**Cobertura.** Consideremos un prefijo válido de longitud $t + 1$.

Su padre, de longitud $t$, aparece por hipótesis inductiva. La construcción incorpora todos los resultados de su fila, incluido el que produce ese prefijo.

Por tanto, también aparece el prefijo de longitud $t + 1$.

La regla de parada coincide exactamente con horizonte o terminación causal. Esto identifica las hojas completas.

**Finitud.** El nivel inicial contiene un nodo. Cada nivel siguiente es una unión finita de filas finitas. Hay como máximo $H + 1$niveles.

Por tanto, el árbol es finito. $\square$

La prueba permite verificar la cobertura desde las filas causales. Una etiqueta que diga «árbol completo» o una topología aparentemente válida no sustituye esa comprobación.

Eliminar un hijo y todos sus descendientes puede dejar una topología coherente, pero cambia el experimento.

**8. Errores, bloqueos y terminación**

Una acción ausente, una acción inexecutable, una exclusión normativa, una fila faltante y una actualización informacional ausente son diagnósticos diferentes.

Ninguno se transforma automáticamente en terminación causal.

Por ejemplo, si se conoce un resultado físico:

$$\left( \lambda,u,x^{'},y^{'} \right),$$

pero no está definida:

$$U_{\gamma}\left( t,\iota,a,y^{'} \right),$$

se conserva la rama física conocida y se registra la ausencia de información sucesora.

No se inventa $\iota^{'}$. Por ello, sus descendientes pueden quedar sin construir: la política siguiente necesita un argumento todavía no disponible.

La evidencia resultante es un árbol parcial diagnosticado. No se certifica como el conjunto completo de futuros.

También se distingue entre:

-   que una política incumpla la admisibilidad local;

-   que una realización de una política admitida incumpla una restricción global.

El segundo caso no autoriza a borrar la realización.

**Contraejemplo de uso incorrecto 7.2. Convertir una rama desfavorable en inexistente.**

Supongamos que una acción admitida tiene dos sucesores:

$$x_{seguro},\ x_{inseguro}.$$

Eliminar el segundo y concluir que la acción garantiza seguridad cambia la relación causal sobre la que se cuantifica.

El módulo excluye esa operación: primero conserva ambos resultados; después la evaluación determina sus propiedades.

**9. Consultas, realizaciones completas y completaciones**

**Definición 7.9. Extensión de prefijos.**

Sea:

$$Q_{\kappa}^{exec}$$

el conjunto de todos los prefijos del árbol, incluidas sus hojas, y sea:

$$F_{\kappa}$$

el conjunto de hojas completas.

Escribimos:

$$h \sqsubseteq u$$

cuando $u$extiende a $h$. La relación es reflexiva: una ejecución se extiende a sí misma.

Las completaciones de una consulta son:

$$L(h) = \left\{ u \in F_{\kappa}:h \sqsubseteq u \right\}.$$

**Teorema 7.4. Existencia de completaciones.**

En el árbol finito certificado:

$$\forall h \in Q_{\kappa}^{exec},\ L(h) \neq \varnothing.$$

Por tanto:

$$Q_{\kappa}^{exec} = Pref\left( F_{\kappa} \right).$$

**Demostración.**

Procedemos por inducción sobre el tiempo restante $H - t$.

Si el nodo está en el horizonte o tiene terminación causal, es una hoja y se completa a sí mismo.

En otro caso, tiene una fila no vacía. Cualquiera de sus hijos posee una completación por hipótesis inductiva. Esa hoja también completa al nodo padre. $\square$

La finitud y la existencia de completaciones son resultados distintos. Un árbol finito con un bloqueo no justificado no satisface automáticamente el segundo.

**Aceptación adicional.**

Supongamos que se declara:

$$F^{'} \subseteq F_{\kappa}.$$

El árbol original y sus consultas permanecen conservados.

**Proposición 7.5. Cobertura de todas las consultas por hojas aceptadas.**

Se cumple:

$$\forall h \in Q_{\kappa}^{exec}\text{\:\,}\exists u \in F^{'}:h \sqsubseteq u$$

si y solo si:

$$F^{'} = F_{\kappa}.$$

**Demostración.**

Si se aceptan todas las hojas, se aplica el teorema anterior.

Si se omite una hoja $\mathcal{l}$, esa hoja sigue siendo una consulta. Como no se extiende a otra hoja del mismo árbol, carece de completación en $F^{'}$. $\square$

Esta propiedad se refiere a todas las consultas del árbol finito. Para lenguajes infinitos, las condiciones de aceptación y extensión deben declararse y comprobarse en su propio ámbito.

**10. Un ejemplo de información parcial y dinámica multivaluada**

Consideremos horizonte $H = 2$.

En $t = 0$existe una única raíz:

$$\left( r,\iota_{0} \right),$$

con una acción inicial fijada.

Esa acción admite dos resultados en $t = 1$:

$$L,\ R,$$

que comparten la misma entrada y observación. Como proceden de la misma información previa y la misma acción, ambos producen:

$$\iota_{1}.$$

En $t = 1$pueden ejecutarse las acciones $a$y $b$:

  ------------------------------------------------------------------------
  **Estado oculto**               **Acción** $a$      **Acción** $b$
  ------------------------------- ------------------- --------------------
  $$L$$                           $$g$$               $$u$$

  $$R$$                           $$u$$               $$g$$
  ------------------------------------------------------------------------

El objetivo es alcanzar $g$.

Desde cada estado oculto existe una acción que lo alcanza. Sin embargo, la política consulta:

$$\pi_{1}\left( \iota_{1} \right),$$

con el mismo argumento en ambas ramas.

Si elige $a$, una realización termina en $u$. Si elige $b$, también.

Por tanto, dentro de esa familia de políticas:

$$\neg\exists\pi\text{\:\,}\forall e \in \mathfrak{F}_{2,\gamma}^{poss}\left( c_{0},\pi \right):x_{2}(e) = g.$$

**Contraejemplo de uso incorrecto 7.3. Controlar mediante el estado oculto.**

Elegir $a$en $L$y $b$en $R$atribuiría al controlador una distinción que su información no contiene.

La condición que excluye esa política es:

$$a_{t} = \pi_{t}\left( \iota_{t} \right).$$

El ejemplo también muestra que compartir entradas y observaciones no garantiza una única ejecución. Las dos ramas deben conservarse.

**11. Régimen efectivo y fidelidad entre marcos**

**Definición 7.10. Régimen de una política.**

La política induce un régimen:

$$\rho_{\gamma}\lbrack\pi\rbrack.$$

Este registro identifica las reglas efectivamente utilizadas y las entradas o efectos pertinentes de todas sus ramas.

Se construye antes de evaluar viabilidad. No se obtiene seleccionando los efectos que produzcan un resultado favorable.

Para comparar el régimen entre un marco común y uno local, se declara una relación:

$$R^{reg} \subseteq \mathcal{E}_{c}^{reg} \times \mathcal{E}_{\mathcal{l}}^{reg}.$$

Sus condiciones son:

1.  los extremos pertenecen a sus espacios declarados;

2.  cada entrada común tiene una fibra local no vacía;

3.  cada entrada local pertinente tiene una contraparte común;

4.  los significados están definidos y son fieles en toda la fibra.

Para una entrada común $a$:

$$R^{reg}(a) = \left\{ b:\left( a,b \right) \in R^{reg} \right\},$$

y se exige:

$$J_{c}(a) = \bigcup_{b \in R^{reg}(a)}^{}J_{\mathcal{l}}(b),$$

con significados definidos y no vacíos.

Estas referencias se fijan independientemente del CAG, del bienestar y del veredicto de la tarea.

Un régimen nulo puede tener ambos espacios de entradas vacíos. La ausencia de una tabla no demuestra que el régimen sea nulo.

La fidelidad del régimen tampoco convierte efectos alternativos en efectos simultáneos. Sus ramas y agrupaciones permanecen identificadas.

Para sustituir un proceso por otro hace falta además una correspondencia causal como la siguiente.

**12. Reducción causal con información y políticas**

**Definición 7.11. Mapas de reducción.**

Consideremos dos procesos $A$y $B$, con acciones comunes y el mismo horizonte.

Se declaran mapas de:

$${\Psi:X_{A} \longrightarrow X_{B},
}{R_{t}:I_{A} \longrightarrow I_{B},
}{O_{t}:Y_{A} \longrightarrow Y_{B},
}{\eta:\mathcal{U}_{A} \longrightarrow \mathcal{U}_{B}.}$$

Representan, respectivamente, estado, información, observaciones e inputs.

Si son parciales, deben estar definidos en todos los argumentos requeridos.

Las políticas emparejadas deben pertenecer realmente a sus familias permitidas y satisfacer:

$$\pi_{B}\left( t,R_{t}(\iota) \right) = \pi_{A}\left( t,\iota \right).$$

Las inicializaciones deben corresponder:

$$\Psi\left( x_{A,0} \right) = x_{B,0},\ R_{0}\left( \iota_{A,0} \right) = \iota_{B,0}.$$

También se conservan los dominios de acciones y la terminación pertinente.

**Igualdad de resultados conjuntos.**

Al omitir las etiquetas de ocurrencia, se exige:

$$\begin{aligned}
 & \left\{ \left( \eta,(u),\Psi\left( x^{'} \right)O_{t}\left( y^{'} \right) \right):\left( \lambda,u,x^{'},y^{'} \right) \in B_{A}\left( t,x,a \right) \right\} \\
 & \  = \left\{ \left( u_{B},x_{B}^{'},y_{B}^{'} \right):\left( \lambda_{B},u_{B},x_{B}^{'},y_{B}^{'} \right) \in B_{B}\left( t,\Psi,(x)a \right) \right\}.
\end{aligned}$$

La igualdad es conjunta: conserva las asociaciones entre input, estado sucesor y observación.

No basta igualar sus tres proyecciones por separado.

La información debe conmutar:

$$R_{t + 1}\text{ }\left( U_{A}\left( t,\iota,a,y^{'} \right) \right) = U_{B}\text{ }\left( t,R_{t},(\iota),aO_{t}\left( y^{'} \right) \right),$$

con los dominios correspondientes comprobados.

**Teorema 7.6. Exactitud de las trazas proyectadas.**

Si estas condiciones se verifican desde cada representante alcanzado bajo la pareja de políticas, los dos procesos tienen exactamente los mismos conjuntos de trazas proyectadas dentro del experimento declarado.

**Demostración.**

La raíz corresponde por las condiciones iniciales.

Cada rama nativa produce una rama reducida mediante la igualdad conjunta. La conmutación informacional y la igualdad de acciones mantienen la correspondencia en el siguiente paso.

Para la dirección inversa, cada rama reducida tiene un resultado nativo correspondiente desde el representante actualmente alcanzado.

Esto permite continuar el levantamiento paso a paso. La conservación del horizonte y la terminación hace coincidir las condiciones de finalización. $\square$

No se permite cambiar a otro representante de la fibra para obtener una continuación conveniente.

Como se han omitido etiquetas, la conclusión no es una biyección entre ejecuciones identificadas. Puede haber varias ocurrencias con la misma traza proyectada.

Tampoco se obtiene igualdad de probabilidades. Esa afirmación necesita conservar las leyes y agregar correctamente las masas de las fibras.

**Cobertura de políticas.**

Certificar una pareja de políticas solo acredita esa pareja.

Para comparar familias se exige cobertura explícita: por ejemplo, que toda política del proceso reducido tenga una política correspondiente admitida en el proceso original.

Las consecuencias sobre CAG y bienestar requieren además preservar los observables y las reglas de sus respectivos módulos.

**13. Monitor de violaciones de trayectoria**

**Definición 7.12. Registro externo de violación.**

Sea $K_{t} \subseteq X$una región requerida en cada tiempo, con pertenencia definida.

Construimos:

$${m_{0} = 1\left\lbrack x_{0} \notin K_{0} \right\rbrack,
}{m_{t + 1} = m_{t} \vee 1\left\lbrack x_{t + 1} \notin K_{t + 1} \right\rbrack.}$$

**Teorema 7.7. Exactitud y persistencia del monitor.**

Para cada tiempo de la ejecución:

$$m_{t} = 1\text{\:\,} \Longleftrightarrow \text{\:\,}\exists s \leq t:\text{\:\,}x_{s} \notin K_{s}.$$

Además, una vez que $m_{t} = 1$, permanece en uno en toda extensión de esa ejecución.

**Demostración.**

En $t = 0$, la equivalencia es la definición.

El paso inductivo añade exactamente la posibilidad de una violación en $t + 1$:

$$m_{t + 1} = \bigvee_{s = 0}^{t + 1}1\left\lbrack x_{s} \notin K_{s} \right\rbrack.$$

Una disyunción verdadera permanece verdadera al añadir términos. $\square$

El estado físico puede regresar a una región segura. Ese retorno no borra una violación anterior.

El monitor es un registro de evaluación. Su cálculo no modifica automáticamente el estado causal, la información del controlador ni la política.

Para deducir un veredicto de inviabilidad, la tarea del Módulo VI debe exigir la condición correspondiente y admitir la evidencia utilizada.

**14. Destinos y trayectorias**

**Definición 7.13. Consulta de destino.**

Un destino declara:

-   los contextos donde resulta aplicable;

-   su caracterización;

-   su significado objetivo;

-   la información o evidencia necesaria para reconocerlo.

La consulta de pertenencia al destino es parcial cuando faltan esos requisitos.

En un protocolo que clasifica todos los estados de la traza inspeccionada, se obtienen los tiempos:

$$T_{dest}(e) = \left\{ t \in D_{e}:\text{la~pertenencia~al~destino~est}\overset{ˊ}{\text{a}}\text{~acreditada~en~}t \right\}.$$

Alcanzar el destino significa:

$$T_{dest}(e) \neq \varnothing.$$

Esta consulta no modifica el árbol.

Llegar a un destino no implica terminar el proceso, permanecer allí ni haber evitado daños anteriores.

**Ejemplo 7.1. Mismo destino, distinta seguridad de trayectoria.**

Consideremos:

$${e_{1} = \left( r,s,s \right),
}{e_{2} = \left( r,u,s \right),}$$

con destino $s$y regiones requeridas:

$$K_{0} = \left\{ r \right\},\ K_{1} = K_{2} = \left\{ s \right\}.$$

Ambas ejecuciones llegan al mismo destino. Sin embargo:

$$m_{2}\left( e_{1} \right) = 0,\ m_{2}\left( e_{2} \right) = 1.$$

La segunda conserva una violación intermedia aunque termine en $s$.

Si falta la traducción o el significado de $u$, esa ausencia afecta a la evaluación correspondiente; no elimina la segunda ejecución.

Si una ley posterior le asigna probabilidad cero, la ejecución continúa perteneciendo al conjunto causal declarado. Su papel en una exigencia universal permanece distinto de su masa probabilística.

**15. Salida del Módulo V e integración**

El módulo entrega, para cada experimento certificado:

$$\boxed{\left( \kappa,Q_{\kappa}^{exec},F_{\kappa}, \sqsubseteq ,R,uns\text{registros~de~cada~ocurrencia} \right).}$$

Las consultas incluyen los prefijos; las realizaciones completas conservan su condición de horizonte o terminación; los escenarios mantienen todas sus ramas.

Esta salida permite:

-   al **Módulo III**, evaluar las recetas generativas sobre todas las realizaciones pertinentes de cada política;

-   al **Módulo IV**, obtener el reloj real de cada ejecución y registrar sus portadores sin borrar intervalos vacíos;

-   al **Módulo VI**, evaluar tareas y construir probabilidades sobre el experimento identificado;

-   al **Módulo VII**, comparar alternativas manteniendo las mismas políticas y realizaciones en las afirmaciones conjuntas.

La muerte de un portador no termina automáticamente el proceso. Una llegada favorable tampoco lo termina. La terminación pertenece a la estructura causal declarada.

**La siguiente entrega es el Módulo VI: evidencia, significado, viabilidad y Probabilidad de Vida Sostenida.**

**Entrega 8 --- Módulo VI: evidencia, significado, viabilidad y Probabilidad de Vida Sostenida**

El Módulo VI establece **cuándo una afirmación de viabilidad está justificada y cuándo puede asignarse una probabilidad al éxito de la tarea declarada**.

La construcción distingue tres preguntas:

-   ¿Qué hechos y significados están acreditados?

-   ¿Esos significados permiten determinar un veredicto?

-   ¿Qué masa probabilística corresponde a cada resultado?

Un veredicto negativo es una respuesta definida. La ausencia de evidencia suficiente conserva la evaluación como indeterminada.

**1. Experimento, tarea y veredicto**

Fijamos un experimento del Módulo V:

$$\kappa = \left( \mathfrak{M},\beta,\gamma,c_{0},\pi,H \right).$$

Sean:

$$\mathsf{Q}^{exec}$$

sus consultas causales, y:

$$F = \mathfrak{F}_{H,\gamma}^{poss}\left( c_{0},\pi \right)$$

sus realizaciones completas.

Las consultas incluyen prefijos. La ley probabilística se construirá sobre $F$.

**Definición 8.1. Tarea de viabilidad.**

La tarea declara un espacio de significados:

$$S_{viab},$$

y una función parcial:

$$\Phi:D_{\Phi} \subseteq S_{viab} \longrightarrow \left\{ 0,1 \right\}.$$

Dentro de su dominio:

$$\Phi(s) = 1$$

significa que el significado $s$satisface la tarea, mientras que:

$$\Phi(s) = 0$$

significa que no la satisface.

Para que la probabilidad resultante se interprete como **Probabilidad de Vida Sostenida**, la tarea debe especificar sus condiciones de vida sostenida: frontera, portadores, horizonte, restricciones y criterios pertinentes.

Una probabilidad de éxito de cualquier otra tarea conserva el significado de esa otra tarea.

Los significados fuera de $D_{\Phi}$no reciben automáticamente el valor cero.

**2. Extracción factual y traducción de contenido**

**Definición 8.2. Cadena factual.**

Consideremos los mapas parciales:

$${\Upsilon:\mathsf{Q}^{exec} \rightharpoonup C_{loc},
}{Q^{eval}:C_{loc} \rightharpoonup C_{c}.}$$

El primero extrae contenido local de una consulta. El segundo lo traduce al marco común.

Se aportan referencias factuales:

$${J_{exec}:\mathsf{Q}^{exec} \rightharpoonup U_{fact},
}{J_{loc}:C_{loc} \rightharpoonup U_{fact},
}{J_{c}:C_{c} \rightharpoonup U_{fact}.}$$

Estas referencias se fundamentan independientemente del resultado que se desea obtener.

La fidelidad de extracción exige:

$$J_{exec}(h) = J_{loc}\left( \Upsilon(h) \right).$$

La fidelidad del puente exige:

$$J_{loc}\left( \Upsilon(h) \right) = J_{c}\left( Q^{eval}\left( \Upsilon(h) \right) \right).$$

Cada igualdad se consulta únicamente cuando están definidos todos sus términos.

**Proposición 8.1. Conservación factual por composición.**

Si ambas igualdades están acreditadas, entonces:

$$J_{exec}(h) = J_{c}\left( Q^{eval}\left( \Upsilon(h) \right) \right).$$

**Demostración.**

Se aplica la transitividad de la igualdad al significado intermedio común. $\square$

Esta prueba establece fidelidad respecto de las referencias. La corrección factual de las referencias sigue siendo una premisa fundamentada de la instancia; una etiqueta de procedencia no demuestra por sí sola su verdad.

**Interpretación de tarea.**

Se declaran además:

$${\tau_{loc}:C_{loc} \rightharpoonup S_{viab},
}{\tau_{c}:C_{c} \rightharpoonup S_{viab}.}$$

La coherencia de tarea exige:

$$\tau_{loc}\left( \Upsilon(h) \right) = \tau_{c}\left( Q^{eval}\left( \Upsilon(h) \right) \right).$$

Esta igualdad se comprueba antes de aplicar $\Phi$.

Dos contenidos pueden recibir el mismo veredicto y tener significados diferentes. Por ello:

$$\Phi\left( s_{1} \right) = \Phi\left( s_{2} \right)$$

no demuestra:

$$s_{1} = s_{2}.$$

**Fidelidad y cobertura.**

Se distinguen los dominios de extracción, traducción e interpretación:

$${A_{U} = \mathsf{Q}^{exec} \cap D_{\Upsilon},
}{A_{Q} = \left\{ h \in A_{U}:\Upsilon(h) \in D_{Q^{eval}} \right\},
}{A_{S} = \left\{ h \in A_{Q}:\begin{matrix}
\Upsilon(h) \in D_{\tau_{loc}}, \\
Q^{eval}\left( \Upsilon(h) \right) \in D_{\tau_{c}}
\end{matrix} \right\}.}$$

Las verificaciones incluyen todas las afirmaciones emitidas, también las que resulten incorrectas.

Se conservan separadamente:

$$\mathsf{Q}^{exec} \smallsetminus A_{U},\ A_{U} \smallsetminus A_{Q},\ A_{Q} \smallsetminus A_{S}.$$

Un extractor que no emite ninguna afirmación puede no haber emitido falsedades, pero eso no acredita cobertura.

**3. Adaptadores con varios significados posibles**

**Definición 8.3. Fidelidad relacional.**

Sea:

$$Q:A \rightharpoonup \mathcal{P}(B)$$

un adaptador que puede producir varias representaciones.

Los intérpretes asignan conjuntos de significados no vacíos:

$${J_{A}:A \rightharpoonup \mathcal{P}_{+}(U),
}{J_{B}:B \rightharpoonup \mathcal{P}_{+}(U),}$$

donde:

$$\mathcal{P}_{+}(U) = \left\{ S \subseteq U:S \neq \varnothing \right\}.$$

La fidelidad en $a$requiere que:

-   $Q(a)$esté definido y sea no vacío;

-   $J_{A}(a)$esté definido;

-   cada $J_{B}(b)$, para $b \in Q(a)$, esté definido;

-   se cumpla:

$$J_{A}(a) = \bigcup_{b \in Q(a)}^{}J_{B}(b).$$

No se selecciona únicamente una salida favorable.

**Teorema 8.2. Composición de adaptadores fieles.**

Sean $Q:A \rightharpoonup \mathcal{P}(B)$y $R:B \rightharpoonup \mathcal{P}(C)$.

Supongamos que $Q$es fiel en $a$, que $R$es fiel en todos los miembros de $Q(a)$, y que ambas interfaces comparten efectivamente el mismo intérprete intermedio $J_{B}$.

Entonces:

$$(R \circ Q)(a) = \bigcup_{b \in Q(a)}^{}R(b)$$

es una traducción fiel en $a$.

**Demostración.**

Por las fidelidades:

$$J_{A}(a) = \bigcup_{b \in Q(a)}^{}J_{B}(b),$$

y:

$$J_{B}(b) = \bigcup_{c \in R(b)}^{}J_{C}(c).$$

Sustituyendo:

$$J_{A}(a) = \bigcup_{b \in Q(a)}^{}{\bigcup_{c \in R(b)}^{}J_{C}}(c).$$

Esta es la unión de significados de la composición. Las guardas garantizan que todas las fibras utilizadas existen y son no vacías. $\square$

Si varias traducciones comparten restricciones o parámetros, también deben conservarse sus interpretaciones conjuntas compatibles, como exige el Módulo II.

**4. Significado causal de una consulta**

**Definición 8.4. Referencia semántica de la tarea.**

La tarea aporta:

$$J_{task}:D_{J} \subseteq F \longrightarrow \mathcal{P}_{+}\left( S_{viab} \right).$$

Cada realización completa tiene, cuando está fundamentada, un conjunto no vacío de significados pertinentes.

Esta referencia no se obtiene del veredicto buscado ni del éxito del extractor que se está validando.

Para una consulta $h$, recordamos:

$$L(h) = \left\{ u \in F:h \sqsubseteq u \right\}.$$

Definimos:

$$D_{Sem} = \left\{ h, \in \mathsf{Q}^{exec}:L(h) \neq \varnothing\text{~}L(h) \subseteq D_{J} \right\}.$$

Solo en ese dominio:

$$\boxed{Sem(h) = \bigcup_{u \in L(h)}^{}J_{task}(u).}$$

La definición comprueba todas las completaciones. Si falta la referencia de alguna, no se presenta la unión de las restantes como la semántica completa.

**Teorema 8.3. No vaciedad y refinamiento semántico.**

Si $h \in D_{Sem}$, entonces:

$$Sem(h) \neq \varnothing.$$

Si:

$$h \sqsubseteq h^{'},$$

y ambas consultas pertenecen al dominio, entonces:

$$\varnothing \neq Sem\left( h^{'} \right) \subseteq Sem(h).$$

**Demostración.**

Existe al menos una completación y cada referencia utilizada es no vacía. Su unión es no vacía.

Además:

$$L\left( h^{'} \right) \subseteq L(h),$$

porque toda completación de $h^{'}$también completa a $h$. La inclusión de las uniones se sigue inmediatamente. $\square$

Una reducción de completaciones es suficiente para esta consulta únicamente si conserva la unión completa de significados. La evaluabilidad de las completaciones seleccionadas no demuestra esa suficiencia.

**5. Horizonte y evidencia terminal**

La cobertura causal y la cobertura temporal de una tarea son propiedades diferentes.

Una ejecución puede terminar causalmente antes de $H$, pero esa terminación no demuestra automáticamente una condición de vida sostenida hasta $H$.

El protocolo temporal debe acreditar lo pertinente mediante:

-   cobertura directa de los tiempos requeridos;

-   una prueba de cierre semántico, cuando intervenga un límite;

-   una prueba de suficiencia de la terminación anticipada para la tarea.

En relojes que permiten aproximación a un límite:

$$\sup D_{e} = H$$

no implica:

$$H \in D_{e}.$$

Por ejemplo, $\left\lbrack 0,1 \right)$tiene supremo $1$, pero no contiene el instante $1$.

Para un horizonte infinito tampoco se introduce un estado ficticio «en infinito».

**Definición 8.5. Evidencia de endpoint.**

Cuando una ruta de evaluación necesita un endpoint, se parte de su existencia y caracterización factual, con sus traducciones certificadas.

Sea:

$$Z(h)$$

el conjunto de endpoints comunes acreditados para la consulta.

Su transporte al contenido terminal de la tarea es:

$$T^{end}:Z_{c}\mathcal{\rightharpoonup P}\left( C_{term} \right).$$

Se exige que $Z(h)$sea no vacío y que cada fibra utilizada exista y sea no vacía.

La fidelidad se comprueba por cada endpoint:

$$J_{Z}(z) = \bigcup_{c \in T^{end}(z)}^{}J_{T}(c).$$

También debe ser fiel la proyección del contenido factual común:

$$\Pi^{term}:C_{c} \rightharpoonup C_{term}.$$

Con una proyección semántica declarada $\rho_{term}$, se comprueba:

$$J_{T}\left( \Pi^{term}(c) \right) = \rho_{term}\left\lbrack \left\{ J_{c}(c) \right\} \right\rbrack,$$

después de verificar todos los dominios involucrados.

Solo entonces se contrasta la coherencia entre la lectura factual y la lectura terminal.

Si la tarea exige un significado simultáneamente compatible con varios contenidos, debe acreditarse la intersección conjunta correspondiente.

**Contraejemplo de uso incorrecto 8.1. Inferir compatibilidad conjunta de compatibilidades por parejas.**

Los conjuntos:

$$\left\{ a,b \right\},\ \left\{ b,c \right\},\ \left\{ a,c \right\}$$

tienen intersecciones no vacías por parejas, pero:

$$\left\{ a,b \right\} \cap \left\{ b,c \right\} \cap \left\{ a,c \right\} = \varnothing.$$

La condición que excluye la inferencia es comprobar el testigo común cuando la tarea lo exige.

Si una ruta no requiere endpoint, esa rama de verificación no se impone. Una prueba decisiva puede justificar un veredicto antes de que exista evidencia terminal.

**6. Certificados decisivos**

**Definición 8.6. Certificado de veredicto.**

Un protocolo $\mathcal{P}$declara qué lectores y certificados admite.

Un certificado $b$para una consulta $h$construye un conjunto de significados:

$$A_{b} \subseteq S_{viab}.$$

Para acreditar un valor $v \in \left\{ 0,1 \right\}$, debe demostrar:

$${h \in D_{Sem},
}{\varnothing \neq Sem(h) \subseteq A_{b},
}{A_{b} \subseteq D_{\Phi},}$$

y:

$$\Phi\left\lbrack A_{b} \right\rbrack = \left\{ v \right\}.$$

Además, los hechos, lectores y argumentos utilizados deben estar admitidos y fundamentados.

Los hechos de una rama hermana no se presentan como observaciones de $h$. Un testigo de ocurrencia utilizado como hecho histórico debe corresponder a la propia consulta o a uno de sus prefijos.

Un lector exacto de todas las completaciones constituye una capacidad distinta del evaluador, que debe estar declarada en el protocolo. Su uso no concede información adicional al controlador.

**Teorema 8.4. Corrección y unicidad del certificado decisivo.**

Todo certificado aceptado acredita:

$$\forall s \in Sem(h),\ \Phi(s) = v.$$

Dos certificados correctos para la misma consulta no pueden acreditar valores diferentes.

**Demostración.**

La primera afirmación se sigue de:

$$Sem(h) \subseteq A_{b}$$

y de la constancia de $\Phi$sobre $A_{b}$.

Para la segunda, sean $A_{b}$y $A_{b^{'}}$dos conjuntos certificados. Como:

$$Sem(h) \neq \varnothing,$$

podemos tomar $s \in Sem(h)$. Ambos conjuntos contienen $s$, por lo que sus valores son necesariamente:

$$v = \Phi(s) = v^{'}.$$

$$\square$$

La no vaciedad proporciona el significado común que sostiene la prueba de unicidad.

**7. Vía completa y unión de las rutas de evaluación**

La vía completa construye un significado:

$$S^{full}(h) = \tau_{c}\left( Q^{eval}\left( \Upsilon(h) \right) \right),$$

con extracción, traducción e interpretación acreditadas.

Además, exige:

$$Sem(h) = \left\{ S^{full}(h) \right\},$$

y:

$$S^{full}(h) \in D_{\Phi}.$$

Un significado completamente identificado puede estar fuera del dominio de la tarea. Por eso la segunda condición no se omite.

La adecuación de esta vía reúne:

$$\begin{aligned}
FullTaskAdeq(h) = & HViabAdeq(h) \\
 & \land EndTaskAdeq^{full}(h) \\
 & \land TaskContentAdeq(h) \\
 & \land FullMeaningFid(h) \\
 & \land OtherReqAdeq(h).
\end{aligned}$$

Estos factores corresponden a evidencia temporal, evidencia terminal cuando se necesita, fidelidad del contenido, determinación semántica completa y requisitos adicionales previamente declarados.

No son etiquetas que sustituyan las pruebas: cada uno se obtiene de sus guardas, coberturas e igualdades.

**Definición 8.7. Evaluador parcial de viabilidad.**

Sea $DecisiveAdeq(h)$la existencia de un certificado decisivo permitido.

Definimos:

$$D_{V} = \left\{ h:DecisiveAdeq(h) \vee FullTaskAdeq(h) \right\}.$$

El evaluador es:

$$V:D_{V} \longrightarrow \left\{ 0,1 \right\}.$$

Cuando hay certificado decisivo, utiliza su valor. En la vía completa:

$$V(h) = \Phi\left( S^{full}(h) \right).$$

**Teorema 8.5. Acuerdo de las rutas.**

Si ambas vías están acreditadas, producen el mismo valor.

**Demostración.**

La vía completa identifica:

$$Sem(h) = \left\{ S^{full}(h) \right\}.$$

Todo certificado decisivo contiene ese significado y coincide con $\Phi$en él. Por tanto, ambos valores son iguales. $\square$

Una contradicción entre certificados invalida su aceptación. No autoriza a elegir el resultado preferido.

La falta de adecuación de una vía tampoco implica $V(h) = 0$. Puede existir otra vía válida o permanecer la consulta fuera del dominio.

**8. Decisión temprana con significado todavía multivaluado**

**Ejemplo 8.1. Una violación histórica decide el resultado.**

Consideremos significados:

$$s = \left( m,r \right) \in \left\{ 0,1 \right\}^{2},$$

donde:

-   $m = 1$indica una violación histórica de una condición obligatoria;

-   $r = 1$indica el cumplimiento de un requisito terminal.

La tarea es:

$$\Phi\left( m,r \right) = 1\text{\:\,} \Longleftrightarrow \text{\:\,}m = 0 \land r = 1.$$

En un prefijo se acredita la violación y se demuestra que todas sus completaciones tienen significados en:

$$A = \left\{ \left( 1,0 \right),\left( 1,1 \right) \right\}.$$

La condición terminal todavía puede variar, pero:

$$\Phi\left( 1,0 \right) = \Phi\left( 1,1 \right) = 0.$$

Si la cobertura y el certificado están admitidos:

$$V(h) = 0.$$

No hace falta determinar cuál de los dos significados terminales ocurrirá.

Si ambos siguen siendo posibles:

$$\mid Sem(h) \mid = 2,$$

de modo que la vía completa no está disponible allí, pero la vía decisiva sí.

El monitor del Módulo V puede aportar la persistencia del hecho histórico. La conclusión requiere además que la tarea efectivamente rechace esa violación y que la cobertura semántica esté acreditada.

**Contraejemplo de uso incorrecto 8.2. Omitir los significados donde la tarea está indefinida.**

Supongamos:

$$Sem(k) = \left\{ p,q \right\},$$

con:

$$\Phi(p) = 1,\ q \notin D_{\Phi}.$$

Si se consideran solo los argumentos definidos:

$$\Phi\left\lbrack Sem(k) \cap D_{\Phi} \right\rbrack = \left\{ 1 \right\}.$$

Pero esto ha omitido $q$.

No puede acreditarse el valor uno porque:

$$Sem(k) \subseteq \not{}D_{\Phi}.$$

La condición de dominio se verifica antes de formar la imagen utilizada en el certificado.

**9. Dominio exacto de decisión**

**Definición 8.8. Dominio semánticamente decisivo.**

Definimos:

$$D_{*} = \left\{ h, \in D_{Sem}:Sem(h) \subseteq D_{\Phi}\text{~} \mid \Phi\left\lbrack Sem(h) \right\rbrack \mid = 1 \right\}.$$

**Teorema 8.6. Exactitud cuando el protocolo admite el lector completo.**

Si el protocolo admite la lectura fundamentada exacta de $Sem(h)$, entonces:

$$D_{V} = D_{*}.$$

**Demostración.**

Si existe un certificado decisivo, su conjunto $A_{b}$contiene $Sem(h)$, está dentro de $D_{\Phi}$y tiene un único veredicto. Esto implica $h \in D_{*}$.

La vía completa también implica esas propiedades.

Recíprocamente, si $h \in D_{*}$, puede utilizarse:

$$A_{b} = Sem(h).$$

El lector exacto está admitido y todas las condiciones del certificado se cumplen. Por tanto, $h \in D_{V}$. $\square$

En la presentación finita, el lector obtiene la unión de todas las referencias pertinentes y comprueba las condiciones.

Un protocolo con lectores o certificados más restringidos puede tener un dominio menor. Su nombre y sus reglas deben acompañar al evaluador y a las probabilidades derivadas de él.

La igualdad anterior no afirma un procedimiento universal para decidir tareas semánticas arbitrarias.

**10. Construcción de una ley probabilística**

La relación causal del Módulo V no contiene por sí sola probabilidades.

**Definición 8.9. Ley del experimento.**

Se aporta una medida:

$$\mathbb{P}_{\kappa}$$

sobre las realizaciones completas de ese mismo experimento.

Para un cálculo finito exacto pueden utilizarse pesos racionales.

La raíz recibe masa:

$$p(r) = 1.$$

Cada fila probabilística suministrada en un nodo interno $h$debe incluir exactamente todos sus hijos causales y satisfacer:

$$q_{h}(c) \geq 0,\ \sum_{c \in Hijos(h)}^{}q_{h}(c) = 1.$$

Las masas se propagan mediante:

$$p(c) = p(h)\text{ }q_{h}(c).$$

Una rama con peso cero permanece en el árbol.

**Filas ausentes y nodos nulos.**

Si falta una fila en un nodo de masa positiva, la ley no queda determinada.

Si el nodo tiene masa cero, todos sus descendientes tienen masa cero para esa medida fija. Esto permite determinar la medida foliar sin inventar una distribución condicional en ese nodo.

Una fila suministrada pero inválida sigue siendo inválida aunque su nodo tenga masa cero. Tampoco se eliminan restricciones compartidas de una familia de leyes mediante este argumento.

**Teorema 8.7. Normalización de la ley finita.**

Bajo esas condiciones:

$$\sum_{e \in F}^{}p(e) = 1.$$

**Demostración.**

La suma de masas de las hojas descendientes de un nodo es igual a la masa de ese nodo.

En una hoja es inmediato.

En un nodo con fila definida:

$$\sum_{c}^{}p(c) = p(h)\sum_{c}^{}q_{h}(c) = p(h).$$

En un nodo de masa cero sin fila, todas las contribuciones descendientes son cero.

La inducción sobre la altura del árbol lleva el resultado hasta la raíz, cuya masa es uno. $\square$

En una presentación medible más general, una ley puede construirse mediante:

$$\mathbb{P}(A) = \int_{D_{K}}^{}K(A \mid h)\text{ }\mu_{up}(dh),$$

si $K$es un kernel legítimo en su dominio, tiene soporte causal y:

$$\mu_{up}\left( D_{K} \right) = 1.$$

La normalización resulta de integrar $K(F \mid h) = 1$. Un dominio de masa menor que uno no se renormaliza silenciosamente.

**11. Partición de las realizaciones**

**Definición 8.10. Tres regiones de evaluación.**

Para un evaluador parcial legítimo $V$, definimos sobre $F$:

$${F^{V, +} = \left\{ e \in F \cap D_{V}:V(e) = 1 \right\},
}{F^{V, -} = \left\{ e \in F \cap D_{V}:V(e) = 0 \right\},
}{F^{V,?} = F \smallsetminus D_{V}.}$$

Son, respectivamente:

-   éxito acreditado;

-   fallo acreditado;

-   evaluación indeterminada.

Una presentación contradictoria o mal tipada se diagnostica antes de esta construcción. No se trata como una realización ordinaria de la tercera región.

**Teorema 8.8. Partición y conservación de masa.**

Las tres regiones son disjuntas y su unión es $F$.

Cuando son medibles, sus masas:

$${M^{+}\mathbb{= P}\left( F^{V, +} \right),
}{M^{-}\mathbb{= P}\left( F^{V, -} \right),
}{M^{?}\mathbb{= P}\left( F^{V,?} \right)}$$

satisfacen:

$$\boxed{M^{+} + M^{-} + M^{?} = 1.}$$

**Demostración.**

Cada realización está dentro o fuera de $D_{V}$.

Dentro del dominio, la función toma exactamente uno de los valores cero o uno. Esto da exclusividad y exhaustividad.

La igualdad de masas se sigue de la aditividad y de $\mathbb{P}(F) = 1$. $\square$

En el espacio finito todas estas regiones son medibles.

Los prefijos evaluados no se agregan como nuevos resultados disjuntos. Un prefijo representa un conjunto de completaciones; sumarlo nuevamente junto a sus hojas duplicaría masa.

**12. Definición de PVS**

**Definición 8.11. Probabilidad de Vida Sostenida.**

Para el experimento, la tarea y el protocolo declarados, la PVS está definida cuando:

1.  existe una ley legítima;

2.  las tres regiones son medibles;

3.  la masa de evaluación indeterminada es cero:

$$M^{?} = 0.$$

Entonces:

$$\boxed{PVS_{\kappa,\mathcal{T,P}} = M^{+}.}$$

Si:

$$M^{?} > 0,$$

se conserva el vector:

$$VProb = \left( M^{+},M^{-},M^{?} \right),$$

y la PVS de ese protocolo permanece indefinida.

Esto no transforma la indeterminación en fracaso ni en éxito.

**Ejemplo 8.2. Masa indeterminada positiva.**

Consideremos:

  -----------------------------------------------------------------------
  **Realización**               **Masa**      **Evaluación**
  ----------------------------- ------------- ---------------------------
  $$\mathbf{e}_{1}$$            $$1/2$$       $$1$$

  $$\mathbf{e}_{2}$$            $$1/4$$       $$0$$

  $$\mathbf{e}_{3}$$            $$1/4$$       Indefinida
  -----------------------------------------------------------------------

Entonces:

$$VProb = \left( \frac{1}{2},\frac{1}{4},\frac{1}{4} \right).$$

La PVS no está definida porque:

$$M^{?} = \frac{1}{4} > 0.$$

**Contraejemplo de uso incorrecto 8.3. Renormalizar sobre lo evaluable.**

El cociente:

$$\frac{M^{+}}{M^{+} + M^{-}} = \frac{1/2}{3/4} = \frac{2}{3}$$

es la probabilidad de éxito condicionada a pertenecer a la región evaluable.

No es la PVS del experimento original. La tercera realización conserva su masa y no puede retirarse para producir ese valor.

**13. Probabilidad uno y garantía universal**

**Ejemplo 8.3. Una rama nula desfavorable.**

Sean dos realizaciones causalmente posibles:

$$g,\ z,$$

con:

$$\mathbb{P}\left( \left\{ g \right\} \right) = 1,\ \mathbb{P}\left( \left\{ z \right\} \right) = 0.$$

Supongamos:

$$V(g) = 1,\ V(z) = 0.$$

Entonces:

$$M^{+} = 1,\ M^{-} = 0,\ M^{?} = 0,$$

y:

$$PVS = 1.$$

Sin embargo:

$$\forall e \in F,\ V(e) = 1$$

es falso, porque $V(z) = 0$.

Por tanto:

$$\boxed{PVS = 1\text{\:\,} \Rightarrow \not{}\text{\:\,}\overset{ˊ}{\text{e}}\text{xito~en~toda~realizaci}\overset{ˊ}{\text{o}}\text{n~causal}.}$$

Si $V(z)$estuviera indefinido, la PVS seguiría valiendo uno porque esa indeterminación tiene masa cero. La evaluación de $z$permanecería indeterminada y la garantía universal no quedaría acreditada.

La rama nula se conserva en ambos casos. También sigue siendo pertinente para las obligaciones universales de otros módulos.

**14. Cotas cuando todavía falta evaluación**

**Proposición 8.9. Cotas de completación.**

Supongamos que existe una extensión semánticamente admisible, total y medible:

$$V^{*}:F \longrightarrow \left\{ 0,1 \right\},$$

que coincide con $V$en $D_{V}$.

Entonces:

$$\boxed{M^{+}\mathbb{\leq P}\left( V^{*} = 1 \right) \leq M^{+} + M^{?}.}$$

**Demostración.**

La extensión conserva todos los éxitos y fallos acreditados. Por ello:

$$F^{V, +} \subseteq \left\{ V^{*} = 1 \right\} \subseteq F^{V, +} \cup F^{V,?}.$$

La monotonía de la medida proporciona las cotas. $\square$

En el ejemplo 8.2:

$$\frac{1}{2}\mathbb{\leq P}\left( V^{*} = 1 \right) \leq \frac{3}{4}.$$

Estas son cotas condicionadas a la existencia de una completación admisible. No afirman que cualquier asignación de los casos indeterminados sea legítima ni que ambos extremos sean alcanzables.

**15. Ampliación de evidencia y estabilidad de PVS**

**Definición 8.12. Refinamiento de evaluación.**

Dos evaluadores sobre la misma tarea, realizaciones y ley satisfacen:

$$V_{1} \preceq_{ev}V_{2}$$

cuando:

$$D_{V_{1}} \subseteq D_{V_{2}},$$

y:

$$V_{2}(h) = V_{1}(h)\ \text{para~todo~}h \in D_{V_{1}}.$$

El segundo decide al menos los mismos casos y conserva sus valores.

Ampliar los certificados admitidos, manteniendo su corrección, puede producir este refinamiento. Cambiar o restringir el protocolo no lo garantiza.

**Teorema 8.10. Monotonía de las masas bajo refinamiento.**

Con la misma ley:

$${M_{1}^{+} \leq M_{2}^{+},
}{M_{1}^{-} \leq M_{2}^{-},
}{M_{2}^{?} \leq M_{1}^{?}.}$$

Además:

$$M_{1}^{?} - M_{2}^{?} = \left( M_{2}^{+} - M_{1}^{+} \right) + \left( M_{2}^{-} - M_{1}^{-} \right).$$

**Demostración.**

El acuerdo de valores y la inclusión de dominios implican:

$$F_{1}^{+} \subseteq F_{2}^{+},\ F_{1}^{-} \subseteq F_{2}^{-},\ F_{2}^{?} \subseteq F_{1}^{?}.$$

Las desigualdades se obtienen por monotonía de la medida. La identidad resulta de restar las dos igualdades de normalización. $\square$

**Corolario. Una PVS ya definida permanece estable.**

Si:

$$M_{1}^{?} = 0,$$

entonces:

$$M_{2}^{?} = 0$$

y:

$$PVS_{2} = PVS_{1}.$$

Las nuevas decisiones solo pueden resolver casos de una región que ya tenía masa cero.

La inclusión semántica entre prefijos no demuestra por sí sola este refinamiento protocolario: también debe conservarse la admisión de las pruebas utilizadas.

**16. Transporte de leyes y evaluaciones**

**Definición 8.13. Imagen directa de una medida finita.**

Sea:

$$T:F \longrightarrow F^{'}$$

un mapa definido en todas las realizaciones de origen, incluidas las de masa cero.

La medida transportada es:

$$p^{'}(y) = \sum_{e:T(e) = y}^{}p(e).$$

Cada realización de origen aporta su masa exactamente a una fibra.

**Teorema 8.11. Conservación de masas de evaluación.**

Supongamos además que el transporte conserva el veredicto parcial completo:

$${\widehat{V}}^{'}\left( T(e) \right) = \widehat{V}(e)\ \text{para~toda~}e \in F.$$

La marca de indefinición forma parte de esta igualdad.

Entonces se conservan:

$$M^{+},\ M^{-},\ M^{?},$$

y, por tanto, el dominio de PVS y su valor.

**Demostración.**

Para cada región $\bullet \in \left\{ + , - ,? \right\}$:

$$T^{- 1}\left( F^{' \bullet} \right) = F^{\bullet}.$$

Por la definición de imagen directa:

$$\mathbb{P}^{'}\left( F^{' \bullet} \right)\mathbb{= P}\left( T^{- 1}\left( F^{' \bullet} \right) \right)\mathbb{= P}\left( F^{\bullet} \right).$$

$$\square$$

La conclusión probabilística no requiere que todo punto del destino tenga preimagen: los puntos restantes reciben masa cero bajo esta medida transportada.

La cobertura causal completa del destino es otra obligación, tratada en el Módulo V.

Para acreditar la igualdad de evaluadores entre marcos no basta comparar los casos donde ambos ya deciden. Deben conservarse también sus dominios, significados, reglas de tarea y certificados admitidos.

**17. PVS común entre realizaciones fieles**

Una misma configuración común puede tener varias realizaciones locales.

En modo $pre$:

$$\chi^{c} = \left( c_{0}^{c},\pi^{c} \right).$$

En modo $fix$:

$$\chi^{c} = \left( c_{0}^{c},\delta^{c},\pi^{c} \right).$$

Sea:

$$\mathfrak{J}_{\beta}^{fid}\left( \chi^{c} \right)$$

la familia completa declarada de realizaciones locales fieles, acreditadas mediante los certificados de inicialización, política, hechos y significado correspondientes.

Para obtener un único valor común se exige:

$$\mathfrak{J}_{\beta}^{fid}\left( \chi^{c} \right) \neq \varnothing,$$

PVS definida en cada miembro, y un valor $v$tal que:

$$\forall r \in \mathfrak{J}_{\beta}^{fid}\left( \chi^{c} \right),\ PVS(r) = v.$$

La igualdad se consulta después de comprobar el dominio de cada miembro.

Entonces:

$$PVS_{\beta}^{com}\left( \chi^{c} \right) = v.$$

La no vaciedad garantiza la unicidad del valor común.

Si una realización fiel permanece fuera del dominio, no se elimina para obtener acuerdo entre las restantes.

Si se comparan varios modelos $\beta$, se conserva su familia indexada y sus resultados. Una mezcla probabilística entre modelos requiere una ley adicional explícita.

**Integración del Módulo VI**

El módulo entrega un evaluador parcial identificado por experimento, tarea y protocolo:

$$V:\mathsf{Q}^{exec} \rightharpoonup \left\{ 0,1 \right\}.$$

Cuando existe una ley adecuada, entrega:

$$VProb = \left( M^{+},M^{-},M^{?} \right).$$

La PVS se añade exactamente cuando:

$$M^{?} = 0.$$

Los dominios y testigos permanecen visibles para el Módulo VII. Una evaluación incompleta no se convierte en fracaso, una probabilidad uno no se convierte en garantía universal y un valor probabilístico no sustituye los registros de CAG o bienestar.

**La siguiente entrega es el Módulo VII: dominancia integrada, frontera y selección.**

**Entrega 9 --- Módulo VII: dominancia integrada, frontera y selección**

El Módulo VII reúne los resultados anteriores para responder tres preguntas:

-   ¿Qué alternativas cumplen las restricciones declaradas?

-   ¿Cuáles no están dominadas por otras alternativas?

-   ¿Qué regla permite elegir una de ellas?

La comparación conserva los tipos de cada objeto: un CAG es un repertorio, el bienestar contiene historias de portadores y la PVS es una probabilidad definida bajo una tarea y un protocolo.

La regla integrada adoptada exige **no empeorar en ninguno de los criterios declarados**. Una elección entre alternativas incomparables requiere una regla adicional explícita.

**1. El problema de decisión**

**Definición 9.1. Alternativas y ámbito común.**

Un problema $\mathcal{K}$declara un conjunto de alternativas:

$$\mathcal{A.}$$

El significado de «alternativa» permanece fijo dentro del problema.

En la instancia integrada que desarrollaremos, cada alternativa es una política:

$$a = \pi_{a}.$$

Las políticas comparten:

$$\mathfrak{M,\ }\beta,\ \gamma,\ c_{0},\ H.$$

La política seleccionada es la variable que cambia.

Para cada alternativa se conservan sus propias ejecuciones:

$$\mathfrak{F}_{H,\gamma}^{poss}\left( c_{0},\pi_{a} \right),$$

y las claves que identifican sus registros.

Una valoración de otra política no acredita esa alternativa, aunque tenga un nombre o un valor numérico coincidente.

**Criterios declarados.**

Se fija un índice no vacío:

$$I \neq \varnothing.$$

Cada criterio tiene una valoración parcial:

$$Y_{i}\mathcal{:A \rightharpoonup}\mathcal{Y}_{i}.$$

Entre los criterios posibles están:

  ----------------------------------------------------------------------------------------------------------------------------
  **Criterio**           **Objeto comparado**                              **Regla pertinente**
  ---------------------- ------------------------------------------------- ---------------------------------------------------
  Desempeño funcional    Perfil del Módulo I                               Producto de órdenes calibrados

  Capacidad generativa   CAG con receta y cuantificadores fijados          Inclusión de repertorios

  Bienestar              Registros y familias de historias del Módulo IV   Regla temporal y poblacional declarada

  PVS                    Probabilidad del Módulo VI                        Orden numérico, con tarea y protocolo comparables
  ----------------------------------------------------------------------------------------------------------------------------

La inclusión de estos criterios en el problema es explícita. No se deduce una utilidad universal sumando directamente objetos de tipos diferentes.

**2. Dominios de valoración y comparación**

**Definición 9.2. Comparación parcial de un criterio.**

Cada criterio declara un dominio de comparación:

$$D_{i} \subseteq \mathcal{Y}_{i} \times \mathcal{Y}_{i}.$$

Dentro de él puede consultarse:

$$u \succeq_{i}v.$$

Para comparar $a$con $b$mediante ese criterio, se exige:

$$a,b \in D_{Y_{i}},$$

y:

$$\left( Y_{i},(a)Y_{i}(b) \right) \in D_{i}.$$

La existencia de dos valores no demuestra automáticamente que puedan compararse.

**Proposición 9.1. Extensionalidad.**

Si:

$$Y_{i}(a) = Y_{i}\left( a^{'} \right),\ Y_{i}(b) = Y_{i}\left( b^{'} \right),$$

como valores del mismo tipo y ámbito, las consultas del criterio deben tener el mismo dominio y resultado.

**Demostración.**

Ambas utilizan el mismo par de argumentos de una misma relación parcial. $\square$

Un criterio no puede cambiar su respuesta por el orden en que se lo consulta o por una preferencia oculta hacia el nombre de una alternativa.

El contrato de comparación integrada comprueba todos los dominios requeridos antes de emitir un resultado conjunto. Una respuesta falsa en un criterio no se utiliza para ocultar que otro está indefinido.

**3. Restricciones obligatorias y factibilidad**

**Definición 9.3. Restricciones hard.**

Sea $J$el conjunto declarado de restricciones obligatorias.

Cada restricción tiene un juicio certificado parcial:

$$H_{j}\mathcal{:A \rightharpoonup}\left\{ 0,1 \right\}.$$

Interpretamos:

$$H_{j}(a) = 1$$

como cumplimiento acreditado de la restricción completa, y:

$$H_{j}(a) = 0$$

como refutación acreditada.

Si no existe evidencia suficiente para ninguna conclusión, el juicio permanece indefinido.

Una restricción puede exigir, por ejemplo:

$$\forall e \in \mathfrak{F}_{H,\gamma}^{poss}\left( c_{0},\pi_{a} \right)\text{~}\forall t \in D_{e}:d\left( e,t \right) \leq B.$$

Un certificado positivo debe cubrir esa afirmación completa. Una realización favorable aislada no la acredita.

Puede haber varias pruebas de una misma restricción. Un intento insuficiente no revoca otro certificado completo correcto. Dos certificados opuestos sobre la misma restricción y alternativa constituyen una contradicción que debe rechazarse.

**Definición 9.4. Tres estados de factibilidad.**

Una vez descartadas las presentaciones contradictorias:

$${A_{feas} = \left\{ a,:\forall j \in J\text{~}H_{j}(a) = 1 \right\},
}{A_{fail} = \left\{ a,:\exists j \in J\text{~}H_{j}(a) = 0 \right\},
}{A_{unk}\mathcal{= A \smallsetminus}\left( A_{feas} \cup A_{fail} \right).}$$

Las igualdades se consultan con sus dominios.

Estos conjuntos particionan $\mathcal{A}$.

Una alternativa puede tener una restricción refutada y otra todavía indeterminada. Pertenece a $A_{fail}$, pero conserva ambos diagnósticos.

Si $J = \varnothing$:

$$A_{feas}\mathcal{= A}$$

respecto de esa familia vacía. No se acredita una exigencia de vida o seguridad que nunca se declaró.

La factibilidad para seleccionar una política tampoco sustituye su posibilidad causal. Una política excluida conserva sus ejecuciones y resultados.

**4. Bloque de comparación y dominancia integrada**

**Definición 9.5. Bloque común.**

Sea:

$$B \subseteq \mathcal{A}$$

un bloque donde:

1.  todos los criterios requeridos están definidos;

2.  todos los pares requeridos son comparables;

3.  cada relación componente es reflexiva y transitiva;

4.  se mantienen el mismo índice de criterios y las mismas reglas.

En particular:

$$Y_{i}\lbrack B\rbrack \times Y_{i}\lbrack B\rbrack \subseteq D_{i}.$$

Sobre ese bloque definimos:

$$\boxed{a \succeq b\text{\:\,} \Longleftrightarrow \text{\:\,}\forall i \in I:Y_{i}(a) \succeq_{i}Y_{i}(b).}$$

La dominancia estricta es:

$$a \succ b\text{\:\,} \Longleftrightarrow \text{\:\,}a \succeq b \land \neg(b \succeq a).$$

La equivalencia es:

$$a \sim b\text{\:\,} \Longleftrightarrow \text{\:\,}a \succeq b \land b \succeq a.$$

Dos alternativas son incomparables cuando ambas comparaciones están definidas y ninguna se cumple.

**Teorema 9.2. Preorden integrado.**

La relación $\succeq$es un preorden. Su parte estricta es irreflexiva y transitiva, y el cociente por $\sim$es un orden parcial.

**Demostración.**

La reflexividad se hereda componente a componente.

Si:

$$a \succeq b,\ b \succeq c,$$

para cada criterio:

$$Y_{i}(a) \succeq_{i}Y_{i}(b) \succeq_{i}Y_{i}(c).$$

La transitividad componente implica $a \succeq c$.

La definición excluye $a \succ a$.

Si $a \succ b$y $b \succ c$, tenemos $a \succeq c$. Si además $c \succeq a$, entonces $c \succeq b$, contradiciendo $b \succ c$. Por tanto, $a \succ c$.

La dominancia mutua define una equivalencia; al identificar sus clases se obtiene antisimetría. $\square$

Se comprueba cada preorden componente. Una segunda relación podría ocultar, al intersectarse con la primera, una infracción de transitividad de esta última. La aparente coherencia del resultado conjunto no certifica por sí sola todos sus componentes.

**5. Frontera de alternativas factibles**

**Definición 9.6. Frontera relativa.**

Sea:

$$C \subseteq B \cap A_{feas}$$

el conjunto factible efectivamente comprendido en la comparación.

Su frontera es:

$$\boxed{Fr(C) = \left\{ a, \in C:\neg\exists b \in C\text{~}b \succ a \right\}.}$$

La frontera contiene los elementos **maximales**: aquellos que no tienen un dominador estricto dentro de $C$.

Un elemento maximal no tiene que dominar a todos los demás. Esa propiedad más fuerte correspondería a un máximo.

**Teorema 9.3. Existencia finita de elementos maximales.**

Si $C$es finito y no vacío:

$$Fr(C) \neq \varnothing.$$

**Demostración.**

Partimos de cualquier $a_{0} \in C$.

Si no es maximal, existe $a_{1} \succ a_{0}$. Si tampoco es maximal, continuamos con un dominador estricto.

La cadena no puede repetir elementos, porque la estricta es transitiva e irreflexiva. La finitud obliga a terminar en un maximal. $\square$

Si $C = \varnothing$, su frontera es vacía.

La afirmación de existencia no se extiende automáticamente a conjuntos infinitos. Por ejemplo, los naturales ordenados por «mayor o igual» no tienen ningún elemento maximal.

**6. Frontera local y alcance global**

**Definición 9.7. Conjunto objetivo.**

Sea:

$$C \subseteq S,$$

donde $S$es el conjunto objetivo declarado.

Para comparar ambas fronteras debe existir un mismo preorden acreditado sobre $S$, cuya restricción a $C$sea la utilizada anteriormente.

El calificativo «global» se refiere a ese conjunto objetivo.

Hay dos garantías distintas:

$$Fr(C) \subseteq Fr(S),$$

y:

$$Fr(C) = Fr(S).$$

La primera acredita que los miembros encontrados siguen siendo maximales globales. La segunda acredita además que no falta ningún maximal global.

**Teorema 9.4. Condiciones exactas de cobertura.**

Se cumple:

$$Fr(C) \subseteq Fr(S)$$

si y solo si ninguna alternativa omitida domina estrictamente a un miembro de la frontera local:

$$\forall a \in Fr(C),\ \neg\exists u \in S \smallsetminus C:\text{~}u \succ a.$$

Bajo esa condición, la igualdad de fronteras equivale a:

$$\forall u \in S \smallsetminus C,\ \exists v \in S:\text{~}v \succ u.$$

**Demostración.**

Un miembro de $Fr(C)$ya carece de dominadores estrictos dentro de $C$. Para ser maximal en $S$, solo resta excluir dominadores exteriores.

Para obtener igualdad, además debe excluirse que una alternativa exterior sea maximal. Eso equivale a que cada omitida tenga un dominador estricto en $S$. $\square$

**Contraejemplo de uso incorrecto 9.1. Confundir maximalidad de los encontrados con exhaustividad.**

Sean:

$$C = \left\{ a \right\},\ S = \left\{ a,b \right\},$$

con $a$y $b$equivalentes.

Entonces:

$$Fr(C) = \left\{ a \right\},$$

pero:

$$Fr(S) = \left\{ a,b \right\}.$$

El elemento encontrado es maximal global. La frontera local, sin embargo, no es exhaustiva.

El mismo ejemplo funciona si $a$y $b$son incomparables.

La condición que excluye la inferencia incorrecta es comprobar también la ausencia de maximales omitidos.

**7. Fronteras con factibilidad todavía indeterminada**

La teoría permite conservar la incertidumbre sobre restricciones sin tratar las alternativas correspondientes como refutadas.

Supongamos que el mismo preorden está acreditado sobre:

$$A_{feas} \cup A_{unk}.$$

Esto exige que sus valores y comparaciones estén disponibles, aunque ciertas restricciones obligatorias sigan sin resolverse.

Consideramos la familia exterior de conjuntos:

$$A_{feas} \cup T,\ T \subseteq A_{unk}.$$

Esta familia contiene todas las combinaciones posibles de admisión de las alternativas indeterminadas. No afirma que todas esas combinaciones sean conjuntamente realizables.

**Definición 9.8. Miembros necesarios y posibles.**

Definimos:

$${N = \bigcap_{T \subseteq A_{unk}}^{}{Fr}\left( A_{feas} \cup T \right),
}{P = \bigcup_{T \subseteq A_{unk}}^{}{Fr}\left( A_{feas} \cup T \right).}$$

**Teorema 9.5. Fórmulas exactas sin enumerar todas las combinaciones.**

Se cumplen:

$$\boxed{N = A_{feas} \cap Fr\left( A_{feas} \cup A_{unk} \right).}$$

Y:

$$\boxed{P = \left\{ a, \in A_{feas} \cup A_{unk}:\neg\exists f \in A_{feas}\text{~}f \succ a \right\}.}$$

**Demostración de la primera igualdad.**

Pertenecer a todas las fronteras exige pertenecer a $A_{feas}$, tomando $T = \varnothing$, y ser maximal en el conjunto mayor, tomando $T = A_{unk}$.

Recíprocamente, un miembro de $A_{feas}$sin dominadores en el conjunto mayor está presente y carece de dominadores en cada conjunto intermedio.

**Demostración de la segunda igualdad.**

Una alternativa dominada por algún $f \in A_{feas}$no puede ser maximal en ninguna completación: ese dominador siempre está presente.

Si no tiene tal dominador y pertenece a $A_{feas}$, basta tomar $T = \varnothing$.

Si pertenece a $A_{unk}$, basta tomar $T = \left\{ a \right\}$. No tiene dominadores en $A_{feas}$y no se domina estrictamente a sí misma. $\square$

Para una familia real más restringida y no vacía de completaciones:

-   $N$es una cota inferior de sus miembros necesarios;

-   $P$es una cota superior de sus miembros posibles.

Si $L = Fr(C)$, entonces:

$$L \subseteq N$$

garantiza que todos sus miembros son maximales en cada completación considerada.

Si además:

$$P \subseteq L,$$

la frontera $L$es exhaustiva en todas ellas.

Para la familia exterior completa, estas condiciones son exactas. Para una familia real restringida, pueden ser condiciones suficientes más fuertes de lo necesario.

Si faltan comparaciones en el conjunto amplio, estas garantías globales permanecen sin certificar, aunque la frontera local pueda estar correctamente definida.

**8. Robustez entre modelos o reglas**

**Definición 9.9. Dominancia robusta.**

Sea $\Omega \neq \varnothing$una familia declarada de modelos o reglas comparativas.

Sobre un bloque común, cada miembro proporciona un preorden:

$$\succeq_{\omega}.$$

Definimos:

$$a \succeq_{*}b\text{\:\,} \Longleftrightarrow \text{\:\,}\forall\omega \in \Omega:a \succeq_{\omega}b.$$

**Teorema 9.6. Preorden robusto y estricta robusta.**

La relación $\succeq_{*}$es un preorden.

Además:

$$a \succ_{*}b$$

equivale a:

$$\left\lbrack \forall,\omega\text{~}a \succeq_{\omega}b \right\rbrack \land \left\lbrack \exists,\omega\text{~}a \succ_{\omega}b \right\rbrack.$$

**Demostración.**

La reflexividad y la transitividad se mantienen al exigirlas en todos los miembros de la familia.

La estricta requiere dominancia débil unánime y que no exista dominancia débil inversa unánime. Bajo la primera condición, esto equivale a que alguna regla acredite mejora estricta. $\square$

No se exige mejora estricta en todas las reglas.

**Contraejemplo de uso incorrecto 9.2. Intersectar las fronteras individuales.**

Supongamos que una regla prefiere estrictamente $a$a $b$, y otra prefiere estrictamente $b$a $a$.

Sus fronteras son:

$$\left\{ a \right\},\ \left\{ b \right\}.$$

Su intersección es vacía.

Sin embargo, bajo la dominancia robusta ninguna alternativa domina a la otra, por lo que:

$${Fr}_{*}\left( \left\{ a,b \right\} \right) = \left\{ a,b \right\}.$$

La frontera robusta se calcula después de construir la relación robusta. No se obtiene, en general, intersectando fronteras.

**9. Reducción de alternativas**

**Definición 9.10. Reducción exacta del orden.**

Sean $C$y $\bar{C}$conjuntos comparativos, y:

$$\rho:C \longrightarrow \bar{C}$$

un mapa sobreyectivo.

Exigimos:

$$a \succeq b\text{\:\,} \Longleftrightarrow \text{\:\,}\rho(a)\text{ }\bar{\succeq}\text{ }\rho(b).$$

La reducción preserva y refleja el orden.

**Teorema 9.7. Conservación exacta de la frontera.**

Bajo esas condiciones:

$$Fr(C) = \rho^{- 1}\left\lbrack Fr\left( \bar{C} \right) \right\rbrack,$$

y:

$$\rho\left\lbrack Fr(C) \right\rbrack = Fr\left( \bar{C} \right).$$

**Demostración.**

La equivalencia de órdenes también conserva y refleja la dominancia estricta.

Si $\rho(a)$tuviera un dominador estricto, la sobreyectividad permitiría levantarlo a un dominador estricto de $a$.

En sentido inverso, todo dominador estricto de $a$produciría uno de $\rho(a)$.

Por tanto, $a$es maximal exactamente cuando lo es su imagen. La sobreyectividad da también la igualdad de imágenes de las fronteras. $\square$

La monotonía sola no basta: puede introducir comparaciones que antes no existían.

Este resultado se aplica al conjunto cuya factibilidad y alcance ya están fijados. Una reducción anterior también debe conservar las restricciones y sus dominios.

Una única clase maximal en el cociente puede contener varias alternativas equivalentes. Identificar esa clase todavía no elige un representante.

**10. Selección de una alternativa**

**Definición 9.11. Selector.**

Una regla de selección es una función parcial:

$$s:\mathcal{K \rightharpoonup}\bigcup_{\mathcal{K}}^{}C_{\mathcal{K}},$$

que, cuando está definida, satisface:

$$s\left( \mathcal{K} \right) \in Fr\left( C_{\mathcal{K}} \right).$$

Su dominio, justificación y alcance forman parte de la regla.

Si la frontera contiene un único elemento, ese elemento determina la selección dentro del alcance certificado.

Si contiene varios, sus datos no determinan automáticamente una elección única.

Una regla posible consiste en declarar un orden de prioridad total $\triangleleft$. Para una frontera finita no vacía:

$$s_{\triangleleft}\left( \mathcal{K} \right) = \min_{\triangleleft}Fr\left( C_{\mathcal{K}} \right).$$

El mínimo existe y es único porque la frontera es finita y la prioridad es total.

La prioridad constituye un dato adicional. No se deduce del preorden multicriterio.

Una frontera exhaustiva plural responde completamente a la pregunta «¿cuáles son todos los maximales?». La pregunta «¿cuál se elige?» necesita además una regla de selección definida.

**11. Simetrías y selección invariante**

**Definición 9.12. Equivarianza.**

Supongamos que un grupo $G$transforma problemas y alternativas, conservando sus datos y transportando sus fronteras:

$$Fr\left( C_{g\mathcal{K}} \right) = g\text{ }Fr\left( C_{\mathcal{K}} \right).$$

Un selector es equivariante cuando su dominio es estable bajo esas transformaciones y:

$$s\left( g\mathcal{K} \right) = g\text{ }s\left( \mathcal{K} \right).$$

Es decir, transformar el problema y luego seleccionar equivale a transformar la selección original.

El estabilizador del problema es:

$$G_{\mathcal{K}} = \left\{ g \in G:g\mathcal{K = K} \right\}.$$

**Teorema 9.8. Condición necesaria de selección equivariante.**

Si el selector está definido en $\mathcal{K}$, su resultado debe ser fijo por todas las simetrías que dejan ese problema inalterado:

$$\forall g \in G_{\mathcal{K}},\ g\text{ }s\left( \mathcal{K} \right) = s\left( \mathcal{K} \right).$$

**Demostración.**

Para $g\mathcal{K = K}$:

$$s\left( \mathcal{K} \right) = s\left( g\mathcal{K} \right) = g\text{ }s\left( \mathcal{K} \right).$$

$$\square$$

Por tanto, se necesita:

$$Fr\left( C_{\mathcal{K}} \right) \cap Fix\left( G_{\mathcal{K}} \right) \neq \varnothing,$$

donde $Fix\left( G_{\mathcal{K}} \right)$contiene los puntos fijos comunes de todo el estabilizador.

**Contraejemplo de uso incorrecto 9.3. Elegir un nombre manteniendo una simetría que lo intercambia.**

Supongamos que la frontera es exactamente:

$$\left\{ a,b \right\},$$

y existe una simetría del problema que intercambia $a$y $b$.

Ninguno queda fijo. Por tanto, ningún selector equivariante puede estar definido en ese problema.

Sí puede conservarse la frontera como resultado, dejando allí indefinida la selección.

Incorporar una prioridad como dato adicional puede reducir las simetrías del problema enriquecido. Esa es una regla diferente, que debe declararse y transportarse junto con los demás datos.

**Teorema 9.9. Construcción de un selector equivariante en una familia finita.**

Consideremos una familia finita de problemas estable bajo la acción. Supongamos que en cada problema existe un maximal fijo por su estabilizador.

Entonces puede construirse un selector equivariante sobre esa familia.

**Demostración.**

Elegimos un representante $r$de cada órbita y un elemento:

$$a_{r} \in Fr\left( C_{r} \right)$$

fijo por su estabilizador.

Para un problema $\mathcal{K}$de esa órbita, tomamos $g$con:

$$gr = \mathcal{K,}$$

y definimos:

$$s\left( \mathcal{K} \right) = ga_{r}.$$

Si también $hr = \mathcal{K}$, entonces $h^{- 1}g$estabiliza $r$. Por tanto:

$$h^{- 1}ga_{r} = a_{r},$$

y:

$$ga_{r} = ha_{r}.$$

La definición no depende del transportador elegido. El transporte de fronteras acredita la pertenencia y la misma identidad demuestra equivarianza. $\square$

El teorema demuestra existencia bajo sus hipótesis. No afirma que exista una única regla de selección posible.

**12. Ejemplo integrado: agua, hábitat y presupuesto**

Consideremos un modelo sintético con:

$$H = 2,$$

y exactamente tres políticas:

$$\Pi = \left\{ \pi_{agua},\pi_{h\overset{ˊ}{a}bitat},\pi_{ambas} \right\}.$$

Todas parten del mismo origen $o$, sin servicios instalados. En $t = 1$instalan los servicios correspondientes y los conservan en $t = 2$.

Hay dos escenarios comunes:

$$\xi_{regular},\ \xi_{estr\overset{ˊ}{e}s},$$

con exactamente una realización por política y escenario, y masas:

$$\frac{3}{4},\ \frac{1}{4}.$$

Los registros están completos y sus correspondencias están fijadas.

**Capacidad generativa y funcionalidad.**

Sean $g_{a},g_{h},g_{ah}$identidades organizacionales distintas.

Cada trayectoria generativa tiene la forma:

$$\left( o,g_{\pi},g_{\pi} \right).$$

Con receta $hold,1$, robustez y la familia singleton de cada política:

  -----------------------------------------------------------------------------------------
  **Política**   **CAG**                         **Perfil funcional en** $t = 2$
  -------------- ------------------------------- ------------------------------------------
  Agua           $$\left\{ o,g_{a} \right\}$$    $$\left( 1,0 \right)$$

  Hábitat        $$\left\{ o,g_{h} \right\}$$    $$\left( 0,1 \right)$$

  Ambas          $$\left\{ o,g_{ah} \right\}$$   $$\left( 1,1 \right)$$
  -----------------------------------------------------------------------------------------

Las coordenadas funcionales indican agua y hábitat.

Que $g_{ah}$contenga organizacionalmente ambos servicios no implica que la trayectoria haya realizado las identidades completas $g_{a}$y $g_{h}$.

Por tanto:

$$\left\{ o,g_{a} \right\} \subseteq \not{}\left\{ o,g_{ah} \right\},$$

y:

$$\left\{ o,g_{h} \right\} \subseteq \not{}\left\{ o,g_{ah} \right\}.$$

Los tres CAG son incomparables por inclusión.

**Bienestar.**

Existen dos portadores identificados, $\mathcal{l}_{1},\mathcal{l}_{2}$, durante los tres tiempos. Cada uno tiene una dimensión medida en el orden $0 \preceq 1$.

Sus trayectorias son:

  ----------------------------------------------------------------------------------------------------
  **Política**   **Perfil personal de** $\mathcal{l}_{1}$   **Perfil personal de** $\mathcal{l}_{2}$
  -------------- ------------------------------------------ ------------------------------------------
  Agua           $$\left( 0,1,1 \right)$$                   $$\left( 0,0,0 \right)$$

  Hábitat        $$\left( 0,0,0 \right)$$                   $$\left( 0,1,1 \right)$$

  Ambas          $$\left( 0,1,1 \right)$$                   $$\left( 0,1,1 \right)$$
  ----------------------------------------------------------------------------------------------------

Estos índices de bienestar son distintos de las coordenadas funcionales, aunque coincidan algunos números.

Los perfiles son iguales entre los dos escenarios de cada política. El escenario permanece registrado y modifica la exigencia de la tarea.

**Tarea y PVS.**

La tarea sintética exige, para el tramo $t = 1,2$:

-   en escenario regular, disponer de al menos uno de los servicios;

-   en estrés, disponer de ambos.

Como los servicios se conservan entre esos tiempos, la condición puede leerse desde los indicadores terminales $A_{2},H_{2}$:

$$\Phi(e) = \left\{ \begin{matrix}
A_{2}(e) \vee H_{2}(e), & \xi = regular, \\
A_{2}(e) \land H_{2}(e), & \xi = estr\overset{ˊ}{e}s.
\end{matrix} \right.\ $$

Con esa tarea y evaluación completa:

$${PVS\left( \pi_{agua} \right) = \frac{3}{4},
}{PVS\left( \pi_{h\overset{ˊ}{a}bitat} \right) = \frac{3}{4},
}{PVS\left( \pi_{ambas} \right) = 1.}$$

**Restricción presupuestaria.**

El problema de selección declara un presupuesto autorizado de una unidad por instante:

$$d\left( e,t \right) \leq 1$$

en todas las realizaciones y tiempos.

Las demandas son:

  ------------------------------------------------------------------------
  **Política**   **Demanda en** $t = 0,1,2$           **Restricción**
  -------------- ------------------------------------ --------------------
  Agua           $$\left( 0,1,1 \right)$$             Cumple

  Hábitat        $$\left( 0,1,1 \right)$$             Cumple

  Ambas          $$\left( 0,2,2 \right)$$             Refutada
  ------------------------------------------------------------------------

Es una cota instantánea de elegibilidad. No se suman sus valores entre tiempos ni se ponderan con probabilidades.

La política «ambas» sigue siendo causalmente realizable en este modelo, pero queda excluida por el presupuesto autorizado.

El presupuesto no forma parte de la $\Phi$anterior. Por eso es coherente que:

$$PVS\left( \pi_{ambas} \right) = 1$$

y, al mismo tiempo, no sea factible para esta decisión.

Si se incorporara el presupuesto dentro de $\Phi$, se definiría otra tarea y habría que recalcular su PVS.

**Frontera integrada.**

El conjunto factible es:

$$A_{feas} = \left\{ \pi_{agua},\pi_{h\overset{ˊ}{a}bitat} \right\}.$$

Sus CAG, perfiles funcionales e historias de bienestar son incomparables. Sus PVS coinciden.

Por tanto:

$$\boxed{Fr\left( A_{feas} \right) = \left\{ \pi_{agua},\pi_{h\overset{ˊ}{a}bitat} \right\}.}$$

Esta frontera es exhaustiva para la familia declarada de tres políticas.

Los datos no determinan una elección única entre sus dos miembros. Tampoco justifican afirmar que «ambas» domina al resto: su CAG no contiene los otros repertorios.

**13. Construcción efectiva y salida del módulo**

En una presentación finita con valores exactos y comparaciones efectivas, el procedimiento es:

1.  Validar identidades, ámbitos y procedencia de las valoraciones.

2.  Resolver los certificados de restricciones sin confundir ausencia con refutación.

3.  Certificar los dominios y preórdenes de los criterios.

4.  Construir la relación integrada sobre el bloque.

5.  Conservar exactamente las alternativas sin dominador estricto.

6.  Comprobar el alcance global declarado.

7.  Aplicar una regla de selección cuando esté definida y respete las invariancias exigidas.

La terminación se sigue de la finitud de las tablas y de sus operaciones. La finitud de un conjunto pretendido no convierte en terminante cualquier programa que se presente como su comparador.

La salida conserva:

$$\boxed{\begin{array}{r}
\text{factibilidad~y~}\text{diagn}\overset{ˊ}{\text{o}}\text{sticos}, \\
\text{bloque~y~relaci}\overset{ˊ}{\text{o}}\text{n~de~comparaci}\overset{ˊ}{\text{o}}\text{n}, \\
\text{frontera~y~alcance~certificado}, \\
\text{selecci}\overset{ˊ}{\text{o}}\text{n,~cuando~est}\overset{ˊ}{\text{a}}\text{~definida}.
\end{array}}$$

Una frontera plural puede ser una respuesta matemática completa para el problema de maximalidad. La elección única conserva su propia regla, dominio y justificación.

**La siguiente entrega es el teorema de integración de los módulos 0--VII: construcción conjunta, coherencia y alcance del cierre.**

**Entrega 10 --- Teorema de integración de los módulos 0--VII: construcción, coherencia y alcance del cierre**

Esta entrega demuestra **bajo qué condiciones los módulos forman una única construcción matemática**, con resultados compatibles y una frontera de decisión correctamente obtenida.

La integración debe conservar tres cosas:

$$\boxed{\text{significado,~dominio~y~procedencia~de~cada~resultado}}$$

No basta con calcular correctamente cada módulo por separado. También debe comprobarse que sus resultados describen la misma instancia, las mismas políticas y las realizaciones pertinentes.

**1. La instancia integrada**

**Definición 10.1. Instancia finita de integración.**

Una instancia se representa por:

$$\mathcal{I =}\left( \mathfrak{M},\beta,\gamma,c_{0},H,\Pi,\mathcal{D} \right),$$

donde:

-   $\mathfrak{M}$es el marco;

-   $\beta$es el modelo;

-   $\gamma$es el contexto efectivo;

-   $c_{0}$es la condición inicial realizada;

-   $H\mathbb{\in N}$es el horizonte;

-   $\Pi$es la familia finita completa de políticas del problema;

-   $\mathcal{D}$reúne los datos de representación, significado, evaluación y comparación.

Para el teorema principal utilizaremos una familia no vacía:

$$\Pi \neq \varnothing.$$

Cada política pertenece al proceso declarado y actúa mediante su información legítima:

$$a_{t} = \pi_{t}\left( \iota_{t} \right).$$

Los datos adicionales comprenden:

  ----------------------------------------------------------------------------------------------------
  **Componente**   **Datos requeridos**
  ---------------- -----------------------------------------------------------------------------------
  Inicialización   Historias iniciales, estado, información, contexto y referencias correspondientes

  Funcionalidad    $\Sigma$, funciones, perfiles, dominios y calibraciones

  Multiescala      Puertos, relaciones conjuntas, vistas y recursos compartidos

  CAG              Identidades, traducción, conservación, receta y cuantificadores

  Bienestar        Reloj, portadores, dimensiones, mediciones y reglas comparativas

  Viabilidad       Referencias semánticas, tarea $\Phi$, lectores y protocolo de evidencia

  Probabilidad     Leyes del experimento y sus condiciones de normalización

  Decisión         Restricciones hard, criterios, alcance y regla de selección cuando se utiliza
  ----------------------------------------------------------------------------------------------------

Los certificados se obtienen comprobando esos datos. Una etiqueta que afirme «fiel», «suficiente» o «completo» no sustituye las igualdades y coberturas correspondientes.

**2. Alcance preciso de la ruta integrada**

El teorema que sigue utiliza una ruta concreta:

1.  Todas las realizaciones alcanzan el horizonte $H$.

2.  Existe un conjunto finito común de escenarios:

$$\Xi \neq \varnothing.$$

3.  Para cada política existe una biyección verificada:

$$e_{\pi}:\Xi F_{\pi},$$

donde:

$$F_{\pi} = \mathfrak{F}_{H,\gamma}^{poss}\left( c_{0},\pi \right).$$

Escribimos:

$$e_{\pi,\xi} = e_{\pi}(\xi).$$

Por tanto, cada par $\left( \pi,\xi \right)$identifica exactamente una realización de esta ruta.

Esta unicidad es una condición del ensamblaje presentado. El Módulo V general sigue admitiendo varias realizaciones por escenario y terminaciones anticipadas.

La correspondencia se comprueba contra los árboles completos. Compartir el nombre de un escenario no acredita una correspondencia entre ejecuciones.

Las comparaciones entre políticas conservan ambas claves:

$$RunKey\left( e_{\pi,\xi} \right),\ RunKey\left( e_{\sigma,\xi} \right).$$

Son claves diferentes porque identifican políticas diferentes.

**3. Procedencia común de las afirmaciones**

**Definición 10.2. Registro integrado de una política.**

Cada política conserva un registro:

$$\mathcal{R}_{\pi} = \left( \kappa_{\pi},Q_{\pi},F_{\pi},C,A,G_{\pi},\mathcal{O}_{\pi},\mathcal{W}_{\pi},V_{\pi},\mathbb{P}_{\pi}{VProb}_{\pi}\mathcal{H}_{\pi} \right),$$

con:

$$\kappa_{\pi} = \left( \mathfrak{M},\beta,\gamma,c_{0},\pi,H \right).$$

Aquí:

-   $Q_{\pi}$contiene todas las consultas causales;

-   $\mathcal{O}_{\pi}$conserva los perfiles funcionales pertinentes;

-   $\mathcal{W}_{\pi}$conserva los registros de bienestar;

-   $V_{\pi}$es el evaluador parcial;

-   $\mathbb{P}_{\pi}$es la ley de esa política;

-   $\mathcal{H}_{\pi}$conserva los certificados de restricciones.

Los conjuntos agregados mantienen sus testigos. El conjunto CAG, por ejemplo, no sustituye los registros que indican qué realizaciones y tiempos justifican cada logro.

**Contraejemplo de uso incorrecto 10.1. Ensamblar logros de políticas diferentes.**

Supongamos:

$${C\left( \pi_{a} \right) = 1,\ W\left( \pi_{a} \right) = 0,
}{C\left( \pi_{b} \right) = 0,\ W\left( \pi_{b} \right) = 1.}$$

Entonces:

$$\left( \exists\pi\text{ }C(\pi) \right) \land \left( \exists\pi\text{ }W(\pi) \right)$$

es verdadero.

Pero:

$$\exists\pi\text{ }\left\lbrack C(\pi) \land W(\pi) \right\rbrack$$

es falso en esa familia.

La integración exige mantener la misma política dentro de una afirmación conjunta. Cuando la afirmación se refiere a una ejecución concreta, también mantiene esa misma ejecución.

**4. Construcción sin dependencias circulares**

Los datos se organizan mediante un grafo finito de dependencias.

Cada constructor recibe primitivas fijadas o resultados de constructores anteriores. Por ejemplo:

-   los futuros causales se construyen antes de evaluar sus resultados;

-   el CAG se obtiene de esos futuros y de su receta;

-   el bienestar se registra sobre sus ejecuciones;

-   los veredictos se obtienen mediante referencias y certificados;

-   las masas se calculan con la ley del experimento;

-   la frontera utiliza las valoraciones y restricciones correspondientes.

Una tarea puede consumir un CAG previamente construido. Ese CAG no puede haberse definido eliminando previamente los futuros que la misma tarea rechazaría.

**Teorema 10.1. Determinación por dependencias acíclicas.**

Sea $G = \left( N,E \right)$un grafo dirigido finito sin ciclos.

Cada nodo $v$tiene un constructor determinista:

$$F_{v}:\prod_{u \in pa(v)}^{}\mathsf{Registro}_{u} \longrightarrow \mathsf{Registro}_{v}.$$

Supongamos que:

1.  los datos primitivos permanecen fijos;

2.  cada constructor tiene un significado y un dominio precisos;

3.  sus resultados no dependen de estado externo mutable ni del orden de consulta;

4.  los registros distinguen valores definidos, ausencia de dominio e invalidez.

Entonces existe una única asignación de registros que satisface:

$$r_{v} = F_{v}\left( \left( r_{u} \right)_{u \in pa(v)} \right).$$

Cualquier evaluación en orden topológico produce esa asignación.

**Demostración.**

Los nodos sin dependencias reciben únicamente primitivas fijadas, por lo que sus registros están determinados.

Supongamos determinados los registros anteriores a un nodo. Sus argumentos son entonces los mismos en cualquier orden topológico, y el mismo constructor produce el mismo resultado.

La inducción sobre el orden topológico determina todos los nodos. $\square$

Esta independencia corresponde al orden de cálculo del expediente. La secuencia causal de acciones de cada política permanece fija.

La aciclicidad tampoco demuestra por sí sola la corrección de los constructores. Esa corrección procede de los teoremas de los módulos y de sus hipótesis verificadas.

**5. La parcialidad se conserva por componente**

Un registro correctamente definido puede contener una función parcial.

Por ejemplo:

$$V_{\pi}:Q_{\pi} \rightharpoonup \left\{ 0,1 \right\}$$

puede estar correctamente construido aunque algunas consultas no tengan veredicto.

Tampoco se impone una propagación uniforme de cualquier ausencia a todos los resultados posteriores:

-   la indisponibilidad de la vía completa no impide una vía decisiva válida;

-   la ausencia de traducción futura no borra un origen representado disponible;

-   una hoja con veredicto indefinido y masa cero puede coexistir con PVS definida.

Cada constructor especifica qué datos requiere y cómo trata sus estados.

Una invalidez compartida que afecta a las premisas de una prueba no puede descartarse como si fuera una ausencia opcional.

**Distinción esencial.**

Que el cálculo produzca un diagnóstico determinado no significa que el valor consultado esté definido.

La teoría puede determinar correctamente:

$$V_{\pi}(h)\text{~fuera~de~dominio}.$$

Eso no equivale a:

$$V_{\pi}(h) = 0.$$

**6. Hipótesis del teorema de ensamblaje**

Para obtener todos los resultados comparativos de esta ruta, se acreditan las siguientes condiciones.

**a. Causalidad e inicialización.**

La condición inicial está realizada; el estado y la información son suficientes para continuar; las políticas pertenecen a la familia declarada y son ejecutables con su información legítima.

Los árboles incluyen todas sus ramas y satisfacen la correspondencia con $\Pi \times \Xi$.

**b. Funcionalidad.**

Los perfiles requeridos están definidos y calibrados en espacios comunes.

La representación propuesta para reducirlos satisface cobertura, saturación de dominio y constancia sobre sus fibras.

**c. Multiescala.**

Las vistas conservan los puertos y las claves correspondientes. Su recomposición coincide exactamente con la relación conjunta.

Las demandas de recursos tienen identidades y unidades compatibles.

**d. Capacidad generativa.**

Todas las identidades y relaciones que utiliza la receta tienen traducción y significado acreditados.

El CAG de cada política se calcula con su familia singleton:

$$\left\{ \pi \right\},$$

conservando todas sus realizaciones.

**e. Bienestar.**

Cada ejecución conserva su reloj completo y su soporte de portadores.

En esta ruta se exige medición completa:

$$D_{\pi,\xi}^{W} = I_{\pi,\xi}^{W},$$

también para las políticas que posteriormente incumplan una restricción presupuestaria.

Los registros que se comparan comparten los soportes, índices y calibraciones exigidos por la regla.

**f. Evidencia y probabilidad.**

Las referencias semánticas y la tarea pueden ser parciales:

$${J_{task}:D_{J} \subseteq F_{\pi} \longrightarrow \mathcal{P}_{+}\left( S_{viab} \right),
}{\Phi:D_{\Phi} \subseteq S_{viab} \longrightarrow \left\{ 0,1 \right\}.}$$

El evaluador utiliza el protocolo declarado. Cada ley es legítima.

Para esta construcción comparativa completa se exige:

$$PVS_{\pi} \downarrow \ \text{para~toda~}\pi \in \Pi.$$

Esto no exige que $V_{\pi}$esté definido en todas las consultas, ni siquiera en todas las hojas de masa cero.

**g. Restricciones y comparación.**

Las restricciones hard están decididas sin contradicciones. Los cuatro criterios utilizados comparten el ámbito comparativo requerido.

La familia objetivo de políticas está cubierta por completo.

Estas son hipótesis suficientes para la ruta fuerte presentada. Los módulos individuales conservan sus dominios más amplios.

**7. Teorema principal de integración**

**Teorema 10.2. Ensamblaje correcto de los módulos 0--VII.**

Si una instancia satisface las condiciones anteriores, la construcción entrega simultáneamente:

1.  todos los árboles causales de sus políticas;

2.  una reducción funcional exacta en el dominio comprobado;

3.  una descomposición multiescalar exacta y certificados de recursos sobre todas las consultas;

4.  los CAG correspondientes a cada política y receta;

5.  los registros completos de bienestar;

6.  los evaluadores parciales, las leyes, las triparticiones y las PVS correspondientes;

7.  la frontera exacta del conjunto factible declarado bajo el producto de los cuatro criterios.

Si el conjunto factible es no vacío, su frontera es no vacía.

Una selección única se obtiene cuando una regla de selección declarada satisface sus propias condiciones.

**Demostración.**

**Paso 1. Cobertura causal.**

El Módulo V construye la raíz realizada y todos los resultados de cada fila causal utilizada por la política.

La inducción sobre la profundidad demuestra corrección y cobertura. Las hojas corresponden exactamente a las realizaciones completas.

En la ruta presente, todas alcanzan $H$, y la biyección con $\Xi$identifica cada realización sin eliminar ninguna.

Las claves de ocurrencia permiten comprobar que cada registro posterior pertenece al experimento correspondiente.

**Paso 2. Reducción funcional.**

Sea $P$el conjunto de puntos estado--tiempo alcanzados por los árboles.

Definimos, en su dominio:

$$\psi\left( x,t \right) = \left( \Sigma,(x)t \right),$$

y:

$$f\left( x,t \right) = O\left( x,t \right).$$

El Módulo 0 exige explícitamente:

$$D_{f} \subseteq D_{\psi},$$

la saturación de $D_{f}$en las fibras de $\psi$y la constancia de $f$en cada fibra definida.

Se obtiene el factor canónico:

$$\overline{f}\left( \psi\left( x,t \right) \right) = f\left( x,t \right),$$

con:

$$D_{\overline{f}} = \psi\left( D_{f} \right).$$

La constancia acredita independencia del representante. La saturación acredita igualdad de dominios.

Por tanto:

$$f = \overline{f} \circ \psi.$$

La conclusión se refiere a esta consulta y a los puntos alcanzados. Los estados causales originales se conservan para las demás evaluaciones.

**Paso 3. Multiescala y recursos.**

Para cada política se construye una relación conjunta $R_{\pi}$con las claves de todas sus consultas.

Las vistas son proyecciones de esa relación. La igualdad comprobada:

$$R_{\pi} = \bowtie_{j}{pr}_{j}\left( R_{\pi} \right)$$

acredita recomposición exacta con sus claves y puertos compartidos.

Para cada recurso $\rho$y consulta $h$, se evalúa:

$$d_{\rho}(h) = \sum_{d \in D_{\rho}(h)}^{}c_{d}(h),$$

con demandas identificadas y unidades comunes.

El presupuesto de trayectoria es:

$$\forall h \in Q_{\pi}\text{\:\,}\forall\rho:d_{\rho}(h) \leq B_{\rho}.$$

La raíz está incluida. La cota instantánea se comprueba en cada tiempo; no se transforma en una suma temporal.

Una refutación modifica la factibilidad para seleccionar la política, sin borrar su árbol ni sus mediciones.

**Paso 4. Capacidad generativa.**

El Módulo III traduce primero las trayectorias y las relaciones organizacionales utilizadas.

Sus recetas calculan exactamente los conjuntos:

$$Ach_{r}\left( e_{\pi,\xi} \right).$$

Para una política fija:

$${G_{\pi,r}^{poss} = \bigcup_{\xi \in \Xi}^{}Ach_{r}\left( e_{\pi,\xi} \right),
}{G_{\pi,r}^{rob} = \bigcap_{\xi \in \Xi}^{}Ach_{r}\left( e_{\pi,\xi} \right).}$$

La no vaciedad de $\Xi$impide interpretar una intersección sin realizaciones como garantía.

El origen se añade según la definición canónica del CAG. Sus testigos futuros permanecen separados de esa pertenencia estructural.

La traducción precede a la intersección robusta y la política permanece fija.

**Paso 5. Bienestar.**

El Módulo IV obtiene el reloj de cada ejecución y conserva:

$$\widetilde{W}\left( e_{\pi,\xi} \right) = \left( E_{\pi,\xi}^{T},S_{\pi,\xi}^{L},I_{\pi,\xi}^{W},D_{\pi,\xi}^{W},w_{\pi,\xi} \right).$$

La completitud exigida y la compatibilidad del bloque permiten comparar los mismos portadores, tiempos y dimensiones.

El producto de sus órdenes es un preorden. Exigirlo para todos los escenarios vuelve a producir un preorden.

Una diferencia intermedia de bienestar permanece registrada aunque los estados finales coincidan.

**Paso 6. Veredictos y masas.**

Para cada consulta, el Módulo VI construye su semántica solo cuando todas las completaciones pertinentes tienen las referencias requeridas.

Un certificado aceptado contiene esa semántica, está dentro de $D_{\Phi}$y tiene un único veredicto.

La no vaciedad semántica demuestra que dos certificados correctos no pueden dar valores opuestos.

La ley conserva masa al propagarse por el árbol. Las hojas quedan particionadas y:

$$M_{\pi}^{+} + M_{\pi}^{-} + M_{\pi}^{?} = 1.$$

La condición de PVS da:

$$M_{\pi}^{?} = 0,\ PVS_{\pi} = M_{\pi}^{+}.$$

Las hojas de masa cero permanecen en el experimento y mantienen sus propios estados de evaluación.

**Paso 7. Orden integrado.**

La relación entre políticas es:

$$\pi \succeq_{\mathcal{I}}\sigma$$

si y solo si se cumplen conjuntamente:

$${CAG_{\sigma} \subseteq CAG_{\pi},
}{\forall\xi \in \Xi:O_{\pi,\xi}(H) \succeq_{DFR}O_{\sigma,\xi}(H),
}{\forall\xi \in \Xi:\widetilde{W}\left( e_{\pi,\xi} \right) \succeq_{W}\widetilde{W}\left( e_{\sigma,\xi} \right),
}{PVS_{\pi} \geq PVS_{\sigma}.}$$

Cada componente es un preorden en el bloque común. Su intersección también lo es.

Sea:

$$\Pi_{feas} = \left\{ \pi \in \Pi:\text{todas~sus~restricciones~hard~est}\overset{ˊ}{\text{a}}\text{n~acreditadas} \right\}.$$

La construcción conserva exactamente:

$$Fr\left( \Pi_{feas} \right) = \left\{ \pi, \in \Pi_{feas}:\neg\exists\sigma \in \Pi_{feas}\text{~}\sigma \succ_{\mathcal{I}}\pi \right\}.$$

Como la familia objetivo está cubierta, esta frontera es exhaustiva respecto de ella.

La finitud y la no vaciedad del conjunto factible garantizan al menos un maximal.

**Paso 8. Composición.**

Todos los pasos utilizan la misma instancia, las claves correspondientes y las correspondencias verificadas entre escenarios.

Las conclusiones anteriores se obtienen sin intercambiar políticas, realizaciones, dominios ni significados. Por tanto, se cumplen simultáneamente las afirmaciones del teorema. $\square$

**8. La suficiencia de una representación no se extiende automáticamente**

**Contraejemplo de uso incorrecto 10.2. Utilizar un resumen funcional como estado suficiente para la tarea.**

Consideremos dos estados terminales:

$${x_{r} = \left( 1,0,regular \right),
}{x_{s} = \left( 1,0,estr\overset{ˊ}{e}s \right).}$$

La representación:

$$\psi\left( a,h,\xi \right) = \left( a,h \right)$$

conserva exactamente el perfil funcional:

$$O = \left( a,h \right).$$

Sin embargo, si la tarea exige algún servicio en escenario regular y ambos en estrés:

$$\Phi\left( x_{r} \right) = 1,\ \Phi\left( x_{s} \right) = 0.$$

Como:

$$\psi\left( x_{r} \right) = \psi\left( x_{s} \right),$$

la tarea no factoriza por esa representación.

El factor funcional está correctamente construido. La inferencia incorrecta consistiría en atribuirle también una suficiencia semántica que no se demostró.

La integración conserva el estado o la referencia adicional necesaria para evaluar el escenario.

**9. Terminación efectiva**

**Teorema 10.3. Terminación relativa a la presentación finita.**

Supongamos que todos los datos utilizados se presentan mediante:

-   tablas finitas explícitas;

-   dominios decidibles;

-   valores con igualdad y comparación efectivas;

-   operaciones exactas;

-   o construcciones adicionales con terminación demostrada.

Entonces el procedimiento integrado termina con los valores que puede certificar y los diagnósticos correspondientes a las obligaciones no satisfechas.

Bajo las hipótesis del teorema principal devuelve sus resultados correctos.

**Demostración.**

Los árboles tienen profundidad acotada por $H$y ramificación finita. Por inducción, contienen un número finito de nodos.

Las verificaciones restantes recorren conjuntos y tablas finitos: fibras de representaciones, vistas, ventanas temporales, referencias, masas, restricciones y comparaciones.

Las operaciones aritméticas y de igualdad están comprendidas en la clase efectiva declarada.

El grafo de dependencias contiene un número finito de constructores. La composición de estas evaluaciones terminantes también termina. $\square$

La finitud de una descripción no garantiza por sí sola la terminación de un programa arbitrario que esa descripción contenga.

Tampoco basta devolver siempre un diagnóstico: cuando las guardas están satisfechas, el procedimiento debe construir los valores correctos, como demuestra el teorema de ensamblaje.

**10. Una instancia que satisface las hipótesis**

Para mostrar que el dominio del teorema no es vacío, completamos la instancia sintética de agua y hábitat.

**Proceso y políticas.**

Sea:

$$H = 2,\ \Xi = \left\{ r,s \right\},$$

con $r$regular y $s$estrés.

El estado inicial es $x_{0}$, sin servicios. Los estados posteriores tienen la forma:

$$\left( B,\xi \right),$$

donde:

$$B \in \left\{ \left\{ a \right\},\left\{ h \right\},\left\{ a,h \right\} \right\},\ \xi \in \left\{ r,s \right\}.$$

En $t = 0$, las tres acciones disponibles instalan uno de esos conjuntos $B$.

Cada instalación tiene dos resultados causales: $\left( B,r \right)$y $\left( B,s \right)$, con etiquetas distintas.

En $t = 1$, la única continuación permitida es mantener $B$hasta $t = 2$.

Las políticas son exactamente las tres elecciones iniciales seguidas de mantenimiento:

$$\Pi = \left\{ \pi_{a},\pi_{h},\pi_{ah} \right\}.$$

Así, la familia declarada queda completamente cubierta.

Las dos ramas de instalación pueden producir la misma observación. La política posterior sigue siendo legítima porque en ambas utiliza la misma acción de mantenimiento.

Para cada política hay una raíz, dos nodos en $t = 1$y dos hojas en $t = 2$.

**Inicialización y referencias.**

Se utiliza una única historia inicial $h_{0}$:

$$b\left( h_{0} \right) = c_{0},\ s\left( h_{0} \right) = x_{0},\ i\left( h_{0} \right) = \iota_{0}.$$

El contexto es de tipo $pre$, común a las tres políticas.

Los puentes iniciales y de régimen se toman como identidades sobre sus registros declarados. Para cada registro $z$, ambos intérpretes utilizan:

$$J(z) = \left\{ z \right\}.$$

Esto acredita, en esta instancia formal, sus coberturas y fidelidades.

**Representación y funcionalidad.**

Definimos:

$$\Sigma\left( x_{0} \right) = \varnothing,\ \Sigma\left( B,\xi \right) = B.$$

El perfil funcional es:

$$O\left( x,t \right) = \left( 1,\left\lbrack a \in \Sigma(x) \right\rbrack 1\left\lbrack h \in \Sigma(x) \right\rbrack \right).$$

Los dos espacios de valores son $\left\{ 0,1 \right\}$con el orden usual y calibración identidad.

El perfil depende únicamente de $\Sigma(x)$, por lo que factoriza por:

$$\psi\left( x,t \right) = \left( \Sigma,(x)t \right).$$

**Identidad generativa.**

La identidad generativa es el propio conjunto de servicios, con equivalencia por igualdad y conservación por inclusión.

La traducción nativa--común es la identidad.

Cada traza generativa es:

$$\left( \varnothing,B,B \right).$$

Por tanto, para $hold,1$robusto:

$$CAG_{\pi_{B}} = \left\{ \varnothing,B \right\}.$$

**Vistas y recursos.**

En cada consulta se registran, con su clave:

$$A = 1\lbrack a \in B\rbrack,\ H_{b} = 1\lbrack h \in B\rbrack,$$

y las demandas:

$$d_{a} = A,\ d_{h} = H_{b}.$$

Las vistas de agua y hábitat conservan la misma clave de consulta. Su unión natural reconstruye exactamente el registro conjunto.

El presupuesto instantáneo es:

$$d_{a} + d_{h} \leq 1.$$

En la raíz, ambas demandas son cero. Después de instalar, las políticas individuales demandan una unidad y la conjunta demanda dos.

**Bienestar.**

Existen dos portadores durante los tres tiempos:

$$L = \left\{ \mathcal{l}_{1},\mathcal{l}_{2} \right\},\ E^{T} = \left\{ 0,1,2 \right\}.$$

Cada uno tiene una dimensión binaria completamente medida:

$${w_{\mathcal{l}_{1}}(t) = A\left( x_{t} \right),
}{w_{\mathcal{l}_{2}}(t) = H_{b}\left( x_{t} \right).}$$

Se conserva:

$$D^{W} = I^{W}.$$

La regla compara los mismos portadores, tiempos y dimensiones en todas las realizaciones.

**Semántica y tarea.**

Cada hoja tiene la referencia singleton:

$$J_{task}\left( e_{B,\xi} \right) = \left\{ \left( B,\xi \right) \right\}.$$

La tarea exige, en el tramo $t = 1,2$, algún servicio en escenario regular y ambos en estrés.

Como $B$se conserva durante ese tramo, se define:

$$\Phi\left( B,\xi \right) = \left\{ \begin{matrix}
1\lbrack B \neq \varnothing\rbrack, & \xi = r, \\
1\left\lbrack \left\{ a,h \right\} \subseteq B \right\rbrack, & \xi = s.
\end{matrix} \right.\ $$

La tarea está definida en todo el espacio semántico utilizado. El protocolo admite el lector exacto de las referencias.

Los extractores y puentes factuales pueden tomarse como identidades sobre las trazas; las interpretaciones local y común coinciden. No se requiere endpoint adicional.

**Ley.**

Las ramas iniciales reciben pesos:

$$q(r) = \frac{3}{4},\ q(s) = \frac{1}{4}.$$

Cada continuación de mantenimiento tiene peso uno.

Por tanto:

  ------------------------------------------------------------------------
  **Política**           **PVS**      **Presupuesto**
  ---------------------- ------------ ------------------------------------
  $$\pi_{a}$$            $$3/4$$      Cumple

  $$\pi_{h}$$            $$3/4$$      Cumple

  $$\pi_{ah}$$           $$1$$        Refutado
  ------------------------------------------------------------------------

El conjunto factible es:

$$\Pi_{feas} = \left\{ \pi_{a},\pi_{h} \right\}.$$

Ambas políticas son incomparables en CAG, funcionalidad y bienestar. Sus PVS coinciden.

En consecuencia:

$$\boxed{Fr\left( \Pi_{feas} \right) = \left\{ \pi_{a},\pi_{h} \right\}.}$$

Todos los componentes de la instancia han sido especificados. Esto proporciona un testigo concreto de que las hipótesis del ensamblaje pueden satisfacerse conjuntamente.

**11. Un cálculo correcto puede conservar consultas indeterminadas**

La instancia anterior permite una distinción adicional.

Para la política de agua, en la raíz:

$$Sem\left( h_{0} \right) = \left\{ \left( \left\{ a \right\},r \right),\left( \left\{ a \right\},s \right) \right\}.$$

Los dos significados tienen veredictos diferentes:

$$\Phi\left( \left\{ a \right\},r \right) = 1,\ \Phi\left( \left\{ a \right\},s \right) = 0.$$

Por tanto, el lector exacto no determina un único veredicto para esa consulta inicial:

$$h_{0} \notin D_{V_{\pi_{a}}}.$$

Sin embargo, las hojas sí están completamente evaluadas y:

$$PVS_{\pi_{a}} = \frac{3}{4}.$$

Esto muestra que pueden coexistir:

-   un proceso completamente especificado;

-   una evaluación exacta;

-   una consulta inicial sin veredicto único;

-   una PVS definida.

La indeterminación de la raíz expresa la diferencia entre sus futuros. No corresponde a una definición matemática pendiente.

**12. Qué acredita el cierre**

La integración distingue cuatro resultados.

  --------------------------------------------------------------------------------------------------------
  **Resultado**                  **Afirmación acreditada**
  ------------------------------ -------------------------------------------------------------------------
  Determinación del ensamblaje   Los mismos datos y constructores producen los mismos registros

  Corrección                     Cada resultado conserva las propiedades demostradas bajo sus guardas

  Terminación efectiva           La presentación finita declarada se evalúa en un número finito de pasos

  Exactitud de la decisión       La frontera coincide con los maximales del conjunto factible cubierto
  --------------------------------------------------------------------------------------------------------

La existencia de una selección autorizada conserva sus condiciones adicionales.

Si una política factible carece de una valoración necesaria, puede existir una frontera sobre un bloque menor. No corresponde presentar esa frontera como exhaustiva sin las pruebas de cobertura del Módulo VII.

La prueba tampoco convierte las referencias empíricas o las reglas normativas en conclusiones del algoritmo: son parte de la instancia cuya fundamentación debe acompañar a una aplicación.

El enunciado respaldado para el núcleo del manuscrito es:

**Para la clase finita de instancias y las correspondencias declaradas, los módulos 0--VII admiten una construcción integrada, determinada y efectiva. Bajo sus condiciones de dominio, fidelidad y cobertura, esa construcción conserva las realizaciones causales, produce los objetos funcionales, generativos, de bienestar y probabilísticos correspondientes, y obtiene exactamente la frontera del problema de decisión declarado.**

Ese es el alcance del cierre demostrado: composición, corrección, dominios y terminación para esta clase de instancias. La originalidad científica y la aceptación editorial requieren una evaluación distinta de estos resultados matemáticos.
