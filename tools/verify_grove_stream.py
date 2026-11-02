"""
Drishti Smart Stick - Robust Grove Vision AI V2 Diagnostic & Stream Verifier
Auto-negotiates baud rate (921600 / 115200), auto-detects protocol (SenseCraft SSCMA JSON or Edge Impulse),
and decodes live object detections for all 8 target classes:
car, chair, door, motorcycle, person, pole, stairs, table.
"""

import sys
import time
import json
import re
import serial
import serial.tools.list_ports

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TARGET_CLASSES = ["car", "chair", "door", "motorcycle", "person", "pole", "stairs", "table"]

# 8-Class Index Mapping
INDEX_TO_CLASS = {
    0: "car",
    1: "chair",
    2: "door",
    3: "motorcycle",
    4: "person",
    5: "pole",
    6: "stairs",
    7: "table"
}

def find_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = (p.description or "").lower()
        if "ch343" in desc or "ch34" in desc:
            return p.device, p.description
    if ports:
        return ports[0].device, ports[0].description
    return None, None

def open_serial_auto_baud(port_name):
    """Tries 921600 baud first (native WiseEye2 rate), then falls back to 115200."""
    baudrates = [921600, 115200]
    
    for baud in baudrates:
        try:
            print(f"[*] Testing connection at {baud} baud...")
            ser = serial.Serial(port_name, baud, timeout=0.8)
            time.sleep(0.15)
            ser.reset_input_buffer()
            # Send wakeup
            ser.write(b"\r\n")
            time.sleep(0.1)
            ser.write(b"AT+INVOKE=1\r\n")
            ser.write(b"AT+RUNIMPULSECONT\r\n")
            
            # Read a few lines to check for valid text
            valid_chars = 0
            total_chars = 0
            start_t = time.time()
            
            while time.time() - start_t < 1.2:
                raw = ser.read(ser.in_waiting or 1)
                if raw:
                    for b in raw:
                        total_chars += 1
                        if 32 <= b <= 126 or b in (10, 13):
                            valid_chars += 1
                if total_chars > 30:
                    break

            ratio = (valid_chars / total_chars) if total_chars > 0 else 0
            if ratio > 0.65 or total_chars == 0:
                print(f"[+] Baud rate locked at {baud} baud (readability ratio: {ratio:.0%})")
                return ser, baud
            else:
                print(f"[-] High noise at {baud} baud ({ratio:.0%} readable). Trying alternative...")
                ser.close()
        except Exception as e:
            if "PermissionError" in str(e) or "Access is denied" in str(e):
                print(f"\n[!] ERROR: Port {port_name} is currently LOCKED by another application!")
                print("    -> If you have SenseCraft AI open in Brave, Edge, or Chrome, CLOSE that tab.")
                print("    -> If preview_drishti_vision is open, CLOSE it.")
                sys.exit(1)
            try:
                ser.close()
            except Exception:
                pass
            continue

    # Default to 921600 if auto-negotiation was inconclusive
    print(f"[*] Defaulting to native 921600 baud for Himax WiseEye2.")
    return serial.Serial(port_name, 921600, timeout=1), 921600

def parse_sscma_json(line):
    """Extracts bounding boxes and classes from SenseCraft SSCMA JSON packets."""
    detections = []
    try:
        data = json.loads(line)
        payload = data.get("data", {})
        
        # Check for boxes: [[x, y, w, h, score, target], ...]
        boxes = payload.get("boxes", [])
        for box in boxes:
            if len(box) >= 6:
                x, y, w, h, score, target = box[0], box[1], box[2], box[3], box[4], box[5]
                # Target can be 0-7, or COCO 0 (person)
                cls_name = INDEX_TO_CLASS.get(target, f"class_{target}")
                if target == 0 and "person" not in INDEX_TO_CLASS.get(0, ""):
                    cls_name = "person (COCO 0)"
                detections.append({
                    "class": cls_name,
                    "target": target,
                    "score": score,
                    "x": x, "y": y, "w": w, "h": h
                })

        # Check for classes: [[score, target], ...]
        classes = payload.get("classes", [])
        for item in classes:
            if len(item) >= 2:
                score, target = item[0], item[1]
                cls_name = INDEX_TO_CLASS.get(target, f"class_{target}")
                detections.append({
                    "class": cls_name,
                    "target": target,
                    "score": score,
                    "x": 0, "y": 0, "w": 0, "h": 0
                })
    except Exception:
        pass
    return detections

