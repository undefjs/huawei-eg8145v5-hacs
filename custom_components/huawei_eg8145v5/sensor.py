"""Support for Huawei EG8145V5 sensors."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
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
            "model": device_info.get("model", ""),
            "serial_number": device_info.get("serial_number", ""),
            "hardware_version": device_info.get("hardware_version", ""),
            "software_version": device_info.get("software_version", ""),
            "mac_address": device_info.get("mac", "")
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
        cpu = device_info.get("cpu_usage")
        # Ensure it's a number, not None
        if cpu is not None:
            return int(cpu) if isinstance(cpu, (int, float, str)) and str(cpu).replace('%', '').isdigit() else None
        return None

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
        mem = device_info.get("memory_usage")
        # Ensure it's a number, not None
        if mem is not None:
            return int(mem) if isinstance(mem, (int, float, str)) and str(mem).replace('%', '').isdigit() else None
        return None

class HuaweiUptimeSensor(CoordinatorEntity, SensorEntity):
    """Sensor for router last boot time."""

    def __init__(self, coordinator: HuaweiDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Last Boot"
        self._attr_unique_id = f"{DOMAIN}_last_boot"
        self._attr_icon = "mdi:restart"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        """Return when the router was last booted."""
        from datetime import datetime, timedelta, timezone
        
        device_info = self.coordinator.data.get("device_info", {})
        uptime_minutes = device_info.get("uptime")
        
        # Uptime from router is in MINUTES
        if uptime_minutes and isinstance(uptime_minutes, (int, float)):
            minutes = int(uptime_minutes)
        elif isinstance(uptime_minutes, str) and uptime_minutes.isdigit():
            minutes = int(uptime_minutes)
        else:
            return None
        
        # Calculate boot time: current time - uptime
        now = datetime.now(timezone.utc)
        boot_time = now - timedelta(minutes=minutes)
        
        return boot_time

    @property
    def extra_state_attributes(self):
        """Return formatted uptime."""
        device_info = self.coordinator.data.get("device_info", {})
        uptime_minutes = device_info.get("uptime")
        
        if uptime_minutes and isinstance(uptime_minutes, (int, float, str)):
            try:
                minutes = int(uptime_minutes) if isinstance(uptime_minutes, (int, float)) else int(uptime_minutes) if uptime_minutes.isdigit() else 0
                if minutes > 0:
                    days = minutes // 1440  # 1440 minutes in a day
                    hours = (minutes % 1440) // 60
                    mins = minutes % 60
                    
                    return {
                        "uptime_formatted": f"{days}d {hours}h {mins}m",
                        "uptime_days": days,
                        "uptime_hours": hours,
                        "uptime_minutes": mins,
                        "uptime_total_minutes": minutes,
                    }
            except (ValueError, AttributeError):
                pass
        
        return {}

