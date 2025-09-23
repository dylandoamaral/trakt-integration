"""Platform for sensor integration."""

import logging
from datetime import timedelta

from homeassistant.helpers.entity import Entity

from custom_components.trakt_tv.const import CONF_SENSORS

from .configuration import Configuration
from .const import DOMAIN
from .models.kind import BASIC_KINDS, NEXT_TO_WATCH_KINDS, TraktKind

LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=8)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform from a config entry."""
    # fetch coordinator from the per-entry bucket
    bucket = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = bucket["coordinator"]

    # read options from OptionsFlow
    sensors_opts = (config_entry.options or {}).get(CONF_SENSORS, {})

    # Get name of the integration to use in prefix
    integration_name = config_entry.title

    def _is_enabled(group_opts: dict) -> bool:
        return bool(group_opts.get("enabled", False))

    # Configure data sources
    data_sources = [
        {"name": "upcoming", "prefix": "Upcoming", "icon": "mdi:calendar"},
        {"name": "all_upcoming", "prefix": "All Upcoming", "icon": "mdi:calendar"},
        {
            "name": "next_to_watch",
            "prefix": "Next to Watch",
            "icon": "mdi:calendar",
            "kinds": NEXT_TO_WATCH_KINDS,
        },
        {
            "name": "anticipated",
            "prefix": "Anticipated",
            "icon": {TraktKind.MOVIE: "mdi:movie", TraktKind.SHOW: "mdi:television"},
            "kinds": BASIC_KINDS,
        },
        {
            "name": "recommendation",
            "prefix": "Recommendation",
            "icon": {TraktKind.MOVIE: "mdi:movie", TraktKind.SHOW: "mdi:television"},
            "kinds": BASIC_KINDS,
        },
    ]

    sensors = []
    # Add sensors for each data source and kind
    for data_source in data_sources:
        kinds = data_source.get("kinds", TraktKind)
        opts = sensors_opts.get(data_source["name"], {})

        for trakt_kind in kinds:
            identifier = trakt_kind.value.identifier

            g = opts.get(identifier, {})

            if _is_enabled(g):
                prefix = f"{integration_name} {data_source['prefix']}"

                # Icon can be a dict (for anticipated) or a string
                mdi_icon = data_source["icon"]
                if isinstance(mdi_icon, dict):
                    mdi_icon = mdi_icon.get(trakt_kind, "mdi:movie")

                sensor = TraktSensor(
                    hass=hass,
                    config_entry=config_entry,
                    coordinator=coordinator,
                    trakt_kind=trakt_kind,
                    source=data_source["name"],
                    prefix=prefix,
                    mdi_icon=mdi_icon,
                )
                sensors.append(sensor)

    # Add sensors for stats
    g = sensors_opts.get("stats", {}).get("all", {})
    if _is_enabled(g):
        stats = {}
        # Check if the coordinator has data
        if coordinator.data:
            stats = coordinator.data.get("stats", {})

        # Create a sensor for each key in the stats
        for key, value in stats.items():
            # Skip the key if it is not a valid state (e.g. rating distribution dict)
            if isinstance(value, dict):
                continue

            # Create the sensor
            sensor = TraktStateSensor(
                hass=hass,
                config_entry=config_entry,
                coordinator=coordinator,
                prefix=f"{integration_name} Stats",
                mdi_icon="mdi:chart-line",
                data_key=key,
                state=value,
            )
            sensors.append(sensor)

    # Add lists
    for list_entry in sensors_opts.get("lists", []):
        sensor = TraktSensor(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            trakt_kind=TraktKind.LIST,
            source="lists",
            prefix=f"{integration_name} {list_entry['friendly_name']}",
            mdi_icon="mdi:view-list",
            sensor_data=list_entry,
            sensor_identifier=list_entry["friendly_name"].replace(" ", "_").lower(),
        )
        sensors.append(sensor)

    async_add_entities(sensors)


class TraktSensor(Entity):
    """Representation of a trakt sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass,
        config_entry,
        coordinator,
        trakt_kind: TraktKind,
        source: str,
        prefix: str,
        mdi_icon: str,
        sensor_data: dict | None = None,
        sensor_identifier: str | None = None,
    ):
        """Initialize the sensor."""
        self.hass = hass
        self.config_entry = config_entry
        self.coordinator = coordinator
        self.trakt_kind = trakt_kind
        self.source = source
        self.prefix = prefix
        self.mdi_icon = mdi_icon
        self.sensor_data = sensor_data
        self._attr_unique_id = f"{self.config_entry.entry_id}_{self.source}_{self.trakt_kind.value.identifier}{f'_{sensor_identifier}' if sensor_identifier else ''}"

    @property
    def name(self):
        """Return the name of the sensor."""
        if not self.trakt_kind.value.name:
            return f"{self.prefix}"
        return f"{self.prefix} {self.trakt_kind.value.name}"

    @property
    def medias(self):
        """Return the media list of the sensor."""
        if not self.coordinator.data:
            return None

        if self.trakt_kind == TraktKind.LIST:
            try:
                name = self.sensor_data["friendly_name"]
                return self.coordinator.data[self.source][self.trakt_kind][name]
            except KeyError:
                return None
            except TypeError:
                return None

        try:
            return self.coordinator.data[self.source][self.trakt_kind]
        except KeyError:
            return None

    @property
    def configuration(self):
        cfg = Configuration(self.hass, self.config_entry)
        sensors = cfg.get_sensors()
        identifier = self.trakt_kind.value.identifier
        source = (
            "next_to_watch" if self.trakt_kind in NEXT_TO_WATCH_KINDS else self.source
        )
        return (sensors.get(source, {}) or {}).get(identifier, {}) or {}

    @property
    def data(self):
        if not self.medias:
            return []

        if self.trakt_kind == TraktKind.LIST:
            sort_by = self.sensor_data["sort_by"]
            sort_order = self.sensor_data["sort_order"]
            max_medias = int(self.sensor_data["max_medias"])
            return self.medias.to_homeassistant(sort_by, sort_order)[0 : max_medias + 1]

        max_medias = int(self.configuration["max_medias"])
        return self.medias.to_homeassistant()[0 : max_medias + 1]

    @property
    def state(self):
        """Return the state of the sensor."""
        return max([len(self.data) - 1, 0])

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self.mdi_icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self.trakt_kind.value.unit:
            return self.trakt_kind.value.unit
        return self.trakt_kind.value.path.split("/")[0]

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {"data": self.data}

    @property
    def has_entity_name(self) -> bool:
        """Return if the name of the entity is describing only the entity itself."""
        return True

    async def async_update(self):
        """Request coordinator to update data."""
        await self.coordinator.async_request_refresh()


class TraktStateSensor(Entity):
    """Trakt sensor to show data as state"""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass,
        config_entry,
        coordinator,
        prefix: str,
        mdi_icon: str,
        data_key: str,
        state: str,
    ):
        """Initialize the sensor."""
        self.hass = hass
        self.config_entry = config_entry
        self.coordinator = coordinator
        self.prefix = prefix
        self.icon = mdi_icon
        self.data_key = data_key
        self.state = state
        self.title = data_key.replace("_", " ").title()
        self._attr_unique_id = f"{self.config_entry.entry_id}_stats_{self.data_key}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.prefix} {self.title}"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity"""
        units = [
            "ratings",
            "minutes",
            "comments",
            "friends",
            "followers",
            "following",
            "episodes",
            "movies",
            "shows",
            "seasons",
        ]
        for unit in units:
            if unit in self.title.lower():
                return unit
        return None

    async def async_update(self):
        """Request coordinator to update data."""
        await self.coordinator.async_request_refresh()
