"""
Drishti Dataset Preparation & Mapping Utility
Maps source datasets (COCO 80, OpenImages, Roboflow) to the 50 Drishti 4-Digit Classes.

Drishti Class Index (0-49) corresponds to ID "0001" through "0050".
"""

import os
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "data" / "classes_config.json"
DATASET_DIR = BASE_DIR / "datasets" / "drishti_34"

# COCO-80 to Drishti 34 class mapping (COCO class name -> Drishti 4-digit ID)
COCO_TO_DRISHTI_MAP = {
    # Outdoor & Traffic
    "traffic light": "0011",  # Defaults to traffic light
    "person": "0013",
    "dog": "0014",
    "cat": "0015",
    "cow": "0016",
    "bicycle": "0017",
    "motorcycle": "0018",
    "car": "0019",
    "bus": "0020",
    "truck": "0021",
    
    # Indoor Furniture & Sanitation
    "chair": "0023",
    "couch": "0024",
    "bed": "0025",
    "dining table": "0026",
    "toilet": "0027",
    "sink": "0028",
    
    # Personal Items & Kitchenware
    "cell phone": "0033",
    "bottle": "0035",
    "cup": "0036",
    "bowl": "0037",
    "fork": "0038",
    "spoon": "0038",
    "knife": "0038",
    
    # Home & Hygiene
    "microwave": "0046",
    "oven": "0046",
    "refrigerator": "0047",
    "toothbrush": "0048",
}

def load_drishti_classes():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        classes = json.load(f)
    # Return mapping from 4-digit ID ("0001") to YOLO 0-based index (0)
    id_to_idx = {item["id"]: idx for idx, item in enumerate(classes)}
    idx_to_id = {idx: item["id"] for idx, item in enumerate(classes)}
    return classes, id_to_idx, idx_to_id

def create_dataset_scaffold():
    """Initializes standard YOLO folder structure for the dataset."""
    splits = ["train", "val", "test"]
    for split in splits:
        (DATASET_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATASET_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)
    print(f"[+] Created dataset directories at {DATASET_DIR}")

def validate_dataset():
    """Validates that all label files in the dataset have valid class indices (0-49)."""
    classes, id_to_idx, idx_to_id = load_drishti_classes()
    print(f"[*] Validating dataset at {DATASET_DIR} against 34 classes...")
    
    issues_found = 0
    total_labels = 0
    for split in ["train", "val"]:
        label_dir = DATASET_DIR / "labels" / split
        if not label_dir.exists():
            continue
        for label_file in label_dir.glob("*.txt"):
            total_labels += 1
            with open(label_file, "r") as f:
                lines = f.readlines()
            for line_no, line in enumerate(lines, 1):
                parts = line.strip().split()
                if not parts:
                    continue
                try:
                    cls_idx = int(parts[0])
                    if cls_idx < 0 or cls_idx >= len(classes):
                        print(f"[-] Invalid class index {cls_idx} in {label_file.name}:{line_no}")
                        issues_found += 1
                except ValueError:
                    print(f"[-] Malformed line in {label_file.name}:{line_no}: '{line.strip()}'")
                    issues_found += 1

    if issues_found == 0:
        print(f"[+] Validation complete! Checked {total_labels} label files. All class indices are within 0-49.")
    else:
        print(f"[!] Validation found {issues_found} issue(s). Please correct them before training.")

def print_summary():
    classes, id_to_idx, _ = load_drishti_classes()
    print("\n" + "=" * 60)
    print(" DRISHTI 50-CLASS SUMMARY & COCO SEEDING MAP")
    print("=" * 60)
    print(f"Total Drishti classes: {len(classes)}")
    print(f"Direct COCO overlaps ready for transfer learning: {len(COCO_TO_DRISHTI_MAP)}")
    print("\nSpecialized Assistive Classes (Recommended Roboflow / OpenImages):")
    specialized = [c for c in classes if c["id"] not in COCO_TO_DRISHTI_MAP.values()]
    for s in specialized:
        print(f"  [{s['id']}] {s['name']} ({s['category']}) - Priority: {s['priority']}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    create_dataset_scaffold()
    print_summary()
    validate_dataset()
