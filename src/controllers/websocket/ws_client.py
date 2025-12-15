import asyncio
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
        
        # Initialize all hardware components
        # These will be initialized when the client starts
        
        # Define control mappings
        self.control_mappings = {
            'arm': {
                'up': 'arm_up',
                'down': 'arm_down',
                'wrist_up': 'wrist_up',
                'wrist_down': 'wrist_down',
                'grip_open': 'grip_open',
                'grip_close': 'grip_close'
            },
            'camera': {
                'tilt_up': 'tilt_up',
                'tilt_down': 'tilt_down'
            },
            'motors': {
                'forward': 'forward',
                'backward': 'backward',
                'turn_left': 'turn_left',
                'turn_right': 'turn_right'
            },
            'leds': {
                'rainbow': 'rainbow',
                'clear': 'clear'
            }
        }
        
        # Define control parameters
        self.control_parameters = {
            'arm': {
                'speed': 100,
                'position': 90
            },
            'camera': {
                'angle': 90
            },
            'motors': {
                'speed': 100,
                'direction': 'forward'
            },
            'leds': {
                'brightness': 50
            }
        }
        
        # Define control functions
        self.control_functions = {
            'arm_up': self._arm_up,
            'arm_down': self._arm_down,
            'wrist_up': self._wrist_up,
            'wrist_down': self._wrist_down,
            'grip_open': self._grip_open,
            'grip_close': self._grip_close,
            'tilt_up': self._tilt_up,
            'tilt_down': self._tilt_down,
            'forward': self._forward,
            'backward': self._backward,
            'turn_left': self._turn_left,
            'turn_right': self._turn_right,
            'rainbow': self._rainbow,
            'clear': self._clear
        }
        
        # Define control status
        self.control_status = {
            'arm': {
                'up': False,
                'down': False,
                'wrist_up': False,
                'wrist_down': False,
                'grip_open': False,
                'grip_close': False
            },
            'camera': {
                'tilt_up': False,
                'tilt_down': False
            },
            'motors': {
                'forward': False,
                'backward': False,
                'turn_left': False,
                'turn_right': False
            },
            'leds': {
                'rainbow': False,
                'clear': False
            }
        }
        
        # Define control history
        self.control_history = []
        
        # Define control event handlers
        self.event_handlers = {
            'arm': {
                'up': self._on_arm_up,
                'down': self._on_arm_down,
                'wrist_up': self._on_wrist_up,
                'wrist_down': self._on_wrist_down,
                'grip_open': self._on_grip_open,
                'grip_close': self._on_grip_close
            },
            'camera': {
                'tilt_up': self._on_tilt_up,
                'tilt_down': self._on_tilt_down
            },
            'motors': {
                'forward': self._on_forward,
                'backward': self._on_backward,
                'turn_left': self._on_turn_left,
                'turn_right': self._on_turn_right
            },
            'leds': {
                'rainbow': self._on_rainbow,
                'clear': self._on_clear
            }
        }
        
        # Define control event handlers
        self.control_event_handlers = {
            'arm': {
                'up': self._on_arm_up,
                'down': self._on_arm_down,
                'wrist_up': self._on_wrist_up,
                'wrist_down': self._on_wrist_down,
                'grip_open': self._on_grip_open,
                'grip_close': self._on_grip_close
            },
            'camera': {
                'tilt_up': self._on_tilt_up,
                'tilt_down': self._on_tilt_down
            },
            'motors': {
                'forward': self._on_forward,
                'backward': self._on_backward,
                'turn_left': self._on_turn_left,
                'turn_right': self._on_turn_right
            },
            'leds': {
                'rainbow': self._on_rainbow,
                'clear': self._on_clear
            }
        }
        
        # Define control event handlers
        self.control_event_handlers = {
            'arm': {
                'up': self._on_arm_up,
                'down': self._on_arm_down,
                'wrist_up': self._on_wrist_up,
                'wrist_down': self._on_wrist_down,
                'grip_open': self._on_grip_open,
                'grip_close': self._on_grip_close
            },
            'camera': {
                'tilt_up': self._on_tilt_up,
                'tilt_down': self._on_tilt_down
            },
            'motors': {
                'forward': self._on_forward,
                'backward': self._on_backward,
                'turn_left': self._on_turn_left,
                'turn_right': self._on_turn_right
            },
            'leds': {
                'rainbow': self._on_rainbow,
                'clear': self._on_clear
            }
        }
        
        # Define control event handlers
        self.control_event_handlers = {
            'arm': {
                'up': self._on_arm_up,
                'down': self._on_arm_down,
                'wrist_up': self._on_wrist_up,
                'wrist_down': self._on_wrist_down,
                'grip_open': self._on_grip_open,
                'grip_close': self._on_grip_close
            },
            'camera': {
                'tilt_up': self._on_tilt_up,
                'tilt_down': self._on_tilt_down
            },
            'motors': {
                'forward': self._on_forward,
                'backward': self._on_backward,
                'turn_left': self._on_turn_left,
                'turn_right': self._on_turn_right
            },
            'leds': {
                'rainbow': self._on_rainbow,
                'clear': self._on_clear
            }
        }
        
        # Define control event handlers
        self.control_event_handlers = {
            'arm': {
                'up': self._on_arm_up,
                'down': self._on_arm_down,
                'wrist_up': self._on_wrist_up,
                'wrist_down': self._on_wrist_down,
                'grip_open': self._on_grip_open,
                'grip_close': self._on_grip_close
            },
            'camera': {
                'tilt_up': self._on_tilt_up,
                'tilt_down': self._on_tilt_down
            },
            'motors': {
                'forward': self._on_forward,
                'backward': self._on_backward,
                'turn_left': self._on_turn_left,
                'turn_right': self._on_turn_right
            },
            'leds': {
                'rainbow': self._on_rainbow,
                'clear': self._on_clear
            }
        }

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
                self.websocket.send(json.dumps({
                    'action': 'handshake',
                    'timestamp': time.time()
                }))
                
                # Listen for incoming messages
                while self.running:
                    # Receive message from server
                    message = self.websocket.recv()
                    
                    # Parse JSON message
                    try:
                        data = json.loads(message)
                        
                        # Process control message
                        if 'control' in data:
                            control = data['control']
                            
                            # Check if control is valid
                            if control in self.control_mappings:
                                # Get control function
                                control_function = self.control_mappings[control]
                                
                                # Check if control function is valid
                                if control_function in self.control_functions:
                                    # Call control function
                                    self.control_functions[control_function]()
                                    
                                    # Update control status
                                    self.control_status[control][control_function] = True
                                    
                                    # Add to control history
                                    self.control_history.append({
                                        'control': control,
                                        'function': control_function,
                                        'timestamp': time.time()
                                    })
                                    
                                    # Call control event handlers
                                    if control_function in self.control_event_handlers:
                                        self.control_event_handlers[control_function]()
                        
                        # Check if control is valid
                        if 'control' in data:
                            control = data['control']
                            
                            # Check if control is valid
                            if control in self.control_mappings:
                                # Get control function
                                control_function = self.control_mappings[control]
                                
                                # Check if control function is valid
                                if control_function in self.control_functions:
                                    # Call control function
                                    self.control_functions[control_function]()
                                    
                                    # Update control status
                                    self.control_status[control][control_function] = True
                                    
                                    # Add to control history
                                    self.control_history.append({
                                        'control': control,
                                        'function': control_function,
                                        'timestamp': time.time()
                                    })
                                    
                                    # Call control event handlers
                                    if control_function in self.control_event_handlers:
                                        self.control_event_handlers[control_function]()
                    
                    except json.JSONDecodeError:
                        print("Invalid JSON message received")
                    
                    except Exception as e:
                        print(f"Error processing message: {e}")
                    
                    # Wait briefly
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Error connecting to server: {e}")
                
                # Wait briefly before reconnecting
                time.sleep(5)
                
            finally:
                # Close connection
                if self.websocket:
                    self.websocket.close()
                    
                # Wait briefly before reconnecting
                time.sleep(1)

    def get_status(self):
        """Get the current status of the WebSocket client"""
        return {
            'running': self.running,
            'uri': self.uri,
            'status': 'connected' if self.websocket else 'disconnected',
            'control_status': self.control_status
        }