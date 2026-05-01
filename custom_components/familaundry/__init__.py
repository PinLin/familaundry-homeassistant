"""Fami Laundry Home Assistant integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FamiLaundryApiClient
from .const import CONF_STORE_ID, DOMAIN, SERVICE_UPDATE
from .coordinator import FamiLaundryCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FamiLaundry from a config entry."""
    client = FamiLaundryApiClient(async_get_clientsession(hass))

    coordinator = FamiLaundryCoordinator(hass, entry, client)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(f"First refresh failed: {err}") from err

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_UPDATE):

        async def _handle_update(call: ServiceCall) -> None:
            store_ids: list[str] = call.data.get("store_ids", [])
            for config_entry in hass.config_entries.async_entries(DOMAIN):
                if store_ids and config_entry.data.get(CONF_STORE_ID) not in store_ids:
                    continue
                if not hasattr(config_entry, "runtime_data"):
                    continue
                await config_entry.runtime_data.async_request_refresh()

        hass.services.async_register(
            DOMAIN,
            SERVICE_UPDATE,
            _handle_update,
            schema=vol.Schema(
                {vol.Optional("store_ids", default=[]): vol.All(cv.ensure_list, [cv.string])}
            ),
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        remaining = [
            config_entry
            for config_entry in hass.config_entries.async_entries(DOMAIN)
            if config_entry.entry_id != entry.entry_id
        ]
        if not remaining:
            hass.services.async_remove(DOMAIN, SERVICE_UPDATE)
    return unload_ok
