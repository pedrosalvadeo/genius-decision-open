# Revisión deductiva de fundamentos y módulos 0–III

Autor funcional: formalizador de fundamentos/M0–MIII. Fecha: 2026-09-23. Tramo leído: S1 P00001–P01532, completo mediante `S1_READABLE.md`, con cotejo de la estructura OMML del DOCX en expresiones problemáticas. El DOCX permanece intacto. `S1_EXTRACTED.txt` se usó para localizar párrafos, no para reconstruir fórmulas.

**Resultado:** 25 resultados numerados revisados deductivamente; 25 `REVIEWED_VALID_UNDER_HYPOTHESES` en la lectura tipada explícita. Se registran la reparación I-06 y las erratas de agrupación en `../AMENDMENTS.md`. No se encontró un contraejemplo a estos resultados bajo sus hipótesis. Se verificó la necesidad de varias hipótesis mediante contraejemplos concretos. Esto es revisión matemática asistida por IA de un tramo; no es una revisión externa humana, una prueba en asistente formal ni una garantía de ausencia absoluta de errores. La aceptación de F1 queda a cargo de la revisión separada y del Integrador.

## 1. Método y alcance

Se leyó cada definición, enunciado y demostración; se reconstruyeron las dependencias, dominios y pasos de las implicaciones. Se revisaron casos vacíos, cambios de ámbito, igualdad de funciones parciales, suficiencia de las hipótesis y pasos que requieren no vaciedad. No se tomó «prueba presente» como sinónimo de prueba correcta. No se ejecutó un Kernel ni se afirma que los casos de conformidad estén implementados por esta revisión.

El perfil `FP1_FINITE_EXACT` convierte los conjuntos, mapas, relaciones y órdenes utilizados en presentaciones finitas cerradas con operaciones decidibles. Esto es una especialización de computabilidad, no una afirmación de que todo objeto finitamente descrito sea computable. Los resultados generales conservan el ámbito que dice S1.

La evidencia se divide en: (a) igualdades y propiedades de las tablas verificables por enumeración finita; (b) premisas semánticas, empíricas y normativas que las tablas declaran representar. El segundo nivel no se certifica por un booleano ni por la validez del primero.

## 2. Inventario de definiciones y convenciones

Todas las entradas de esta tabla fueron leídas y tipadas. `TYPED` significa que la Definition es coherente con sus dependencias, incluyendo las correcciones de notación declaradas; no significa que sus premisas se cumplan en cualquier aplicación.

