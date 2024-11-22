"""The HVV Routes integration."""
from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryNotReady

from .sensor import HVVRoutesDataUpdateCoordinator
from .services import register_services  # Add this import

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]
DOMAIN = "hvv_routes"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HVV Routes from a config entry."""
    try:
        session = async_get_clientsession(hass, verify_ssl=True)

        # Extract authentication and home location
        auth_data = {
            CONF_USERNAME: entry.data[CONF_USERNAME],
            CONF_PASSWORD: entry.data[CONF_PASSWORD]
        }
        home_station = entry.data.get('home_station')
        home_city = entry.data.get('home_city')

        # Validate required data
        if not all([auth_data[CONF_USERNAME], auth_data[CONF_PASSWORD], 
                   home_station, home_city]):
            _LOGGER.error("Missing configuration parameters")
            return False

        # Create the data coordinator
        coordinator = HVVRoutesDataUpdateCoordinator(
            hass,
            session,
            auth_data,
            home_station,
            home_city
        )

        # Verify initial data fetch
        await coordinator.async_config_entry_first_refresh()

        # Store the coordinator
        hass.data.setdefault(DOMAIN, {})
        # Use a dict to store coordinators if multiple entries are possible
        hass.data[DOMAIN].setdefault('coordinators', {})[entry.entry_id] = coordinator

        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Register custom services (new addition)
        await register_services(hass)

        return True
    except Exception as err:
        _LOGGER.error(f"Error setting up HVV integration: {err}")
        raise ConfigEntryNotReady(f"Could not connect to HVV: {err}") from err

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Remove the specific coordinator for this entry
        hass.data[DOMAIN]['coordinators'].pop(entry.entry_id, None)
        
        # Optional: Remove the entire DOMAIN data if no coordinators left
        if not hass.data[DOMAIN]['coordinators']:
            hass.data.pop(DOMAIN, None)
    return unload_ok

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the HVV component."""
    return True