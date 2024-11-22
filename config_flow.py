"""Config flow for HVV integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
import aiohttp
from pygti.auth import Auth
from pygti.gti import GTI

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class HVVConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HVV integration."""

    VERSION = 1
    
    def __init__(self):
        """Initialize the config flow."""
        self.auth_data = {}

    async def validate_auth(self, username: str, password: str) -> None:
        try:
            session = async_get_clientsession(self.hass, verify_ssl=True)
            auth = Auth(session, username, password)
            gti = GTI(auth)
            
            # More granular error handling
            try:
                await gti.init()
            except AuthenticationError:
                _LOGGER.error("Specific authentication failure")
                raise InvalidAuth()
            except NetworkError:
                _LOGGER.error("Network connection issue")
                raise CannotConnect()
                
        except Exception as e:
            _LOGGER.error(f"Unexpected authentication error: {e}")
            raise InvalidAuth()

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle the initial authentication step."""
        errors: Dict[str, str] = {}
        
        if user_input is not None:
            try:
                await self.validate_auth(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD]
                )
                self.auth_data = {
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD]
                }
                return await self.async_step_home_location()
                
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.error(f"Unexpected error: {e}")
                errors["base"] = "unknown"
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str
            }),
            errors=errors
        )

    async def async_step_home_location(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle home location setup."""
        errors: Dict[str, str] = {}
        
        if user_input is not None:
            full_config = {
                **self.auth_data,
                "home_station": user_input["home_station"],
                "home_city": user_input["home_city"]
            }
            return self.async_create_entry(
                title=f"HVV Routes: {user_input['home_station']}",
                data=full_config
            )

        return self.async_show_form(
            step_id="home_location",
            data_schema=vol.Schema({
                vol.Required("home_station"): str,
                vol.Required("home_city"): str,
            }),
            errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return HVVOptionsFlow(config_entry)

class HVVOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for HVV integration."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Manage the options."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                await HVVConfigFlow.validate_auth(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD]
                )
                return self.async_create_entry(title="", data=user_input)
            except (CannotConnect, InvalidAuth) as e:
                errors["base"] = str(e)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME, 
                    default=self._config_entry.data.get(CONF_USERNAME, "")): str,
                vol.Required(CONF_PASSWORD, 
                    default=self._config_entry.data.get(CONF_PASSWORD, "")): str,
                vol.Required("home_station", 
                    default=self._config_entry.data.get("home_station", "")): str,
                vol.Required("home_city", 
                    default=self._config_entry.data.get("home_city", "")): str,
            }),
            errors=errors
        )

class CannotConnect(Exception):
    """Error to indicate we cannot connect."""
    pass

class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
    pass