| Definición | Fuente | Objeto, dominio y dependencia crítica | Estado / realización FP1 |
|---|---|---|---|
| 1.1 | P00091 | Función parcial `(D_f, f~)`; igualdad exige dominio y valores | TYPED; tabla cerrada |
| 1.2 | P00107 | Registro total de pertenencia y valor con etiqueta disjunta del codominio | TYPED; distinguir dominio conocido, conocimiento e invalidez |
| 1.3 | P00143 | Predicado parcial y gate positivo total matemático | TYPED; gate conserva diagnóstico separado; computable solo con presentación efectiva |
| 1.4 | P00170 | Ámbito κ y ocurrencia `(κ,ξ,e)` | TYPED; IDs de procedencia, política y ejecución retenidos |
| 1.5 | P00224 | Preorden, equivalencia, estricta e incomparabilidad | TYPED; matrices finitas completas |
| 2.1 | P00260 | Historia→estado total en historias admitidas | TYPED; suficiencia no implícita en totalidad |
| 2.2 | P00290 | FSuf como igualdad parcial `f=fbar∘ψ` | TYPED; cobertura/saturación/constancia |
| 2.3 | P00443 | Sistema conjunto `(S,A,Y,E,B,T)`; filas habilitadas no vacías | TYPED; fila ausente no es terminación |
| 2.4 | P00469 | DSuf de un paso con pares sucesor/observación | TYPED con A-F1-002; no permite marginalizar |
| 3.1 | P00569 | Ámbito funcional, X,T,I y Σ parcial | TYPED; índice explícito finito |
| 3.2 | P00585 | F_i y u_i; `o_i(x,t)=u_i(F_i(Σ(x),x,A),x,t)` | TYPED con A-F1-002 |
| 3.3 | P00604 | Dominio por tres guardas secuenciales | TYPED con A-F1-002; no evaluar argumento ausente |
| 3.4 | P00622 | Perfil completo, producto e intersección de dominios | TYPED; índice vacío explícitamente vacuo |
| 3.5 | P00637 | Bloque, referencia r_i y h_i común que preserva/refleja orden | TYPED; evidencia algebraica separada de adecuación empírica |
| 3.6 | P00675 | Producto de preórdenes en bloque común | TYPED; falta de dominio no es incomparabilidad |
| 4.1 | P00850 | Unidad/escala y relación estructural declarada | TYPED; no inferir subsistema por nombre o escala |
| 4.2 | P00869 | Puertos con identidad, valores, unidades, tiempo y recurso | TYPED; normalizar interfaces antes de unir |
| 4.3 | P00883 | Relación conjunta con w y asignación total a puertos | TYPED; distinguir ejecución de completaciones |
| 4.4 | P00898 | Proyección que conserva w | TYPED; conserva procedencia, puede perder restricciones |
| 4.5 | P00905 | Unión natural de familia no vacía de relaciones | TYPED; componer todas las restricciones |
| 4.6 | P01017 | Consumo por ID de demanda, unidad y ámbito temporal | TYPED donde U está definido; FP1 suma finita racional no negativa |
| 4.7 | P01062 | Reducción total de filas relativa a consultas parciales | TYPED; procedencia no se agrega al observable |
| 5.1 | P01139 | Firma, equivalencia generativa, cociente y semántica constante | TYPED; FP1 IDs ya cocientados, sin fusionar por igualdad semántica |
| 5.2 | P01164 | Preorden de conservación | TYPED; conservación no significa cardinalidad ni bienestar |
| 5.3 | P01181 | Inicialización, políticas, escenarios y Runs | TYPED; FP1 fuerte con hojas biyectivas y T_e=H |
| 5.4 | P01202 | Traducción funcional parcial, fidelidad y transporte del preorden | TYPED; FP1 traducción factorizada por identidad, parcialidad explícita |
| 5.5 | P01218 | att, hold,L y acc sobre traza común | TYPED; datos completos, reloj discreto, L natural |
| 5.6 | P01285 | Posible por unión, robusto por intersección, exterior por política | TYPED; no vaciedad por escenario y cobertura |
| 5.7 | P01381 | Origen representado desde inicialización | TYPED; no requiere logros futuros |
| 5.8 | P01386 | CAG adicional y canónico | TYPED; origen distinguido del repertorio bruto |
| 5.9 | P01409 | Joint de políticas que garantizan un conjunto D | TYPED; no afirma coexistencia temporal |
| 5.10 | P01432 | Dominio certificado y suficiencia de lectura | TYPED; all-state coverage incluso tras fallo acc |
| 5.11 | P01460 | Clases iniciales con dominio completo, origen y CAG constantes | TYPED; máximo dominio de clases enteras bajo estas exigencias |
| 5.12 | P01496 | Dominancia por inclusión en bloque autorizado | TYPED; misma receta, cuantificador, horizonte y semántica |

Las convenciones 1.1 (P00059), 1.2 (P00203), 1.3 (P00241), 2.1 (P00274), 2.2 (P00527) y 4.1 (P01092) fueron leídas. 2.2 requiere A-F1-001/I-06. Las demás precisan tipos, no vaciedad, alcance de cierre y separación de procedencia; no aportan por sí solas pruebas de premisas empíricas.

## 3. Revisión resultado por resultado

En la columna de estado, `VALID` abrevia exactamente `REVIEWED_VALID_UNDER_HYPOTHESES`. El alcance no se extiende fuera de las hipótesis listadas. La numeración reproduce S1; no se atribuye originalidad.

