class AquaTempError(Exception):
    """Base exception for all AquaTemp domain errors."""


class InvalidSetPoint(AquaTempError):
    """Raised when a temperature setpoint is outside the allowed range."""


class DeviceNotReady(AquaTempError):
    """Raised when the device cannot be connected to or is unavailable."""


class FrameError(AquaTempError):
    """Raised when a BLE frame cannot be parsed or fails CRC validation."""


class CommunicationError(AquaTempError):
    """Raised when a BLE operation times out or is interrupted."""
