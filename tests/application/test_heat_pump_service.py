from unittest.mock import AsyncMock

import pytest

from custom_components.auqatemp.application.heat_pump_service import HeatPumpService
from custom_components.auqatemp.domain.commands import SetMode, SetPower, SetTemperature
from custom_components.auqatemp.domain.exceptions import CommunicationError
from custom_components.auqatemp.domain.heat_pump import HeatPump
from custom_components.auqatemp.domain.value_objects import OperatingMode, PowerState, SetPoint
from custom_components.auqatemp.infrastructure.ble.frame_codec import (
    build_write_frame,
    crc16_modbus,
)
from tests.conftest import make_registers


def _build_valid_response(registers: list[int]) -> str:
    payload = bytes([0x63, 0x03, 0x5A])
    for reg in registers:
        val = reg & 0xFFFF
        payload += bytes([(val >> 8) & 0xFF, val & 0xFF])
    crc = crc16_modbus(payload)
    frame = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    return frame.hex().upper()


class TestHeatPumpServicePoll:
    async def test_poll_sends_read_frame(self):
        transport = AsyncMock()
        transport.send_and_receive.return_value = _build_valid_response(make_registers())
        service = HeatPumpService(transport)

        await service.poll()

        transport.send_and_receive.assert_called_once_with("63030007002D3C54")

    async def test_poll_returns_heat_pump_aggregate(self):
        transport = AsyncMock()
        transport.send_and_receive.return_value = _build_valid_response(make_registers())
        service = HeatPumpService(transport)

        result = await service.poll()

        assert isinstance(result, HeatPump)

    async def test_poll_parses_power_state(self):
        transport = AsyncMock()
        transport.send_and_receive.return_value = _build_valid_response(
            make_registers(power=PowerState.OFF)
        )
        service = HeatPumpService(transport)

        result = await service.poll()

        assert result.power == PowerState.OFF


class TestHeatPumpServiceExecute:
    async def test_execute_set_power_on(self):
        transport = AsyncMock()
        service = HeatPumpService(transport)

        await service.execute(SetPower(PowerState.ON))

        transport.send.assert_called_once_with(build_write_frame(8, 1).upper())

    async def test_execute_set_power_off(self):
        transport = AsyncMock()
        service = HeatPumpService(transport)

        await service.execute(SetPower(PowerState.OFF))

        transport.send.assert_called_once_with(build_write_frame(8, 0).upper())

    async def test_execute_set_mode_heat(self):
        transport = AsyncMock()
        service = HeatPumpService(transport)

        await service.execute(SetMode(OperatingMode.HEAT))

        transport.send.assert_called_once_with(build_write_frame(13, 3).upper())

    async def test_execute_set_mode_cool(self):
        transport = AsyncMock()
        service = HeatPumpService(transport)

        await service.execute(SetMode(OperatingMode.COOL))

        transport.send.assert_called_once_with(build_write_frame(13, 2).upper())

    async def test_execute_set_temperature(self):
        transport = AsyncMock()
        service = HeatPumpService(transport)

        await service.execute(SetTemperature(20, SetPoint(25.0)))

        transport.send.assert_called_once_with(build_write_frame(20, 250).upper())

    async def test_execute_unknown_command_raises(self):
        transport = AsyncMock()
        service = HeatPumpService(transport)

        with pytest.raises(CommunicationError):
            await service.execute("not_a_command")  # type: ignore[arg-type]


class TestHeatPumpServiceTargetAddresses:
    def test_heat_target_address(self):
        assert HeatPumpService.heat_target_address() == 20

    def test_cool_target_address(self):
        assert HeatPumpService.cool_target_address() == 19

    def test_auto_target_address(self):
        assert HeatPumpService.auto_target_address() == 21

    def test_target_address_for_heat_mode(self):
        assert HeatPumpService.target_address_for_mode(OperatingMode.HEAT) == 20

    def test_target_address_for_single_heat_mode(self):
        assert HeatPumpService.target_address_for_mode(OperatingMode.SINGLE_HEAT) == 20

    def test_target_address_for_cool_mode(self):
        assert HeatPumpService.target_address_for_mode(OperatingMode.COOL) == 19

    def test_target_address_for_single_cool_mode(self):
        assert HeatPumpService.target_address_for_mode(OperatingMode.SINGLE_COOL) == 19

    def test_target_address_for_auto_mode(self):
        assert HeatPumpService.target_address_for_mode(OperatingMode.AUTO) == 21
