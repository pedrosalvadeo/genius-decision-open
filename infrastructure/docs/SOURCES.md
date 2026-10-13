# Fuentes primarias de controles F5

Consulta: 2026-09-26. Runtime observado: CPython 3.12.14 en Linux 6.18.44 x86_64.
No se infiere soporte universal de Python 3.12 ni otros SO a partir de este entorno.
Las fuentes se consultaron en vivo mediante búsqueda/apertura oficial. Resúmenes
propios; las pruebas locales, y no la documentación, acreditan la implementación.

| Fuente/versionado | Uso en F5 | Límite relevante |
|---|---|---|
| [Python 3.12.14 resource](https://docs.python.org/3.12/library/resource.html) | `setrlimit`: CPU, espacio de direcciones, archivos, descriptores y core | Depende del SO y aplica por proceso; AS no es memoria global ni cgroup |
| [Python 3.12.14 subprocess](https://docs.python.org/3.12/library/subprocess.html) | argv sin shell, env explícito, close_fds, start_new_session, pipes y user/group para ensayos | `preexec_fn` puede bloquear con threads; user no elimina por sí solo grupos suplementarios; crear proceso no siempre es interrumpible |
| [Python 3.12.14 command line](https://docs.python.org/3.12/using/cmdline.html) | `-I -S -B`: reducir imports de entorno/site/cwd y escrituras pyc | No aísla SO ni protege contra intérprete/código confiado comprometidos |
| [Python 3.12.14 ctypes](https://docs.python.org/3.12/library/ctypes.html) | Interfaz estándar para llamada Linux `prctl` | FFI exige tipos/retorno/errno correctos y no concede portabilidad |
| [Linux man-pages 6.19 PR_SET_PDEATHSIG](https://man7.org/linux/man-pages/man2/PR_SET_PDEATHSIG.2const.html) | SIGKILL al morir padre, comprobación posterior de getppid | Linux; configuración se borra por ciertos cambios de credenciales; muerte antes de configurarlo requiere check explícito; semántica del thread padre |
| [Python 3.12.14 os](https://docs.python.org/3.12/library/os.html) | Dirfds, O_NOFOLLOW/O_EXCL, fsync y operaciones de archivos | Consulta de equipo datos; atomicidad y durabilidad dependen del sistema de archivos |
| [Python 3.12.14 fcntl](https://docs.python.org/3.12/library/fcntl.html) | flock no bloqueante por almacén | Consulta de equipo datos; cooperación local, no lock distribuido ni autorización contra mismo UID |

Motivo: construir el mínimo local con biblioteca estándar, sin instalar
frameworks, SDKs, demonios o conectores. Protocols y Specification conservan sus
fuentes y contratos anteriores. No se declara implementación MCP, A2A, HTTP,
OpenAPI ni estándares nuevos por utilizar JSON o stdio.

## ENV01: namespace de un único UID

Fuentes adicionales primarias consultadas 2026-09-26:

- [Linux Kernel: no_new_privs](https://docs.kernel.org/userspace-api/no_new_privs.html)
  y [man-pages6.19 PR_SET_NO_NEW_PRIVS](https://man7.org/linux/man-pages/man2/PR_SET_NO_NEW_PRIVS.2const.html):
  herencia y persistencia del atributo; impide ganancias por exec, no todos los
  cambios de privilegio ajenos a exec ni efectos de propietario del mismo UID.
- [man-pages6.19 capset](https://man7.org/linux/man-pages/man2/capset.2.html):
  ABI Linux de capacidades por thread, versión3 y dos estructuras uint32;
  restricciones de permisos. El código reduce su propio proceso, no otros.
- [man-pages6.19 user_namespaces](https://man7.org/linux/man-pages/man7/user_namespaces.7.html):
  alcance de IDs/mapeos/capacidades. Un UID textual no determina por sí solo
  privilegios de host. Se registran ambos, sin simular una cuenta no-root.

ENV01 es decisión de laboratorio por limitación observada, no una recomendación
de desplegar servicios como UID0 ni una ampliación del alcance local sintético.

- [Linux man-pages6.19 pidfd_open](https://man7.org/linux/man-pages/man2/pidfd_open.2.html),
  consulta2026-09-26: descriptor de proceso y poll de terminación. Se usa en
  ensayo de muerte del padre porque el procfs montado muestra otro namespace
  de PIDs; evita confundir el PID interno del worker con un proceso externo.
