from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from dateutil.tz import tzlocal
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_LANGUAGE, CONF_SENSORS
from .models.kind import TraktKind


@dataclass
class Configuration:
    """Config accessor for the Trakt integration (per-entry)."""

    hass: HomeAssistant
    entry: ConfigEntry

    # ---------- Internal helpers ----------

    @property
    def _sensors(self) -> Dict[str, Any]:
        """The sensors options blob stored on the config entry."""
        return (self.entry.options or {}).get(CONF_SENSORS, {}) or {}

    # ---------- Public (backwards-friendly) API ----------

    def get_sensors(self) -> Dict[str, Any]:
        return self._sensors

    def get_language(self) -> str:
        return self.entry.data.get(CONF_LANGUAGE, "en")

    def get_timezone(self) -> str:
        # Use HA's configured timezone
        return self.hass.config.time_zone or (datetime.now(tzlocal()).tzname() or "UTC")

    def get_kinds(self, source: str) -> list[TraktKind]:
        """Return only enabled kinds for a source."""
        kinds: list[TraktKind] = []
        for ident, cfg in (self._sensors.get(source, {}) or {}).items():
            if isinstance(cfg, dict) and not cfg.get("enabled", True):
                continue
            try:
                kinds.append(TraktKind.from_string(ident))
            except Exception:
                continue
        return kinds

    # ----- Generic accessors over sensors -----

    def source_exists(self, source: str) -> bool:
        """Return True only if the source has something effectively enabled.

        - For dict sources (upcoming/all_upcoming/next_to_watch/...):
        require at least one subgroup with enabled=True (default True).
        - For list sources (e.g. 'list'): True if non-empty.
        - For anything else: truthy presence.
        """
        data = self._sensors.get(source)
        if not data:
            return False

        if isinstance(data, list):
            return len(data) > 0

        if isinstance(data, dict):
            # At least one enabled subgroup
            return any(
                (not isinstance(cfg, dict)) or cfg.get("enabled", True)
                for cfg in data.values()
            )

        return True

    def identifier_exists(self, identifier: str, source: str) -> bool:
        """True if the subgroup exists AND is enabled (default True)."""
        group = self._sensors.get(source, {}).get(identifier)
        if group is None:
            return False
        if isinstance(group, dict):
            return group.get("enabled", True)
        return True

    def get_days_to_fetch(self, identifier: str, source: str) -> int:
        return int(
            self._sensors.get(source, {}).get(identifier, {}).get("days_to_fetch", 30)
        )

    def get_max_medias(self, identifier: str, source: str) -> int:
        return int(
            self._sensors.get(source, {}).get(identifier, {}).get("max_medias", 3)
        )

    def get_exclude_items(self, identifier: str, source: str) -> List[str]:
        return list(
            self._sensors.get(source, {}).get(identifier, {}).get("exclude", []) or []
        )

    def get_exclude_collected(self, identifier: str, source: str) -> bool:
        return bool(
            self._sensors.get(source, {})
            .get(identifier, {})
            .get("exclude_collected", False)
        )

    # ----- Upcoming / All upcoming -----

    def upcoming_identifier_exists(
        self, identifier: str, all_medias: bool = False
    ) -> bool:
        source = "all_upcoming" if all_medias else "upcoming"
        return self.identifier_exists(identifier, source)

    def get_upcoming_days_to_fetch(
        self, identifier: str, all_medias: bool = False
    ) -> int:
        source = "all_upcoming" if all_medias else "upcoming"
        return self.get_days_to_fetch(identifier, source)

    def get_upcoming_max_medias(self, identifier: str, all_medias: bool = False) -> int:
        source = "all_upcoming" if all_medias else "upcoming"
        return self.get_max_medias(identifier, source)

    # ----- List -----

    def get_sensor_config(self, identifier: str) -> list:
        """Used for list-based sensors: returns the list for a given source key (e.g. 'list')."""
        return list(self._sensors.get(identifier, []) or [])
