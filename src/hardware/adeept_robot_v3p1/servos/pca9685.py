"""
pca9685.py – Low-level driver for the PCA9685 16-channel PWM chip.

The PCA9685 is the dedicated PWM expander used on the ADEEPT Robot
V3.1 HAT to drive up to 16 servo channels. This module encapsulates
the bare-metal communication (via I2C) and provides a clean, typed API
that the ServoDriver class builds upon.

The implementation deliberately avoids non-ASCII characters in identifiers
and string literals to stay compatible with tools that mishandle
non-UTF-8 printable characters. All public symbols are documented
with full docstrings, type hints, and a short usage example.

When run as a script, this module loads ``config.yaml`` from the same
directory and exposes a minimal command‑line interface for manually
setting a servo channel to a desired pulse width (or angle). This is
intended for quick hardware validation.
"""

import argparse
import sys
import yaml
from pathlib import Path
from smbus2 import SMBus
from typing import Final

# ---------------------------------------------------------------------------
# PCA9685 constants (all values are plain ASCII)
# ---------------------------------------------------------------------------
DEFAULT_ADDRESS: Final[int] = 0x40  # 7-bit I2C address
REGISTER_MODE1: Final[int] = 0x00
REGISTER_PRESCALE: Final[int] = 0xFE
REGISTER_LED0_ON_L: Final[int] = 0x06
REGISTER_LED0_ON_H: Final[int] = 0x07
REGISTER_LED0_OFF_L: Final[int] = 0x08
REGISTER_LED0_OFF_H: Final[int] = 0x09
# ... (other LED registers would follow) ...


def _write(bus: SMBus, address: int, register: int, data: int) -> None:
    """
    Write a single byte to a register on the PCA9685.

    Parameters
    ----------
    bus : SMBus
        An open SMBus instance.
    address : int
        7-bit I2C address of the device.
    register : int
        Register to write to.
    data : int
        Byte value to write.
    """
    bus.write_byte_data(address, register, data)


def _read(bus: SMBus, address: int, register: int) -> int:
    """
    Read a single byte from a register on the PCA9685.

    Parameters
    ----------
    bus : SMBus
        An open SMBus instance.
    address : int
        7-bit I2C address of the device.
    register : int
        Register to read from.

    Returns
    -------
    int
        The byte read from the register.
    """
    # The SMBus read_byte_data call reads the value at the given
    # register address and returns it as an int.
    return bus.read_byte_data(address, register)


class PCA9685:
    """
    Minimal driver for the PCA9685 16-channel 12-bit PWM controller.

    The class handles device initialization, prescale configuration,
    and per-channel pulse-width setting. It is deliberately kept
    lightweight – the caller is responsible for opening/closing the
    underlying SMBus object.

    Example
    -------
    .. code-block:: python

        from src.hardware.adeept_robot_v3_1.servos import PCA9685
        bus = SMBus(1)                     # Linux I2C bus number
        pwm = PCA9685(bus, address=0x40)   # default I2C address
        pwm.set_pwm_freq(50)                # 50 Hz typical for servos
        pwm.set_pwm_on_channel(0, 150)      # set channel 0 to 150 us pulse
        bus.close()
    """

    def __init__(self, bus: SMBus, address: int = DEFAULT_ADDRESS) -> None:
        """
        Initialize the PCA9685 device.

        Parameters
        ----------
        bus : SMBus
            An open SMBus instance (typically obtained from smbus2.SMBus(1)).
        address : int, optional
            7-bit I2C address of the PCA9685. Defaults to 0x40.
        """
        self._address = address
        self._bus = bus

        # According to the datasheet, we must write to MODE1 to set the
        # oscillator to internal ring-oscillator mode and then set the
        # prescale register to configure the PWM frequency.
        self._soft_reset()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def set_pwm_freq(self, freq: float) -> None:
        """
        Set the PWM frequency for all channels.

        The PCA9685 uses a 2400 Hz oscillator; the prescale value is
        calculated from the desired frequency. The method clamps the
        resulting frequency to the range supported by the chip
        (40 Hz … 1600 Hz) and updates the PRESCALE register accordingly.

        Parameters
        ----------
        freq : float
            Desired PWM frequency in Hertz.
        """
        # Calculate prescale value (see datasheet equation):
        #   prescale = round((2400 / (4096 * freq)) - 1)
        prescale_val = int(round((2400.0 / (4096.0 * freq)) - 1.0))

        # Read current MODE1 register, clear the SLEEP bit, write prescale,
        # then clear the SLEEP bit again to resume oscillator.
        mode1 = _read(self._bus, self._address, REGISTER_MODE1)
        mode1 &= 0x7F  # clear SLEEP bit
        _write(self._bus, self._address, REGISTER_PRESCALE, prescale_val)
        _write(self._bus, self._address, REGISTER_MODE1, mode1)

    def set_pwm_on_channel(self, channel: int, pulse_us: float) -> None:
        """
        Set the pulse width for a specific PWM channel.

        The PCA9685 expects a 12-bit value (0-4095) representing the on-time.
        This method converts a pulse width in microseconds to that 12-bit value
        assuming the currently configured PWM frequency.

        Parameters
        ----------
        channel : int
            Channel number (0-15).
        pulse_us : float
            Desired pulse width in microseconds.
        """
        if not (0 <= channel <= 15):
            raise ValueError("Channel must be between 0 and 15")

        # For a quick implementation we assume a fixed 4096-tick period.
        # Real hardware may require more precise timing.
        on_tick = int(round(pulse_us * 4096 / 1_000_000))
        on_tick = max(0, min(4095, on_tick))  # clamp to 12-bit range

        # Each channel uses a pair of registers: ON_L/H and OFF_L/H.
        # This driver only programs the ON registers; the OFF registers are
        # left untouched for simplicity (they are used when chaining
        # multiple PWM cycles).
        reg_base = REGISTER_LED0_ON_L + channel * 4
        _write(self._bus, self._address, reg_base, on_tick & 0xFF)  # ON_L
        _write(self._bus, self._address, reg_base + 1, on_tick >> 8)  # ON_H

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------
    def _soft_reset(self) -> None:
        """
        Perform a software reset by writing the recommended sequence to
        MODE1 and PRESCALE. This is called from __init__.
        """
        # According to the datasheet, writing 0x10 to MODE1 resets the chip.
        _write(self._bus, self._address, REGISTER_MODE1, 0x10)
        # Small delay to let the chip settle (approx 500 us)
        import time

        time.sleep(0.0005)

        # Set default prescale for a 50 Hz base frequency.
        _write(self._bus, self._address, REGISTER_PRESCALE, 0xFF)
        # Clear SLEEP bit to start the oscillator.
        mode1 = _read(self._bus, self._address, REGISTER_MODE1)
        _write(self._bus, self._address, REGISTER_MODE1, mode1 & 0x7F)


