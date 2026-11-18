"""Generic maDMP renderer driven by the declarative mapping spec.

This module is deliberately **free of RDMO and Django imports**. It renders a
maDMP dict from a *value provider* — any object exposing the lookup contract
of the RDMO `Export` base class (RDMO 2.5.x):

    get_text(path, set_prefix='', set_index=0, collection_index=0) -> str | None
    get_list(...)      -> list[str]
    get_bool(...)      -> bool | None
    get_timestamp(...) -> date | datetime | None
    get_value(...)     -> value object with .text / .value / .unit / .option | None
    get_option(option_map, path, ..., default=None) -> str | None
    get_set(path)      -> iterable of elements with .set_index and .text

The RDMO adapter (`rdmo.py`) binds this renderer to the real `Export` base
class; `tests/fakes.py` ships a provider mock implementing the same contract,
so the full rendering logic is testable without an RDMO installation.

Leaf-spec grammar consumed here (see the bundled mapping spec for the
authoritative documentation):

    {attribute: <rdmo path>, extract: text|list|bool|timestamp|value}
    {attribute: <rdmo path>, options: <options key>, default: <value>}
    {project_field: <project object attribute>}
    {base_attribute: <rdmo path>, name_suffix: ..., mbox_suffix: ...,
     identifier_suffix: ..., role_template: ...}          # person specs
    {identifier: {...}, type: {...}, fallback_identifier: {...}}  # identifier specs
    {generated: <kind>, seed: <template>}   # minted at export time, no RDMO source
    {fixed: <value>}                        # constant, no RDMO source
"""

from __future__ import annotations

import uuid
from collections import defaultdict


