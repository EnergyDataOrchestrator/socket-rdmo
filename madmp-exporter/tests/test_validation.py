"""Structural-check tests (`rdmo_madmp_exporter.validation`)."""

from rdmo_madmp_exporter.validation import structural_checks, summarize_checks


def make_document(**overrides):
    dataset = {
        "title": "bnetza_vorhabenpunkte_bbplg_2",
        "dataset_id": {"identifier": "bnetza_vorhabenpunkte_bbplg_2", "type": "other"},
        "personal_data": "no",
        "sensitive_data": "unknown",
        "distribution": [
            {"title": "Storage during the project", "data_access": "closed",
             "format": ["CSV and JSON"]},
            {"title": "Preservation after the project", "data_access": "closed"},
        ],
    }
    dataset.update(overrides.get("dataset", {}))
    return {
        "dmp": {
            "title": "maDMP for Measurement_02",
            "created": "2026-03-02T09:54:14.726258+00:00",
            "modified": "2026-11-09T12:24:33.927859+00:00",
            "contributor": [{"name": "A. Koubaa", "role": ["Responsible for preservation"]}],
            "dataset": [dataset],
            **overrides.get("dmp", {}),
        }
    }


def test_valid_document_passes_all_checks():
    checks = structural_checks(make_document())
    summary = summarize_checks(checks)
    assert summary["failed"] == [], summary
    assert summary["passed"] == summary["total"]


def test_missing_title_fails():
    document = make_document()
    document["dmp"].pop("title")
    failed = [c["check"] for c in structural_checks(document) if not c["ok"]]
    assert "dmp/title required and non-empty" in failed


def test_bad_yes_no_unknown_fails():
    document = make_document(dataset={"personal_data": "maybe"})
    failed = [c["check"] for c in structural_checks(document) if not c["ok"]]
    assert any("personal_data" in f for f in failed)


def test_bad_data_access_fails():
    document = make_document()
    document["dmp"]["dataset"][0]["distribution"][0]["data_access"] = "maybe"
    failed = [c["check"] for c in structural_checks(document) if not c["ok"]]
    assert any("data_access" in f for f in failed)


def test_bad_contributor_role_fails():
    document = make_document()
    document["dmp"]["contributor"][0]["role"] = "Responsible for preservation"
    failed = [c["check"] for c in structural_checks(document) if not c["ok"]]
    assert any("contributor[0].role" in f for f in failed)


def test_funding_entry_passes_all_checks():
    document = make_document(dmp={"funding": [{
        "funder": {
            "name": "Helmholtz Metadata Collaboration",
            "funder_id": {
                "identifier": "https://helmholtz-metadaten.de/about-hmc",
                "type": "url",
            },
        },
        "funding_status": "granted",
    }]})
    summary = summarize_checks(structural_checks(document))
    assert summary["failed"] == [], summary


def test_bad_funding_status_fails():
    document = make_document(dmp={"funding": [{
        "funder": {"name": "Helmholtz Metadata Collaboration"},
        "funding_status": "maybe",
    }]})
    failed = [c["check"] for c in structural_checks(document) if not c["ok"]]
    assert any("funding_status" in f for f in failed)
