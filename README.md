# robot-frank

`robot because its a robot, frank because its a tank`

A modular, extensible control system for Raspberry Pi-powered robots with hardware-abstracted components, web interfaces, and automation capabilities.

Initially developed for the [Adeept/RaspTank2 Metal](https://www.adeept.com/rasptank-metal_p0436.html)

## Features

- ✨ **Multi-Interface Control**: Web UI (Flask) and WebSocket Python UI
- 🤖 **4-Servo Arm Control**: Up/down, wrist rotation, grip
- 📷 **Camera & Sensor System**: Tilt servo + ultrasonic distance sensor
- 🚶 **Tank Tread Movement**: 2-motor control for forward/backward and rotation
- 🌈 **WS2812 LED Strip**: Programmable lighting
- 🤖 **Automation API**: Scriptable control for external systems
- 🧩 **Modular Design**: Easy to add new components without breaking existing code

## Hardware Components

| Component             | Description                                           |
| --------------------- | ----------------------------------------------------- |
| **4-Servo Arm**       | Controls arm movement (up/down, wrist rotation, grip) |
| **Camera Tilt**       | Servo-controlled camera angle (0-180°)                |
| **Ultrasonic Sensor** | Distance measurement (0-500cm)                        |
| **Tank Motors**       | 2 independent motors for tank tread movement          |
| **WS2812 LEDs**       | Addressable RGB LED strip (24+ pixels)                |

## Project Structure

```text
/robot-pi
├── /src
│   ├── /hardware        # Hardware-specific drivers (pin-abstracted)
│   │   ├── /arm         # 4-servo arm control
│   │   ├── /camera      # Tilt servo, ultrasonic sensor, camera handler
│   │   ├── /motors      # Tank treads
│   │   └── /leds        # WS2812 LED strip
│   │
│   ├── /controllers     # User interfaces
│   │   ├── /web         # Web UI (Flask server)
│   │   └── /websocket   # Python WebSocket UI
│   │
│   ├── /automation      # Scriptable automation
│   │   ├── default_automation.py  # Pre-built scripts
│   │   └── api_endpoints.py       # Exposed API
│   │
│   ├── /config          # GPIO pin mappings
│   │   └── pins.py      # Configurable pin assignments
│   │
│   └── main.py          # Entry point
│
├── /docs                # Documentation
├── /tests               # Unit/integration tests
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Getting Started

1. **Install Dependencies**:

   ```bash
   python3 -m venv --system-site-packages .venv # since we are pulling in some raspberry pi apt packages
   pip install -r requirements.txt
   ```

2. **Configure GPIO Pins**:
   - Edit `/src/config/pins.py` to match your physical wiring

3. **Run the Web Interface**:

   ```bash
   python src/main.py  # Starts the Flask server
   ```
