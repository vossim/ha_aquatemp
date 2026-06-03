from __future__ import annotations

from ..domain.commands import Command, SetMode, SetPower, SetTemperature
from ..domain.exceptions import CommunicationError
from ..domain.heat_pump import HeatPump
from ..domain.ports import Transport
from ..domain.register_map import (
    MODBUS_ADDR_AUTO_TARGET,
    MODBUS_ADDR_COOL_TARGET,
    MODBUS_ADDR_HEAT_TARGET,
    MODBUS_ADDR_MODE,
    MODBUS_ADDR_POWER,
)
from ..domain.value_objects import OperatingMode
from ..infrastructure.ble.frame_codec import (
    build_read_frame,
    build_write_frame,
    parse_fc03_response,
)


class HeatPumpService:
    """Orchestrates polling and command dispatch for a single heat pump device."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def poll(self) -> HeatPump:
        """Read all registers and return current device state."""
        response = await self._transport.send_and_receive(build_read_frame())
        registers = parse_fc03_response(response)
        return HeatPump.from_registers(registers)

    async def execute(self, command: Command) -> None:
        """Translate a domain command to a Modbus write and send it."""
        frame = self._build_frame(command)
        await self._transport.send(frame)

    def _build_frame(self, command: Command) -> str:
        if isinstance(command, SetPower):
            return build_write_frame(MODBUS_ADDR_POWER, int(command.power))
        if isinstance(command, SetMode):
            return build_write_frame(MODBUS_ADDR_MODE, int(command.mode))
        if isinstance(command, SetTemperature):
            return build_write_frame(
                command.modbus_address,
                command.set_point.as_register_value(),
            )
        raise CommunicationError(f"Unknown command type: {type(command)}")

    @staticmethod
    def heat_target_address() -> int:
        return MODBUS_ADDR_HEAT_TARGET

    @staticmethod
    def cool_target_address() -> int:
        return MODBUS_ADDR_COOL_TARGET

    @staticmethod
    def auto_target_address() -> int:
        return MODBUS_ADDR_AUTO_TARGET

    @staticmethod
    def target_address_for_mode(mode: OperatingMode) -> int:
        if mode in (OperatingMode.HEAT, OperatingMode.SINGLE_HEAT):
            return MODBUS_ADDR_HEAT_TARGET
        if mode in (OperatingMode.COOL, OperatingMode.SINGLE_COOL):
            return MODBUS_ADDR_COOL_TARGET
        return MODBUS_ADDR_AUTO_TARGET
