"""Config flow for Fami Laundry."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FamiLaundryApiClient, FamiLaundryApiError
from .const import (
    CONF_STORE_ID,
    CONF_STORE_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


class FamiLaundryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """FamiLaundry config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._countries: dict[str, str] = {}
        self._stores: dict[str, str] = {}
        self._store_shop_names: dict[str, str] = {}
        self._selected_country: str | None = None
        self._selected_store_id: str | None = None
        self._selected_store_name: str | None = None
        self._store_label: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FamiLaundryOptionsFlowHandler:
        return FamiLaundryOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 1 — choose county."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._selected_country = user_input["country"]
            return await self.async_step_store()

        if not self._countries:
            client = FamiLaundryApiClient(async_get_clientsession(self.hass))
            try:
                self._countries = await client.async_get_countries()
            except FamiLaundryApiError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("country"): vol.In(self._countries)}),
            errors=errors,
        )

    async def async_step_store(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 2 — choose store."""
        errors: dict[str, str] = {}

        if not self._stores and self._selected_country is not None:
            client = FamiLaundryApiClient(async_get_clientsession(self.hass))
            try:
                stores = await client.async_get_stores_by_country(self._selected_country)
            except FamiLaundryApiError:
                errors["base"] = "cannot_connect"
                stores = []
            for store_id, area_name, shop_name in stores:
                self._stores[store_id] = f"{area_name} - {shop_name}"
                self._store_shop_names[store_id] = shop_name

        if user_input is not None:
            self._selected_store_id = user_input[CONF_STORE_ID]
            await self.async_set_unique_id(self._selected_store_id)
            self._abort_if_unique_id_configured()
            self._store_label = self._stores.get(
                self._selected_store_id, f"Store {self._selected_store_id}"
            )
            self._selected_store_name = self._store_shop_names.get(
                self._selected_store_id, self._selected_store_id
            )
            return await self.async_step_interval()

        return self.async_show_form(
            step_id="store",
            data_schema=vol.Schema({vol.Required(CONF_STORE_ID): vol.In(self._stores)}),
            errors=errors,
        )

    async def async_step_interval(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 3 — set update interval."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._store_label or "",
                data={
                    CONF_STORE_ID: self._selected_store_id,
                    CONF_STORE_NAME: self._selected_store_name,
                },
                options={CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL]},
            )

        return self.async_show_form(
            step_id="interval",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=30, step=1, mode=selector.NumberSelectorMode.BOX
                        )
                    )
                }
            ),
        )


class FamiLaundryOptionsFlowHandler(config_entries.OptionsFlowWithReload):
    """Handle options flow for FamiLaundry.

    ``OptionsFlowWithReload`` (HA 2025.8+) reloads the entry automatically
    when options change, so the integration doesn't need to register an
    update listener.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        update_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=update_interval
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=30, step=1, mode=selector.NumberSelectorMode.BOX
                        )
                    )
                }
            ),
        )
