"""API client for Fami Laundry."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_URL, API_URL_AREA, API_URL_COUNTRY, USER_AGENT

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=30)
_JSON_HEADERS = {
    "Content-Type": "application/json;charset=utf-8",
    "User-Agent": USER_AGENT,
}
_PLAIN_HEADERS = {"User-Agent": USER_AGENT}


class FamiLaundryApiError(Exception):
    """Raised when the upstream API returns an error or unparseable response."""


class FamiLaundryApiClient:
    """Client for the Fami Laundry endpoints. Receives a shared aiohttp session."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _post_json(
        self,
        url: str,
        *,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=headers or _JSON_HEADERS,
                timeout=_TIMEOUT,
            ) as response:
                if response.status != 200:
                    raise FamiLaundryApiError(f"HTTP {response.status} from {url}")
                return await response.json(content_type=None)
        except aiohttp.ClientError as err:
            raise FamiLaundryApiError(f"network error talking to {url}: {err}") from err

    async def async_get_machines(self, store_id: str) -> list[dict[str, Any]]:
        """Fetch raw machine list for a store. Returns the data array as-is."""
        data = await self._post_json(API_URL, payload={"store": store_id})
        if data.get("syscode") != "200":
            raise FamiLaundryApiError(f"API error: {data.get('sysmsg')}")
        return list(data.get("data", []))

    async def async_get_countries(self) -> dict[str, str]:
        """Fetch the list of counties keyed by id."""
        data = await self._post_json(API_URL_COUNTRY, headers=_PLAIN_HEADERS)
        return {item["id"]: item["name"] for item in data.get("data", [])}

    async def async_get_stores_by_country(
        self, country_no: str
    ) -> list[tuple[str, str, str]]:
        """Fetch stores for a county. Returns a list of (store_id, area_name, shop_name)."""
        data = await self._post_json(API_URL_AREA, payload={"CountryNo": country_no})
        results: list[tuple[str, str, str]] = []
        for area in data.get("data", []):
            area_name = str(area.get("AreaName", ""))
            for shop in area.get("ShopData", []):
                results.append((str(shop["id"]), area_name, str(shop["name"])))
        return results
