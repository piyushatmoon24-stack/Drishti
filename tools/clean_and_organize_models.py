"""
Drishti Smart Stick - Clean and Organize Models Pipeline
1. Integrates the new ML model from "C:\\Users\\mohan\\OneDrive\\文档\\Drishti\\export\\new model.zip".
2. Extracts new firmware.img and model_vela.tflite into tools/edge_impulse_firmware/.
3. Updates export/grove_vision_ai_v2/FOR_SENSECRAFT_UPLOAD/ with the new model and repackages REAL_NEW_MODEL_FOR_SENSECRAFT.zip.
4. Preserves the single best previous model in export/highest_accuracy_backup_model/.
5. Deletes all obsolete/failed models (New drishti-v2-v16-impulse.zip, archive_old_models, etc.).
6. Deletes duplicate .tflite files and temporary build/flasher artifacts.
7. Mirrors clean state to OneDrive export directory.
"""

import os
import sys
import shutil
import zipfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ONEDRIVE_ROOT = r"C:\Users\mohan\OneDrive\文档\Drishti"

SRC_ZIP = os.path.join(ONEDRIVE_ROOT, "export", "new model.zip")
if not os.path.exists(SRC_ZIP):
    SRC_ZIP = os.path.join(PROJECT_ROOT, "export", "new model.zip")

print("=" * 68)
print(" DRISHTI: CLEANING & ORGANIZING ML MODELS")
print("=" * 68)
print(f"[*] Source New Model Zip: {SRC_ZIP}")

if not os.path.exists(SRC_ZIP):
    print(f"[!] Error: Could not locate new model.zip at {SRC_ZIP}")
    sys.exit(1)

# Paths in project
EI_DIR = os.path.join(PROJECT_ROOT, "tools", "edge_impulse_firmware")
EXPORT_DIR = os.path.join(PROJECT_ROOT, "export")
SENSECRAFT_DIR = os.path.join(EXPORT_DIR, "grove_vision_ai_v2", "FOR_SENSECRAFT_UPLOAD")
BACKUP_DIR = os.path.join(EXPORT_DIR, "highest_accuracy_backup_model")

