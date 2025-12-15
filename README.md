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

## Roadmap

### Phase 1: Core System Setup

**Objective**: Establish the foundational structure for the robot system.

| Task | Description                               | Tools                    |
| ---- | ----------------------------------------- | ------------------------ |
| 1.1  | **Set up the repository structure**       | Git, GitHub              |
| 1.2  | **Create the main `main.py` entry point** | Python                   |
| 1.3  | **Implement hardware abstraction layer**  | Python, GPIO             |
| 1.4  | **Add configuration system**              | Python, `config/pins.py` |
| 1.5  | **Set up error handling and logging**     | Python, `robot.log`      |

### Phase 2: Hardware Control Implementation

**Objective**: Develop drivers for all physical components.

| Task | Description                        | Tools                               |
| ---- | ---------------------------------- | ----------------------------------- |
| 2.1  | **Implement arm control**          | `arm_controller.py`, `arm_servo.py` |
| 2.2  | **Develop camera tilt control**    | `camera_tilt.py`                    |
| 2.3  | **Create ultrasonic sensor logic** | `ultrasonic.py`                     |
| 2.4  | **Build tank motor control**       | `tank_motors.py`                    |
| 2.5  | **Implement WS2812 LED animation** | `ws2812.py`                         |

### Phase 3: User Interface Development

**Objective**: Create interfaces for manual control.

| Task | Description                    | Tools                                                                 |
| ---- | ------------------------------ | --------------------------------------------------------------------- |
| 3.1  | **Develop web UI**             | Flask, HTML templates                                                 |
| 3.2  | **Implement WebSocket client** | `ws_client.py`                                                        |
| 3.3  | **Create control interfaces**  | `controllers/web/web_server.py`, `controllers/websocket/ws_client.py` |

### Phase 4: Automation Scripting

**Objective**: Enable script-based control and automation.

| Task | Description                           | Tools                              |
| ---- | ------------------------------------- | ---------------------------------- |
| 4.1  | **Build automation API**              | `automation/api_endpoints.py`      |
| 4.2  | **Create default automation scripts** | `automation/default_automation.py` |
| 4.3  | **Implement scriptable control**      | Python, `main.py`                  |

### Phase 5: Testing and Documentation

**Objective**: Ensure reliability and create comprehensive documentation.

| Task | Description                               | Tools              |
| ---- | ----------------------------------------- | ------------------ |
| 5.1  | **Add unit tests**                        | `tests/` directory |
| 5.2  | **Create integration tests**              | `tests/` directory |
| 5.3  | **Develop comprehensive documentation**   | `docs/` directory  |
| 5.4  | **Implement real-time status monitoring** | `main.py`          |

### Phase 6: Future Extensions

**Objective**: Plan for long-term maintenance and expansion.

| Task | Description                       | Tools                   |
| ---- | --------------------------------- | ----------------------- |
| 6.1  | **Design for extensibility**      | Modular structure       |
| 6.2  | **Plan for automation scripts**   | `automation/` directory |
| 6.3  | **Create scriptable control API** | `api_endpoints.py`      |
