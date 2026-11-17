"""Structural conformance checks for a rendered maDMP document.

These checks mirror the EDO feasibility-study validation (card CF1-004,
`04_P04_S04_validate-export.py`) and encode the shape constraints of the
maDMP common standard / the EDO `madmp-lightmodel.yaml` subset:

* tree root `{"dmp": {...}}` with required, non-empty `title`
* ISO-8601 `created` / `modified`
* person objects (contact/contributor) with string names, list-of-str roles
* cost entries with numeric values
* dataset entries with `yes|no|unknown` for personal/sensitive data,
  identifier objects, and distributions with
  `data_access in open|shared|closed|external`

The checks are intentionally *structural*: the plugin emits the full RDA
maDMP shape (contributor, cost, project, ...), while `madmp-lightmodel.yaml`
is the EDO target subset — unknown top-level keys are therefore not flagged.
"""

from __future__ import annotations

YES_NO_UNKNOWN = {"yes", "no", "unknown"}
DATA_ACCESS = {"open", "shared", "closed", "external"}


def _check(checks: list, name: str, ok, detail: str = "") -> None:
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


def structural_checks(document: dict) -> list[dict]:
    """Check `{"dmp": {...}}` structurally; returns a list of check dicts."""
    checks: list[dict] = []
    dmp = (document or {}).get("dmp", {})

    _check(checks, 'tree root object has "dmp"',
           isinstance(document, dict) and "dmp" in document)
    _check(checks, "dmp/title required and non-empty", bool(dmp.get("title")))

    for key in ("created", "modified"):
        value = dmp.get(key)
        _check(checks, f"dmp/{key} is ISO-8601 timestamp",
               bool(value) and "T" in str(value), str(value))

    contact = dmp.get("contact")
    if contact is not None:
        _check(checks, "dmp/contact has name (str)",
               isinstance(contact, dict) and isinstance(contact.get("name"), str))
        _check(checks, "dmp/contact mbox absent or str",
               contact.get("mbox") is None or isinstance(contact.get("mbox"), str))

    for i, contributor in enumerate(dmp.get("contributor", []) or []):
        _check(checks, f"dmp/contributor[{i}] has name (str)",
               isinstance(contributor.get("name"), str))
        roles = contributor.get("role", [])
        _check(checks, f"dmp/contributor[{i}].role is list of str",
               isinstance(roles, list) and all(isinstance(r, str) for r in roles))

    for i, cost in enumerate(dmp.get("cost", []) or []):
        _check(checks, f"dmp/cost[{i}] has title and numeric value",
               isinstance(cost.get("title"), str)
               and isinstance(cost.get("value"), (int, float)))

    datasets = dmp.get("dataset", [])
    _check(checks, "dmp/dataset is a list", isinstance(datasets, list))
    for i, dataset in enumerate(datasets or []):
        _check(checks, f"dmp/dataset[{i}] has title (str)",
               isinstance(dataset.get("title"), str))
        for key in ("personal_data", "sensitive_data"):
            value = dataset.get(key)
            _check(checks, f"dmp/dataset[{i}].{key} in {sorted(YES_NO_UNKNOWN)}",
                   value in YES_NO_UNKNOWN, str(value))

        dataset_id = dataset.get("dataset_id")
        if dataset_id is not None:
            _check(checks, f"dmp/dataset[{i}].dataset_id has identifier (str)",
                   isinstance(dataset_id.get("identifier"), str))
            _check(checks, f"dmp/dataset[{i}].dataset_id.type present",
                   isinstance(dataset_id.get("type"), str), str(dataset_id.get("type")))

        distributions = dataset.get("distribution", [])
        _check(checks, f"dmp/dataset[{i}].distribution is a list",
               isinstance(distributions, list))
        for j, distribution in enumerate(distributions or []):
            _check(checks, f"dmp/dataset[{i}].distribution[{j}] has title (str)",
                   isinstance(distribution.get("title"), str))
            data_access = distribution.get("data_access")
            _check(checks,
                   f"dmp/dataset[{i}].distribution[{j}].data_access in "
                   "open|shared|closed|external",
                   data_access in DATA_ACCESS, str(data_access))

    return checks


def summarize_checks(checks: list[dict]) -> dict:
    """Aggregate check results: total, passed, failed (check names only)."""
    failed = [c["check"] for c in checks if not c["ok"]]
    return {
        "total": len(checks),
        "passed": len(checks) - len(failed),
        "failed": failed,
    }
