import websockets
import json
import threading
import time


class WebSocketClient:
    def __init__(self):
        self.uri = "ws://localhost:8765"
        self.running = False
        self.client_thread = None
        self.websocket = None

        # Control mappings (action -> method name)
        self.control_functions = {
            "arm_up": self._arm_up,
            "arm_down": self._arm_down,
            "wrist_up": self._wrist_up,
            "wrist_down": self._wrist_down,
            "grip_open": self._grip_open,
            "grip_close": self._grip_close,
            "tilt_up": self._tilt_up,
            "tilt_down": self._tilt_down,
            "forward": self._forward,
            "backward": self._backward,
            "turn_left": self._turn_left,
            "turn_right": self._turn_right,
            "rainbow": self._rainbow,
            "clear": self._clear,
        }

        # Event handlers for each action
        self.control_event_handlers = {
            "arm_up": self._on_arm_up,
            "arm_down": self._on_arm_down,
            "wrist_up": self._on_wrist_up,
            "wrist_down": self._on_wrist_down,
            "grip_open": self._on_grip_open,
            "grip_close": self._on_grip_close,
            "tilt_up": self._on_tilt_up,
            "tilt_down": self._on_tilt_down,
            "forward": self._on_forward,
            "backward": self._on_backward,
            "turn_left": self._on_turn_left,
            "turn_right": self._on_turn_right,
            "rainbow": self._on_rainbow,
            "clear": self._on_clear,
        }

        # Status tracking
        self.control_status = {
            "arm_up": False,
            "arm_down": False,
            "wrist_up": False,
            "wrist_down": False,
            "grip_open": False,
            "grip_close": False,
            "tilt_up": False,
            "tilt_down": False,
            "forward": False,
            "backward": False,
            "turn_left": False,
            "turn_right": False,
            "rainbow": False,
            "clear": False,
        }

        self.control_history = []

    def start(self):
        """Start the WebSocket client"""
        if not self.running:
            self.running = True
            self.client_thread = threading.Thread(target=self._run_client, daemon=True)
            self.client_thread.start()
            print("WebSocket client started")
        else:
            print("WebSocket client is already running")

    def stop(self):
        """Stop the WebSocket client"""
        if self.running:
            self.running = False
            if self.client_thread:
                self.client_thread.join()
            print("WebSocket client stopped")

    def _run_client(self):
        """Internal method to run the WebSocket client"""
        while self.running:
            try:
                # Connect to the WebSocket server
                self.websocket = websockets.connect(self.uri)

                # Send a handshake message
                self.websocket.send(
                    json.dumps({"action": "handshake", "timestamp": time.time()})
                )

                # Listen for incoming messages
                while self.running:
                    # Receive message from server
                    message = self.websocket.recv()

                    # Parse JSON message
                    try:
                        data = json.loads(message)

                        # Process control message
                        if "action" in data:
                            action = data["action"]
                            if action in self.control_functions:
                                # Call the appropriate control function
                                self.control_functions[action]()

                                # Update status
                                self.control_status[action] = True

                                # Add to history
                                self.control_history.append(
                                    {
                                        "action": action,
                                        "timestamp": time.time(),
                                    }
                                )

                                # Invoke event handler if defined
                                if action in self.control_event_handlers:
                                    self.control_event_handlers[action]()

                    except json.JSONDecodeError:
                        print("Invalid JSON message received")

                    except Exception as e:
                        print(f"Error processing message: {e}")

                    # Brief pause
                    time.sleep(0.1)

            except Exception as e:
                print(f"Error connecting to server: {e}")

                # Wait before reconnecting
                time.sleep(5)

            finally:
                # Close connection cleanly
                if self.websocket:
                    self.websocket.close()
                # Wait before next attempt
                time.sleep(1)

    def get_status(self):
        """Get the current status of the WebSocket client"""
        return {
            "running": self.running,
            "uri": self.uri,
            "status": "connected" if self.websocket else "disconnected",
            "control_status": self.control_status,
        }
