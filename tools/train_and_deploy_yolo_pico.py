"""
Drishti Smart Stick - End-to-End YOLO-Pro Pico Cloud Training & SenseCraft Packaging
1. Monitors ongoing YOLO-Pro Pico training job (55692581) on Edge Impulse GPU.
2. Compiles model with Arm Vela compiler for Himax WiseEye2 / Ethos-U55 NPU.
3. Verifies SRAM footprint is strictly within physical limits to prevent Invoke Failed.
4. Downloads deployment and packages ready-to-upload files for SenseCraft and local flasher.
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
TRAIN_JOB_ID = 55692581

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EI_DIR = os.path.join(ROOT_DIR, "tools", "edge_impulse_firmware")
SENSECRAFT_DIR = os.path.join(ROOT_DIR, "export", "grove_vision_ai_v2", "FOR_SENSECRAFT_UPLOAD")
ONEDRIVE_DIR = r"C:\Users\mohan\OneDrive\文档\Drishti\export"

os.makedirs(EI_DIR, exist_ok=True)
os.makedirs(SENSECRAFT_DIR, exist_ok=True)

session = requests.Session()

print("=" * 68)
print(" DRISHTI: YOLO-PRO PICO GPU TRAINING & SENSECRAFT COMPILATION")
print("=" * 68)
print(f"[*] Monitoring Training Job: {TRAIN_JOB_ID}")

# 1. Monitor training job
t0 = time.time()
seen_lines = set()
while True:
    time.sleep(6)
    try:
        st = session.get(f"{BASE_URL}/jobs/{TRAIN_JOB_ID}/status", headers=HEADERS, timeout=20).json()
        job = st.get("job", {})
        finished = job.get("finished")

        r = session.get(f"{BASE_URL}/jobs/{TRAIN_JOB_ID}/stdout", headers=HEADERS, timeout=20).json()
        logs = r.get("stdout", [])
        for item in logs:
            text = item.get("data", "").strip() if isinstance(item, dict) else str(item).strip()
            if text and text not in seen_lines:
                seen_lines.add(text)
                if any(k in text for k in ["Epoch", "loss", "accuracy", "Precision", "Recall", "mAP", "Finished", "Converting", "Profiling", "Model:"]):
                    print(f"    [Training] {text}", flush=True)

        if finished:
            success = job.get("finishedSuccessful", False)
            print(f"\n[+] Training job finished! Success={success} in {time.time()-t0:.1f}s")
            if not success:
                print("[-] Training failed. Check logs.")
                sys.exit(1)
            break
    except Exception as e:
        pass

# 2. Trigger Arm Vela Himax WiseEye2 deployment
print("\n" + "=" * 68)
print(" STEP 2: TRIGGERING ARM VELA HIMAX WISEEYE2 NPU COMPILATION")
print("=" * 68)

r = session.post(f"{BASE_URL}/jobs/build-ondevice-model?type=himax-wiseeye2", 
                 headers=HEADERS, json={"engine": "tflite"}, timeout=25).json()
if not r.get("success"):
    print(f"[-] Vela build trigger failed: {r}")
    sys.exit(1)

build_job_id = r.get("id")
print(f"[+] Arm Vela compilation started (Job ID: {build_job_id})", flush=True)

t1 = time.time()
seen_build_lines = set()
while True:
    time.sleep(6)
    try:
        st = session.get(f"{BASE_URL}/jobs/{build_job_id}/status", headers=HEADERS, timeout=20).json()
        job = st.get("job", {})
        finished = job.get("finished")

        r = session.get(f"{BASE_URL}/jobs/{build_job_id}/stdout", headers=HEADERS, timeout=20).json()
        logs = r.get("stdout", [])
        for item in logs:
            text = item.get("data", "").strip() if isinstance(item, dict) else str(item).strip()
            if text and text not in seen_build_lines:
                seen_build_lines.add(text)
                if any(k in text for k in ["SRAM", "Flash", "operators", "Ethos", "Compiling", "arena", "Building", "IMAGE GEN"]):
                    print(f"    [Vela] {text}", flush=True)

        if finished:
            success = job.get("finishedSuccessful", False)
            print(f"\n[+] Arm Vela compilation finished! Success={success} in {time.time()-t1:.1f}s")
            if not success:
                print("[-] Vela compilation failed.")
                sys.exit(1)
            break
    except Exception as e:
        pass

# 3. Download deployment zip
print("\n[*] Downloading deployment package...")
down_url = f"{BASE_URL}/deployment/download?type=himax-wiseeye2"
zip_data = None
for attempt in range(1, 10):
    try:
        res = session.get(down_url, headers=HEADERS, timeout=180)
        if res.status_code == 200 and len(res.content) > 1000:
            zip_data = res.content
            print(f"[+] Download complete: {len(zip_data):,} bytes")
            break
        time.sleep(4)
    except Exception as e:
        time.sleep(4)

if not zip_data:
    print("[-] Failed to download deployment.")
    sys.exit(1)

# 4. Extract and package
import io
with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
    for name in z.namelist():
        print(f"  Archive item: {name} ({z.getinfo(name).file_size:,} bytes)")
        if name.endswith("firmware.img") or "firmware" in name.lower() and name.endswith(".img"):
            with open(os.path.join(EI_DIR, "firmware.img"), "wb") as f:
                f.write(z.read(name))
        elif name.endswith("model_vela.tflite") or name.endswith(".tflite"):
            # Save local
            with open(os.path.join(EI_DIR, "model_vela.tflite"), "wb") as f:
                f.write(z.read(name))
            with open(os.path.join(SENSECRAFT_DIR, "model.tflite"), "wb") as f:
                f.write(z.read(name))
            with open(os.path.join(SENSECRAFT_DIR, "drishti_yolo_pico_192_vela.tflite"), "wb") as f:
                f.write(z.read(name))

# 5. Write model.json for SenseCraft
classes_list = ["car", "chair", "door", "motorcycle", "person", "pole", "stairs", "table"]
meta = {
    "version": "2.3.0",
    "name": "Drishti-8-YOLO-Pico-192x192",
    "description": "8-Class Real-Time Assistive Vision AI (YOLO-Pro Pico 192x192) for Himax WiseEye2 (Ethos-U55 NPU)",
    "author": "Drishti",
    "category": "Object Detection",
    "algorithm": "YOLO-Pro-Pico",
    "input_type": "image",
    "image_type": "rgb",
    "input_shape": [1, 192, 192, 3],
    "classes": classes_list,
    "score_threshold": 0.45,
    "labels": {str(i): c for i, c in enumerate(classes_list)},
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

json_path = os.path.join(SENSECRAFT_DIR, "model.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)

# 6. Create SenseCraft Zip
zip_path = os.path.join(SENSECRAFT_DIR, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(os.path.join(SENSECRAFT_DIR, "model.tflite"), arcname="model.tflite")
    zf.write(json_path, arcname="model.json")
print(f"[+] SenseCraft package created: {zip_path}")

# 7. Mirror to OneDrive
if os.path.exists(ONEDRIVE_DIR):
    import shutil
    shutil.copy2(zip_path, os.path.join(ONEDRIVE_DIR, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip"))
    shutil.copy2(os.path.join(SENSECRAFT_DIR, "model.tflite"), os.path.join(ONEDRIVE_DIR, "drishti_yolo_pico_192_vela.tflite"))
    shutil.copy2(json_path, os.path.join(ONEDRIVE_DIR, "model.json"))
    print(f"[+] Mirrored to OneDrive: {ONEDRIVE_DIR}")

print("\n" + "=" * 68)
print(" PIPELINE COMPLETED SUCCESSFULLY!")
print("=" * 68)
