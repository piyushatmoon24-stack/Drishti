"""
Drishti Smart Stick - Test Evaluation & Metrics Calculator
Parses the Edge Impulse classify-all test dataset results (452 unseen images, 1092 objects),
computes exact Precision, Recall, F1-Score, Confusion Matrix, and generates the final conclusion.
"""

import os
import sys
import json
import requests
from collections import defaultdict

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(line_buffering=True)

API_KEY = "ei_f6f7e400ef663cbdb2f53e05906703d28ce75fe82b6ded4d"
PROJECT_ID = 1146751
HEADERS = {"x-api-key": API_KEY}
BASE_URL = f"https://studio.edgeimpulse.com/v1/api/{PROJECT_ID}"
OUTPUT_DIR = os.path.abspath(r"tools\edge_impulse_firmware")

# Alphabetical class mapping (1-indexed in Edge Impulse debugInfo)
# 1: car, 2: chair, 3: door, 4: motorcycle, 5: person, 6: pole, 7: stairs, 8: table
TARGET_CLASSES = ["car", "chair", "door", "motorcycle", "person", "pole", "stairs", "table"]

def get_class_name(label_val):
    if isinstance(label_val, int):
        idx = label_val - 1
        if 0 <= idx < len(TARGET_CLASSES):
            return TARGET_CLASSES[idx]
    return f"unknown_{label_val}"

