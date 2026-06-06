from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from custom_components.aquatemp.domain.commands import SetMode, SetPower, SetTemperature
from custom_components.aquatemp.domain.heat_pump import HeatPump
from custom_components.aquatemp.domain.value_objects import OperatingMode, PowerState, SetPoint
from custom_components.aquatemp.infrastructure.ha.climate_entity import AquaTempClimateEntity
from homeassistant.components.climate import HVACAction, HVACMode
from tests.conftest import make_registers


def _make_coordinator(heat_pump: HeatPump | None = None, success: bool = True) -> MagicMock:
    coord = MagicMock()
    coord.last_update_success = success
    coord.data = heat_pump or HeatPump.from_registers(make_registers())
    coord.async_execute = AsyncMock()
    coord.async_add_listener = MagicMock(return_value=MagicMock())
    return coord


def _make_entity(coordinator=None) -> AquaTempClimateEntity:
    coord = coordinator or _make_coordinator()
    entity = AquaTempClimateEntity(coord, unique_id="test-uid")
    return entity


class TestAvailability:
    def test_available_when_coordinator_success_and_data(self):
        entity = _make_entity(_make_coordinator(success=True))
        assert entity.available is True

    def test_unavailable_when_coordinator_failure(self):
        entity = _make_entity(_make_coordinator(success=False))
        assert entity.available is False

    def test_unavailable_when_no_data(self):
        coord = _make_coordinator(success=True)
        coord.data = None
        entity = _make_entity(coord)
        assert entity.available is False


class TestTemperatureProperties:
    def test_current_temperature_returns_inlet_temp(self):
        hp = HeatPump.from_registers(make_registers(inlet_temp=245))
        entity = _make_entity(_make_coordinator(hp))
        assert entity.current_temperature == 24.5

    def test_target_temperature_returns_heat_setpoint_in_heat_mode(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.HEAT, heat_target=250))
        entity = _make_entity(_make_coordinator(hp))
        assert entity.target_temperature == 25.0

    def test_target_temperature_returns_cool_setpoint_in_cool_mode(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.COOL, cool_target=200))
        entity = _make_entity(_make_coordinator(hp))
        assert entity.target_temperature == 20.0

    def test_current_temperature_none_when_unavailable(self):
        entity = _make_entity(_make_coordinator(success=False))
        assert entity.current_temperature is None

    def test_target_temperature_none_when_unavailable(self):
        entity = _make_entity(_make_coordinator(success=False))
        assert entity.target_temperature is None


class TestHvacMode:
    def test_off_when_power_is_off(self):
        hp = HeatPump.from_registers(make_registers(power=PowerState.OFF))
        entity = _make_entity(_make_coordinator(hp))
        assert entity.hvac_mode == HVACMode.OFF

    def test_heat_when_mode_is_heat(self):
        hp = HeatPump.from_registers(
            make_registers(power=PowerState.ON, mode=OperatingMode.HEAT)
        )
        entity = _make_entity(_make_coordinator(hp))
        assert entity.hvac_mode == HVACMode.HEAT

    def test_heat_when_mode_is_single_heat(self):
        hp = HeatPump.from_registers(
            make_registers(power=PowerState.ON, mode=OperatingMode.SINGLE_HEAT)
        )
        entity = _make_entity(_make_coordinator(hp))
        assert entity.hvac_mode == HVACMode.HEAT

    def test_cool_when_mode_is_cool(self):
        hp = HeatPump.from_registers(
            make_registers(power=PowerState.ON, mode=OperatingMode.COOL)
        )
        entity = _make_entity(_make_coordinator(hp))
        assert entity.hvac_mode == HVACMode.COOL

    def test_cool_when_mode_is_single_cool(self):
        hp = HeatPump.from_registers(
            make_registers(power=PowerState.ON, mode=OperatingMode.SINGLE_COOL)
        )
        entity = _make_entity(_make_coordinator(hp))
        assert entity.hvac_mode == HVACMode.COOL

    def test_heat_cool_when_mode_is_auto(self):
        hp = HeatPump.from_registers(
            make_registers(power=PowerState.ON, mode=OperatingMode.AUTO)
        )
        entity = _make_entity(_make_coordinator(hp))
        assert entity.hvac_mode == HVACMode.HEAT_COOL

    def test_off_when_unavailable(self):
        entity = _make_entity(_make_coordinator(success=False))
        assert entity.hvac_mode == HVACMode.OFF


