"""
Drishti Smart Stick - Balanced Dataset Generator, Cloud Trainer & Vela Deployment Pipeline
1. Selects an optimally balanced dataset (~750 images per class, including all 629 pole images).
2. Preserves native 128x128 resolution for enhanced spatial feature extraction on Ethos-U55 NPU.
3. Resets Edge Impulse Project 1146751 and parallel-uploads the clean balanced dataset.
4. Generates DSP features, trains FOMO MobileNetV2 0.35, compiles with Arm Vela, and evaluates.
"""

import os
import sys
import json
import time
import random
import zipfile
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(line_buffering=True)

random.seed(42)

API_KEY = "ei_f6f7e400ef663cbdb2f53e05906703d28ce75fe82b6ded4d"
PROJECT_ID = 1146751
HEADERS = {"x-api-key": API_KEY}
BASE_URL = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}"
INGEST_URL = "https://ingestion.edgeimpulse.com/api"
ZIP_PATH = os.path.abspath(r"datasets\My First Project.v3i.yolov8.zip")
OUTPUT_DIR = os.path.abspath(r"tools\edge_impulse_firmware")

TARGET_NAMES = {0: 'car', 1: 'chair', 5: 'motorcycle', 6: 'person', 7: 'pole', 9: 'table', 11: 'door', 12: 'stairs'}
PRIORITY_ORDER = ['pole', 'motorcycle', 'door', 'chair', 'car', 'table', 'stairs', 'person']
TARGET_PER_CLASS = 750

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=35, pool_maxsize=35, max_retries=3)
session.mount("https://", adapter)

def parse_boxes_from_text(lines, img_w=128, img_h=128):
    boxes = []
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        try:
            cls_id = int(parts[0])
            if cls_id not in TARGET_NAMES:
                continue
            lbl = TARGET_NAMES[cls_id]
            coords = [float(x) for x in parts[1:]]
            if len(coords) == 4:
                xc, yc, w, h = coords
                x = int(round((xc - w / 2.0) * img_w))
                y = int(round((yc - h / 2.0) * img_h))
                bw = int(round(w * img_w))
                bh = int(round(h * img_h))
            elif len(coords) >= 6:
                xs = coords[0::2]
                ys = coords[1::2]
                min_x = min(xs)
                max_x = max(xs)
                min_y = min(ys)
                max_y = max(ys)
                x = int(round(min_x * img_w))
                y = int(round(min_y * img_h))
                bw = int(round((max_x - min_x) * img_w))
                bh = int(round((max_y - min_y) * img_h))
            else:
                continue

            x = max(0, min(img_w - 1, x))
            y = max(0, min(img_h - 1, y))
            bw = max(1, min(img_w - x, bw))
            bh = max(1, min(img_h - y, bh))

            boxes.append({"label": lbl, "x": x, "y": y, "width": bw, "height": bh})
        except Exception:
            pass
    return boxes

def build_balanced_dataset_manifest():
    print("=" * 68, flush=True)
    print(" STEP 1: SELECTING BALANCED 700-750 SAMPLES PER CLASS", flush=True)
    print("=" * 68, flush=True)

    image_to_classes = defaultdict(set)
    image_to_label_lines = {}

    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        for name in z.namelist():
            if name.endswith('.txt') and ('/labels/' in name or '\\labels\\' in name):
                img_name = name.replace('/labels/', '/images/').replace('.txt', '.jpg')
                try:
                    z.getinfo(img_name)
                except KeyError:
                    continue

                lines = z.read(name).decode('utf-8', errors='ignore').strip().splitlines()
                classes_in_img = set()
                for l in lines:
                    parts = l.strip().split()
                    if parts and int(parts[0]) in TARGET_NAMES:
                        classes_in_img.add(TARGET_NAMES[int(parts[0])])

                if classes_in_img:
                    image_to_classes[img_name] = classes_in_img
                    image_to_label_lines[img_name] = lines

    print(f"[*] Total target images available: {len(image_to_classes)}", flush=True)

    selected_images = set()
    class_counts = defaultdict(int)

    # 1. Add all pole images (629)
    for img, classes in image_to_classes.items():
        if 'pole' in classes:
            selected_images.add(img)
            for c in classes:
                class_counts[c] += 1

    # 2. Add remaining classes in priority order up to TARGET_PER_CLASS (750)
    for target_c in PRIORITY_ORDER[1:]:
        candidates = [img for img, classes in image_to_classes.items() if target_c in classes and img not in selected_images]
        random.shuffle(candidates)
        needed = TARGET_PER_CLASS - class_counts[target_c]
        if needed > 0:
            to_add = candidates[:needed]
            for img in to_add:
                selected_images.add(img)
                for c in image_to_classes[img]:
                    class_counts[c] += 1

    print("\n[+] Balanced Dataset Class Breakdown:")
    for c in PRIORITY_ORDER:
        print(f"    {c:<12}: {class_counts[c]} images", flush=True)
    print(f"[*] Total unique balanced images selected: {len(selected_images)}", flush=True)

    # 3. Create 85% train / 15% test split
    selected_list = list(selected_images)
    random.shuffle(selected_list)
    split_idx = int(0.85 * len(selected_list))
    train_imgs = selected_list[:split_idx]
    test_imgs = selected_list[split_idx:]

    print(f"[+] Train Split: {len(train_imgs)} images | Test Split: {len(test_imgs)} images", flush=True)

    # Prepare upload manifests
    upload_items = []
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        for img_name in train_imgs:
            lines = image_to_label_lines[img_name]
            boxes = parse_boxes_from_text(lines)
            if not boxes: continue
            raw_bytes = z.read(img_name)
            fn = os.path.basename(img_name)
            upload_items.append({
                "category": "training",
                "filename": fn,
                "data": raw_bytes,
                "boxes": boxes,
                "label": boxes[0]["label"]
            })

        for img_name in test_imgs:
            lines = image_to_label_lines[img_name]
            boxes = parse_boxes_from_text(lines)
            if not boxes: continue
            raw_bytes = z.read(img_name)
            fn = os.path.basename(img_name)
            upload_items.append({
                "category": "testing",
                "filename": fn,
                "data": raw_bytes,
                "boxes": boxes,
                "label": boxes[0]["label"]
            })

    return upload_items

