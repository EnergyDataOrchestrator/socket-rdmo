"""Thin adapter binding the generic renderer to the RDMO `Export` base class.

This is the **only** module that imports RDMO/Django, and even here both are
lazy:

* `MaDMPExport` is constructed on first access (PEP 562 module `__getattr__`)
  and subclasses the real `rdmo.projects.exports.Export` when RDMO is
  importable, so it can be registered in the instance via

      PROJECT_EXPORTS += [('madmp', _('as maDMP'),
                           'rdmo_madmp.exports.MaDMPExport')]

  The deployed plugin shim in the instance is a one-liner:

      # site-packages/rdmo_madmp/exports.py
      from rdmo_madmp_exporter.rdmo import MaDMPExport  # noqa: F401

* outside RDMO (or before `django.setup()`), the import of
  `rdmo.projects.exports.Export` fails and `MaDMPExport`
  degrades to the plain mixin; tests provide an `Export`-like base
  (`tests/fakes.py::FakeExport`) with the same helper contract.

All catalog intelligence lives in the declarative mapping spec (see
`mapping.py`); this module adds no mapping decisions of its own.
"""

from __future__ import annotations

from rdmo_madmp_exporter.mapping import load_mapping
from rdmo_madmp_exporter.renderer import MaDMPRenderer


class MaDMPExportMixin:
    """Mapping-driven maDMP export logic, independent of the RDMO base class.

    Expects the surrounding object to expose the RDMO `Export` helper contract
    (`get_text`, `get_list`, `get_bool`, `get_timestamp`, `get_value`,
    `get_option`, `get_set`) plus a `project` attribute — either by
    subclassing the real `Export` or a mock with the same contract.

    Important RDMO contract detail: pass `set_index` **as a keyword** — the
    second positional slot of the `Export` helpers is `set_prefix`.
    """

    #: Optional override of the mapping spec location; `None` = resolution
    #: order of `load_mapping()` (see `mapping.py`).
    mapping_file = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = load_mapping(self.mapping_file)
        self.renderer = MaDMPRenderer(self.mapping, self)

    # ------------------------------------------------------------------
    # thin delegation — kept as public methods because the RDMO plugin
    # interface and downstream tooling address them directly
    # ------------------------------------------------------------------

    def render(self):
        """The RDMO export view entry point (requires the real base class)."""
        import json

        from django.conf import settings
        from django.http import HttpResponse

        response = HttpResponse(
            json.dumps({"dmp": self.get_dmp()}, indent=2),
            content_type="application/json")

        if settings.EXPORT_CONTENT_DISPOSITION == "attachment":
            response["Content-Disposition"] = \
                f'attachment; filename="{self.project.title}.json"'

        return response

    def get_dmp(self) -> dict:
        return self.renderer.get_dmp()

    def resolve(self, spec, set_index=0):
        """Resolve a leaf mapping spec; delegates to the renderer."""
        return self.renderer.resolve(spec, set_index=set_index)

    def resolve_option(self, spec, set_index=0):
        """Resolve an `{attribute, options, default}` spec; validator-facing."""
        return self.renderer.resolve_option(spec, set_index=set_index)

    def resolve_identifier(self, spec, set_index=0):
        """Resolve an `{identifier, type, fallback_identifier}` spec."""
        return self.renderer.resolve_identifier(spec, set_index=set_index)

    def get_person(self, spec, set_index=0, roles=None):
        return self.renderer.get_person(spec, set_index=set_index, roles=roles)

    def get_cost(self, spec):
        return self.renderer.get_cost(spec)

    def get_funding(self, spec):
        return self.renderer.get_funding(spec)

    def get_dataset(self, dataset):
        return self.renderer.get_dataset(dataset)


def _build_export_class():
    """Bind `MaDMPExportMixin` onto the RDMO `Export` base — or a plain stub.

    A failed plain import means "no usable RDMO in this process" (either not
    installed, or Django settings not configured yet) and the mixin stands
    alone — mock/test mode. We deliberately do *not* try to configure Django
    here: that would poison the app registry for a later, real
    `django.setup()` in the same process (e.g. the live tests).
    """
    try:
        from rdmo.projects.exports import Export
    except Exception:
        class Export:
            def __init__(self, *args, **kwargs):
                raise RuntimeError(
                    "RDMO is not available in this process; MaDMPExport was "
                    "not bound to rdmo.projects.exports.Export. Compose "
                    "MaDMPExportMixin with an Export-like base yourself "
                    "(see tests/fakes.py).")
        Export.__doc__ = None

    doc = ("The RDMO export plugin (registered as "
           "`rdmo_madmp.exports.MaDMPExport`); subclasses the real "
           "`rdmo.projects.exports.Export` when RDMO is available.")
    return type("MaDMPExport", (MaDMPExportMixin, Export), {"__doc__": doc})


def __getattr__(name):  # PEP 562 — lazy class binding on first access
    if name == "MaDMPExport":
        cls = _build_export_class()
        if any(getattr(b, "__module__", "").startswith("rdmo.")
               for b in cls.__mro__):
            # cache only successful bindings; a stub must stay re-buildable
            # so a later django.setup() in the same process picks up RDMO
            globals()["MaDMPExport"] = cls
        return cls
    if name == "RDMO_AVAILABLE":
        cls = _build_export_class()
        available = any(getattr(base, "__module__", "").startswith("rdmo.")
                        for base in cls.__mro__)
        if available:
            globals()["RDMO_AVAILABLE"] = True
        return available
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | {"MaDMPExport", "RDMO_AVAILABLE"})
