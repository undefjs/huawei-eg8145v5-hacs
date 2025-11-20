"""Support for Huawei EG8145V5 sensors."""
import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HuaweiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: HuaweiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        HuaweiDeviceCountSensor(coordinator),
        HuaweiOnlineDevicesSensor(coordinator),
        HuaweiCPUSensor(coordinator),
        HuaweiMemorySensor(coordinator),
        HuaweiUptimeSensor(coordinator),
    ]

    async_add_entities(sensors)

class HuaweiDeviceCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor for total device count."""

    def __init__(self, coordinator: HuaweiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Total Devices"
        self._attr_unique_id = f"{DOMAIN}_total_devices"
        self._attr_icon = "mdi:devices"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        devices = self.coordinator.data.get("devices", [])
        return len(devices)

    @property
    def extra_state_attributes(self):
        """Return device attributes."""
        device_info = self.coordinator.data.get("device_info", {})
        return {
            "model": device_info.get("model", "EG8145V5"),
            "serial_number": device_info.get("serial_number", ""),
            "hardware_version": device_info.get("hardware_version", ""),
            "software_version": device_info.get("software_version", ""),
            "mac_address": device_info.get("mac", ""),
        }

class HuaweiOnlineDevicesSensor(CoordinatorEntity, SensorEntity):
    """Sensor for online device count."""

    def __init__(self, coordinator: HuaweiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Online Devices"
        self._attr_unique_id = f"{DOMAIN}_online_devices"
        self._attr_icon = "mdi:lan-connect"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("device_count", 0)

class HuaweiCPUSensor(CoordinatorEntity, SensorEntity):
    """Sensor for CPU usage."""

    def __init__(self, coordinator: HuaweiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "CPU Usage"
        self._attr_unique_id = f"{DOMAIN}_cpu_usage"
        self._attr_icon = "mdi:cpu-64-bit"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state of the sensor."""
        device_info = self.coordinator.data.get("device_info", {})
        return device_info.get("cpu_usage")

class HuaweiMemorySensor(CoordinatorEntity, SensorEntity):
    """Sensor for memory usage."""

    def __init__(self, coordinator: HuaweiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Memory Usage"
        self._attr_unique_id = f"{DOMAIN}_memory_usage"
        self._attr_icon = "mdi:memory"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state of the sensor."""
        device_info = self.coordinator.data.get("device_info", {})
        return device_info.get("memory_usage")

class HuaweiUptimeSensor(CoordinatorEntity, SensorEntity):
    """Sensor for router uptime."""

    def __init__(self, coordinator: HuaweiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Uptime"
        self._attr_unique_id = f"{DOMAIN}_uptime"
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS

    @property
    def native_value(self):
        """Return the state of the sensor."""
        device_info = self.coordinator.data.get("device_info", {})
        uptime_seconds = device_info.get("uptime", 0)
        # Convert to seconds if needed
        return uptime_seconds if uptime_seconds else 0

    @property
    def extra_state_attributes(self):
        """Return formatted uptime."""
        device_info = self.coordinator.data.get("device_info", {})
        uptime_seconds = device_info.get("uptime", 0)
        
        if uptime_seconds:
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            minutes = (uptime_seconds % 3600) // 60
            seconds = uptime_seconds % 60
            
            return {
                "formatted": f"{days}d {hours}h {minutes}m {seconds}s",
                "days": days,
                "hours": hours,
                "minutes": minutes,
            }
        return {}