class MaDMPRenderer:
    """Renders the maDMP document against a value provider."""

    yes_no_unknown = {True: "yes", False: "no", None: "unknown"}

    def __init__(self, mapping: dict, provider):
        self.mapping = mapping
        self.provider = provider
        self.options = mapping.get("options", {})

    # ------------------------------------------------------------------
    # Leaf-spec resolution
    # ------------------------------------------------------------------

    def resolve(self, spec: dict | None, set_index: int = 0):
        """Resolve a leaf mapping spec against the provider's answers."""
        if not spec:
            return None

        if "generated" in spec:
            return self.generate(spec["generated"], spec)

        if "project_field" in spec:
            return getattr(self.provider.project, spec["project_field"], None)

        attribute = spec.get("attribute")
        extract = spec.get("extract", "text")
        if extract == "text":
            return self.provider.get_text(attribute, set_index=set_index)
        if extract == "list":
            return self.provider.get_list(attribute, set_index=set_index)
        if extract == "bool":
            return self.provider.get_bool(attribute, set_index=set_index)
        if extract == "timestamp":
            return self.provider.get_timestamp(attribute, set_index=set_index)
        if extract == "value":
            value = self.provider.get_value(attribute, set_index=set_index)
            return value.value if value else None
        raise ValueError(f"Unknown extract kind: {extract}")

    def resolve_option(self, spec: dict | None, set_index: int = 0):
        """Resolve an `{attribute, options, default}` spec via an option map."""
        if not spec:
            return None

        if "fixed" in spec:
            return spec["fixed"]

        option_map = self.options.get(spec.get("options"), {})
        return self.provider.get_option(
            option_map, spec.get("attribute"), set_index=set_index,
            default=spec.get("default"))

    def generate(self, kind: str, spec: dict):
        """Mint a value that has no RDMO source (gap-register decisions).

        `seed` is a format template over the project object, e.g.
        `"rdmo:project:{project.pk}"`. `urn_uuid5` derives a stable
        `urn:uuid:<hex>` deterministically from the seed, so every export of
        the same project carries the same identifier.
        """
        seed = spec.get("seed", "{project.pk}").format(project=self.provider.project)

        if kind == "urn_uuid5":
            return f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, seed)}"
        if kind == "uuid4":
            return f"urn:uuid:{uuid.uuid4()}"
        raise ValueError(f"Unknown generated kind: {kind}")

    def resolve_identifier(self, spec: dict | None, set_index: int = 0):
        """Resolve an `{identifier, type, fallback_identifier}` spec."""
        identifier = self.resolve(spec.get("identifier"), set_index=set_index)
        if identifier:
            return {
                "identifier": identifier,
                "type": self.resolve_option(spec.get("type"), set_index=set_index) or "other",
            }

        fallback = spec.get("fallback_identifier")
        if fallback:
            identifier = self.resolve(fallback, set_index=set_index)
            if identifier:
                return {"identifier": identifier, "type": "other"}

        return None

    # ------------------------------------------------------------------
    # Export functions (the maDMP production)
    # ------------------------------------------------------------------

    def get_dmp(self) -> dict:
        mapping = self.mapping.get("dmp", {})
        dmp = defaultdict(list)

        # dmp/title
        title_spec = mapping.get("title", {})
        if "attribute" in title_spec:
            dmp["title"] = self.resolve(title_spec)
        else:
            template = title_spec.get("template", "maDMP for {project.title}")
            dmp["title"] = template.format(project=self.provider.project)

        # dmp/created, dmp/modified
        for key in ("created", "modified"):
            timestamp = self.resolve(mapping.get(key))
            if timestamp:
                dmp[key] = timestamp.isoformat()

        # dmp/contact
        contact_spec = mapping.get("contact")
        if contact_spec:
            contact = self.get_person(contact_spec)
            if contact:
                dmp["contact"] = contact

        # dmp/contributor
        for spec in mapping.get("contributor", []):
            set_attribute = spec.get("set")
            if set_attribute:
                for element in self.provider.get_set(set_attribute):
                    role = spec.get("role_template", "").format(set=element)
                    self._append_contributor(dmp, spec,
                                             set_index=element.set_index, role=role)
            else:
                self._append_contributor(dmp, spec, role=spec.get("role_template"))

        # dmp/cost
        for spec in mapping.get("cost", []):
            cost = self.get_cost(spec)
            if cost:
                dmp["cost"].append(cost)

        # dmp/dataset
        dataset_set = self.mapping.get("dataset", {}).get("set", "project/dataset/id")
        for dataset in self.provider.get_set(dataset_set):
            dmp_dataset = self.get_dataset(dataset)
            if dmp_dataset:
                dmp["dataset"].append(dmp_dataset)

        # dmp/dmp_id
        dmp_id = self.resolve_identifier(mapping.get("dmp_id"))
        if dmp_id:
            dmp["dmp_id"] = dmp_id

        # dmp/language
        language = self.resolve_option(mapping.get("language"))
        if language:
            dmp["language"] = language

        # dmp/project
        project_spec = mapping.get("project", {})
        project_start = self._as_iso(self.resolve(project_spec.get("start")))
        project_end = self._as_iso(self.resolve(project_spec.get("end")))
        if project_start and project_end:
            dmp["project"] = [
                {
                    "title": self.resolve(project_spec.get("title")) or self.provider.project.title,
                    "description": self.resolve(project_spec.get("description")),
                    "start": project_start,
                    "end": project_end,
                }
            ]

        return dict(dmp)

    @staticmethod
    def _as_iso(value):
        """Normalise dates/datetimes to ISO strings (JSON-safe in every env)."""
        if value is None or isinstance(value, str):
            return value
        return value.isoformat()

    def _append_contributor(self, dmp, spec, set_index=0, role=None):
        contributor = self.get_person(spec, set_index=set_index,
                                      roles=[role] if role else None)
        if contributor:
            dmp["contributor"].append(contributor)

    def get_person(self, spec, set_index=0, roles=None):
        """Render a person (dmp/contact or dmp/contributor entry) from a spec."""
        base_attribute = spec.get("base_attribute")
        name_suffix = spec.get("name_suffix", "name")
        mbox_suffix = spec.get("mbox_suffix", "mbox")
        identifier_suffix = spec.get("identifier_suffix", "identifier")

        name = self.provider.get_text(f"{base_attribute}/{name_suffix}", set_index=set_index)
        if not name:
            return None

        contributor = {"name": name}

        mbox = self.provider.get_text(f"{base_attribute}/{mbox_suffix}", set_index=set_index)
        if mbox:
            contributor["mbox"] = mbox

        identifier = self.provider.get_text(
            f"{base_attribute}/{identifier_suffix}", set_index=set_index)
        if identifier:
            contributor["contributor_id"] = {
                "identifier": identifier,
                "type": self.provider.get_option(
                    self.options.get("person_id_type_options", {}),
                    f"{base_attribute}/{identifier_suffix}_type",
                    set_index=set_index, default="other"),
            }

        if roles:
            contributor["role"] = roles

        return contributor

    def get_cost(self, spec):
        """Render one dmp/cost entry; skipped when the question is unanswered."""
        value = self.provider.get_value(spec.get("attribute"))
        if value is None or not value.text:
            return None

        title = spec.get("title")
        cost = {"title": title}

        try:
            cost["value"] = int(value.text)
        except ValueError:
            try:
                cost["value"] = float(value.text)
            except ValueError:
                cost["value"] = 0

        if value.unit:
            cost["description"] = f"{title} in {value.unit}"

            # this is a hack to make 'Euro' work
            currency_code = value.unit.upper()[:3]
            if currency_code in self.options.get("currency_codes", []):
                cost["currency_code"] = currency_code

        return cost

    def get_dataset(self, dataset):
        """Render one dmp/dataset entry for an element of the dataset set."""
        fields = self.mapping.get("dataset", {}).get("fields", {})
        set_index = dataset.set_index
        dmp_dataset = defaultdict(list)

        # dmp/dataset/data_quality_assurance
        data_quality_assurance = self.resolve(fields.get("data_quality_assurance"), set_index)
        if data_quality_assurance:
            dmp_dataset["data_quality_assurance"] = data_quality_assurance

        # dmp/dataset/description
        description = self.resolve(fields.get("description"), set_index)
        if description:
            dmp_dataset["description"] = description

        # dmp/dataset/dataset_id
        dataset_id = self.resolve_identifier(fields.get("dataset_id"), set_index)
        if dataset_id:
            dmp_dataset["dataset_id"] = dataset_id

        # dmp/dataset/distribution (two distributions per dataset, as in the
        # RDA maDMP common standard: storage during the project and
        # preservation afterwards; the post-project data_access is derived in
        # code: open iff the during-project data_access is open, else closed)
        distribution = fields.get("distribution", {})
        during_spec = distribution.get("during", {})
        distribution_during = {}

        access_url = self.resolve(during_spec.get("access_url"), set_index)
        if access_url:
            distribution_during["access_url"] = access_url

        data_access = self.resolve_option(during_spec.get("data_access"), set_index)
        if data_access:
            distribution_during["data_access"] = data_access

        dmp_format = self.resolve(during_spec.get("format"), set_index)
        if dmp_format:
            distribution_during["format"] = dmp_format

        if distribution_during:
            dmp_dataset["distribution"].append({
                "title": during_spec.get("title", "Storage during the project"),
                **distribution_during,
            })

        after_spec = distribution.get("after", {})
        distribution_after = {}

        distribution_after["data_access"] = \
            "open" if distribution_during.get("data_access") == "open" else "closed"

        certified_with = self.resolve_option(after_spec.get("certified_with"), set_index)
        if certified_with:
            distribution_after["certified_with"] = certified_with

        pid_system = self.resolve_option(after_spec.get("pid_system"), set_index)
        if pid_system:
            distribution_after["pid_system"] = pid_system

        host_title = self.resolve(after_spec.get("host"), set_index)
        if host_title:
            distribution_after["host"] = {"title": host_title}

        license_ref = self.resolve_option(after_spec.get("license_ref"), set_index)
        if license_ref:
            license = {"license_ref": license_ref}

            start_date = self.resolve(after_spec.get("license_start_date"), set_index)
            if start_date:
                license["start_date"] = start_date

            distribution_after["license"] = [license]

        if distribution_after:
            dmp_dataset["distribution"].append({
                "title": after_spec.get("title", "Preservation after the project"),
                **distribution_after,
            })

        # dmp/dataset/issued
        issued = self.resolve(fields.get("issued"), set_index)
        if issued:
            dmp_dataset["issued"] = issued

        # dmp/dataset/keyword (project-level)
        keywords = self.resolve(fields.get("keyword"))
        if keywords:
            dmp_dataset["keyword"] = keywords

        # dmp/dataset/language
        language = self.resolve_option(fields.get("language"), set_index)
        if language:
            dmp_dataset["language"] = language

        # dmp/dataset/personal_data
        personal_data = self.resolve(fields.get("personal_data"), set_index)
        dmp_dataset["personal_data"] = self.yes_no_unknown[personal_data]

        # dmp/dataset/preservation_statement
        preservation_statement = self.resolve(fields.get("preservation_statement"), set_index)
        if preservation_statement:
            dmp_dataset["preservation_statement"] = preservation_statement

        # dmp/dataset/security_and_privacy
        for spec in fields.get("security_and_privacy", []):
            value = self.provider.get_value(spec.get("attribute"), set_index=set_index)
            if value:
                dmp_dataset["security_and_privacy"].append({
                    "title": spec.get("title"),
                    "description": value.text,
                })

        # dmp/dataset/sensitive_data
        sensitive_data = self.resolve(fields.get("sensitive_data"), set_index)
        dmp_dataset["sensitive_data"] = self.yes_no_unknown[sensitive_data]

        # dmp/dataset/type
        dmp_type = self.resolve(fields.get("type"), set_index)
        if dmp_type:
            dmp_dataset["type"] = dmp_type

        # dmp/dataset/title — falls back to "Dataset #n"
        dmp_dataset["title"] = self.resolve(fields.get("title_fallback"), set_index) or \
                               f"Dataset #{set_index + 1}"

        return dict(dmp_dataset)
