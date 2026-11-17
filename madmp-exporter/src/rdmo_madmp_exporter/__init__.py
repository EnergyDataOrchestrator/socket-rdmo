"""rdmo_madmp_exporter — the EDO/Regimo maDMP exporter for RDMO.

Layers (see README.md):

* `mapping`    — loads and validates the declarative mapping spec (YAML)
* `renderer`   — generic maDMP rendering against a value provider (RDMO-free)
* `validation` — structural conformance checks against the maDMP shape
* `rdmo`       — thin adapter binding the renderer to the RDMO `Export` base
                 class (imports RDMO/Django only here)

Importing this package does **not** require RDMO; only
`rdmo_madmp_exporter.rdmo` does.
"""

from rdmo_madmp_exporter.mapping import MappingError, load_mapping
from rdmo_madmp_exporter.renderer import MaDMPRenderer
from rdmo_madmp_exporter.validation import structural_checks, summarize_checks

__version__ = "0.1.0"

__all__ = [
    "MaDMPRenderer",
    "MappingError",
    "load_mapping",
    "structural_checks",
    "summarize_checks",
    "__version__",
]
