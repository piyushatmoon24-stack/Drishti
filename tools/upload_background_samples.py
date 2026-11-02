"""
Drishti Smart Stick - Background Images Ingestion for Edge Impulse
Uploads 250 pure negative (background) images with zero bounding boxes
into the training set of Edge Impulse Project 1146751.
"""

import os
import sys
import json
import time
import random
import zipfile
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

random.seed(42)

API_KEY = "ei_f6f7e400ef663cbdb2f53e05906703d28ce75fe82b6ded4d"
PROJECT_ID = 1146751
HEADERS = {"x-api-key": API_KEY}
BASE_URL = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}"
INGEST_URL = "https://ingestion.edgeimpulse.com/api"

ZIP_PATH = os.path.abspath(r"datasets\new data set .v4i.yolov8.zip")
NUM_BACKGROUND_SAMPLES = 250

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=25, pool_maxsize=25, max_retries=3)
session.mount("https://", adapter)

def upload_single_bg(item):
    filename = item["filename"]
    raw_bytes = item["data"]
    url = f"{INGEST_URL}/training/files"
    
    headers = {
        "x-api-key": API_KEY,
        "x-file-name": filename,
        "x-bounding-boxes": json.dumps([])  # Zero bounding boxes = pure negative sample
    }

    for attempt in range(1, 4):
        try:
            files = [('data', (filename, raw_bytes, 'image/jpeg'))]
            r = session.post(url, headers=headers, files=files, timeout=30)
            if r.status_code == 200 and r.json().get("success"):
                return True, filename
            time.sleep(0.3 * attempt)
        except Exception:
            time.sleep(0.5 * attempt)
    return False, filename

def main():
    print("=" * 72)
    print(f" SELECTING & UPLOADING {NUM_BACKGROUND_SAMPLES} PURE BACKGROUND IMAGES")
    print("=" * 72)

    if not os.path.exists(ZIP_PATH):
        raise FileNotFoundError(f"Zip file not found: {ZIP_PATH}")

    empty_train_candidates = []
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        for name in z.namelist():
            if name.startswith('train/labels/') and name.endswith('.txt'):
                content = z.read(name).decode('utf-8', errors='replace').strip()
                if not content:  # Zero bounding boxes in label
                    img_cand = name.replace('/labels/', '/images/')[:-4] + '.jpg'
                    try:
                        z.getinfo(img_cand)
                        empty_train_candidates.append(img_cand)
                    except KeyError:
                        pass

    print(f"[*] Found {len(empty_train_candidates)} empty background candidate images in train set.")
    random.shuffle(empty_train_candidates)
    selected_bg_files = empty_train_candidates[:NUM_BACKGROUND_SAMPLES]

    print(f"[*] Selected {len(selected_bg_files)} background images for upload.")

    # Read bytes from zip
    upload_items = []
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        for p in selected_bg_files:
            b = z.read(p)
            fn = "bg_" + os.path.basename(p)
            upload_items.append({"filename": fn, "data": b})

    # Initial count
    r_tr_before = session.get(f"{BASE_URL}/raw-data/count", headers=HEADERS, params={"category": "training"}).json()
    count_before = r_tr_before.get("count", 0)
    print(f"[*] Current Training Set Count: {count_before}")

    t0 = time.time()
    uploaded = 0
    failed = 0

    print(f"\n[*] Uploading {len(upload_items)} background images to /training/files...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(upload_single_bg, it): it for it in upload_items}
        for future in as_completed(futures):
            ok, fn = future.result()
            if ok:
                uploaded += 1
            else:
                failed += 1

            total = uploaded + failed
            if total % 50 == 0 or total == len(upload_items):
                speed = total / max(0.1, time.time() - t0)
                print(f"    Uploaded: {total:>3}/{len(upload_items)} ({uploaded} ok, {failed} fail) - {speed:.1f} img/s", flush=True)

    time.sleep(2)
    r_tr_after = session.get(f"{BASE_URL}/raw-data/count", headers=HEADERS, params={"category": "training"}).json()
    count_after = r_tr_after.get("count", 0)

    print("\n" + "=" * 72)
    print(" BACKGROUND INGESTION COMPLETE")
    print("=" * 72)
    print(f"[+] Successfully uploaded: {uploaded} background images ({failed} failed)")
    print(f"[+] Previous training count: {count_before}")
    print(f"[+] New training count:      {count_after} (Net increase: +{count_after - count_before})")

if __name__ == "__main__":
    main()