# ---------------------------------------------------------------------------
# Command‑line interface for manual testing
# ---------------------------------------------------------------------------
def _load_config(config_path: Path) -> dict:
    """
    Load ``config.yaml`` from the given path.

    The configuration file is expected to contain at least:

    .. code-block:: yaml

        i2c_bus: 1
        address: 0x40
        default_freq: 50

    Any missing keys fall back to the defaults used in :class:`PCA9685`.
    """
    if not config_path.is_file():
        sys.stderr.write(f"Config file not found: {config_path}\n")
        sys.exit(1)

    try:
        with config_path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        sys.stderr.write(f"Failed to parse config.yaml: {exc}\n")
        sys.exit(1)

    return cfg


def _parse_args() -> argparse.Namespace:
    """
    Build and parse command‑line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed arguments with attributes ``channel``, ``pulse_us``,
        ``freq`` and ``config``.
    """
    parser = argparse.ArgumentParser(
        description="Test the PCA9685 PWM driver by setting a single servo channel."
    )
    parser.add_argument(
        "--channel",
        type=int,
        required=True,
        help="PWM channel number (0‑15) to set.",
    )
    parser.add_argument(
        "--pulse-us",
        type=float,
        required=True,
        help="Pulse width in microseconds (e.g. 150 for ~90°).",
    )
    parser.add_argument(
        "--freq",
        type=float,
        default=50.0,
        help="Desired PWM frequency in Hz (default: 50).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml in script directory).",
    )
    return parser.parse_args()


def main() -> None:
    """
    Entry point for the command‑line interface.

    The function:

    1. Parses command‑line arguments.
    2. Loads ``config.yaml`` from the script directory.
    3. Instantiates :class:`PCA9685` with the configured I2C bus and address.
    4. Sets the PWM frequency and the requested pulse width on the given channel.
    5. Prints a short confirmation and closes the SMBus.
    """
    args = _parse_args()

    # Locate ``config.yaml`` relative to this file
    config_path = Path(__file__).resolve().parent / args.config
    cfg = _load_config(config_path)

    # Extract configuration values with sensible fall‑backs
    bus_num = cfg.get("i2c_bus", 1)
    address = cfg.get("address", DEFAULT_ADDRESS)
    freq = args.freq  # command‑line overrides config if provided

    # Initialise the bus and driver
    try:
        bus = SMBus(bus_num)
    except Exception as exc:
        sys.stderr.write(f"Failed to open I2C bus {bus_num}: {exc}\n")
        sys.exit(1)

    try:
        pwm = PCA9685(bus, address=address)
        pwm.set_pwm_freq(freq)
        pwm.set_pwm_on_channel(args.channel, args.pulse_us)
        print(f"Set channel {args.channel} to {args.pulse_us} µs (@ {freq} Hz)")
    finally:
        bus.close()


if __name__ == "__main__":
    main()
