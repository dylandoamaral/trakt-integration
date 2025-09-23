from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

import voluptuous as vol
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from custom_components.trakt_tv.const import (
    DEFAULT_DAYS_TO_FETCH,
    DEFAULT_MAX_MEDIAS,
    LIST_MEDIA_TYPES,
    LIST_SORT_BY_CUSTOM,
    LIST_SORT_BY_DEFAULT,
    LIST_SORT_BY_VIP,
    LIST_SORT_ORDER,
)

# ---- Reusable leaf field specs ----


@dataclass(frozen=True)
class NumberSpec:
    min: int
    max: int
    step: int = 1


@dataclass(frozen=True)
class FieldSpec:
    key: str
    title: str  # used only for translation generation
    description: str | None  # used only for translation generation
    kind: str  # "bool" | "number" | "text" | "select"
    options: List[Dict[str, str]] | None = None  # for "select
    number: NumberSpec | None = None
    multiline: bool = False  # for text fields
    required: bool = False  # all fields required in schema
    default: str | int | None = None  # default value


FIELDS: Dict[str, FieldSpec] = {
    "enabled": FieldSpec("enabled", "Enabled", None, "bool"),
    "days_to_fetch": FieldSpec(
        "days_to_fetch",
        "Days to fetch",
        "How far ahead to look (days).",
        "number",
        number=NumberSpec(1, 365),
        required=True,
        default=DEFAULT_DAYS_TO_FETCH,
    ),
    "max_medias": FieldSpec(
        "max_medias",
        "Maximum items to display",
        None,
        "number",
        number=NumberSpec(1, 50),
        required=True,
        default=DEFAULT_MAX_MEDIAS,
    ),
    "exclude_text": FieldSpec(
        "exclude_text",
        "Exclude (comma separated)",
        "Slugs to hide, separated by commas. See documentation for more details.",
        "text",
        multiline=True,
        default="",
    ),
    "exclude_collected": FieldSpec(
        "exclude_collected", "Exclude collected items", None, "bool"
    ),
}

# ---- Groups (labels only used for translations) ----

UPCOMING_GROUPS: Mapping[str, str] = {
    "show": "Show",
    "new_show": "New show",
    "premiere": "Premiere",
    "movie": "Movie",
    "dvd": "DVD",
}

NTW_GROUPS: Mapping[str, str] = {
    "next_to_watch_all": "All",
    "next_to_watch_only_aired": "Only aired",
    "next_to_watch_only_upcoming": "Only upcoming",
}

BASIC_GROUPS: Mapping[str, str] = {
    "show": "Show",
    "movie": "Movie",
}

# For descriptions with links (used only by translation generation)
TRAKT_CAL_MY = {
    "show": "https://trakt.tv/calendars/my/shows/",
    "new_show": "https://trakt.tv/calendars/my/new-shows/",
    "premiere": "https://trakt.tv/calendars/my/premieres/",
    "movie": "https://trakt.tv/calendars/my/movies/",
    "dvd": "https://trakt.tv/calendars/my/dvd/",
}
TRAKT_CAL_ALL = {
    "show": "https://trakt.tv/calendars/shows/",
    "new_show": "https://trakt.tv/calendars/new-shows/",
    "premiere": "https://trakt.tv/calendars/premieres/",
    "movie": "https://trakt.tv/calendars/movies/",
    "dvd": "https://trakt.tv/calendars/dvd/",
}
TRAKT_CAL_RECOMMENDATIONS = {
    "show": "https://trakt.tv/shows/recommendations",
    "movie": "https://trakt.tv/movies/recommendations",
}
TRAKT_CAL_ANTICIPATED = {
    "show": "https://trakt.tv/shows/anticipated",
    "movie": "https://trakt.tv/movies/anticipated",
}

# ---- Section plans (which fields each section uses) ----


