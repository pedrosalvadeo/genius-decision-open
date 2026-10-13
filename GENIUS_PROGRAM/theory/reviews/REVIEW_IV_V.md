# Revisión deductiva de MIV–MV

Fuente: snapshot GENIUS-THEORY-2026-09-23-S1, párrafos P01535–P02344. Derivado de lectura: S1_READABLE.md, secciones «Entrega 6» y «Entrega 7», leídas completas. Para localizar párrafos se usó S1_EXTRACTED.txt; para las fórmulas ambiguas de biyección y reducción se contrastó el XML/OMML original de S1_Matematica_Genius_Modulos_Astra_01.docx, contando los párrafos incluidos en tablas. La fuente no fue modificada.

Tipo de trabajo: revisión deductiva escrita y construcción de contraejemplos; no demostración mecanizada, no ejecución de tests del Kernel y no auditoría empírica. Este informe es del formalizador, no reemplaza la revisión adversarial separada ni concede por sí solo aceptación de F1.

## 1. Resultado y alcance

Se revisaron 22 definiciones numeradas (6.1–6.9 y 7.1–7.13), 14 resultados numerados con sus demostraciones (6.1–6.7 y 7.1–7.7), cinco contraejemplos numerados y dos ejemplos numerados, además de consultas, certificados y condiciones no numeradas. Los 14 argumentos son válidos bajo las hipótesis precisadas abajo. No se encontró un contraejemplo a sus conclusiones con esas hipótesis.

Se detectaron riesgos de implementación que sí destruirían esas hipótesis: escenarios arbitrariamente renombrados para forzar una biyección; fusión de ocurrencias reconvergentes; decisiones que usan estados ocultos; cobertura comprobada solo sobre el árbol aportado; desaparición de soportes vacíos; comparaciones con índices cambiantes; uso de restricciones globales para borrar futuros; inferencia de probabilidades desde reducción causal. `specification/03_CAUSAL_AND_WELFARE.md` los excluye expresamente.

FP1 adopta una restricción de software documentada: relojes 0…H, familia finita explícita de políticas, sin terminaciones anticipadas, una hoja por palabra exógena para cada política, soporte global de bienestar y mediciones racionales completas. El resto de MIV–MV conserva validez teórica revisada dentro de su propio dominio. No se afirma computabilidad de funciones arbitrarias ni adecuación de un modelo al mundo por haber tabulado sus primitivas.

## 2. Inventario de definiciones

