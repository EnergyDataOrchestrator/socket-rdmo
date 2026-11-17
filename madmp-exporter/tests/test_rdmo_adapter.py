"""Tests of the RDMO adapter layer (`rdmo_madmp_exporter.rdmo`).

Runs **without RDMO installed**: `MaDMPExport` degrades to the plain mixin and
is combined with the `FakeExport` base — the same composition the real class
uses inside RDMO (`MaDMPExportMixin` + `Export`). This proves the adapter
wiring (mapping loading, renderer binding, helper contract) independently of
the instance.
"""

import pytest

from rdmo_madmp_exporter.rdmo import MaDMPExport, MaDMPExportMixin, RDMO_AVAILABLE

from fakes import FakeExport


def test_package_import_works_without_rdmo_installed(monkeypatch):
    """The top-level package must not import RDMO/Django."""
    import rdmo_madmp_exporter
    assert rdmo_madmp_exporter.__version__


def test_rdmo_availability_flag_consistent():
    base_modules = [getattr(b, "__module__", "") for b in MaDMPExport.__mro__]
    assert any(m.startswith("rdmo_madmp_exporter") for m in base_modules)
    assert RDMO_AVAILABLE == any(m.startswith("rdmo.") for m in base_modules)


def test_adapter_composes_with_fake_base():
    """Mixin + FakeExport = full export without RDMO (mock of the real MRO)."""

    class MockMaDMPExport(MaDMPExportMixin, FakeExport):
        pass

    export = MockMaDMPExport([])
    assert export.renderer.provider is export
    assert export.get_dmp()["title"] == "maDMP for Measurement_02"


def test_adapter_get_person_delegates():
    class MockMaDMPExport(MaDMPExportMixin, FakeExport):
        pass

    answers = [
        {"attribute": "project/data_management/name", "set_index": 0, "text": "A. Koubaa"},
        {"attribute": "project/data_management/mbox", "set_index": 0,
         "text": "mohamed-anis.koubaa@kit.edu"},
    ]
    export = MockMaDMPExport(answers)
    person = export.get_person({"base_attribute": "project/data_management"})
    assert person == {"name": "A. Koubaa", "mbox": "mohamed-anis.koubaa@kit.edu"}


def test_adapter_get_cost_skips_unanswered():
    class MockMaDMPExport(MaDMPExportMixin, FakeExport):
        pass

    export = MockMaDMPExport([])
    assert export.get_cost({"title": "Personal costs for data creation",
                            "attribute": "project/costs/creation/personnel"}) is None


def test_custom_mapping_file_override(tmp_path):
    mapping_file = tmp_path / "custom.yaml"
    mapping_file.write_text(
        "options: {}\ndmp: {}\ndataset:\n  set: project/custom/set\n  fields: {}\n",
        encoding="utf-8")

    MockMaDMPExport = type(
        "MockMaDMPExport", (MaDMPExportMixin, FakeExport),
        {"mapping_file": str(mapping_file)})

    export = MockMaDMPExport([])
    assert export.mapping["dataset"]["set"] == "project/custom/set"


def test_mixin_docstring_documents_set_index_contract():
    """The set_index positional-slot pitfall must stay documented."""
    assert "set_index" in (MaDMPExportMixin.__doc__ or "")
