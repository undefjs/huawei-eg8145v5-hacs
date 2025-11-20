"""Huawei EG8145V5 device tracker."""
import logging
from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for Huawei EG8145V5."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # We need to track devices dynamically.
    # For simplicity in this initial version, we'll add entities for all currently found devices.
    # A better approach is to listen for new devices in the coordinator update.
    # But ScannerEntity usually works by polling.
    # Here we use CoordinatorEntity to get updates.
    
    # Actually, for ScannerEntity, it's often better to just let the coordinator handle the list
    # and we create entities for them.
    # Let's create a helper to add new devices.
    
    # For now, let's just add trackers for devices present at setup.
    # Dynamic addition requires a bit more logic (listening to coordinator updates in __init__ or here).
    # We will implement a basic version that adds devices found during the first refresh.
    
    devices = coordinator.data.get("active_devices", [])
    trackers = []
    for device in devices:
        trackers.append(HuaweiDeviceTracker(coordinator, device))
        
    async_add_entities(trackers)

class HuaweiDeviceTracker(CoordinatorEntity, ScannerEntity):
    """Representation of a device connected to the router."""

    def __init__(self, coordinator, device_info):
        """Initialize the tracker."""
        super().__init__(coordinator)
        self._device_info = device_info
        self._mac = device_info.get("MACAddress")
        self._hostname = device_info.get("HostName")
        self._ip = device_info.get("IPAddress")

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._mac

    @property
    def name(self):
        """Return the name."""
        return self._hostname or self._mac

    @property
    def source_type(self):
        """Return the source type."""
        return SourceType.ROUTER

    @property
    def is_connected(self):
        """Return true if the device is connected."""
        # Check if this mac is in the current active devices list
        active_devices = self.coordinator.data.get("active_devices", [])
        for device in active_devices:
            if device.get("MACAddress") == self._mac:
                return True
        return False

    @property
    def ip_address(self):
        """Return the primary ip address of the device."""
        return self._ip

    @property
    def mac_address(self):
        """Return the mac address of the device."""
        return self._mac
