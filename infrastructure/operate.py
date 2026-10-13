#!/usr/bin/env python3
"""Explicit bootstrap: use python3 -I infrastructure/operate.py ..."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genius_infra.cli import main

raise SystemExit(main())
