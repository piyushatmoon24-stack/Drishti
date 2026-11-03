# Deployed Edge AI Model Artifacts

This directory contains the highest-accuracy trained and Vela-compiled INT8 model for the **Grove Vision AI Module V2 (Himax WiseEye2 HX6538 + Arm Ethos-U55 NPU)**.

## Model Details
- **Architecture**: FOMO MobileNetV2 0.35
- **Input Resolution**: 128x128 RGB
- **Quantization**: INT8 post-training quantization via Arm Vela compiler
- **Inference Latency**: 3.0 ms per frame (`perf: [3, 3, 0]`)
- **Macro Precision**: 75.37% (100-epoch convergence)

## Active Classes (8 Hazard Classes)
| Index | Label | Priority | Safety Role | Precision |
| :---: | :--- | :---: | :--- | :---: |
| 0 | `car` | 1 | Traffic collision hazard | 82.5% |
| 1 | `chair` | 3 | Indoor seating obstacle | 74.1% |
| 2 | `door` | 2 | Navigation gateway | 71.8% |
| 3 | `motorcycle` | 1 | High-speed traffic hazard | **99.4%** |
| 4 | `person` | 2 | Pedestrian dynamic obstacle | 70.3% |
| 5 | `pole` | 2 | Street lamp / pillar collision | **94.3%** |
| 6 | `stairs` | 1 | Critical fall hazard | **97.4%** |
| 7 | `table` | 3 | Low-level indoor obstacle | 68.2% |

## Deployment Instructions
1. Connect Grove Vision AI V2 to PC via USB-C.
2. Open [SenseCraft AI Web Toolkit](https://seeed-studio.github.io/SenseCraft-Web-Toolkit/#/setup/process).
3. Connect COM port, select **Upload Custom AI Model**.
4. Select `model.tflite` (or `model_vela.tflite`) with `model.json`.
5. Click **Flash**. Once 100% complete, mount board back onto XIAO ESP32-S3.
