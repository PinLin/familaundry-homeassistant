import asyncio
import logging
from datetime import timedelta
import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, API_URL, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

class FamiLaundryCoordinator(DataUpdateCoordinator):
    """FamiLaundry data update coordinator."""

    def __init__(self, hass, store_id, update_interval):
        """Initialize the coordinator."""
        self._store_id = store_id
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        payload = {"store": self._store_id}
        headers = {
            "Content-Type": "application/json;charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:150.0) Gecko/20100101 Firefox/150.0",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, json=payload, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"API returned status {response.status}")
                    
                    json_data = await response.json()
                    if json_data.get("syscode") != "200":
                        raise UpdateFailed(f"API returned error: {json_data.get('sysmsg')}")
                    
                    return {machine["id"]: machine for machine in json_data.get("data", [])}
                    
        except asyncio.TimeoutError as err:
            raise UpdateFailed(f"Timeout while fetching data: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
