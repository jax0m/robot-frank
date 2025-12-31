"""
ADEEPT Robot V3.1 HAT – top‑level package.

This module re‑exports the main driver classes so that users can simply do:

    from src.hardware.adeept_robot_v3-1 import LedDriver, ServoGroup

rather than having to know the full sub‑package paths.
"""

from .leds import LedDriver
from .servos import ServoDriver

# Future re‑exports can be added here (e.g., ADC, DigitalIO)
