import cv2
import time
from picamera2 import Picamera2


class CameraController:
    def __init__(self, resolution=(640, 480), framerate=30):
        # Store configuration
        self.resolution = resolution
        self.framerate = framerate
        self.stop_stream = False  # Flag to control streaming loop

        # Configure and start the camera
        self.camera = Picamera2()
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
        self.width, self.height = self.resolution

    def get_frame(self):
        """Return a single frame from the camera as a BGR numpy array."""
        frame = self.camera.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame

    def get_frame_with_processing(self, processing=None):
        """Return a frame optionally processed by the given function."""
        frame = self.get_frame()
        if processing is not None:
            frame = processing(frame)
        return frame

    def get_camera_info(self):
        """Return a dictionary with current camera parameters."""
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
        """Capture frames continuously until stop_stream is set to True."""
        while not self.stop_stream:
            frame = self.get_frame()
            if callback is not None:
                callback(frame)
            time.sleep(1.0 / self.framerate)

    def stop_stream(self):
        """Signal the streaming loop to stop."""
        self.stop_stream = True
        self.camera.stop()

    def release(self):
        """Release camera resources."""
        self.camera.close()
        # GPIO.cleanup()
