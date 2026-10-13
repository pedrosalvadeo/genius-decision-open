"""Launch with PYTHONPATH=kernel:protocols python3 -m genius_protocols."""
import argparse
import sys

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(description="Genius Protocols offline JSON-RPC stdio server")
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    from .server import serve
    return serve(sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    sys.exit(main())

