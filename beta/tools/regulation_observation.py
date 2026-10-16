"""Command-line compatibility entry point for private, read-only observation."""
from genius_beta.observation import ObservationError, main, report, write_private


if __name__ == "__main__":
    raise SystemExit(main())
