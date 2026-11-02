"""
Drishti Smart Stick - v4 Dataset Ingestion Pipeline for Edge Impulse
1. Filters 'new data set .v4i.yolov8.zip' strictly for the 8 target classes:
   [car, chair, motorcycle, person, pole, table, door, stairs].
2. Filters out images with 0 target classes or > 2 target classes per image.
3. Resets old 128x128 data in Edge Impulse Project 1146751.
4. Accurately converts YOLO normalized coordinates to 416x416 pixel bounding boxes.
5. Ingests clean samples into Edge Impulse (train -> training, valid/test -> testing).
"""

import os
import sys
import json
import time
import zipfile
import requests
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API_KEY = "ei_f6f7e400ef663cbdb2f53e05906703d28ce75fe82b6ded4d"
PROJECT_ID = 1146751
HEADERS = {"x-api-key": API_KEY}
BASE_URL = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}"
INGEST_URL = "https://ingestion.edgeimpulse.com/api"

ZIP_PATH = os.path.abspath(r"datasets\new data set .v4i.yolov8.zip")
IMG_WIDTH = 416
IMG_HEIGHT = 416

TARGET_NAMES = {
    0: 'car',
    1: 'chair',
    2: 'motorcycle',
    3: 'person',
    4: 'pole',
    5: 'table',
    6: 'door',
    7: 'stairs'
}

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=30, pool_maxsize=30, max_retries=3)
session.mount("https://", adapter)

def parse_yolo_boxes(lines, img_w=IMG_WIDTH, img_h=IMG_HEIGHT):
    boxes = []
    classes_present = set()
    has_unknown = False

    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        try:
            cls_id = int(parts[0])
            if cls_id not in TARGET_NAMES:
                has_unknown = True
                continue
            lbl = TARGET_NAMES[cls_id]
            classes_present.add(lbl)
            
            coords = [float(x) for x in parts[1:5]]
            if len(coords) == 4:
                xc, yc, w, h = coords
                x = int(round((xc - w / 2.0) * img_w))
                y = int(round((yc - h / 2.0) * img_h))
                bw = int(round(w * img_w))
                bh = int(round(h * img_h))
                
                # Clip to image boundaries
                x = max(0, min(img_w - 1, x))
                y = max(0, min(img_h - 1, y))
                bw = max(1, min(img_w - x, bw))
                bh = max(1, min(img_h - y, bh))
                
                boxes.append({"label": lbl, "x": x, "y": y, "width": bw, "height": bh})
        except Exception:
            pass

    return boxes, classes_present, has_unknown

def filter_and_build_manifest():
    print("=" * 72)
    print(" STEP 1: SCANNING & FILTERING v4 DATASET (416x416)")
    print("=" * 72)
    print(f"[*] Dataset Archive: {ZIP_PATH}")
    
    if not os.path.exists(ZIP_PATH):
        raise FileNotFoundError(f"Archive not found: {ZIP_PATH}")

    items_to_upload = []
    stats = {
        "total_labels": 0,
        "rejected_unknown": 0,
        "rejected_zero_classes": 0,
        "rejected_over_2_classes": 0,
        "passed_train": 0,
        "passed_valid": 0,
        "passed_test": 0,
        "class_box_counts": Counter(),
        "class_img_counts": Counter()
    }

    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        names = z.namelist()
        label_files = [f for f in names if f.endswith('.txt') and ('/labels/' in f or '\\labels\\' in f)]
        stats["total_labels"] = len(label_files)
        print(f"[*] Total label files found: {len(label_files)}")

        for lf in label_files:
            # Determine split
            split = lf.split('/')[0] if '/' in lf else lf.split('\\')[0]
            img_name = lf.replace('/labels/', '/images/').replace('\\labels\\', '\\images\\')
            # Handle potential extension variants
            img_path_in_zip = None
            for ext in ['.jpg', '.jpeg', '.png']:
                cand = img_name[:-4] + ext
                try:
                    z.getinfo(cand)
                    img_path_in_zip = cand
                    break
                except KeyError:
                    pass

            if not img_path_in_zip:
                continue

            content = z.read(lf).decode('utf-8', errors='replace').strip()
            lines = [l.strip() for l in content.splitlines() if l.strip()]

            boxes, classes_present, has_unknown = parse_yolo_boxes(lines)

            # Filter 1: reject if unknown class
            if has_unknown:
                stats["rejected_unknown"] += 1
                continue

            # Filter 2: reject if 0 target classes
            if len(classes_present) == 0 or len(boxes) == 0:
                stats["rejected_zero_classes"] += 1
                continue

            # Filter 3: reject if > 2 distinct target classes
            if len(classes_present) > 2:
                stats["rejected_over_2_classes"] += 1
                continue

            # Assign category: train -> training, valid & test -> testing
            category = "training" if split == "train" else "testing"
            if split == "train":
                stats["passed_train"] += 1
            elif split == "valid":
                stats["passed_valid"] += 1
            else:
                stats["passed_test"] += 1

            for c in classes_present:
                stats["class_img_counts"][c] += 1
            for b in boxes:
                stats["class_box_counts"][b["label"]] += 1

            raw_bytes = z.read(img_path_in_zip)
            fn = os.path.basename(img_path_in_zip)

            items_to_upload.append({
                "category": category,
                "filename": fn,
                "data": raw_bytes,
                "boxes": boxes,
                "primary_label": boxes[0]["label"]
            })

    print(f"\n[+] Filtering Complete:")
    print(f"    - Total Label Files Scanned: {stats['total_labels']}")
    print(f"    - Rejected (0 target classes): {stats['rejected_zero_classes']}")
    print(f"    - Rejected (> 2 classes in image): {stats['rejected_over_2_classes']}")
    print(f"    - Passed Training Split: {stats['passed_train']}")
    print(f"    - Passed Testing Split (valid + test): {stats['passed_valid'] + stats['passed_test']} ({stats['passed_valid']} val + {stats['passed_test']} test)")
    print(f"    - TOTAL IMAGES TO UPLOAD: {len(items_to_upload)}")
    print("\n[+] Target Class Breakdown in Filtered Set:")
    for c in ['car', 'chair', 'door', 'motorcycle', 'person', 'pole', 'stairs', 'table']:
        print(f"    {c:<12}: {stats['class_img_counts'][c]:>5} images | {stats['class_box_counts'][c]:>5} bounding boxes")

    return items_to_upload

