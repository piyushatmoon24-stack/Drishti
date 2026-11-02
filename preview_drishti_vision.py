"""
Drishti Smart Stick - Standalone PC GUI Preview & Audio Simulator
Visualizes Grove Vision AI Module V2 (Himax WiseEye2) object detections in real-time.
Renders spatial FOV radar, distance estimates, live serial telemetry stream,
and simulates DFPlayer Mini voice announcements through your PC speakers.

Completely independent of the XIAO ESP32-S3 firmware.
"""

import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import time
import subprocess
import json
import re

# Resilient imports for optional computer vision & image display
try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    cv2 = None
    CV2_AVAILABLE = False

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

# Color palette for 8 active balanced classes
CLASS_COLORS = {
    "stairs": "#FF3333",        # Bright Red (Critical Hazard)
    "car": "#FF5500",           # Red-Orange (Traffic)
    "motorcycle": "#FF7700",    # Amber-Orange (Moving Vehicle)
    "door": "#FF9933",          # Warm Amber (Navigation)
    "person": "#33CCFF",        # Bright Cyan (Pedestrian)
    "pole": "#33FFCC",          # Teal (Street Obstacle)
    "chair": "#FFCC00",         # Gold-Yellow (Furniture)
    "table": "#E6B800",         # Deep Gold (Furniture)
}

# DFPlayer Audio Track & Alert Catalog
AUDIO_CATALOG = {
    "stairs": ("0001.mp3", "Stairs ahead. Watch your step.", "CRITICAL HAZARD (Priority 1)"),
    "car": ("0019.mp3", "Vehicle ahead.", "TRAFFIC HAZARD (Priority 1)"),
    "motorcycle": ("0018.mp3", "Motorcycle approaching.", "TRAFFIC HAZARD (Priority 1)"),
    "door": ("0008.mp3", "Door ahead.", "NAVIGATION (Priority 2)"),
    "person": ("0013.mp3", "Person ahead.", "NAVIGATION (Priority 2)"),
    "pole": ("0006.mp3", "Pole ahead.", "OBSTACLE (Priority 2)"),
    "chair": ("0023.mp3", "Chair ahead.", "FURNITURE (Priority 3)"),
    "table": ("0026.mp3", "Table ahead.", "FURNITURE (Priority 3)"),
}

# 0-based index to class label mapping (8 Active Classes)
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

def kill_zombie_serial_holders():
    """Kills any orphaned python flasher scripts that might lock COM3."""
    try:
        cmd = "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*xmodem_send*' -or $_.CommandLine -like '*flash_edge_impulse*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
    except Exception:
        pass

class DrishtiVisionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Drishti Smart Stick - Vision AI V2 Real-Time Preview (8 Classes)")
        self.root.geometry("1060x700")
        self.root.configure(bg="#121212")

        kill_zombie_serial_holders()

        self.ser = None
        self.ser_lock = threading.Lock()
        self.running = True
        self.active_boxes = []
        self.last_speech_time = {}
        self.speech_cooldown = 2.5
        self.speech_enabled = tk.BooleanVar(value=True)
        self.webcam_enabled = tk.BooleanVar(value=False)
        self.demo_mode = False

        # Video capture (optional overlay)
        self.cap = None
        self.current_photo = None
        self.last_rx_time = 0

        self.setup_ui()
        self.init_webcam()

        # Start serial management thread
        self.serial_thread = threading.Thread(target=self.serial_management_loop, daemon=True)
        self.serial_thread.start()

        # Start UI render loop (~30 FPS)
        self.update_frame()

    def setup_ui(self):
        # Header Frame
        header = tk.Frame(self.root, bg="#1E1E1E", height=50)
        header.pack(fill="x", side="top", padx=10, pady=(10, 5))

        title = tk.Label(header, text="DRISHTI 8-CLASS ASSISTIVE VISION AI - LIVE PREVIEW", 
                         font=("Consolas", 13, "bold"), fg="#00FFCC", bg="#1E1E1E")
        title.pack(side="left", padx=15, pady=8)

        self.status_lbl = tk.Label(header, text="SEARCHING FOR BOARD...", font=("Consolas", 10, "bold"),
                                   fg="#FFAA00", bg="#1E1E1E")
        self.status_lbl.pack(side="right", padx=15)

        # Main Layout (Left: Radar Canvas, Right: Telemetry & Controls)
        main_frame = tk.Frame(self.root, bg="#121212")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left Canvas (FOV Visualizer 480x480)
        canvas_box = tk.LabelFrame(main_frame, text=" Smart Stick Spatial Radar (Cone of Vision) ",
                                  font=("Consolas", 10), fg="#888888", bg="#1E1E1E", bd=1)
        canvas_box.pack(side="left", fill="both", padx=(0, 5), pady=5)

        self.canvas = tk.Canvas(canvas_box, width=480, height=480, bg="#0A0A0A", highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        # Right Panel (Telemetry, Audio & Controls)
        right_panel = tk.Frame(main_frame, bg="#121212")
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=5)

        # Controls Box
        ctrl_box = tk.LabelFrame(right_panel, text=" Preview & Audio Controls ", font=("Consolas", 10),
                                fg="#888888", bg="#1E1E1E", bd=1)
        ctrl_box.pack(fill="x", pady=(0, 8))

        btn_row = tk.Frame(ctrl_box, bg="#1E1E1E")
        btn_row.pack(fill="x", padx=10, pady=6)

        chk_speech = tk.Checkbutton(btn_row, text="Voice Alerts", variable=self.speech_enabled,
                                    font=("Consolas", 9, "bold"), fg="#00FFCC", bg="#1E1E1E", selectcolor="#2A2A2A",
                                    activebackground="#1E1E1E", activeforeground="#00FFCC")
        chk_speech.pack(side="left", padx=(0, 8))

        if CV2_AVAILABLE and PIL_AVAILABLE:
            chk_cam = tk.Checkbutton(btn_row, text="Laptop Cam", variable=self.webcam_enabled,
                                     font=("Consolas", 9), fg="#888888", bg="#1E1E1E", selectcolor="#2A2A2A",
                                     activebackground="#1E1E1E", activeforeground="#FFFFFF")
            chk_cam.pack(side="left", padx=(0, 8))

        self.btn_sim = tk.Button(btn_row, text="Test Sound", font=("Consolas", 9, "bold"),
                                 bg="#0066AA", fg="#FFFFFF", relief="flat", padx=6, pady=2,
                                 command=self.simulate_person_detection)
        self.btn_sim.pack(side="right", padx=(4, 0))

        self.btn_start = tk.Button(btn_row, text="Start AI", font=("Consolas", 9, "bold"),
                                  bg="#008855", fg="#FFFFFF", relief="flat", padx=6, pady=2,
                                  command=self.start_inference_command)
        self.btn_start.pack(side="right", padx=(4, 0))

        self.btn_stop = tk.Button(btn_row, text="Stop AI", font=("Consolas", 9),
                                 bg="#444444", fg="#FFFFFF", relief="flat", padx=6, pady=2,
                                 command=self.stop_inference_command)
        self.btn_stop.pack(side="right", padx=(4, 0))

        self.btn_reboot = tk.Button(btn_row, text="Reboot", font=("Consolas", 9),
                                   bg="#774400", fg="#FFFFFF", relief="flat", padx=6, pady=2,
                                   command=self.reboot_board_command)
        self.btn_reboot.pack(side="right", padx=(4, 0))

        # Live Detection Details Box
        det_box = tk.LabelFrame(right_panel, text=" Active Detection Telemetry ", font=("Consolas", 10),
                               fg="#888888", bg="#1E1E1E", bd=1)
        det_box.pack(fill="x", pady=(0, 8))

        self.det_label = tk.Label(det_box, text="Searching for objects...", font=("Consolas", 12, "bold"),
                                  fg="#FFAA00", bg="#1E1E1E", anchor="w")
        self.det_label.pack(fill="x", padx=12, pady=(8, 2))

        self.track_label = tk.Label(det_box, text="DFPlayer Track: --", font=("Consolas", 9),
                                    fg="#AAAAAA", bg="#1E1E1E", anchor="w")
        self.track_label.pack(fill="x", padx=12, pady=1)

        self.alert_label = tk.Label(det_box, text="Earphone Voice: --", font=("Consolas", 9, "italic"),
                                    fg="#00FFCC", bg="#1E1E1E", anchor="w")
        self.alert_label.pack(fill="x", padx=12, pady=1)

        self.dist_label = tk.Label(det_box, text="Estimated Distance: --", font=("Consolas", 9, "bold"),
                                   fg="#AAAAAA", bg="#1E1E1E", anchor="w")
        self.dist_label.pack(fill="x", padx=12, pady=1)

        self.perf_label = tk.Label(det_box, text="NPU Latency: DSP 2ms | Inference 2ms (Ethos-U55 NPU)", font=("Consolas", 9),
                                   fg="#00FF88", bg="#1E1E1E", anchor="w")
        self.perf_label.pack(fill="x", padx=12, pady=(4, 6))

        # Raw Serial Console Log Box
        raw_box = tk.LabelFrame(right_panel, text=" Live Serial Stream from Grove Vision AI V2 ", font=("Consolas", 10),
                               fg="#888888", bg="#1E1E1E", bd=1)
        raw_box.pack(fill="both", expand=True)

        self.log_list = tk.Listbox(raw_box, bg="#0A0A0A", fg="#DDDDDD", font=("Consolas", 8),
                                   bd=0, highlightthickness=0)
        self.log_list.pack(fill="both", expand=True, padx=6, pady=6)

    def init_webcam(self):
        if not CV2_AVAILABLE:
            self.cap = None
            return
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.cap = None
        except Exception:
            self.cap = None

    def send_serial(self, data: bytes):
        with self.ser_lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(data)
                except Exception:
                    pass

    def start_inference_command(self):
        self.send_serial(b"\r\nAT+RUNIMPULSE\r\n")
        self.send_serial(b"AT+INVOKE=1\r\n")
        self.append_raw_log("[HOST -> BOARD] Sent AT+RUNIMPULSE")

    def stop_inference_command(self):
        self.send_serial(b"b\r\n")
        self.send_serial(b"AT+INVOKE=0\r\n")
        self.append_raw_log("[HOST -> BOARD] Sent Stop command ('b')")

    def reboot_board_command(self):
        self.send_serial(b"0\r\n")
        self.send_serial(b"AT+CLEARCONFIG\r\n")
        self.append_raw_log("[HOST -> BOARD] Sent Reboot command ('0')")

    def serial_management_loop(self):
        """Continuously monitors COM port, auto-connects to Grove Vision AI (115200 baud native for Edge Impulse), and streams detections."""
        while self.running:
            if not self.ser or not self.ser.is_open:
                ports = list(serial.tools.list_ports.comports())
                ch343 = [p.device for p in ports if "ch343" in (p.description or "").lower() or "ch34" in (p.description or "").lower()]
                target = ch343[0] if ch343 else ("COM3" if "COM3" in [p.device for p in ports] else (ports[0].device if ports else None))

                if target:
                    try:
                        with self.ser_lock:
                            self.ser = serial.Serial(target, 115200, timeout=0.2, dsrdtr=False, rtscts=False)
                            self.ser.dtr = False
                            self.ser.rts = False
                        time.sleep(0.15)
                        self.status_lbl.config(text=f"CONNECTED ({target} @ 115200) - READY", fg="#00FF88")
                        
                        # Stop any pending loops and send run command
                        self.send_serial(b"b\r\n\r\n")
                        time.sleep(0.1)
                        self.send_serial(b"0\r\n") # In case it was in bootloader
                        time.sleep(0.1)
                        self.send_serial(b"AT+RUNIMPULSE\r\n") # Launch camera pipeline
                        self.last_rx_time = time.time()
                    except Exception as e:
                        with self.ser_lock:
                            if self.ser:
                                try:
                                    self.ser.close()
                                except Exception:
                                    pass
                            self.ser = None
                        kill_zombie_serial_holders()
                        self.status_lbl.config(text=f"PORT {target} BUSY (RELEASING...)", fg="#FFAA00")
                else:
                    self.status_lbl.config(text="BOARD UNPLUGGED (CONNECT USB-C)", fg="#FFAA00")
                time.sleep(1.5)
                continue

            # Read stream from Grove Vision AI Module V2
            try:
                line = ""
                with self.ser_lock:
                    if self.ser and self.ser.is_open:
                        line = self.ser.readline().decode('latin1', errors='replace').strip()
                now = time.time()

                if not line:
                    time.sleep(0.02)
                    continue

                self.last_rx_time = now
                self.root.after(0, self.append_raw_log, line)

                # Check if bootloader is waiting for selection
                if "[0] Reboot system" in line or "waiting input key" in line:
                    self.send_serial(b"0\r\n")
                    self.root.after(0, self.append_raw_log, "[AUTO-BOOT] Sent '0' to exit bootloader into application")

                # If application just booted, launch impulse
                if "Compiler Version:" in line or "Edge Impulse firmware" in line:
                    time.sleep(0.1)
                    self.send_serial(b"AT+RUNIMPULSE\r\n")
                    self.root.after(0, self.append_raw_log, "[AUTO-START] Application detected, sent AT+RUNIMPULSE")

                if "Timing:" in line or "Classification:" in line or "Predictions" in line or "perf" in line:
                    self.root.after(0, self.update_timing, line)

                # Parse detection lines & hardware warnings
                self.parse_detection_line(line)

            except Exception:
                with self.ser_lock:
                    if self.ser:
                        try:
                            self.ser.close()
                        except Exception:
                            pass
                    self.ser = None
                self.status_lbl.config(text="BOARD DISCONNECTED", fg="#FF4444")
                time.sleep(1.0)

    def append_raw_log(self, text):
        if not text:
            return
        self.log_list.insert(0, f"> {text}")
        if self.log_list.size() > 80:
            self.log_list.delete(80, tk.END)

    def on_memory_overflow(self, detail_msg=""):
        """Called when Himax WiseEye2 runs out of internal SRAM arena for the active model."""
        self.det_label.config(text="NPU MEMORY OVERFLOW (ARENA EXCEEDED)", fg="#FF3333")
        self.dist_label.config(text="YOLO-Pro requires more SRAM than available with camera buffers!", fg="#FF5500")
        self.track_label.config(text=f"STATUS: {detail_msg or 'AllocateTensors() failed / ERR (-3 or -6)'}")
        self.alert_label.config(text="SOLUTION: Retrain with FOMO (MobileNetV2) or lighter resolution on Edge Impulse.")

    def parse_detection_line(self, line):
        """Extracts label, coordinates, and confidence from all Edge Impulse & SSCMA output formats."""
        # Check memory exhaustion error from firmware
        if "Failed to allocate TFLite arena" in line or "AllocateTensors() failed" in line or "ERR: Failed to run impulse (-3)" in line or "ERR: Failed to run impulse (-6)" in line:
            self.root.after(0, self.on_memory_overflow, line)
            return

        # Format 1: Edge Impulse console format:
        #   person (0.85) [ x: 24, y: 32, width: 40, height: 50 ]  OR  person (0.85) [ x: 24, y: 32 ]
        m1 = re.search(r'([a-zA-Z_]+)\s*\(([\d\.]+)\)\s*\[\s*x:\s*(\d+),\s*y:\s*(\d+)(?:,\s*width:\s*(\d+))?(?:,\s*height:\s*(\d+))?\s*\]', line)
        if m1:
            lbl = m1.group(1).lower()
            conf = int(float(m1.group(2)) * 100) if float(m1.group(2)) <= 1.0 else int(float(m1.group(2)))
            x = int(m1.group(3))
            y = int(m1.group(4))
            w = int(m1.group(5)) if m1.group(5) else 32
            h = int(m1.group(6)) if m1.group(6) else 32
            self.root.after(0, self.add_detection, lbl, x, y, w, h, conf)
            return

        # Format 2: Bracket-first format: [x: 12, y: 34, width: 20, height: 25, value: 0.92] (person)
        m2 = re.search(r'\[\s*x:\s*(\d+),\s*y:\s*(\d+)(?:,\s*width:\s*(\d+))?(?:,\s*height:\s*(\d+))?(?:,\s*value:\s*([\d\.]+))?\s*\]\s*\(([a-zA-Z_]+)\)', line)
        if m2:
            x = int(m2.group(1))
            y = int(m2.group(2))
            w = int(m2.group(3)) if m2.group(3) else 32
            h = int(m2.group(4)) if m2.group(4) else 32
            conf = int(float(m2.group(5)) * 100) if m2.group(5) else 85
            lbl = m2.group(6).lower()
            self.root.after(0, self.add_detection, lbl, x, y, w, h, conf)
            return

        # Format 3: JSON format (SenseCraft SSCMA packets & custom JSON)
        if "{" in line:
            try:
                s = line.find('{')
                e = line.rfind('}')
                if s != -1 and e != -1:
                    raw_json = line[s:e+1]
                    data = json.loads(raw_json)
                    payload = data.get("data", data)
                    
                    lbl = data.get("label", "").lower()
                    if lbl:
                        x = int(data.get("x", 48))
                        y = int(data.get("y", 48))
                        w = int(data.get("width", data.get("w", 32)))
                        h = int(data.get("height", data.get("h", 32)))
                        conf = float(data.get("value", data.get("score", 0.8)))
                        conf = int(conf * 100) if conf <= 1.0 else int(conf)
                        self.root.after(0, self.add_detection, lbl, x, y, w, h, conf)
                        return

                    boxes = payload.get("boxes", [])
                    for b in boxes:
                        if isinstance(b, list) and len(b) >= 6:
                            target_id = int(b[5])
                            cname = INDEX_TO_CLASS.get(target_id, f"target_{target_id}").lower()
                            if target_id == 0 and "person" not in cname:
                                cname = "person"
                            conf = int(b[4]) if int(b[4]) <= 100 else int(float(b[4]) * 100)
                            self.root.after(0, self.add_detection, cname, int(b[0]), int(b[1]), int(b[2]), int(b[3]), conf)
                        elif isinstance(b, dict):
                            target_id = int(b.get("target", 0))
                            cname = INDEX_TO_CLASS.get(target_id, b.get("name", "unknown")).lower()
                            if target_id == 0 and "person" not in cname:
                                cname = "person"
                            score = float(b.get("score", 0.8))
                            conf = int(score * 100) if score <= 1.0 else int(score)
                            self.root.after(0, self.add_detection, cname, int(b.get("x", 48)), int(b.get("y", 48)), int(b.get("w", 32)), int(b.get("h", 32)), conf)

                    classes = payload.get("classes", [])
                    for item in classes:
                        if isinstance(item, list) and len(item) >= 2:
                            score = float(item[0])
                            conf = int(score * 100) if score <= 1.0 else int(score)
                            target_id = int(item[1])
                            cname = INDEX_TO_CLASS.get(target_id, f"class_{target_id}").lower()
                            if target_id == 0 and "person" not in cname:
                                cname = "person"
                            self.root.after(0, self.add_detection, cname, 48, 48, 32, 32, conf)
            except Exception:
                pass

    def add_detection(self, label, x, y, w, h, conf):
        color = CLASS_COLORS.get(label.lower(), "#00FFCC")
        audio_info = AUDIO_CATALOG.get(label.lower(), ("----", f"{label.capitalize()} detected", "OBSTACLE"))
        track, alert_text, priority = audio_info

        # Add to active boxes with expiration timestamp (lasts 0.6s on radar)
        expires = time.time() + 0.6

        # Auto-detect coordinate space (if coordinates exceed 130, assume 256 or 192 base; otherwise 128)
        base_dim = 192.0 if (x + w > 140 or y + h > 140) else 128.0
        scale = 480.0 / base_dim

        x0 = int(x * scale)
        y0 = int(y * scale)
        x1 = min(480, int((x + w) * scale))
        y1 = min(480, int((y + h) * scale))

        # Spatial direction determination (Left, Center, Right)
        cx = (x0 + x1) // 2
        if cx < 160:
            dir_str = "LEFT"
        elif cx > 320:
            dir_str = "RIGHT"
        else:
            dir_str = "CENTER"

        # Distance estimation based on bounding box size / area
        rel_area = (w * h) / (base_dim * base_dim)
        if rel_area > 0.15 or h > (base_dim * 0.4):
            dist_str = f"CLOSE (~1.0m) [{dir_str}]"
            dist_color = "#FF3333"
        elif rel_area > 0.04 or h > (base_dim * 0.2):
            dist_str = f"MEDIUM (~1.8m) [{dir_str}]"
            dist_color = "#FFAA00"
        else:
            dist_str = f"FAR (>2.5m) [{dir_str}]"
            dist_color = "#00FF88"

        self.active_boxes = [(x0, y0, x1, y1, label, conf, color, expires, dir_str)]

        # Update UI labels
        self.det_label.config(text=f"{label.upper()} ({conf}% confidence)", fg=color)
        self.track_label.config(text=f"DFPlayer Track: {track} ({priority})")
        self.alert_label.config(text=f"Earphone Voice: \"{alert_text}\"")
        self.dist_label.config(text=f"Spatial Position: {dist_str}", fg=dist_color)

        # Log to serial listbox
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] *** {label.upper():8s} ({conf}%) | {dist_str[:16]} | {track} ***"
        self.log_list.insert(0, log_entry)

        # Speak alert if enabled
        if self.speech_enabled.get():
            now = time.time()
            last = self.last_speech_time.get(label.lower(), 0)
            if (now - last) > self.speech_cooldown:
                self.last_speech_time[label.lower()] = now
                threading.Thread(target=self.speak, args=(alert_text,), daemon=True).start()

    def simulate_person_detection(self):
        """Simulate a test detection so user can verify speech audio and UI instantly."""
        self.add_detection("person", 36, 20, 56, 70, 88)

    def update_frame(self):
        """Main rendering loop: draws spatial radar + active detections."""
        if not self.running:
            return

        now = time.time()
        self.active_boxes = [b for b in self.active_boxes if b[7] > now]

        self.canvas.delete("all")

        # 1. Optional laptop webcam overlay
        has_camera_frame = False
        if self.webcam_enabled.get() and CV2_AVAILABLE and PIL_AVAILABLE and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                h, w, _ = frame.shape
                min_dim = min(h, w)
                crop = frame[(h - min_dim)//2 : (h + min_dim)//2, (w - min_dim)//2 : (w + min_dim)//2]
                resized = cv2.resize(crop, (480, 480))
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                self.current_photo = ImageTk.PhotoImage(image=img)
                self.canvas.create_image(0, 0, image=self.current_photo, anchor="nw")
                has_camera_frame = True

        # 2. Draw high-tech Assistive Vision Radar Grid
        grid_color = "#444444" if has_camera_frame else "#1A2634"
        accent_color = "#00FFCC"

        # Concentric distance zones
        for i, dist_lbl in [(1, "CLOSE (1m)"), (2, "MEDIUM (2m)"), (3, "FAR (3m)")]:
            r = i * 70
            self.canvas.create_oval(240 - r, 240 - r, 240 + r, 240 + r, outline=grid_color, width=1, dash=(2, 4))
            self.canvas.create_text(245, 240 - r + 8, text=dist_lbl, fill="#556677", font=("Consolas", 7))

        # Vertical sector dividers (Left, Center, Right)
        self.canvas.create_line(160, 0, 160, 480, fill=grid_color, width=1, dash=(3, 6))
        self.canvas.create_line(320, 0, 320, 480, fill=grid_color, width=1, dash=(3, 6))
        self.canvas.create_text(80, 15, text="[LEFT SECTOR]", fill="#556677", font=("Consolas", 8, "bold"))
        self.canvas.create_text(240, 15, text="[CENTER PATHWAY]", fill="#00FFCC", font=("Consolas", 8, "bold"))
        self.canvas.create_text(400, 15, text="[RIGHT SECTOR]", fill="#556677", font=("Consolas", 8, "bold"))

        # Smart stick base indicator at bottom
        self.canvas.create_rectangle(140, 452, 340, 474, fill="#0F172A", outline=accent_color, width=1)
        self.canvas.create_text(240, 463, text="SMART STICK SENSOR POSITION", fill=accent_color, font=("Consolas", 8, "bold"))

        # 3. Draw active detected objects
        for box in self.active_boxes:
            x0, y0, x1, y1, label, conf, color, _, dir_str = box
            # Glowing bounding box
            self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=3)
            # Centroid point
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            self.canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=color, outline="#FFFFFF")
            # Label tag
            tag_w = min(150, max(110, (x1 - x0)))
            self.canvas.create_rectangle(x0, max(0, y0 - 22), x0 + tag_w, y0, fill=color, outline=color)
            self.canvas.create_text(x0 + tag_w//2, max(10, y0 - 11), text=f"{label.upper()} {conf}%", 
                                    fill="#000000", font=("Consolas", 9, "bold"))

        # 4. If idle / no board connected
        if not self.ser or not self.ser.is_open:
            self.canvas.create_rectangle(50, 190, 430, 290, fill="#161616", outline="#333333", width=2)
            self.canvas.create_text(240, 220, text="GROVE VISION AI V2 DISCONNECTED",
                                    fill="#FFAA00", font=("Consolas", 11, "bold"))
            self.canvas.create_text(240, 248, text="Plug Grove Vision AI V2 into USB-C to stream.",
                                    fill="#CCCCCC", font=("Consolas", 9))
            self.canvas.create_text(240, 270, text="Click 'Test Sound' to verify speech audio.",
                                    fill="#00FFCC", font=("Consolas", 9, "bold"))

        # Schedule next frame in 33ms (~30 FPS)
        self.root.after(33, self.update_frame)

    def update_timing(self, line):
        self.perf_label.config(text=f"NPU Performance: {line[:55]}")

    def speak(self, text):
        try:
            cmd = ["powershell", "-NoProfile", "-Command", f"(New-Object -ComObject SAPI.SpVoice).Speak('{text}')"]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def on_closing(self):
        self.running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
        with self.ser_lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(b"b\r\n") # Stop impulse
                    self.ser.close()
                except Exception:
                    pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DrishtiVisionGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
