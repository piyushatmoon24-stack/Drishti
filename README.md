# Drishti: 34-Class Assistive Vision AI System

**Drishti** (दृष्टि - *Sight/Vision*) is an intelligent, low-latency, edge AI navigation and safety assistant designed for visually impaired individuals.

It combines an ultra-low-power vision processor (**Grove Vision AI Module V2**) with a microcontroller bridge (**ESP32-S3**) and an audio synthesizer (**DFPlayer Mini**), delivering real-time spoken audio alerts through earphones.

---

## 🌟 System Architecture & Concept

```
+---------------------------------------+
|      Grove Vision AI Module V2        |
|  (Himax WiseEye2 / Arm Ethos-U55 NPU) |
+---------------------------------------+
                   ||  Direct Dual 7-Pin Socket Dock
                   ||  Internal I2C (D4=SDA, D5=SCL) + Power
                   vv
+---------------------------------------+
|     Seeed Studio XIAO ESP32-S3        |
|  - Real-time Priority Scheduler       |
|  - Anti-Chatter Distance Arbiter      |
|  - Direct DFPlayer Audio Trigger      |
+---------------------------------------+
                   |
                   | UART (D1=TX, D2=RX, D3=BUSY)
                   v
+---------------------------------------+        Direct Audio      +------------------------+
|             DFPlayer Mini             | -----------------------> |  3.5mm Stereo Earphone |
|       (FAT32 MicroSD: /MP3/*.mp3)     |       (DAC_L / DAC_R)    |  Spoken Voice Guidance |
+---------------------------------------+                          +------------------------+
```

### Why 4-Digit Unique IDs (`0001` - `0050`)?
Instead of sending long English strings over embedded serial links, the model is trained with **4-digit numerical class labels**:
- `0001` -> Stairs Down
- `0002` -> Stairs Up
- `0003` -> Curb / Drop-off
- ...
- `0050` -> Fan

This directly matches the native file naming format required by the **DFPlayer Mini**:
$$\text{Class ID: } \mathbf{0001} \longrightarrow \text{MicroSD File: } \texttt{/MP3/0001.mp3}$$

The ESP32-S3 simply forwards the integer `1` to `playMp3Folder(1)`, resulting in near-instantaneous audio playback with zero text processing latency!

---

## 🎯 Active Deployed 8-Class Edge AI Model (128x128 Balanced Dataset)

The active standalone model running 100% on the **Grove Vision AI Module V2 (Ethos-U55 NPU)** is trained with FOMO MobileNetV2 0.35 on a **balanced 8-class Roboflow dataset (~750 images/class, 4,193 total images) at native 128x128 resolution**, compiled with Arm Vela:

| Model Index | Model Class | Catalog ID | DFPlayer Track | Hazard Priority | Description | Verified Precision |
| :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| `0` | `car` | `0019` | `0019.mp3` | **Critical (1)** | Moving or parked automobiles / taxis | **48.6%** |
| `1` | `chair` | `0023` | `0023.mp3` | **Low (3)** | Indoor chairs, benches, office seating | **57.8%** |
| `2` | `door` | `0008` | `0008.mp3` | **Normal (2)** | Closed & open entry doors, pathways | **76.0%** |
| `3` | `motorcycle` | `0018` | `0018.mp3` | **Critical (1)** | Approaching motorcycles, two-wheelers | **72.2%** |
| `4` | `person` | `0013` | `0013.mp3` | **Normal (2)** | Pedestrians, walking humans | **70.7%** |
| `5` | `pole` | `0006` | `0006.mp3` | **Normal (2)** | Street light poles, utility posts, pillars | **77.9%** |
| `6` | `stairs` | `0001` | `0001.mp3` | **Critical (1)** | Ascending and descending stairs (fall hazard) | **56.2%** |
| `7` | `table` | `0026` | `0026.mp3` | **Low (3)** | Tables, dining surfaces, office desks | **22.2%** |

### 🚀 Flashing & Live Preview Shortcuts
- **Flash Vision AI Module V2:** Double-click `flash_grove_vision.bat` (flashes `model_vela.tflite` via XModem).
- **Flash XIAO ESP32-S3:** Double-click `flash_xiao_esp32s3.bat` (flashes precompiled bridge firmware with calibrated 35% threshold).
- **Live GUI Preview & Audio Simulator:** Double-click `preview_drishti_vision.bat` for live bounding box visualization and speech synthesis.

---

## 📋 The 50 Assistive Classes Catalog

