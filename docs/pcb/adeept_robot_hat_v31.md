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
All numbers are now defined in `src/hardware/config.yaml`; the YAML file serves as the single source of truth for both the Python API and this documentation.

| Symbol (YAML)             | BCM GPIO | Physical Pin | Voltage | Function / Label on Board        | Notes                       |
| ------------------------- | -------- | ------------ | ------- | -------------------------------- | --------------------------- |
| `gpio.sda`                | 2        | 3            | 3.3 V   | I²C SDA                          | Pull‑up to 3.3 V required   |
| `gpio.scl`                | 3        | 5            | 3.3 V   | I²C SCL                          | Pull‑up to 3.3 V required   |
| `gpio.pwm_servo_0`        | 12       | 32           | 3.3 V   | PWM channel 0 (Servo 0)          | 50 Hz‑1 kHz                 |
| `gpio.pwm_servo_1`        | 13       | 33           | 3.3 V   | PWM channel 1 (Servo 1)          |                             |
| `gpio.pwm_servo_2`        | 19       | 35           | 3.3 V   | PWM channel 2 (Servo 2)          |                             |
| `gpio.pwm_servo_3`        | 18       | 37           | 3.3 V   | PWM channel 3 (Servo 3)          | Shares pin with WS2812_DATA |
| `gpio.ultrasonic_trigger` | 5        | 10           | 3.3 V   | Ultrasonic trigger output        | 10 µs pulse                 |
| `gpio.ultrasonic_echo`    | 6        | 12           | 3.3 V   | Ultrasonic echo input            |                             |
| `gpio.ir_rx`              | 5        | 10           | 3.3 V   | IR receiver data                 |                             |
| `gpio.ws2812_data`        | 18       | 12           | 5 V     | WS2812 data line (5 V tolerant)  |                             |
| `gpio.line_left`          | 22       | 15           | 3.3 V   | Left‑side line‑tracker sensor    |                             |
| `gpio.line_middle`        | 27       | 13           | 3.3 V   | Middle line‑tracker sensor       |                             |
| `gpio.line_right`         | 17       | 11           | 3.3 V   | Right‑side line‑tracker sensor   |                             |
| `gpio.spi0.mosi`          | 10       | 19           | 3.3 V   | SPI0 MOSI (alternate WS2812‑PIN) |                             |
| `gpio.spi0.miso`          | 9        | 21           | 3.3 V   | SPI0 MISO                        |                             |
| `gpio.spi0.sclk`          | 11       | 23           | 3.3 V   | SPI0 SCLK                        |                             |
| `gpio.spi0.ce0`           | 8        | 24           | 3.3 V   | SPI0 CE0                         |                             |
| `gpio.spi0.ce1`           | 7        | 25           | 3.3 V   | SPI0 CE1                         |                             |
| `gpio.spi1.mosi`          | 20       | 23           | 3.3 V   | SPI1 MOSI (alternate WS2812‑PIN) |                             |
| `gpio.spi1.miso`          | 19       | 25           | 3.3 V   | SPI1 MISO                        |                             |
| `gpio.spi1.sclk`          | 21       | 31           | 3.3 V   | SPI1 SCLK                        |                             |
| `gpio.spi1.ce0`           | 18       | 35           | 3.3 V   | SPI1 CE0                         |                             |
| `gpio.spi1.ce1`           | 17       | 37           | 3.3 V   | SPI1 CE1                         |                             |

> **How to keep the table in sync** – The YAML file `src/hardware/config.yaml` is the single source of truth.
> When a pin number changes, edit that file and re‑run the small script `tools/gen_pinout_md.py` (provided in the repo) to regenerate this markdown table automatically.

## Electrical Characteristics & Power Requirements

- **Nominal supply** – 5 V via USB‑C or barrel‑jack.
- **Peak current** – up to **3.75 A** when all servos move; a 4 A (or higher) source is recommended.
- **Regulation** – The HAT contains a 5 V buck‑converter that feeds the motor driver; the Pi’s 5 V rail must stay within ±5 % under load.
- **Grounding** – All grounds (Pi, HAT, external battery, motor driver) must be tied together.

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

The HAT is exposed through the **`src.hardware.adeept_robot_hat`** package.
A minimal example that loads the pin‑mapping and drives a servo:

```python
from adeept_robot_hat import ServoController

# Initialise – reads the mapping from src/hardware/config.yaml
servo = ServoController(board="Adeept_Robot_HAT_V31")

# Move servo 1 (connected to SERVO_1) to 90°
servo.set_angle(channel=0, angle=90)

# Turn on the buzzer for 0.2 s
servo.buzzer.on(duration=0.2)
```

_All public methods (`set_angle`, `set_speed`, `read_ultrasonic`, etc.) will be documented in `software_api.md` that lives alongside this overview._

## Diagram & Images

![Top view of Adeept Robot HAT V3.1](assets/adeept_robot_hat_v31_top.png)

> **Alt‑text:** “Purple Adeept Robot HAT V3.1 stacked on a Raspberry Pi, showing motor ports, servo block, and I²C header.”

## PDF Version

[Full technical manual (PDF)](pdfs/Lesson%202%20Introduction%20of%20Adeept%20Robot%20HAT%20V3.1.pdf)

## Changelog

- **v3.1 (2025‑12‑XX)** – Centralised all pin, bus, and address definitions in `src/hardware/config.yaml`; updated documentation to reference the YAML file.
- **v3.0 (2024‑08‑15)** – Updated motor‑driver interfacing notes.
