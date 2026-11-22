# socket-rdmo / madmp-exporter

Mapping-driven **maDMP export plugin for RDMO** — the in-RDMO variant of the
EDO/Regimo maDMP production. Renders an RDMO project (including snapshots) as
a machine-actionable DMP (maDMP, RDA common standard shape) directly from the
answers, next to the offline pipeline in
`projecting_spaces/EDO/Artefacts/07_Fragments/scripts/dmp/`.

**Card:** CF1-004 (DMP Erstellung mit RDMO) · **Fragment:** 02_DMP_Erstellung

---

## Design

Following the EDO principle **"intelligence in YAML, generic driver"**, all
catalog intelligence lives in a declarative mapping spec; the code is a
generic driver with a deliberately thin RDMO coupling:

```mermaid
graph TD
    A[RDMO project answers<br/>RDMO Export helpers] --> B[rdmo.py<br/>thin adapter / mixin]
    B --> C[renderer.py<br/>generic MaDMPRenderer]
    D[mapping.py<br/>spec loader] --> C
    E[data/madmp-export.mapping.yaml<br/>ALL paths / option maps / templates] --> D
    C --> F[maDMP document<br/>dmp / contact / contributor / cost / dataset / project]
    F --> G[validation.py<br/>structural checks]
    F --> H[EDO Databus<br/>first payload]
```

| Module | Responsibility | Depends on |
|---|---|---|
| `mapping.py` | Load + validate the mapping spec (bundled, env-var or explicit path) | PyYAML |
| `renderer.py` | Generic maDMP rendering against a *value provider* | — (nothing!) |
| `validation.py` | Structural conformance checks (`{"dmp": {...}}` shape) | — |
| `rdmo.py` | Adapter: binds the renderer to `rdmo.projects.exports.Export` | RDMO/Django (lazy) |

The **value-provider contract** mirrors the RDMO `Export` base class helpers
(RDMO 2.5.x): `get_text`, `get_list`, `get_bool`, `get_timestamp`, `get_value`,
`get_option`, `get_set`. `tests/fakes.py::FakeExport` implements the same
contract as a mock, so the rendering logic is fully testable without RDMO.

> **RDMO pitfall (documented in the mixin):** pass `set_index` to the Export
> helpers **as a keyword** — the second positional slot is `set_prefix`.

## Layout

```
madmp-exporter/
├── pyproject.toml
├── README.md
├── src/rdmo_madmp_exporter/
│   ├── __init__.py            # public API: load_mapping, MaDMPRenderer, structural_checks
│   ├── mapping.py             # spec loading/validation (MappingError)
│   ├── renderer.py            # generic renderer (RDMO/Django-free)
│   ├── validation.py          # structural_checks(), summarize_checks()
│   ├── rdmo.py                # adapter: MaDMPExport (lazy RDMO binding)
│   └── data/
│       └── madmp-export.mapping.yaml   # bundled mapping spec (canonical copy)
└── tests/
    ├── conftest.py            # src on sys.path, RDMO_APP location
    ├── fakes.py               # RDMO Export mock (value-provider contract)
    ├── data/
    │   ├── bnetza-measurement-02-answers.json  # REAL answers of project #4
    │   └── alt-mapping.yaml                     # loader-test fixture
    ├── test_mapping.py        # loader tests
    ├── test_renderer.py       # mock tests (real answers, fake provider)
    ├── test_validation.py     # structural checks
    ├── test_rdmo_adapter.py   # adapter wiring without RDMO
    └── test_live_rdmo.py      # live tests (marker `live`, auto-skipped)
```

## Tests

Two tiers, with **identical expectations** — the mock tier proves the logic,
the live tier proves the instance:

| Tier | Environment | Command |
|---|---|---|
| Mock (no RDMO) | any Python ≥ 3.10 with `pip install -e .[test]` | `.venv/bin/python -m pytest tests -m "not live"` |
| Live (real RDMO) | the RDMO env (`pytest` required) | `infrastructure/Servers/rdmo-app/env/bin/python -m pytest tests` |

The mock tests run against `tests/data/bnetza-measurement-02-answers.json` —
the ground-truth dump of the live RDMO project #4 (BNetzA BBPlG answer set),
produced by the traceable validation procedure
(`Artefacts/07_Fragments/scripts/dmp/04_P04_S04_validate-export.py`). Expected
values in mock and live tests therefore match by construction.

