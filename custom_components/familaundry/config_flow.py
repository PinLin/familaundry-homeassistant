import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_STORE_ID, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, API_URL_COUNTRY, API_URL_AREA

class FamiLaundryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """FamiLaundry config flow."""
    
    VERSION = 1
    
    def __init__(self):
        """Initialize."""
        self._countries = {}
        self._stores = {}
        self._selected_country = None
        self._selected_store_id = None
        self._selected_store_name = None
        self._store_label = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return FamiLaundryOptionsFlowHandler()

    async def async_step_user(self, user_input=None):
        """Handle the initial step - choose county."""
        errors = {}

        if user_input is not None:
            self._selected_country = user_input["country"]
            return await self.async_step_store()

        if not self._countries:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(API_URL_COUNTRY, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            json_data = await response.json()
                            self._countries = {item["id"]: item["name"] for item in json_data.get("data", [])}
                        else:
                            errors["base"] = "cannot_connect"
                except Exception:
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("country"): vol.In(self._countries),
            }),
            errors=errors,
        )

    async def async_step_store(self, user_input=None):
        """Handle the second step - choose store."""
        errors = {}

        if not self._stores:
            self._stores = {}
            payload = {"CountryNo": self._selected_country}
            headers = {"Content-Type": "application/json;charset=utf-8", "User-Agent": "Mozilla/5.0"}
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(API_URL_AREA, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            json_data = await response.json()
                            for area in json_data.get("data", []):
                                area_name = area.get("AreaName", "")
                                for shop in area.get("ShopData", []):
                                    self._stores[shop["id"]] = f"{area_name} - {shop['name']}"
                        else:
                            errors["base"] = "cannot_connect"
                except Exception:
                    errors["base"] = "cannot_connect"

        if user_input is not None:
            self._selected_store_id = user_input[CONF_STORE_ID]
            self._store_label = self._stores.get(self._selected_store_id, f"Store {self._selected_store_id}")
            self._selected_store_name = self._store_label
            return await self.async_step_interval()
            
        return self.async_show_form(
            step_id="store",
            data_schema=vol.Schema({
                vol.Required(CONF_STORE_ID): vol.In(self._stores),
            }),
            errors=errors,
        )

    async def async_step_interval(self, user_input=None):
        """Handle the third step - set update interval."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._store_label, 
                data={
                    CONF_STORE_ID: self._selected_store_id,
                    "store_name": self._selected_store_name
                },
                options={
                    CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL]
                }
            )

        return self.async_show_form(
            step_id="interval",
            data_schema=vol.Schema({
                vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=30,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }),
        )

class FamiLaundryOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for FamiLaundry."""

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        update_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=update_interval,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=30,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }),
        )
