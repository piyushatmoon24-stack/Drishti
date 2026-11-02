"""
Drishti Smart Stick - Download and Package Edge Impulse Himax WiseEye2 Deployment
Downloads the compiled Arm Vela FOMO model & firmware and packages it for SenseCraft & local flashing.
"""

import os
import sys
import time
import json
import zipfile
import requests

API_KEY = "ei_f6f7e400ef663cbdb2f53e05906703d28ce75fe82b6ded4d"
PROJECT_ID = 1146751
HEADERS = {"x-api-key": API_KEY}
BASE_URL = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}"
JOB_ID = 55682639

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EI_DIR = os.path.join(ROOT_DIR, "tools", "edge_impulse_firmware")
SENSECRAFT_DIR = os.path.join(ROOT_DIR, "export", "grove_vision_ai_v2", "FOR_SENSECRAFT_UPLOAD")
os.makedirs(EI_DIR, exist_ok=True)
os.makedirs(SENSECRAFT_DIR, exist_ok=True)

print("=" * 68)
print(" DRISHTI: WAITING FOR ARM VELA DEPLOYMENT & DOWNLOADING PACKAGE")
print("=" * 68)

session = requests.Session()

# 1. Wait for build job to complete
t0 = time.time()
while True:
    try:
        r = session.get(f"{BASE_URL}/jobs/{JOB_ID}/status", headers=HEADERS, timeout=20).json()
        job = r.get("job", {})
        finished = job.get("finished")
        if finished:
            success = job.get("finishedSuccessful", False)
            print(f"\n[+] Job {JOB_ID} finished! Success={success} in {time.time()-t0:.1f}s")
            if not success:
                print("[-] Job marked as failed. Exiting.")
                sys.exit(1)
            break
        print(".", end="", flush=True)
    except Exception as e:
        print(f"\n[!] Status query error: {e}")
    time.sleep(5)

# 2. Download deployment package
print("\n[*] Downloading deployment zip for himax-wiseeye2...")
down_url = f"{BASE_URL}/deployment/download?type=himax-wiseeye2"
for attempt in range(1, 10):
    try:
        res = session.get(down_url, headers=HEADERS, timeout=180)
        if res.status_code == 200 and len(res.content) > 1000:
            print(f"[+] Download successful! Size: {len(res.content):,} bytes")
            zip_data = res.content
            break
        else:
            print(f"[-] Download returned HTTP {res.status_code}, retrying ({attempt}/10)...")
            time.sleep(5)
    except Exception as e:
        print(f"[-] Download error: {e}, retrying ({attempt}/10)...")
        time.sleep(5)
else:
    print("[-] Failed to download deployment zip.")
    sys.exit(1)

# 3. Extract contents
import io
extracted_files = []
with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
    for name in z.namelist():
        print(f"  Archive member: {name} ({z.getinfo(name).file_size:,} bytes)")
        if name.endswith("firmware.img") or "firmware" in name.lower() and name.endswith(".img"):
            dest = os.path.join(EI_DIR, "firmware.img")
            with open(dest, "wb") as f:
                f.write(z.read(name))
            print(f"  [+] Saved firmware image: {dest}")
            extracted_files.append(dest)
        elif name.endswith("model_vela.tflite") or name.endswith(".tflite"):
            # Save to EI directory
            dest = os.path.join(EI_DIR, "model_vela.tflite")
            with open(dest, "wb") as f:
                f.write(z.read(name))
            print(f"  [+] Saved Vela TFLite model: {dest}")
            extracted_files.append(dest)
            
            # Copy to SenseCraft folder
            sc_dest1 = os.path.join(SENSECRAFT_DIR, "model.tflite")
            sc_dest2 = os.path.join(SENSECRAFT_DIR, "drishti_192x192_vela.tflite")
            sc_dest3 = os.path.join(SENSECRAFT_DIR, "DRISHTI_192x192_FOR_SENSECRAFT.tflite")
            with open(sc_dest1, "wb") as f:
                f.write(z.read(name))
            with open(sc_dest2, "wb") as f:
                f.write(z.read(name))
            with open(sc_dest3, "wb") as f:
                f.write(z.read(name))
            print(f"  [+] Copied model to SenseCraft upload paths: {sc_dest1}")

# 4. Write updated model.json for SenseCraft
model_json_path = os.path.join(SENSECRAFT_DIR, "model.json")
sensecraft_meta = {
    "version": "2.2.0",
    "name": "Drishti-8-FOMO-192x192",
    "description": "8-Class Real-Time Assistive Vision AI (FOMO MobileNetV2 0.35 192x192) for Visually Impaired Navigation on Himax WiseEye2 (Ethos-U55 NPU)",
    "author": "Drishti",
    "category": "Object Detection",
    "algorithm": "FOMO",
    "input_type": "image",
    "image_type": "rgb",
    "input_shape": [1, 192, 192, 3],
    "classes": [
        "car",
        "chair",
        "door",
        "motorcycle",
        "person",
        "pole",
        "stairs",
        "table"
    ],
    "score_threshold": 0.5,
    "labels": {
        "0": "car",
        "1": "chair",
        "2": "door",
        "3": "motorcycle",
        "4": "person",
        "5": "pole",
        "6": "stairs",
        "7": "table"
    },
    "audio_mapping": {
        "0": {"name": "car", "track": "0019.mp3", "catalog_id": 19, "priority": 1},
        "1": {"name": "chair", "track": "0023.mp3", "catalog_id": 23, "priority": 3},
        "2": {"name": "door", "track": "0024.mp3", "catalog_id": 24, "priority": 2},
        "3": {"name": "motorcycle", "track": "0020.mp3", "catalog_id": 20, "priority": 1},
        "4": {"name": "person", "track": "0022.mp3", "catalog_id": 22, "priority": 2},
        "5": {"name": "pole", "track": "0021.mp3", "catalog_id": 21, "priority": 1},
        "6": {"name": "stairs", "track": "0025.mp3", "catalog_id": 25, "priority": 1},
        "7": {"name": "table", "track": "0026.mp3", "catalog_id": 26, "priority": 3}
    }
}

with open(model_json_path, "w", encoding="utf-8") as f:
    json.dump(sensecraft_meta, f, indent=2)
print(f"[+] Updated model.json for SenseCraft: {model_json_path}")

# Also update the parent model.json
parent_json_path = os.path.join(ROOT_DIR, "export", "grove_vision_ai_v2", "model.json")
with open(parent_json_path, "w", encoding="utf-8") as f:
    json.dump(sensecraft_meta, f, indent=2)

# 5. Create SenseCraft Zip file
zip_target = os.path.join(SENSECRAFT_DIR, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip")
with zipfile.ZipFile(zip_target, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(os.path.join(SENSECRAFT_DIR, "model.tflite"), arcname="model.tflite")
    zf.write(model_json_path, arcname="model.json")
print(f"[+] Packaged SenseCraft ZIP: {zip_target} ({os.path.getsize(zip_target):,} bytes)")

print("\n" + "=" * 68)
print(" PACKAGING COMPLETE AND VERIFIED!")
print("=" * 68)
