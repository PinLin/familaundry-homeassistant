import asyncio
import logging
from datetime import timedelta
import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, API_URL, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

_RETRY_COUNT = 3
_RETRY_DELAY = 5  # seconds between retries
_REQUEST_TIMEOUT = 30  # seconds per attempt
_MAX_CONSECUTIVE_FAILURES = 2  # raise UpdateFailed only after this many consecutive failures


class FamiLaundryCoordinator(DataUpdateCoordinator):
    """FamiLaundry data update coordinator."""

    def __init__(self, hass, store_id, update_interval):
        """Initialize the coordinator."""
        self._store_id = store_id
        self._consecutive_failures = 0
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _fetch_once(self, session):
        """Perform a single API request and return parsed data."""
        payload = {"store": self._store_id}
        headers = {
            "Content-Type": "application/json;charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:150.0) Gecko/20100101 Firefox/150.0",
        }
        timeout = aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT)
        async with session.post(API_URL, json=payload, headers=headers, timeout=timeout) as response:
            if response.status != 200:
                raise UpdateFailed(f"API returned status {response.status}")
            json_data = await response.json(content_type=None)
            if json_data.get("syscode") != "200":
                raise UpdateFailed(f"API returned error: {json_data.get('sysmsg')}")
            return {machine["id"]: machine for machine in json_data.get("data", [])}

    async def _async_update_data(self):
        """Fetch data from API with retry logic."""
        last_err = None
        async with aiohttp.ClientSession() as session:
            for attempt in range(_RETRY_COUNT):
                try:
                    data = await self._fetch_once(session)
                    self._consecutive_failures = 0
                    return data
                except UpdateFailed as err:
                    # Non-retryable API errors (bad status, wrong syscode)
                    last_err = err
                    _LOGGER.debug("API error on attempt %d/%d: %s", attempt + 1, _RETRY_COUNT, err)
                except (asyncio.TimeoutError, aiohttp.ClientError) as err:
                    last_err = UpdateFailed(f"Network error while fetching data: {err}")
                    _LOGGER.debug("Network error on attempt %d/%d: %s", attempt + 1, _RETRY_COUNT, err)

                if attempt < _RETRY_COUNT - 1:
                    await asyncio.sleep(_RETRY_DELAY)

        self._consecutive_failures += 1
        if self._consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
            _LOGGER.warning(
                "FamiLaundry: %d consecutive failures, marking entities unavailable. Last error: %s",
                self._consecutive_failures,
                last_err,
            )
            raise last_err

        _LOGGER.warning(
            "FamiLaundry: transient failure (%d/%d), keeping last known data. Error: %s",
            self._consecutive_failures,
            _MAX_CONSECUTIVE_FAILURES,
            last_err,
        )
        # Return last known data to keep sensors available during transient failures
        return self.data
