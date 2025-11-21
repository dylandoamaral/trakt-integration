"""The Trakt integration."""

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .apis.trakt import TraktApi
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN

LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Trakt TV from a modern OAuth config entry (no legacy fallbacks)."""

    # Get the OAuth implementation saved by HA during your config flow
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except Exception as err:
        # No implementation = app credentials missing/misconfigured
        raise ConfigEntryNotReady(
            "Trakt OAuth implementation not found. Ensure Application Credentials are configured for this integration."
        ) from err

    # OAuth2 session (handles refresh automatically)
    session = OAuth2Session(hass, entry, implementation)

    # API client
    api = TraktApi(async_get_clientsession(hass), session, hass, entry)

    coordinator = DataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name="trakt",
        update_method=api.retrieve_data,
        update_interval=timedelta(
            minutes=entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        ),
    )

    await coordinator.async_config_entry_first_refresh()

    # Store per-entry data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "session": session,
        "api": api,
        "coordinator": coordinator,
    }

    # Reload on options change (toggles, intervals, etc.)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    # Forward platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options updates by reloading the entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Trakt config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data.pop(DOMAIN)

    return unload_ok
