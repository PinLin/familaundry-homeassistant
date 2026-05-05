"""Data coordinator for Fami Laundry."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import FamiLaundryApiClient, FamiLaundryApiError
from .const import (
    CONF_STORE_ID,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_RETRY_COUNT = 3
_RETRY_DELAY = 5  # seconds between retries
# Tolerate this many consecutive failures by returning last-known data so a
# brief upstream blip doesn't make every machine entity flip to unavailable.
_MAX_CONSECUTIVE_FAILURES = 2
# Threshold for surfacing a repair issue. With the default 60s polling
# cadence this is ~10 minutes of sustained failure — enough that a real
# outage is happening and not just a transient blip.
_FAILURES_BEFORE_ISSUE = 10
ISSUE_POLLING_FAILING = "polling_failing"


@dataclass(frozen=True)
class MachineData:
    """Snapshot of one laundry machine, normalized from the API payload."""

    id: str
    name: str           # 機台類型: "洗+烘"、"烘乾"
    seq: str            # 同類型內的序號
    status: str         # raw API code: "0" idle / "1" running / "2" offline
    finish_time: str    # raw API code: 剩餘分鐘字串; status="1"+finish_time="0" = 待取件

    @property
    def state(self) -> str:
        """Map raw API status + finish_time to a stable HA state string.

        These are the values exposed in entity.state, so the strings.json
        translation keys (idle/busy/finish/offline/unknown) must match.
        """
        if self.status == "0":
            return "idle"
        if self.status == "2":
            return "offline"
        if self.status == "1":
            return "finish" if self.finish_time == "0" else "busy"
        return "unknown"

    @property
    def remaining_minutes(self) -> int:
        """Parse finish_time as int. The API sends a string, sometimes empty."""
        try:
            return int(self.finish_time)
        except (ValueError, TypeError):
            return 0


def _to_machine(raw: dict[str, Any]) -> MachineData:
    return MachineData(
        id=str(raw.get("id", "")),
        name=str(raw.get("name", "")),
        seq=str(raw.get("seq", "")),
        status=str(raw.get("status", "")),
        finish_time=str(raw.get("FINISH_TIME", "")),
    )


class FamiLaundryCoordinator(DataUpdateCoordinator[dict[str, MachineData]]):
    """Polls the Fami Laundry API for one store."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: FamiLaundryApiClient,
    ) -> None:
        self._entry = entry
        self._client = client
        self._store_id: str = entry.data[CONF_STORE_ID]
        self._consecutive_failures = 0
        self._last_update: datetime | None = None

        update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            # Unique per entry so multi-entry logs don't all collide under one logger.
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=update_interval),
        )

    @property
    def last_update(self) -> datetime | None:
        """Wall-clock time of the last successful API fetch."""
        return self._last_update

    async def _async_update_data(self) -> dict[str, MachineData]:
        last_err: Exception | None = None
        for attempt in range(_RETRY_COUNT):
            try:
                machines = await self._client.async_get_machines(self._store_id)
                self._consecutive_failures = 0
                self._last_update = dt_util.now()
                self._clear_polling_issue()
                return {m.id: m for m in (_to_machine(raw) for raw in machines) if m.id}
            except FamiLaundryApiError as err:
                last_err = err
                _LOGGER.debug(
                    "API error on attempt %d/%d: %s", attempt + 1, _RETRY_COUNT, err
                )
            except (asyncio.TimeoutError, aiohttp.ClientError) as err:
                last_err = err
                _LOGGER.debug(
                    "Network error on attempt %d/%d: %s", attempt + 1, _RETRY_COUNT, err
                )

            if attempt < _RETRY_COUNT - 1:
                await asyncio.sleep(_RETRY_DELAY)

        self._consecutive_failures += 1
        if self._consecutive_failures >= _FAILURES_BEFORE_ISSUE:
            self._raise_polling_issue()

        if self._consecutive_failures >= _MAX_CONSECUTIVE_FAILURES or self.data is None:
            _LOGGER.warning(
                "FamiLaundry: %d consecutive failures, marking entities unavailable. Last error: %s",
                self._consecutive_failures,
                last_err,
            )
            raise UpdateFailed(f"API failed after {_RETRY_COUNT} attempts: {last_err}")

        _LOGGER.warning(
            "FamiLaundry: transient failure (%d/%d), keeping last known data. Error: %s",
            self._consecutive_failures,
            _MAX_CONSECUTIVE_FAILURES,
            last_err,
        )
        return self.data

    def _raise_polling_issue(self) -> None:
        """Surface a Repairs entry once sustained polling failure crosses the threshold."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            f"{ISSUE_POLLING_FAILING}_{self._entry.entry_id}",
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_POLLING_FAILING,
            translation_placeholders={"store_id": self._store_id},
        )

    def _clear_polling_issue(self) -> None:
        """Drop the Repairs entry once the next refresh succeeds."""
        ir.async_delete_issue(
            self.hass, DOMAIN, f"{ISSUE_POLLING_FAILING}_{self._entry.entry_id}"
        )
