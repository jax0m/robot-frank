"""
Example script that demonstrates how to use the ADEEPT Robot V3.1 HAT
drivers from other parts of the repository.

It showcases:
* Loading the LED strip driver and starting its animation in a background thread.
* Instantiating the servo driver and moving a few logical servos to positions.
"""

import threading
import time
from servos import move, get_driver
from leds import LedDriver

# ----------------------------------------------------------------------
# LED control -----------------------------------------------------------
# ----------------------------------------------------------------------
# Example configuration for the "body" LED group.
# In a real project this would normally be loaded from a YAML file,
# but for the sake of a self‑contained example we build the dict manually.
led_cfg = {
    "count": 30,  # number of LEDs in the strip
    "bus": 0,  # SPI bus number (default on the HAT)
    "device": 0,  # SPI device number (default on the HAT)
    "brightness": 0.8,  # global brightness (0.0 – 1.0)
}

# Create the driver – `demo=False` prevents the one‑shot start‑up animation
# when the script is executed from the command line (the demo is intended for
# interactive testing only).
body_led = LedDriver(led_cfg, demo=False)

# Run the animation in a daemon thread so the main thread can continue
anim_thread = threading.Thread(target=body_led.run, daemon=True)
anim_thread.start()

# ----------------------------------------------------------------------
# Servo control ---------------------------------------------------------
# ----------------------------------------------------------------------
# Move a couple of servos to illustrate the API.
# The names must match entries in `src/hardware/adeept_robot_v3-1/servos/config.yaml`.
# If you need more direct access to the underlying driver you can do:
driver = get_driver()  # returns the singleton ServoDriver instance
driver.home_all()
time.sleep(5)
move("elbow", -90)  # set the base joint to a 90° angle
time.sleep(0.5)
move("grip", 45)  # raise the left shoulder
time.sleep(0.5)


time.sleep(0.5)
driver.set_angle("wrist", 120)  # example of a raw call
time.sleep(5)
driver.home_all()


# ----------------------------------------------------------------------
# Keep the script alive for a short while so you can see the effects.
# ----------------------------------------------------------------------
try:
    print("LED animation and servo movements are now running...")
    print("Press Ctrl‑C to shut down.")
    time.sleep(10)  # let the demo run for 10 seconds
    body_led.pause()  # clear the LED strip
except KeyboardInterrupt:
    print("\nShutting down …")
    body_led.pause()  # clear the LED strip
    # The servo driver does not need explicit cleanup in this simple example.
