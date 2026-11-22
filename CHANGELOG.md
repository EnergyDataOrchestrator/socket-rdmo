# Changelog

All notable changes to `socket-rdmo` are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/); versioning: SemVer.

## [0.1.0] - 2026-11-23

First release — the mapping-driven maDMP export plugin for RDMO.

### Added
- `rdmo-madmp-exporter` package (src layout): generic renderer driven by a bundled YAML mapping spec (`renderer.py`), mapping loader, structural validation, thin RDMO adapter (`rdmo.py`, lazy binding, PEP 562) installed into the RDMO instance as a one-line shim.
- maDMP export exposed over the RDMO HTTP API (`/api/v1/madmp/projects/{pk}/`) and as a project export button.
- Extract kinds beyond plain answers: `value_list` (checkbox joins), `items_list` (dash-list textareas), `generated:` (deterministic `dmp_id` urn:uuid minting), `fixed:`.
- Candidate-list contact fallback: the contact spec accepts several base attributes (`project/data_management`, then `project/coordination`) and uses the first that answers — projects created from a DOI carry a contact without data churn.
- `dmp/funding` export from the RDMO funder answers.
- Two-tier tests: mock tier (53 passed, no RDMO needed) and live tier (real RDMO in the loop, marker `live`).
