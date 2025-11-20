"""Config flow for Huawei EG8145V5 integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .client import HuaweiEG8145V5Client

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
})

async def validate_input(hass: HomeAssistant, data: dict):
    """Validate the user input allows us to connect."""
    client = await hass.async_add_executor_job(
        lambda: HuaweiEG8145V5Client(data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD])
    )
    
    try:
        result = await hass.async_add_executor_job(client.login)
    except Exception as e:
        _LOGGER.error(f"Connection error: {e}")
        raise CannotConnect

    # Check for errorCategory in response (common in Huawei APIs)
    if isinstance(result, dict) and result.get("errorCategory") != "ok":
        # If it's not "ok", it might be an auth error, but let's check.
        # Some routers return different structures.
        # For now, if we get ANY JSON back, we assume connection is OK, 
        # but we should verify auth.
        _LOGGER.warning(f"Login response: {result}")
        # raise InvalidAuth # Uncomment if we are sure about the error format

    return {"title": f"Huawei Router ({data[CONF_HOST]})"}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Huawei EG8145V5."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
