"""
Drishti Real-Time Webcam Inference Tester
Runs live detection using the newly trained 34-class model at Grove Vision AI V2 resolution (192x192).
Displays both the 4-Digit Unique ID (matching DFPlayer Mini MP3s) and the Object Name.
"""

import time
import json
from pathlib import Path
import cv2
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "export" / "grove_vision_ai_v2" / "drishti_34.pt"
CONFIG_PATH = BASE_DIR / "data" / "classes_config.json"

def main():
    if not MODEL_PATH.exists():
        print(f"[!] Model not found at: {MODEL_PATH}")
        return

    print(f"[*] Loading Drishti trained model: {MODEL_PATH}...")
    model = YOLO(str(MODEL_PATH))

    # Load friendly object names mapping: ID -> Name
    id_to_name = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            classes = json.load(f)
        id_to_name = {c["id"]: c["name"] for c in classes}

    print("[*] Opening webcam stream (Camera 0)...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[!] Could not open webcam.")
        return

    print("=" * 60)
    print("  DRISHTI LIVE OBJECT DETECTION (WEBCAM)")
    print("  - Resolution: 192x192 (Micro-NPU SRAM Compliant)")
    print("  - Press 'q' or 'ESC' to exit")
    print("=" * 60)

    prev_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run inference at 192x192
        t0 = time.time()
        results = model(frame, imgsz=192, conf=0.45, iou=0.4, verbose=False)
        infer_ms = (time.time() - t0) * 1000

        # Annotate detections
        boxes = results[0].boxes
        annotated = frame.copy()

        for box in boxes:
            cls_idx = int(box.cls[0])
            conf_val = float(box.conf[0])
            xyxy = box.xyxy[0].cpu().numpy().astype(int)

            class_id_str = model.names.get(cls_idx, f"{cls_idx:04d}")
            name_str = id_to_name.get(class_id_str, "Object")
            label_text = f"[{class_id_str}] {name_str} {conf_val:.2f}"

            # Draw bounding box
            color = (0, 220, 50) if "Stairs" not in name_str and "Pothole" not in name_str else (0, 0, 255)
            cv2.rectangle(annotated, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 2)

            # Draw label banner
            (w, h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(annotated, (xyxy[0], max(0, xyxy[1] - h - 8)), (xyxy[0] + w + 6, max(0, xyxy[1])), color, -1)
            cv2.putText(annotated, label_text, (xyxy[0] + 3, max(12, xyxy[1] - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        # Calculate FPS
        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        # Overlay status banner
        banner_text = f"Drishti AI | FPS: {fps:.1f} | Infer: {infer_ms:.1f}ms | Detections: {len(boxes)}"
        cv2.putText(annotated, banner_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow("Drishti Assistive Vision - Live Feed", annotated)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[+] Webcam stream closed.")

if __name__ == "__main__":
    main()
