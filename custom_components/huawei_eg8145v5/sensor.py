"""Huawei EG8145V5 sensors."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Huawei EG8145V5 sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        HuaweiDeviceCountSensor(coordinator),
        HuaweiUptimeSensor(coordinator),
    ]
    
    async_add_entities(sensors)

class HuaweiSensor(CoordinatorEntity, SensorEntity):
    """Base class for Huawei sensors."""
    
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_has_entity_name = True

class HuaweiDeviceCountSensor(HuaweiSensor):
    """Sensor for the number of connected devices."""

    _attr_name = "Device Count"
    _attr_unique_id = "device_count"
    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "devices"

    @property
    def native_value(self):
        return self.coordinator.data.get("device_count")

class HuaweiUptimeSensor(HuaweiSensor):
    """Sensor for the router uptime."""

    _attr_name = "Uptime"
    _attr_unique_id = "uptime"
    _attr_icon = "mdi:clock-outline"
    _attr_native_unit_of_measurement = "s"
    _attr_device_class = "duration"

    @property
    def native_value(self):
        info = self.coordinator.data.get("device_info", {})
        return int(info.get("UpTime", 0))