@dataclass(frozen=True)
class SectionPlan:
    section_key: str  # e.g. "upcoming_show"
    name: str  # used only for translations
    description: str | None  # used only for translations
    # where to store values in CONF_SENSORS:
    source: str  # e.g. "upcoming", "next_to_watch"
    group_key: str  # e.g. "show", "all", "only_upcoming"
    fields: Sequence[str]  # keys in FIELDS
    collapsed: bool = True


def build_section_plans() -> List[SectionPlan]:
    plans: List[SectionPlan] = []

    # Stats (no options)
    plans.append(
        SectionPlan(
            section_key="stats",
            name="Statistics",
            description="Your Trakt statistics, e.g. movies watched, shows collected.",
            source="stats",
            group_key="all",
            fields=("enabled",),
            collapsed=True,
        )
    )
    # Upcoming
    for key, label in UPCOMING_GROUPS.items():
        plans.append(
            SectionPlan(
                section_key=f"upcoming_{key}",
                name=f"Upcoming — {label}",
                description=f"Upcoming {label.lower()}s from your watchlist. See: {TRAKT_CAL_MY[key]}",
                source="upcoming",
                group_key=key,
                fields=("enabled", "days_to_fetch", "max_medias"),
                collapsed=True,
            )
        )
    # All upcoming
    for key, label in UPCOMING_GROUPS.items():
        plans.append(
            SectionPlan(
                section_key=f"all_upcoming_{key}",
                name=f"All upcoming — {label}",
                description=f"All upcoming {label.lower()}s. See: {TRAKT_CAL_ALL[key]}",
                source="all_upcoming",
                group_key=key,
                fields=("enabled", "days_to_fetch", "max_medias"),
                collapsed=True,
            )
        )
    # Next to watch
    for key, label in NTW_GROUPS.items():
        plans.append(
            SectionPlan(
                section_key=f"next_to_watch_{key}",
                name=f"Next to watch — {label}",
                description=None,
                source="next_to_watch",
                group_key=key,
                fields=("enabled", "max_medias", "exclude_text"),
                collapsed=True,
            )
        )
    # Recommendations
    for key, label in BASIC_GROUPS.items():
        plans.append(
            SectionPlan(
                section_key=f"recommendation_{key}",
                name=f"Recommendations — {label}",
                description=f"Recommended {label.lower()}s based on what you might like. See: {TRAKT_CAL_RECOMMENDATIONS[key]}",
                source="recommendation",
                group_key=key,
                fields=("enabled", "max_medias"),
                collapsed=True,
            )
        )
    # Anticipated
    for key, label in BASIC_GROUPS.items():
        plans.append(
            SectionPlan(
                section_key=f"anticipated_{key}",
                name=f"Anticipated — {label}",
                description=f"Most anticipated {label.lower()}s. See: {TRAKT_CAL_ANTICIPATED[key]}",
                source="anticipated",
                group_key=key,
                fields=("enabled", "max_medias", "exclude_collected"),
                collapsed=True,
            )
        )

    return plans


# ---- UI builder (OptionsFlow) ----


def _selector_for(field: FieldSpec):
    if field.kind == "bool":
        return BooleanSelector()
    if field.kind == "number":
        ns = field.number or NumberSpec(1, 999999, 1)
        return NumberSelector(
            NumberSelectorConfig(
                min=ns.min, max=ns.max, step=ns.step, mode=NumberSelectorMode.BOX
            )
        )
    if field.kind == "text":
        return TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT, multiline=field.multiline)
        )
    if field.kind == "select":
        return SelectSelector(
            SelectSelectorConfig(
                options=field.options, mode=SelectSelectorMode.DROPDOWN
            )
        )
    raise ValueError(f"Unknown field kind: {field.kind}")


