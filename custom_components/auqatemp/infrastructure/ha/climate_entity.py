from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ...application.heat_pump_service import HeatPumpService
from ...domain.commands import SetMode, SetPower, SetTemperature
from ...domain.value_objects import OperatingMode, PowerState, SetPoint
from .coordinator import AquaTempCoordinator

_HVAC_MODE_TO_OPERATING_MODE: dict[HVACMode, OperatingMode] = {
    HVACMode.HEAT: OperatingMode.SINGLE_HEAT,
    HVACMode.COOL: OperatingMode.SINGLE_COOL,
    HVACMode.HEAT_COOL: OperatingMode.AUTO,
}

_OPERATING_MODE_TO_HVAC_MODE: dict[OperatingMode, HVACMode] = {
    OperatingMode.SINGLE_HEAT: HVACMode.HEAT,
    OperatingMode.HEAT: HVACMode.HEAT,
    OperatingMode.SINGLE_COOL: HVACMode.COOL,
    OperatingMode.COOL: HVACMode.COOL,
    OperatingMode.AUTO: HVACMode.HEAT_COOL,
}

_INLET_OUTLET_DELTA_THRESHOLD = 2.0


class AquaTempClimateEntity(CoordinatorEntity[AquaTempCoordinator], ClimateEntity):
    """HA climate entity backed by an AquaTempCoordinator."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_min_temp = 5.0
    _attr_max_temp = 32.0
    _attr_target_temperature_step = 0.5
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, coordinator: AquaTempCoordinator, unique_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = unique_id

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def current_temperature(self) -> float | None:
        if not self.available:
            return None
        return self.coordinator.data.inlet_temp.value_celsius

    @property
    def target_temperature(self) -> float | None:
        if not self.available:
            return None
        return self.coordinator.data.target_temperature.value_celsius

    @property
    def hvac_mode(self) -> HVACMode:
        if not self.available:
            return HVACMode.OFF
        state = self.coordinator.data
        if state.power == PowerState.OFF:
            return HVACMode.OFF
        return _OPERATING_MODE_TO_HVAC_MODE.get(state.mode, HVACMode.OFF)

    @property
    def hvac_action(self) -> HVACAction:
        if not self.available or self.coordinator.data.power == PowerState.OFF:
            return HVACAction.OFF
        state = self.coordinator.data
        delta = state.outlet_temp.value_celsius - state.inlet_temp.value_celsius
        if delta > _INLET_OUTLET_DELTA_THRESHOLD:
            return HVACAction.HEATING
        if delta < -_INLET_OUTLET_DELTA_THRESHOLD:
            return HVACAction.COOLING
        return HVACAction.IDLE

    async def async_turn_on(self) -> None:
        await self.coordinator.async_execute(SetPower(PowerState.ON))

    async def async_turn_off(self) -> None:
        await self.coordinator.async_execute(SetPower(PowerState.OFF))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_execute(SetPower(PowerState.OFF))
            return
        operating_mode = _HVAC_MODE_TO_OPERATING_MODE[hvac_mode]
        await self.coordinator.async_execute(SetPower(PowerState.ON))
        await self.coordinator.async_execute(SetMode(operating_mode))

    async def async_set_temperature(self, **kwargs: object) -> None:
        temperature = kwargs.get("temperature")
        if temperature is None:
            return
        state = self.coordinator.data
        address = HeatPumpService.target_address_for_mode(state.mode)
        await self.coordinator.async_execute(
            SetTemperature(address, SetPoint(float(temperature)))
        )
