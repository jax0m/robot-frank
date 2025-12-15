import rpi_ws281x as ws2812
<<<<<<< HEAD
import math

=======
>>>>>>> 86ee538ad2c139a5522b7c643637e764bee9c5a1

class WS2812Controller:
    def __init__(self, num_leds=24, pin=12):
        # Initialize WS2812 LED strip
        self.num_leds = num_leds
        self.pin = pin
        self.strip = ws2812.PixelStrip(num_leds, pin=pin)
        self.strip.begin()
        self.strip.setBrightness(50)  # 50% brightness

    def set_color(self, led_id, r, g, b):
        """
        Set color of a specific LED
        :param led_id: ID of the LED (0-23)
        :param r: Red value (0-255)
        :param g: Green value (0-255)
        :param b: Blue value (0-255)
        """
        if 0 <= led_id < self.num_leds:
            self.strip.setPixelColor(led_id, r, g, b)
            self.strip.show()

    def set_all_colors(self, r, g, b):
        """
        Set all LEDs to the same color
        :param r: Red value (0-255)
        :param g: Green value (0-255)
        :param b: Blue value (0-255)
        """
        for i in range(self.num_leds):
            self.set_color(i, r, g, b)

    def show(self):
        """
        Update the LEDs with the current colors
        """
        self.strip.show()

    def rainbow_animation(self, delay=100):
        """
        Create a rainbow animation across the LEDs
        :param delay: Delay between steps (in milliseconds)
        """
        for i in range(self.num_leds):
            # Calculate color based on position
            r = int(128 * (1 + math.sin(i * 0.1)))
            g = int(128 * (1 + math.cos(i * 0.1)))
            b = int(128 * (1 + math.sin(i * 0.2)))
            self.set_color(i, r, g, b)
        self.show()

    def clear(self):
        """
        Turn off all LEDs
        """
        for i in range(self.num_leds):
            self.set_color(i, 0, 0, 0)
<<<<<<< HEAD
        self.show()
=======
        self.show()
>>>>>>> 86ee538ad2c139a5522b7c643637e764bee9c5a1
