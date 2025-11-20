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
        from datetime import datetime, timedelta
        from dateutil import parser
        
        device_info = self.coordinator.data.get("device_info", {})
        uptime_seconds_str = device_info.get("uptime")
        system_time_str = device_info.get("system_time")
        
        # Uptime from router is in SECONDS
        if uptime_seconds_str and isinstance(uptime_seconds_str, str) and uptime_seconds_str.isdigit():
            uptime_seconds = int(uptime_seconds_str)
        elif isinstance(uptime_seconds_str, (int, float)):
            uptime_seconds = int(uptime_seconds_str)
        else:
            return None
        
        # Use router's system time if available, otherwise use current time
        if system_time_str:
            try:
                # Parse router time: '2025-11-20 23:57:30+01:00'
                router_time = parser.parse(system_time_str)
            except (ValueError, TypeError):
                # Fallback to current time if parsing fails
                router_time = datetime.now()
        else:
            router_time = datetime.now()
        
        # Calculate boot time: router_time - uptime
        boot_time = router_time - timedelta(seconds=uptime_seconds)
        
        return boot_time

    @property
    def extra_state_attributes(self):
        """Return formatted uptime."""
        device_info = self.coordinator.data.get("device_info", {})
        uptime_seconds_str = device_info.get("uptime")
        
        if uptime_seconds_str and isinstance(uptime_seconds_str, (str, int, float)):
            try:
                seconds = int(uptime_seconds_str) if isinstance(uptime_seconds_str, (int, float, str)) and str(uptime_seconds_str).isdigit() else 0
                if seconds > 0:
                    days = seconds // 86400  # 86400 seconds in a day
                    hours = (seconds % 86400) // 3600
                    minutes = (seconds % 3600) // 60
                    secs = seconds % 60
                    
                    return {
                        "uptime_formatted": f"{days}d {hours}h {minutes}m {secs}s",
                        "uptime_days": days,
                        "uptime_hours": hours,
                        "uptime_minutes": minutes,
                        "uptime_seconds": secs,
                        "uptime_total_seconds": seconds,
                    }
            except (ValueError, AttributeError):
                pass
        
        return {}