| Resultado / fuente | Hipótesis y dependencia | Reproducción del argumento revisado | Estado y puntos adversariales |
|---|---|---|---|
| Proposición 1.1, P00119–P00127 | f:A⇀B y g:B⇀C tipadas | `a∈D_(g∘f)` iff a∈D_f y f(a)∈D_g; entonces valor único de g(f(a)). Ambas guardas son necesarias y suficientes por definición | VALID. Coincidencia de valores en intersección no prueba igualdad parcial |
| Proposición 1.2, P00129–P00141 | Familia fija `(f_i)` sobre mismo A | Existe la tupla completa iff cada componente existe, de modo que dominio=intersección; para I vacío se usa producto singleton/intersección A | VALID. Una tupla de diagnósticos es otro objeto |
| Proposición 1.3, P00180–P00201 | Propiedades A,B sobre misma familia F | Un mismo testigo de A∧B da ambas existencias. Para refutar inversa, dos filas `(1,0)` y `(0,1)` no contienen `(1,1)` | VALID. La prueba refuta la inversa, no afirma incompatibilidad en toda instancia |
| Proposición 1.4, P00213–P00221 | Políticas y escenarios fijados; predicado común | Una π universal sirve a cada ξ. Matriz identidad 2×2 hace verdadero ∀ξ∃π y falso ∃π∀ξ | VALID. Sigue válida la implicación con conjuntos vacíos; la garantía sustantiva exige no vaciedad adicional |
| Teorema 2.1, P00307–P00347 | ψ,f parciales; igualdad de funciones incluye dominios | Necesidad: dominio de composición aporta cobertura y saturación; mismo ψ da mismo f. Suficiencia: D_fbar=ψ[D_f]; saturación da todos los representantes definidos y constancia da valor único; se prueban las dos inclusiones de dominios | VALID. Factor único solo sobre im ψ. No requiere escoger representantes globalmente: el valor único define la función |
| Proposición 2.2, P00366–P00382 | Fibras q∈im ψ no vacías; seguridad exige todos los representantes definidos con mismo valor | Construcción admite exactamente fibras incluidas en D_f con imagen singleton. Toda otra respuesta segura obliga ambas condiciones, por tanto su dominio se incluye | VALID. No cubre D_f fuera de D_ψ ni factoriza f completa |
| Teorema 2.3, P00384–P00416 | Familia fija de consultas; ψ alternativa total | Igualdad de vectores de registros es equivalencia. Teorema 2.1 da factores; si ψ(h)=ψ(h'), igualdad de todas consultas implica misma clase. Definir r(ψ(h))=[h] y probar independencia/unicidad | VALID. La totalidad de ψ es necesaria para el ámbito H completo; «mínima» no significa fácil de calcular |
| Teorema 2.4, P00487–P00513 | Sistema Def.2.3, ψ,o totales, DSuf conjunta | Inducción uniforme sobre n: base traza vacía; terminal se conserva. Para no terminal, proyectar primer par y aplicar hipótesis al sucesor. Inversa: levantar primer par desde el representante actual y aplicar hipótesis a ese sucesor | VALID con notación A-F1-002. No se cambia de representante a mitad de una ejecución. No conserva automáticamente probabilidades/control |
| Teorema 3.1, P00689–P00705 | Mismo bloque, índice y preórdenes; perfiles completos | Reflexividad por todas coordenadas. Transitividad aplica la misma relación i a o_i(r)≼o_i(q)≼o_i(p) y luego conjunción | VALID. Calibración sirve a interpretación; el preorden algebraico requiere órdenes comunes |
| Proposición 3.2, P00707–P00716 | Def.3.5: o_i=h_i∘r_i y preservación/reflexión en valores alcanzados | Sustituir ambas componentes por sus referencias; equivalencia de órdenes se aplica por i; conjunción da bicondicional global | VALID. Monotonía sola da un sentido y es insuficiente |
| Teorema 3.3, P00718–P00740 | Preorden de Teorema 3.1 | Dominancia mutua reflexiva/simétrica/transitiva. Cadena p'≽p≽q≽q' demuestra independencia de representantes. Antisimetría de clases por equivalencia. Para estricta, r≽p contradiría q≻r si p≻q y q≻r | VALID. No convierte equivalencia funcional en identidad causal |
| Teorema 3.4, P00742–P00765 | Cobertura de k_i sobre imagen de B y bicondicional de orden para todas parejas alcanzadas | Cobertura define todas componentes nuevas. Cada comparación i es equivalente antes/después; conjunción preserva dominancia y combinaciones booleanas preservan equivalencia, estricta e incomparabilidad | VALID. Dominio global original exige cobertura global; inyectividad literal no necesaria para preórdenes |
| Proposición 4.1, P00918–P00931 | U⊆V⊆S; cubierta de S para recomposición | Restricciones de funciones son asociativas. Cada fila original satisface cada proyección y por ello pertenece a la unión natural | VALID. Solo inclusión global, no igualdad; sin cubierta limitarse a puertos cubiertos |
| Teorema 4.2, P00933–P00962 | Dos vistas cubren fila `(η,a,b)` con η común completo | Igualdad con join implica cierre al cruzar dos filas de la fibra. Recíproca: pertenencia a ambas proyecciones proporciona a',b'; rectangularidad produce fila global, y Prop.4.1 da otra inclusión | VALID. Rectangularidad es conjuntista, no independencia probabilística |
| Proposición 4.3, P00964–P00979 | R y tablas locales completas, esquemas cubiertos y tipados | La afirmación exige literalmente que las L_j sean las proyecciones y su join sea R. Las tres comprobaciones enumeradas son necesarias y suficientes para esa afirmación | VALID. Es un criterio extensional de auditoría, no un teorema de compatibilidad física |
| Teorema 4.4, P00981–P01003 | Familia no vacía de tablas, J su join; global sobre unión de esquemas | Si existe G, G⊆J; proyectar da L_j⊆π_jJ y definición del join da la inversa. Si las igualdades valen, elegir G=J testimonia existencia | VALID. J puede ser vacío; ejecución existente requiere condición adicional |
| Proposición 4.5, P01032–P01039 | Todas U_ρ(r) definidas, recursos/unidades y sumas legítimas | Cumplir todos presupuestos es el universal de sus desigualdades. Su negación es existir un par (r,ρ) incumplido; en tabla finita un registro exhaustivo vacío equivale al universal | VALID. Dominio completo antes de desigualdad; vacuidad no da alternativa realizable |
| Teorema 4.6, P01074–P01090 | ψ total en H=R y familia fija q parciales | Necesidad por igualdad de imagen reducida; suficiencia por constancia del registro: dominio saturado y valores constantes permiten definir q_red con dominio ψ[D_q]. Unicidad sobre im ψ | VALID. Equivale a aplicación de 2.1. Motivos de ausencia solo descienden si también son observables |
| Proposición 4.7, P01111–P01122 | Recomposición exactamente R y/o todas consultas factoran por ψ | Igualdad de conjuntos permite sustitución en cuantificadores. Para cada vector, usar z=ψ(h); en inversa tomar una misma h de la fibra para todas componentes | VALID. Conserva conjuntos de vectores, no conteos, multiplicidad o masa |
| Teorema 5.1, P01234–P01246 | Misma traza y preorden; H,L naturales; datos requeridos definidos | hold,0 usa reflexividad; ventana L+1 contiene L. Todas recetas exigen tiempo positivo. Cadena consecutiva de acc implica conservación de cada previo por transitividad, incluido j=t por reflexividad | VALID. Identidades logradas más de una vez no invalidan inclusión. No garantiza después del hito |
| Teorema 5.2, P01300–P01315 | Dominio certificado, todas ocurrencias cubiertas y fibras no vacías | Desarrollar uniones e intersecciones da ∃π∃ξ∃e o ∃π∀ξ∀e, respectivamente. Para rob⊆poss elegir una ocurrencia de la π testigo usando no vaciedad | VALID. Tiempo puede depender de ejecución; no cambiar π retrospectivamente |
| Proposición 5.3, P01394–P01407 | g0 y G definidos; CAG por Def.5.8 | Unión con singleton incluye g0; retirarlo deja G\{g0}; para g≠g0, pertenencia no cambia | VALID. La inclusión canónica de origen no es testigo de logro futuro |
| Proposición 5.4, P01415–P01429 | π∈Π en dominio robusto; D tipado | `D⊆⋂_e Ach(e)` iff para toda ocurrencia y todo g∈D se cumple g∈Ach(e). La condición no vacía sigue siendo guardia previa | VALID. D vacío no acredita demandas sustantivas; logro de cada g no equivale a coexistencia |
| Teorema 5.5, P01474–P01494 | Clase entera no vacía incluida en D_f, ámbito común, g0 y f constantes | Cualquier representante tiene f definido; constancia da mismo CAG. Origen constante permite sustraer mismo singleton y bajar CAG+. Maximalidad segura resulta de que cualquiera de estas exigencias fallida excluye clase | VALID. No factoriza f completa si D_f no está saturado; no transporta testigos de política entre representantes |
| Teorema 5.6, P01504–P01523 | Bloque comparativo legítimo y CAG definidos | Inclusión reflexiva/transitiva da preorden; inclusión mutua equivale a igualdad, y cociente por igualdad es antisimétrico | VALID. Cantidad de elementos no sustituye inclusión; bienestar/PVS siguen independientes |

## 4. Hipótesis que deben permanecer visibles

1. **Presentación versus teoría.** La constancia en fibras o la igualdad de conjuntos es una propiedad matemática; para decidirla por enumeración se requieren universos y tablas completos. S1 admite más generalidad que la implementación inicial.
2. **Igualdad de dominio.** Los teoremas 2.1, 2.3, 3.4 y 4.6 no se verifican comparando únicamente valores existentes en ambos lados. La cobertura y las fibras mixtas son testigos diferentes de fallo.
3. **Transporte controlado.** Teorema 2.4 no contiene las condiciones de Convención 2.2. Para transferir políticas hacen falta inicialización, ecuación I-06 reparada con dominios, acciones y pertenencia/cobertura de familias.
4. **Universo común.** Los preórdenes requieren índice y relación comunes. Cambiar criterio por pareja puede dar ciclo pese a datos completos. La calibración semántica añade factorización y reflexión; compartir rango no basta.
5. **Estructura de recursos.** S1 4.6 define U cuando las sumas son legítimas. Para una familia infinita de demandas sería necesario declarar convergencia y codominio adecuado; FP1 evita esa extensión al exigir sumas finitas racionales. El teorema 4.5 es válido donde U está definida y no prueba existencia de la suma.
6. **No vaciedad.** Teoremas 4.4 y 5.2 responden a preguntas diferentes: el primero puede producir global vacío; la robustez exige realizaciones. No sustituir estas guardas por una intersección matemática vacía convencional.
7. **Traducción temporal.** Las identidades se traducen antes de evaluar la receta común y antes de intersectar escenarios; el mapa no tiene por qué ser inyectivo. La conservación necesita preservación y reflexión en los pares pertinentes.
8. **CAG familiar versus política.** El repertorio robusto familiar tiene ∃π por identidad, no una única π para todo repertorio. El registro de una alternativa de MVII usa singleton de política; `Joint` responde a la pregunta conjunta explícita.
9. **Origen y horizonte.** H=0 produce ningún logro futuro; el CAG canónico mantiene el origen. La fuente general puede parar antes de H, sin inventar estados; el perfil fuerte exige T_e=H.
10. **Verdad factual y adecuación.** Un significado tabulado igual/no vacío y un preorden válido son comprobables. Su correspondencia con el mundo y la pertinencia de una regla normativa son premisas externas. Esta revisión no prueba esas premisas.

No se encontró una hipótesis oculta cuya adición alterase una conclusión sustantiva en este tramo. Sí hubo tipado incompleto en la notación original y restricciones de efectividad necesarias al convertir la teoría en contrato; se registran sin generalizar el perfil a toda S1.

## 5. Contraejemplos reproducibles y casos límite

Son instancias matemáticas completamente descritas para incorporación al catálogo de conformidad. Esta sección diseña y calcula sus resultados, pero no afirma tests ejecutados de una implementación.

| ID local | Entrada finita | Resultado exacto / fallo que distingue | Fuente / obligación |
|---|---|---|---|
| EARLY-C01 | A={a,b}; ψ(a)=ψ(b)=q; D_f={a}; f(a)=7 | FSuf falla por fibra mixta; dominio seguro vacío; valor conocido en a no se puede asignar a clase | 2.1–2.2; dominio |
| EARLY-C02 | D_f={a}, D_ψ=∅ | FSuf falla por argumento no cubierto, sin inventar fibra q; diagnóstico distinto de C01 | 2.1; cobertura |
| EARLY-C03 | ψ total constante; f(a)=0,f(b)=1 | FSuf falla por valor discordante con dominio saturado | 2.1; constancia |
| EARLY-C04 | Dos filas sucesor/observación B₁={(0,0),(1,1)}, B₂={(0,1),(1,0)}; ψ,o identidad | Marginales iguales, conjuntos conjuntos distintos; acción θ=y coincide con estado en B₁ y no en B₂ | 2.4; correlación |
| EARLY-C05 | I_A={i₁,i₂}; R constante j; πA(i₁)=a,πA(i₂)=b, a≠b | No existe πB(j) que satisfaga ambas ecuaciones; DSuf causal no basta para políticas | A-F1-001; transporte |
| EARLY-C06 | Un triple k; U_A definida en k, U_B indefinida en v(k) | La ecuación sobre intersección de dominios es vacua; igualdad parcial y transporte fallan | A-F1-001; dominio de U |
| EARLY-C07 | Referencias 8<9; escalas locales 8/10 y 9/100 | 4/5>9/100 invierte comparación absoluta; mismo rango [0,1] no acredita calibración | 3.2; referencia común |
| EARLY-C08 | Valores 1<2; k(1)=k(2)=0 | Mapa monótono borra estricta y crea comparación inversa; falla reflexión | 3.4 |
| EARLY-C09 | a=(2,0,1), b=(1,2,0), c=(0,1,2); comparar a/b solo componente1, b/c solo2, c/a solo3 | a≻b≻c≻a; transitividad inválida por criterio variable | 3.1; índice común |
| EARLY-C10 | L_ab={(0,0),(1,1)}, L_bc={(0,0),(1,1)}, L_ac={(0,1),(1,0)} | Cada pareja compatible; join triple vacío; π_jJ≠L_j, no global exacto | 4.4; composición |
| EARLY-C11 | Dos demandas diferentes d₁,d₂ de 6 a fondo10; otra vista repite d₁ | Uso=12 si son demandas diferentes; repetir ID d₁ no crea un tercer consumo. La fila incumplida permanece causalmente presente | 4.5; identidad de recursos |
| EARLY-C12 | R={(0,0),(6,0),(0,6)} con w fijo; proyecciones univariadas | Join añade (6,6); exactitud conjunta falla aunque locales exactas | 4.1–4.3 |
| EARLY-C13 | h₁=(w₁,a=0,b=0), h₂=(w₂,a=0,b=1); ψ=a; consulta b | Reducción no suficiente; añadir w a ψ cambiaría la pregunta | 4.6; procedencia |
| EARLY-C14 | Dos hojas alcanzan a y b; τ(a)=τ(b)=c | Intersectar nativo da vacío, traducir primero da robusto {c}; si se exige preorden, tomar a,b mutuamente conservativos para satisfacer reflexión | 5.2; traducción antes de intersección |
| EARLY-C15 | p: (o,u,z)/(o,u,u); q: (o,v,v)/(o,v,z), escenarios ξ₁/ξ₂ | P_p^rob={u}; P_q^rob={v}; G^rob={u,v}; z solo posible; Joint({u,v})=∅ | 5.2,5.4; cuantificadores |
| EARLY-C16 | Traza ∅,{a},{a,b},{b},{b,c},{b,c}, conservación por inclusión | att={{a},{a,b},{b},{b,c}}; hold1={{a},{b},{b,c}}; acc={{a},{a,b}} | 5.1; receta |
| EARLY-C17 | H=0, Π y Ξ no vacíos con una hoja inicial por π; g0=o | Ach y G vacíos; CAG+ vacío; CAG={o}. No existe testigo futuro de o | 5.3; origen |
| EARLY-C18 | Ξ={ξ₁,ξ₂}, ξ₁ tiene ejecución, ξ₂ no | CAG robusto fuera de dominio certificado; no descartar ξ₂ | 5.2; no vaciedad por fibra |
| EARLY-C19 | Traza acc pierde conservación en paso1 y carece traducción del estado final | No devolver CAG con «no más logros»: falla dominio completo requerido aunque prefijo ya sea desfavorable | 5.10; cobertura |
| EARLY-C20 | Dos inicializaciones en misma clase; una CAG válida y otra fuera de dominio | Clase excluida del descenso seguro; elegir representante favorable no repara dominio | 5.5 |
| EARLY-C21 | CAG_A={o,u}, CAG_B={o,v}, u≠v | Igual cardinalidad, ambas diferencias no vacías, incomparables | 5.6 |
| EARLY-C22 | Dos filas de mismo ámbito: logro generativo solo en e₁, bienestar favorable solo en e₂ | No existe ejecución con ambos; la agregación separada no proporciona testigo conjunto | 1.3; integración |

Las comprobaciones son reproducibles mediante las definiciones y las tablas mostradas, usando solo igualdad, pertenencia, operaciones de conjuntos y racionales. Los teoremas se justifican por los argumentos generales de la sección 3; estos casos no los reemplazan.

## 6. Conclusión local de integración

Los constructores quedan acíclicos: datos y representaciones → futuros causales de MV → trazas traducidas y recetas → CAG; MI/MII se evalúan desde sus datos y los mismos testigos, sin filtrar futuros por una tarea que dependa del CAG. La Comparison se aplica después de construir valores en su dominio.

El tramo no presenta bloqueador deductivo residual dentro de `FP1_FINITE_EXACT` después de las enmiendas explícitas. Permanecen obligaciones de cada instancia, no problemas abiertos que deban «resolverse» inventando datos: calibración, significado, completitud del modelo causal y criterio normativo. Los contratos y sus diagnósticos permiten rechazar o limitar una instancia que no las acredite. Se entrega al Integrador y al auditor separado; esta conclusión local no acepta por sí sola F1.
