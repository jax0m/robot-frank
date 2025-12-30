"""
Common utilities for ADEEPT Robot V3.1 HAT.

Provides low‑level bus access (SPI, I²C, PWM) that can be used by
component‑specific drivers.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class BusDevice(ABC):
    """Abstract base for a device connected via SPI or I²C."""

    def __init__(self, device_path: str):
        self.device_path = Path(device_path)

    @abstractmethod
    def open(self) -> None:
        """Open the underlying hardware resource."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the underlying hardware resource."""
        ...

    @abstractmethod
    def read(self, nbytes: int = 1) -> bytes:
        """Read *nbytes* bytes from the device."""
        ...

    @abstractmethod
    def write(self, data: bytes) -> None:
        """Write *data* to the device."""
        ...
