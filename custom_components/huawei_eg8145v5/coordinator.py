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
            # Check if we need to re-login (session might have expired)
            # Try to get data, if it fails, attempt re-login
            
            data = {}
            
            # We run these in executor because client is synchronous
            try:
                all_devices = await self.hass.async_add_executor_job(self.client.get_devices)
            except Exception as e:
                # If getting devices fails, try to re-login
                _LOGGER.warning(f"Failed to get devices, attempting re-login: {e}")
                login_success = await self.hass.async_add_executor_job(self.client.login)
                if not login_success:
                    raise UpdateFailed(f"Authentication failed - session expired or invalid credentials")
                # Retry after login
                all_devices = await self.hass.async_add_executor_job(self.client.get_devices)
            
            # If we got empty devices, it might be an auth issue
            if all_devices is None or (isinstance(all_devices, list) and len(all_devices) == 0):
                # This could be normal (no devices) or an auth issue. Let's check device_info
                device_info = await self.hass.async_add_executor_job(self.client.get_device_info)
                if not device_info or device_info.get("model") == "EG8145V5" and len(device_info) == 2:
                    # Minimal response suggests auth failure
                    raise UpdateFailed("Unable to fetch router data - authentication may have failed")
            
            active_devices = await self.hass.async_add_executor_job(self.client.get_active_devices)
            device_info = await self.hass.async_add_executor_job(self.client.get_device_info)
            device_count = await self.hass.async_add_executor_job(self.client.get_device_count)
            
            data["devices"] = all_devices  # All devices (online + offline)
            data["active_devices"] = active_devices  # Only online devices
            data["device_info"] = device_info
            data["device_count"] = device_count
            
            return data
            
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Error communicating with router: {err}")