os.makedirs(EI_DIR, exist_ok=True)
os.makedirs(SENSECRAFT_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# 1. Preserve the single best previous model before overwriting
best_prev_tflite = os.path.join(EI_DIR, "model_vela.tflite")
best_prev_model_json = os.path.join(SENSECRAFT_DIR, "model.json")
if os.path.exists(best_prev_tflite):
    shutil.copy2(best_prev_tflite, os.path.join(BACKUP_DIR, "best_previous_model_vela.tflite"))
    print(f"[+] Saved best previous model to backup: {os.path.join(BACKUP_DIR, 'best_previous_model_vela.tflite')}")
if os.path.exists(best_prev_model_json):
    shutil.copy2(best_prev_model_json, os.path.join(BACKUP_DIR, "model.json"))

# 2. Extract new model from new model.zip into tools/edge_impulse_firmware
print("\n[*] Extracting new model and firmware from new model.zip...")
with zipfile.ZipFile(SRC_ZIP, "r") as z:
    for name in z.namelist():
        if name.endswith("firmware.img") or "firmware" in name.lower() and name.endswith(".img"):
            dest = os.path.join(EI_DIR, "firmware.img")
            with open(dest, "wb") as f:
                f.write(z.read(name))
            print(f"  [+] Extracted firmware: {dest} ({os.path.getsize(dest):,} bytes)")
        elif name.endswith("model_vela.tflite") or name.endswith(".tflite"):
            dest = os.path.join(EI_DIR, "model_vela.tflite")
            with open(dest, "wb") as f:
                f.write(z.read(name))
            print(f"  [+] Extracted model: {dest} ({os.path.getsize(dest):,} bytes)")
            
            # Copy to SenseCraft upload folder
            sc_dest = os.path.join(SENSECRAFT_DIR, "model.tflite")
            shutil.copy2(dest, sc_dest)
            print(f"  [+] Copied new model to SenseCraft path: {sc_dest}")
        elif "xmodem" in name and not name.endswith("/"):
            rel_name = name if not name.startswith("xmodem/") else name[7:]
            xmodem_dest = os.path.join(EI_DIR, "xmodem", rel_name)
            os.makedirs(os.path.dirname(xmodem_dest), exist_ok=True)
            with open(xmodem_dest, "wb") as f:
                f.write(z.read(name))

# Copy new model.zip into project export directory as well
dest_zip = os.path.join(EXPORT_DIR, "new model.zip")
if not os.path.exists(dest_zip) or os.path.getmtime(SRC_ZIP) > os.path.getmtime(dest_zip):
    shutil.copy2(SRC_ZIP, dest_zip)
    print(f"[+] Synced new model.zip into project export directory: {dest_zip}")

# 3. Re-package REAL_NEW_MODEL_FOR_SENSECRAFT.zip with new model.tflite and model.json
print("\n[*] Packaging REAL_NEW_MODEL_FOR_SENSECRAFT.zip...")
sc_zip = os.path.join(SENSECRAFT_DIR, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip")
with zipfile.ZipFile(sc_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(os.path.join(SENSECRAFT_DIR, "model.tflite"), arcname="model.tflite")
    zf.write(os.path.join(SENSECRAFT_DIR, "model.json"), arcname="model.json")
print(f"[+] Packaged SenseCraft ZIP: {sc_zip} ({os.path.getsize(sc_zip):,} bytes)")

# Also copy REAL_NEW_MODEL_FOR_SENSECRAFT.zip to export/ root
shutil.copy2(sc_zip, os.path.join(EXPORT_DIR, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip"))

# 4. Delete obsolete/failed previous models and duplicates in PROJECT_ROOT
print("\n[*] Deleting obsolete and duplicate model files...")

files_to_delete = [
    # Failed YOLO-Pro Nano model from prompt #2 (caused AllocateTensors error)
    os.path.join(EXPORT_DIR, "New drishti-v2-v16-impulse.zip"),
    # Loose duplicate .tflites in export/
    os.path.join(EXPORT_DIR, "drishti_192x192_fomo_vela.tflite"),
    os.path.join(EXPORT_DIR, "drishti_yolo_pico_192_vela.tflite"),
    # Loose duplicates in FOR_SENSECRAFT_UPLOAD
    os.path.join(SENSECRAFT_DIR, "DRISHTI_192x192_FOR_SENSECRAFT.tflite"),
    os.path.join(SENSECRAFT_DIR, "drishti_192x192_vela.tflite"),
    os.path.join(SENSECRAFT_DIR, "drishti_yolo_pico_192_vela.tflite"),
    # Temporary flasher file
    os.path.join(EI_DIR, "_temp_model_0_preamble_data.bin")
]

dirs_to_delete = [
    os.path.join(EXPORT_DIR, "archive_old_models")
]

for f in files_to_delete:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"  [-] Deleted: {f}")
        except Exception as e:
            print(f"  [!] Failed to delete {f}: {e}")

for d in dirs_to_delete:
    if os.path.exists(d):
        try:
            shutil.rmtree(d)
            print(f"  [-] Deleted directory: {d}")
        except Exception as e:
            print(f"  [!] Failed to delete dir {d}: {e}")

# 5. Clean Python __pycache__ folders
for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
    if "__pycache__" in dirnames:
        pycache_dir = os.path.join(dirpath, "__pycache__")
        try:
            shutil.rmtree(pycache_dir)
            print(f"  [-] Cleaned cache: {pycache_dir}")
        except Exception:
            pass

# 6. Mirror cleanup to OneDrive if it exists
if os.path.exists(ONEDRIVE_ROOT):
    print("\n[*] Mirroring cleanup to OneDrive directory...")
    od_export = os.path.join(ONEDRIVE_ROOT, "export")
    od_sc = os.path.join(od_export, "grove_vision_ai_v2", "FOR_SENSECRAFT_UPLOAD")
    od_backup = os.path.join(od_export, "highest_accuracy_backup_model")
    os.makedirs(od_backup, exist_ok=True)
    os.makedirs(od_sc, exist_ok=True)
    
    # Sync new packages to OneDrive
    shutil.copy2(sc_zip, os.path.join(od_sc, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip"))
    shutil.copy2(sc_zip, os.path.join(od_export, "REAL_NEW_MODEL_FOR_SENSECRAFT.zip"))
    shutil.copy2(os.path.join(SENSECRAFT_DIR, "model.tflite"), os.path.join(od_sc, "model.tflite"))
    shutil.copy2(os.path.join(BACKUP_DIR, "best_previous_model_vela.tflite"), os.path.join(od_backup, "best_previous_model_vela.tflite"))
    
    # Delete obsolete files from OneDrive
    od_files_to_delete = [
        os.path.join(od_export, "New drishti-v2-v16-impulse.zip"),
        os.path.join(od_export, "drishti_192x192_fomo_vela.tflite"),
        os.path.join(od_export, "drishti_yolo_pico_192_vela.tflite"),
        os.path.join(od_sc, "DRISHTI_192x192_FOR_SENSECRAFT.tflite"),
        os.path.join(od_sc, "drishti_192x192_vela.tflite"),
        os.path.join(od_sc, "drishti_yolo_pico_192_vela.tflite"),
        os.path.join(ONEDRIVE_ROOT, "tools", "edge_impulse_firmware", "_temp_model_0_preamble_data.bin")
    ]
    for f in od_files_to_delete:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"  [-] (OneDrive) Deleted: {f}")
            except Exception:
                pass
                
    od_archive = os.path.join(od_export, "archive_old_models")
    if os.path.exists(od_archive):
        try:
            shutil.rmtree(od_archive)
            print(f"  [-] (OneDrive) Deleted dir: {od_archive}")
        except Exception:
            pass

print("\n" + "=" * 68)
print(" CLEANUP AND REORGANIZATION COMPLETE!")
print("=" * 68)
