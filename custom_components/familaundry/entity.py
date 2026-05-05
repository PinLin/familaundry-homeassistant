"""Shared entity helpers for Fami Laundry."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STORE_ID, CONF_STORE_NAME, DOMAIN
from .coordinator import FamiLaundryCoordinator, MachineData


def device_id_for(store_id: str, machine_id: str) -> str:
    """Stable device identifier used in unique_id and device.identifiers."""
    return f"{store_id}_{machine_id}"


def stable_object_id(store_id: str, machine_id: str, attribute: str) -> str:
    """Object id that stays English-only (avoids HA's pinyin auto-conversion)."""
    return f"{DOMAIN}_{store_id}_{machine_id}_{attribute}"


def stable_entity_id(
    platform: str, store_id: str, machine_id: str, attribute: str
) -> str:
    return f"{platform}.{stable_object_id(store_id, machine_id, attribute)}"


class FamiLaundryEntity(CoordinatorEntity[FamiLaundryCoordinator]):
    """Common base for Fami Laundry entities.

    Each subclass declares ``_attribute`` — used as the translation key,
    suggested object_id suffix, and entity_id suffix. ``_legacy_uid_suffix``
    can override the suffix used for ``unique_id`` only; this is how we keep
    pre-existing entities (e.g. ``finish_time`` instead of ``time_remaining``)
    from being recreated as duplicates after the refactor.
    """

    _attr_has_entity_name = True
    _attribute: str
    _legacy_uid_suffix: str | None = None

    # Subclasses list the entity property names that, when changed, require
    # broadcasting a new state to HA. Each coordinator refresh fans out to
    # every entity's _handle_coordinator_update; this guard suppresses
    # async_write_ha_state when the snapshot of those properties is
    # unchanged. An empty tuple keeps the default CoordinatorEntity
    # behaviour (broadcast on every refresh).
    _state_attrs: tuple[str, ...] = ()

    def __init__(
        self,
        coordinator: FamiLaundryCoordinator,
        machine_id: str,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._machine_id = machine_id
        self._store_id: str = entry.data[CONF_STORE_ID]
        self._store_name: str = entry.data.get(CONF_STORE_NAME, self._store_id)
        self._last_broadcast_state: tuple[Any, ...] | None = None

        uid_suffix = self._legacy_uid_suffix or self._attribute
        self._attr_unique_id = (
            f"{DOMAIN}_{self._store_id}_{self._machine_id}_{uid_suffix}"
        )
        self._attr_translation_key = self._attribute
        self._attr_suggested_object_id = stable_object_id(
            self._store_id, self._machine_id, self._attribute
        )
        self.entity_id = stable_entity_id(
            "sensor", self._store_id, self._machine_id, self._attribute
        )

    async def async_added_to_hass(self) -> None:
        """Seed the last-broadcast snapshot so the first real update is honest."""
        await super().async_added_to_hass()
        self._refresh_last_broadcast()

    def _refresh_last_broadcast(self) -> bool:
        """Recompute the snapshot. Return True if it differs from the prior one."""
        if not self._state_attrs:
            return True
        snapshot = tuple(getattr(self, attr, None) for attr in self._state_attrs)
        if snapshot != self._last_broadcast_state:
            self._last_broadcast_state = snapshot
            return True
        return False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Only broadcast when the entity's tracked state actually changed."""
        if self._refresh_last_broadcast():
            self.async_write_ha_state()

    @property
    def _machine(self) -> MachineData | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._machine_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"store_id": self._store_id}

    @property
    def device_info(self) -> DeviceInfo:
        m = self._machine
        if m is not None:
            label = f"{m.name} {m.seq} ({self._store_name})"
        else:
            label = f"{self._machine_id} ({self._store_name})"
        return DeviceInfo(
            identifiers={(DOMAIN, device_id_for(self._store_id, self._machine_id))},
            name=label,
            manufacturer="Fami Laundry",
            model=self._store_id,
        )
