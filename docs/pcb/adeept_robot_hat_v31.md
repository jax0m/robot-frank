---
title: "Adeept Robot HAT V3.1 – Technical Overview"
component: "Adeept Robot HAT V3.1"
manufacturer: "Adeept"
model: "V3.1"
status: "released"
related_python_pkg: "src.hardware.adeept_robot_hat"
version: "v3.1 (2025-12-XX)"
---

## Overview

The **Adeept Robot HAT V3.1** is a purple single‑board microcontroller that stacks directly on a Raspberry Pi.
It acts as the robot’s “brain”, providing power distribution, motor control, and a rich set of sensor/actuator interfaces.
The board is manufactured by **Adeept** (<https://www.adeept.com>) and is the reference controller for the **Adeept Rasptank‑Metal** robot platform.

> **Quick link** – [Download the full PDF manual](pdfs/Lesson%202%20Introduction%20of%20Adeept%20Robot%20HAT%20V3.1.pdf)

## Pin‑out / Mapping Table

The table below translates the **hardware labels** used on the HAT to the **Raspberry Pi GPIO numbers** (BCM) that the robot’s Python drivers use.
If you have the board schematic, verify the numbers and fill any missing entries.

| Symbol            | BCM GPIO                     | Physical Pin                  | Voltage | Function / Label on Board            | Notes                                     |
| ----------------- | ---------------------------- | ----------------------------- | ------- | ------------------------------------ | ----------------------------------------- |
| `VCC_5V`          | 2 (or 4)                     | 3 & 5                         | 5 V     | Power rail for servos & LEDs         | Must be able to source ≥ 4 A peak         |
| `GND`             | 6, 9, 14, 20, 25, 30, 34, 39 | 9, 11, 13, 15, 17, 21, 23, 25 | 0 V     | Common ground                        | Connect to all ground pins on Pi          |
| `M1_PWM`          | 12                           | 32                            | 3.3 V   | Motor 1 PWM (IN1)                    | PWM range 0‑255, 50 Hz – 1 kHz            |
| `M2_PWM`          | 13                           | 33                            | 3.3 V   | Motor 2 PWM (IN2)                    | Same as M1                                |
| `M3_PWM`          | 19                           | 35                            | 3.3 V   | Motor 3 PWM (IN3)                    |                                           |
| `M4_PWM`          | 26                           | 37                            | 3.3 V   | Motor 4 PWM (IN4)                    |                                           |
| `SERVO_1`         | 17                           | 11                            | 3.3 V   | Servo PWM channel 0                  | 500‑2500 µs pulse                         |
| `SERVO_2`         | 27                           | 13                            | 3.3 V   | Servo PWM channel 1                  |                                           |
| `SERVO_3`         | 22                           | 15                            | 3.3 V   | Servo PWM channel 2                  |                                           |
| `SERVO_4`         | 23                           | 16                            | 3.3 V   | Servo PWM channel 3                  |                                           |
| `IR_RX`           | 5                            | 10                            | 3.3 V   | Infrared receiver data               |                                           |
| `WS2812_DATA`     | 18                           | 12                            | 5 V     | WS2812 data line                     | 5 V tolerant, use level‑shifter if needed |
| `I2C_SCL`         | 3                            | 5                             | 3.3 V   | I²C clock                            | Pull‑up to 3.3 V required                 |
| `I2C_SDA`         | 2                            | 3                             | 3.3 V   | I²C data                             | Pull‑up to 3.3 V required                 |
| `UART_TX`         | 14                           | 8                             | 3.3 V   | UART TX (to host)                    |                                           |
| `UART_RX`         | 15                           | 10                            | 3.3 V   | UART RX (from host)                  |                                           |
| `ULTRASONIC_TRIG` | 24                           | 18                            | 3.3 V   | Trigger output                       | 10 µs pulse                               |
| `ULTRASONIC_ECHO` | 25                           | 22                            | 3.3 V   | Echo input                           |                                           |
| `LED_POWER`       | 4                            | 7                             | 3.3 V   | Power‑ON indicator (X5)              | LED on when board powered                 |
| `BAT_LOW`         | 21                           | 37                            | 3.3 V   | Low‑battery indicator (last red LED) |                                           |
| `BUZZER`          | 24                           | 18                            | 3.3 V   | Passive buzzer control               |                                           |

> **How to fill the table**
>
> 1. Open the schematic PDF (or the PCB layout file).
> 2. Locate each labeled connector (e.g., `M1`, `SERVO_1`, `IR_RX`).
> 3. Identify the Raspberry Pi pin that the schematic routes to (most Adeept docs label the pins with BCM numbers; if not, use the physical pin number and convert with the Pi GPIO table).
> 4. Populate the columns **BCM GPIO**, **Physical Pin**, **Voltage**, **Function**, and **Notes**.
> 5. If a signal is not directly tied to a Pi pin (e.g., a dedicated driver output), note that the Python driver creates the PWM channel internally – you can still expose the _symbolic name_ here for documentation purposes.

## Electrical Characteristics & Power Requirements

- **Nominal supply** – 5 V via USB‑C or barrel‑jack.
- **Peak current** – up to **3.75 A** when all servos are moving; a 4 A (or higher) source is strongly recommended.
- **Regulation** – The HAT contains a 5 V buck‑converter that feeds the motor driver; the Pi’s 5 V rail must stay within ±5 % under load.
- **Grounding** – All grounds (Pi, HAT, external battery, motor driver) must be tied together to avoid floating references.

## Mechanical / Connector Summary

| Connector               | Physical description                           | Typical use                                |
| ----------------------- | ---------------------------------------------- | ------------------------------------------ |
| **Type‑C USB**          | 24‑pin micro‑USB‑C receptacle                  | Power input & data transfer                |
| **Barrel‑Jack**         | 3‑pin 5.5 mm centre‑positive                   | External battery / power source            |
| **Motor Ports (M1‑M4)** | 4× white screw‑terminal block (2 × 2 mm pitch) | Connect external motor driver board        |
| **Servo Block**         | Red‑black‑yellow trio of terminals             | Individual servo power & signal            |
| **IR Receiver**         | 3‑pin IR module footprint                      | Remote‑control receiver                    |
| **WS2812 Port**         | 3‑pin header (5 V, GND, DIN)                   | Addressable RGB LED strip                  |
| **X1‑X9 I/O Block**     | Mixed header pins (see table)                  | I²C, UART, line‑tracking, ultrasonic, etc. |
| **LED Indicators**      | Surface‑mount LEDs (X5, RD15, battery‑LEDs)    | Status feedback                            |

## Software API (Python)

The HAT is exposed through the **`src.hardware.adeept_robot_hat`** package (to be created).
A minimal example that loads the pin‑mapping and drives a servo:

```python
from adeept_robot_hat import ServoController

# Initialise – reads the mapping from the YAML front‑matter
servo = ServoController(board="Adeept_Robot_HAT_V31")

# Move servo 1 (connected to SERVO_1) to 90°
servo.set_angle(channel=0, angle=90)

# Turn on the buzzer for 0.2 s
servo.buzzer.on(duration=0.2)
```

_All public methods (`set_angle`, `set_speed`, `read_ultrasonic`, etc.) will be documented in the `software_api.md` file that lives alongside this overview._

## Diagram & Images

### Top of HAT

The image displays a top-down view of a purple single-board microcontroller, designed for robotics or embedded projects. The board is densely populated with various electronic components, connectors, and integrated circuits, all labeled with callouts.
The board features several rows of white terminal blocks and pin headers, providing numerous connection points for sensors, motors, and other peripherals. The overall layout suggests a versatile platform for controlling and interacting with various hardware components.
The boxes around the "Ultrasonic," "LED1~3," and "X4/X5:RGB" components are a visual aid, possibly from the source material, to group related pins together. The board is populated with various sensors and connectors for robotics and embedded applications.

#### Top 1 of 2

![Top view of Adeept Robot HAT V3.1 (1 of 2)](<assets/adeept_robot_hat_v3.1_top(1of2).png>)

- MPU6050: Located in the upper-left area, this is a 6-axis motion tracking sensor (accelerometer and gyroscope) used for detecting movement and orientation.
- Buzzer: A small, black, cylindrical component located near the center of the board, used to generate audible signals.
- Indicator: A small LED (Light-Emitting Diode) labeled "RD15" in the upper-center, used to provide visual feedback.
- Type-C USB - CHARGING ONLY
- Switch: A slide switch on the right side, labeled "OFF" and "ON", used to power the board on or off.
- Power: 2 pin socket (for battery pack)
- Battery Indicator: A series of 4 LEDs (Upper most in image being red, followed by 3 green which indicate the charge state (Red + 3 Green = 100%, Red + 0 Green = Nearly depleted).
- Power Indicator: A single LED, labeled "X5", which serves as a power-on indicator.
- Servo: A group of red, black, and yellow terminal blocks on the lower left, which are used to connect servo motors.
- IR: An infrared receiver module, located in the center left section to the immediate right of a WS2812 onboard.
- WS2812: A type of addressable RGB LED, shown with its integrated circuit (IC).
- WS2812 Port: A connector designed to interface with WS2812 LEDs, which are commonly used for programmable lighting.

#### Top 2 of 2

![Top view of Adeept Robot HAT V3.1 (2 of 2)](<assets/adeept_robot_hat_v3.1_top(2of2).png>)

- X8: Line Tracking: This label points to a white header (a row of connection pins) on the upper-left side of the board. This is a dedicated connector for a line-tracking sensor, which is used by robots to follow a black line on the floor.
- X9: Ultrasonic: This label points to a white header in the center of the board. This connector is for an ultrasonic sensor, which uses sound waves to measure distance to objects.
- LED1~3: This label highlights a group of three small, white, rectangular connectors. These are the output terminals for connecting external RGB LEDs, which can display a wide range of colors.
- X4/X5: RGB: This label points to another set of white connectors in the center-right, specifically for connecting RGB LEDs.
- X1/X2: I2C: This label indicates a group of white terminal blocks on the lower-left. These pins are for the I2C (Inter-Integrated Circuit) communication protocol, a common way to connect sensors and other devices.
- X6/X7: UART: This label points to another group of white terminal blocks, located on the lower-center. These are for the UART (Universal Asynchronous Receiver/Transmitter) serial communication interface.
- X3: Light Tracking: This label is directed at a white header on the lower-left side, which is used to connect a light-tracking sensor (such as a photodiode array) that detects the direction of a light source.

### Bottom of HAT

![Bottom view of Adeept Robot HAT V3.1](assets/adeept_robot_hat_v3.1_bottom.png)

The board features several key components and connectors, which are highlighted and labeled in the image:

- "Adeep Robot HAT v3.0 for Raspberry Pi" - This is the main title printed in the center of the board, clearly identifying its model and purpose.
- "www.adeept.com" - This URL is printed in the top-left corner, which is the official website of the manufacturer, Adeep.
- Adeep: The brand logo, a stylized "A" with a gear symbol, is visible in the lower-right section of the board.
- Motor: This label points to a large, black, dual-row connector located at the top of the board. This is the primary connection for a motor driver, designed to interface with motors (like DC motors or stepper motors) for robot applications. These labels point to four white, female, screw-terminal connectors arranged vertically on the right side of the board. These are standard terminal blocks used to make secure electrical connections to external components.
  - M1 - Upper-right connector
  - M2 - Below M1
  - M3 - Above M4
  - M4 - Lower-right connector

The red box and the labels "M1," "M2," "M3," and "M4" specifically highlight this group of connectors, which are typically used to connect motor driver boards or other external peripherals to the main controller board.

## PDF Version

[Full technical manual (PDF)](pdfs/Lesson%202%20Introduction%20of%20Adeept%20Robot%20HAT%20V3.1.pdf)