class TestHvacAction:
    def test_off_when_power_is_off(self):
        hp = HeatPump.from_registers(
            make_registers(power=PowerState.OFF, inlet_temp=240, outlet_temp=240)
        )
        entity = _make_entity(_make_coordinator(hp))
        assert entity.hvac_action == HVACAction.OFF

    def test_heating_when_outlet_much_higher_than_inlet(self):
        hp = HeatPump.from_registers(
            make_registers(power=PowerState.ON, inlet_temp=240, outlet_temp=280)
        )
        entity = _make_entity(_make_coordinator(hp))
        assert entity.hvac_action == HVACAction.HEATING

    def test_cooling_when_outlet_much_lower_than_inlet(self):
        hp = HeatPump.from_registers(
            make_registers(power=PowerState.ON, inlet_temp=280, outlet_temp=240)
        )
        entity = _make_entity(_make_coordinator(hp))
        assert entity.hvac_action == HVACAction.COOLING

    def test_idle_when_delta_within_threshold(self):
        hp = HeatPump.from_registers(
            make_registers(power=PowerState.ON, inlet_temp=250, outlet_temp=260)
        )
        entity = _make_entity(_make_coordinator(hp))
        assert entity.hvac_action == HVACAction.IDLE

    def test_off_when_unavailable(self):
        entity = _make_entity(_make_coordinator(success=False))
        assert entity.hvac_action == HVACAction.OFF


class TestSetHvacMode:
    async def test_off_sends_set_power_off(self):
        entity = _make_entity()
        await entity.async_set_hvac_mode(HVACMode.OFF)
        entity.coordinator.async_execute.assert_called_once_with(SetPower(PowerState.OFF))

    async def test_heat_turns_on_then_sets_single_heat_mode(self):
        entity = _make_entity()
        await entity.async_set_hvac_mode(HVACMode.HEAT)
        calls = entity.coordinator.async_execute.call_args_list
        assert calls[0][0][0] == SetPower(PowerState.ON)
        assert calls[1][0][0] == SetMode(OperatingMode.SINGLE_HEAT)

    async def test_cool_turns_on_then_sets_single_cool_mode(self):
        entity = _make_entity()
        await entity.async_set_hvac_mode(HVACMode.COOL)
        calls = entity.coordinator.async_execute.call_args_list
        assert calls[0][0][0] == SetPower(PowerState.ON)
        assert calls[1][0][0] == SetMode(OperatingMode.SINGLE_COOL)

    async def test_heat_cool_turns_on_then_sets_auto_mode(self):
        entity = _make_entity()
        await entity.async_set_hvac_mode(HVACMode.HEAT_COOL)
        calls = entity.coordinator.async_execute.call_args_list
        assert calls[0][0][0] == SetPower(PowerState.ON)
        assert calls[1][0][0] == SetMode(OperatingMode.AUTO)


class TestSetTemperature:
    async def test_dispatches_set_temperature_command(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.HEAT))
        entity = _make_entity(_make_coordinator(hp))

        await entity.async_set_temperature(temperature=26.0)

        call_arg = entity.coordinator.async_execute.call_args[0][0]
        assert isinstance(call_arg, SetTemperature)
        assert call_arg.set_point.value_celsius == 26.0

    async def test_no_dispatch_when_temperature_missing(self):
        entity = _make_entity()
        await entity.async_set_temperature()
        entity.coordinator.async_execute.assert_not_called()

    async def test_uses_heat_address_in_heat_mode(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.HEAT))
        entity = _make_entity(_make_coordinator(hp))

        await entity.async_set_temperature(temperature=25.0)

        call_arg = entity.coordinator.async_execute.call_args[0][0]
        assert call_arg.modbus_address == 20  # MODBUS_ADDR_HEAT_TARGET

    async def test_uses_cool_address_in_cool_mode(self):
        hp = HeatPump.from_registers(make_registers(mode=OperatingMode.COOL))
        entity = _make_entity(_make_coordinator(hp))

        await entity.async_set_temperature(temperature=20.0)

        call_arg = entity.coordinator.async_execute.call_args[0][0]
        assert call_arg.modbus_address == 19  # MODBUS_ADDR_COOL_TARGET


class TestTurnOnOff:
    async def test_turn_on_dispatches_set_power_on(self):
        entity = _make_entity()
        await entity.async_turn_on()
        entity.coordinator.async_execute.assert_called_once_with(SetPower(PowerState.ON))

    async def test_turn_off_dispatches_set_power_off(self):
        entity = _make_entity()
        await entity.async_turn_off()
        entity.coordinator.async_execute.assert_called_once_with(SetPower(PowerState.OFF))
