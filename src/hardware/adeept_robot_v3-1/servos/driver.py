# src/hardware/adeept_robot_v3-1/servos/driver.py
"""
driver.py – Central wrapper for controlling the PCA9685 PWM driver
            using the configuration defined in config.yaml.

The module provides a high‑level ``ServoDriver`` class that:

* Loads ``config.yaml`` (bus number, I²C address, PWM frequency,
  per‑servo channel and pulse limits).
* Initializes a single ``PCA9685`` instance (from ``pca9685.py``) that
  lives for the lifetime of the process.
* Exposes simple methods such as ``set_angle(channel, angle)``,
  ``set_pwm(channel, pulse_us)`` and ``move_to_named_position(name,
  angle)`` that can be called from user code or from a command‑line
  interface.
* Keeps all I²C handling in a single place, preventing the “missing
  parameter” errors that appeared when the driver was constructed
  with the wrong arguments.

Only standard‑library modules and the local ``pca9685.py`` are used,
so the file stays fully portable and type‑checkable.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any

# ---------------------------------------------------------------------------
# Local PCA9685 driver – we reuse the class that already lives in
# ``pca9685.py``.  Importing it directly gives us access to the low‑level
# register helpers without re‑implementing them.
# ---------------------------------------------------------------------------

from adafruit_pca9685 import PCA9685
from smbus2 import (
    SMBus,
)  # Imported locally to keep import statements at the top level tidy.
import board

import busio


# ---------------------------------------------------------------------------
# Helper for loading the YAML configuration file.
# ---------------------------------------------------------------------------
def _load_config() -> Dict[str, Any]:
    """
    Load ``config.yaml`` from the directory that contains this file.

    The configuration file must contain at least the following sections:

    .. code-block:: yaml

        i2c:
          bus_number: 0                 # Linux I²C bus (e.g. 0 → /dev/i2c-0)
          device_address:
            pwm_driver: 0x40            # 7‑bit address of the PCA9685

        pwm:
          default_freq: 50              # Desired PWM frequency in Hz

        servos:
          base_joint:
            channel: 0
            min_pulse: 150
            max_pulse: 600
            default_angle: 90
          # …additional servos…

    Returns
    -------
    dict
        The parsed configuration dictionary.
    """
    cfg_path = Path(__file__).resolve().parent / "config.yaml"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {cfg_path}")

    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse config.yaml: {exc}") from exc

    # Minimal validation – enough to fail early if required keys are missing.
    if "i2c" not in cfg or "bus_number" not in cfg["i2c"]:
        raise KeyError("config.yaml must contain 'i2c.bus_number'.")
    if (
        "device_address" not in cfg["i2c"]
        or "pwm_driver" not in cfg["i2c"]["device_address"]
    ):
        raise KeyError("config.yaml must contain 'i2c.device_address.pwm_driver'.")
    if "pwm" not in cfg or "default_freq" not in cfg["pwm"]:
        raise KeyError("config.yaml must contain 'pwm.default_freq'.")

    return cfg


# ---------------------------------------------------------------------------
# High‑level driver class
# ---------------------------------------------------------------------------
class ServoDriver:
    """
    Wrapper around the ``PCA9685`` hardware driver that provides a clean,
    typed API for setting servo positions based on the mappings defined in
    ``config.yaml``.

    The driver is **not** thread‑safe by default; if you need to control
    multiple servos from different threads you must add your own locking
    around the calls that modify the PWM registers.

    Example
    -------
    .. code-block:: python

        from src.hardware.adeept_robot_v3_1.servos.driver import ServoDriver
        driver = ServoDriver()
        driver.set_angle("base_joint", 45)          # move to 45°
        driver.set_angle("shoulder_left", 90)      # move to 90°
        driver.close()                              # release the I²C bus
    """

    # -----------------------------------------------------------------------
    # Construction / teardown
    # -----------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Initialise the driver by loading the configuration, opening the I²C
        bus, and creating a single ``PCA9685`` instance.
        """
        cfg = _load_config()

        # Store configuration values that will be used throughout the class.
        self.bus_number: int = cfg["i2c"]["bus_number"]
        self.address: int = cfg["i2c"]["device_address"]["pwm_driver"]
        self.freq: float = cfg["pwm"]["default_freq"]

        # Open the I²C bus exactly once.
        self._bus = self._open_bus()

        try:
            busio.I2C.try_lock(self._bus)

        except Exception as e:
            print("Unable to lock with exception caught as:", e)
        # Create the low‑level PCA9685 object – it takes an already‑opened
        # ``SMBus`` instance and the 7‑bit address.
        self._pca = PCA9685(self._bus, address=self.address)

        # Apply the default PWM frequency.
        self._pca.set_pwm_freq(self.freq)
        self._pca.i2c_device.write()

        # Populate per‑servo lookup tables from the ``servos`` section.
        self._servo_defs: Dict[str, Dict[str, Any]] = cfg["servos"]
        self._channel_map: Dict[str, int] = {
            name: info["channel"] for name, info in self._servo_defs.items()
        }
        self._min_pulse: List[int] = [
            info["min_pulse"] for info in self._servo_defs.values()
        ]
        self._max_pulse: List[int] = [
            info["max_pulse"] for info in self._servo_defs.values()
        ]
        self._default_angle: List[float] = [
            info["default_angle"] for info in self._servo_defs.values()
        ]

        # For convenience we also keep a reverse map from channel → servo name.
        self._channel_to_name: Dict[int, str] = {
            ch: name
            for name, info in self._servo_defs.items()
            if (ch := info.get("channel"))
        }

    @staticmethod
    def _open_bus() -> Any:
        """
        Open the I²C bus using the bus number defined in the configuration.

        Returns
        -------
        smbus2.SMBus
            An active SMBus instance.
        """
        return SMBus(0)  # The bus number will be overridden by the config value later.

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def _pulse_from_angle(self, angle: float, idx: int) -> float:
        """
        Convert an angle (0‑180°) to a pulse width (µs) using the limits
        defined for servo *idx*.

        The conversion follows a linear mapping between ``min_pulse`` and
        ``max_pulse`` for the given servo.
        """
        min_us = self._min_pulse[idx]
        max_us = self._max_pulse[idx]
        return min_us + (angle / 180.0) * (max_us - min_us)

    def set_angle(self, servo_name: str, angle: float) -> None:
        """
        Move the specified servo to *angle* degrees.

        The method performs the following steps:

        1. Look up the channel number associated with ``servo_name``.
        2. Convert the angle to a pulse width in microseconds using the
           servo‑specific limits.
        3. Write the pulse width to the appropriate channel register via
           the underlying ``PCA9685`` instance.

        Parameters
        ----------
        servo_name : str
            The logical name of the servo as defined in ``config.yaml``.
        angle : float
            Desired angle in degrees (0‑180).  Values outside the 0‑180 range
            are clamped to the nearest bound.
        """
        if servo_name not in self._servo_defs:
            raise ValueError(f"Unknown servo name: {servo_name!r}")

        # idx = self._servo_defs[servo_name]["index"]  # We'll add this later if needed
        # Clamp angle to the 0‑180 range.
        angle = max(0.0, min(180.0, angle))

        # Compute the corresponding pulse width in microseconds.
        pulse_us = self._pulse_from_angle(angle, self._servo_defs[servo_name]["index"])

        # Write the pulse to the hardware.
        channel = self._channel_map[servo_name]
        self._pca.set_pwm_on_channel(channel, pulse_us)

    def set_angle_by_channel(self, channel: int, angle: float) -> None:
        """
        Low‑level helper that moves the servo attached to *channel* to
        *angle* degrees.  This method is primarily useful for internal
        implementation; users are encouraged to call :meth:`set_angle`
        with a logical servo name.

        Parameters
        ----------
        channel : int
            The PCA9685 channel number (0‑15).
        angle : float
            Desired angle in degrees.
        """
        # Implementation mirrors ``set_angle`` but works directly with a
        # raw channel number.
        if channel not in self._channel_to_name:
            raise ValueError(f"Channel {channel} is not defined in the configuration.")
        idx = self._servo_defs[self._channel_to_name[channel]]["index"]
        pulse_us = self._pulse_from_angle(angle, idx)
        self._pca.set_pwm_on_channel(channel, pulse_us)

    def get_channel(self, servo_name: str) -> int:
        """
        Return the hardware channel number that is bound to *servo_name*.

        Returns
        -------
        int
            The channel number (0‑15) used by the PCA9685.
        """
        return self._channel_map[servo_name]

    def close(self) -> None:
        """
        Close the underlying ``SMBus`` connection and release the I²C
        resources.  After calling this method the driver instance must not
        be used any further.
        """
        self._bus.close()

    # -----------------------------------------------------------------------
    # Convenience methods for common patterns
    # -----------------------------------------------------------------------
    def home_all(self) -> None:
        """
        Move every servo to its ``default_angle`` value defined in the
        configuration file.
        """
        for name in self._servo_defs:
            self.set_angle(name, self._default_angle[self._servo_defs[name]["index"]])

    def set_all_angles(self, angles: List[float]) -> None:
        """
        Set the angle for *all* servos at once.  ``angles`` must be a list
        with the same length as the number of configured servos; each
        element corresponds to the servo order defined in ``config.yaml``.
        """
        for idx, name in enumerate(self._servo_defs):
            self.set_angle(name, angles[idx])

    # -----------------------------------------------------------------------
    # Pythonic dunder methods for context‑manager usage
    # -----------------------------------------------------------------------
    def __enter__(self) -> "ServoDriver":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Simple command‑line interface – handy for quick manual testing.
