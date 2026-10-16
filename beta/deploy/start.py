"""One supervised web process and one durable worker; no root HTTP process.

Railway may need RAILWAY_RUN_UID=0 to initialize a newly mounted volume.
Only /data/genius is initialized while privileged; drop UID/GID before imports,
migrations, workers, or socket binding. There is no shell command interpolation.
"""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import time

UID = GID = 10001
SHUTDOWN_SECONDS = 105 if os.environ.get('GENIUS_TWIN_ENABLED') == '1' else 40
MANAGEMENT_VARIABLES = (
    "RAILWAY_TOKEN", "RAILWAY_API_TOKEN", "CLOUDFLARE_API_TOKEN",
    "CLOUDFLARE_API_KEY", "CF_API_TOKEN", "GITHUB_TOKEN", "GH_TOKEN",
    "SUPABASE_ACCESS_TOKEN",
)


def validate_runtime_environment():
    """Fail before filesystem writes if runtime contains management access.

    A production image contains /data/genius even without a volume. Directory
    existence therefore cannot establish persistence. Require the /data mount;
    Railway additionally supplies its volume name/path when one is attached.
    This checks bootstrap configuration, not cloud durability or recovery.
    """
    if any(os.environ.get(name) for name in MANAGEMENT_VARIABLES):
        raise RuntimeError("Management credentials must not be injected into the application runtime")
    if os.environ.get("GENIUS_ENV", "development") != "production":
        return
    if os.environ.get("GENIUS_DATA_DIR", "/data/genius") != "/data/genius":
        raise RuntimeError("Production requires GENIUS_DATA_DIR=/data/genius")
    validate_data_path(Path("/data/genius"))
    if not os.path.ismount("/data"):
        raise RuntimeError("Production requires a persistent volume mounted at /data")
    if os.environ.get("RAILWAY_SERVICE_ID") or os.environ.get("RAILWAY_PROJECT_ID"):
        if (os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") != "/data"
                or not os.environ.get("RAILWAY_VOLUME_NAME")):
            raise RuntimeError("Railway volume metadata must identify the /data mount")


def validate_data_path(path):
    if not path.is_absolute():
        raise RuntimeError("GENIUS_DATA_DIR must be absolute in the supervised service")
    if path.is_symlink() or path.resolve() != path:
        raise RuntimeError("Data directory must not use symbolic links or a redirected path")


def prepare_identity():
    os.umask(0o077)
    path = Path(os.environ.get("GENIUS_DATA_DIR", "/data/genius"))
    validate_data_path(path)
    if os.geteuid() == 0:
        if str(path) != "/data/genius":
            raise RuntimeError("Privileged volume initialization only permits /data/genius")
        path.mkdir(mode=0o700, exist_ok=True)
        os.chown(path, UID, GID)
        os.chmod(path, 0o700)
        os.setgroups([])
        os.setgid(GID)
        os.setuid(UID)
    if os.geteuid() == 0:
        raise RuntimeError("Service must not run as root")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not os.access(path, os.W_OK | os.X_OK):
        raise RuntimeError("Persistent directory is not writable by service UID")


def stop_group(process, sig):
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass


def service_commands(port):
    if not 1024 <= port <= 65535:
        raise RuntimeError("PORT must be between 1024 and 65535")
    twin_enabled = os.environ.get('GENIUS_TWIN_ENABLED') == '1'
    commands = [
        [sys.executable, "-m", "gunicorn", "genius_beta.app:create_app()",
         "--bind", f"0.0.0.0:{port}", "--workers", "1", "--threads", "4",
         "--timeout", "120" if twin_enabled else "45", "--graceful-timeout", "100" if twin_enabled else "35", "--keep-alive", "2",
         "--limit-request-line", "2048", "--limit-request-fields", "32",
         "--limit-request-field_size", "4096", "--max-requests", "500",
         "--max-requests-jitter", "50", "--error-logfile", "-"],
        [sys.executable, "-m", "genius_beta.worker"],
    ]
    from genius_beta.r2_backup import enabled
    if enabled():
        commands.append([sys.executable, '-m', 'genius_beta.backup_agent'])
    if os.environ.get('GENIUS_NETWORK_NODE_ENABLED','false')=='true':
        commands.append([sys.executable, '-m', 'genius_beta.network_seed'])
    return commands


def supervise(commands):
    """Process lifecycle, independently testable from platform UID support."""
    stopping = False

    def request_stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    processes = []
    failed = False
    try:
        for index, command in enumerate(commands):
            processes.append(subprocess.Popen(command, start_new_session=True))
            print(f"service_child_started index={index} pid={processes[-1].pid}", flush=True)
        while not stopping:
            if any(process.poll() is not None for process in processes):
                failed = True
                print("service_child_exited; stopping peer", file=sys.stderr, flush=True)
                break
            time.sleep(0.2)
    finally:
        for process in processes:
            stop_group(process, signal.SIGTERM)
        deadline = time.monotonic() + SHUTDOWN_SECONDS
        for index, process in enumerate(processes):
            try:
                process.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                stop_group(process, signal.SIGKILL)
                process.wait()
            print(f"service_child_reaped index={index} returncode={process.returncode}", flush=True)
    return 1 if failed else 0


def main():
    validate_runtime_environment()
    prepare_identity()
    from genius_beta.config import settings
    from genius_beta.db import initialize
    from genius_beta.r2_backup import BackupError, enabled, encryption_key, R2Store

    if enabled():
        encryption_key()
        R2Store()  # validate explicit runtime credentials before serving

    config = settings()
    if enabled() and not config['DATABASE'].exists() and R2Store().list('snapshots/'):
        raise BackupError('REMOTE_BACKUPS_EXIST_RECOVERY_REQUIRED')
    initialize(config["DATABASE"])
    return supervise(service_commands(int(os.environ.get("PORT", "8080"))))


if __name__ == "__main__":
    raise SystemExit(main())
