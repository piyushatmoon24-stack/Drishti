"""
Drishti Smart Stick - Official Edge Impulse Firmware Flasher
Flashes the Edge Impulse multi-class scenario firmware to Seeed Grove Vision AI Module V2.
Enables standalone, multi-object detection on Himax WiseEye2 (Ethos-U55 NPU).
"""

import os
import sys
import subprocess
import argparse
import time
import serial.tools.list_ports

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EI_DIR = os.path.join(BASE_DIR, "tools", "edge_impulse_firmware")
XMODEM_SCRIPT = os.path.join(EI_DIR, "xmodem", "xmodem_send.py")
FIRMWARE_IMG = os.path.join(EI_DIR, "firmware.img")
MODEL_TFLITE = os.path.join(EI_DIR, "model_vela.tflite")

def find_ch343_ports():
    ports = list(serial.tools.list_ports.comports())
    ch343 = [p for p in ports if "ch343" in p.description.lower() or "ch34" in p.description.lower()]
    if ch343:
        return ch343
    return ports

def main():
    parser = argparse.ArgumentParser(description="Drishti Edge Impulse Flasher")
    parser.add_argument("--port", type=str, default=None, help="COM port (e.g. COM3)")
    parser.add_argument("--yes", "-y", action="store_true", help="Bypass prompts")
    args = parser.parse_args()

    print("=" * 68)
    print("   DRISHTI: EDGE IMPULSE VISION AI V2 FIRMWARE FLASHER")
    print("   Multi-Object Edge AI for Himax WiseEye2 / Ethos-U55 NPU")
    print("   100% OFFLINE ON HARDWARE - NO PC STREAMING REQUIRED")
    print("=" * 68)
    print()

    if not os.path.exists(XMODEM_SCRIPT):
        print(f"[!] Error: XModem script not found at {XMODEM_SCRIPT}")
        sys.exit(1)

    if not os.path.exists(FIRMWARE_IMG):
        print(f"[!] Error: firmware.img not found at {FIRMWARE_IMG}")
        sys.exit(1)

    if not os.path.exists(MODEL_TFLITE):
        print(f"[!] Error: model_vela.tflite not found at {MODEL_TFLITE}")
        sys.exit(1)

    # 1. Close any running preview scripts that could lock COM3
    try:
        subprocess.run(["taskkill", "/F", "/FI", "WINDOWTITLE eq *preview_drishti_vision*"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    selected_port = args.port
    if not selected_port:
        print("[*] Checking USB connection for Grove Vision AI Module V2...")
        ports = find_ch343_ports()
        
        if not ports:
            print("\n" + "=" * 68)
            print(" [ACTION NEEDED] BOARD NOT DETECTED VIA USB")
            print("--------------------------------------------------------------------")
            print(" 1. Take your Grove Vision AI Module V2.")
            print(" 2. Plug a USB-C data cable into the board and into your computer.")
            print(" 3. Waiting for board to appear...")
            print("=" * 68)
            
            while not ports:
                time.sleep(1.2)
                ports = find_ch343_ports()
                print(".", end="", flush=True)

            print("\n")

        selected_port = ports[0].device
        print(f"[+] Detected Board: {selected_port} ({ports[0].description})")

    print(f"\n[*] Target Port:  {selected_port}")
    print(f"[*] Firmware:     {os.path.basename(FIRMWARE_IMG)} ({os.path.getsize(FIRMWARE_IMG):,} bytes)")
    print(f"[*] Model Vela:   {os.path.basename(MODEL_TFLITE)} ({os.path.getsize(MODEL_TFLITE):,} bytes)")
    print(f"[*] Class Count:  8 Active Pristine Classes (car, chair, door, motorcycle, person, pole, stairs, table)")
    print(f"[*] Safety Note:  Dog permanently pruned to eliminate pedestrian/dog confusion.")
    print()
    print("=" * 68)
    print(" [CRITICAL INSTRUCTION FOR HIMAX WISEEYE2 BOOTLOADER]")
    print("--------------------------------------------------------------------")
    print(" In a few seconds, the screen will display:")
    print("     Please press reset button!!")
    print()
    print(" When that appears, immediately press the tiny physical button")
    print(" labeled 'RST' (Reset) on the Grove Vision AI Module V2 board ONCE.")
    print()
    print(" Do NOT unplug the board while the progress bar runs (0% -> 100%).")
    print("=" * 68)
    print()

    if not args.yes:
        input("Press Enter to begin flashing...")

    cmd = [
        sys.executable,
        os.path.join("xmodem", "xmodem_send.py"),
        f"--port={selected_port}",
        "--baudrate=921600",
        "--protocol=xmodem",
        "--file=firmware.img",
        "--model=model_vela.tflite 0x200000 0x00000"
    ]

    print("\n[*] Initializing XModem serial connection at 921600 baud...")
    res = subprocess.run(cmd, cwd=EI_DIR)

    if res.returncode == 0:
        print("\n" + "=" * 68)
        print(" [SUCCESS] Edge Impulse firmware and 8-class model flashed successfully!")
        print(" The board has rebooted and is now running standalone Edge AI!")
        print(" You can now launch preview_drishti_vision.bat to view live detections!")
        print("=" * 68)
    else:
        print(f"\n[!] Flashing exited with code: {res.returncode}")
        print("    If it timed out, run again and make sure to press the RST button")
        print("    on the board once when prompted.")

if __name__ == "__main__":
    main()
