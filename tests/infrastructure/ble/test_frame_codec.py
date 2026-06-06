import pytest

from custom_components.aquatemp.domain.exceptions import FrameError
from custom_components.aquatemp.infrastructure.ble.frame_codec import (
    build_read_frame,
    build_write_frame,
    crc16_modbus,
    parse_fc03_response,
    validate_response_crc,
)


class TestCrc16Modbus:
    def test_known_poll_frame_crc(self):
        # "63030007002D" → CRC should be 0x543C (lo=3C, hi=54)
        data = bytes.fromhex("63030007002D")
        crc = crc16_modbus(data)
        assert crc == 0x543C

    def test_known_write_power_on_crc(self):
        # From spec: Power ON = "631000080001020001D7BA"
        data = bytes.fromhex("631000080001020001")
        crc = crc16_modbus(data)
        crc_lo = crc & 0xFF
        crc_hi = (crc >> 8) & 0xFF
        assert bytes([crc_lo, crc_hi]).hex().upper() == "D7BA"

    def test_empty_data(self):
        # Smoke test — should not raise
        crc16_modbus(b"")

    def test_single_byte(self):
        # Should not raise
        crc16_modbus(bytes([0xFF]))


class TestBuildReadFrame:
    def test_returns_poll_frame_from_spec(self):
        assert build_read_frame() == "63030007002D3C54"


class TestBuildWriteFrame:
    def test_power_on_matches_spec(self):
        # Spec: Power ON = "631000080001020001D7BA"
        frame = build_write_frame(8, 1)
        assert frame.upper() == "631000080001020001D7BA"

    def test_power_off_matches_spec(self):
        # Spec: Power OFF = "631000080001020000167A"
        frame = build_write_frame(8, 0)
        assert frame.upper() == "631000080001020000167A"

    def test_mode_single_cool_matches_spec(self):
        # Spec: Mode = singleCool = "6310000D0001020000162F"
        frame = build_write_frame(13, 0)
        assert frame.upper() == "6310000D0001020000162F"

    def test_mode_single_heat_matches_spec(self):
        # Spec: Mode = singleHeat = "6310000D0001020001D7EF"
        frame = build_write_frame(13, 1)
        assert frame.upper() == "6310000D0001020001D7EF"

    def test_mode_auto_matches_spec(self):
        # Spec: Mode = auto = "6310000D000102000417EC"
        frame = build_write_frame(13, 4)
        assert frame.upper() == "6310000D000102000417EC"

    def test_heat_target_25_matches_spec(self):
        # Spec: SetHeatTargetTemp=25.0°C = "6310001400010200FA9465"
        frame = build_write_frame(20, 250)
        assert frame.upper() == "6310001400010200FA9465"

    def test_heat_target_30_matches_spec(self):
        # Spec: SetHeatTargetTemp=30.0°C = "63100014000102012C146B"
        frame = build_write_frame(20, 300)
        assert frame.upper() == "63100014000102012C146B"

    def test_cool_target_20_matches_spec(self):
        # Spec: SetCoolTargetTemp=20.0°C = "6310001300010200C81407"
        frame = build_write_frame(19, 200)
        assert frame.upper() == "6310001300010200C81407"

    def test_auto_target_28_matches_spec(self):
        # Spec: SetAutoTargetTemp=28.0°C = "631000150001020118146D"
        frame = build_write_frame(21, 280)
        assert frame.upper() == "631000150001020118146D"

    def test_frame_length_is_22_chars(self):
        # FC16 single register = 11 bytes = 22 hex chars
        frame = build_write_frame(8, 1)
        assert len(frame) == 22


class TestValidateResponseCrc:
    def test_poll_frame_crc_validates(self):
        assert validate_response_crc("63030007002D3C54")

    def test_modified_frame_fails_crc(self):
        assert not validate_response_crc("63030007002D3C55")

    def test_empty_string_returns_false(self):
        assert not validate_response_crc("")

    def test_invalid_hex_returns_false(self):
        assert not validate_response_crc("ZZZZ")

    def test_too_short_returns_false(self):
        assert not validate_response_crc("63")


class TestParseFc03Response:
    def _build_valid_response(self, registers: list[int]) -> str:
        """Build a valid 95-byte FC03 response hex string."""
        payload = bytes([0x63, 0x03, 0x5A])
        for reg in registers:
            # Encode as signed 16-bit big-endian
            val = reg & 0xFFFF
            payload += bytes([(val >> 8) & 0xFF, val & 0xFF])
        crc = crc16_modbus(payload)
        frame = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        return frame.hex().upper()

    def test_parses_45_registers(self):
        regs = list(range(45))
        response = self._build_valid_response(regs)
        parsed = parse_fc03_response(response)
        assert len(parsed) == 45

    def test_correct_register_values(self):
        regs = [i * 10 for i in range(45)]
        response = self._build_valid_response(regs)
        parsed = parse_fc03_response(response)
        assert parsed == regs

    def test_parses_negative_temperature(self):
        # Register value -50 (0xFFCE) = -5.0°C
        regs = [0] * 45
        regs[19] = -50
        response = self._build_valid_response(regs)
        parsed = parse_fc03_response(response)
        assert parsed[19] == -50

    def test_wrong_length_raises_frame_error(self):
        with pytest.raises(FrameError):
            parse_fc03_response("63035A" + "0000" * 44)  # missing one register + CRC

    def test_invalid_hex_raises_frame_error(self):
        with pytest.raises(FrameError):
            parse_fc03_response("ZZZZ")

    def test_bad_slave_address_raises_frame_error(self):
        regs = [0] * 45
        response = self._build_valid_response(regs)
        # Corrupt slave byte
        corrupted = "FF" + response[2:]
        with pytest.raises(FrameError):
            parse_fc03_response(corrupted)

    def test_bad_crc_raises_frame_error(self):
        regs = [0] * 45
        response = self._build_valid_response(regs)
        # Corrupt last CRC byte
        corrupted = response[:-2] + "FF"
        with pytest.raises(FrameError):
            parse_fc03_response(corrupted)
