from __future__ import annotations

import asyncio
from typing import Callable

from bleak import BleakClient, BleakError

from ...domain.exceptions import CommunicationError, DeviceNotReady

_SERVICE_UUID = "0000fee7-0000-1000-8000-00805f9b34fb"
_WRITE_CHAR_UUID = "0000fec7-0000-1000-8000-00805f9b34fb"
_NOTIFY_CHAR_UUID = "0000fec8-0000-1000-8000-00805f9b34fb"

_CONNECT_TIMEOUT_SECONDS = 10.0
_NOTIFY_TIMEOUT_SECONDS = 5.0


class BleakTransport:
    """BLE transport that connects on demand for each operation."""

    def __init__(self, mac_address: str) -> None:
        self._mac_address = mac_address

    async def send_and_receive(self, frame: str) -> str:
        """Write frame to the device and return the first notification as hex."""
        received: asyncio.Future[str] = asyncio.get_event_loop().create_future()

        def _on_notify(_sender: int, data: bytearray) -> None:
            if not received.done():
                received.set_result(data.hex().upper())

        try:
            async with BleakClient(
                self._mac_address, timeout=_CONNECT_TIMEOUT_SECONDS
            ) as client:
                await client.start_notify(_NOTIFY_CHAR_UUID, _on_notify)
                await client.write_gatt_char(
                    _WRITE_CHAR_UUID,
                    bytes.fromhex(frame),
                    response=False,
                )
                try:
                    return await asyncio.wait_for(received, timeout=_NOTIFY_TIMEOUT_SECONDS)
                except asyncio.TimeoutError as exc:
                    raise CommunicationError(
                        f"No notification received within {_NOTIFY_TIMEOUT_SECONDS}s"
                    ) from exc
                finally:
                    await client.stop_notify(_NOTIFY_CHAR_UUID)
        except BleakError as exc:
            raise DeviceNotReady(
                f"Cannot connect to device at {self._mac_address}: {exc}"
            ) from exc

    async def send(self, frame: str) -> None:
        """Write frame to the device without waiting for a response."""
        try:
            async with BleakClient(
                self._mac_address, timeout=_CONNECT_TIMEOUT_SECONDS
            ) as client:
                await client.write_gatt_char(
                    _WRITE_CHAR_UUID,
                    bytes.fromhex(frame),
                    response=False,
                )
        except BleakError as exc:
            raise DeviceNotReady(
                f"Cannot connect to device at {self._mac_address}: {exc}"
            ) from exc
