import cv2
import time
from picamera2 import Picamera2


class CameraController:
    def __init__(self, resolution=(640, 480), framerate=30):
        # Initialize camera with specific parameters
        self.resolution = resolution
        self.framerate = framerate
        self.camera = Picamera2()

        # Configure camera settings
        self.camera.configure(self.camera.create_still_configuration())
        self.camera.set_controls(
            {
                "Sharpness": 1.0,
                "Contrast": 1.0,
                "Brightness": 0.5,
                "Saturation": 1.0,
                "ExposureTime": 50000,
                "FrameRate": framerate,
            }
        )

        self.camera.start()

        # Camera properties
        self.width = self.resolution[0]
        self.height = self.resolution[1]

        # OpenCV settings
        self.cv_settings = {
            "cv2.CAP_PROP_FRAME_WIDTH": self.width,
            "cv2.CAP_PROP_FRAME_HEIGHT": self.height,
            "cv2.CAP_PROP_FPS": self.framerate,
            "cv2.CAP_PROP_BRIGHTNESS": 0.5,
            "cv2.CAP_PROP_CONTRAST": 1.0,
            "cv2.CAP_PROP_SATURATION": 1.0,
            "cv2.CAP_PROP_SHARPNESS": 1.0,
            "cv2.CAP_PROP_EXPOSURE": 50000,
        }

    def get_frame(self):
        """
        Get a single frame from the camera
        :return: OpenCV frame (numpy array)
        """
        # Capture frame from camera
        frame = self.camera.capture_array()

        # Convert to BGR format (OpenCV uses BGR, not RGB)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        return frame

    def get_frame_with_processing(self, processing=None):
        """
        Get a frame with optional processing
        :param processing: Processing function (e.g., edge detection, object detection)
        :return: Processed frame (numpy array)
        """
        # Get raw frame
        frame = self.get_frame()

        # Apply processing if provided
        if processing is not None:
            frame = processing(frame)

        return frame

    def get_camera_info(self):
        """
        Get camera information
        :return: Dictionary with camera parameters
        """
        return {
            "resolution": self.resolution,
            "framerate": self.framerate,
            "width": self.width,
            "height": self.height,
            "frame_rate": self.framerate,
            "exposure_time": 50000,
            "sharpness": 1.0,
            "contrast": 1.0,
            "brightness": 0.5,
            "saturation": 1.0,
        }

    def start_stream(self, callback=None):
        """
        Start camera stream with callback
        :param callback: Function to call for each frame
        """
        # Start camera stream
        self.camera.start()

        # Process frames in a loop
        while True:
            # Get frame
            frame = self.get_frame()

            # Call callback if provided
            if callback is not None:
                callback(frame)

            # Sleep briefly to avoid overwhelming the system
            time.sleep(1.0 / self.framerate)

            # Check if we should stop
            if self.stop_stream:
                break

    def stop_stream(self):
        """
        Stop the camera stream
        """
        self.camera.stop()

    def release(self):
        """
        Release camera resources
        """
        self.camera.close()

        # Cleanup GPIO (if applicable)
        # GPIO.cleanup()
