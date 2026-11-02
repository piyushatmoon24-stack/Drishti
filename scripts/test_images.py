"""
Drishti Validation Images Tester
Runs model inference on validation images from the dataset and saves annotated
results into runs/test_predictions/ for review.
"""

from pathlib import Path
import cv2
import json
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "export" / "grove_vision_ai_v2" / "drishti_34.pt"
CONFIG_PATH = BASE_DIR / "data" / "classes_config.json"
VAL_IMAGES_DIR = BASE_DIR / "datasets" / "drishti_34" / "images" / "val"
OUTPUT_DIR = BASE_DIR / "runs" / "test_predictions"

def main():
    if not MODEL_PATH.exists():
        print(f"[!] Model not found at: {MODEL_PATH}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[*] Loading model: {MODEL_PATH}...")
    model = YOLO(str(MODEL_PATH))

    # Load ID -> Name mapping
    id_to_name = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            classes = json.load(f)
        id_to_name = {c["id"]: c["name"] for c in classes}

    image_paths = list(VAL_IMAGES_DIR.glob("*.jpg"))[:10]
    if not image_paths:
        print("[!] No validation images found in datasets/drishti_34/images/val/")
        return

    print(f"[*] Running predictions on {len(image_paths)} sample validation images...")

    for idx, img_p in enumerate(image_paths, 1):
        results = model(str(img_p), imgsz=192, conf=0.45, iou=0.4, verbose=False)
        frame = cv2.imread(str(img_p))

        for box in results[0].boxes:
            cls_idx = int(box.cls[0])
            conf_val = float(box.conf[0])
            xyxy = box.xyxy[0].cpu().numpy().astype(int)

            class_id_str = model.names.get(cls_idx, f"{cls_idx:04d}")
            name_str = id_to_name.get(class_id_str, "Object")
            label_text = f"[{class_id_str}] {name_str} {conf_val:.2f}"

            color = (0, 220, 50) if "Stairs" not in name_str and "Pothole" not in name_str else (0, 0, 255)
            cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 2)
            cv2.putText(frame, label_text, (xyxy[0], max(15, xyxy[1] - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

        out_path = OUTPUT_DIR / f"pred_{img_p.name}"
        cv2.imwrite(str(out_path), frame)
        print(f"  [{idx}/{len(image_paths)}] Saved prediction: {out_path.name} ({len(results[0].boxes)} detections)")

    print(f"\n[+] Done! Annotated images saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
