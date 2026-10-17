"""Discovery@Home protocol tools (standard library only)."""

__version__ = "0.1.0"

import os

# The hub this tooling talks to: the canonical hub unless DISCOVER_HUB names another
# (OWNER/REPO). Commands that take --hub override both.
CANONICAL_HUB = "discoveryathome/discover"
HUB_REPO = os.environ.get("DISCOVER_HUB") or CANONICAL_HUB
