"""
Drishti Smart Stick - Enhanced Model Training & Deployment Pipeline
Monitors Edge Impulse Job 55732505, compiles with Arm Vela, and packages the model.
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
TRAIN_JOB_ID = 55732505

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EI_DIR = os.path.join(PROJECT_ROOT, "tools", "edge_impulse_firmware")
EXPORT_DIR = os.path.join(PROJECT_ROOT, "export")
SENSECRAFT_DIR = os.path.join(EXPORT_DIR, "grove_vision_ai_v2", "FOR_SENSECRAFT_UPLOAD")
ONEDRIVE_DIR = r"C:\Users\mohan\OneDrive\文档\Drishti\export"

os.makedirs(EI_DIR, exist_ok=True)
os.makedirs(SENSECRAFT_DIR, exist_ok=True)

session = requests.Session()

print("=" * 68)
print(" DRISHTI: ENHANCED MODEL GPU TRAINING & VELA COMPILATION")
print("=" * 68)
print(f"[*] Training Job ID: {TRAIN_JOB_ID}")

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
            print(f"\n[+] Training finished! Success={success} in {time.time()-t0:.1f}s")
            if not success:
                print("[-] Training failed. Check logs.")
                sys.exit(1)
            break
    except Exception as e:
        pass

# 2. Trigger Arm Vela compilation for Himax WiseEye2
print("\n" + "=" * 68)
print(" STEP 2: TRIGGERING ARM VELA NPU COMPILATION (WISEEYE2 / ETHOS-U55)")
print("=" * 68)

r = session.post(f"{BASE_URL}/jobs/build-ondevice-model?type=himax-wiseeye2", 
                 headers=HEADERS, json={"engine": "tflite"}, timeout=25).json()
if not r.get("success"):
    print(f"[-] Vela trigger failed: {r}")
    sys.exit(1)

build_job_id = r.get("id")
print(f"[+] Arm Vela compilation started (Job ID: {build_job_id})", flush=True)

t1 = time.time()
seen_build = set()
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
            if text and text not in seen_build:
                seen_build.add(text)
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

# 3. Download fresh deployment package
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

# 4. Extract and deploy
import io
with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
    for name in z.namelist():
        if name.endswith("firmware.img") or "firmware" in name.lower() and name.endswith(".img"):
            dest_fw = os.path.join(EI_DIR, "firmware.img")
            with open(dest_fw, "wb") as f:
                f.write(z.read(name))
            print(f"  [+] Saved firmware image: {dest_fw}")
        elif name.endswith("model_vela.tflite") or name.endswith(".tflite"):
            dest_tflite = os.path.join(EI_DIR, "model_vela.tflite")
            with open(dest_tflite, "wb") as f:
                f.write(z.read(name))
            print(f"  [+] Saved Vela model: {dest_tflite}")

            # SenseCraft upload paths
            sc_dest = os.path.join(SENSECRAFT_DIR, "model.tflite")
            with open(sc_dest, "wb") as f:
                f.write(z.read(name))
            print(f"  [+] Updated SenseCraft model: {sc_dest}")

# 5. Save master new model.zip
with open(os.path.join(EXPORT_DIR, "new model.zip"), "wb") as f:
    f.write(zip_data)
if os.path.exists(ONEDRIVE_DIR):
    with open(os.path.join(ONEDRIVE_DIR, "new model.zip"), "wb") as f:
        f.write(zip_data)
print(f"[+] Saved master new model.zip ({len(zip_data):,} bytes)")

# 6. Repackage REAL_NEW_MODEL_FOR_SENSECRAFT.zip
sc_zip = os.path.join(SENSECRAFT_DIR, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip")
with zipfile.ZipFile(sc_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(os.path.join(SENSECRAFT_DIR, "model.tflite"), arcname="model.tflite")
    zf.write(os.path.join(SENSECRAFT_DIR, "model.json"), arcname="model.json")
shutil_root_zip = os.path.join(EXPORT_DIR, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip")
with open(shutil_root_zip, "wb") as f:
    with open(sc_zip, "rb") as sf:
        f.write(sf.read())

if os.path.exists(ONEDRIVE_DIR):
    od_sc = os.path.join(ONEDRIVE_DIR, "grove_vision_ai_v2", "FOR_SENSECRAFT_UPLOAD")
    os.makedirs(od_sc, exist_ok=True)
    with open(os.path.join(od_sc, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip"), "wb") as f:
        with open(sc_zip, "rb") as sf:
            f.write(sf.read())
    with open(os.path.join(od_sc, "model.tflite"), "wb") as f:
        with open(os.path.join(SENSECRAFT_DIR, "model.tflite"), "rb") as sf:
            f.write(sf.read())
    with open(os.path.join(ONEDRIVE_DIR, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip"), "wb") as f:
        with open(sc_zip, "rb") as sf:
            f.write(sf.read())

print("\n" + "=" * 68)
print(" ENHANCED TRAINING & DEPLOYMENT PIPELINE FINISHED SUCCESSFULLY!")
print("=" * 68)
