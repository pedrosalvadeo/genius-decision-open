# Revisión deductiva de MVI–MVII

Fuente revisada: S1, DOCX original, P02352–P03261 inclusive. Se leyó el tramo completo, se contrastaron sus fórmulas con `S1_READABLE.md` y se inspeccionó la estructura OMML de las expresiones del tramo, incluidos operadores de unión/intersección, fracciones, índices y delimitadores que se pierden en el extracto plano. Revisión de autor formalizador, pendiente de la aceptación separada del Integrador y auditor. No constituye prueba mecanizada ni revisión de originalidad.

Resultado: 20 resultados numerados y un corolario examinados. Diecinueve resultados son correctos bajo las hipótesis y ámbitos declarados. El Teorema 8.6 necesita explicitar una hipótesis de admisión de certificados que no se deduce de admitir un lector. FP1 la satisface de forma constructiva. El corolario es correcto. Se registran además aclaraciones de tipado y erratas de presentación, sin modificar S1.

## 1. Hallazgo estructural y reparación

### F1-ED-01 — El lector exacto no basta sin admisión de sus certificados

**Original.** La Definición 8.6, P02518–P02528, separa lectores y certificados admitidos por un protocolo. El Teorema 8.6, P02610–P02618, afirma DV=D* si el protocolo admite lectura exacta fundamentada de Sem.

**Problema.** Admitir el lector no obliga lógicamente a admitir el certificado A=Sem utilizado en la prueba inversa. La fuente reconoce en P02620 que los certificados pueden ser restringidos.

**Contraejemplo a la lectura literal sin clausura.** Sean Sem(h)={p,q}, Φ(p)=Φ(q)=0 y ambos significados en DΦ. El protocolo admite el lector exacto, pero admite únicamente certificados cuyo valor sea uno. La vía completa no aplica porque Sem(h) tiene dos elementos; no hay certificado decisivo permitido de valor cero. Entonces h∈D* y h∉DV. Las condiciones semánticas del certificado cero se satisfacen, pero no su admisión protocolaria.

**Reparación.** El enunciado efectivo es: si el protocolo admite la lectura exacta fundamentada y, para cada h∈D*, admite el certificado canónico con A=Sem(h) y v único en Φ[Sem(h)], entonces DV=D*. Todas las demás guardas de evidencia exigibles deben estar satisfechas por esa ruta. Equivalente: declarar como capacidad conjunta el lector exacto y la regla de certificación canónica completa.

**Prueba reparada.** DV⊆D* conserva la prueba fuente: todo certificado admitido tiene cobertura, dominio y constancia; la vía completa también. Si h∈D*, su lectura exacta produce Sem(h), y la hipótesis adicional garantiza la admisión del certificado canónico. Por tanto h∈DV. La necesidad de esa clausura se muestra por el contraejemplo anterior.

**Impacto.** El protocolo `FP1_EXACT_ENUM_V1` especifica `SEM_UNION` y `DECISIVE_SET` y genera automáticamente el certificado con A=Sem(h). Por ello satisface la hipótesis reparada sin programas arbitrarios ni oráculos. El resultado original no se usa como teorema sobre cualquier protocolo que tenga un lector exacto. Los resultados 8.7–8.11 no cambian. La integración fuerte puede usar la versión reparada.

**Estado.** Reparación propuesta e incorporada a `specification/04_EVIDENCE_AND_DECISION.md`; requiere revisión separada, no autoaceptación del autor. Es una hipótesis adicional explícita, no una corrección silenciosa de S1.

### F1-ED-02 — Restricción del acuerdo de una extensión a las hojas

P02740–P02742 introduce V*:F→{0,1} y dice que coincide con V «en DV», aunque V también puede evaluar prefijos. Para tipar la afirmación sobre hojas se usa F∩DV. La prueba P02747 ya opera únicamente sobre regiones foliares. Interpretar literalmente el acuerdo en todo DV impondría además DV⊆F, condición innecesaria que excluiría evaluaciones tempranas. La aclaración no altera la desigualdad ni su prueba: V* conserva V en F∩DV. No se afirma existencia de V* por esta corrección.

