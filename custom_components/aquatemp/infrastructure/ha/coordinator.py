from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ...application.heat_pump_service import HeatPumpService
from ...domain.commands import Command
from ...domain.exceptions import AquaTempError
from ...domain.heat_pump import HeatPump

_LOGGER = logging.getLogger(__name__)

POLL_INTERVAL = timedelta(seconds=30)


class AquaTempCoordinator(DataUpdateCoordinator[HeatPump]):
    """Polls the heat pump and notifies HA entities of state changes."""

    def __init__(self, hass: HomeAssistant, service: HeatPumpService) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="AquaTemp",
            update_interval=POLL_INTERVAL,
        )
        self._service = service

    async def _async_update_data(self) -> HeatPump:
        try:
            return await self._service.poll()
        except AquaTempError as exc:
            raise UpdateFailed(f"Error reading from heat pump: {exc}") from exc

    async def async_execute(self, command: Command) -> None:
        """Send a command to the device then immediately refresh state."""
        try:
            await self._service.execute(command)
        except AquaTempError as exc:
            raise UpdateFailed(f"Error sending command to heat pump: {exc}") from exc
        await self.async_request_refresh()
