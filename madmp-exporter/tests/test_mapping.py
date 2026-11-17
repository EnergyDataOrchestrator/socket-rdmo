"""Tests of the mapping-spec loader (`rdmo_madmp_exporter.mapping`)."""

import json
from pathlib import Path

import pytest

from rdmo_madmp_exporter.mapping import MappingError, load_mapping, validate_mapping

TESTS = Path(__file__).resolve().parent


def test_bundled_mapping_loads():
    mapping = load_mapping()
    assert mapping["name"] == "madmp-export-mapping"
    assert "dmp" in mapping and "dataset" in mapping and "options" in mapping


def test_bundled_mapping_declares_dataset_set():
    mapping = load_mapping()
    assert mapping["dataset"]["set"] == "project/dataset/id"


def test_mapping_from_env_var(monkeypatch):
    monkeypatch.setenv("EDO_MADMP_MAPPING", str(TESTS / "data" / "alt-mapping.yaml"))
    mapping = load_mapping()
    assert mapping["dataset"]["set"] == "project/dataset/alternative"


def test_missing_env_file_raises(monkeypatch):
    monkeypatch.setenv("EDO_MADMP_MAPPING", "/does/not/exist.yaml")
    with pytest.raises(MappingError, match="EDO_MADMP_MAPPING"):
        load_mapping()


def test_validation_requires_top_keys():
    with pytest.raises(MappingError, match="missing key: dmp"):
        validate_mapping({"options": {}, "dataset": {"set": "x"}})


def test_validation_requires_dataset_set():
    with pytest.raises(MappingError, match="dataset.set"):
        validate_mapping({"options": {}, "dmp": {}, "dataset": {}})


def test_ground_truth_fixture_is_parseable():
    """The canned project-#4 answers used by the mock tests are valid."""
    data = json.loads(
        (TESTS / "data" / "bnetza-measurement-02-answers.json").read_text(encoding="utf-8"))
    assert data["project_id"] == 4
    assert len(data["answers"]) > 40