### F1-ED-03 — Normalización de erratas tipográficas

P02461 y P02609 omiten el signo de conjunción entre dos guardas; la prosa y las demostraciones exigen ambas. Se escriben explícitamente `L(h)≠∅ ∧ L(h)⊆DJ` y `Sem(h)⊆DΦ ∧ |Φ[Sem(h)]|=1`. P02892 muestra un par mal delimitado, `(Y_i,(a)Y_i(b))`; la consulta bien tipada es `(Y_i(a),Y_i(b))∈Di`, determinada por Definición 9.2 y su prueba de extensionalidad. P03100 sobrecarga K como problema y como familia; la especificación usa una familia de problemas y su elemento por separado. Estas normalizaciones no constituyen nuevos resultados.

## 2. Inventario de definiciones

Cada fila fue revisada con sus dominios y dependencias. «Fuera del perfil mínimo» conserva validez teórica bajo las hipótesis; no impone una capacidad no especificada a F2.

| Definición | Fuente | Contenido y dependencia | Tratamiento FP1 |
|---|---|---|---|
| 8.1 | P02369–P02381 | Tarea Φ:DΦ⊆S→{0,1}; significado de vida sostenida declarado | Tabla parcial y ámbito normativo explícito |
| 8.2 | P02384–P02418 | Extracción Υ, puente Qeval, tres referencias, intérpretes y dominios de cobertura | Revisada; la ruta exacta no afirma automáticamente fidelidad de esos mapas |
| 8.3 | P02421–P02435 | Fidelidad de adaptador multivaluado por igualdad de unión no vacía | Finita y decidible; extensiones de adaptadores no son lectores arbitrarios |
| 8.4 | P02453–P02464 | Jtask parcial, L(h), DSem y unión de todas las completaciones | Operación obligatoria |
| 8.5 | P02492–P02515 | Evidencia de endpoint, transporte y compatibilidad conjunta | Revisión general; terminación anticipada y límites fuera de FP1 |
| 8.6 | P02518–P02528 | Certificado con cobertura, dominio y veredicto constante | `DECISIVE_SET` con payload verificable |
| 8.7 | P02557–P02572 | Evaluador parcial por rutas admitidas | Ruta exacta completa, no depende de presentación voluntaria de certificados |
| 8.8 | P02607–P02621 | Dominio semánticamente decisivo D* | Igualdad DV=D* bajo clausura F1-ED-01 |
| 8.9 | P02625–P02640 | Ley sobre mismo experimento; filas racionales y nodos nulos | Validación completa y propagación exacta |
| 8.10 | P02658–P02677 | Regiones foliares +, −, ? | Partición exacta conservada |
| 8.11 | P02680–P02693 | PVS solo con ley legítima y M?=0 | Guarda por política; VProb fuera de ella |
| 8.12 | P02754–P02762 | Refinamiento por inclusión de dominios y acuerdo | No se confunde con modificar tarea, modelo o ley |
| 8.13 | P02783–P02789 | Imagen directa de medida por transporte total | Revisada; transporte multimarco no obligatorio FP1 |
| 9.1 | P02847–P02881 | Alternativas y cuatro criterios con ámbito común | Π finita explícita, misma instancia salvo política |
| 9.2 | P02884–P02901 | Dominio parcial de comparación | Verificar todos los criterios antes de resultado integrado |
| 9.3 | P02904–P02917 | Restricciones hard certificadas parciales | Presupuesto de recursos y éxito universal de tarea opcional |
| 9.4 | P02918–P02927 | Partición factible/refutada/indeterminada | Preservar los diagnósticos de todas las restricciones |
| 9.5 | P02930–P02946 | Bloque común y dominancia integrada | Componentes con índices fijos y preórdenes verificados |
| 9.6 | P02962–P02969 | Frontera de maximales relativos | Finita con testigos de exclusión y cobertura |
| 9.7 | P02981–P02991 | Objetivo y alcance de frontera local/global | Exhaustividad solo respecto de objetivo declarado |
| 9.8 | P03022–P03024 | Miembros necesarios/posibles con hard desconocido | Diagnóstico opcional si el preorden amplio existe |
| 9.9 | P03050–P03055 | Intersección robusta de preórdenes | Resultado general revisado; multirregla fuera del perfil mínimo |
| 9.10 | P03076–P03082 | Reducción sobreyectiva que preserva y refleja orden | Resultado general revisado; reducción no obligatoria FP1 |
| 9.11 | P03098–P03110 | Selector parcial con pertenencia a frontera | NONE, UNIQUE o PRIORITY_LIST explícitos |
| 9.12 | P03113–P03120 | Equivarianza bajo acción que transporta fronteras | Revisada; no se afirma sin acción/regla compatible |

