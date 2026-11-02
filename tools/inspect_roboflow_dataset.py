import os
import sys
import zipfile
from collections import defaultdict
import yaml

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ZIP_PATH = r"C:\Users\mohan\OneDrive\文档\Drishti\datasets\My First Project.v3i.yolov8.zip"
EXTRACT_DIR = os.path.abspath(r"datasets\roboflow_yolov8")

def main():
    print(f"[*] Extracting dataset archive to {EXTRACT_DIR}...")
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(EXTRACT_DIR)
    print("[+] Extraction complete.")

    yaml_path = os.path.join(EXTRACT_DIR, "data.yaml")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data_cfg = yaml.safe_load(f)

    class_names = data_cfg.get('names', [])
    print(f"[*] Total classes ({len(class_names)}): {class_names}")

    splits = ['train', 'valid', 'test']
    split_stats = {s: defaultdict(int) for s in splits}
    images_with_target_8 = {s: 0 for s in splits}
    images_without_target_8 = {s: 0 for s in splits}
    total_images = {s: 0 for s in splits}

    target_8_indices = set()
    target_8_names = ["car", "chair", "door", "motorcycle", "person", "pole", "stairs", "table"]
    
    for idx, name in enumerate(class_names):
        if name.lower() in target_8_names:
            target_8_indices.add(idx)

    print(f"[*] Target 8 Class Indices: {target_8_indices}")

    for s in splits:
        labels_dir = os.path.join(EXTRACT_DIR, s, "labels")
        images_dir = os.path.join(EXTRACT_DIR, s, "images")
        
        if not os.path.exists(labels_dir):
            continue
            
        label_files = [f for f in os.listdir(labels_dir) if f.endswith('.txt')]
        total_images[s] = len(label_files)
        
        for lf in label_files:
            p = os.path.join(labels_dir, lf)
            has_target = False
            with open(p, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                for line in lines:
                    parts = line.split()
                    if parts:
                        cls_idx = int(parts[0])
                        split_stats[s][cls_idx] += 1
                        if cls_idx in target_8_indices:
                            has_target = True
            if has_target:
                images_with_target_8[s] += 1
            else:
                images_without_target_8[s] += 1

    print("\n" + "=" * 70)
    print("ROBOFLOW DATASET CLASS BREAKDOWN ACROSS SPLITS")
    print("=" * 70)
    print(f"{'Class ID':<10} {'Class Name':<16} {'Train':<10} {'Valid':<10} {'Test':<10} {'Total Boxes':<12} {'Target 8?'}")
    print("-" * 70)

    for idx, name in enumerate(class_names):
        tr = split_stats['train'][idx]
        va = split_stats['valid'][idx]
        te = split_stats['test'][idx]
        tot = tr + va + te
        is_target = "YES" if idx in target_8_indices else "NO (filtered)"
        print(f"{idx:<10} {name:<16} {tr:<10} {va:<10} {te:<10} {tot:<12} {is_target}")

    print("=" * 70)
    for s in splits:
        print(f"[{s:<5}] Total images: {total_images[s]:<6} | With Target 8: {images_with_target_8[s]:<6} | Only Other Classes: {images_without_target_8[s]:<6}")

if __name__ == "__main__":
    main()
