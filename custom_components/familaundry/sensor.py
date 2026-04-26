import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_STORE_ID, CONF_STORE_NAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up FamiLaundry sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for machine_id in coordinator.data:
        entities.append(FamiLaundryStatusSensor(coordinator, machine_id, config_entry))
        entities.append(FamiLaundryFinishTimeSensor(coordinator, machine_id, config_entry))
        
    async_add_entities(entities)

class FamiLaundryBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for FamiLaundry sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, machine_id, config_entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._machine_id = machine_id
        self._store_id = config_entry.data[CONF_STORE_ID]
        self._store_name = config_entry.data.get(CONF_STORE_NAME, self._store_id)

        machine_data = self.coordinator.data[self._machine_id]
        self.machine_type = machine_data["name"]  # e.g., "洗+烘", "烘乾"
        self.machine_seq = machine_data["seq"]

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"{self._store_id}_{self._machine_id}")},
            "name": f"{self.machine_type} {self.machine_seq} ({self._store_name})",
            "manufacturer": "Fami Laundry",
            "configuration_url": "https://www.family.com.tw/Marketing/Laundry",
        }

class FamiLaundryStatusSensor(FamiLaundryBaseSensor):
    """FamiLaundry machine status sensor."""

    _attr_translation_key = "status"

    def __init__(self, coordinator, machine_id, config_entry):
        """Initialize the sensor."""
        super().__init__(coordinator, machine_id, config_entry)
        self._attr_unique_id = f"{DOMAIN}_{self._store_id}_{machine_id}_status"
        self.entity_id = f"sensor.{DOMAIN}_{self._store_id}_{machine_id}_status"

    @property
    def icon(self):
        """Return the icon based on status and machine type."""
        status = self.coordinator.data[self._machine_id]["status"]
        finish_time = self.coordinator.data[self._machine_id]["FINISH_TIME"]
        
        # 離線狀態
        if status == "2":
            return "mdi:washing-machine-off"
            
        # 待取件狀態
        if status == "1" and finish_time == "0":
            return "mdi:basket-check"
            
        if "洗" in self.machine_type and "烘" in self.machine_type:
            return "mdi:washing-machine"
        elif "烘" in self.machine_type:
            return "mdi:tumble-dryer"
        return "mdi:washing-machine"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        status = self.coordinator.data[self._machine_id]["status"]
        finish_time = self.coordinator.data[self._machine_id]["FINISH_TIME"]
        
        if status == "0":
            return "idle"
        elif status == "2":
            return "offline"
        elif status == "1":
            if finish_time == "0":
                return "finish"
            return "busy"
        return "unknown"

class FamiLaundryFinishTimeSensor(FamiLaundryBaseSensor):
    """FamiLaundry machine finish time sensor."""

    _attr_translation_key = "time_remaining"
    _attr_native_unit_of_measurement = "min"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator, machine_id, config_entry):
        """Initialize the sensor."""
        super().__init__(coordinator, machine_id, config_entry)
        self._attr_unique_id = f"{DOMAIN}_{self._store_id}_{machine_id}_finish_time"
        self.entity_id = f"sensor.{DOMAIN}_{self._store_id}_{machine_id}_time_remaining"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        try:
            return int(self.coordinator.data[self._machine_id]["FINISH_TIME"])
        except (ValueError, TypeError):
            return 0
