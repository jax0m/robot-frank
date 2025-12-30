import time
import threading
import yaml
from pathlib import Path
from rpi5_ws2812.ws2812 import Color, WS2812SpiDriver, Strip


# ---------------------------------------------------------------------------
# Helper: classic WS2812 colour wheel (mirrors original behaviour)
# ---------------------------------------------------------------------------
def _wheel(pos: int) -> Color:
    """
    Convert a position on the 256‑step rainbow into an RGB ``Color``.

    Parameters
    ----------
    pos : int
        Position in the wheel (0‑255).

    Returns
    -------
    Color
        An RGB colour object representing the wheel position.
    """
    if pos < 85:
        return Color(255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return Color(0, 255 - pos * 3, pos * 3)
    pos -= 170
    return Color(pos * 3, 0, 255 - pos * 3)


# ---------------------------------------------------------------------------
# Core driver wrapper
# ---------------------------------------------------------------------------
class LedDriver:
    """
    Wrapper that mirrors the original script’s public API for controlling a
    WS2812 LED strip.

    Public methods
    ---------------
    * ``pause()`` – clears the strip and stops any animation.
    * ``resume()`` – no‑op kept for API compatibility (animation runs
      continuously).
    * ``run()`` – infinite rainbow animation that updates the strip in real‑time.
    * ``demo_startup()`` – one‑shot start‑up sequence executed once during
      object creation when ``demo=True``.
    """

    def __init__(self, cfg: dict, demo: bool = False):
        """
        Initialise the driver.

        Parameters
        ----------
        cfg : dict
            Must contain the keys ``count`` (LED count), ``bus`` (SPI bus),
            ``device`` (SPI device), and ``brightness`` (float 0.0‑1.0).
        demo : bool, optional
            If ``True`` the start‑up demo runs once after construction.
        """
        self._count = cfg["count"]
        self._bus = cfg["bus"]
        self._device = cfg["device"]
        self._brightness = cfg["brightness"]  # 0.0 – 1.0
        # The concrete driver is always instantiated on bus 0, device 0.
        backend = WS2812SpiDriver(
            spi_bus=self._bus, spi_device=self._device, led_count=self._count
        )
        self._strip = Strip(backend)

        if demo:
            self.demo_startup()

    # -----------------------------------------------------------------------
    # Public control helpers (mirroring the original API)
    # -----------------------------------------------------------------------
    def pause(self) -> None:
        """
        Stop all animation and clear the strip.

        This method is used by the main loop when the user requests a pause,
        e.g. via a keyboard interrupt handler.
        """
        self._strip.clear()

    def resume(self) -> None:
        """
        Resume animation.

        In the original implementation the animation never truly stops, so
        this method is a placeholder kept only for API compatibility.
        """
        pass

    # -----------------------------------------------------------------------
    # Animation primitives
    # -----------------------------------------------------------------------
    @staticmethod
    def _clear_strip(driver) -> None:
        """
        Helper that clears the underlying strip.

        Parameters
        ----------
        driver : Strip
            The strip instance to clear.
        """
        driver.clear()

    def _set_all_rgb(self, driver, r: int, g: int, b: int) -> None:
        """
        Set every pixel on the strip to a solid colour and push the update.

        Parameters
        ----------
        driver : Strip
            The strip instance to modify.
        r, g, b : int
            Red, green, and blue intensities (0‑255).
        """
        driver.set_all_pixels(Color(r, g, b))

    def demo_startup(self) -> None:
        """
        Run a short start‑up demo that mimics the original behaviour:

        1. White pulse – brightness ramps up and down.
        2. Quick rainbow sweep – a brief colourful sweep across the strip.
        3. End on black to leave the strip ready for continuous animation.

        This method is invoked once during ``LedDriver`` construction when
        ``demo=True``.
        """
        # 1️⃣ White pulse (brightness sweep)
        for intensity in range(0, 256, 15):
            self._set_all_rgb(self._strip, intensity, intensity, intensity)
            time.sleep(0.02)
        for intensity in range(255, -1, -15):
            self._set_all_rgb(self._strip, intensity, intensity, intensity)
            time.sleep(0.02)

        # 2️⃣ Quick rainbow sweep (reduced steps to keep it short)
        for offset in range(0, 256, 16):
            for i in range(self._count):
                c = _wheel((i * 256 // self._count + offset) % 256)
                self._strip.set_pixel_color(i, c)
            self._strip.show()
            time.sleep(0.01)

        # Ensure the strip is black and ready for continuous animation
        self._strip.clear()

    # -----------------------------------------------------------------------
    # Main animation loop (runs forever until ``pause()`` clears it)
    # -----------------------------------------------------------------------
    def run(self) -> None:
        """
        Continuously cycle through the rainbow colour wheel.

        This method is intended to be executed in a background thread
        (``daemon=True``) so that the main thread can remain responsive.
        It repeatedly updates every pixel with the next colour in the wheel
        and respects the configured brightness.
        """
        while True:
            for start in range(256):
                for i in range(self._count):
                    col = _wheel((i * 256 // self._count + start) % 256)
                    self._strip.set_pixel_color(i, col)
                self._strip.set_brightness(self._brightness)
                self._strip.show()
                time.sleep(0.01)  # ~50 fps


# ---------------------------------------------------------------------------
# Configuration handling (kept for backward‑compatibility)
# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).resolve().parents[0] / "config.yaml"


def load_config() -> dict:
    """
    Load the YAML configuration file that defines LED groups.

    Returns
    -------
    dict
        The parsed configuration dictionary; only the ``leds`` section is
        consumed by the caller.
    """
    with open(CONFIG_PATH) as f:
        print("Config was opened successfully")
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Entry point – creates drivers for the two logical groups defined in YAML
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Program entry point.

    Loads the configuration, creates a driver for the ``body`` LED group,
    starts its animation in a daemon thread, and blocks until the user
    interrupts the program (Ctrl‑C). On interrupt the strip is cleared and
    the program exits gracefully.
    """
    cfg = load_config()

    # Extract the per‑group configuration (still expects ``count`` etc.).
    body_cfg = cfg["leds"]["body"]

    # Create drivers – demo is disabled to avoid duplicate start‑up sequence
    # when the script is launched from the command line.
    body_driver = LedDriver(
        body_cfg, demo=False
    )  # runs demo internally if ``demo=True``

    # -------------------------------------------------------------------
    # Start continuous animation in a background thread (daemon)
    # -------------------------------------------------------------------
    anim_thread = threading.Thread(target=body_driver.run, daemon=True)
    anim_thread.start()

    # Keep the main thread alive until the user hits Ctrl‑C.
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nShutting down …")
        body_driver.pause()
        # Give the daemon thread a moment to finish cleanly.
        # anim_thread.join()


if __name__ == "__main__":
    main()
