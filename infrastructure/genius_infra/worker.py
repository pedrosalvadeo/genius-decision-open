"""Fixed Linux bootstrap for the unchanged F4 stdio server. No input code."""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import resource
import signal
import sys


def identity_snapshot():
    status = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        key, _, value = line.partition(":")
        if key in {"CapEff", "CapPrm", "CapInh", "CapAmb", "CapBnd", "NoNewPrivs"}:
            status[key] = value.strip()
    return {"euid": os.geteuid(), "egid": os.getegid(),
            "uid_map": Path("/proc/self/uid_map").read_text().strip(),
            "gid_map": Path("/proc/self/gid_map").read_text().strip(), **status}


def _single_uid_namespace(snapshot):
    return (snapshot["euid"] == 0 and snapshot["uid_map"].split() == ["0", "0", "1"] and
            snapshot["gid_map"].split() == ["0", "0", "1"])


def _prctl(option, arg2=0):
    libc = ctypes.CDLL(None, use_errno=True)
    prctl = libc.prctl
    prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                      ctypes.c_ulong, ctypes.c_ulong]
    prctl.restype = ctypes.c_int
    if prctl(option, arg2, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "Required Linux prctl failed")


def enter_lab_containment():
    """Explicit laboratory opt-in: irreversibly reduce this subprocess only.

    Actual UID remains 0. This is never evidence of a non-root deployment.
    """
    if sys.platform != "linux" or not _single_uid_namespace(identity_snapshot()):
        raise PermissionError("Laboratory mode requires the exact single-UID namespace")
    _prctl(38, 1)  # PR_SET_NO_NEW_PRIVS
    class Header(ctypes.Structure):
        _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]
    class Data(ctypes.Structure):
        _fields_ = [("effective", ctypes.c_uint32), ("permitted", ctypes.c_uint32),
                    ("inheritable", ctypes.c_uint32)]
    header = Header(0x20080522, 0)  # _LINUX_CAPABILITY_VERSION_3, current process
    data = (Data * 2)()
    libc = ctypes.CDLL(None, use_errno=True)
    capset = libc.capset
    capset.argtypes = [ctypes.POINTER(Header), ctypes.POINTER(Data)]
    capset.restype = ctypes.c_int
    if capset(ctypes.byref(header), data) != 0:
        raise OSError(ctypes.get_errno(), "Required Linux capset failed")
    # Ambient capabilities can survive exec unless cleared explicitly.
    prctl = libc.prctl
    prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                      ctypes.c_ulong, ctypes.c_ulong]
    prctl.restype = ctypes.c_int
    if prctl(47, 4, 0, 0, 0) != 0:  # PR_CAP_AMBIENT, PR_CAP_AMBIENT_CLEAR_ALL
        raise OSError(ctypes.get_errno(), "Ambient clear failed")
    return validate_identity(lab_single_uid_root=True)


def validate_identity(*, lab_single_uid_root=False):
    if sys.platform != "linux":
        raise PermissionError("Linux required")
    snapshot = identity_snapshot()
    if lab_single_uid_root:
        if (not _single_uid_namespace(snapshot) or snapshot.get("NoNewPrivs") != "1" or
                any(int(snapshot.get(name, "-1"), 16) != 0 for name in ("CapEff", "CapPrm", "CapInh", "CapAmb"))):
            raise PermissionError("Laboratory mode requires zero capabilities and NoNewPrivs")
        snapshot["identity_scope"] = "LAB_ONLY_NOT_NONROOT"
    elif snapshot["euid"] == 0:
        raise PermissionError("Normal operation requires a non-root effective UID")
    else:
        snapshot["identity_scope"] = "NONROOT"
    return snapshot


def apply_containment(cpu_seconds: int, address_space_bytes: int, parent_pid: int, *, lab_single_uid_root=False):
    """Fail closed; also used by trusted synthetic control probes."""
    validate_identity(lab_single_uid_root=lab_single_uid_root)
    if (type(cpu_seconds) is not int or cpu_seconds < 1 or
            type(address_space_bytes) is not int or address_space_bytes < 64 * 1024**2 or
            type(parent_pid) is not int or parent_pid < 1):
        raise ValueError("Invalid containment configuration")
    # Credentials are already final when Popen starts this process. Changing
    # them afterwards can clear PDEATHSIG on Linux.
    _prctl(1, signal.SIGKILL)  # PR_SET_PDEATHSIG
    if os.getppid() != parent_pid:  # Close the parent-death race after prctl.
        os.kill(os.getpid(), signal.SIGKILL)
        raise RuntimeError("Parent changed")
    for kind, value in ((resource.RLIMIT_CPU, cpu_seconds),
                        (resource.RLIMIT_AS, address_space_bytes),
                        (resource.RLIMIT_CORE, 0), (resource.RLIMIT_FSIZE, 0),
                        (resource.RLIMIT_NOFILE, 32)):
        resource.setrlimit(kind, (value, value))
    os.umask(0o077)


def main():
    try:
        lab = len(sys.argv) == 5 and sys.argv[4] == "--lab-single-uid-root"
        if len(sys.argv) != (5 if lab else 4):
            raise ValueError("Expected CPU, AS and parent PID")
        apply_containment(*(int(value) for value in sys.argv[1:4]), lab_single_uid_root=lab)
        root = Path(__file__).resolve().parents[2]
        sys.path[:0] = [str(root / "protocols"), str(root / "kernel")]
        from genius_protocols.server import serve
        return serve(sys.stdin.buffer, sys.stdout.buffer)
    except Exception:
        # Never serialize an exception carrying input, environment, or paths.
        sys.stderr.write("GENIUS_WORKER_BOOTSTRAP_FAILED\n")
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
