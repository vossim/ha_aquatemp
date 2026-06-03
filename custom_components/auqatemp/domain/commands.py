from __future__ import annotations

from dataclasses import dataclass

from .value_objects import OperatingMode, PowerState, SetPoint


@dataclass(frozen=True)
class SetPower:
    power: PowerState


@dataclass(frozen=True)
class SetMode:
    mode: OperatingMode


@dataclass(frozen=True)
class SetTemperature:
    modbus_address: int
    set_point: SetPoint


Command = SetPower | SetMode | SetTemperature