| Definición | Fuente | Dominios, hipótesis y dependencias revisadas | Tratamiento FP1 |
|---|---|---|---|
| 6.1 Reloj | P01543–P01549 | E_e^T=D_e procede de la ejecución; termina realmente en T_e | E={0,…,H}; no relleno ficticio |
| 6.2 Existencia | P01550–P01557 | S_e^L⊆L_H(e)×E_e^T; IDs conservados entre escalas | Soporte explícito global S* |
| 6.3 Dimensiones | P01558–P01565 | I_e^W proyecta dentro de S_e^L; espacios ordenados por índice | I* común; racionales orientados y calibrados |
| 6.4 Mediciones | P01566–P01587 | D⊆I; dom(w)=D; valores tipados | D=I exigido para ruta fuerte; ausencia no es cero |
| 6.5 Bloque conservador | P01658–P01674 | Reloj, portadores, índices y calibraciones comunes; K fijo y medido | K=I*, producto adicional sobre Xi |
| 6.6 Perfil personal | P01761–P01771 | Igual cardinalidad poblacional, reloj e índices personales, soporte homogéneo, medición completa | Revisado fuera del comparador FP1 |
| 6.7 Dominancia anónima | P01772–P01777 | Una biyección B→A para toda la trayectoria; preorden personal común | No se activa por defecto |
| 6.8 Grafo | P01836–P01843 | Aristas exactamente parejas autorizadas no peores; restricciones de admisibilidad locales por arista | Teoría finita revisada; fuera de ruta FP1 |
| 6.9 Regla poblacional | P01872–P01897 | Dominio comparativo simétrico, correspondencias y no emparejados visibles; Just explícita | No extender soporte por inferencia |
| 7.1 Experimento | P01960–P01983 | M,beta,gamma,c0,pi,H distintos; Base(gamma)=beta | Clave de experimento conservada |
| 7.2 Realización inicial | P01984–P01995 | RealC0 es relación; Init produce (x0,i0); no unicidad de intervención supuesta | Inicialización realizada con premisa identificada |
| 7.3 Certificado basal | P02016–P02023 | Mapas b,s,i totales en historias basales; fibra no vacía y par constante | Verificación finita si se presenta; adecuación externa aparte |
| 7.4 Política | P02041–P02051 | pi_t:I⇀A; familia previa a resultados; memoria e información legítimas | Tabla por (tiempo,información) |
| 7.5 Fila causal | P02063–P02089 | (lambda,u,x',y'); lambda local única; U(t,i,a,y'); A_exec y A_adm separados | Todas las filas usadas completas y no vacías |
| 7.6 Ejecución | P02091–P02096 | RunKey=(kappa,palabra lambda); incluye contexto y política | Ocurrencia, no estado final |
| 7.7 Escenario | P02097–P02109 | Escenario=palabra u; Runs es conjunto, posiblemente múltiple | Fibras singleton verificadas; Xi común |
| 7.8 Árbol | P02113–P02128 | Raíz realizada; horizonte/terminación explícita; política, acciones, filas y U en todo nodo | Solo parada a H; fallos no son terminales |
| 7.9 Prefijos | P02166–P02176 | Extensión reflexiva en mismo experimento; F completo | L(h) y Q=Pref(F) certificados |
| 7.10 Régimen | P02234–P02255 | Efectos de todas las ramas; relación con fibras no vacías y significados definidos | Registro descriptivo; sin pretensión automática de reducción |
| 7.11 Reducción | P02257–P02275 | Mapas de estado/info/observación/entrada; igualdad conjunta y conmutación; políticas permitidas y paradas compatibles | Revisado fuera de sustitución nativa FP1 |
| 7.12 Monitor | P02292–P02295 | K_t⊆X con pertenencia definida; OR acumulada incluyendo raíz | Derivado opcional; no cambia controlador |
| 7.13 Destino | P02310–P02322 | Contexto, caracterización, significado y evidencia; pertenencia parcial | Predicado externo declarado, sin parada implícita |

«Revisado» en esta tabla significa que los tipos y dependencias permiten las operaciones declaradas, no que una definición pruebe que su objeto representa correctamente un fenómeno real.

## 3. Revisión de los siete resultados de MIV

### R-IV-01 — Proposición 6.1 (P01616–P01637)

**Afirmación.** I^W no determina en general S^L; S^L no determina E^T.

**Hipótesis.** Las dimensiones aplicables pueden ser vacías para un portador existente. El reloj puede incluir tiempos sin portadores. Esas posibilidades están permitidas por las definiciones 6.1–6.4.

**Verificación.** Con E={0}, I=D=∅, el registro con S=∅ y el registro con S={(l,0)}, J_{l,0}=∅ son ambos coherentes. Tienen el mismo I y distinto S. Con S={(l,0)} e I=D=∅, los relojes {0} y {0,1} también son ambos coherentes. Tienen el mismo S y distinto E. Ambos pares satisfacen las inclusiones de soporte y poseen exactamente las diferencias que afirma el resultado.

**Intento de refutación y límite.** Si una aplicación exige al menos una dimensión por cada par existente, S se puede recuperar como proyección de I. Esto no refuta el «en general»: añade una hipótesis que la teoría no impone. Análogamente, exigir un portador en cada instante haría recuperable E desde S; no es una regla del módulo.

**Dictamen.** Válido. FP1 mantiene E,S,I separados incluso cuando impone medición completa. Obligaciones CW-09 y CW-13.

### R-IV-02 — Teorema 6.2 (P01675–P01690)

**Afirmación.** El producto identificado sobre un bloque común y un único K es un preorden.

**Hipótesis.** Cada orden de valores es al menos reflexivo y transitivo. Todo registro tiene todos los valores de K, con significado/calibración comunes. K es el mismo para toda pareja y toda cadena.

**Verificación.** Para e, cada w_e(i) se compara consigo mismo. Para A≥B y B≥C, la cadena w_C(i)≤w_B(i)≤w_A(i) existe para cada mismo i∈K. Transitividad en la coordenada implica A≥C. La equivalencia mutua es reflexiva, simétrica y transitiva; si se cambian representantes equivalentes, las dos aplicaciones de transitividad preservan la relación. Por ello el cociente está bien definido y es antisimétrico.

**Contraejemplo al retirar K común.** A observa 1→1 y 3→0; B observa 1→0 y 2→1; C observa 2→0 y 3→1. Comparar solo intersecciones produce A>B, B>C y C>A. La relación resultante es cíclica; no es un contraejemplo al teorema porque cambia K entre parejas.

**Extensión FP1 justificada.** El índice fijo es Xi×I*. Repetir la prueba coordenada a coordenada preserva el preorden entre políticas. I*=∅ produce relación universal y equivalencia vacua; no se obtiene existencia.

**Dictamen.** Válido bajo hipótesis de bloque. Obligaciones CW-10, CW-11 y CW-14.

### R-IV-03 — Teorema 6.3 (P01741–P01757)

**Afirmación.** Una consulta parcial f desciende por una representación total Psi exactamente cuando su valor elevado con indefinición es constante en cada fibra.

**Hipótesis.** Psi:H_W→Z es total sobre el conjunto declarado; la marca de indefinición está fuera del codominio ordinario. La factorización se entiende como igualdad de funciones parciales, incluyendo igualdad de dominios.

**Necesidad revisada.** Si f=f_bar∘Psi como parciales y Psi(h)=Psi(h'), ambos argumentos pertenecen o no a dom(f_bar) simultáneamente. Por ello h,h' pertenecen o no a dom(f) simultáneamente; en el caso definido reciben el mismo valor.

**Suficiencia revisada.** Definir D_bar=Psi(D_f). Si z∈D_bar, escoger h∈D_f con Psi(h)=z y definir f_bar(z)=f(h). Otro representante tiene el mismo valor por constancia de la fibra. Además, si Psi(h)∈D_bar, existe h'∈D_f con la misma imagen; la constancia de la marca impone h∈D_f. Así D_f=Psi^{-1}(D_bar) y la composición coincide también en el dominio. Fuera de Psi(H_W) no se requieren valores de f_bar; esta elección parcial es suficiente.

**Contraejemplo si solo se exige valor donde ambas consultas están definidas.** H={a,b}, Psi(a)=Psi(b)=z, D_f={a}, f(a)=1. No hay dos valores definidos en conflicto, pero cualquier f_bar que defina 1 en z también haría definido f en b. La saturación de dominio es indispensable.

**Límite.** Basta una familia de consultas declarada; no se deduce reconstrucción de todo bienestar ni preservación de RunKey. Dos trayectorias (2,0,2) y (2,2,2) tienen igual final y distinta consulta «hubo valor inferior a 1».

**Dictamen.** Válido, con parcialidad explícita. Obligaciones CW-12 y de suficiencia M0. FP1 no sustituye registros por resúmenes.

### R-IV-04 — Teorema 6.4 (P01778–P01799)

**Afirmación.** La dominancia anónima por una biyección de trayectorias completas es un preorden.

**Hipótesis.** Poblaciones finitas de igual tamaño; perfiles en un mismo preorden P; biyecciones completas, una sola por comparación temporal. Si se restringen correspondencias, identidades y composición de autorizadas deben estar autorizadas en el bloque.

**Verificación.** La identidad de L_A acredita A≥A. Si f:L_B→L_A y g:L_C→L_B son testigos, f∘g es una biyección y p_C(c)≤p_B(g(c))≤p_A(f(g(c))). La transitividad personal acredita A≥C. Las correspondencias restringidas conservan la misma prueba si se satisface clausura. Renombramientos r_A,r_B transportan el testigo a r_A∘f∘r_B^{-1}; la invariancia adicional requiere que siga autorizado.

**Contraejemplo al emparejamiento temporal variable.** A={(1,0),(0,1)}, B={(1,1),(0,0)}. Las distribuciones por tiempo coinciden. A no domina B porque ninguna trayectoria de A domina (1,1). B no domina A porque sus dos trayectorias positivas parciales requerirían la única (1,1), violando inyectividad. El emparejamiento por instante cambia la regla.

**Límites revisados.** Un conjunto vacío de portadores admite la biyección vacía; no acredita existencia. La clausura por composición no prueba invariancia bajo cualquier renombramiento. La duración personal heterogénea está fuera de la definición.

**Dictamen.** Válido. Fuera del comparador FP1; no se generaliza a nacimientos/muertes ni a tamaños diferentes.

### R-IV-05 — Teorema 6.5 y certificados (P01844–P01869)

**Afirmación.** Dominancia anónima equivale a emparejamiento perfecto en el grafo completo de parejas permitidas que no empeoran.

**Hipótesis.** Igual cardinalidad n de ambos lados; todo perfil/comparación de arista está definido; las biyecciones autorizadas son exactamente las que usan aristas permitidas. Una restricción global adicional sobre el conjunto de parejas rompe esa última equivalencia y exige un contrato distinto.

**Verificación del bicondicional.** Una biyección utiliza exactamente una arista por cada vértice de ambos lados, sin repetir extremos. Es un matching perfecto. Un matching perfecto define a la inversa una función biyectiva; cada arista garantiza el no empeoramiento por construcción.

**Verificación del procedimiento y el certificado negativo.** Invertir un camino aumentante alternante iniciado y terminado en vértices libres aumenta |M| exactamente en uno y preserva que ningún vértice tenga dos aristas. Tras como máximo n aumentos, o se alcanza un matching perfecto o no hay camino aumentante. En el segundo caso, hacer búsqueda exhaustiva desde **todos** los vértices libres del lado izquierdo, R. Sea X el conjunto izquierdo alcanzado. Todo vecino de X queda alcanzado a la derecha: una arista no emparejada se recorre hacia él; si es la arista emparejada de un x no raíz, ese vecino es precisamente el predecesor por el que x fue alcanzado. Ningún vecino es libre por ausencia de camino aumentante. El emparejamiento establece biyección entre N(X) y X\R, por lo que |N(X)|=|X|−|R|<|X|. Una biyección de X en N(X) es imposible. El certificado puede comprobarse directamente enumerando X y **todos** sus vecinos.

**Contraejemplo de arista ausente por medición desconocida.** Con un portador a y uno b, borrar la arista porque falta una coordenada fabricaría un déficit 0<1. Si esa coordenada completada permite a≥b, existe matching. El déficit solo acredita imposibilidad en un grafo completo ya determinado.

**Dictamen.** Válido. No se implementa en FP1; queda un algoritmo finito correctamente especificado para un perfil futuro.

### R-IV-06 — Teorema 6.6 (P01899–P01918)

**Afirmación.** En un bloque con todas las comparaciones determinadas, reflexividad y la condición A≥B ⇒ Down(B)⊆Down(A) equivalen a preorden.

**Hipótesis.** B_L×B_L⊆D_L y todos los valores booleanos de la relación están determinados. La finitud permite verificación exhaustiva; el bicondicional lógico en sí no requiere finitud.

**Verificación.** Si A≥B y B≥C, entonces C∈Down(B)⊆Down(A), de donde A≥C. Con reflexividad esto es un preorden. Inversamente, por transitividad, todo C∈Down(B) está en Down(A) cuando A≥B. Las dos direcciones no utilizan simetría de la relación, solo la total disponibilidad de consultas del bloque.

**Contraejemplo a confundir dominio simétrico con preorden.** Sobre {A,B,C}, tomar toda la diagonal más (A,B) y (B,C), sin (A,C), con dominio completo y simétrico. La relación no es transitiva. Puede consultarse en ambos sentidos sin obedecer las leyes de orden.

**Dictamen.** Válido. La verificación de una tabla no justifica la regla normativa que produjo esa tabla. Fuera de comparador FP1.

### R-IV-07 — Proposición 6.7 (P01920–P01935)

**Afirmación.** Datos descriptivos y axiomas de preorden no determinan una única comparación entre poblaciones de tamaños distintos.

**Hipótesis.** A tiene un portador y B dos, con iguales perfiles individuales; ninguna norma adicional sobre cardinalidad está impuesta. El universo comparativo es {A,B}.

**Verificación.** R1=diagonal∪{(A,B)}, R2=diagonal∪{(B,A)} y R3=diagonal son reflexivas. En R1 cualquier composición no diagonal posible usa (A,B) junto a una diagonal y conserva (A,B); no exige (B,A). Análogo para R2; R3 es identidad. Son transitivas y distintas, y respetan exactamente los mismos datos descriptivos.

**Límite.** El resultado prueba subdeterminación por esas premisas; no que toda norma poblacional tenga la misma calidad o que ningún principio adicional pueda seleccionar una. Tampoco convierte una justificación normativa textual en evidencia empírica.

**Dictamen.** Válido. FP1 mantiene una regla explícita y soportes fijos, sin inferir compensación entre vidas.

## 4. Revisión de los siete resultados de MV

### R-V-01 — Teorema 7.1 (P02024–P02039)

**Afirmación.** Las historias de una fibra basal constante en (x0,i0) tienen los mismos conjuntos de continuaciones finitas compatibles ante las mismas entradas, bajo igual proceso, contexto y política.

**Hipótesis.** Fibra no vacía; x causalmente suficiente; memoria pertinente en i y U; mismo contexto y dinámica; misma política. La legitimidad empírica de esas hipótesis no se sigue de las igualdades tabuladas.

**Verificación.** Dos historias empiezan con el mismo par. A tiempo 0, la misma política recibe el mismo i0 y decide la misma acción. La suficiencia causal entrega la misma relación de resultados condicionada por las entradas. Para cada resultado correspondiente, la misma regla U entrega el mismo i siguiente. Inductivamente, el conjunto de pares, transiciones y prefijos de longitud n coincide para cada n finito. La multivaluación se conserva: igual relación no significa función.

**Contraejemplos al retirar hipótesis.** (a) Mismo x0, distinta memoria i0: pi puede elegir acciones diferentes. (b) Mismo par pero distinto gamma: una intervención deja el depósito lleno con suministro conectado y otra lo deja desconectado; el futuro difiere. (c) Estado insuficiente que omite una variable persistente: no se garantiza igualdad de filas de continuación.

**Límite.** La prueba se refiere a continuaciones finitas; no establece por sí sola existencia o aceptación de trayectorias infinitas. Si la fibra está vacía, la afirmación universal no certifica una realización.

**Dictamen.** Válido con premisas explícitas. Obligaciones CW-01–CW-03 y M0.

### R-V-02 — Proposición 7.2 (P02052–P02061)

**Afirmación.** Igual tiempo e información implican igual acción para una política funcional definida.

**Hipótesis.** Misma política; tiempo igual; mismo elemento del espacio I; consulta dentro de dom(pi). No se admite acción indexada adicionalmente por el estado oculto.

**Verificación.** Ambas consultas son a una misma función y con el mismo argumento `(t,i)`. La unicidad de valor de una función da igualdad. Que una ocurrencia física sea distinta no cambia el argumento informacional.

**Contraejemplo al retirar información común.** Dos ramas L y R comparten i1 y requieren respectivamente a y b para alcanzar g. Elegir a en L y b en R no es una función de (1,i1). Con pi(i1)=a una rama falla; con pi(i1)=b falla la otra. Existencia de una acción correcta en cada estado no implica existencia de una política legítima robusta.

**Límite.** Igual i en tiempos distintos puede producir acciones distintas porque pi_t puede variar. Pi puede ser parcial, pero una consulta indefinida no devuelve una acción arbitraria.

**Dictamen.** Válido. Obligaciones CW-03–CW-04.

### R-V-03 — Teorema 7.3 (P02129–P02144)

**Afirmación.** El constructor entrega exactamente todos los prefijos y todas las hojas completas del experimento; el árbol es finito.

**Hipótesis.** H finito; raíz realizada; filas finitas; toda ocurrencia no terminal tiene decisión definida, acción ejecutable/admitida, fila no vacía y actualización para cada resultado; termina exactamente por H o regla causal explícita. Las etiquetas son únicas por fila y cada resultado genera una ocurrencia.

**Corrección revisada.** Base: la raíz es Init(c0). Paso: una ocurrencia construida usa pi(t,i), las guardas de acción verificadas, un resultado perteneciente a B(t,x,a) y la información determinada por U. Por inducción, cada camino es un prefijo causal válido. La regla terminal coincide con la definición de ejecución completa.

**Cobertura revisada.** Para un prefijo válido de longitud t+1, su prefijo padre de longitud t existe por inducción. La construcción incluye cada resultado de su fila, incluido el de este prefijo. La unicidad local de lambda identifica correctamente el hijo sin borrar otros con el mismo estado. Por ello no falta ningún prefijo ni hoja.

**Finitud revisada.** Cada nivel es unión finita de conjuntos finitos de hijos de los nodos del nivel anterior; hay H+1 niveles como máximo. No se requiere un máximo global de todas las filas de un universo infinito, porque basta finitud de las alcanzadas, aunque FP1 las tabula en un universo finito.

**Contraejemplos.** Una acción con sucesores seguro e inseguro no conserva cobertura si se elimina inseguro. Un grafo cociente por estado puede fusionar dos prefijos con mismo x pero distinta memoria o genealogía; ya no representa las mismas ocurrencias. Una fila vacía no es una terminación si la semántica no la declaró así.

**Dictamen.** Válido. FP1 elimina la alternativa de terminación temprana por restricción de perfil, sin modificar el teorema general. Obligaciones CW-05–CW-08.

### R-V-04 — Teorema 7.4 (P02177–P02190)

**Afirmación.** Todo prefijo de un árbol finito certificado tiene alguna completación; Q=Pref(F).

**Hipótesis.** Árbol del teorema 7.3 con hojas auténticas por horizonte/terminación y filas no vacías en todo no terminal; completación incluye extensión reflexiva.

**Verificación.** Inducción en H−t. Una hoja se completa a sí misma. Si el nodo no es terminal, tiene al menos un hijo. Ese hijo, con menor tiempo restante, tiene una hoja descendiente; la misma hoja completa el padre. Por construcción todo prefijo de una hoja pertenece a Q; por la inducción todo nodo de Q es prefijo de alguna hoja. Esto prueba igualdad de conjuntos, no solo una inclusión.

**Contraejemplo al retirar certificación.** Un árbol finito con raíz t=0<H y una política indefinida tiene un nodo visible pero ninguna hoja causal completa. Es finito y L(raíz)=∅. Llamar «hoja» a ese bloqueo alteraría la definición de completación.

**Dictamen.** Válido. A H=0 la prueba base da una única hoja raíz y su completación. Obligación CW-08.

### R-V-05 — Proposición 7.5 (P02191–P02200)

**Afirmación.** Una subfamilia F'⊆F cubre por completaciones todas las consultas originales si y solo si F'=F.

**Hipótesis.** Se conserva Q completo, incluidas las hojas; las hojas son prefijos máximos de ese árbol; extensión reflexiva; hipótesis de 7.4.

**Verificación.** Si F'=F, 7.4 da cobertura. Si falta una hoja l∈F\F', l sigue en Q. Una hoja no tiene extensión propia en ese árbol; la única hoja que la extiende es ella misma. Ningún miembro de F' completa l. Por contraposición, cobertura completa exige F'=F.

**Límite y contraejemplo fuera de dominio.** Si se cambia Q para conservar solo la raíz, una sola hoja basta para completar esa única consulta, aunque F tenga más hojas. Eso no contradice la proposición: ha desaparecido su requisito «todas las consultas originales». Tampoco se extrapola a aceptación de lenguajes infinitos.

**Dictamen.** Válido. Impide certificar cobertura después de filtrar hojas desfavorables o nulas sin reconocer cambio de experimento. Obligaciones CW-08 y CW-15.

### R-V-06 — Teorema 7.6 (P02276–P02289)

**Afirmación.** Bajo reducción compatible, los conjuntos de trazas proyectadas de dos procesos coinciden.

**Hipótesis tipadas.** Mismos H y acciones comunes; mapas de estados Psi, información R_t, observaciones O_t e inputs eta definidos sobre todos los argumentos requeridos; inicializaciones relacionadas; políticas admitidas y compatibles; ejecutabilidad/admisibilidad y terminación conservadas; actualización conmutativa. Desde **cada representante nativo alcanzado** se exige igualdad de conjuntos de triples conjuntos, omitiendo solo lambda:

`{(eta(u),Psi(x'),O_t(y')):(lambda,u,x',y')∈B_A(t,x,a)}`

`= {(u_B,x'_B,y'_B):(lambda_B,u_B,x'_B,y'_B)∈B_B(t,Psi(x),a)}`.

La conmutación es `R_{t+1}(U_A(t,i,a,y')) = U_B(t,R_t(i),a,O_t(y'))`.

**Dirección directa.** La raíz se proyecta a la raíz. Para un prefijo nativo, compatibilidad de política da la misma acción reducida. Igualdad conjunta da una transición reducida con esos tres componentes simultáneos. Conmutación da la información reducida requerida. La inducción continúa con ese sucesor y, al conservar la parada, produce una traza completa reducida.

**Dirección inversa.** Partiendo del representante nativo ya alcanzado, tomar el siguiente resultado de una traza reducida. La igualdad de filas desde **ese** representante garantiza un resultado nativo que proyecta al triple. Elegirlo continúa el levantamiento; la conmutación conserva el par de informaciones y permite repetir. No se sustituye el representante actual por otro de la fibra para escoger una continuación conveniente. En H pasos se obtiene una traza nativa que proyecta a toda la traza reducida.

**Contraejemplo a usar solo marginales.** Los conjuntos {(u0,x0,y0),(u1,x1,y1)} y {(u0,x1,y0),(u1,x0,y1)} tienen iguales proyecciones de inputs, estados y observaciones, pero diferente asociación entre input y sucesor. Por ejemplo, la continuación (u0,x0,y0) solo existe en el primero. Igualar marginales no prueba igualdad de trazas conjuntas.

**Contraejemplo a omitir condición por representante.** Una fibra contiene x y z. Desde x solo se alcanza r, desde z solo s. El cociente ofrece r y s porque une las filas de toda la fibra. Llegar concretamente a x no habilita elegir s. La fila reducida no coincide con la proyectada desde x; el levantamiento inverso falla.

**Límites exactos.** Dos resultados nativos con distintas lambda pueden tener igual triple proyectado. Al tomar conjuntos sin etiquetas ambos colapsan en el mismo elemento, por lo que el teorema no garantiza biyección de ocurrencias ni preservación de cardinalidad de F. Tampoco conserva probabilidades: hacen falta leyes y masas de fibras. Una pareja de políticas no cubre toda la familia; hace falta una relación de políticas con cobertura. Observables CAG/bienestar necesitan sus propios mapas de preservación.

**Dictamen.** Válido bajo todas las hipótesis. FP1 conserva árboles nativos y no deriva leyes desde esta equivalencia. Obligaciones CW-06 y de suficiencia M0.

### R-V-07 — Teorema 7.7 (P02296–P02308)

**Afirmación.** m_t=1 si y solo si hubo s≤t con x_s∉K_s; una vez 1, permanece 1.

**Hipótesis.** K_s y pertenencia definidos para todos los tiempos inspeccionados; estado de cada ocurrencia conocido dentro del modelo; monitor inicial incluye t=0; actualización por disyunción, sin reinicio tácito.

**Verificación.** En t=0 la afirmación es la definición. Si m_t=OR_{s=0}^t 1[x_s∉K_s], entonces m_{t+1}=esa disyunción OR 1[x_{t+1}∉K_{t+1}], exactamente OR_{s=0}^{t+1}. Una disyunción verdadera sigue verdadera al añadir términos; por ello persiste en todas las extensiones.

**Contraejemplo a usar solo el destino.** (r,s,s) y (r,u,s) con K0={r}, K1=K2={s} terminan ambas en s; la segunda tiene m2=1. El retorno no borra la violación. Si pertenencia de u estuviera fuera de dominio, no se obtiene un monitor booleano total aplicando una suposición de seguridad.

**Límite.** m_t es evaluación de historia, no memoria accesible al controlador por definición. No modifica x, i ni pi, y solo determina inviabilidad cuando la tarea pertinente exige esa condición. Una hoja de masa cero sigue conservando m_t para una exigencia universal.

**Dictamen.** Válido. Obligación CW-15.

## 5. Inventario de ejemplos y obligaciones no numeradas

| Fuente | Contenido revisado | Resultado de la comprobación escrita |
|---|---|---|
| P01588–P01614 | Coherencia de E,S,I,D,w y distinción de desconocimiento | Inclusiones transitivas impiden medición fuera de reloj; parcialidad no invalida todo registro |
| P01638–P01656 | Existencia por tiempo y persistencia individual | ∀t∃l no implica ∃l∀t; T_req vacío no acredita existencia |
| P01692–P01719 | Contraejemplo 6.1, índices por pareja | Ciclo verificado coordenada a coordenada en R-IV-02 |
| P01721–P01740 | Ejemplo 6.1, igual final/distinta historia | (2,2,2) domina estrictamente (2,0,2); final igual no equivale a historia |
| P01800–P01834 | Contraejemplo 6.2, emparejamiento variable | Incomparabilidad de las dos poblaciones verificada en R-IV-04 |
| P01849–P01869 | Matching, augmentación y déficit | Revisados en R-IV-05; exhaustividad del grafo requerida |
| P01936–P01949 | Familias de bienestar por RunKey | La cobertura causal exige conservar cada hoja, aunque falle medición |
| P01996–P02014 | Modos pre/fix; contraejemplo 7.1 | Intervenciones de igual x0 pueden fijar mecanismos futuros distintos |
| P02145–P02164 | Diagnósticos; contraejemplo 7.2 | Ausencia de U no es fin causal; borrar rama insegura falsea cobertura |
| P02201–P02232 | Información parcial; contraejemplo 7.3 | No existe decisión uniforme ganadora entre a,b sobre mismo i1 |
| P02234–P02255 | Fidelidad de régimen | Igualdad de significados debe cubrir toda fibra; no sustituye correspondencia causal |
| P02309–P02322 | Consulta de destino | Llegada, permanencia, terminación y seguridad histórica son distintas |
| P02323–P02332 | Ejemplo 7.1, misma meta/distinta seguridad | Monitor distingue las dos trazas; masa cero no borra segunda hoja |
| P02334–P02344 | Salida e integración MV | Futuros preceden a evaluación; muerte o éxito no son paradas implícitas |

## 6. Reparaciones, precisiones y restricciones declaradas

### IVV-N1 — Normalización editorial, sin cambio matemático

P01774 presenta una fórmula cuyo extractor pierde el símbolo de biyección entre L_B y L_A. P01775–P01776 dicen explícitamente «biyección» y «la misma … en todos los tiempos y dimensiones». Se verificó el original y se fijó en el contrato la expresión inequívoca `existe una biyección f:L_B→L_A` que compara perfiles completos. No se sustituyó por una función arbitraria ni por emparejamientos por tiempo.

P02270 y P02274 presentan separadores de tuplas y argumentos degradados en el derivado de lectura. Se contrastaron con OMML original y P02271–P02275. R-V-06 reproduce la igualdad de triples conjuntos y la conmutación tipadas. Esta restitución editorial no cambia la tesis de 7.6.

### IVV-P1 — Escenarios con significado causal, no biyección arbitraria

**Problema potencial:** la sola palabra «biyección» en la ruta 10.2 podría implementarse asignando un ID nuevo por hoja aunque varias hojas compartan el mismo escenario de 7.7. Eso aparentaría satisfacer la hipótesis fuerte mediante renombramiento.

**Resolución:** construir word_u de cada hoja, comprobar imagen exacta contra Xi y cardinalidad uno de cada fibra; luego comprobar la biyección contra esa relación. Xi común usa palabras distintas de longitud H. La instancia multivaluada continúa siendo válida en MV general, pero no satisface FP1. Esto refuerza fidelidad entre 7.7 y 10.2, sin redefinir escenario.

**Impacto:** todo caso con varias hojas de una política y la misma palabra exógena requiere extensión de perfil; no se descarta una rama. A H=0, Xi es singleton de la palabra vacía. Obligación CW-07.

### IVV-P2 — Producto de bienestar entre políticas

S1 6.2 define comparación de registros; la ruta integrada necesita comparar familias por escenario. FP1 fija el índice común Xi×I* y la relación racional coordenada a coordenada. La prueba de preorden está en R-IV-02. Es una elección contractual explícita, sin ponderación probabilística ni compensación entre personas/tiempos.

**Impacto:** requiere Xi común, mismo reloj, portadores, aplicabilidad y calibración. Es más restrictivo que reglas poblacionales generales, pero su dominio y consecuencia son exactos. No necesita escoger una norma sobre nacimientos o número de vidas para implementar este perfil.

### IVV-P3 — Mediciones por ocurrencia compartida

Para evitar que un productor entregue valores diferentes de la misma ocurrencia en dos hojas que comparten prefijo, FP1 almacena medidas por `(pi,path,carrier,dimension)` y deriva los registros de hoja. Tiempo=|path|. Es una coherencia efectiva adicional del perfil. No se fusionan ocurrencias de distintas políticas ni ramas reconvergentes. Falta de una medición implica registro parcial/guarda de comparación no satisfecha, no valor cero.

### IVV-P4 — Separación de demostración formal y adecuación externa

Las tablas de realización, observación e interpretación permiten comprobar pertenencia, composición, dominios y cobertura en el modelo. Su presencia no demuestra que un sensor mida correctamente, que una intervención se haya realizado en la realidad ni que x sea un estado causal suficiente de un sistema físico. Se registran premisas y evidencia externa; no se reemplazan por un booleano de fidelidad.

## 7. Handoff al Integrador y a conformidad

Se entregan contratos CW-01–CW-16 en la Specification y pruebas revisadas R-IV-01–R-IV-07, R-V-01–R-V-07. El Integrador fija nombres y serialización globales sin debilitar los siguientes puntos:

- Igual cadena de ID no iguala tipos X e I.
- Cobertura se verifica contra B/U de todas las ramas; no solo contra el árbol presentado.
- Toda consulta causal completa tiene completación; los fallos son diagnósticos distintos de parada.
- Los escenarios son palabras u con fibras singleton en FP1 y cobertura común exacta.
- Bienestar se deriva por nodo, conserva cinco capas y exige cobertura completa para ruta fuerte.
- El producto usa siempre Xi×I*; no cambia índices por pareja ni ignora hojas nulas.
- Políticas localmente inadmisibles y políticas causalmente admitidas que fallan una restricción global no se confunden.
- CAG, bienestar y viabilidad conjuntos conservan pi y RunKey; el orden causal precede a su evaluación.

Estado final de este tramo: revisión deductiva del inventario completada; contratos escritos; casos adversariales razonados y especificados. No se ejecutó un Kernel. Aceptación integrada y cobertura de transferencia quedan a cargo de las revisiones separadas de F1.
