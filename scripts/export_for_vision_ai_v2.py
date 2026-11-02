"""
Drishti Model Export Pipeline for Grove Vision AI Module V2
Converts trained Edge AI models into Ethos-U55 NPU compatible TFLite + SSCMA metadata.

Supports:
1. Active 8-Class Edge Impulse FOMO MobileNetV2 0.35 (128x128) -> SenseCraft AI Package
2. PyTorch (.pt) / Ultralytics YOLO -> INT8 TFLite -> Arm Vela Compilation
"""

import sys
import os
import json
try:
    import yaml
except ImportError:
    yaml = None
import shutil
import argparse
import subprocess
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "data" / "classes_config.json"
YAML_PATH = BASE_DIR / "data" / "drishti_active_8.yaml"
OUTPUT_DIR = BASE_DIR / "export" / "grove_vision_ai_v2"
EI_FIRMWARE_DIR = BASE_DIR / "tools" / "edge_impulse_firmware"

def package_edge_impulse_model():
    """Package the newly trained & compiled Edge Impulse FOMO Vela model
    into export/grove_vision_ai_v2/ for Seeed SenseCraft AI."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    vela_src = EI_FIRMWARE_DIR / "model_vela.tflite"

    if not vela_src.exists():
        print(f"[!] Error: {vela_src} not found!")
        return False

    # Copy binary
    dst_vela = OUTPUT_DIR / "model_vela.tflite"
    dst_tflite = OUTPUT_DIR / "model.tflite"
    shutil.copyfile(vela_src, dst_vela)
    shutil.copyfile(vela_src, dst_tflite)

    # Generate metadata
    metadata = {
        "version": "2.0.0",
        "name": "Drishti-8-Assistive-Vision",
        "description": "8-Class Real-Time Assistive Vision AI for Visually Impaired Navigation (Ethos-U55 NPU)",
        "author": "Drishti",
        "category": "Object Detection",
        "algorithm": "FOMO-MobileNetV2-0.35",
        "input_type": "image",
        "image_type": "rgb",
        "input_shape": [1, 128, 128, 3],
        "classes": [
            "car", "chair", "door", "motorcycle",
            "person", "pole", "stairs", "table"
        ],
        "score_threshold": 0.35,
        "labels": {
            "0": "car", "1": "chair", "2": "door", "3": "motorcycle",
            "4": "person", "5": "pole", "6": "stairs", "7": "table"
        },
        "audio_mapping": {
            "0": {"name": "car", "track": "0019.mp3", "catalog_id": 19, "priority": 1},
            "1": {"name": "chair", "track": "0023.mp3", "catalog_id": 23, "priority": 3},
            "2": {"name": "door", "track": "0008.mp3", "catalog_id": 8, "priority": 2},
            "3": {"name": "motorcycle", "track": "0018.mp3", "catalog_id": 18, "priority": 1},
            "4": {"name": "person", "track": "0013.mp3", "catalog_id": 13, "priority": 2},
            "5": {"name": "pole", "track": "0006.mp3", "catalog_id": 6, "priority": 2},
            "6": {"name": "stairs", "track": "0001.mp3", "catalog_id": 1, "priority": 1},
            "7": {"name": "table", "track": "0026.mp3", "catalog_id": 26, "priority": 3}
        }
    }

    meta_path = OUTPUT_DIR / "model.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Create zip archive for SenseCraft AI
    zip_path = OUTPUT_DIR / "drishti_8class_fomo_128_vela.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(meta_path, arcname="model.json")
        zf.write(dst_tflite, arcname="model.tflite")

    print(f"[+] Successfully exported Edge Impulse FOMO Vela model to {OUTPUT_DIR}")
    print(f"    - Model binary: {dst_tflite} ({dst_tflite.stat().st_size:,} bytes)")
    print(f"    - Metadata:     {meta_path}")
    print(f"    - SenseCraft AI Package: {zip_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Drishti model for Grove Vision AI V2")
    parser.add_argument("--edge-impulse", action="store_true", default=True, help="Package active Edge Impulse FOMO Vela model")
    args = parser.parse_args()

    package_edge_impulse_model()
