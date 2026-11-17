"""Live integration tests — real RDMO in the loop.

These tests run against a real RDMO instance (default:
`/Users/ot2661/Servers/rdmo-app`, project #4) and exercise the actual
`rdmo.projects.exports.Export` base class with the real project values:

1. configure Django (`config.settings`) and `django.setup()`
2. render project #4 through `rdmo_madmp_exporter.rdmo.MaDMPExport`
3. assert the same ground-truth expectations as the mock tests, plus the
   structural checks of `rdmo_madmp_exporter.validation`

They are auto-skipped when no RDMO installation is present, and they must be
run **with the RDMO env's Python**:

    /Users/ot2661/Servers/rdmo-app/env/bin/python -m pytest tests/test_live_rdmo.py
"""

import json
import os
import sys
from pathlib import Path

import pytest

from conftest import RDMO_APP

pytestmark = pytest.mark.live

PROJECT_ID = int(os.environ.get("RDMO_PROJECT_ID", "4"))

if not RDMO_APP.exists():
    pytest.skip(f"no RDMO instance at {RDMO_APP}", allow_module_level=True)


@pytest.fixture(scope="module")
def django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, str(RDMO_APP))
    os.chdir(RDMO_APP)  # db.sqlite3 path is relative to the rdmo-app dir
    import django
    django.setup()


@pytest.fixture(scope="module")
def ground_truth():
    data = json.loads(
        (Path(__file__).resolve().parent / "data" /
         "bnetza-measurement-02-answers.json").read_text(encoding="utf-8"))
    assert data["project_id"] == PROJECT_ID
    return data


@pytest.fixture(scope="module")
def document(django_ready):
    from rdmo.projects.models import Project
    from rdmo_madmp_exporter.rdmo import MaDMPExport

    project = Project.objects.get(id=PROJECT_ID)
    export = MaDMPExport("madmp", "as maDMP", "rdmo_madmp_exporter.rdmo.MaDMPExport")
    export.project = project
    return {"dmp": export.get_dmp()}


# ---------------------------------------------------------------------------
# ground-truth expectations (same as the mock tests)
# ---------------------------------------------------------------------------

def test_title_and_timestamps(document, ground_truth):
    dmp = document["dmp"]
    assert dmp["title"] == "maDMP for Measurement_02"
    assert dmp["created"] == "2026-03-02T09:54:14.726258+00:00"
    assert dmp["modified"] == "2026-11-09T12:24:33.927859+00:00"


def test_dataset_matches_ground_truth(document, ground_truth):
    dmp = document["dmp"]
    assert len(dmp["dataset"]) == 1
    dataset = dmp["dataset"][0]
    assert dataset["title"] == "bnetza_vorhabenpunkte_bbplg_2"
    assert dataset["personal_data"] == "no"
    assert dataset["sensitive_data"] == "unknown"
    assert "BBPlG" in dataset["keyword"]


def test_contributors_have_mbox(document, ground_truth):
    preservation = [c for c in document["dmp"]["contributor"]
                    if c["role"] == ["Responsible for preservation"]]
    assert preservation, "preservation contributor missing"
    assert preservation[0]["mbox"] == "mohamed-anis.koubaa@kit.edu"


def test_project_dates(document, ground_truth):
    project = document["dmp"]["project"][0]
    assert project["start"] == "2017-01-01"
    assert project["end"] == "2017-07-31"


def test_render_produces_http_response(document, ground_truth):
    from rdmo.projects.models import Project
    from rdmo_madmp_exporter.rdmo import MaDMPExport

    project = Project.objects.get(id=PROJECT_ID)
    export = MaDMPExport("madmp", "as maDMP", "rdmo_madmp_exporter.rdmo.MaDMPExport")
    export.project = project
    response = export.render()
    assert response["Content-Type"].startswith("application/json")
    assert json.loads(response.content.decode("utf-8")) == document


# ---------------------------------------------------------------------------
# structural conformance
# ---------------------------------------------------------------------------

def test_structural_checks(document):
    from rdmo_madmp_exporter.validation import structural_checks, summarize_checks

    summary = summarize_checks(structural_checks(document))
    # The only tolerated failure is distribution.data_access when the
    # sharing question is unanswered in the project (answer gap, not a
    # plugin defect) — every other failure is a real regression.
    unexpected = [f for f in summary["failed"] if "data_access" not in f]
    assert not unexpected, summary

    sharing_answered = any(
        a["attribute"] == "project/dataset/sharing/yesno"
        for a in ground_truth_answers())
    if sharing_answered:
        assert summary["failed"] == [], summary


def ground_truth_answers():
    data = json.loads(
        (Path(__file__).resolve().parent / "data" /
         "bnetza-measurement-02-answers.json").read_text(encoding="utf-8"))
    return data["answers"]
