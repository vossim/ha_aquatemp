from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .exceptions import InvalidSetPoint
from .register_map import SETPOINT_MAX_CELSIUS, SETPOINT_MIN_CELSIUS


class OperatingMode(IntEnum):
    SINGLE_COOL = 0
    SINGLE_HEAT = 1
    COOL = 2
    HEAT = 3
    AUTO = 4


class PowerState(IntEnum):
    OFF = 0
    ON = 1


@dataclass(frozen=True)
class SetPoint:
    value_celsius: float

    def __post_init__(self) -> None:
        if not (SETPOINT_MIN_CELSIUS <= self.value_celsius <= SETPOINT_MAX_CELSIUS):
            raise InvalidSetPoint(
                f"Setpoint {self.value_celsius}°C is outside the allowed range "
                f"[{SETPOINT_MIN_CELSIUS}, {SETPOINT_MAX_CELSIUS}]°C"
            )

    def as_register_value(self) -> int:
        return round(self.value_celsius * 10)


@dataclass(frozen=True)
class TemperatureReading:
    value_celsius: float

    @classmethod
    def from_register(cls, raw: int) -> TemperatureReading:
        return cls(value_celsius=raw / 10.0)
