"""DataUpdateCoordinator for Huawei EG8145V5."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class HuaweiDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Huawei EG8145V5 data."""

    def __init__(self, hass: HomeAssistant, client):
        """Initialize global Huawei data updater."""
        self.client = client
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        """Fetch data from the router."""
        try:
            # Login if needed (client handles session, but we might need to refresh)
            # Ideally client.login() checks if session is valid or we just try/except
            # For now, we'll assume client methods handle re-auth or we do it here.
            # Let's try to get data, if it fails, try login then get data.
            
            data = {}
            
            # We run these in executor because client is synchronous
            all_devices = await self.hass.async_add_executor_job(self.client.get_devices)
            active_devices = await self.hass.async_add_executor_job(self.client.get_active_devices)
            device_info = await self.hass.async_add_executor_job(self.client.get_device_info)
            device_count = await self.hass.async_add_executor_job(self.client.get_device_count)
            
            data["devices"] = all_devices  # All devices (online + offline)
            data["active_devices"] = active_devices  # Only online devices
            data["device_info"] = device_info
            data["device_count"] = device_count
            
            return data
            
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