def build_options_schema(current: Dict) -> vol.Schema:
    """Return a schema with one SECTION per plan, defaults from current."""
    plans = build_section_plans()
    schema_fields: Dict = {}

    for p in plans:
        # Pull values for this (source, group)
        gdef = current.get(p.source, {}) or {}
        if p.group_key is not None:
            gdef = gdef.get(p.group_key, {}) or {}

        # Build body for this section
        body: Dict = {}
        for key in p.fields:
            fs = FIELDS[key]
            sel = _selector_for(fs)

            if key == "exclude_text" and "exclude" in gdef:
                # Join list into comma-separated string
                default = ", ".join(gdef.get("exclude", []))
            else:
                default = gdef.get(key, fs.default)

            if fs.required:
                body[vol.Required(key, default=default)] = sel
            else:
                body[vol.Optional(key, default=default)] = sel

        # Expand if enabled; otherwise use plan's default
        is_enabled = (
            bool(gdef.get("enabled", False)) if "enabled" in p.fields else False
        )
        collapsed = not is_enabled if "enabled" in p.fields else p.collapsed

        sect = section(vol.Schema(body), {"collapsed": collapsed})

        # Make section required so user_input always carries it
        schema_fields[vol.Required(p.section_key)] = sect

    return vol.Schema(schema_fields)


# ---- Parser (user_input -> CONF_SENSORS) ----


def build_sensors_dict(plans: List[SectionPlan]) -> Dict:
    """Return empty sensors dict using sources from plans."""
    keys = {p.source for p in plans}
    return {k: {} for k in keys}


def parse_options_submission(user_input: Dict) -> Dict:
    """Convert the section payload into nested sensors dict."""
    plans = build_section_plans()
    sensors = build_sensors_dict(plans)

    for p in plans:
        data = user_input.get(p.section_key, {}) or {}
        out = {}
        for key in p.fields:
            val = data.get(key)
            if key == "exclude_text":
                raw = (val or "").strip()
                out["exclude"] = [x.strip() for x in raw.split(",")] if raw else []
            else:
                out[key] = val
        sensors[p.source][p.group_key] = out

    return sensors


# --- Lists (special case, not in plans) ---

MENU_INIT = {
    "sensors": "Configure sensors",
    "lists_menu": "Manage lists",
    "finish": "Save & exit",
}

MENU_LISTS = {
    "lists_add": "Add list",
    "lists_edit_pick": "Edit list",
    "lists_delete": "Delete list(s)",
    "init": "Back",
}


def get_menu_labels(step_id: str) -> dict:
    if step_id == "init":
        return MENU_INIT
    if step_id == "lists_menu":
        return MENU_LISTS
    return {}


def _get_sort_options() -> List[Dict[str, str]]:
    sort_options = LIST_SORT_BY_DEFAULT.copy()

    for item in LIST_SORT_BY_VIP:
        if item not in sort_options:
            sort_options.append(
                {"value": item["value"], "label": f"{item['label']} (VIP only)"}
            )

    for item in LIST_SORT_BY_CUSTOM:
        if item not in sort_options:
            sort_options.append(
                {"value": item["value"], "label": f"{item['label']} (Custom)"}
            )

    return sorted(sort_options, key=lambda d: d["label"])


LIST_FIELDS: Dict[str, FieldSpec] = {
    "friendly_name": FieldSpec(
        "friendly_name",
        "Friendly name",
        "A name to identify this list in Home Assistant. Must be unique.",
        "text",
        required=True,
    ),
    "private_list": FieldSpec(
        "private_list", "Private list (authorized user only)", None, "bool"
    ),
    "list_id": FieldSpec(
        "list_id",
        "List ID or slug",
        "Public lists require a numeric ID (e.g. 26885014). Private lists can use the slug from the URL (e.g. favorites, watchlist). See documentation for details.",
        "text",
        required=True,
    ),
    "max_medias": FieldSpec(
        "max_medias",
        "Maximum items to display",
        None,
        "number",
        number=NumberSpec(1, 50),
        required=True,
        default=DEFAULT_MAX_MEDIAS,
    ),
    "media_type": FieldSpec(
        "media_type",
        "Filter media type",
        None,
        "select",
        options=LIST_MEDIA_TYPES,
        required=True,
        default="any",
    ),
    "sort_by": FieldSpec(
        "sort_by",
        "Sort by",
        None,
        "select",
        options=_get_sort_options(),
        required=True,
        default="rank",
    ),
    "sort_order": FieldSpec(
        "sort_order",
        "Sort order",
        None,
        "select",
        options=LIST_SORT_ORDER,
        required=True,
        default="asc",
    ),
    "exclude_collected": FieldSpec(
        "exclude_collected", "Exclude collected and watched items", None, "bool"
    ),
    "only_released": FieldSpec("only_released", "Only released items", None, "bool"),
}