def reset_project_data():
    print("\n" + "=" * 68, flush=True)
    print(" STEP 2: WIPING OLD DATA IN EDGE IMPULSE PROJECT 1146751", flush=True)
    print("=" * 68, flush=True)

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
    label = item["label"]

    url = f"{INGEST_URL}/{category}/files"
    headers = {
        "x-api-key": API_KEY,
        "x-label": label,
        "x-file-name": filename,
        "x-bounding-boxes": json.dumps(boxes)
    }

    for attempt in range(1, 5):
        try:
            files = [('data', (filename, raw_bytes, 'multipart/form-data'))]
            r = session.post(url, headers=headers, files=files, timeout=35)
            if r.status_code == 200 and r.json().get("success"):
                return True, filename
            time.sleep(0.4 * attempt)
        except Exception:
            time.sleep(0.8 * attempt)
    return False, filename

def upload_balanced_dataset(items):
    print("\n" + "=" * 68, flush=True)
    print(f" STEP 3: PARALLEL UPLOADING {len(items)} BALANCED 128x128 SAMPLES", flush=True)
    print("=" * 68, flush=True)

    t0 = time.time()
    uploaded = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(upload_single_sample, item): item for item in items}
        for future in as_completed(futures):
            ok, fn = future.result()
            if ok: uploaded += 1
            else: failed += 1

            total = uploaded + failed
            if total % 200 == 0 or total == len(items):
                speed = total / (time.time() - t0)
                print(f"    Upload Progress: {total}/{len(items)} ({uploaded} ok, {failed} fail) - {speed:.1f} img/s", flush=True)

    print(f"[+] Finished uploading {uploaded} samples in {time.time()-t0:.1f}s!", flush=True)

def run_feature_generation():
    print("\n" + "=" * 68, flush=True)
    print(" STEP 4: GENERATING 128x128 DSP FEATURE MATRICES", flush=True)
    print("=" * 68, flush=True)

    r = session.post(f"{BASE_URL}/jobs/generate-features", headers=HEADERS, 
                     json={"dspId": 2, "skipFeatureExplorer": True}, timeout=25).json()
    if not r.get("success"):
        print(f"[-] Feature generation trigger failed: {r}")
        return False

    job_id = r.get("id")
    print(f"[+] DSP Feature Generation started (Job ID: {job_id})", flush=True)

    t0 = time.time()
    while True:
        time.sleep(6)
        try:
            status = session.get(f"{BASE_URL}/jobs/{job_id}/status", headers=HEADERS, timeout=20).json()
            if status.get("job", {}).get("finished"):
                print(f"\n[+] Feature generation completed in {time.time()-t0:.1f}s!", flush=True)
                break
            print(".", end="", flush=True)
        except Exception:
            pass

    return True

