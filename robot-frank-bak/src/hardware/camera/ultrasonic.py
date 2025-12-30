import RPi.GPIO as GPIO
import time


class UltrasonicSensor:
    def __init__(self, trigger_pin=23, echo_pin=24):
        # Initialize GPIO for ultrasonic sensor
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(trigger_pin, GPIO.OUT)
        GPIO.setup(echo_pin, GPIO.IN)

    def get_distance(self, timeout=0.04):
        """
        Get distance in cm using ultrasonic sensor.
        :return: Distance in cm (0-500cm)
        """
        # Send trigger pulse
        GPIO.output(self.trigger_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, False)

        # Measure echo time with timeout
        start = time.time()
        while GPIO.input(self.echo_pin) == 0:
            if time.time() - start > timeout:
                raise TimeoutError("Echo timeout")
            pass
        pulse_start = time.time()

        while GPIO.input(self.echo_pin) == 1:
            if time.time() - start > timeout:
                raise TimeoutError("Echo timeout")
            pass
        pulse_end = time.time()

        # Calculate distance
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150  # cm/s

        return min(distance, 500)  # Cap at 500cm

    def is_object_near(self, threshold=10):
        """
        Check if an object is near (within threshold distance).
        :param threshold: Distance threshold in cm.
        :return: True if object is near, False otherwise.
        """
        return self.get_distance() <= threshold

    def stop(self):
        """
        Cleanup GPIO resources.
        """
        GPIO.cleanup()

    def __del__(self):
        """
        Ensure GPIO cleanup on object deletion.
        """
        self.stop()
