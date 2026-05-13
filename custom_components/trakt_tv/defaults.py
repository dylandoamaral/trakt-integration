"""Default sensor configuration for UI-managed setup."""

from typing import Any, Dict, Optional

from .models.kind import (
    ANTICIPATED_KINDS,
    BASIC_KINDS,
    NEXT_TO_WATCH_KINDS,
    UPCOMING_KINDS,
)

SENSOR_GROUPS = [
    "upcoming",
    "all_upcoming",
    "next_to_watch",
    "recommendation",
    "anticipated",
    "watchlist",
    "stats",
    "now_playing",
]

DEFAULT_ENABLED_GROUPS = {group: True for group in SENSOR_GROUPS}


def _upcoming_defaults() -> Dict[str, Any]:
    return {
        trakt_kind.value.identifier: {
            "days_to_fetch": 30,
            "max_medias": 3,
        }
        for trakt_kind in UPCOMING_KINDS
    }


def _next_to_watch_defaults() -> Dict[str, Any]:
    return {
        trakt_kind.value.identifier: {
            "max_medias": 3,
            "exclude": [],
            "sort_by": "released",
            "sort_order": "asc",
        }
        for trakt_kind in NEXT_TO_WATCH_KINDS
    }


def _recommendation_defaults() -> Dict[str, Any]:
    return {
        trakt_kind.value.identifier: {"max_medias": 3} for trakt_kind in BASIC_KINDS
    }


def _anticipated_defaults() -> Dict[str, Any]:
    return {
        trakt_kind.value.identifier: {
            "max_medias": 3,
            "exclude_collected": False,
        }
        for trakt_kind in ANTICIPATED_KINDS
    }


def _watchlist_defaults() -> Dict[str, Any]:
    base = {
        "only_released": True,
        "only_unwatched": True,
        "max_medias": 20,
        "sort_by": "released",
        "sort_order": "asc",
    }
    return {"movie": dict(base), "show": dict(base)}


def default_sensor_config_for_group(group: str) -> Any:
    """Return the default config payload for a known sensor group."""
    if group == "upcoming" or group == "all_upcoming":
        return _upcoming_defaults()
    if group == "next_to_watch":
        return _next_to_watch_defaults()
    if group == "recommendation":
        return _recommendation_defaults()
    if group == "anticipated":
        return _anticipated_defaults()
    if group == "watchlist":
        return _watchlist_defaults()
    if group == "stats":
        return ["all"]
    if group == "now_playing":
        return {"enabled": True}
    return None


def build_default_sensors_config() -> Dict[str, Any]:
    """Build the full default sensors dict for UI-only installs."""
    sensors: Dict[str, Any] = {}
    for group in SENSOR_GROUPS:
        value = default_sensor_config_for_group(group)
        if value is not None:
            sensors[group] = value
    return sensors


def options_enabled_groups(options: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    """Return the enabled state for each sensor group, honoring options."""
    options = options or {}
    enabled = {}
    for group in SENSOR_GROUPS:
        opt_key = f"enable_{group}"
        enabled[group] = bool(options.get(opt_key, True))
    return enabled


def apply_options_to_sensors(
    sensors: Dict[str, Any], options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Filter a sensors dict based on per-group enable toggles in options."""
    enabled = options_enabled_groups(options)
    return {
        group: value
        for group, value in sensors.items()
        if group not in SENSOR_GROUPS or enabled.get(group, True)
    }


def merge_sensor_config(
    yaml_sensors: Optional[Dict[str, Any]],
    options: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Merge YAML-provided sensors with defaults and apply options toggles.

    YAML always wins for groups it declares. Groups absent from YAML get the
    in-code default. Groups disabled via options are removed at the end.
    """
    sensors: Dict[str, Any] = {}
    for group in SENSOR_GROUPS:
        value = default_sensor_config_for_group(group)
        if value is not None:
            sensors[group] = value

    if yaml_sensors:
        for key, value in yaml_sensors.items():
            sensors[key] = value

    return apply_options_to_sensors(sensors, options)
