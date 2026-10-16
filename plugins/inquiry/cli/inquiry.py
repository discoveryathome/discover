#!/usr/bin/env python3
"""Run the inquiry CLI from a checkout or an installed plugin: python3 path/to/cli/inquiry.py ..."""
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("inquiry needs Python 3.10 or later")
for stream in (sys.stdout, sys.stderr):  # never crash on non-UTF-8 consoles (e.g. Windows cp1252)
    try:
        stream.reconfigure(errors="backslashreplace")
    except AttributeError:
        pass
sys.path.insert(0, str(Path(__file__).resolve().parent))
from inquiry.cli import main  # noqa: E402

sys.exit(main())
