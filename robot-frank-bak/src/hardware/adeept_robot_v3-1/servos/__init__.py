"""
Public API for the Servo subsystem of the ADEEPT Robot V3.1 HAT.

The module exposes a ready‑to‑use ``ServoDriver`` instance and a small
convenience ``move`` function so that user code can simply write::

    from src.hardware.adeept_robot_v3-1.servos import move

    move("base_joint", 90)   # set the "base_joint" servo to 90°
"""

from .driver import ServoDriver, create_servo_driver

# Create a singleton driver that points at the bundled configuration.
# Users can import the driver directly if they need finer‑grained control.
_driver = create_servo_driver()


def move(name: str, angle: float) -> None:
    """
    Move the named servo to *angle* (0‑180°).

    Parameters
    ----------
    name : str
        Logical servo name as defined in ``servos/config.yaml``.
    angle : float
        Desired angle in degrees.
    """
    _driver.set_angle(name, angle)


def get_driver() -> ServoDriver:
    """
    Return the underlying :class:`ServoDriver` instance.
    This is useful if you need to call methods that are not wrapped by
    the ``move`` helper (e.g. ``set_pulse_width``).
    """
    return _driver
