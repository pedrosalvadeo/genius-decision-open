"""Run a reviewed command with no credentials and no IPv4/IPv6 sockets (Linux)."""
import ctypes
import ctypes.util
import errno
import os
from pathlib import Path
import sys

class ArgCompare(ctypes.Structure):
    _fields_ = [('arg', ctypes.c_uint), ('op', ctypes.c_uint),
                ('datum_a', ctypes.c_uint64), ('datum_b', ctypes.c_uint64)]

lib = ctypes.CDLL(ctypes.util.find_library('seccomp'), use_errno=True)
lib.seccomp_init.argtypes = [ctypes.c_uint32]
lib.seccomp_init.restype = ctypes.c_void_p
lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
lib.seccomp_rule_add_array.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                     ctypes.c_int, ctypes.c_uint, ctypes.POINTER(ArgCompare)]
lib.seccomp_load.argtypes = [ctypes.c_void_p]
lib.seccomp_release.argtypes = [ctypes.c_void_p]
ctx = lib.seccomp_init(0x7fff0000)
if not ctx:
    raise RuntimeError('seccomp_init failed')
try:
    for family in (2, 10):
        compare = ArgCompare(0, 4, family, 0)  # argument zero == AF_INET/AF_INET6
        code = lib.seccomp_rule_add_array(ctx, 0x00050000 | errno.EPERM,
                                         lib.seccomp_syscall_resolve_name(b'socket'),
                                         1, ctypes.byref(compare))
        if code != 0:
            raise RuntimeError('seccomp_rule_add failed: %s' % code)
    if lib.seccomp_load(ctx) != 0:
        raise RuntimeError('seccomp_load failed')
finally:
    lib.seccomp_release(ctx)
root = Path(__file__).resolve().parent
env = {
    'PATH': str(root / 'vitals-env/bin') + ':/usr/bin:/bin',
    'LANG': 'C.UTF-8',
    'LOCPATH': str(root / 'vitals-locales'),
    'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
    'ANSIBLE_HOME': str(root / 'vitals-ansible'),
    'ANSIBLE_NOCOLOR': '1',
}
os.execvpe(sys.argv[1], sys.argv[1:], env)