def reset_project_data():
    print("\n" + "=" * 72)
    print(f" STEP 2: PURGING OLD 128x128 DATA IN PROJECT {PROJECT_ID}")
    print("=" * 72)
    r1 = session.post(f"{BASE_URL}/raw-data/delete-all/training", headers=HEADERS, timeout=30).json()
    r2 = session.post(f"{BASE_URL}/raw-data/delete-all/testing", headers=HEADERS, timeout=30).json()
    print(f"[*] Reset Training Data: {r1.get('success')}")
    print(f"[*] Reset Testing Data:  {r2.get('success')}")
    time.sleep(3)

def upload_single_sample(item):
    category = item["category"]
    filename = item["filename"]
    raw_bytes = item["data"]
    boxes = item["boxes"]
    label = item["primary_label"]

    url = f"{INGEST_URL}/{category}/files"
    headers = {
        "x-api-key": API_KEY,
        "x-label": label,
        "x-file-name": filename,
        "x-bounding-boxes": json.dumps(boxes)
    }

    for attempt in range(1, 5):
        try:
            files = [('data', (filename, raw_bytes, 'image/jpeg'))]
            r = session.post(url, headers=headers, files=files, timeout=40)
            if r.status_code == 200 and r.json().get("success"):
                return True, filename
            time.sleep(0.3 * attempt)
        except Exception:
            time.sleep(0.6 * attempt)
    return False, filename

def upload_all_samples(items):
    print("\n" + "=" * 72)
    print(f" STEP 3: PARALLEL UPLOADING {len(items)} FILTERED 416x416 SAMPLES")
    print("=" * 72)

    t0 = time.time()
    uploaded = 0
    failed = 0
    total_items = len(items)

    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(upload_single_sample, item): item for item in items}
        for future in as_completed(futures):
            ok, fn = future.result()
            if ok:
                uploaded += 1
            else:
                failed += 1

            total = uploaded + failed
            if total % 250 == 0 or total == total_items:
                speed = total / max(0.1, (time.time() - t0))
                remaining = (total_items - total) / max(0.1, speed)
                print(f"    Progress: {total:>5}/{total_items} ({uploaded} ok, {failed} fail) - {speed:.1f} img/s - ETA: {remaining:.0f}s", flush=True)

    print(f"\n[+] Finished Ingestion: {uploaded} successfully uploaded, {failed} failed in {time.time()-t0:.1f}s!")

def verify_dataset_in_edge_impulse():
    print("\n" + "=" * 72)
    print(" STEP 4: VERIFYING PROJECT INGESTION STATUS")
    print("=" * 72)
    r_tr = session.get(f"{BASE_URL}/raw-data/count", headers=HEADERS, params={"category": "training"}).json()
    r_te = session.get(f"{BASE_URL}/raw-data/count", headers=HEADERS, params={"category": "testing"}).json()
    tr_cnt = r_tr.get("count", 0)
    te_cnt = r_te.get("count", 0)
    print(f"[+] Edge Impulse Live Count:")
    print(f"    - Training Set: {tr_cnt:>5} images")
    print(f"    - Testing Set:  {te_cnt:>5} images")
    print(f"    - Total Images: {tr_cnt + te_cnt:>5} images")
    
    # Check sample bounding boxes
    r_samp = session.get(f"{BASE_URL}/raw-data", headers=HEADERS, params={"category": "training", "limit": 3}).json()
    samples = r_samp.get("samples", [])
    print(f"\n[+] Verified Sample Annotations:")
    for s in samples:
        print(f"    - {s.get('filename')}: {s.get('boundingBoxes')}")

def main():
    items = filter_and_build_manifest()
    reset_project_data()
    upload_all_samples(items)
    verify_dataset_in_edge_impulse()
    print("\n" + "=" * 72)
    print(" ALL DATASET INGESTION TASKS COMPLETED SUCCESSFULLY!")
    print("=" * 72)

if __name__ == "__main__":
    main()
