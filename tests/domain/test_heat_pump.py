import pytest

from custom_components.aquatemp.domain.heat_pump import HeatPump
from custom_components.aquatemp.domain.value_objects import OperatingMode, PowerState
from tests.conftest import make_registers


class TestHeatPumpFromRegisters:
    def test_parses_power_on(self):
        hp = HeatPump.from_registers(make_registers(power=PowerState.ON))
        assert hp.power == PowerState.ON

    def test_parses_power_off(self):
        hp = HeatPump.from_registers(make_registers(power=PowerState.OFF))
        assert hp.power == PowerState.OFF

    def test_parses_mode(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.COOL))
        assert hp.mode == OperatingMode.COOL

    def test_parses_heat_setpoint(self):
        hp = HeatPump.from_registers(make_registers(heat_target=250))
        assert hp.heat_setpoint.value_celsius == 25.0

    def test_parses_cool_setpoint(self):
        hp = HeatPump.from_registers(make_registers(cool_target=200))
        assert hp.cool_setpoint.value_celsius == 20.0

    def test_parses_auto_setpoint(self):
        hp = HeatPump.from_registers(make_registers(auto_target=220))
        assert hp.auto_setpoint.value_celsius == 22.0

    def test_parses_inlet_temp(self):
        hp = HeatPump.from_registers(make_registers(inlet_temp=245))
        assert hp.inlet_temp.value_celsius == 24.5

    def test_parses_outlet_temp(self):
        hp = HeatPump.from_registers(make_registers(outlet_temp=280))
        assert hp.outlet_temp.value_celsius == 28.0

    def test_parses_ambient_temp(self):
        hp = HeatPump.from_registers(make_registers(ambient_temp=150))
        assert hp.ambient_temp.value_celsius == 15.0

    def test_parses_fault_flags(self):
        hp = HeatPump.from_registers(make_registers(fault_flags=0b101))
        assert hp.fault_flags == 5

    def test_wrong_register_count_raises(self):
        with pytest.raises(ValueError):
            HeatPump.from_registers([0] * 10)

    def test_too_many_registers_raises(self):
        with pytest.raises(ValueError):
            HeatPump.from_registers([0] * 50)


class TestHeatPumpTargetTemperature:
    def test_heat_mode_returns_heat_setpoint(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.HEAT, heat_target=250))
        assert hp.target_temperature.value_celsius == 25.0

    def test_single_heat_mode_returns_heat_setpoint(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.SINGLE_HEAT, heat_target=260))
        assert hp.target_temperature.value_celsius == 26.0

    def test_cool_mode_returns_cool_setpoint(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.COOL, cool_target=200))
        assert hp.target_temperature.value_celsius == 20.0

    def test_single_cool_mode_returns_cool_setpoint(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.SINGLE_COOL, cool_target=185))
        assert hp.target_temperature.value_celsius == 18.5

    def test_auto_mode_returns_auto_setpoint(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.AUTO, auto_target=220))
        assert hp.target_temperature.value_celsius == 22.0


class TestHeatPumpIsFaulted:
    def test_no_fault_when_flags_zero(self):
        hp = HeatPump.from_registers(make_registers(fault_flags=0))
        assert not hp.is_faulted

    def test_faulted_when_flags_nonzero(self):
        hp = HeatPump.from_registers(make_registers(fault_flags=1))
        assert hp.is_faulted


class TestHeatPumpImmutability:
    def test_is_frozen(self):
        hp = HeatPump.from_registers(make_registers())
        with pytest.raises((AttributeError, TypeError)):
            hp.power = PowerState.OFF  # type: ignore[misc]
