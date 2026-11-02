"""
Drishti Roboflow Dataset Importer & Remapper
Extracts Roboflow YOLOv8 zip dataset, remaps the 13 classes to the
Drishti 34-class architecture indices (matching 4-digit unique IDs),
and saves into datasets/drishti_34/.
"""

import os
import shutil
import zipfile
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
ZIP_PATH = BASE_DIR / "My First Project.v2-version.yolov8.zip"
TARGET_DATASET_DIR = BASE_DIR / "datasets" / "drishti_34"

# Roboflow classes as exported in data.yaml:
# ['Car', 'Chair', 'Closed Door', 'Dog', 'Dustbin', 'Mobile Phone', 
#  'Motorcycle', 'Person', 'Pole', 'Pothole', 'Stairs down', 'Stairs up', 'Table']
ROBOFLOW_TO_DRISHTI_MAP = {
    0: 15,  # Car -> 0019 (Car / Taxi)
    1: 18,  # Chair -> 0023 (Chair)
    2: 5,   # Closed Door -> 0008 (Closed Door)
    3: 10,  # Dog -> 0014 (Dog / Guide Dog)
    4: 23,  # Dustbin -> 0030 (Dustbin / Trash Can)
    5: 25,  # Mobile Phone -> 0033 (Mobile Phone)
    6: 14,  # Motorcycle -> 0018 (Motorcycle / Scooter)
    7: 9,   # Person -> 0013 (Person / Pedestrian)
    8: 3,   # Pole -> 0006 (Pole / Street Post)
    9: 2,   # Pothole -> 0004 (Pothole / Trench / Hole)
    10: 0,  # Stairs down -> 0001 (Stairs Down)
    11: 1,  # Stairs up -> 0002 (Stairs Up)
    12: 20  # Table -> 0026 (Table / Desk)
}

CLASS_DISPLAY = {
    0: "0001 - Stairs Down",
    1: "0002 - Stairs Up",
    2: "0004 - Pothole",
    3: "0006 - Pole",
    5: "0008 - Closed Door",
    9: "0013 - Person",
    10: "0014 - Dog",
    14: "0018 - Motorcycle",
    15: "0019 - Car",
    18: "0023 - Chair",
    20: "0026 - Table",
    23: "0030 - Dustbin",
    25: "0033 - Mobile Phone"
}

def main():
    if not ZIP_PATH.exists():
        print(f"[!] Zip file not found at: {ZIP_PATH}")
        return

    print(f"[*] Opening Roboflow zip: {ZIP_PATH.name}...")
    
    # 1. Clean / create target directories
    for split in ["train", "val"]:
        (TARGET_DATASET_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (TARGET_DATASET_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    counts = Counter()
    total_images = 0
    total_labels = 0

    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        namelist = z.namelist()
        
        # Determine source splits inside zip:
        # Roboflow uses train/, valid/, test/
        split_map = {
            "train": "train",
            "valid": "val",
            "val": "val",
            "test": "val"  # merge test into validation to increase validation strength
        }

        print("[*] Extracting images and remapping labels...")

        for name in namelist:
            if name.endswith("/") or name == "data.yaml" or name == "README.roboflow.txt" or name == "README.dataset.txt":
                continue

            parts = name.split("/")
            if len(parts) < 3:
                continue

            src_split, file_type, filename = parts[0], parts[1], parts[2]
            if src_split not in split_map:
                continue

            dst_split = split_map[src_split]

            # Process Images
            if file_type == "images":
                dst_img_path = TARGET_DATASET_DIR / "images" / dst_split / filename
                with z.open(name) as src, open(dst_img_path, "wb") as dst:
                    dst.write(src.read())
                total_images += 1

            # Process & Remap Labels
            elif file_type == "labels":
                content = z.read(name).decode("utf-8", errors="ignore")
                lines = content.strip().split("\n")
                remapped_lines = []

                for line in lines:
                    line_parts = line.strip().split()
                    if not line_parts:
                        continue
                    try:
                        orig_cls = int(line_parts[0])
                        if orig_cls in ROBOFLOW_TO_DRISHTI_MAP:
                            new_cls = ROBOFLOW_TO_DRISHTI_MAP[orig_cls]
                            remapped_line = f"{new_cls} " + " ".join(line_parts[1:])
                            remapped_lines.append(remapped_line)
                            counts[new_cls] += 1
                    except ValueError:
                        continue

                dst_lbl_path = TARGET_DATASET_DIR / "labels" / dst_split / filename
                with open(dst_lbl_path, "w", encoding="utf-8") as dst:
                    dst.write("\n".join(remapped_lines) + "\n")
                total_labels += 1

    print("\n" + "=" * 60)
    print(f"[+] Dataset Import & Remap Complete!")
    print(f"[+] Total Images Extracted: {total_images}")
    print(f"[+] Total Label Files Remapped: {total_labels}")
    print("=" * 60)
    print("Class Instance Counts in Remapped Dataset:")
    for cls_idx in sorted(counts.keys()):
        label_name = CLASS_DISPLAY.get(cls_idx, f"Class {cls_idx}")
        print(f"  [{label_name:<25}] : {counts[cls_idx]:>5} bounding boxes")
    print("=" * 60)
    print(f"[+] Clean, remapped dataset ready at: {TARGET_DATASET_DIR}")

if __name__ == "__main__":
    main()
