"""Renderer tests against the RDMO mock, fed with the REAL answers of
RDMO project #4 (`tests/data/bnetza-measurement-02-answers.json`).

The expectations below are the same as in the live tests
(`test_live_rdmo.py`) — proving that the mock mirrors the real RDMO
behaviour for the exercised contract.
"""

import json
import uuid
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


# ---------------------------------------------------------------------------
# generated dmp_id (gap register item #6)
# ---------------------------------------------------------------------------


def test_dmp_id_is_generated_and_stable(dmp):
    # minted deterministically from the project seed, not from an answer
    expected = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'rdmo:project:4')}"
    assert dmp["dmp_id"]["identifier"] == expected


def test_dmp_id_type_is_urn(dmp):
    assert dmp["dmp_id"]["type"] == "urn"


def test_dmp_id_identical_across_renders(answers):
    # two renders of the same project must carry the same DMP identifier
    provider = FakeExport(answers)
    renderer = MaDMPRenderer(load_mapping(), provider)
    first = renderer.get_dmp()["dmp_id"]
    second = renderer.get_dmp()["dmp_id"]
    assert first == second


def test_dmp_id_differs_per_project(answers):
    from fakes import FakeProject

    provider = FakeExport(answers, project=FakeProject())
    renderer = MaDMPRenderer(load_mapping(), provider)
    provider.project.pk = 5
    assert renderer.get_dmp()["dmp_id"] != MaDMPRenderer(
        load_mapping(), FakeExport(answers)).get_dmp()["dmp_id"]


def test_fixed_spec_resolution():
    renderer = MaDMPRenderer({"options": {}}, FakeExport([]))
    assert renderer.resolve_option({"fixed": "urn"}) == "urn"
    assert renderer.resolve_option({"fixed": "urn"}, set_index=3) == "urn"


# ---------------------------------------------------------------------------
# value_list extract + join modifier (checkbox collections, e.g. preservation)
# ---------------------------------------------------------------------------

CHECKBOX_ANSWERS = [
    # one Value per ticked option; option text lives in `.value`, `.text` empty;
    # collection indices are non-contiguous, as RDMO keeps them on deselect
    {"attribute": "project/dataset/preservation/purpose", "set_index": 0,
     "collection_index": 0, "text": "", "value": "Basis of a publication",
     "option": "preservation_motivation_options/131"},
    {"attribute": "project/dataset/preservation/purpose", "set_index": 0,
     "collection_index": 2, "text": "", "value": "Legal obligations",
     "option": "preservation_motivation_options/132"},
    {"attribute": "project/dataset/preservation/purpose", "set_index": 0,
     "collection_index": 4, "text": "", "value": "Self-commitment",
     "option": "preservation_motivation_options/134"},
]


def test_value_list_joins_checkbox_values():
    provider = FakeExport(CHECKBOX_ANSWERS)
    renderer = MaDMPRenderer({"options": {}}, provider)
    spec = {"attribute": "project/dataset/preservation/purpose",
            "extract": "value_list", "join": "; "}
    assert renderer.resolve(spec) == "Basis of a publication; Legal obligations; Self-commitment"


def test_value_list_without_join_returns_ordered_list():
    provider = FakeExport(CHECKBOX_ANSWERS)
    renderer = MaDMPRenderer({"options": {}}, provider)
    spec = {"attribute": "project/dataset/preservation/purpose",
            "extract": "value_list"}
    assert renderer.resolve(spec) == ["Basis of a publication", "Legal obligations",
                                      "Self-commitment"]


def test_text_extract_stays_empty_for_checkbox_values():
    # documents WHY extract: text silently dropped the field (gap register #14-adjacent)
    provider = FakeExport(CHECKBOX_ANSWERS)
    renderer = MaDMPRenderer({"options": {}}, provider)
    assert renderer.resolve({"attribute": "project/dataset/preservation/purpose"}) == ""


# ---------------------------------------------------------------------------
# items_list extract (dash-formatted textarea, e.g. quality assurance)
# ---------------------------------------------------------------------------

ITEMS_LIST_ANSWERS = [
    {"attribute": "project/dataset/quality_assurance", "set_index": 0,
     "text": "- completeness checks\n- data reconciliation\n- sampling procedures"},
]


def test_items_list_splits_dash_lines_into_proper_list():
    provider = FakeExport(ITEMS_LIST_ANSWERS)
    renderer = MaDMPRenderer({"options": {}}, provider)
    spec = {"attribute": "project/dataset/quality_assurance",
            "extract": "items_list"}
    assert renderer.resolve(spec) == ["completeness checks", "data reconciliation",
                                      "sampling procedures"]


def test_items_list_drops_blank_lines_and_stray_dashes():
    provider = FakeExport([
        {"attribute": "project/dataset/quality_assurance", "set_index": 0,
         "text": "- first\n\n-\n  - indented second\nplain line"},
    ])
    renderer = MaDMPRenderer({"options": {}}, provider)
    spec = {"attribute": "project/dataset/quality_assurance",
            "extract": "items_list"}
    # blank lines dropped, stray "-" alone dropped, indented dash handled,
    # non-dash lines kept as-is (lossless for plain line lists)
    assert renderer.resolve(spec) == ["first", "indented second", "plain line"]


def test_items_list_empty_text_yields_empty_list():
    provider = FakeExport([
        {"attribute": "project/dataset/quality_assurance", "set_index": 0,
         "text": ""},
    ])
    renderer = MaDMPRenderer({"options": {}}, provider)
    spec = {"attribute": "project/dataset/quality_assurance",
            "extract": "items_list"}
    assert renderer.resolve(spec) == []


def test_items_list_unanswered_yields_empty_list():
    provider = FakeExport([])
    renderer = MaDMPRenderer({"options": {}}, provider)
    spec = {"attribute": "project/dataset/quality_assurance",
            "extract": "items_list"}
    assert renderer.resolve(spec) == []


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
