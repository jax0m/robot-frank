# ADEEPT Robot V3.1 HAT

**Brand / Version:** `ADEEPT Robot V3.1`
**Form factor:** Raspberry Pi 5 HAT that aggregates the following peripherals:

| Subsystem             | Example chip / driver                | Purpose                                                                     |
| :-------------------- | :----------------------------------- | :-------------------------------------------------------------------------- |
| **WS2812B LED strip** | `LedDriver` (wraps `rpi5_ws2812`)    | Visual feedback, status indicators, and programmable lighting effects.      |
| **Servo PWM channel** | PCA9685 16‑channel 12‑bit PWM driver | Controls up to 16 hobby servos for joints, grippers, or other moving parts. |
| **Future extensions** | ADC, Digital I/O, I²C sensors        | Add more sensors or actuators as the robot evolves.                         |

The folder layout under `src/hardware/adeept_robot_v3-1/` mirrors this logical separation:

```text
src/
 └─ hardware/
     └─ adeept_robot_v3-1/
         ├─ __init__.py          # top‑level re‑exports
         ├─ README.md              # <‑‑ this file
         ├─ config.yaml            # central config (LED groups, servo mappings)
         ├─ base.py                # common bus utilities (SPI/I²C/PWM base classes)
         ├─ leds/
         │   ├─ __init__.py
         │   ├─ ws2812.py           # existing WS2812 wrapper (already in repo)
         │   └─ config.yaml         # per‑LED‑group configuration
         └─ servos/
             ├─ __init__.py
             ├─ driver.py          # low‑level PWM driver wrapper
             └─ config.yaml        # per‑servo calibration / channel mapping
```

## Quick‑Start for New Projects

```python
# main.py (example)
from src.hardware.adeept_robot_v3-1 import LedDriver, ServoGroup

# ---- LED -------------------------------------------------
led_cfg = {
    "count": 30,
    "bus": 0,
    "device": 0,
    "brightness": 0.8,
}
led_driver = LedDriver(led_cfg, demo=False)

# start animation in background thread
import threading
threading.Thread(target=led_driver.run, daemon=True).start()

# ---- SERVO ---------------------------------------------
servo_group = ServoGroup()                # loads config automatically
servo_group.move_to("base_joint", 90)       # move a named servo to 90°
```

All component‑specific code lives in its own sub‑package (`leds/`, `servos/`), making it trivial to add new drivers (e.g., an ADC driver) later without touching existing code.

## Configuration Files

- **`config.yaml` (root)** – Global mapping of logical names to hardware resources.
- **`leds/config.yaml`** – Defines LED strip groups (`body`, `head`, …) and their SPI parameters.
- **`servos/config.yaml`** – Maps logical servo names to PWM channel numbers and calibration data (min/max pulse widths, default angles).

These files are loaded automatically by the drivers, so you can adjust pin‑outs, channel assignments, or pulse‑width limits without code changes.

---

_For detailed driver documentation, see the auto‑generated API reference in `docs/` or the docstrings inside each module._