def fetch_and_evaluate():
    print("=" * 78, flush=True)
    print(" DRISHTI: EVALUATING UNSEEN TEST DATASET (452 IMAGES)", flush=True)
    print("=" * 78, flush=True)

    r = requests.get(f"{BASE_URL}/classify/all/result/page", headers=HEADERS, timeout=60).json()
    if not r.get("success"):
        print(f"[-] Failed to fetch results: {r}")
        return

    results = r.get("result", [])
    print(f"[*] Total test samples evaluated: {len(results)}", flush=True)

    class_stats = {cls: {"gt": 0, "tp": 0, "fp": 0, "fn": 0} for cls in TARGET_CLASSES}
    confusion = defaultdict(lambda: defaultdict(int))
    total_assigned = 0
    total_unassigned_true = 0
    total_unassigned_pred = 0

    for sample_res in results:
        sample = sample_res.get("sample", {})
        gt_boxes = sample.get("boundingBoxes", [])
        classifications = sample_res.get("classifications", [])
        if not classifications:
            continue
        
        details = classifications[0].get("details", [])
        if not details:
            continue

        det_entry = details[0]
        debug_info = det_entry.get("debugInfoJson")
        if not debug_info:
            continue

        try:
            dbg = json.loads(debug_info)
            y_trues = dbg.get("y_trues", [])
            y_preds = dbg.get("y_preds", [])
            assignments = dbg.get("assignments", [])

            assigned_true_idxs = set()
            assigned_pred_idxs = set()

            for a in assignments:
                yt_idx = a.get("yt")
                yp_idx = a.get("yp")
                assigned_true_idxs.add(yt_idx)
                assigned_pred_idxs.add(yp_idx)
                total_assigned += 1

                true_lbl_num = y_trues[yt_idx]["label"]
                pred_lbl_num = y_preds[yp_idx]["label"]

                true_cls = get_class_name(true_lbl_num)
                pred_cls = get_class_name(pred_lbl_num)

                confusion[true_cls][pred_cls] += 1
                if true_cls == pred_cls:
                    if true_cls in class_stats:
                        class_stats[true_cls]["tp"] += 1
                else:
                    if pred_cls in class_stats:
                        class_stats[pred_cls]["fp"] += 1
                    if true_cls in class_stats:
                        class_stats[true_cls]["fn"] += 1

            # False Negatives (unassigned ground truth objects)
            for idx in dbg.get("unassigned_y_true_idxs", []):
                if idx not in assigned_true_idxs and idx < len(y_trues):
                    lbl_num = y_trues[idx]["label"]
                    true_cls = get_class_name(lbl_num)
                    if true_cls in class_stats:
                        class_stats[true_cls]["fn"] += 1
                    confusion[true_cls]["None (Missed)"] += 1
                    total_unassigned_true += 1

            # False Positives (unassigned predicted ghost boxes)
            for idx in dbg.get("unassigned_y_pred_idxs", []):
                if idx not in assigned_pred_idxs and idx < len(y_preds):
                    lbl_num = y_preds[idx]["label"]
                    pred_cls = get_class_name(lbl_num)
                    if pred_cls in class_stats:
                        class_stats[pred_cls]["fp"] += 1
                    confusion["Background (Ghost)"][pred_cls] += 1
                    total_unassigned_pred += 1

        except Exception as e:
            pass

        # Ground truth counts
        for b in gt_boxes:
            lbl = b.get("label", "").lower()
            if lbl in class_stats:
                class_stats[lbl]["gt"] += 1

    # Print clean summary table
    print("\n" + "=" * 82, flush=True)
    print(f"{'Class':<12} | {'GroundTruth':<11} | {'TP':<6} | {'FP':<6} | {'FN':<6} | {'Precision':<9} | {'Recall':<7} | {'F1-Score':<8}", flush=True)
    print("-" * 82, flush=True)

    summary_data = {}
    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_gt = 0

    for cls in TARGET_CLASSES:
        st = class_stats[cls]
        tp = st["tp"]
        fp = st["fp"]
        fn = st["fn"]
        gt = st["gt"]

        prec = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0.0
        rec = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        total_tp += tp
        total_fp += fp
        total_fn += fn
        total_gt += gt

        summary_data[cls] = {
            "ground_truth": gt,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision_pct": round(prec, 2),
            "recall_pct": round(rec, 2),
            "f1_score": round(f1, 2)
        }

        print(f"{cls:<12} | {gt:<11} | {tp:<6} | {fp:<6} | {fn:<6} | {prec:>7.1f}%  | {rec:>5.1f}% | {f1:>6.2f}", flush=True)

    print("-" * 82, flush=True)
    overall_prec = (total_tp / (total_tp + total_fp)) * 100 if (total_tp + total_fp) > 0 else 0.0
    overall_rec = (total_tp / (total_tp + total_fn)) * 100 if (total_tp + total_fn) > 0 else 0.0
    overall_f1 = (2 * overall_prec * overall_rec / (overall_prec + overall_rec)) if (overall_prec + overall_rec) > 0 else 0.0
    print(f"{'OVERALL':<12} | {total_gt:<11} | {total_tp:<6} | {total_fp:<6} | {total_fn:<6} | {overall_prec:>7.1f}%  | {overall_rec:>5.1f}% | {overall_f1:>6.2f}", flush=True)
    print("=" * 82, flush=True)

    print(f"\n[*] Total Match Assignments: {total_assigned} | Total Misses: {total_unassigned_true} | Ghost Detections: {total_unassigned_pred}")

    # Confusion matrix dump
    print("\n" + "=" * 78, flush=True)
    print(" DETAILED CONFUSION MATRIX (GROUND TRUTH -> PREDICTED)", flush=True)
    print("=" * 78, flush=True)
    for true_c in TARGET_CLASSES:
        preds = confusion[true_c]
        print(f"Ground Truth [{true_c.upper()}]:", flush=True)
        if not preds:
            print("   (No detections or predictions recorded)")
        for pred_c, count in sorted(preds.items(), key=lambda x: -x[1]):
            tag = "CORRECT" if pred_c == true_c else ("MISSED" if "None" in pred_c else "CONFUSED")
            print(f"   -> {pred_c:<18}: {count:>4} [{tag}]", flush=True)

    # Save to json report
    final_report = {
        "model": "FOMO MobileNetV2 0.35 (96x96)",
        "dataset": "Roboflow Target 8 Classes (User Uploaded)",
        "test_images_count": len(results),
        "total_ground_truth_objects": total_gt,
        "overall_precision_pct": round(overall_prec, 2),
        "overall_recall_pct": round(overall_rec, 2),
        "overall_f1_score": round(overall_f1, 2),
        "classes": summary_data,
        "confusion_matrix": {k: dict(v) for k, v in confusion.items()}
    }

    out_path = os.path.join(OUTPUT_DIR, "test_evaluation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)
    print(f"\n[+] Full test evaluation report saved to {out_path}", flush=True)

if __name__ == "__main__":
    fetch_and_evaluate()
