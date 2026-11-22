"""Pytest configuration for the maDMP exporter tests.

Mock tests run on any Python >= 3.10 with pyyaml + pytest — no RDMO needed.
Live tests (marker `live`) need a real RDMO instance; they are auto-skipped
unless `RDMO_APP` points at one (default: ../../infrastructure/Servers/rdmo-app).

The src layout is put on `sys.path` here, so the tests run from a plain
checkout without installing the package first.
"""

import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
SRC = PKG_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

#: Where a live RDMO instance lives (override via environment variable).
#: The dev instance is part of the infrastructure submodule; see
#: infrastructure/README.md. Old location: /Users/ot2661/Servers/rdmo-app.
RDMO_APP = (PKG_ROOT / ".." / ".." / ".." / "infrastructure" / "Servers"
            / "rdmo-app").resolve()