def run_model_training():
    print("\n" + "=" * 68, flush=True)
    print(" STEP 5: TRAINING FOMO MOBILENETV2 0.35 AT 128x128 RESOLUTION", flush=True)
    print("=" * 68, flush=True)

    train_payload = {
        "trainingCycles": 45,
        "learningRate": 0.001,
        "batchSize": 128
    }

    r = session.post(f"{BASE_URL}/jobs/train/keras/3", headers=HEADERS, json=train_payload, timeout=25).json()
    if not r.get("success"):
        print(f"[-] Training trigger failed: {r}")
        return False

    job_id = r.get("id")
    print(f"[+] Model Training Job started (Job ID: {job_id})", flush=True)

    t0 = time.time()
    seen_lines = set()
    while True:
        time.sleep(8)
        try:
            status = session.get(f"{BASE_URL}/jobs/{job_id}/status", headers=HEADERS, timeout=20).json()
            finished = status.get("job", {}).get("finished")

            stdout_res = session.get(f"{BASE_URL}/jobs/{job_id}/stdout", headers=HEADERS, timeout=20).json()
            logs = stdout_res.get("stdout", [])
            for item in logs[:15]:
                text = item.get("data", "").strip() if isinstance(item, dict) else str(item).strip()
                if not text or text in seen_lines:
                    continue
                seen_lines.add(text)
                if any(k in text for k in ["Epoch", "loss", "accuracy", "Precision", "Recall", "F1", "Finished"]):
                    print(f"    [Training] {text}", flush=True)

            if finished:
                print(f"\n[+] Training completed in {time.time()-t0:.1f}s!", flush=True)
                break
        except Exception:
            pass

    return True

def compile_and_download_vela():
    print("\n" + "=" * 68, flush=True)
    print(" STEP 6: ARM VELA NPU COMPILATION & DOWNLOAD", flush=True)
    print("=" * 68, flush=True)

    r = session.post(f"{BASE_URL}/jobs/build-ondevice-model?type=himax-wiseeye2", 
                     headers=HEADERS, json={"engine": "tflite"}, timeout=25).json()
    if not r.get("success"):
        print(f"[-] Vela build trigger failed: {r}")
        return False

    job_id = r.get("id")
    print(f"[+] Arm Vela NPU compilation started (Job ID: {job_id})", flush=True)

    t0 = time.time()
    while True:
        time.sleep(8)
        try:
            status = session.get(f"{BASE_URL}/jobs/{job_id}/status", headers=HEADERS, timeout=20).json()
            if status.get("job", {}).get("finished"):
                print(f"\n[+] Arm Vela compilation finished in {time.time()-t0:.1f}s!", flush=True)
                break
            print(".", end="", flush=True)
        except Exception:
            pass

    print("[*] Downloading Himax WiseEye2 deployment package...", flush=True)
    down_url = f"{BASE_URL}/deployment/download?type=himax-wiseeye2"
    r = session.get(down_url, headers=HEADERS, timeout=120)
    if r.status_code != 200:
        print(f"[-] Download failed: HTTP {r.status_code}")
        return False

    import io
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for name in z.namelist():
            if name.endswith("model_vela.tflite") or name.endswith(".tflite"):
                target = os.path.join(OUTPUT_DIR, "model_vela.tflite")
                with open(target, "wb") as f:
                    f.write(z.read(name))
                print(f"[+] Downloaded & extracted fresh model: {target} ({os.path.getsize(target):,} bytes)", flush=True)
                return True

    return False

def evaluate_test_set():
    print("\n" + "=" * 68, flush=True)
    print(" STEP 7: INDEPENDENT TEST SET EVALUATION", flush=True)
    print("=" * 68, flush=True)

    r = session.post(f"{BASE_URL}/jobs/classify", headers=HEADERS, json={}, timeout=25).json()
    if not r.get("success"):
        print(f"[-] Test classify job trigger failed: {r}")
        return

    job_id = r.get("id")
    print(f"[+] Test classification started (Job ID: {job_id})", flush=True)

    while True:
        time.sleep(5)
        try:
            status = session.get(f"{BASE_URL}/jobs/{job_id}/status", headers=HEADERS, timeout=20).json()
            if status.get("job", {}).get("finished"):
                print("\n[+] Test classification completed!", flush=True)
                break
            print(".", end="", flush=True)
        except Exception:
            pass

    # Run the metrics evaluator
    os.system("python tools/compute_test_metrics.py")

def main():
    print("=" * 68, flush=True)
    print(" DRISHTI: BALANCED 128x128 MODEL TRAINING & VELA COMPILATION", flush=True)
    print("=" * 68, flush=True)

    upload_items = build_balanced_dataset_manifest()
    reset_project_data()
    upload_balanced_dataset(upload_items)

    if not run_feature_generation():
        print("[-] Aborted.")
        return

    if not run_model_training():
        print("[-] Aborted.")
        return

    if not compile_and_download_vela():
        print("[-] Aborted.")
        return

    evaluate_test_set()

    print("\n" + "=" * 68, flush=True)
    print(" ALL TASKS COMPLETED SUCCESSFULLY!", flush=True)
    print("=" * 68, flush=True)

if __name__ == "__main__":
    main()
