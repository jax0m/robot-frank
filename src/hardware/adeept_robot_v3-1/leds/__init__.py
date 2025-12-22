"""
Public API for the LED subsystem of the ADEEPT Robot V3.1 HAT.

The module re‑exports the :class:`LedDriver` so that users can simply import:

    from src.hardware.adeept_robot_v3-1.leds import LedDriver

instead of using the fully‑qualified path.
"""

from .ws2812 import LedDriver

__all__ = ["LedDriver"]
