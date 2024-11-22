"""Services for HVV Routes integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up custom services for HVV Routes integration."""
    
    async def handle_set_route(call: ServiceCall) -> None:
        """Handle the set_route service call."""
        entity_registry = er.async_get(hass)
        
        # Log incoming service call data
        _LOGGER.debug(f"Service call data: {call.data}")
        
        # Get target entities
        entity_ids = call.data.get('entity_id', [])
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]
        _LOGGER.debug(f"Processing entities: {entity_ids}")
        
        # Extract service call parameters
        destination_station = call.data.get('destination_station')
        destination_city = call.data.get('destination_city')
        departure_time = call.data.get('departure_time', 'currenttime')
        _LOGGER.debug(f"Parameters: station={destination_station}, city={destination_city}, time={departure_time}")
        
        # Process each targeted entity
        for entity_id in entity_ids:
            try:
                # Get entry_id from entity_id
                entity_entry = entity_registry.async_get(entity_id)
                _LOGGER.debug(f"Found entity entry: {entity_entry}")
                
                if entity_entry is None:
                    _LOGGER.warning(f"No entity found for {entity_id}")
                    continue
                
                # Retrieve the coordinator
                coordinator = hass.data.get(DOMAIN, {}).get('coordinators', {}).get(entity_entry.config_entry_id)
                _LOGGER.debug(f"Retrieved coordinator for {entity_id}: {coordinator}")
                
                if not coordinator:
                    _LOGGER.warning(f"No coordinator found for {entity_id}")
                    continue
                
                # Log before setting destination
                _LOGGER.debug(f"Setting destination for {entity_id}")
                await coordinator.set_destination(
                    station=destination_station, 
                    city=destination_city
                )
                _LOGGER.debug(f"Destination set successfully")
                
                # Set departure time if provided
                if departure_time:
                    _LOGGER.debug(f"Setting departure time: {departure_time}")
                    await coordinator.set_departure_time(departure_time)
                    _LOGGER.debug(f"Departure time set successfully")
                    
                    _LOGGER.info(f"Route set for {entity_id}: {destination_station}, {destination_city}")
                    
            except Exception as e:
                _LOGGER.error(f"Error setting route for {entity_id}: {e}", exc_info=True)

    # Register the service
    hass.services.async_register(
        DOMAIN, 
        'set_route', 
        handle_set_route
    )

async def register_services(hass: HomeAssistant) -> None:
    """Register HVV Routes services."""
    await async_setup_services(hass)