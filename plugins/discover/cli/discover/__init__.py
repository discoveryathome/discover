"""Discovery@Home protocol tools (standard library only)."""

__version__ = "0.2.0"

import os

# The hub this tooling talks to: the canonical hub unless DISCOVER_HUB names another
# (OWNER/REPO). Commands that take --hub override both.
CANONICAL_HUB = "discoveryathome/discover"
HUB_REPO = os.environ.get("DISCOVER_HUB") or CANONICAL_HUB
# Where the hub's website (and its playbooks, under v0/) is served.
CANONICAL_SITE = "https://discoveryathome.github.io/discover/"
SITE = os.environ.get("DISCOVER_SITE") or CANONICAL_SITE
