import pytest

from custom_components.aquatemp.domain.register_map import REGISTER_COUNT
from custom_components.aquatemp.domain.value_objects import OperatingMode, PowerState


def make_registers(
    power: int = PowerState.ON,
    mode: int = OperatingMode.HEAT,
    cool_target: int = 200,   # 20.0°C
    heat_target: int = 250,   # 25.0°C
    auto_target: int = 220,   # 22.0°C
    inlet_temp: int = 245,    # 24.5°C
    outlet_temp: int = 280,   # 28.0°C
    ambient_temp: int = 150,  # 15.0°C
    fault_flags: int = 0,
) -> list[int]:
    """Return a 45-element register list with sensible defaults."""
    regs = [0] * REGISTER_COUNT
    regs[1] = power
    regs[6] = mode
    regs[12] = cool_target
    regs[13] = heat_target
    regs[14] = auto_target
    regs[19] = inlet_temp
    regs[20] = outlet_temp
    regs[21] = ambient_temp
    regs[40] = fault_flags
    return regs
