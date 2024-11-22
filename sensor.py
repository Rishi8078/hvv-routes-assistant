"""Sensor platform for HVV route information."""
import asyncio
import logging
from datetime import timedelta
import json

import aiohttp
from pygti.auth import Auth
from pygti.gti import GTI

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)

DOMAIN = "hvv_routes"
SCAN_INTERVAL = timedelta(minutes=15)

class HVVRoutesDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching HVV route data."""
    
    def __init__(self, hass, session, auth_data, home_station, home_city):
        """Initialize with authentication and home location."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL
        )
        self._session = session
        self._username = auth_data[CONF_USERNAME]
        self._password = auth_data[CONF_PASSWORD]
        self._home_station = home_station
        self._home_city = home_city
        self._dest_station = None
        self._dest_city = None
        self._departure_time = None

    async def set_destination(self, station: str, city: str):
        """Update destination dynamically."""
        self._dest_station = station
        self._dest_city = city
        _LOGGER.debug(f"Destination set to station: {station}, city: {city}")
        await self.async_refresh()

    async def set_departure_time(self, time: str):
        """Update departure time dynamically."""
        self._departure_time = time
        _LOGGER.debug(f"Departure time set to: {time}")
        await self.async_refresh()

    async def _async_update_data(self):
        """Fetch data from HVV API."""
        if not all([self._dest_station, self._dest_city]):
            _LOGGER.debug("Destination station or city not set, skipping update")
            return None

        try:
            auth = Auth(self._session, self._username, self._password)
            gti = GTI(auth)

            payload = {
                "start": {
                    "name": self._home_station,
                    "city": self._home_city,
                    "type": "STATION"
                },
                "dest": {
                    "name": self._dest_station,
                    "city": self._dest_city,
                    "type": "STATION"
                },
                "time": {
                    "date": "today",
                    "time": self._departure_time or "currenttime"
                },
                "timeIsDeparture": True,
                "realtime": "REALTIME",
            }

            _LOGGER.debug(f"Route request payload: {json.dumps(payload, indent=2)}")
            route_data = await gti.getRoute(payload)
            
            if not route_data:
                _LOGGER.error("No route data received")
                raise UpdateFailed("No route data received")
                
            _LOGGER.debug("Route data successfully fetched")
            return route_data
        except Exception as err:
            _LOGGER.error("Error fetching route data", exc_info=True)
            raise UpdateFailed(f"Error: {err}") from err

class HVVDynamicRouteSensor(CoordinatorEntity, SensorEntity):
    """Dynamic HVV route sensor."""
    
    def __init__(self, coordinator, name, unique_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = "mdi:bus-clock"

    @property
    def state(self):
        """Return the state of the sensor."""
        try:
            if not self.coordinator.data:
                return 'No Destination Set'
            
            schedules = self.coordinator.data.get('realtimeSchedules', [])
            if schedules:
                return schedules[0].get('time', 'Unknown')
            return 'No Routes Found'
        except Exception as e:
            _LOGGER.error(f"Error getting state: {e}", exc_info=True)
            return 'Error'

    @property
    def extra_state_attributes(self):
        """Return additional sensor attributes."""
        try:
            _LOGGER.debug(f"Coordinator values: dest_station={self.coordinator._dest_station}, dest_city={self.coordinator._dest_city}, departure_time={self.coordinator._departure_time}")
            if not self.coordinator.data:
                return {
                    'home_station': self.coordinator._home_station,
                    'home_city': self.coordinator._home_city,
                    'destination_station': self.coordinator._dest_station,
                    'destination_city': self.coordinator._dest_city,
                    'departure_time': self.coordinator._departure_time,
                }

            routes = []
            for schedule in self.coordinator.data.get('realtimeSchedules', []):
                route = {
                    'departure_time': schedule.get('plannedDepartureTime'),
                    'arrival_time': schedule.get('plannedArrivalTime'),
                    'duration': schedule.get('time'),
                    'line': schedule.get('scheduleElements', [{}])[0].get('line', {}).get('name'),
                    'direction': schedule.get('scheduleElements', [{}])[0].get('line', {}).get('direction'),
                }
                routes.append(route)

            return {
                'home_station': self.coordinator._home_station,
                'home_city': self.coordinator._home_city,
                'destination_station': self.coordinator._dest_station,
                'destination_city': self.coordinator._dest_city,
                'departure_time': self.coordinator._departure_time,
                'routes': routes
            }
        except Exception as e:
            _LOGGER.error(f"Error getting attributes: {e}", exc_info=True)
            return {}

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the HVV sensor from a config entry."""
    try:
        coordinator = HVVRoutesDataUpdateCoordinator(
            hass,
            async_get_clientsession(hass),
            {
                CONF_USERNAME: config_entry.data[CONF_USERNAME],
                CONF_PASSWORD: config_entry.data[CONF_PASSWORD]
            },
            config_entry.data["home_station"],
            config_entry.data["home_city"]
        )
        
        sensor = HVVDynamicRouteSensor(
            coordinator,
            name=f"HVV Route from {config_entry.data['home_station']}",
            unique_id=f"hvv_route_{config_entry.entry_id}"
        )
        
        await coordinator.async_config_entry_first_refresh()
        async_add_entities([sensor])
        
    except Exception as e:
        _LOGGER.error(f"Failed to setup sensor: {e}", exc_info=True)
        raise ConfigEntryNotReady(f"Setup failed: {e}")