## 3. Veinte resultados y corolario: hipótesis y revisión de pruebas

### R08.01 — Proposición 8.1, conservación factual

**Fuente:** P02396–P02401. **Hipótesis:** Υ(h), Qeval(Υ(h)) y las tres referencias están definidos; se han acreditado las dos igualdades a través del mismo significado local. **Dependencias:** Def. 8.2, igualdad del tipo Ufact. **Prueba:** si a=b y b=c entonces a=c. El argumento no requiere inyectividad de los extractores. **Límite:** igualdad de referencias no prueba verdad empírica ni cobertura fuera de h. **Estado:** correcto.

### R08.02 — Teorema 8.2, composición relacional fiel

**Fuente:** P02436–P02450. **Hipótesis:** Q(a) definido no vacío, todos sus intérpretes definidos; R fiel en cada b∈Q(a); exactamente el mismo JB en ambas interfaces. **Dependencias:** Def. 8.3. **Prueba:** sustituir JB(b)=⋃c∈R(b)JC(c) en JA(a)=⋃b∈Q(a)JB(b). La unión anidada es la unión sobre (R∘Q)(a). Hay al menos un b y cada R(b) es no vacío; todos sus JC están definidos. Si una salida c aparece por varias rutas, la idempotencia de unión evita duplicación. **Límite:** no conserva por sí misma compatibilidades conjuntas entre varios adaptadores; requiere el contrato relacional de MII. **Estado:** correcto.

### R08.03 — Teorema 8.3, no vaciedad y refinamiento

**Fuente:** P02465–P02477. **Hipótesis:** h∈DSem; para refinamiento h⊑h′ y ambos en DSem. **Dependencias:** Def. 8.4 y transitividad del prefijo de MV. **Prueba:** elegir e∈L(h), luego s∈Jtask(e), prueba no vaciedad. Toda completación de h′ completa h, de modo que L(h′)⊆L(h); las uniones preservan inclusión. **Límite:** tomar solo completaciones con referencias existentes no cumple DSem. **Estado:** correcto, con conjunción tipográfica explicitada.

### R08.04 — Teorema 8.4, corrección y unicidad

**Fuente:** P02529–P02542. **Hipótesis:** certificado admitido y verificado con ∅≠Sem(h)⊆Ab⊆DΦ, Φ[Ab]={v}. **Dependencias:** Def. 8.6. **Prueba:** todo s∈Sem(h) pertenece a Ab y cumple Φ(s)=v. Para dos certificados, cualquier s de la semántica no vacía pertenece a ambos, así que v=Φ(s)=v′. **Límite:** si Sem fuese vacío y se omitiera su guarda de no vaciedad, A={p} con Φ(p)=0 y A′={q} con Φ(q)=1 cumplirían cobertura y constancia para valores opuestos. La no vaciedad semántica es indispensable para unicidad. **Estado:** correcto.

### R08.05 — Teorema 8.5, acuerdo de rutas

**Fuente:** P02565–P02572. **Hipótesis:** ambas rutas acreditadas para la misma consulta/tarea; vía completa tiene Sem(h)={Sfull(h)}, Sfull(h)∈DΦ; vía decisiva incluye Sem(h) en su conjunto certificado. **Dependencias:** Defs. 8.6–8.7. **Prueba:** Sfull(h) pertenece al conjunto decisivo, así que el valor constante de este es Φ(Sfull(h)), que es el de la vía completa. **Límite:** coherencia factual sola o coincidencia de veredictos no demuestra la identidad de significados. **Estado:** correcto.

