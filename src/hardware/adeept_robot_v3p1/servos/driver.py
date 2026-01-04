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
    # print(f"Successfully found Configuration file:  {cfg_path}") # Diagnostic output
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            # print("Successfully loaded Configuration file") # Diagnostic output
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse config.yaml: {exc}") from exc

    if "i2c" not in cfg or "bus_number" not in cfg["i2c"]:
        raise KeyError("config.yaml must contain 'i2c.bus_number'.")
    # else: # Diagnostic output
    #     print("Found bus_number in i2c") # Diagnostic output
    if (
        "device_address" not in cfg["i2c"]
        or "pwm_driver" not in cfg["i2c"]["device_address"]
    ):
        raise KeyError("config.yaml must contain 'i2c.device_address.pwm_driver'.")
    # else: # Diagnostic output
    #     print("Found 'i2c.device_address.pwm_driver'") # Diagnostic output
    if "pwm" not in cfg or "default_freq" not in cfg["pwm"]:
        raise KeyError("config.yaml must contain 'pwm.default_freq'.")
    # else: # Diagnostic output
    #     print("Found 'pwm.default_freq'") # Diagnostic output

    # Every servo entry must provide at least the pulse limits and a channel.
    for name, info in cfg["pwm"]["servos"].items():
        for req in ("channel", "min_pulse", "max_pulse", "default_angle"):
            if req not in info:
                raise KeyError(f"Servo '{name}' is missing required key '{req}'.")
        # New optional fields – we simply store them if present.
        info.setdefault("min_angle", 0)
        info.setdefault("max_angle", 180)

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
        self._bus = board.I2C()

        # Create the low‑level PCA9685 object – it takes an already‑opened
        # ``SMBus`` instance and the 7‑bit address.
        self._pca = PCA9685(self._bus, address=self.address)

        # Apply the default PWM frequency.
        self._pca.frequency = self.freq  # type: ignore[attr-defined]

        self._servo_defs: Dict[str, Dict[str, Any]] = cfg["pwm"]["servos"]

        # Mapping ``servo_name → channel`` (hardware channel 0‑15)
        self._channel_map: Dict[str, int] = {
            name: info["channel"] for name, info in self._servo_defs.items()
        }

        # Parallel lists for pulse limits – order will be the same as the
        # enumeration order used for ``_servo_names`` later.
        self._min_pulse: List[float] = []
        self._max_pulse: List[float] = []
        self._default_angle: List[float] = []
        self._angle_limits: List[tuple] = []  # (min_angle, max_angle)
        self._servo_names: List[str] = []  # keep stable order

        for idx, (name, info) in enumerate(self._servo_defs.items()):
            self._servo_names.append(name)
            min_pulse = float(info.get("min_pulse") or 0.0)
            self._min_pulse.append(min_pulse)
            max_pulse = float(info.get("max_pulse") or 0.0)
            self._max_pulse.append(max_pulse)
            default_angle = float(info.get("default_angle") or 0.0)
            self._default_angle.append(default_angle)
            self._angle_limits.append(
                (info.get("min_angle", 0), info.get("max_angle", 180))
            )

        # Validate that every servo has the mandatory keys.
        for name, info in self._servo_defs.items():
            missing = [
                k
                for k in ("channel", "min_pulse", "max_pulse", "default_angle")
                if k not in info
            ]
            if missing:
                raise KeyError(
                    f"Servo '{name}' is missing required keys: {', '.join(missing)}"
                )

        # Stable mapping servo_name → numeric index (0‑based)
        self._servo_index = {name: idx for idx, name in enumerate(self._servo_names)}

        # Mapping channel → servo name for error‑checking helpers.
        self._channel_to_name = {
            ch: name
            for name, info in self._servo_defs.items()
            if (ch := info.get("channel"))
        }

    @staticmethod
    def _open_bus(bus) -> Any:
        """
        Open the I²C bus using the bus number defined in the configuration.

        Returns
        -------
        smbus2.SMBus
            An active SMBus instance.
        """
        return SMBus(
            bus
        )  # The bus number will be overridden by the config value later.

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def _pulse_from_angle(self, angle: float, idx: int) -> float:
        """
        Convert a *desired angle* (in degrees) to a pulse width (µs) using the
        per‑servo pulse limits and angle limits.
        """
        min_angle, max_angle = self._angle_limits[idx]

        # Clamp the requested angle to the servo's allowed range.
        angle = max(min_angle, min(max_angle, angle))

        # ----> Use the *idx*‑th entries of the stored lists <----
        min_us = self._min_pulse[idx]
        max_us = self._max_pulse[idx]
        # print("Converting angle to pulse:\n") # Diagnostic output
        # print(
        #     f"{int(min_us + (angle - min_angle) / (max_angle - min_angle) * (max_us - min_us))}"
        # ) # Diagnostic output
        # Linear interpolation between the two pulse limits.
        return int(
            min_us + (angle - min_angle) / (max_angle - min_angle) * (max_us - min_us)
        )

    def set_angle(self, servo_name: str, angle: float) -> None:
        """
        Move the specified servo (identified by its logical name in
        ``config.yaml``) to *angle* degrees.

        The method:
          1. Verifies that ``servo_name`` exists.
          2. Looks up the hardware channel number.
          3. Clamps *angle* to the servo‑specific ``min_angle`` / ``max_angle``.
          4. Converts the clamped angle to a pulse width using the servo’s
             ``min_pulse`` / ``max_pulse`` limits.
          5. Writes the pulse to the appropriate channel register.
        """
        if servo_name not in self._servo_defs:
            raise ValueError(f"Unknown servo name: {servo_name!r}")

        idx = self._servo_index[servo_name]  # numeric index of the servo
        min_angle, max_angle = self._angle_limits[idx]

        # Clamp to the servo’s allowed angle range.
        angle = max(min_angle, min(max_angle, angle))

        # Compute pulse width using the per‑servo pulse limits.
        pulse_us = self._pulse_from_angle(angle, idx)

        channel = self._channel_map[servo_name]
        # Use the upstream PCA9685 API – write the 12‑bit duty cycle directly. #This was commented out for now as the duty_cycle command seems to want to take the pulse_us more directly.
        # duty = int(round(pulse_us * 4096 / 1_000_000)) & 0xFFF #This was commented out for now as the duty_cycle command seems to want to take the pulse_us more directly.
        self._pca.channels[channel].duty_cycle = pulse_us  # type: ignore[attr-defined]

    def set_pulse(self, servo_name: str, pulse: int) -> None:
        """
        Move the specified servo (identified by its logical name in
        ``config.yaml``) to *pulse* microseconds.
        """
        if servo_name not in self._servo_defs:
            raise ValueError(f"Unknown servo name: {servo_name!r}")
        # print(f"Attempting to set pulse for: {servo_name}") # Diagnostic output
        idx = self._servo_index[servo_name]  # numeric index of the servo
        # print(f"Index of servo as {idx} with min_pulse of:") # Diagnostic output
        min_pulse = self._min_pulse[idx]
        # print(min_pulse, " and a max_pulse of") # Diagnostic output
        max_pulse = self._max_pulse[idx]
        # print(max_pulse, "\n") # Diagnostic output
        # print(
        #     f"Pulse is attempting to be set to {pulse} clamping against min/max results in:"
        # ) # Diagnostic output
        # Clamp to the servo's allowed pulse range.
        pulse_us = int(max(min_pulse, min(max_pulse, pulse)))
        # print(pulse_us, "\n attempting to send value to driver") # Diagnostic output
        channel = self._channel_map[servo_name]
        # print(f"servo channel found as {channel}") # Diagnostic output
        # duty = int(round(pulse_us * 4096 / 1_000_000)) & 0xFFF #This was commented out for now as the duty_cycle command seems to want to take the pulse_us more directly.
        # print(f"calculated duty cycle as: {duty}\n Sending") #This was commented out for now as the duty_cycle command seems to want to take the pulse_us more directly.
        self._pca.channels[channel].duty_cycle = pulse_us  # type: ignore[attr-defined]

    def set_angle_by_channel(self, channel: int, angle: float) -> None:
        """
        Low‑level helper that moves the servo attached to *channel* to
        *angle* degrees.  This method is primarily useful for internal
        implementation; users are encouraged to call :meth:`set_angle`
        with a logical servo name.
        """
        if channel not in self._channel_to_name:
            raise ValueError(f"Channel {channel} is not defined in the configuration.")

        # Resolve the servo name that belongs to this channel.
        servo_name = self._channel_to_name[channel]
        idx = self._servo_index[servo_name]

        # Re‑use the same clamping / conversion logic as ``set_angle``.
        min_angle, max_angle = self._angle_limits[idx]
        angle = max(min_angle, min(max_angle, angle))
        pulse_us = int(self._pulse_from_angle(angle, idx))

        # Use the same duty‑cycle write as in ``set_angle``.
        # duty = int(round(pulse_us * 4096 / 1_000_000)) & 0xFFF #This was commented out for now as the duty_cycle command seems to want to take the pulse_us more directly.
        self._pca.channels[channel].duty_cycle = pulse_us

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
        # self._bus.close()
        self._pca.deinit

    # -----------------------------------------------------------------------
    # Convenience methods for common patterns
    # -----------------------------------------------------------------------
    def home_all(self) -> None:
        """
        Move every servo to its ``default_angle`` value defined in the
        configuration file.
        """
        for idx, name in enumerate(self._servo_defs):
            self.set_angle(name, self._default_angle[idx])

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
        print("ending connection")


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
        "--pulse",
        type=int,
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
    if (args.angle is None) == (args.pulse is None):
        parser.error("Exactly one of '--angle' or '--pulse' must be provided.")

    # Load configuration.
    # cfg = _load_config()
    # freq = args.freq if args.freq is not None else cfg["pwm"]["default_freq"]

    with ServoDriver() as driver:
        # Open bus and instantiate driver.
        try:
            # ---------------------------------------------------------------
            # Pick the requested operation (angle or pulse width) and convert
            # it to a 12‑bit duty cycle.  The conversion mirrors the logic
            # used in ``set_angle`` – we reuse the driver’s own helper when
            # an explicit angle is supplied.
            # ---------------------------------------------------------------
            if args.angle is not None:
                print(f"Setting {args.servo} to {args.angle} deg")
                driver.set_angle(args.servo, args.angle)
                print(f"Set {args.servo} to {args.angle} deg")
            else:
                print(f"Setting {args.servo} to {args.pulse} us")
                driver.set_pulse(args.servo, args.pulse)
                print(f"Set {args.servo} to {args.pulse} us")
        except Exception as e:
            print(f"Could not set {args.servo} encountered exception:\n", e)


if __name__ == "__main__":
    _cli()
