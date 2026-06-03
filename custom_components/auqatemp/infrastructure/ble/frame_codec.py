from __future__ import annotations

from ...domain.exceptions import FrameError
from ...domain.register_map import (
    POLL_FRAME,
    REGISTER_COUNT,
    SLAVE_ADDRESS,
)

_FC03 = 0x03
_FC16 = 0x10
_FC03_BYTE_COUNT = REGISTER_COUNT * 2  # 90 = 0x5A
_RESPONSE_HEADER_BYTES = 3  # slave + FC + byte_count
_CRC_BYTES = 2
_EXPECTED_RESPONSE_BYTES = _RESPONSE_HEADER_BYTES + _FC03_BYTE_COUNT + _CRC_BYTES  # 95
_EXPECTED_RESPONSE_HEX_LEN = _EXPECTED_RESPONSE_BYTES * 2  # 190 chars


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def build_read_frame() -> str:
    return POLL_FRAME


def build_write_frame(modbus_address: int, value: int) -> str:
    """Build an FC16 single-register write frame as an ASCII hex string."""
    addr_hi = (modbus_address >> 8) & 0xFF
    addr_lo = modbus_address & 0xFF
    val_hi = (value >> 8) & 0xFF
    val_lo = value & 0xFF
    # FC16: slave, 0x10, addr_hi, addr_lo, 0x00, 0x01 (qty), 0x02 (byte count), val_hi, val_lo
    payload = bytes([SLAVE_ADDRESS, _FC16, addr_hi, addr_lo, 0x00, 0x01, 0x02, val_hi, val_lo])
    crc = crc16_modbus(payload)
    frame = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    return frame.hex().upper()


def validate_response_crc(hex_str: str) -> bool:
    """Return True if the frame's CRC matches the appended CRC bytes."""
    try:
        data = bytes.fromhex(hex_str)
    except ValueError:
        return False
    if len(data) < _CRC_BYTES + 1:
        return False
    payload, crc_lo, crc_hi = data[:-2], data[-2], data[-1]
    expected_crc = (crc_hi << 8) | crc_lo
    return crc16_modbus(payload) == expected_crc


def parse_fc03_response(hex_str: str) -> list[int]:
    """Parse an FC03 response and return 45 signed 16-bit register values."""
    try:
        data = bytes.fromhex(hex_str)
    except ValueError as exc:
        raise FrameError(f"Response is not valid hex: {hex_str!r}") from exc

    if len(data) != _EXPECTED_RESPONSE_BYTES:
        raise FrameError(
            f"Expected {_EXPECTED_RESPONSE_BYTES} bytes, got {len(data)}"
        )

    if data[0] != SLAVE_ADDRESS or data[1] != _FC03 or data[2] != _FC03_BYTE_COUNT:
        raise FrameError(
            f"Unexpected frame header: {data[:3].hex()!r}"
        )

    if not validate_response_crc(hex_str):
        raise FrameError("CRC validation failed")

    registers: list[int] = []
    for i in range(REGISTER_COUNT):
        hi = data[_RESPONSE_HEADER_BYTES + i * 2]
        lo = data[_RESPONSE_HEADER_BYTES + i * 2 + 1]
        raw = (hi << 8) | lo
        # Interpret as signed 16-bit
        registers.append(raw - 0x10000 if raw >= 0x8000 else raw)

    return registers
