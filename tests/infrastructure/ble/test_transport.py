import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.auqatemp.domain.exceptions import CommunicationError, DeviceNotReady
from custom_components.auqatemp.infrastructure.ble.transport import BleakTransport

_MAC = "AA:BB:CC:DD:EE:FF"
_FRAME = "63030007002D3C54"
_RESPONSE_HEX = "63035A" + "0000" * 45 + "0000"  # simplified; not a real CRC


def _make_bleak_client_mock(notify_data: bytes | None = b"\x63\x03\x5A" + b"\x00\x5A"):
    """Return a context-manager mock for BleakClient that fires a notification."""

    client_mock = AsyncMock()

    async def fake_start_notify(char_uuid, callback):
        if notify_data is not None:
            callback(0, bytearray(notify_data))

    client_mock.start_notify = fake_start_notify
    client_mock.stop_notify = AsyncMock()
    client_mock.write_gatt_char = AsyncMock()

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client_mock)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm, client_mock


class TestBleakTransportSendAndReceive:
    async def test_returns_notification_as_hex(self):
        raw = bytes([0x63, 0x03, 0x5A] + [0x00] * 90 + [0xAB, 0xCD])
        cm, client = _make_bleak_client_mock(notify_data=raw)
        with patch(
            "custom_components.auqatemp.infrastructure.ble.transport.BleakClient",
            return_value=cm,
        ):
            transport = BleakTransport(_MAC)
            result = await transport.send_and_receive(_FRAME)
        assert result == raw.hex().upper()
        client.write_gatt_char.assert_called_once()

    async def test_writes_correct_frame_bytes(self):
        raw = bytes([0x63, 0x03, 0x5A] + [0x00] * 90 + [0x00, 0x00])
        cm, client = _make_bleak_client_mock(notify_data=raw)
        with patch(
            "custom_components.auqatemp.infrastructure.ble.transport.BleakClient",
            return_value=cm,
        ):
            transport = BleakTransport(_MAC)
            await transport.send_and_receive(_FRAME)
        call_args = client.write_gatt_char.call_args
        assert call_args[0][1] == bytes.fromhex(_FRAME)

    async def test_timeout_raises_communication_error(self):
        cm, client = _make_bleak_client_mock(notify_data=None)

        async def fake_start_notify(char_uuid, callback):
            pass  # never fires callback

        client.start_notify = fake_start_notify

        with patch(
            "custom_components.auqatemp.infrastructure.ble.transport.BleakClient",
            return_value=cm,
        ), patch(
            "custom_components.auqatemp.infrastructure.ble.transport._NOTIFY_TIMEOUT_SECONDS",
            0.01,
        ):
            transport = BleakTransport(_MAC)
            with pytest.raises(CommunicationError):
                await transport.send_and_receive(_FRAME)

    async def test_bleak_error_raises_device_not_ready(self):
        from bleak import BleakError

        cm = MagicMock()
        cm.__aenter__ = AsyncMock(side_effect=BleakError("connection refused"))
        cm.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "custom_components.auqatemp.infrastructure.ble.transport.BleakClient",
            return_value=cm,
        ):
            transport = BleakTransport(_MAC)
            with pytest.raises(DeviceNotReady):
                await transport.send_and_receive(_FRAME)


class TestBleakTransportSend:
    async def test_send_writes_frame(self):
        cm, client = _make_bleak_client_mock()
        with patch(
            "custom_components.auqatemp.infrastructure.ble.transport.BleakClient",
            return_value=cm,
        ):
            transport = BleakTransport(_MAC)
            await transport.send(_FRAME)
        client.write_gatt_char.assert_called_once()

    async def test_send_bleak_error_raises_device_not_ready(self):
        from bleak import BleakError

        cm = MagicMock()
        cm.__aenter__ = AsyncMock(side_effect=BleakError("no device"))
        cm.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "custom_components.auqatemp.infrastructure.ble.transport.BleakClient",
            return_value=cm,
        ):
            transport = BleakTransport(_MAC)
            with pytest.raises(DeviceNotReady):
                await transport.send(_FRAME)
