from custom_components.aquatemp.domain.register_map import (
    MODBUS_ADDR_AUTO_TARGET,
    MODBUS_ADDR_COOL_TARGET,
    MODBUS_ADDR_HEAT_TARGET,
    MODBUS_ADDR_MODE,
    MODBUS_ADDR_POWER,
    POLL_FRAME,
    REGISTER_COUNT,
    SETPOINT_MAX_CELSIUS,
    SETPOINT_MIN_CELSIUS,
    SLAVE_ADDRESS,
    RegisterField,
)


def test_slave_address_is_99():
    assert SLAVE_ADDRESS == 0x63


def test_register_count_is_45():
    assert REGISTER_COUNT == 45


def test_poll_frame_matches_spec():
    assert POLL_FRAME == "63030007002D3C54"


def test_setpoint_bounds():
    assert SETPOINT_MIN_CELSIUS == 5.0
    assert SETPOINT_MAX_CELSIUS == 32.0


def test_modbus_write_addresses():
    assert MODBUS_ADDR_POWER == 8
    assert MODBUS_ADDR_MODE == 13
    assert MODBUS_ADDR_COOL_TARGET == 19
    assert MODBUS_ADDR_HEAT_TARGET == 20
    assert MODBUS_ADDR_AUTO_TARGET == 21


def test_register_field_is_frozen():
    field = RegisterField(index=1, name="power")
    try:
        field.index = 99  # type: ignore[misc]
        assert False, "Should have raised"
    except (AttributeError, TypeError):
        pass
