from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .infrastructure.ha.climate_entity import AquaTempClimateEntity
from .infrastructure.ha.coordinator import AquaTempCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AquaTempCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AquaTempClimateEntity(coordinator, entry.entry_id)])
