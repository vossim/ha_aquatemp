import pytest

from custom_components.aquatemp.domain.exceptions import InvalidSetPoint
from custom_components.aquatemp.domain.value_objects import (
    OperatingMode,
    PowerState,
    SetPoint,
    TemperatureReading,
)


class TestSetPoint:
    def test_valid_setpoint_stores_value(self):
        sp = SetPoint(25.0)
        assert sp.value_celsius == 25.0

    def test_minimum_boundary_is_accepted(self):
        assert SetPoint(5.0).value_celsius == 5.0

    def test_maximum_boundary_is_accepted(self):
        assert SetPoint(32.0).value_celsius == 32.0

    def test_below_minimum_raises(self):
        with pytest.raises(InvalidSetPoint):
            SetPoint(4.9)

    def test_above_maximum_raises(self):
        with pytest.raises(InvalidSetPoint):
            SetPoint(32.1)

    def test_as_register_value_multiplies_by_ten(self):
        assert SetPoint(25.0).as_register_value() == 250
        assert SetPoint(30.0).as_register_value() == 300
        assert SetPoint(20.0).as_register_value() == 200

    def test_as_register_value_rounds_half_degree(self):
        assert SetPoint(20.5).as_register_value() == 205

    def test_setpoint_is_immutable(self):
        sp = SetPoint(25.0)
        with pytest.raises((AttributeError, TypeError)):
            sp.value_celsius = 30.0  # type: ignore[misc]


class TestTemperatureReading:
    def test_from_register_divides_by_ten(self):
        reading = TemperatureReading.from_register(245)
        assert reading.value_celsius == 24.5

    def test_from_register_handles_negative(self):
        # -50 = 0xFFCE interpreted as signed = -50
        reading = TemperatureReading.from_register(-50)
        assert reading.value_celsius == -5.0

    def test_from_register_zero(self):
        assert TemperatureReading.from_register(0).value_celsius == 0.0

    def test_reading_is_immutable(self):
        reading = TemperatureReading(24.5)
        with pytest.raises((AttributeError, TypeError)):
            reading.value_celsius = 30.0  # type: ignore[misc]


class TestOperatingMode:
    def test_values_match_spec(self):
        assert OperatingMode.SINGLE_COOL == 0
        assert OperatingMode.SINGLE_HEAT == 1
        assert OperatingMode.COOL == 2
        assert OperatingMode.HEAT == 3
        assert OperatingMode.AUTO == 4


class TestPowerState:
    def test_values_match_spec(self):
        assert PowerState.OFF == 0
        assert PowerState.ON == 1