### R08.06 — Teorema 8.6, dominio exacto

**Fuente:** P02610–P02621. **Hipótesis revisadas:** lector exacto fundamentado y clausura de admisión de certificados canónicos descrita en F1-ED-01. **Dependencias:** Defs. 8.6–8.8. **Prueba:** DV⊆D* por cobertura y constancia de cada ruta admitida. Para h∈D*, el lector obtiene Sem(h) y la clausura admite A=Sem(h) con su único v; luego h∈DV. **Contraejemplo literal:** protocolo con lector exacto pero certificados solo positivos, Sem={p,q}, ambos Φ=0. **Estado:** correcto con hipótesis completada; no se registra como aceptación literal incondicional del original.

### R08.07 — Teorema 8.7, normalización finita

**Fuente:** P02641–P02650. **Hipótesis:** árbol finito completo, raíz de masa uno, filas suministradas válidas para todos sus hijos; filas ausentes únicamente bajo masa cero si se afirma ley determinada. **Dependencias:** Def. 8.9, MV. **Prueba:** inducción en altura. Una hoja conserva su masa. En nodo con fila, la suma de masas de hijos es p(h)∑qh=p(h); aplicar hipótesis inductiva a cada hijo. En nodo nulo sin fila todas las hojas descendientes reciben cero. Llegar a raíz da suma uno. **Límite:** una fila inválida no se excusa por masa cero; varias leyes con parámetros compartidos requieren su propio contrato. **Estado:** correcto.

### R08.08 — Teorema 8.8, partición y masa

**Fuente:** P02666–P02677. **Hipótesis:** evaluador parcial bien definido con valores binarios; ley normalizada y regiones medibles. **Dependencias:** Def. 8.10. **Prueba:** cada hoja está fuera de DV o dentro con un único valor cero/uno. Las tres posibilidades son excluyentes y exhaustivas. Aditividad finita da M++M−+M?=1. En FP1 toda parte del conjunto finito es medible. **Límite:** una entrada contradictoria no define un evaluador legítimo; prefijos y sus hojas no son sucesos disjuntos adicionales. **Estado:** correcto.

### R08.09 — Proposición 8.9, cotas de completación

**Fuente:** P02739–P02751. **Hipótesis:** existe V*:F→{0,1} total medible y semánticamente admisible, coincidente con V sobre F∩DV; misma ley. **Dependencias:** Def. 8.10, aclaración F1-ED-02. **Prueba:** F+⊆{V*=1} porque preserva éxitos; {V*=1}⊆F+∪F? porque preserva los fallos. Monotonía de la medida da [M+,M++M?]. **Límite:** no demuestra existencia de extensión ni que ambos extremos sean alcanzables. **Estado:** correcto con acuerdo de dominios explicitado.

### R08.10 — Teorema 8.10, refinamiento de evidencia

**Fuente:** P02763–P02771. **Hipótesis:** mismas realizaciones, tarea y ley; DV1⊆DV2 y acuerdo en DV1. **Dependencias:** Def. 8.12. **Prueba:** F1+⊆F2+, F1−⊆F2− y F2?⊆F1? por definición y acuerdo. Monotonía de la misma medida da las tres desigualdades. Restar las dos normalizaciones da M1?−M2?=(M2+−M1+)+(M2−−M1−). **Límite:** una nueva ley o un protocolo restringido no satisface automáticamente las hipótesis. **Estado:** correcto.

### C08.10 — Corolario, estabilidad de PVS definida

**Fuente:** P02772–P02780. **Hipótesis:** las de R08.10 y M1?=0. **Prueba:** 0≤M2?≤M1?=0. La identidad de R08.10 tiene suma cero de dos incrementos no negativos; ambos son cero. En particular M2+=M1+, de modo que las dos PVS existen y coinciden. **Límite:** no transforma una indeterminación de masa cero en veredicto ni equipara refinamiento de prefijos con ampliación de protocolo. **Estado:** correcto.

