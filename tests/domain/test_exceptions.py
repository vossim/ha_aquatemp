import pytest

from custom_components.auqatemp.domain.exceptions import (
    AquaTempError,
    CommunicationError,
    DeviceNotReady,
    FrameError,
    InvalidSetPoint,
)


def test_all_exceptions_inherit_from_base():
    for exc_type in (InvalidSetPoint, DeviceNotReady, FrameError, CommunicationError):
        assert issubclass(exc_type, AquaTempError)


def test_exceptions_can_be_raised_and_caught():
    for exc_type in (InvalidSetPoint, DeviceNotReady, FrameError, CommunicationError):
        with pytest.raises(AquaTempError):
            raise exc_type("test message")
