from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.aquatemp.domain.commands import SetPower
from custom_components.aquatemp.domain.exceptions import CommunicationError
from custom_components.aquatemp.domain.heat_pump import HeatPump
from custom_components.aquatemp.domain.value_objects import PowerState
from custom_components.aquatemp.infrastructure.ha.coordinator import AquaTempCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from tests.conftest import make_registers


def _make_hass() -> MagicMock:
    hass = MagicMock()
    hass.loop = MagicMock()
    hass.data = {}
    hass.bus = MagicMock()
    hass.bus.async_fire = MagicMock()
    return hass


def _make_coordinator(hass, service):
    with patch("homeassistant.helpers.frame.report_usage"):
        coordinator = AquaTempCoordinator(hass, service)
    coordinator._unsub_refresh = MagicMock()
    return coordinator


class TestAquaTempCoordinatorUpdate:
    async def test_successful_poll_returns_heat_pump(self):
        service = AsyncMock()
        expected = HeatPump.from_registers(make_registers())
        service.poll.return_value = expected
        hass = _make_hass()

        coordinator = _make_coordinator(hass, service)
        result = await coordinator._async_update_data()

        assert result is expected
        service.poll.assert_called_once()

    async def test_aquatemp_error_raises_update_failed(self):
        service = AsyncMock()
        service.poll.side_effect = CommunicationError("timeout")
        hass = _make_hass()

        coordinator = _make_coordinator(hass, service)

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


class TestAquaTempCoordinatorExecute:
    async def test_execute_calls_service(self):
        service = AsyncMock()
        service.poll.return_value = HeatPump.from_registers(make_registers())
        hass = _make_hass()

        coordinator = _make_coordinator(hass, service)
        coordinator.async_request_refresh = AsyncMock()

        cmd = SetPower(PowerState.ON)
        await coordinator.async_execute(cmd)

        service.execute.assert_called_once_with(cmd)
        coordinator.async_request_refresh.assert_called_once()

    async def test_execute_aquatemp_error_raises_update_failed(self):
        service = AsyncMock()
        service.execute.side_effect = CommunicationError("write failed")
        hass = _make_hass()

        coordinator = _make_coordinator(hass, service)
        coordinator.async_request_refresh = AsyncMock()

        with pytest.raises(UpdateFailed):
            await coordinator.async_execute(SetPower(PowerState.ON))