### R08.11 — Teorema 8.11, transporte de las tres masas

**Fuente:** P02790–P02805. **Hipótesis:** T total en F, p′ imagen directa de p, V̂′(T(e))=V̂(e) para cada e, incluida etiqueta de indefinición. **Dependencias:** Def. 8.13. **Prueba:** para cada b∈{+,−,?}, una e está en T⁻¹(F′b) exactamente cuando su etiqueta es b, luego la preimagen es Fb. Definición de imagen directa da igualdad de masas. Los puntos del destino sin preimagen reciben cero y no afectan la igualdad. **Límite:** no acredita cobertura causal de F′, ni permite colapsar en una fibra hojas con etiquetas distintas. **Estado:** correcto.

### R09.01 — Proposición 9.1, extensionalidad

**Fuente:** P02894–P02901. **Hipótesis:** los valores son iguales como objetos del mismo tipo y ámbito; la relación parcial es fija. **Dependencias:** Def. 9.2. **Prueba:** sustituir argumentos iguales da exactamente el mismo par de dominio y la misma relación. **Límite:** números iguales de políticas, unidades o criterios distintos no satisfacen igualdad tipada. Un comparador con estado oculto no representa la relación declarada. **Estado:** correcto, con errata del par P02892 corregida en la especificación.

### R09.02 — Teorema 9.2, preorden integrado

**Fuente:** P02947–P02959. **Hipótesis:** bloque común, índices fijos, todos los pares requeridos en dominios y cada componente reflexivo/transitivo. **Dependencias:** Def. 9.5. **Prueba:** reflexividad y transitividad se heredan por conjunción. La estricta no puede relacionar a consigo mismo. Si a≻b y b≻c, a≽c; suponer c≽a implica c≽b, contradiciendo b≻c. La dominancia mutua es equivalencia; la relación sobre clases está bien definida por transitividad y es antisimétrica por construcción. **Límite:** no basta auditar solo la intersección ni variar el índice por par. **Estado:** correcto.

### R09.03 — Teorema 9.3, maximales finitos

**Fuente:** P02970–P02978. **Hipótesis:** C finito no vacío bajo el preorden del bloque. **Dependencias:** R09.02. **Prueba:** iniciar una cadena estrictamente ascendente desde cualquier a. No puede repetir: transitividad produciría un ciclo y por tanto a≻a. Tras a lo sumo |C|−1 pasos llega a un elemento sin dominador estricto. **Límite:** C vacío tiene frontera vacía; la finitud no se omite. **Estado:** correcto.

### R09.04 — Teorema 9.4, dos condiciones de cobertura

**Fuente:** P02992–P03012. **Hipótesis:** C⊆S y mismo preorden acreditado sobre S. **Dependencias:** Defs. 9.6–9.7. **Prueba:** un maximal de C ya no tiene dominadores en C; es maximal de S si y solo si tampoco los tiene en S\C. Bajo esa inclusión de fronteras, igualdad requiere que ningún omitido sea maximal; por definición equivale a que cada omitido posea un dominador en S. Si un maximal global está en C también es maximal local. **Límite:** cobertura de encontrados no cubre omitidos equivalentes o incomparables; no exige finitud para esta equivalencia. **Estado:** correcto.

### R09.05 — Teorema 9.5, fronteras con hard indeterminado

**Fuente:** P03025–P03047. **Hipótesis:** preorden común definido sobre Afeas∪Aunk; familia exterior de todos T⊆Aunk. **Dependencias:** Def. 9.8. **Prueba para N:** pertenecer a todas las fronteras obliga pertenecer a Afeas tomando T vacío y ser maximal en el conjunto mayor tomando T=Aunk. Recíprocamente ambas condiciones garantizan presencia y maximalidad en cada intermedio. **Prueba para P:** un dominador factible nunca desaparece. Sin tal dominador, un a factible es maximal para T vacío; uno desconocido lo es para T={a}. **Límite:** para una familia real restringida no vacía N y P solo dan cotas, salvo prueba adicional. **Estado:** correcto.

