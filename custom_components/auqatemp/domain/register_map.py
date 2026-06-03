from dataclasses import dataclass

SLAVE_ADDRESS: int = 0x63
REGISTER_COUNT: int = 45
READ_START_ADDRESS: int = 7

# Pre-computed poll frame: FC03, addr=7, qty=45, CRC=0x543C
POLL_FRAME: str = "63030007002D3C54"

# Modbus write addresses (FC16 target addresses)
MODBUS_ADDR_POWER: int = 8
MODBUS_ADDR_MODE: int = 13
MODBUS_ADDR_COOL_TARGET: int = 19
MODBUS_ADDR_HEAT_TARGET: int = 20
MODBUS_ADDR_AUTO_TARGET: int = 21

# Register indices in the FC03 response (0-based after the 3-byte header)
REG_PV_READY_MODE: int = 0
REG_POWER: int = 1
REG_FREQUENCY_MODE: int = 2
REG_FAN_MODE: int = 3
REG_BOOST_MODE: int = 4
REG_APP_TIME_UPDATE: int = 5
REG_MODE: int = 6
REG_SET_CURRENT_TEMP: int = 7
REG_MODE_TYPE: int = 8
REG_TEMP_UNIT: int = 9
REG_OUTLET_SENSOR_EN: int = 10
REG_SILENT: int = 11
REG_COOL_TARGET: int = 12
REG_HEAT_TARGET: int = 13
REG_AUTO_TARGET: int = 14
REG_COOL_MIN: int = 15
REG_COOL_MAX: int = 16
REG_HEAT_MIN: int = 17
REG_HEAT_MAX: int = 18
REG_INLET_WATER_TEMP: int = 19
REG_OUTLET_WATER_TEMP: int = 20
REG_AMBIENT_TEMP: int = 21
REG_FAULT1: int = 40
REG_MAIN_SW_VER: int = 41
REG_MAIN_SW_CODE: int = 42
REG_DISPLAY_SW_VER: int = 43
REG_DISPLAY_SW_CODE: int = 44

TEMP_SCALE: float = 10.0
SETPOINT_MIN_CELSIUS: float = 5.0
SETPOINT_MAX_CELSIUS: float = 32.0


@dataclass(frozen=True)
class RegisterField:
    index: int
    name: str


REGISTER_FIELDS: tuple[RegisterField, ...] = (
    RegisterField(REG_POWER, "power"),
    RegisterField(REG_MODE, "mode"),
    RegisterField(REG_COOL_TARGET, "cool_target"),
    RegisterField(REG_HEAT_TARGET, "heat_target"),
    RegisterField(REG_AUTO_TARGET, "auto_target"),
    RegisterField(REG_INLET_WATER_TEMP, "inlet_water_temp"),
    RegisterField(REG_OUTLET_WATER_TEMP, "outlet_water_temp"),
    RegisterField(REG_AMBIENT_TEMP, "ambient_temp"),
    RegisterField(REG_FAULT1, "fault1"),
)
