"""Renderer tests against the RDMO mock, fed with the REAL answers of
RDMO project #4 (`tests/data/bnetza-measurement-02-answers.json`).

The expectations below are the same as in the live tests
(`test_live_rdmo.py`) — proving that the mock mirrors the real RDMO
behaviour for the exercised contract.
"""

import json
from pathlib import Path

import pytest

from rdmo_madmp_exporter.mapping import load_mapping
from rdmo_madmp_exporter.renderer import MaDMPRenderer
from fakes import FakeExport

TESTS = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def answers():
    data = json.loads(
        (TESTS / "data" / "bnetza-measurement-02-answers.json").read_text(encoding="utf-8"))
    return data["answers"]


@pytest.fixture(scope="module")
def dmp(answers):
    provider = FakeExport(answers)
    renderer = MaDMPRenderer(load_mapping(), provider)
    return renderer.get_dmp()


def test_dmp_title_and_timestamps(dmp):
    assert dmp["title"] == "maDMP for Measurement_02"
    assert dmp["created"] == "2026-03-02T09:54:14.726258+00:00"
    assert dmp["modified"] == "2026-11-09T12:24:33.927859+00:00"


def test_contact_absent_when_unanswered(dmp):
    # project/data_management/{name,mbox} are NOT answered in project #4
    assert "contact" not in dmp


def test_contributors_from_ground_truth(dmp):
    contributors = dmp["contributor"]
    by_role = {c["role"][0]: c for c in contributors}

    preservation = by_role["Responsible for preservation"]
    assert preservation["name"] == "A. Koubaa"
    assert preservation["mbox"] == "mohamed-anis.koubaa@kit.edu"

    metadata = by_role["Responsible for metadata for bnetza_vorhabenpunkte_bbplg_2"]
    assert metadata["name"] == "A. Koubaa"


def test_costs_omitted_when_unanswered(dmp):
    # none of the 18 project/costs/* questions is answered in project #4
    assert "cost" not in dmp


def test_dataset_from_ground_truth(dmp):
    assert len(dmp["dataset"]) == 1
    dataset = dmp["dataset"][0]

    # title falls back to the dataset set value (project/dataset/id)
    assert dataset["title"] == "bnetza_vorhabenpunkte_bbplg_2"
    assert dataset["dataset_id"] == {
        "identifier": "bnetza_vorhabenpunkte_bbplg_2",
        "type": "other",
    }
    assert dataset["description"].startswith("Der Datensatz enthält")
    assert dataset["personal_data"] == "no"       # answered '0'
    assert dataset["sensitive_data"] == "unknown"  # not answered
    assert "BBPlG" in dataset["keyword"]
    assert dataset["security_and_privacy"][0]["description"] == "Data is public under GeoNutzV."


def test_dataset_distributions(dmp):
    dataset = dmp["dataset"][0]
    during, after = dataset["distribution"]

    assert during["title"] == "Storage during the project"
    assert during["format"] == ["CSV and JSON"]
    # sharing/yesno unanswered -> during distribution has no data_access
    assert "data_access" not in during

    assert after["title"] == "Preservation after the project"
    # derived: open iff during == open, else closed
    assert after["data_access"] == "closed"


def test_project_section(dmp):
    project = dmp["project"][0]
    assert project["title"] == "Measurement_02"
    assert project["start"] == "2017-01-01"
    assert project["end"] == "2017-07-31"


def test_unanswered_paths_resolve_to_none(answers):
    provider = FakeExport(answers)
    renderer = MaDMPRenderer(load_mapping(), provider)
    assert renderer.resolve({"attribute": "project/dataset/storage/uri"}) is None
    assert renderer.resolve_option(
        {"attribute": "project/dataset/sharing/yesno", "options": "data_access_options"}) is None


def test_extract_kinds(answers):
    provider = FakeExport(answers)
    renderer = MaDMPRenderer(load_mapping(), provider)
    # list
    assert renderer.resolve(
        {"attribute": "project/dataset/format", "extract": "list"}) == ["CSV and JSON"]
    # bool
    assert renderer.resolve(
        {"attribute": "project/dataset/sensitive_data/personal_data_yesno/yesno",
         "extract": "bool"}) is False
    # timestamp
    assert renderer.resolve(
        {"attribute": "project/schedule/project_start", "extract": "timestamp"}
    ).isoformat() == "2017-01-01"
    # value
    assert renderer.resolve(
        {"attribute": "project/dataset/id", "extract": "value"}) == \
        "bnetza_vorhabenpunkte_bbplg_2"


def test_unknown_extract_kind_raises(answers):
    renderer = MaDMPRenderer(load_mapping(), FakeExport(answers))
    with pytest.raises(ValueError, match="Unknown extract kind"):
        renderer.resolve({"attribute": "project/dataset/id", "extract": "blob"})


def test_identifier_fallback(answers):
    provider = FakeExport(answers)
    renderer = MaDMPRenderer(load_mapping(), provider)
    # dataset_identifier (maDMP-example path) does not exist -> fallback to set value
    spec = load_mapping()["dataset"]["fields"]["dataset_id"]
    assert renderer.resolve_identifier(spec, set_index=0) == {
        "identifier": "bnetza_vorhabenpunkte_bbplg_2", "type": "other"}


def test_option_map_translation(answers):
    provider = FakeExport(answers)
    renderer = MaDMPRenderer(load_mapping(), provider)
    provider._values["project/dataset/sharing/yesno"] = [
        type(provider._values["project/dataset/id"][0])(
            attribute="project/dataset/sharing/yesno", set_index=0,
            option=type(provider._values["project/dataset/id"][0].option)(uri_path="dataset_sharing_options/69"))
    ]
    resolved = renderer.resolve_option(
        {"attribute": "project/dataset/sharing/yesno", "options": "data_access_options"})
    assert resolved == "open"
