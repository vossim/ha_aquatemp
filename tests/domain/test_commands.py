import pytest

from custom_components.auqatemp.domain.commands import SetMode, SetPower, SetTemperature
from custom_components.auqatemp.domain.value_objects import OperatingMode, PowerState, SetPoint


class TestSetPower:
    def test_stores_power_state(self):
        cmd = SetPower(PowerState.ON)
        assert cmd.power == PowerState.ON

    def test_is_immutable(self):
        cmd = SetPower(PowerState.OFF)
        with pytest.raises((AttributeError, TypeError)):
            cmd.power = PowerState.ON  # type: ignore[misc]


class TestSetMode:
    def test_stores_mode(self):
        cmd = SetMode(OperatingMode.HEAT)
        assert cmd.mode == OperatingMode.HEAT

    def test_is_immutable(self):
        cmd = SetMode(OperatingMode.COOL)
        with pytest.raises((AttributeError, TypeError)):
            cmd.mode = OperatingMode.HEAT  # type: ignore[misc]


class TestSetTemperature:
    def test_stores_address_and_setpoint(self):
        sp = SetPoint(25.0)
        cmd = SetTemperature(modbus_address=20, set_point=sp)
        assert cmd.modbus_address == 20
        assert cmd.set_point == sp

    def test_is_immutable(self):
        cmd = SetTemperature(modbus_address=20, set_point=SetPoint(25.0))
        with pytest.raises((AttributeError, TypeError)):
            cmd.modbus_address = 99  # type: ignore[misc]
