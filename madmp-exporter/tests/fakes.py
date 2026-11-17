"""Mock of the RDMO `Export` base class — value provider for the tests.

`FakeExport` implements the helper contract of `rdmo.projects.exports.Export`
(RDMO 2.5.x) against an in-memory value store, so the whole export logic is
exercisable without an RDMO installation:

    get_text(path, set_prefix='', set_index=0, collection_index=0)
    get_list(...) / get_bool(...) / get_timestamp(...)
    get_value(...) / get_option(option_map, path, ..., default=None)
    get_set(path)   -> elements with .set_index and .text

The value store format matches the ground-truth dumps of the validation
procedure (`{"answers": [{attribute, set_index, text, value, option}, ...]}`),
so the mock tests run against the *real* answers of RDMO project #4
(`tests/data/bnetza-measurement-02-answers.json`) and their expectations are
traceable to the live render.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class FakeOption:
    uri_path: str | None = None


@dataclass
class FakeValue:
    """Mirror of the relevant `rdmo.projects.models.Value` surface."""
    attribute: str
    set_index: int = 0
    text: str | None = None
    value: object = None
    unit: str | None = None
    option: FakeOption = field(default_factory=FakeOption)


@dataclass
class FakeSetElement:
    """Mirror of the elements yielded by `Export.get_set`."""
    set_index: int
    text: str | None


class FakeProject:
    """Mirror of the `Project` fields the mapping specs may reference."""

    def __init__(self, title="Measurement_02",
                 description="Example Measurement, as a child-project of IAI."):
        self.title = title
        self.description = description
        self.created = dt.datetime(2026, 3, 2, 9, 54, 14, 726258,
                                   tzinfo=dt.timezone.utc)
        self.updated = dt.datetime(2026, 11, 9, 12, 24, 33, 927859,
                                   tzinfo=dt.timezone.utc)


class FakeExport:
    """Value provider with the RDMO `Export` helper contract (mock)."""

    def __init__(self, answers: list[dict], project: FakeProject | None = None):
        self.project = project or FakeProject()
        self._values: dict[str, list[FakeValue]] = defaultdict(list)
        for row in answers:
            self._values[row["attribute"]].append(FakeValue(
                attribute=row["attribute"],
                set_index=row.get("set_index", 0),
                text=row.get("text"),
                value=row.get("value"),
                unit=row.get("unit"),
                option=FakeOption(uri_path=row.get("option")),
            ))

    # ------------------------------------------------------------------
    # RDMO Export helper contract
    # ------------------------------------------------------------------

    def _lookup(self, attribute, set_index=0):
        for value in self._values.get(attribute, []):
            if value.set_index == set_index:
                return value
        return None

    def get_text(self, attribute, set_prefix="", set_index=0, collection_index=0):
        value = self._lookup(attribute, set_index=set_index)
        return value.text if value and value.text else None

    def get_list(self, attribute, set_prefix="", set_index=0, collection_index=0):
        return [v.text for v in self._values.get(attribute, []) if v.text]

    def get_bool(self, attribute, set_prefix="", set_index=0, collection_index=0):
        value = self._lookup(attribute, set_index=set_index)
        if value is None or value.text is None:
            return None
        return value.text.strip() in ("1", "true", "True", "yes")

    def get_timestamp(self, attribute, set_prefix="", set_index=0, collection_index=0):
        value = self._lookup(attribute, set_index=set_index)
        if value is None or not value.text:
            return None
        return dt.date.fromisoformat(str(value.text)[:10])

    def get_value(self, attribute, set_prefix="", set_index=0, collection_index=0):
        return self._lookup(attribute, set_index=set_index)

    def get_option(self, option_map, attribute, set_prefix="", set_index=0,
                   collection_index=0, default=None):
        value = self._lookup(attribute, set_index=set_index)
        if value is None or value.option is None or not value.option.uri_path:
            return default
        return option_map.get(value.option.uri_path, default)

    def get_set(self, attribute):
        elements = []
        for value in self._values.get(attribute, []):
            elements.append(FakeSetElement(set_index=value.set_index, text=value.text))
        return elements