Live tests are auto-skipped when `tests/conftest.py::RDMO_APP` does not exist
(override via that constant; project id via `RDMO_PROJECT_ID`, default `4`).

## Installation & RDMO integration

The RDMO instance keeps a **one-line shim**; the package is installed into the
RDMO env (editable, so edits in this repo take effect after a server reload):

```bash
# 1. install the package into the RDMO env
infrastructure/Servers/rdmo-app/env/bin/pip install --no-build-isolation \
    -e components/socket-rdmo/madmp-exporter

# 2. shim: site-packages/rdmo_madmp/exports.py
from rdmo_madmp_exporter.rdmo import MaDMPExport  # noqa: F401

# 3. registration in config/settings/local.py — each entry a (key,label,class) 3-tuple
PROJECT_EXPORTS = [
    ('xml', 'RDMO XML', 'rdmo.projects.exports.RDMOXMLExport'),
    ('csvcomma', 'CSV (comma separated)', 'rdmo.projects.exports.CSVCommaExport'),
    ('csvsemicolon', 'CSV (semicolon separated)', 'rdmo.projects.exports.CSVSemicolonExport'),
    ('json', 'JSON', 'rdmo.projects.exports.JSONExport'),
    ('madmp', 'maDMP Export Plugin', 'rdmo_madmp.exports.MaDMPExport'),
]
```

> **Do not** add the plugin to `PROJECT_EXPORTS` as a bare string — every entry
> must be the 3-tuple `(key, label, class_path)`. A stray non-tuple entry is
> what produces `ValueError: Need 3 values to unpack in for loop` (and a plain
> 2-tuple yields `not enough values to unpack`).

### Verifying the registration (before starting the server)

```bash
cd infrastructure/Servers/rdmo-app
DJANGO_SETTINGS_MODULE=config.settings env/bin/python -c "
import django; django.setup()
from rdmo.core.plugins import get_plugins
for k, p in get_plugins('PROJECT_EXPORTS').items():
    print(k, '|', p.label, '|', p.class_name)
"
```

The `madmp` row must appear with label `maDMP Export Plugin` and class
`rdmo_madmp.exports.MaDMPExport`.

### Mapping-spec resolution order

1. explicit `MaDMPExport.mapping_file` (class attribute)
2. environment variable `EDO_MADMP_MAPPING`
3. the bundled `data/madmp-export.mapping.yaml`

Point 2/1 at another spec to bind the plugin to a different RDMO catalog —
no code changes required.

### Running the instance

The dev RDMO instance lives **in the repo tree**, in the `regimo-infrastructure`
submodule (cloned from the official `rdmorganiser/rdmo-app` skeleton, Python
3.12 env, SQLite dev database, superuser `admin` / `admin` — see
`infrastructure/README.md`). The plugin is installed into that instance's env:

```bash
cd infrastructure/Servers/rdmo-app
source env/bin/activate          # py3.12 env with rdmo + rdmo-madmp-exporter installed
python manage.py runserver       # http://127.0.0.1:8000/
```

> **Only one RDMO env, please.** The instance has exactly one virtualenv
> (`env/`) and one `config/settings/local.py`. If `runserver` dies during
> startup with `ModuleNotFoundError: No module named 'rdmo_madmp'` while
> loading `INSTALLED_APPS`, another RDMO checkout/venv is active in your
> shell — activate `env/bin` from `infrastructure/Servers/rdmo-app` (as
> above) or call the env python directly:
> `env/bin/python manage.py runserver`.

### Stopping the server

