class ArmServoController:
    """Controller for managing four ARM servos via GPIO."""
    def __init__(self) -> None:
        """Initialize GPIO pins for the 4 servos."""
        pass

    def set_position(self, servo_id: int, position: int) -> None:
        """
        Set servo position (0-180 degrees).

        :param servo_id: ID of the servo (1-4)
        :param position: Position (0-180)
        """
        if not 1 <= servo_id <= 4:
            raise ValueError("servo_id must be between 1 and 4")
        if not 0 <= position <= 180:
            raise ValueError("position must be between 0 and 180")
        # TODO: Add actual GPIO control code here
        pass

    def get_position(self, servo_id: int) -> int:
        """
        Get current position of a servo.

        :param servo_id: ID of the servo (1-4)
        :return: Current position (0-180)
        """
        if not 1 <= servo_id <= 4:
            raise ValueError("servo_id must be between 1 and 4")
        # TODO: Add actual position reading code here
        return 0