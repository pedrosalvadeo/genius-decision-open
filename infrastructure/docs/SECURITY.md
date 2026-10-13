# Controles de operación local

Componente GENIUS-INFRASTRUCTURE-1.0.0, Linux/CPython. Modelo y exclusiones en
[THREAT_MODEL](THREAT_MODEL.md), fuentes primarias en [SOURCES](SOURCES.md).
Los resultados que acreditan cada control se conservan en `validation/F5/`;
la tabla siguiente no convierte un diseño en ensayo ejecutado.

## Perfil explícito y procesos

La CLI exige `--profile local-fp1-v1`. El perfil declara CPU 10 s, espacio virtual
256 MiB, plazo de pared 30 s, stdout 34 MiB y stderr 64 KiB por intento. Los
valores alternativos deben ser explícitos y quedar registrados. No se añaden
límites por defecto al Kernel: su `LimitMap` se conserva separado. Un valor
operativo nunca modifica horizonte, políticas, ramas nulas, pesos ni selector.

El supervisor crea un worker nuevo por operación, negocia P03 y transmite bytes.
Python usa `-I -S -B`, paths de código explícitos, entorno mínimo, sin shell y
sin descriptores heredados innecesarios. La CLI normal rechaza UID 0. El worker
comparte usuario con el operador; no se presenta como aislamiento de identidad.
La prueba como nobody resultó imposible por mapeo UID/GID único `0 0 1`
(EINVAL conservado). El opt-in ENV01 `lab_single_uid_root` requiere ese mapeo
exacto, retira capacidades efectivas/permitidas/heredables/ambientales, configura
NoNewPrivs=1 y comprueba estado real también en el worker. UID continúa siendo
0: el alcance acreditable es laboratorio UID0LAB, no perfil no-root/piloto.
NoNewPrivs impide ganancias de privilegios por exec; no es sandbox ni reemplaza
la protección frente al propietario del mismo UID. La negociación y la validación de respuesta no son una
segunda prueba matemática.

El bootstrap común aplica RLIMIT_CPU, RLIMIT_AS, RLIMIT_FSIZE=0,
RLIMIT_CORE=0 y RLIMIT_NOFILE=32. El supervisor aplica tiempo monotónico y
caps de bytes mientras drena stdout/stderr separados. No se mide CPU mediante
el reloj de pared; AS limita espacio virtual, no RSS combinado del host.
La generación y asignación dentro del supervisor no están cubiertas por el
rlimit del worker; sus entradas/salidas están acotadas por sus interfaces.

El worker se crea en una sesión nueva. La cancelación controlada mata el grupo
y recoge el proceso. PDEATHSIG SIGKILL se configura en el worker y comprueba
`getppid()` después para cerrar la carrera de padre ya muerto. No se cambian
credenciales después de configurar PDEATHSIG. Este contrato se limita al
worker confiado sin descendientes; no promete supervisar árboles de procesos
arbitrarios. Un zombie ya no ejecuta código y su recolección tras muerte del
padre depende del reaper del entorno.

## Interpretación de fallos y preservación

Una respuesta incompleta, exceso operativo, señal o plazo vencido no crea un
Result ni `KernelLIMITED`. Solo se exporta como resultado la respuesta completa
validada. Los artefactos parciales se conservan como evidencia operativa sin
rotularlos resultado válido. El cálculo pudo haber empezado o terminado aun
cuando la entrega falla; no se promete exactamente una vez ni reanudación del
mismo cálculo. Cada reintento es un intento nuevo.

Un Result real con COMPLETE/LIMITED/ERROR o una verificación
VALID/INVALID/INCOMPLETE conserva su significado; entrega completa no significa
que una instancia sea válida, seleccionable ni que un certificado pase. Las
celdas DEFINED, OUTSIDE_DOMAIN y BLOCKED permanecen distintas. Una selección
sobre frontera relativa nunca se fabrica para compensar una interrupción.

El almacén controla paths y permisos, evita overwrite y publica pares completos
mediante sus procedimientos de staging/commit. Usa lock no bloqueante: otro
trabajo sobre ese almacén recibe BUSY, no cola oculta. La recuperación verifica
inventario y hashes, conserva originales y restaura a destino nuevo. Consulte
DATA_RECOVERY para detalle y ensayos de corrupción, interrupción y ENOSPC.

## Evidencia y secretos

Los eventos identifican intento, método, versión, límites, tiempos y fallo,
sin imprimir el payload FP1 o el entorno real. Input/result/candidate son
artefactos completos privados: no son logs redactados. El perfil actual usa
solo datos sintéticos. No se incluyen tokens, credenciales, cookies ni llaves
en el handoff; no se leen variables del entorno para construir un inventario
de secretos. Las pruebas de entorno usan marcadores sintéticos propios.

Tests de seguridad: `infrastructure/tests/test_security.py` y fixtures de su
subdirectorio. Prueban el bootstrap y supervisor compartidos mediante peers
sintéticos; no simulan una instancia matemática adversarial ni constituyen
pentest externo. Los scripts fixtures son código confiado de ensayo, no una
capacidad para ejecutar código recibido por API/CLI. Los tests de datos, el
flujo real y la revisión final pertenecen a otras funciones y mantienen su
propia evidencia. Autor, auditor y receptor son agentes distintos del mismo
proveedor y entorno: independencia funcional interna, no institucional.