def main():
    print("=" * 68)
    print("   DRISHTI: GROVE VISION AI V2 DUAL-PROTOCOL STREAM VERIFIER")
    print("   Target 8 Classes: car, chair, door, motorcycle, person, pole, stairs, table")
    print("   Supports: SenseCraft SSCMA JSON & Edge Impulse ASCII Stream")
    print("=" * 68)

    port, desc = find_port()
    if not port:
        print("[!] No USB COM port found!")
        print("    Please connect Grove Vision AI Module V2 to your PC via USB-C.")
        print("    Waiting for connection...", end="", flush=True)
        while not port:
            time.sleep(1)
            print(".", end="", flush=True)
            port, desc = find_port()
        print()

    print(f"[+] Detected Vision AI Port: {port} ({desc})")
    ser, baud = open_serial_auto_baud(port)

    # Wakeup & trigger inference
    ser.write(b"\r\n")
    time.sleep(0.1)
    ser.write(b"AT+INVOKE=1\r\n")
    ser.write(b"AT+RUNIMPULSECONT\r\n")
    print("[*] Sent AT+INVOKE=1 & AT+RUNIMPULSECONT to WiseEye2.")
    print("[*] Listening for detections (Press Ctrl+C to stop)...\n")

    last_ping = time.time()
    detections_count = 0

    try:
        while True:
            # Keepalive ping every 4s
            if time.time() - last_ping > 4.0:
                ser.write(b"AT+INVOKE=1\r\n")
                ser.write(b"AT+RUNIMPULSECONT\r\n")
                last_ping = time.time()

            raw_bytes = ser.readline()
            if not raw_bytes:
                continue

            line = raw_bytes.decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            # 1. Check for SSCMA JSON Packet
            if line.startswith("{") and line.endswith("}"):
                detections = parse_sscma_json(line)
                if detections:
                    for d in detections:
                        detections_count += 1
                        cls_name = d["class"].upper()
                        score = d["score"]
                        x, y, w, h = d["x"], d["y"], d["w"], d["h"]
                        print(f"  >>> [DETECTED {cls_name}!] Confidence: {score}% | Box: [x={x}, y={y}, w={w}, h={h}]")
                else:
                    # Print raw JSON if it's status/timing
                    print(f"  [JSON] {line}")
                continue

            # 2. Check for Edge Impulse ASCII Predictions
            lower_line = line.lower()
            matched = False
            for cls in TARGET_CLASSES:
                if cls in lower_line and ("(" in line or "[" in line or ":" in line):
                    detections_count += 1
                    matched = True
                    print(f"  >>> [DETECTED {cls.upper()}!] -> {line}")
                    break

            if not matched:
                # Check for Himax Bootloader prompt
                if "reboot system" in lower_line or "(y)" in lower_line:
                    print("  [BOOTLOADER DETECTED] Board is in bootloader. Sending 'y' to start Edge AI application...")
                    ser.write(b"y\r\n")
                elif "xmodem" in lower_line:
                    print(f"  [BOOTLOADER READY] {line}")
                elif "timing:" in lower_line or "predictions" in lower_line or "dsp:" in lower_line:
                    print(f"  [PERF] {line}")
                else:
                    print(f"  [RAW] {line}")

    except KeyboardInterrupt:
        print(f"\n[*] Stopped. Total detections captured: {detections_count}")
    finally:
        try:
            ser.write(b"AT+INVOKE=0\r\n")
            ser.write(b"b\r\n")
            ser.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
