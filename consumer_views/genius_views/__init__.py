"""Read-only deterministic consumers of an explicitly supplied R2 dossier."""

__version__ = "0.1.0"

from .reader import ViewError, read_case
from .views import render_case

__all__ = ["ViewError", "read_case", "render_case"]