| ID | Class Name | Category | Hazard Level | Voice Prompt |
| :---: | :--- | :--- | :---: | :--- |
| **0001** | Stairs Down | Critical Hazard | Level 1 | *"Caution, stairs going down ahead"* |
| **0002** | Stairs Up | Critical Hazard | Level 1 | *"Stairs going up ahead"* |
| **0004** | Pothole / Trench / Hole | Critical Hazard | Level 1 | *"Warning, hole or uneven ground ahead"* |
| **0006** | Pole / Street Post | Navigation Obstacle | Level 2 | *"Obstacle, pole directly ahead"* |
| **0007** | Wall / Barricade | Navigation Obstacle | Level 2 | *"Barrier or wall ahead"* |
| **0008** | Closed Door | Navigation Obstacle | Level 2 | *"Closed door ahead"* |
| **0010** | Zebra Crosswalk | Outdoor Safety | Level 2 | *"Pedestrian crosswalk ahead"* |
| **0011** | Traffic Light (Red) | Outdoor Safety | Level 1 | *"Stop, red traffic signal"* |
| **0012** | Traffic Light (Green) | Outdoor Safety | Level 1 | *"Safe, green traffic signal"* |
| **0013** | Person / Pedestrian | Living Organism | Level 2 | *"Person in front of you"* |
| **0014** | Dog / Guide Dog | Living Organism | Level 2 | *"Dog detected"* |
| **0015** | Cat / Small Pet | Living Organism | Level 3 | *"Small animal on the floor"* |
| **0016** | Cow / Large Animal | Living Organism | Level 1 | *"Caution, large animal in your path"* |
| **0017** | Bicycle | Traffic Vehicle | Level 2 | *"Bicycle approaching"* |
| **0018** | Motorcycle / Scooter | Traffic Vehicle | Level 2 | *"Motorcycle nearby"* |
| **0019** | Car / Taxi | Traffic Vehicle | Level 2 | *"Car ahead"* |
| **0020** | Bus | Traffic Vehicle | Level 2 | *"Bus ahead"* |
| **0022** | Auto Rickshaw | Traffic Vehicle | Level 2 | *"Auto rickshaw nearby"* |
| **0023** | Chair | Indoor Furniture | Level 3 | *"Chair nearby"* |
| **0025** | Bed | Indoor Furniture | Level 3 | *"Bed ahead"* |
| **0026** | Table / Desk | Indoor Furniture | Level 3 | *"Table ahead"* |
| **0027** | Toilet / Commode | Indoor Sanitation | Level 3 | *"Toilet bowl directly ahead"* |
| **0029** | Elevator / Lift | Indoor Navigation | Level 2 | *"Elevator door ahead"* |
| **0030** | Dustbin / Trash Can | Indoor / Outdoor | Level 3 | *"Trash bin nearby"* |
| **0032** | Eyeglasses / Spectacles | Personal Essential | Level 3 | *"Eyeglasses on the surface"* |
| **0033** | Mobile Phone | Personal Essential | Level 3 | *"Mobile phone detected"* |
| **0035** | Water Bottle | Personal Essential | Level 3 | *"Water bottle ahead"* |
| **0039** | Currency Banknote | Personal Essential | Level 2 | *"Paper banknote detected"* |
| **0040** | Coin | Personal Essential | Level 3 | *"Coin detected"* |
| **0042** | Wallet / Purse | Personal Essential | Level 3 | *"Wallet detected"* |
| **0045** | Wall Socket / Switch | Safety Hazard | Level 2 | *"Caution, electric wall socket"* |
| **0046** | Stove / Microwave / Burner | Safety Hazard | Level 1 | *"Warning, stove or cooking burner"* |
| **0047** | Refrigerator | Home Appliance | Level 3 | *"Refrigerator ahead"* |
| **0050** | Ceiling / Table Fan | Home Appliance | Level 3 | *"Fan detected"* |

