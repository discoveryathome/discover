#!/usr/bin/env python3
"""Run the discover CLI from a checkout or an installed plugin: python3 path/to/cli/discover.py ..."""
import sys
from pathlib import Path

if sys.version_info < (3, 9):
    sys.exit("discover needs Python 3.9 or later")
for stream in (sys.stdout, sys.stderr):  # never crash on non-UTF-8 consoles (e.g. Windows cp1252)
    try:
        stream.reconfigure(errors="backslashreplace")
    except AttributeError:
        pass
sys.path.insert(0, str(Path(__file__).resolve().parent))
from discover.cli import main  # noqa: E402

sys.exit(main())
