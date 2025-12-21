# WS2812 LED Strip Driver

A small, self‑contained Python library that wraps the `rpi5_ws2812` hardware driver
and provides a convenient, Pythonic API for controlling WS2812B LED strips on a
Raspberry Pi 5.
The driver is deliberately written to mirror the behaviour of an existing
bare‑bones script (`ws2812.py`) while adding a clean public interface,
configuration handling, and a non‑blocking animation loop.

---

## 📦 Installation / Prerequisites

1. **Hardware** – Raspberry Pi 5 with a WS2812B (NeoPixel) strip connected to the
   dedicated SPI bus (default: `spi0` bus 0, device 0).
2. **Python** – 3.13.5+ (tested).
3. **Dependencies** – `rpi5_ws2812`, `pyyaml`, and `threading` (standard library).
   Install with:

   ```bash
   pip install rpi5_ws2812 pyyaml
   ```

4. **Add the package to your project** – Clone or copy the `src/hardware/leds`
   directory into your repository’s source tree.

---

## 📂 Directory Layout

```text
src/
 └─ hardware/
     └─ leds/
         ├─ ws2812.py      # Core implementation (the file you are reading now)
         └─ README.md      # <‑‑ this file
```

---

## 🚀 Quick Start

### 1. Load a configuration

A YAML file (`config.yaml`) lives one level above the `leds` directory and
describes each logical LED group. A minimal example:

```yaml
leds:
  body:
    count: 30 # Number of LEDs in the strip
    bus: 0 # SPI bus number
    device: 0 # SPI device number
    brightness: 0.5 # Float 0.0‑1.0
  # Additional groups can be added here (e.g. "head", "tail", ...)
```

Load it in your script:

```python
from pathlib import Path
import yaml

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"
with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)

body_cfg = cfg["leds"]["body"]          # <-- configuration for the "body" strip
```

### 2. Create a driver instance

```python
from src.hardware.leds.ws2812 import LedDriver

# demo=False prevents the one‑shot start‑up animation from running when the
# script is launched from the command line (it is only meant for interactive
# testing).
driver = LedDriver(body_cfg, demo=False)
```

### 3. Run the animation in a background thread

The `run()` method blocks indefinitely, so it should be executed in a daemon
thread:

```python
import threading

anim_thread = threading.Thread(target=driver.run, daemon=True)
anim_thread.start()
```

### 4. Control the strip

| Method                        | Description                                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `driver.pause()`              | Clears the strip and stops animation (e.g. on user request).                                                                   |
| `driver.resume()`             | No‑op kept for API compatibility; animation continues running.                                                                 |
| `driver.demo_startup()`       | Runs a short start‑up sequence (white pulse → rainbow sweep → black). Called automatically if `demo=True` during construction. |
| `driver.set_all_rgb(r, g, b)` | Helper that sets every pixel to a solid colour (internal use).                                                                 |
| `driver.run()`                | Main infinite animation loop that cycles through the rainbow wheel.                                                            |

**Example – pause after 5 seconds:**

```python
import time

time.sleep(5)
driver.pause()          # clear LEDs
```

### 5. Graceful shutdown

When your application exits (e.g. on `KeyboardInterrupt`), invoke `driver.pause()`
to clear the LEDs. If you used a daemon thread, the interpreter will exit
automatically once the main thread ends.

---

## 🛠️ Public API Overview

```python
class LedDriver:
    __init__(self, cfg: dict, demo: bool = False)
    pause() -> None
    resume() -> None
    run() -> None                 # blocking; typically executed in a thread
    demo_startup() -> None        # one‑shot start‑up animation
    _set_all_rgb(driver, r, g, b) # static helper (internal)
    _clear_strip(driver)          # static helper (internal)
```

All parameters are validated when the driver is instantiated; missing keys in
`cfg` will raise a `KeyError`. The `demo` flag is purely for convenience when
testing the driver interactively.

---

## 📚 Configuration Details

| Key          | Type    | Description                             |
| ------------ | ------- | --------------------------------------- |
| `count`      | `int`   | Number of LEDs in the strip.            |
| `bus`        | `int`   | SPI bus number (usually `0`).           |
| `device`     | `int`   | SPI device number (usually `0`).        |
| `brightness` | `float` | Global brightness multiplier (0.0‑1.0). |

The driver always creates the underlying `WS2812SpiDriver` on `spi_bus=self._bus`,
`spi_device=self._device`, and passes `led_count=self._count`.

---

## 🎨 Example Use‑Case in a Larger Application

```python
# src/app/main.py
import time
import threading
from src.hardware.leds.ws2812 import LedDriver

# Load global config (shared by multiple modules)
from pathlib import Path
import yaml

CONFIG_PATH = Path(__file__).resolve().parents[2] / "hardware" / "leds" / "config.yaml"
cfg = yaml.safe_load(open(CONFIG_PATH))

# Create drivers for each logical group
body_driver = LedDriver(cfg["leds"]["body"], demo=False)
head_driver = LedDriver(cfg["leds"]["head"], demo=False)

# Start animations in separate daemon threads
for driver in (body_driver, head_driver):
    threading.Thread(target=driver.run, daemon=True).start()

# Keep the main thread alive and react to external events
try:
    while True:
        # ... other app logic (e.g., sensor reading, network messages) ...
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...")
    body_driver.pause()
    head_driver.pause()
```

In the example above:

- The configuration file lives at the repository root (`config.yaml`), making it
  easy for any module to locate and load.
- Each LED group can be driven independently, enabling complex lighting
  patterns across the robot’s various body parts.
- All animation runs in background daemon threads, allowing the main program to
  stay responsive to user input, sensor data, or network commands.

---

## 📜 License

This driver is provided under the MIT License – see the `LICENSE` file for
details.

---

## 🙋‍♂️ FAQ

**Q: Can I change the brightness at runtime?**
A: The driver exposes the brightness value via `self._brightness`. To adjust it,
store the driver instance in a mutable container (e.g., a dict) and modify that
value before the next call to `run()`'s loop. The `run()` method reads the
current brightness each iteration.

**Q: Is the animation thread‑safe?**
A: Yes. The `run()` method only accesses its own internal state and the
underlying `Strip` object. Because it runs in a daemon thread, you must ensure
that `pause()` or any other method is not called concurrently from another
thread. If you need concurrent control, protect calls with a `threading.Lock`.

**Q: How do I add a new LED group?**
A: Add an entry under `leds` in `config.yaml` with the required keys (`count`,
`bus`, `device`, `brightness`). Then instantiate a new `LedDriver` with that
sub‑dictionary and start its animation in its own thread.

---

_Happy lighting!_ 🎉
