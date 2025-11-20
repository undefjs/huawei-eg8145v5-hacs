"""Support for Huawei EG8145V5 device tracking."""
import logging
from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
    """Set up device tracker from a config entry."""
    coordinator: HuaweiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    @callback
    def update_devices():
        """Update tracked devices."""
        tracked = set()
        new_entities = []
        
        # Get ALL devices (both online and offline)
        for device in coordinator.data.get("devices", []):
            mac = device.get("MacAddress", "")
            if mac and mac not in tracked:
                tracked.add(mac)
                new_entities.append(HuaweiDeviceTracker(coordinator, device))
        
        if new_entities:
            async_add_entities(new_entities)

    coordinator.async_add_listener(update_devices)
    update_devices()

class HuaweiDeviceTracker(CoordinatorEntity, ScannerEntity):
    """Representation of a Huawei router tracked device."""

    def __init__(self, coordinator: HuaweiDataUpdateCoordinator, device: dict) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._mac = device.get("MacAddress", "")
        self._device = device
        
        # Create entity ID: device_tracker.huawei_eg8145v5_MAC (without colons)
        mac_clean = self._mac.replace(":", "").lower()
        self._attr_unique_id = f"{DOMAIN}_{mac_clean}"
        self.entity_id = f"device_tracker.{DOMAIN}_{mac_clean}"
        
        # Friendly name: hostname or MAC
        hostname = device.get("HostName", "")
        self._attr_name = hostname if hostname else self._mac

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        # Check all devices (not just active) to see if this MAC is Online
        for device in self.coordinator.data.get("devices", []):
            if device.get("MacAddress") == self._mac:
                return device.get("DevStatus", "").upper() == "ONLINE"
        return False

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.ROUTER

    @property
    def ip_address(self) -> str | None:
        """Return the IP address."""
        for device in self.coordinator.data.get("devices", []):
            if device.get("MacAddress") == self._mac:
                return device.get("IpAddr")
        return None

    @property
    def mac_address(self) -> str:
        """Return the MAC address."""
        return self._mac

    @property
    def hostname(self) -> str | None:
        """Return the hostname."""
        for device in self.coordinator.data.get("devices", []):
            if device.get("MacAddress") == self._mac:
                hostname = device.get("HostName", "")
                return hostname if hostname else None
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return device attributes."""
        for device in self.coordinator.data.get("devices", []):
            if device.get("MacAddress") == self._mac:
                attrs = {
                    "mac_address": device.get("MacAddress", ""),
                    "ip_address": device.get("IpAddr", ""),
                    "status": device.get("DevStatus", ""),
                }
                
                # Add optional attributes if available
                if device.get("HostName"):
                    attrs["hostname"] = device.get("HostName")
                if device.get("DevType"):
                    attrs["device_type"] = device.get("DevType")
                if device.get("Port"):
                    attrs["port"] = device.get("Port")
                if device.get("ConnectedTime"):
                    attrs["connected_time"] = device.get("ConnectedTime")
                if device.get("ActiveTime"):
                    attrs["active_time"] = device.get("ActiveTime")
                if device.get("RealMacAddress"):
                    attrs["real_mac_address"] = device.get("RealMacAddress")
                
                return attrs
        
        return {"mac_address": self._mac}
