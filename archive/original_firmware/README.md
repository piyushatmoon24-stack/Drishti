# Drishti Bridge Firmware (Seeed Studio XIAO ESP32-S3)

This firmware runs on the **Seeed Studio XIAO ESP32-S3**, serving as the central nervous system connecting the **Grove Vision AI Module V2** and the **DFPlayer Mini**.

---

## 1. Hardware Architecture & Mounting

The **Grove Vision AI Module V2** features a dual 7-pin female header socket on its back designed specifically to dock the **Seeed Studio XIAO ESP32-S3**.

### Direct Socket Mount (Zero Wires Between Vision AI & XIAO!)
1. Plug the **Seeed Studio XIAO ESP32-S3** directly into the socket on the Grove Vision AI Module V2.
2. Align both boards so that **both USB-C ports face in the same direction**.
3. Once plugged in, the following connections are established internally through the socket:
   - **I2C Bus (Primary):** XIAO `D4` (GPIO 5, SDA) <—> Grove Vision AI SDA
   - **I2C Bus (Primary):** XIAO `D5` (GPIO 6, SCL) <—> Grove Vision AI SCL
   - **Socket UART Bus (Fallback):** XIAO `D7` (GPIO 44, RX) <— Himax WiseEye2 TX
   - **Socket UART Bus (Fallback):** XIAO `D6` (GPIO 43, TX) —> Himax WiseEye2 RX
   - **Power:** 3.3V, 5V (VBUS), and GND are shared automatically.

---

## 2. DFPlayer Mini & Earphone Wiring

Connect the DFPlayer Mini to the exposed header pins of the XIAO ESP32-S3:

| XIAO ESP32-S3 Pin | DFPlayer Mini Pin | DFPlayer Pin # | Notes / Purpose |
| :--- | :--- | :---: | :--- |
| **D1 (GPIO 2)** | **RX** | Pin 2 | **Must insert a 1kΩ resistor in series** to suppress audio buzz |
| **D2 (GPIO 3)** | **TX** | Pin 3 | Direct connection |
| **D3 (GPIO 4)** | **BUSY** | Pin 16 | Detects when voice is actively playing (LOW = Playing, HIGH = Idle) |
| **5V (VBUS)**   | **VCC** | Pin 1 | 5V power supply |
| **GND**         | **GND** | Pin 7 or 10 | Shared common ground |

### 3.5mm Stereo Earphone Jack Wiring
Connect your 3.5mm female earphone socket to the DFPlayer Mini:
- **DAC_R (Pin 9)**  —> 3.5mm Earphone Right Channel
- **DAC_L (Pin 10)** —> 3.5mm Earphone Left Channel
- **GND   (Pin 11)** —> 3.5mm Earphone Ground / Sleeve Ring

> [!WARNING]
> Always insert a **1kΩ series resistor** between XIAO `D1` and DFPlayer `RX`. This protects the DFPlayer chip and eliminates serial buzz / background hiss on your earphones.

---

## 3. Active 8-Class Model Calibration

The bridge firmware is pre-calibrated for the **Edge Impulse FOMO MobileNetV2 0.35 ($128 \times 128$)** model:
- **Operating Threshold:** `35%` (`MIN_CONFIDENCE_THRESHOLD = 35` in [`config.h`](file:///c:/Users/mohan/Documents/Drishti/firmware/esp32s3_drishti_bridge/config.h))
- **Verified Cross-Class Confusion:** `0.0%`
- **Supported Active Classes:**
  - `car` (0) -> `0019.mp3` (Priority 1 Critical Traffic Hazard)
  - `chair` (1) -> `0023.mp3` (Priority 3 Indoor Furniture)
  - `door` (2) -> `0008.mp3` (Priority 2 Navigation Pathway, 76.0% precision)
  - `motorcycle` (3) -> `0018.mp3` (Priority 1 Critical Traffic Hazard, 72.2% precision)
  - `person` (4) -> `0013.mp3` (Priority 2 Pedestrian Safety, 70.7% precision)
  - `pole` (5) -> `0006.mp3` (Priority 2 Street Obstacle, 77.9% precision)
  - `stairs` (6) -> `0001.mp3` (Priority 1 Critical Fall Hazard, 56.2% precision)
  - `table` (7) -> `0026.mp3` (Priority 3 Indoor Furniture)

---

## 4. Flashing Instructions

### Option A: One-Click Automated Script (Fastest)
Double-click [`flash_xiao_esp32s3.bat`](file:///c:/Users/mohan/Documents/Drishti/flash_xiao_esp32s3.bat) in the project root. This automatically flashes the precompiled 8MB merged binary via `esptool`.

### Option B: Arduino IDE
1. Open Arduino IDE.
2. In **Tools -> Board -> esp32**, select:
   - **XIAO_ESP32S3** (or **ESP32S3 Dev Module** if the Seeed board package is not installed).
3. Set the following board options in the **Tools** menu:
   - **USB CDC On Boot:** `Enabled` (Mandatory for Serial Monitor output over USB-C)
   - **Flash Size:** `8MB`
   - **Partition Scheme:** `Default 4MB with spiffs`
4. Open [`esp32s3_drishti_bridge.ino`](file:///c:/Users/mohan/Documents/Drishti/firmware/esp32s3_drishti_bridge/esp32s3_drishti_bridge.ino).
5. Select the COM port for your XIAO ESP32-S3 and click **Upload**.

---

## 5. Serial Monitor Testing Console

1. Open **Serial Monitor** at **115200 baud**.
2. Type any class ID number (e.g. `1` or `0001` for stairs, `13` for person, `8` for door, `19` for car) and press Enter.
3. The XIAO ESP32-S3 will simulate receiving that detection and immediately command the DFPlayer Mini to play the matching voice alert (`/MP3/0001.mp3`, `/MP3/0013.mp3`, etc.) through your earphones.
4. You can also adjust volume at runtime by typing `vol 25` (range: 0 to 30).
