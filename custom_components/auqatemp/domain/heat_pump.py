from __future__ import annotations

from dataclasses import dataclass

from .register_map import (
    REGISTER_COUNT,
    REG_AMBIENT_TEMP,
    REG_AUTO_TARGET,
    REG_COOL_TARGET,
    REG_FAULT1,
    REG_HEAT_TARGET,
    REG_INLET_WATER_TEMP,
    REG_MODE,
    REG_OUTLET_WATER_TEMP,
    REG_POWER,
)
from .value_objects import OperatingMode, PowerState, SetPoint, TemperatureReading


@dataclass(frozen=True)
class HeatPump:
    power: PowerState
    mode: OperatingMode
    heat_setpoint: SetPoint
    cool_setpoint: SetPoint
    auto_setpoint: SetPoint
    inlet_temp: TemperatureReading
    outlet_temp: TemperatureReading
    ambient_temp: TemperatureReading
    fault_flags: int

    @classmethod
    def from_registers(cls, registers: list[int]) -> HeatPump:
        if len(registers) != REGISTER_COUNT:
            raise ValueError(
                f"Expected {REGISTER_COUNT} registers, got {len(registers)}"
            )
        return cls(
            power=PowerState(registers[REG_POWER]),
            mode=OperatingMode(registers[REG_MODE]),
            heat_setpoint=SetPoint(registers[REG_HEAT_TARGET] / 10.0),
            cool_setpoint=SetPoint(registers[REG_COOL_TARGET] / 10.0),
            auto_setpoint=SetPoint(registers[REG_AUTO_TARGET] / 10.0),
            inlet_temp=TemperatureReading.from_register(registers[REG_INLET_WATER_TEMP]),
            outlet_temp=TemperatureReading.from_register(registers[REG_OUTLET_WATER_TEMP]),
            ambient_temp=TemperatureReading.from_register(registers[REG_AMBIENT_TEMP]),
            fault_flags=registers[REG_FAULT1],
        )

    @property
    def target_temperature(self) -> SetPoint:
        """Return the active setpoint for the current operating mode."""
        if self.mode in (OperatingMode.HEAT, OperatingMode.SINGLE_HEAT):
            return self.heat_setpoint
        if self.mode in (OperatingMode.COOL, OperatingMode.SINGLE_COOL):
            return self.cool_setpoint
        return self.auto_setpoint

    @property
    def is_faulted(self) -> bool:
        return self.fault_flags != 0