# ---------------------------------------------------------------------------
def _cli() -> None:
    """
    Minimal command‑line interface that allows a user to set a single
    servo channel to a specific pulse width or angle.  The CLI parses the
    same ``config.yaml`` used by the library, so any changes made there
    are immediately reflected here.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Set a PCA9685 servo channel to a given angle or pulse width."
    )
    parser.add_argument(
        "--servo",
        type=str,
        required=True,
        help="Logical servo name as defined in config.yaml (e.g. 'base_joint').",
    )
    parser.add_argument(
        "--angle",
        type=float,
        default=None,
        help="Desired angle in degrees (0‑180). Mutually exclusive with --pulse-us.",
    )
    parser.add_argument(
        "--pulse-us",
        type=float,
        default=None,
        help="Pulse width in microseconds. Mutually exclusive with --angle.",
    )
    parser.add_argument(
        "--freq",
        type=float,
        default=None,
        help="Override the PWM frequency defined in config.yaml.",
    )
    args = parser.parse_args()

    # Validate mutually exclusive arguments.
    if (args.angle is None) == (args.pulse_us is None):
        parser.error("Exactly one of '--angle' or '--pulse-us' must be provided.")

    # Load configuration.
    cfg = _load_config()
    address = cfg["i2c"]["device_address"]["pwm_driver"]
    print("Loaded Address:", address)
    freq = args.freq if args.freq is not None else cfg["pwm"]["default_freq"]

    # Open bus and instantiate driver.
    try:
        bus_addr = cfg["i2c"]["bus_number"]
        bus = SMBus(bus_addr)
        print("Got bus:", bus_addr)
        i2c = board.I2C()
    except Exception as exc:
        sys.stderr.write(f"Failed to open I2C bus: {exc}\n")
        sys.exit(1)

    try:
        pca = PCA9685(i2c, address=0x5F)
        if args.freq is not None:
            pca.set_pwm_freq(freq)

        # Determine whether we are given an angle or a pulse width.
        if args.angle is not None:
            # Convert angle → pulse width using the limits for the requested servo.
            # For a quick conversion we reuse the linear mapping defined in the
            # driver (150‑600 µs for a 0‑180° range).
            pulse_us = 150 + (args.angle / 180.0) * (600 - 150)
        else:
            pulse_us = args.pulse_us

        pulse_12bit = int(round(pulse_us * 4096 / 1_000_000)) & 0xFFF  # → 0‑4095
        # Find the channel number for the requested servo.
        channel = cfg["pwm"]["servos"][args.servo]["channel"]
        pca.channels[channel].duty_cycle = pulse_12bit
        # pca.set_pwm_on_channel(channel, pulse_us)
        print(
            f"Set {args.servo} to {pulse_us:.1f} µs"
            + (" (angle)" if args.angle else " (pulse)")
        )
    finally:
        bus.close()


if __name__ == "__main__":
    _cli()
