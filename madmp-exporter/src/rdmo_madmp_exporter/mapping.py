"""Loading and validation of the declarative mapping spec.

The mapping spec carries **all** catalog intelligence of the exporter — RDMO
attribute paths, option maps (controlled-vocabulary translations), titles and
role templates — following the EDO principle "intelligence in YAML, generic
driver". Changing the RDMO catalog only requires editing the spec (or pointing
`EDO_MADMP_MAPPING` at another one); no code changes are required.

Resolution order for `load_mapping()`:

1. explicit `path` argument
2. environment variable `EDO_MADMP_MAPPING`
3. the spec bundled with this package (`data/madmp-export.mapping.yaml`)
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

import yaml

#: Bundled fallback spec (package data).
DEFAULT_MAPPING_RESOURCE = "data/madmp-export.mapping.yaml"

#: Environment variable pointing at an alternative spec.
MAPPING_ENV_VAR = "EDO_MADMP_MAPPING"


class MappingError(RuntimeError):
    """The mapping spec is missing, unreadable or invalid."""


def load_mapping(path: str | os.PathLike | None = None) -> dict:
    """Load the mapping spec as a dict, with validation (see module docstring)."""
    if path is not None:
        source = Path(path)
        if not source.is_file():
            raise MappingError(f"mapping spec not found: {source}")
        text = source.read_text(encoding="utf-8")
    else:
        env_path = os.environ.get(MAPPING_ENV_VAR)
        if env_path:
            source = Path(env_path)
            if not source.is_file():
                raise MappingError(
                    f"{MAPPING_ENV_VAR} points to a missing file: {source}")
            text = source.read_text(encoding="utf-8")
        else:
            resource = resources.files(__package__).joinpath(DEFAULT_MAPPING_RESOURCE)
            text = resource.read_text(encoding="utf-8")
            source = f"{__package__}/{DEFAULT_MAPPING_RESOURCE}"

    try:
        mapping = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise MappingError(f"invalid YAML in {source}: {exc}") from exc

    validate_mapping(mapping, source)
    return mapping


def validate_mapping(mapping: dict, source: str = "<mapping>") -> None:
    """Raise `MappingError` if the spec is missing structural keys."""
    if not isinstance(mapping, dict):
        raise MappingError(f"mapping spec {source} must be a YAML mapping")
    for key in ("options", "dmp", "dataset"):
        if key not in mapping:
            raise MappingError(f"mapping spec {source} is missing key: {key}")
    dataset = mapping["dataset"]
    if not isinstance(dataset, dict) or "set" not in dataset:
        raise MappingError(
            f"mapping spec {source} must define dataset.set (the RDMO set attribute "
            "that enumerates the datasets, e.g. project/dataset/id)")
    if not isinstance(mapping["options"], dict):
        raise MappingError(f"mapping spec {source}: options must be a mapping")