def build_list_form_schema(current: Dict | None = None) -> vol.Schema:
    """Schema for a single list entry (add/edit)."""
    # Get current values if any
    cur = current or {}

    # Build Schema from LIST_FIELDS
    body: Dict = {}
    for key, fs in LIST_FIELDS.items():
        sel = _selector_for(fs)
        default = cur.get(key, fs.default)
        if fs.required:
            body[vol.Required(key, default=default)] = sel
        else:
            body[vol.Optional(key, default=default)] = sel

    return vol.Schema(body)


def parse_list_form(user_input: Dict, keep_friendly_name: str | None = None) -> Dict:
    """Normalize a single list entry from form data."""
    # Build entry from LIST_FIELDS
    entry = {}
    for key, fs in LIST_FIELDS.items():
        val = user_input.get(key, fs.default)

        # Normalize types
        if fs.kind == "number":
            val = int(val) if val is not None else fs.default
        elif fs.kind == "bool":
            val = bool(val)
        elif fs.kind == "text":
            val = (val or "").strip() if val is not None else fs.default

        entry[key] = val

    return entry


# ---- Translations (dev-time generation) ----


def build_translations_en() -> Dict:
    """Minimal en.json built from the same meta."""

    # Build sections from plans
    sections = {}
    for p in build_section_plans():
        # Leaf field labels for this section
        data_labels = {FIELDS[k].key: FIELDS[k].title for k in p.fields}
        data_desc = {
            k: FIELDS[k].description for k in data_labels if FIELDS[k].description
        }
        # Strip Nones
        data_desc = {k: v for k, v in data_desc.items() if v}

        sections[p.section_key] = {
            "name": p.name,
            "description": p.description or "",
            "data": data_labels,
        }
        if data_desc:
            sections[p.section_key]["data_description"] = data_desc

    # Generate translations for LIST_FIELDS
    list_data_labels = {k: v.title for k, v in LIST_FIELDS.items()}
    list_data_desc = {k: v.description for k, v in LIST_FIELDS.items() if v.description}

    return {
        "title": "Trakt TV",
        "config": {
            "step": {
                "user": {
                    "title": "Connect Trakt",
                    "description": "You will be redirected to Trakt to sign in.",
                },
                "profile": {
                    "title": "Profile settings",
                    "data": {
                        "language": "Language",
                        "update_interval": "API Update interval, minutes",
                    },
                },
                "reauth_confirm": {
                    "title": "Reauthenticate Trakt",
                    "description": "Your Trakt account needs to be re-authenticated. Continue to sign in.",
                },
            }
        },
        "options": {
            "step": {
                # Top-level menu
                "init": {"menu_options": MENU_INIT},
                # Sensors page, built from sections plans
                "sensors": {
                    "title": "Trakt sensors",
                    "description": "Configure which Trakt sensors to enable and their settings.",
                    "sections": sections,
                },
                # Lists submenu + forms
                "lists_menu": {"title": "Manage lists", "menu_options": MENU_LISTS},
                "lists_add": {
                    "title": "Add list",
                    "data": list_data_labels,
                    "data_description": list_data_desc,
                },
                "lists_edit_pick": {
                    "title": "Edit list",
                    "data": {"pick": "Select a list"},
                },
                "lists_edit": {
                    "title": "Edit list",
                    "data": list_data_labels,
                    "data_description": list_data_desc,
                },
                "lists_delete": {
                    "title": "Delete list(s)",
                    "data": {"names": "Choose list(s) to remove"},
                },
            },
            "error": {
                "name_exists": "A list with this name already exists.",
                "numeric_required_for_public": "For public lists, the List ID must be a numeric ID (not a slug).",
            },
        },
    }
