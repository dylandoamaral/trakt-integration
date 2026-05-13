"""The Trakt integration."""

import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .apis.trakt import TraktApi
from .config_flow import OAuth2FlowHandler
from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from .defaults import merge_sensor_config, options_enabled_groups
from .exception import TraktException
from .schema import configuration_schema
from .utils import update_domain_data

LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = configuration_schema
PLATFORMS = ["sensor"]


def _default_language() -> str:
    return "en"


def _default_timezone() -> str:
    tz = datetime.now(ZoneInfo("UTC")).astimezone().tzname()
    return tz or "UTC"


def _build_configuration(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Compose the effective configuration: YAML + defaults + options."""
    yaml_config = hass.data.get(DOMAIN, {}).get("yaml_configuration") or {}
    yaml_sensors = yaml_config.get("sensors") if isinstance(yaml_config, dict) else None

    sensors = merge_sensor_config(yaml_sensors, entry.options)

    return {
        "client_id": entry.data[CONF_CLIENT_ID],
        "sensors": sensors,
        "language": yaml_config.get("language", _default_language()),
        "timezone": yaml_config.get("timezone", _default_timezone()),
    }


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the TraktTV component from a yaml (optional)."""
    yaml_config = CONFIG_SCHEMA(config).get(DOMAIN, {})
    update_domain_data(hass, "yaml_configuration", yaml_config)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up TraktTV from a config entry."""
    OAuth2FlowHandler.async_register_implementation(
        hass,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )

    implementation = await async_get_config_entry_implementation(hass, entry)
    session = OAuth2Session(hass, entry, implementation)

    configuration = _build_configuration(hass, entry)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["configuration"] = configuration

    api = TraktApi(async_get_clientsession(hass), session, hass)

    async def async_update_data():
        try:
            return await api.retrieve_data()
        except TraktException as err:
            raise UpdateFailed(f"Communication error with Trakt API: {err}")

    coordinator = DataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name="trakt",
        update_method=async_update_data,
    )

    await coordinator.async_config_entry_first_refresh()

    instances = {
        "coordinator": coordinator,
        "api": api,
    }

    enabled_groups = options_enabled_groups(entry.options)
    if enabled_groups.get("now_playing", True):

        async def async_update_now_playing_data():
            try:
                return await api.fetch_now_playing()
            except TraktException as err:
                raise UpdateFailed(f"Communication error with Trakt API: {err}")

        now_playing_coordinator = DataUpdateCoordinator(
            hass=hass,
            logger=LOGGER,
            name="trakt_now_playing",
            update_method=async_update_now_playing_data,
            update_interval=timedelta(seconds=30),
        )
        await now_playing_coordinator.async_config_entry_first_refresh()
        instances["now_playing_coordinator"] = now_playing_coordinator

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["instances"] = instances

    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when the options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
