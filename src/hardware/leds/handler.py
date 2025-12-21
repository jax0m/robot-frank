#!/usr/bin/env python3

"""
Optimized WS2812 driver for Raspberry Pi (SPI) with:
  • config‑driven setup (body & onboard strips)
  • start‑up demo (pulse + rainbow sweep)
  • continuous rainbow animation
"""

import time
import yaml
import threading
import spidev
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration handling
# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"


def load_config() -> dict:
    """Load the YAML configuration file."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Low‑level SPI driver
# ---------------------------------------------------------------------------
class SpiLedStrip(threading.Thread):
    """
    Represents a single WS2812 strip (body or onboard) and runs its
    animation in a dedicated thread.
    """

    # -----------------------------------------------------------------------
    # Construction / basic configuration
    # -----------------------------------------------------------------------
    def __init__(self, cfg: dict, demo: bool = False, rgb_type: str = "GRB"):
        """
        Parameters
        ----------
        cfg : dict
            Sub‑dictionary from the YAML file (e.g. leds.body or leds.onboard).
        demo : bool
            If True, the thread will execute the start‑up demo before entering
            the normal animation loop.
        """
        self.cfg = cfg
        self.count = cfg["count"]
        self.bus = cfg["bus"]
        self.device = cfg["device"]
        self.freq = cfg.get("frequency", 800000)
        self.dma = cfg.get("dma", 10)
        self.invert = cfg.get("invert", False)
        self.brightness = cfg.get("brightness", 255)
        self.rgb_type = cfg.get("rgb_type", "GRB")

        # LED colour offsets for different GRB variants
        self.led_type_offsets = {
            "RGB": 0x06,
            "RBG": 0x09,
            "GRB": 0x12,
            "GBR": 0x21,
            "BRG": 0x18,
            "BGR": 0x24,
        }
        self.red_offset, self.green_offset, self.blue_offset = 0, 0, 0
        self.led_color = [[0, 0, 0] for _ in range(self.count)]
        self.led_original = [[0, 0, 0] for _ in range(self.count)]

        # Runtime state
        self.spi = None
        self.led_init_state = 0  # 0 = not initialised, 1 = ok
        self.light_mode = "none"
        self.set_led_type(rgb_type)
        self.flag = threading.Event()
        self.flag.set()

        # Thread control
        super().__init__(daemon=True)

        # Optional demo execution
        if demo:
            self.demo_startup()

        # Initialise hardware (SPI) immediately after construction
        self._open_spi()

    # -----------------------------------------------------------------------
    # SPI handling
    # -----------------------------------------------------------------------
    def _open_spi(self) -> None:
        """Open the SPI device and set basic mode."""
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(self.bus, self.device)
            self.spi.mode = 0
            self.led_init_state = 1
        except OSError as exc:
            self._handle_spi_error(exc)

    def _handle_spi_error(self, exc: OSError) -> None:
        """Print a helpful message and keep the device in a safe state."""
        print("SPI open failed:", exc)
        print(
            "Check /boot/firmware/config.txt – enable the correct SPI overlay "
            "or adjust the bus/device indices."
        )
        self.led_init_state = 0

    # -----------------------------------------------------------------------
    # Public control helpers
    # -----------------------------------------------------------------------
    def pause(self) -> None:
        """Stop animation and clear the strip."""
        self.light_mode = "none"
        self.flag.clear()
        self._clear_strip()

    def resume(self) -> None:
        """Resume animation (used after a pause)."""
        self.flag.set()

    # -----------------------------------------------------------------------
    # Animation primitives
    # -----------------------------------------------------------------------
    def _clear_strip(self) -> None:
        """Set all LEDs to black and push the update."""
        self._set_all_rgb(0, 0, 0)

    def _set_pixel(self, idx: int, r: int, g: int, b: int) -> None:
        """Store colour for a single pixel (taking brightness into account)."""
        r, g, b = (int(c * self.brightness / 255) for c in (r, g, b))
        # Store original colour for later use (e.g., breath animation)
        self.led_original[idx] = [r, g, b]
        # Convert to the WS2812 bit order defined by the configured type
        self.led_color[idx][self.red_offset] = r
        self.led_color[idx][self.green_offset] = g
        self.led_color[idx][self.blue_offset] = b

    def _set_all_rgb(self, r: int, g: int, b: int) -> None:
        """Set every pixel to the same RGB value and display it."""
        for i in range(self.count):
            self._set_pixel(i, r, g, b)
        self._send_data()

    def _send_data(self) -> None:
        """Transmit the current colour buffer to the strip."""
        if not self.led_init_state:
            return

        # Build a flat array of raw RGB values
        flat = [c for pixel in self.led_color for c in pixel]
        data_len = len(flat)

        # Choose the most efficient bit‑packing routine
        if data_len * 3 <= 64:  # tiny strips – use the 4‑bit version
            tx = self._pack_4bit(flat)
            self._xfer(tx, self.freq / 1_000_000)  # µs → MHz
        else:
            tx = self._pack_8bit(flat)
            self._xfer(tx, self.freq / 1_000_000)

    # -----------------------------------------------------------------------
    # Bit‑packing helpers
    # -----------------------------------------------------------------------
    @staticmethod
    def _pack_8bit(colour_bytes: list[int]) -> bytes:
        """Pack colour data using the WS2812 8‑bit protocol."""
        # There are 8 bytes per colour component (24‑bit colour = 3 bytes)
        tx = bytearray(len(colour_bytes) * 8)
        for ibit in range(8):
            tx[7 - ibit :: 8] = [((c >> ibit) & 1) * 0x78 + 0x80 for c in colour_bytes]
        return bytes(tx)

    @staticmethod
    def _pack_4bit(colour_bytes: list[int]) -> bytes:
        """Pack colour data using the 4‑bit (NYC) protocol."""
        tx = bytearray(len(colour_bytes) * 4)
        for ibit in range(4):
            # Extract two consecutive bits from each colour component
            # and map them to the NYC timing pattern (0x88, 0x60, 0x06, 0x60)
            tx[3 - ibit :: 4] = (
                ((c >> (2 * ibit + 1)) & 1) * 0x60
                + ((c >> (2 * ibit + 0)) & 1) * 0x06
                + 0x88
                for c in colour_bytes
            )
        return bytes(tx)

    # -----------------------------------------------------------------------
    # Low‑level transfer
    # -----------------------------------------------------------------------
    def _xfer(self, data: bytes, hz: float) -> None:
        """Send the prepared byte buffer at the requested frequency."""
        if not self.spi:
            return
        # Convert Hz → transfer length in µs (the original script used a hack)
        # Here we simply use the value as‑is; the hardware expects a byte count.
        self.spi.xfer(list(data), 0)

    # -----------------------------------------------------------------------
    # Animation building blocks
    # -----------------------------------------------------------------------
    @staticmethod
    def _wheel(pos: int) -> tuple[int, int, int]:
        """Generate a colour wheel (classic rainbow)."""
        if pos < 85:
            return (255 - pos * 3, pos * 3, 0)
        if pos < 170:
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)

    def _rainbow_cycle(self, wait_ms: int = 20) -> None:
        """Yield a continuously shifting rainbow across the strip."""
        for start in range(256):
            for i, pixel in enumerate(self.led_color):
                color = self._wheel((i * 256 // self.count + start) % 256)
                self._set_pixel(i, *color)
            self._send_data()
            time.sleep(wait_ms / 1000.0)

    # -----------------------------------------------------------------------
    # Demo sequence (run once at start‑up)
    # -----------------------------------------------------------------------
    def demo_startup(self) -> None:
        """Simple demo: white pulse → rainbow sweep → ready flag."""
        # 1️⃣ White pulse
        for intensity in range(0, 256, 15):
            self._set_all_rgb(intensity, intensity, intensity)
            self._send_data()
            time.sleep(0.02)
        for intensity in range(255, -1, -15):
            self._set_all_rgb(intensity, intensity, intensity)
            self._send_data()
            time.sleep(0.02)

        # 2️⃣ Rainbow sweep (quick preview)
        for offset in range(0, 256, 16):
            for i, pixel in enumerate(self.led_color):
                c = self._wheel((i * 256 // self.count + offset) % 256)
                self._set_pixel(i, *c)
            self._send_data()
            time.sleep(0.01)

        # Reset to black before handing control to the main loop
        self._clear_strip()
        self.flag.set()  # ensure the main loop can start

    # -----------------------------------------------------------------------
    # Public run loop (called from `start()` after thread is alive)
    # -----------------------------------------------------------------------
    def run(self) -> None:
        """Main animation loop – blocks until `pause()` clears the flag."""
        while self.flag.is_set():
            self._rainbow_cycle(wait_ms=20)  # 20 ms ≈ 50 fps


# ---------------------------------------------------------------------------
# Helper to start a strip from the global config
# ---------------------------------------------------------------------------
def start_strip(cfg_dict: dict, demo: bool = False) -> SpiLedStrip:
    strip = SpiLedStrip(cfg_dict, demo=demo)
    if strip.led_init_state:
        strip.start()
    return strip


# ---------------------------------------------------------------------------
# Entry point – uses the hierarchical config from config.yaml
# ---------------------------------------------------------------------------
def main() -> None:
    cfg = load_config()

    # -----------------------------------------------------------------------
    # Extract logical groups
    # -----------------------------------------------------------------------
    body_cfg = cfg["leds"]["body"]
    onboard_cfg = cfg["leds"]["onboard"]

    # Create and start the *body* strip with the demo flag enabled.
    # The onboard strip is optional – we simply instantiate it but do not
    # start a separate animation thread (it can be used later for extra effects).
    body_strip = start_strip(body_cfg, demo=True)
    # onboard_strip = SpiLedStrip(onboard_cfg, demo=True)   # just for future use
    onboard_strip = start_strip(onboard_cfg, demo=True)

    # -----------------------------------------------------------------------
    # Optional: keep the script alive if the user wants manual control.
    # -----------------------------------------------------------------------
    try:
        while True:
            time.sleep(1)  # main thread just idles – animations run in background
    except KeyboardInterrupt:
        print("\nShutting down …")
        body_strip.pause()
        onboard_strip.pause()
        # Give the daemon threads a moment to finish cleanly
        time.sleep(0.5)


if __name__ == "__main__":
    main()