A running instance holds port 8000; find its PID and terminate it gracefully:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN   # shows the LISTEN-ing Python process
kill <PID>                          # SIGTERM, clean shutdown
```

Django's autoreloader runs as a child process; it exits by itself when the
parent dies. Use `kill -9 <PID>` only if a hung process ignores SIGTERM.

## Troubleshooting: export plugins not appearing / template errors

All of the following are symptoms of a single invariant being violated:
**`PROJECT_EXPORTS` must be a list of `(key, label, class_path)` 3-tuples.**
Both the RDMO loader and the UI sidebar iterate it as flat 3-tuples — they must
agree, and `local.py` must feed them that shape.

| Symptom | Root cause | Fix |
|---|---|---|
| `ValueError: Need 3 values to unpack in for loop; got 30` | `PROJECT_EXPORTS` was replaced with something that isn't a list of 3-tuples (e.g. a list of 30 unrelated items, or mixed entries) | Re-declare `PROJECT_EXPORTS` as clean 3-tuples (see registration block above) |
| `ValueError: need 3 values, got 2` / `too many values (expected 3)` | one entry is a 2- or 4-tuple (e.g. `('madmp','label')` missing the class path) | Ensure every entry is exactly `(key, label, class_path)` |
| Export box missing / plugins don't show | A broken `local.py` (wrong shape) or a locally-patched sidebar template | Restore `…/rdmo/projects/templates/projects/project_detail_sidebar.html` from anything you overrode; it ships with `{% for key, label, class in settings.PROJECT_EXPORTS %}` — keep that loop as-is |

Two consumer contracts you **must not desync**:

* **Loader** — `rdmo/core/plugins.py` does
  `for key, label, class_name in getattr(settings, 'PROJECT_EXPORTS')` and
  `import_class(class_name)` (splits the dotted path into module+class).
* **UI sidebar** — `projects/project_detail_sidebar.html` renders
  `{% url 'project_export' project.pk key %}` with `{{ label }}`, so the URL key
  must be a lower-case identifier (`madmp`), **not** the dotted class path.

If you experiment with the sidebar template, do it on a copy and always verify
against the shipped `.bak` so the loop form stays a 3-tuple unpack.

**Second install trap:** keep exactly one RDMO env — the one at
`infrastructure/Servers/rdmo-app/env/`. Older checkouts under `~/Servers/`
(`~/Servers/rdmo-app`, `~/Servers/rdmo/.venv`) predate the move into the repo
and no longer exist on current machines; if one is ever active in your shell
it will be a **plugin-less** RDMO and `runserver` will fail as described
above.

## API

### maDMP over HTTP (CF1 sync entry point)

The plugin exposes one DRF endpoint so other sockets (e.g. `regimo-core`) can
pull a project's maDMP without touching the RDMO database directly:

```
GET /api/v1/madmp/projects/{pk}/
```

- Auth: Token / Basic / Session (`IsAuthenticated`) plus RDMO's
  `projects.export_project_object` permission.
- Response: `{"dmp": {...}}` — byte-identical to the export plugin's
  `MaDMPExport.get_dmp()` output (verified by the live test).
- Deployment: one line in the instance's `config/urls.py`:

  ```python
  path("api/v1/madmp/", include("rdmo_madmp_exporter.urls")),
  ```

A token for machine access: `python manage.py drf_create_token <user>`.

### Python API

```python
from rdmo_madmp_exporter import load_mapping, MaDMPRenderer, structural_checks

mapping = load_mapping()                      # bundled spec, validated
renderer = MaDMPRenderer(mapping, provider)   # provider = Export-like object
document = {"dmp": renderer.get_dmp()}
summary = structural_checks(document)         # list of {check, ok, detail}
```

Outside RDMO, compose the mixin with your own provider base:

```python
from rdmo_madmp_exporter.rdmo import MaDMPExportMixin
from fakes import FakeExport                  # your provider mock

class Export(MaDMPExportMixin, FakeExport): ...
export = Export(answers)                      # answers = ground-truth dump
```

## Provenance & traceability

| Artefact (seed) | Role here |
|---|---|
| `Artefacts/07_Fragments/scripts/dmp/exports.py` | original mapping-driven plugin, promoted into `renderer.py` + `rdmo.py` |
| `Artefacts/07_Fragments/scripts/dmp/03_P03_S03_madmp-export.mapping.yaml` | bundled as `data/madmp-export.mapping.yaml` (canonical copy lives here) |
| `Artefacts/07_Fragments/scripts/dmp/04_P04_S04_validate-export.py` | traceable validation; its structural checks are generalised in `validation.py` |
| `Artefacts/07_Fragments/scripts/dmp/measurement_02/Measurement_02-groundtruth.json` | canned as `tests/data/bnetza-measurement-02-answers.json` |

## Known limitations

* `dmp/contact` requires `project/data_management/{name,mbox}`; the
  preservation contributor's email lives at the **dataset level**
  (`project/dataset/preservation/responsible_person/email`) in the installed
  catalog — encoded in the bundled spec.
* `distribution.data_access` is only emitted when
  `project/dataset/sharing/yesno` is answered (option map
  `dataset_sharing_options/{67..70}`); the after-project distribution derives
  `closed` unless the during-project access is `open`.
* Costs are skipped unless the value is non-empty (empty costs are never
  rendered as `value: 0`).
* The plugin does not yet emit `ethical_issues_*`, `storage` budgets or
  metadata-standard IDs; extend the mapping spec as the catalog grows.