### R09.06 — Teorema 9.6, orden robusto

**Fuente:** P03056–P03073. **Hipótesis:** familia no vacía de preórdenes sobre un bloque común. **Dependencias:** Def. 9.9 y lógica clásica de los cuantificadores. **Prueba:** la intersección de relaciones reflexivas/transitivas conserva ambas propiedades. La estricta robusta exige ∀ω a≽ωb y ¬∀ω b≽ωa. La segunda es ∃ω ¬(b≽ωa), y junto a la primera produce ∃ω a≻ωb. La recíproca es inmediata. **Límite:** no equivale a mejora estricta en cada modelo ni a intersección de fronteras individuales. **Estado:** correcto.

### R09.07 — Teorema 9.7, reducción exacta de frontera

**Fuente:** P03083–P03095. **Hipótesis:** ρ:C→C̄ sobreyectiva y equivalencia a≽b ⇔ ρ(a)≽̄ρ(b) para todo par. **Dependencias:** Def. 9.10. **Prueba:** aplicando la equivalencia en ambos sentidos del par, se preserva y refleja la estricta. Un dominador de la imagen se levanta a C por sobreyectividad; un dominador de a se proyecta. Por eso a es maximal si y solo si ρ(a) lo es. La sobreyectividad también garantiza que todo maximal de C̄ es imagen de alguno de C. **Límite:** monotonía sola no refleja ausencia de dominadores; un cociente con única clase maximal no selecciona representante. **Estado:** correcto.

### R09.08 — Teorema 9.8, condición necesaria de equivarianza

**Fuente:** P03121–P03137. **Hipótesis:** selector definido en K, dominio estable, acción sobre problemas y alternativas, equivarianza y transporte de fronteras. **Dependencias:** Defs. 9.11–9.12. **Prueba:** para gK=K, s(K)=s(gK)=g s(K). Como s(K) debe ser maximal, pertenece a Fr(CK)∩Fix(GK). **Límite:** una simetría que intercambia todos los candidatos sin punto fijo impide selección equivariante; no impide devolver la frontera. **Estado:** correcto.

### R09.09 — Teorema 9.9, construcción equivariante finita

**Fuente:** P03138–P03154. **Hipótesis:** familia finita estable de problemas, acción que transporta fronteras, maximal fijo por el estabilizador en cada problema. **Dependencias:** Def. 9.12, elecciones finitas de representantes y testigos. **Prueba:** elegir un representante r por órbita y un ar maximal fijo. Para K=gr definir s(K)=gar. Si K=hr, h⁻¹g estabiliza r, así que h⁻¹gar=ar y gar=har; la definición es independiente del transportador. La frontera se transporta, por lo que s(K) es maximal. Para k∈G, s(kK)=(kg)ar=k s(K), probando equivarianza. **Límite:** existencia no significa unicidad ni algoritmo efectivo si la acción o la búsqueda de testigos no están presentadas de forma decidible. FP1 no declara implementar esta extensión. **Estado:** correcto.

## 4. Afirmaciones adicionales y ejemplos

La unicidad de PVS común, P02807–P02825, se justifica por familia no vacía: dos valores comunes coinciden al evaluar cualquier miembro. La condición exige comprobar el dominio de todos; no puede eliminarse un miembro indeterminado. No se añade ley probabilística entre modelos.

La partición de factibilidad, P02918–P02927, es correcta tras excluir contradicciones: todos los juicios uno excluye cualquier cero; el resto se define por complemento. Un cero decide refutación aunque coexistan faltantes. La familia vacía acredita exclusivamente sus propias restricciones vacías.

La selección por prioridad, P03106–P03110, existe y es única en una frontera finita no vacía si la prioridad es un orden total estricto. En FP1 se representa por una permutación de Π; la prioridad no se deduce del preorden. El comportamiento sin regla es conservar la frontera.

