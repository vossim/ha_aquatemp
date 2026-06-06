from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .application.heat_pump_service import HeatPumpService
from .infrastructure.ble.transport import BleakTransport
from .infrastructure.ha.coordinator import AquaTempCoordinator

DOMAIN = "aquatemp"
_PLATFORMS = ["climate"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    mac_address: str = entry.data["mac_address"]
    transport = BleakTransport(mac_address)
    service = HeatPumpService(transport)
    coordinator = AquaTempCoordinator(hass, service)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
