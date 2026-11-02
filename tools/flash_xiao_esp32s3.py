"""
Drishti Smart Stick - 1-Click XIAO ESP32-S3 Flasher
Automatically detects Seeed Studio XIAO ESP32-S3, uploads compiled firmware
using high-speed esptool or arduino-cli, and opens an instant interactive serial test console.
"""

import sys
import os
import glob
import time
import shutil
import subprocess
import serial.tools.list_ports

SKETCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "firmware", "esp32s3_drishti_bridge"))
BUILD_DIR = os.path.join(SKETCH_DIR, "build", "esp32.esp32.XIAO_ESP32S3")
MERGED_BIN = os.path.join(BUILD_DIR, "esp32s3_drishti_bridge.ino.merged.bin")
FQBN = "esp32:esp32:XIAO_ESP32S3:CDCOnBoot=cdc"

def find_esptool():
    """Locate esptool.exe from Arduino15 package or PATH."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        pattern = os.path.join(local_app_data, "Arduino15", "packages", "esp32", "tools", "esptool_py", "*", "esptool.exe")
        matches = glob.glob(pattern)
        if matches:
            return matches[-1]
    
    which_path = shutil.which("esptool.exe") or shutil.which("esptool")
    if which_path:
        return which_path

    return None

def find_arduino_cli():
    """Locate arduino-cli.exe."""
    standard_paths = [
        r"C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe",
    ]
    for p in standard_paths:
        expanded = os.path.expandvars(p)
        if os.path.isfile(expanded):
            return expanded
            
    return shutil.which("arduino-cli.exe") or shutil.which("arduino-cli")

def print_header():
    print("=" * 65)
    print("   DRISHTI: XIAO ESP32-S3 1-CLICK FIRMWARE FLASHER")
    print("=" * 65)
    print(f" Sketch Path: {SKETCH_DIR}")
    print(f" Target FQBN: {FQBN}")
    if os.path.exists(MERGED_BIN):
        print(f" Precompiled: {os.path.basename(MERGED_BIN)} ({os.path.getsize(MERGED_BIN):,} bytes)")
    print("=" * 65)
    print()

def find_xiao_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None
    
    # Priority: search for Seeed, XIAO, or ESP32-S3 JTAG/CDC
    for p in ports:
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        if "seeed" in desc or "xiao" in desc or "esp32-s3" in desc or "303a:" in hwid:
            return p.device
            
    # Fallback: if only one USB serial device is plugged in
    if len(ports) == 1:
        return ports[0].device
        
    return None

def wait_for_board():
    port = find_xiao_port()
    if port:
        return port
        
    print("[*] No XIAO ESP32-S3 detected on USB.")
    print("[*] Please connect your XIAO ESP32-S3 board to your PC via USB-C cable.")
    print("    Waiting for device connection (Press Ctrl+C to abort)...", end="", flush=True)
    
    while True:
        time.sleep(1)
        print(".", end="", flush=True)
        port = find_xiao_port()
        if port:
            print(f"\n[+] Device detected on {port}!")
            return port

def upload_firmware(port):
    esptool_bin = find_esptool()
    arduino_cli = find_arduino_cli()
    
    # Method 1: High-Speed direct flash using esptool if merged binary exists
    if esptool_bin and os.path.isfile(MERGED_BIN):
        print(f"\n[*] Flashing precompiled firmware to {port} using esptool (921,600 baud)...")
        cmd = [
            esptool_bin,
            "--chip", "esp32s3",
            "--port", port,
            "--baud", "921600",
            "--before", "default_reset",
            "--after", "hard_reset",
            "write_flash",
            "-z",
            "--flash_mode", "dio",
            "--flash_freq", "80m",
            "--flash_size", "8MB",
            "0x0", MERGED_BIN
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print("[+] SUCCESS: Drishti firmware uploaded successfully via esptool!")
            return True
        else:
            print("[-] esptool returned an error, falling back to arduino-cli...")
            if res.stderr:
                print(res.stderr.strip())

    # Method 2: Arduino CLI upload
    if arduino_cli:
        print(f"\n[*] Uploading firmware to {port} using arduino-cli...")
        cmd = [
            arduino_cli,
            "upload",
            "-p", port,
            "--fqbn", FQBN,
            "--input-dir", BUILD_DIR,
            SKETCH_DIR
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print("[+] SUCCESS: Drishti firmware uploaded successfully via arduino-cli!")
            return True
        else:
            print("[-] Arduino-CLI upload failed. Error details:")
            print(res.stderr or res.stdout)
            
    print("\n[!] TROUBLESHOOTING TIP:")
    print("    If upload timed out or failed to connect to ESP32-S3 ROM:")
    print("    1. Press and HOLD the tiny 'B' (Boot) button on the XIAO ESP32-S3.")
    print("    2. While holding 'B', press the 'R' (Reset) button once, then release 'B'.")
    print("    3. Run this script again.")
    print("\n    Alternatively, upload directly using Arduino IDE:")
    print(f"    - Open {SKETCH_DIR}\\esp32s3_drishti_bridge.ino")
    print("    - Board: 'XIAO_ESP32S3', USB CDC On Boot: 'Enabled'")
    print("    - Click Upload.")
    return False

def open_serial_test(port):
    print("\n" + "=" * 65)
    print(" DRISHTI SERIAL TEST CONSOLE")
    print("=" * 65)
    print(" You can test the standalone board right now:")
    print(" - Type '1'  + Enter to simulate 'stairs' hazard voice alert (0001.mp3)")
    print(" - Type '6'  + Enter to simulate 'pole' warning alert (0006.mp3)")
    print(" - Type '8'  + Enter to simulate 'door' alert (0008.mp3)")
    print(" - Type '13' + Enter to simulate 'person' alert (0013.mp3)")
    print(" - Type '18' + Enter to simulate 'motorcycle' alert (0018.mp3)")
    print(" - Type '19' + Enter to simulate 'car' alert (0019.mp3)")
    print(" - Type '23' + Enter to simulate 'chair' alert (0023.mp3)")
    print(" - Type '26' + Enter to simulate 'table' alert (0026.mp3)")
    print(" - Type 'vol 25' + Enter to set volume")
    print(" - Press Ctrl+C anytime to exit the serial monitor.")
    print("=" * 65)
    
    try:
        import serial
        ser = serial.Serial(port, 115200, timeout=0.2)
        time.sleep(1.0)
        print(f"[+] Connected to Serial Monitor on {port} (115200 baud).")
        
        # Read initial banner
        deadline = time.time() + 2.0
        while time.time() < deadline:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"[XIAO] {line}")
                
        import threading
        stop_thread = False
        
        def read_loop():
            while not stop_thread:
                try:
                    if ser.in_waiting:
                        text = ser.readline().decode('utf-8', errors='ignore').strip()
                        if text:
                            print(f"[XIAO] {text}")
                    time.sleep(0.05)
                except Exception:
                    break
                    
        t = threading.Thread(target=read_loop, daemon=True)
        t.start()
        
        print("\nEnter test class ID (or press Enter to finish): ", end="", flush=True)
        while True:
            cmd = sys.stdin.readline().strip()
            if not cmd:
                break
            ser.write((cmd + "\n").encode('utf-8'))
            time.sleep(0.3)
            print("Enter another test class ID (or Enter to finish): ", end="", flush=True)
            
        stop_thread = True
        ser.close()
    except KeyboardInterrupt:
        print("\nExiting Serial Console.")
    except Exception as e:
        print(f"\nSerial monitor notice: {e}")

def main():
    print_header()
    port = wait_for_board()
    success = upload_firmware(port)
    if success:
        time.sleep(1.5)
        open_serial_test(port)

if __name__ == "__main__":
    main()
