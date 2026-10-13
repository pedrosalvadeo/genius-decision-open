"""Run the local adapter with no externally reachable bind option."""
import argparse
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path

from .app import create_app


@contextmanager
def exclusive_database(database):
    """Hold across recovery and serving; a second local launcher fails closed."""
    path = Path(database).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".server.lock")
    fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Ya existe un servidor local usando esta base de datos.") from exc
        yield path
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description="GENIUS — modelos declarados en servidor local")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--database", type=Path, default=None)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("--port debe estar entre 1024 y 65535")
    database = args.database or Path(__file__).resolve().parents[2] / "local-data" / "twin.sqlite3"
    try:
        with exclusive_database(database) as locked_database:
            app = create_app(database_path=locked_database)
            app.extensions["twin_service"].recover_jobs()
            app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False, threaded=False)
    except RuntimeError as exc:
        parser.exit(2, str(exc) + "\n")


if __name__ == "__main__":
    main()
