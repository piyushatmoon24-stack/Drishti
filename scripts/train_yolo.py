"""
Drishti Model Training Script (Ultralytics YOLO)
Optimized for Micro-NPU Deployment on Grove Vision AI Module V2 (Ethos-U55).

Key Constraints for Grove Vision AI Module V2:
- Model: YOLOv8n (nano) or YOLO11n
- Input Resolution: 192x192 or 224x224 (fits within Ethos-U55 SRAM for max FPS)
- Classes: 34 classes (0 to 49 mapped to '0001' to '0050')
"""

import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
YAML_PATH = BASE_DIR / "data" / "drishti_34.yaml"

def train_model(epochs=100, imgsz=192, batch_size=32, device="0", pretrained_weights="yolov8n.pt"):
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[!] Ultralytics is not installed. Install with: pip install ultralytics")
        sys.exit(1)

    print(f"[*] Initializing YOLO training on {YAML_PATH}...")
    print(f"[*] Input size: {imgsz}x{imgsz} | Epochs: {epochs} | Batch size: {batch_size}")
    
    # Load base nano model
    model = YOLO(pretrained_weights)

    # Train model with parameters optimized for edge vision micro-controllers
    results = model.train(
        data=str(YAML_PATH),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=device,
        workers=4,
        optimizer="AdamW",
        lr0=0.002,
        lrf=0.01,
        # Edge friendly augmentations
        mosaic=1.0,
        mixup=0.1,
        degrees=10.0,
        flipud=0.0,  # Don't flip vertically (stairs down must stay down!)
        fliplr=0.5,
        project=str(BASE_DIR / "runs" / "train"),
        name="drishti_34_yolov8n",
        save=True,
        plots=True
    )
    
    print("[+] Training completed!")
    best_model_path = Path(results.save_dir) / "weights" / "best.pt"
    print(f"[+] Best model checkpoint saved at: {best_model_path}")
    return best_model_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Drishti 34-Class YOLO Model")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=192, help="Image size (192 or 224 recommended for Grove Vision AI V2)")
    parser.add_argument("--batch", type=int, default=32, help="Batch size")
    parser.add_argument("--device", type=str, default="0", help="GPU device ID (e.g. '0') or 'cpu'")
    parser.add_argument("--weights", type=str, default="yolov8n.pt", help="Pretrained weights")
    
    args = parser.parse_args()
    train_model(epochs=args.epochs, imgsz=args.imgsz, batch_size=args.batch, device=args.device, pretrained_weights=args.weights)
