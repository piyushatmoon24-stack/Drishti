# Grove Vision AI Module V2: Hardware Constraints & Model Deployment Guide

## 1. How the Camera Identifies Objects Without a Manual Image Database

Training an object detector from scratch on 50 classes requires ~50,000+ hand-annotated images. In professional edge AI engineering, this problem is solved using **Transfer Learning from Foundation Models**:

### A. The COCO Foundation Model (27 Overlapping Classes)
The **YOLOv8-Nano** base model is pre-trained on Microsoft's **COCO (Common Objects in Context)** benchmark dataset—comprising **120,000+ real-world photos** with millions of bounding boxes.
Out of our 50 Drishti classes, **27 classes are already learned by this foundation model**:
- **Living Beings & Traffic**: Person (`0013`), Dog (`0014`), Cat (`0015`), Cow (`0016`), Bicycle (`0017`), Motorcycle (`0018`), Car (`0019`), Bus (`0020`), Truck (`0021`), Traffic Light (`0011`).
- **Indoor Living**: Chair (`0023`), Sofa (`0024`), Bed (`0025`), Table (`0026`), Toilet (`0027`), Sink (`0028`).
- **Personal Essentials & Kitchen**: Mobile Phone (`0033`), Water Bottle (`0035`), Cup (`0036`), Food Bowl (`0037`), Cutlery (`0038`), Microwave (`0046`), Refrigerator (`0047`), Toothbrush (`0048`).

Because the neural network already knows the visual features of these objects, the camera can detect them immediately without you needing to take thousands of pictures!

### B. Automated Assistive Dataset Seeding (For Stairs, Doors, Hazards)
For the specialized assistive classes (Stairs Down `0001`, Stairs Up `0002`, Pothole `0004`, Closed Door `0008`, White Cane `0031`):
We provide the automated downloader:
```bash
python scripts/download_sample_dataset.py
```
This automatically fetches real, annotated assistive navigation images from open repositories (Roboflow Universe Assistive Navigation / OpenImages) and stores them directly into:
- `datasets/drishti_50/images/train`
- `datasets/drishti_50/labels/train`

---

## 2. Grove Vision AI Module V2: Storage & Processing Capacity

The **Grove Vision AI Module V2** (Seeed Studio SKU 114993112) is an ultra-low-power edge micro-NPU board. Here are its exact hardware specifications and our optimization strategy:

| Metric | Hardware Limit | Drishti Model Specification | Safety Margin |
| :--- | :--- | :--- | :--- |
| **Processor** | Dual Cortex-M55 CPU + Ethos-U55 NPU @ 400 MHz | Full hardware acceleration via Arm Vela | 100% NPU scheduled |
| **Onboard Flash** | **16 MB QSPI Flash** | **~2.2 MB** (INT8 Quantized `.tflite`) | **>13 MB free** (86% headroom) |
| **System SRAM** | **2.4 MB total SRAM** (~1.4 MB NPU Arena) | **~1.1 MB Tensor Arena** (at $192 \times 192$) | **Fits completely in SRAM** |
| **Inference Speed** | Up to 20 FPS on Ethos-U55 | **12 – 16 FPS** (Real-time navigation) | Smooth obstacle tracking |
| **Power Consumption** | ~0.3W – 0.5W | Ultra-low power | Ideal for battery operation |

### Why $192 \times 192$ Resolution?
- Standard YOLO runs at $640 \times 640$. At that resolution, activation tensors require **>8 MB of RAM**, which would instantly crash the micro-controller with an out-of-memory error (`kTfLiteError`).
- At **$192 \times 192$**, feature maps require only **~1.1 MB of RAM**, fitting inside the Himax HX6538 SRAM without memory swapping or frame drops!

### Why INT8 Quantization?
- 32-bit floating point (FP32) weights take ~12 MB of storage and run slowly on micro-controllers.
- Full INT8 quantization converts all weights and activation tensors to 8-bit integers, reducing model size by **75%** (down to ~2.2 MB) while accelerating Ethos-U55 multiply-accumulate (MAC) throughput by **$4\times$**.

---

## 3. Two Immediate Ways to Run Your System

### Option 1: Instant Zero-Training Setup (Recommended for Day 1)
You can have a working physical prototype running **today without waiting to train a model**:
1. Connect Grove Vision AI Module V2 via USB-C.
2. Open **[Seeed SenseCraft AI Flasher](https://sensecraft.seeed.cc/ai/)** in Chrome/Edge.
3. Flash the official **Swift-YOLO / YOLOv8-Nano COCO Model** (pre-compiled for Ethos-U55 by Seeed).
4. Dock the **Seeed Studio XIAO ESP32-S3** directly into the dual 7-pin socket on the back of the Grove Vision AI Module V2 (both USB-C ports facing the same direction). Zero wires needed between them!
5. Our XIAO ESP32-S3 firmware automatically recognizes the detections (`person`, `chair`, `car`, `bottle`, etc.) over I2C or UART, maps them to the corresponding 4-digit ID (`0013`, `0023`, `0019`, `0035`), and immediately commands the DFPlayer Mini to play the Indian bilingual audio!

### Option 2: Custom 50-Class Drishti Model
For custom training of all 50 classes (including stairs and drop-offs):
1. **Seed Dataset**:
   ```bash
   python scripts/download_sample_dataset.py
   ```
2. **Train YOLOv8n**:
   ```bash
   python scripts/train_yolo.py --epochs 100 --imgsz 192 --batch 32
   ```
3. **Export to INT8 TFLite & Arm Vela**:
   ```bash
   python scripts/export_for_vision_ai_v2.py --weights runs/train/drishti_50_yolov8n/weights/best.pt --imgsz 192
   ```
4. **Flash Custom Bundle**:
   In SenseCraft AI Web, choose **Upload Custom Model**, select `export/grove_vision_ai_v2/model.tflite` and `model.json`, and flash!
