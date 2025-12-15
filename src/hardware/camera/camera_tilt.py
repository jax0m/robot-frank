import RPi.GPIO as GPIO

class CameraTiltController:
    def __init__(self, tilt_pin=18):
        # Initialize GPIO for camera tilt servo
        self.tilt_pin = tilt_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(tilt_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(tilt_pin, 50)  # 50Hz PWM
        self.pwm.start(0)  # Start with 0% duty cycle (90 degrees)

    def set_angle(self, angle):
        """
        Set camera tilt angle (0-180 degrees)
        :param angle: Angle to set (0-180 degrees)
        """
        # Convert angle to PWM duty cycle
        # 0 degrees = 2.5% duty cycle, 180 degrees = 12.5% duty cycle
        duty_cycle = 2.5 + (angle / 180) * 10
        self.pwm.ChangeDutyCycle(duty_cycle)
        
    def get_angle(self):
        """
        Get current camera tilt angle
        :return: Current angle (0-180 degrees)
        """
        # In a real implementation, you'd read the actual angle
        # For now, we'll just return a placeholder
        return 90

    def stop(self):
        """
        Stop the camera tilt servo
        """
        self.pwm.stop()
        GPIO.cleanup()