| Caso fuente | Verificación deductiva | Consecuencia contractual |
|---|---|---|
| Contraejemplo 8.1, P02509–P02514 | {a,b}, {b,c}, {a,c} intersectan por parejas pero la triple intersección es vacía | Comprobar testigo conjunto |
| Ejemplo 8.1, P02575–P02593 | Φ(1,0)=Φ(1,1)=0 con Sem multivaluada | Certificado decisivo no requiere singleton |
| Contraejemplo 8.2, P02594–P02604 | Sem={p,q}, Φ(p)=1, q fuera de DΦ | No filtrar significados antes de dominio |
| Ejemplo 8.2 y contraejemplo 8.3, P02694–P02716 | Masas (1/2,1/4,1/4); 2/3 es una condicional distinta | Mantener VProb y PVS indefinida |
| Ejemplo 8.3, P02719–P02736 | Hoja g éxito de masa uno, z fallo/indefinida de masa cero | PVS=1 no es garantía universal |
| Contraejemplo 9.1, P03002–P03012 | Omitido equivalente o incomparable permanece maximal | Cobertura de encontrados no es exhaustividad |
| Contraejemplo 9.2, P03066–P03073 | Dos reglas opuestas tienen fronteras disjuntas; robusta contiene ambos | Construir relación robusta antes de frontera |
| Contraejemplo 9.3, P03131–P03137 | Simetría intercambia a y b sin maximal fijo | Selección equivariante inexistente allí |
| Agua/hábitat/presupuesto, P03156–P03246 | CAG singleton de logros distintos más origen; PVS 3/4,3/4,1; presupuesto rechaza ambas; frontera agua/hábitat | Testigo sintético consistente, sin validación empírica ni selector implícito |

En agua/hábitat, el presupuesto es cota por instante, no suma temporal. La política «ambas» conserva sus futuros y PVS=1 aunque falle hard. Su CAG no contiene los logros completos de las otras dos identidades, de modo que el perfil funcional (1,1) no prueba dominancia integrada.

## 5. Ataques adicionales al contrato FP1

Estos son razonamientos adversariales y casos de conformidad propuestos, no tests del Kernel ejecutados en F1.

| Ataque | Resultado necesario |
|---|---|
| Lector exacto disponible pero veto a certificados cero | Rechazar aplicación literal de 8.6; FP1 genera ambos valores y satisface clausura |
| Certificado aporta solo una de dos hojas, misma masa total positiva | Rechazar cobertura aunque la otra hoja sea nula |
| Jtask(e)=∅ como fila definida | Presentación inválida, no evidencia semántica vacía |
| Falta la fila de una hoja en dominio parcial declarado | Sem de sus ancestros indefinida; conservar hojas faltantes |
| Dos significados distintos producen Φ=1 | Puede haber veredicto decisivo; no afirmar significado único ni fidelidad de extractor |
| Fila probabilística inválida bajo nodo nulo | Rechazar fila; no excusarla por irrelevancia de masa |
| Fila ausente en nodo positivo | Ley no determinada; no renormalizar ni emitir PVS |
| Fila ausente en nodo nulo sin otras inconsistencias | Masa foliar descendiente cero; nodos y hojas se conservan |
| Restricción universal con exceso en una ocurrencia y medición ausente en otra | Refutación por testigo; conservar faltante en diagnóstico |
| PVS=1 con fallo nulo y hard task_all hojas | PVS definida, hard refutado, hoja causal conservada |
| Un criterio falso y otro fuera de dominio | Comparación integrada sin valor; ambos diagnósticos |
| Misma cardinalidad de CAG con miembros distintos | No inferir igualdad ni inclusión |
| Filtrar políticas indeterminadas y llamar global a la frontera | Rechazar alcance exhaustivo; solo frontera del C declarado |
| Elegir primer ID de una frontera plural con regla NONE | Rechazar selección sin regla |

El tramo no justifica empiricidad, utilidad práctica ni una teoría universal de elección. Sí proporciona, con F1-ED-01 explícita, contratos finitos cuyo verificador puede comprobar todas las obligaciones declaradas y distinguir los estados parciales sin circularidad.
