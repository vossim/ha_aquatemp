from typing import Protocol, runtime_checkable


@runtime_checkable
class Transport(Protocol):
    """Abstraction over the BLE communication channel."""

    async def send_and_receive(self, frame: str) -> str:
        """Send a frame and return the response notification as an ASCII hex string."""
        ...

    async def send(self, frame: str) -> None:
        """Send a frame without waiting for a response."""
        ...
