# Drishti: Edge Vision AI Assistive Stick for the Visually Impaired

[![C++](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](https://isocpp.org/)
[![Hardware](https://img.shields.io/badge/Hardware-XIAO%20ESP32--S3%20%7C%20Grove%20Vision%20AI%20V2-brightgreen.svg)](https://www.seeedstudio.com/)
[![NPU](https://img.shields.io/badge/NPU-Arm%20Ethos--U55%20(3ms%20Inference)-orange.svg)](https://www.arm.com/products/silicon-ip-cpu/ethos/ethos-u55)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Award](https://img.shields.io/badge/Recognition-Department's%20Best%20Project%20Award%20Winner-gold.svg)](#acknowledgments)

**Drishti** (*Sanskrit for "Vision"*) is an embedded edge-AI navigation and obstacle identification smart stick designed to empower visually impaired individuals with real-time, context-aware mobility safety.

Unlike conventional white canes that detect hazards only upon physical contact, and unlike ultrasonic canes that emit indiscriminate beeps without context, Drishti uses on-device computer vision to detect, classify, prioritize, and speak out obstacles directly to the user's earphones in **under 50 milliseconds**.

---

## Key Highlights

- **3.0 ms NPU Inference**: Runs a quantized FOMO MobileNetV2 architecture on the **Himax WiseEye2 HX6538 (Arm Cortex-M55 + Arm Ethos-U55 microNPU)** at **31+ FPS**.
- **100% Offline Edge Autonomy**: Zero cloud dependency, zero cellular latency, and zero private data transmission. Works reliably in basements, rural roads, and indoor buildings.
- **Hierarchical Hazard Arbitration**: Prioritizes life-critical drop hazards (stairs, approaching vehicles) over everyday obstacles (chairs, tables), pre-empting lower-priority announcements when immediate safety is at risk.
- **Ultra-Low Power**: Total system consumption is ~1.55W (310 mA @ 5V), providing **over 40 hours of continuous runtime** on a standard 20,000 mAh power bank.

---

## Active 8-Class Hazard Detection System

The current release deploys a curated 8-class model trained and benchmarked over 100 epochs on genuine assistive navigation imagery:

| Index | Class Name | Track ID | Hazard Priority | Safety Role | Precision (%) |
| :---: | :--- | :---: | :---: | :--- | :---: |
| **0** | `car` | `0019.mp3` | Priority 1 | Traffic collision warning | 82.5% |
| **1** | `chair` | `0023.mp3` | Priority 3 | Indoor seating obstacle | 74.1% |
| **2** | `door` | `0008.mp3` | Priority 2 | Gateway & pathway navigation | 71.8% |
| **3** | `motorcycle` | `0018.mp3` | Priority 1 | Fast-moving vehicular hazard | **99.4%** |
| **4** | `person` | `0013.mp3` | Priority 2 | Pedestrian crowd awareness | **70.3%** |
| **5** | `pole` | `0006.mp3` | Priority 2 | Street lamp & pillar collision risk | **94.3%** |
| **6** | `stairs` | `0001.mp3` | Priority 1 | Critical fall hazard (near-zero false alarms) | **97.4%** |
| **7** | `table` | `0026.mp3` | Priority 3 | Low-profile indoor obstacle | 68.2% |

> **Roadmap Note:** The firmware architecture and SD audio catalog include reserved identifiers for an expanded 50-class taxonomy (including traffic signals, crosswalks, potholes, and currency). The active, fully tested, and award-winning implementation focuses strictly on these 8 high-impact classes for verified real-time reliability.

---

## System Architecture

```
[OV2640 Camera]
       │ (DVP @ 30 FPS)
       ▼
[Grove Vision AI Module V2]
  - Himax WiseEye2 HX6538
  - Arm Ethos-U55 NPU (3ms inference)
       │
       │ Hardware UART1 (921,600 baud, non-blocking SSCMA JSON)
       ▼
[Seeed Studio XIAO ESP32-S3]
  - Ring buffer stream ingest
  - Spatial bounding-area priority arbiter
  - Anti-chatter cooldown manager
       │
       │ Hardware UART2 (9600 baud, Command 0x12)
       ▼
[DFPlayer Mini (YX5200)] ──► MicroSD (/MP3/xxxx.mp3)
       │
       │ Analog Left/Right Audio DAC Output
       ▼
[3.5mm Earphone Jack] ──► Spoken real-time audio to user
```

---

## Hardware Interfacing

### 1. Direct Socket Mount (Vision AI <—> XIAO ESP32-S3)
The XIAO ESP32-S3 mounts directly into the dual 7-pin header on the back of the Grove Vision AI Module V2 (ensure both USB-C ports face the same direction):
- **Socket UART1**: XIAO `D7` (RX / GPIO 44) <— Vision AI TX
- **Socket UART1**: XIAO `D6` (TX / GPIO 43) —> Vision AI RX
- **Socket I2C**: XIAO `D4` (SDA / GPIO 5) and `D5` (SCL / GPIO 6)
- **Power**: 3.3V, 5V, and GND are routed internally through the socket.

### 2. DFPlayer Mini Interconnect
Connect the DFPlayer Mini to the exposed header pins of the XIAO ESP32-S3:

| XIAO ESP32-S3 Pin | DFPlayer Mini Pin | Description |
| :--- | :--- | :--- |
| **D1 (GPIO 2)** | **RX (Pin 2)** | Connect via **1kΩ series resistor** to limit current |
| **D2 (GPIO 3)** | **TX (Pin 3)** | Serial feedback |
| **5V (VBUS)** | **VCC (Pin 1)** | 5V supply |
| **GND** | **GND (Pin 7)** | Common system ground |
| **—** | **DAC_R (Pin 9)** | Earphone Right Channel |
| **—** | **DAC_L (Pin 10)** | Earphone Left Channel |
| **—** | **GND (Pin 11)** | Earphone Ground (Sleeve) |

---

## Repository Structure

```
Drishti/
├── firmware/
│   └── esp32s3_drishti_bridge/     # Core ESP32-S3 production firmware
│       ├── esp32s3_drishti_bridge.ino
│       ├── config.h                # System timing and pin configuration
│       ├── vision_ai_parser.h      # SSCMA JSON stream parser & arbiter
│       ├── audio_manager.h         # Cooldown & hazard preemption engine
│       ├── dfplayer_driver.h       # YX5200 serial packet driver
│       └── Seeed_Arduino_SSCMA.*   # SSCMA transport drivers
├── export/                         # Deployed Edge AI Model Artifacts
│   ├── model.tflite                # Quantized INT8 model for SenseCraft
│   ├── model_vela.tflite           # Vela-compiled model for Ethos-U55 NPU
│   ├── model.json                  # Model metadata and class mappings
│   └── README.md                   # Flashing instructions
├── sdcard_mp3/
│   └── MP3/                        # 4-digit voice prompt files (0001.mp3 - 0026.mp3)
├── archive/                        # Preserved historical models and development backups
└── README.md                       # Project documentation
```

---

## Quick Start Guide

### 1. Flash the Vision AI Model
1. Connect the Grove Vision AI Module V2 to your computer via USB-C.
2. Open the [Seeed SenseCraft AI Web Toolkit](https://seeed-studio.github.io/SenseCraft-Web-Toolkit/#/setup/process).
3. Select **Upload Custom AI Model**, choose `export/model.tflite` along with `export/model.json`.
4. Flash the model onto the device.

### 2. Prepare the MicroSD Card
1. Format a microSD card (32GB or smaller) as **FAT32**.
2. Copy the `sdcard_mp3/MP3/` directory into the root of the microSD card.
3. Ensure file paths follow the structure: `/MP3/0001.mp3`, `/MP3/0013.mp3`, etc.
4. Insert the card into the DFPlayer Mini slot.

### 3. Flash the Bridge Firmware
Using the Arduino CLI:
```bash
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:CDCOnBoot=default,PSRAM=opi firmware/esp32s3_drishti_bridge
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3:CDCOnBoot=default,PSRAM=opi --port <PORT> firmware/esp32s3_drishti_bridge
```
Alternatively, open `firmware/esp32s3_drishti_bridge/esp32s3_drishti_bridge.ino` in Arduino IDE, select **XIAO_ESP32S3** with **USB CDC On Boot: Enabled**, and upload.

---

## Diagnostics & Telemetry

Open the Arduino Serial Monitor at **115200 baud** to view live telemetry:
```text
[VisionAI] Connected. ID: bda66518, Name: Grove Vision AI (V2)
[System] Drishti online. Listening for detections...
[Detected] Person (ID 0013) | Conf: 84% | Box: [38,22 115x172]
[Audio] Triggering class 0013 (Person) | Conf: 84%
```

Interactive console commands (type in Serial Monitor and press Enter):
- `13` — Manually triggers the "Person" announcement to test audio.
- `1` — Manually triggers the "Stairs" emergency fall warning.
- `vol 25` — Sets DFPlayer volume level (range: 0 to 30).

---

## Acknowledgments

- **Best Project Award Winner** — Awarded 1st place in the Department Project Exhibition.
- Core development by the Drishti project team.
- Special thanks to our friends who generously assisted with precision hardware soldering and circuit assembly.
- Built on top of Seeed Studio hardware and the Arm Ethos-U55 microNPU ecosystem.
