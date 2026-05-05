"""Diagnostics support for Fami Laundry."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN

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


async def async_get_device_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device: DeviceEntry,
) -> dict[str, Any]:
    """Return diagnostics for a single machine.

    Includes the machine snapshot the coordinator stores plus a roster
    of entities registered for the device with their current state and
    attributes — enough to triage "this entity shows wrong value" bug
    reports without asking for screenshots.
    """
    coordinator = entry.runtime_data

    # Resolve machine_id from the device's identifiers; entity.py builds
    # device_id_for(store_id, machine_id) → "<store>_<machine>". The
    # store id can itself contain underscores, so split on the LAST one.
    machine_id: str | None = None
    for ident_domain, identifier in device.identifiers:
        if ident_domain != DOMAIN:
            continue
        _, _, machine = identifier.rpartition("_")
        if machine:
            machine_id = machine
        break

    machine_snapshot: Any = None
    if machine_id and coordinator.data is not None:
        machine = coordinator.data.get(machine_id)
        if machine is not None:
            machine_snapshot = _serialize(machine)

    ent_reg = er.async_get(hass)
    entities: list[dict[str, Any]] = []
    for ent in er.async_entries_for_device(
        ent_reg, device.id, include_disabled_entities=True
    ):
        state = hass.states.get(ent.entity_id)
        entities.append(
            {
                "entity_id": ent.entity_id,
                "unique_id": ent.unique_id,
                "platform": ent.platform,
                "domain": ent.domain,
                "translation_key": ent.translation_key,
                "device_class": ent.device_class or ent.original_device_class,
                "disabled_by": ent.disabled_by,
                "state": state.state if state else None,
                "attributes": dict(state.attributes) if state else None,
            }
        )

    return {
        "device": {
            "id": device.id,
            "name": device.name,
            "name_by_user": device.name_by_user,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "identifiers": [list(i) for i in device.identifiers],
        },
        "machine_id": machine_id,
        "machine": (
            async_redact_data(machine_snapshot, REDACT_KEYS)
            if machine_snapshot is not None
            else None
        ),
        "entities": async_redact_data(entities, REDACT_KEYS),
    }
