"""Diagnostics support for Fami Laundry."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# Conservative default redaction set. FamiLaundry data is mostly public store
# information, but if we ever start storing auth tokens these keys are already
# covered. Keep this set in sync with what the API client / config flow stores.
REDACT_KEYS = {
    "access_token",
    "refresh_token",
    "password",
    "api_key",
}


def _serialize(obj: Any) -> Any:
    """Convert nested dataclasses to plain dicts so async_redact_data can walk them."""
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    return obj


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostic info for one config entry."""
    coordinator = entry.runtime_data
    raw_data = coordinator.data if coordinator is not None else None
    last_update = coordinator.last_update if coordinator is not None else None

    return {
        "entry": async_redact_data(entry.as_dict(), REDACT_KEYS),
        "coordinator": {
            "last_update": last_update.isoformat() if last_update else None,
            "last_update_success": (
                coordinator.last_update_success if coordinator is not None else None
            ),
        },
        "data": async_redact_data(_serialize(raw_data), REDACT_KEYS),
    }
