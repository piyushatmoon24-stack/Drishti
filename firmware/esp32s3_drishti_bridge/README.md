# Drishti Bridge Firmware (Seeed Studio XIAO ESP32-S3)

Central coordination firmware running on the **Seeed Studio XIAO ESP32-S3**. It manages high-speed serial ingest from the **Grove Vision AI Module V2**, performs non-blocking priority arbitration, and controls the **DFPlayer Mini** audio synthesizer.

---

## Hardware Interface

### Grove Vision AI V2 Direct Socket Mount
The XIAO ESP32-S3 docks directly into the dual 7-pin socket on the back of the Grove Vision AI Module V2 (both USB-C ports facing the same direction):
- **Socket UART1**: XIAO `D7` (GPIO 44, RX) <— Himax WiseEye2 TX @ 921,600 baud
- **Socket UART1**: XIAO `D6` (GPIO 43, TX) —> Himax WiseEye2 RX
- **Socket I2C**: XIAO `D4` (GPIO 5, SDA) <—> Grove Vision AI SDA
- **Socket I2C**: XIAO `D5` (GPIO 6, SCL) —> Grove Vision AI SCL
- **Power**: 3.3V and GND shared directly through the socket.

### DFPlayer Mini & Audio Interface
- **XIAO D1 (GPIO 2)** —> 1kΩ Resistor —> DFPlayer `RX` (Pin 2)
- **XIAO D2 (GPIO 3)** <— DFPlayer `TX` (Pin 3)
- **XIAO 5V** —> DFPlayer `VCC` (Pin 1)
- **XIAO GND** —> DFPlayer `GND` (Pin 7)
- **DFPlayer DAC_R (Pin 9)** —> 3.5mm Earphone Tip (Right)
- **DFPlayer DAC_L (Pin 10)** —> 3.5mm Earphone Ring (Left)
- **DFPlayer GND (Pin 11)** —> 3.5mm Earphone Sleeve (Ground)

---

## Active 8-Class Hazard Hierarchy

| Index | Label | ID | Audio Track | Priority | Empirical Precision |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 0 | `car` | 19 | `0019.mp3` | Priority 1 | 82.5% |
| 1 | `chair` | 23 | `0023.mp3` | Priority 3 | 74.1% |
| 2 | `door` | 8 | `0008.mp3` | Priority 2 | 71.8% |
| 3 | `motorcycle` | 18 | `0018.mp3` | Priority 1 | **99.4%** |
| 4 | `person` | 13 | `0013.mp3` | Priority 2 | **70.3%** |
| 5 | `pole` | 6 | `0006.mp3` | Priority 2 | **94.3%** |
| 6 | `stairs` | 1 | `0001.mp3` | Priority 1 | **97.4%** |
| 7 | `table` | 26 | `0026.mp3` | Priority 3 | 68.2% |

*Note: The system architecture includes a reserved ceiling for a 50-class catalog as part of future expansion.*

---

## Building and Uploading

### Arduino CLI
```bash
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:CDCOnBoot=default,PSRAM=opi firmware/esp32s3_drishti_bridge
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3:CDCOnBoot=default,PSRAM=opi --port <COM_PORT> firmware/esp32s3_drishti_bridge
```

### Arduino IDE
1. Board: `XIAO_ESP32S3` (ESP32 Arduino core)
2. Settings:
   - USB CDC On Boot: `Enabled`
   - PSRAM: `OPI PSRAM`
   - Flash Size: `8MB`
3. Open `esp32s3_drishti_bridge.ino` and upload.