*Full metadata available in [`data/classes_config.json`](file:///c:/Users/mohan/Documents/Drishti/data/classes_config.json) and [`data/classes_reference.md`](file:///c:/Users/mohan/Documents/Drishti/data/classes_reference.md).*

---

## ⚡ Hardware Wiring & Connections

### Direct Socket Mount (Grove Vision AI V2 <—> XIAO ESP32-S3)
The **Seeed Studio XIAO ESP32-S3** docks directly into the dual 7-pin socket on the back of the **Grove Vision AI Module V2** (USB-C ports facing the same direction):
- **SDA / SCL:** XIAO `D4` (GPIO 5) and `D5` (GPIO 6) internally connect to the Vision AI module via I2C.
- **Power:** 3.3V, 5V, and GND are routed through the socket automatically. **Zero jumper wires required!**

### DFPlayer Mini Interconnect Table

| XIAO ESP32-S3 Pin | To Peripheral | Peripheral Pin | Connection Note |
| :--- | :--- | :---: | :--- |
| **D1 (GPIO 2)**  | DFPlayer Mini | **RX (Pin 2)** | **Must add 1kΩ series resistor** to eliminate audio hiss |
| **D2 (GPIO 3)**  | DFPlayer Mini | **TX (Pin 3)** | Direct connection |
| **D3 (GPIO 4)**  | DFPlayer Mini | **BUSY (Pin 16)**| Senses active playback (LOW = Playing, HIGH = Idle) |
| **5V (VBUS)**    | DFPlayer Mini | **VCC (Pin 1)** | 5V power supply |
| **GND**          | DFPlayer Mini | **GND (Pin 7/10)**| Common ground |

### Vision AI Module V2 Socket Interconnect (Internal)
When the XIAO ESP32-S3 is docked into the Grove Vision AI Module V2 socket:
- **D4 (GPIO 5, SDA) / D5 (GPIO 6, SCL):** Primary I2C communication bus (0x62)
- **D7 (GPIO 44, RX) / D6 (GPIO 43, TX):** Secondary Socket UART fallback (115200 baud)
- **3.3V, 5V, GND:** Shared internal power rails

### Earphone Connection (DFPlayer Mini)
- **Pin 9 (DAC_R)** -> 3.5mm Earphone Jack Right Channel
- **Pin 10 (DAC_L)** -> 3.5mm Earphone Jack Left Channel
- **Pin 11 (GND)** -> 3.5mm Earphone Jack Ground Ring

---

## 🚀 Step-by-Step Setup Guide

### 1. Prepare the MicroSD Card for DFPlayer Mini
1. Format a MicroSD card (≤32GB) with **FAT32** file system.
2. Run the audio generation script (pre-configured with high quality neural TTS voices):
   ```bash
   python scripts/generate_audio_assets.py
   ```
3. Copy the entire `sdcard_mp3/MP3` folder directly to the root of your MicroSD card.
   The structure must be:
   ```
   [MicroSD Root]
   └── MP3/
       ├── 0001.mp3
       ├── 0002.mp3
       ├── ...
       └── 0050.mp3
   ```
4. Insert the MicroSD card into the DFPlayer Mini slot.

---

### 2. Flash the XIAO ESP32-S3 Bridge Firmware
1. Open Arduino IDE.
2. In **Tools -> Board -> esp32**, select **XIAO_ESP32S3** (or **ESP32S3 Dev Module**).
3. Set **USB CDC On Boot: Enabled** in the Tools menu.
4. *(Optional)*: Install the `Seeed_Arduino_SSCMA` library via **Sketch -> Include Library -> Manage Libraries...** for native I2C socket support.
5. Open [`firmware/esp32s3_drishti_bridge/esp32s3_drishti_bridge.ino`](file:///c:/Users/mohan/Documents/Drishti/firmware/esp32s3_drishti_bridge/esp32s3_drishti_bridge.ino).
6. Upload the firmware.
7. Open **Serial Monitor** at **115200 baud**:
   - Type `1` or `0001` to test the "Stairs Down" prompt over your earphones!
   - Type `13` to test "Person ahead".
   - Type `vol 25` to adjust earphone volume.

---

### 3. Model Training & Vision AI V2 Deployment

The Drishti object detection model is deployed to the **Himax WiseEye2 HX6538 (Arm Cortex-M55 + Ethos-U55 NPU)** on the Grove Vision AI Module V2.

#### A. Active 8-Class Model Specifications
- **Architecture**: FOMO MobileNetV2 0.35 ($128 \times 128$ RGB native resolution)
- **Hardware Acceleration**: Compiled via Arm Vela for Himax WiseEye2 Ethos-U55 NPU (37,648 bytes)
- **Dataset**: Balanced 4,193 authentic Roboflow assistive images (~750 images/class)
- **Verified Test Precision**: **67.11%** (Breakthrough: `door` 76.0%, `person` 70.7%, `pole` 77.9%, `motorcycle` 72.2%)
- **Cross-Class Confusion**: **0.0%** (zero false swaps between classes)
- **Calibrated Operating Threshold**: **35%** (calibrated in [`firmware/esp32s3_drishti_bridge/config.h`](file:///c:/Users/mohan/Documents/Drishti/firmware/esp32s3_drishti_bridge/config.h))

#### B. Flashing the Model onto Grove Vision AI Module V2

##### Method 1: One-Click Offline Flasher (Recommended)
1. Connect the Grove Vision AI Module V2 directly to your PC via USB-C.
2. Double-click `flash_grove_vision.bat` (or run `python flash_edge_impulse.py`).
3. When prompted, press the physical **RST** button on the Grove Vision AI board once.
4. The flasher transfers the Ethos-U55 firmware image and `model_vela.tflite` at 921,600 baud via XModem.

##### Method 2: Seeed SenseCraft AI Web Flasher
1. Connect the Grove Vision AI Module V2 to your computer via USB-C.
2. Open **[Seeed SenseCraft AI](https://sensecraft.seeed.cc/ai/#/model)** in Google Chrome or Edge.
3. Select **Grove - Vision AI V2** and click **Connect**.
4. Choose **Upload Custom Model**, upload [`export/grove_vision_ai_v2/drishti_8class_fomo_128_vela.zip`](file:///c:/Users/mohan/Documents/Drishti/export/grove_vision_ai_v2/drishti_8class_fomo_128_vela.zip) (or `model.json` + `model.tflite`), set confidence to **35%**, and flash!

---

## 🧠 Smart Firmware Features
- **Anti-Chatter Debounce**: Prevents spamming the user when looking at an object continuously.
- **Life-Critical Preemption**: Immediate hazards (e.g. `0001` Stairs Down or `0004` Pothole) bypass non-critical cooldowns to alert the user instantly.
- **Hardware-Serial Native**: Zero external library conflicts, operates on ESP32-S3's dedicated hardware UART FIFO buffers.
