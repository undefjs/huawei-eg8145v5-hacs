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
        
        # Create unique_id: huawei_eg8145v5_MAC (uppercase, underscores)
        # This must remain consistent to avoid duplicate entities
        mac_clean = self._mac.replace(":", "_").upper()
        self._attr_unique_id = f"{DOMAIN}_{mac_clean}"
        
        # Don't set entity_id manually - let Home Assistant generate it from unique_id
        # This prevents duplicate entity issues
        
        # Enable all device trackers by default
        self._attr_entity_registry_enabled_default = True
        
        # Friendly name: hostname (avoid generic names like wlan0, --), fallback to MAC
        hostname = device.get("HostName", "")
        # Generic or empty hostnames should use MAC instead
        if hostname and hostname not in ["--", "wlan0", ""]:
            self._attr_name = hostname
        else:
            self._attr_name = mac_clean

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
                    "ip": device.get("IpAddr", ""),
                    "mac": device.get("MacAddress", ""),
                    "status": device.get("DevStatus", ""),
                }
                
                # Add optional attributes if available and not empty
                if device.get("DevType"):
                    attrs["device_type"] = device.get("DevType")
                if device.get("Port"):
                    attrs["port"] = device.get("Port")
                if device.get("ConnectedTime"):
                    attrs["connected_time"] = device.get("ConnectedTime")
                if device.get("ActiveTime"):
                    attrs["active_time"] = device.get("ActiveTime")
                
                # Only add real_mac if it's different from the main MAC
                real_mac = device.get("RealMacAddress", "")
                if real_mac and real_mac != self._mac:
                    attrs["real_mac"] = real_mac
                
                return attrs
        
        return {"mac": self._mac}
