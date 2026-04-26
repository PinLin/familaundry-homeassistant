"""Sensor entities for Fami Laundry."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FamiLaundryCoordinator
from .entity import FamiLaundryEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FamiLaundry sensor platform."""
    coordinator: FamiLaundryCoordinator = config_entry.runtime_data

    entities: list[SensorEntity] = []
    for machine_id in (coordinator.data or {}):
        entities.append(StatusSensor(coordinator, machine_id, config_entry))
        entities.append(TimeRemainingSensor(coordinator, machine_id, config_entry))
    async_add_entities(entities)


class StatusSensor(FamiLaundryEntity, SensorEntity):
    """Machine status: idle / busy / finish / offline / unknown."""

    _attribute = "status"

    @property
    def icon(self) -> str:
        m = self._machine
        if m is None:
            return "mdi:washing-machine"
        if m.status == "2":
            return "mdi:washing-machine-off"
        if m.status == "1" and m.finish_time == "0":
            return "mdi:basket-check"
        if "洗" in m.name and "烘" in m.name:
            return "mdi:washing-machine"
        if "烘" in m.name:
            return "mdi:tumble-dryer"
        return "mdi:washing-machine"

    @property
    def native_value(self) -> str | None:
        m = self._machine
        return m.state if m else None


class TimeRemainingSensor(FamiLaundryEntity, SensorEntity):
    """Minutes remaining until the cycle finishes."""

    # entity_id and translation key use the user-facing name…
    _attribute = "time_remaining"
    # …but keep the original unique_id suffix so existing entries don't get
    # reissued as duplicates after the refactor.
    _legacy_uid_suffix = "finish_time"

    _attr_native_unit_of_measurement = "min"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_icon = "mdi:timer-sand"

    @property
    def native_value(self) -> int | None:
        m = self._machine
        return m.remaining_minutes if m else None
