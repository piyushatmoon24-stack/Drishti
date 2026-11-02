"""
Drishti Audio Asset Generator (Indian Voice & Bilingual Edition)
Generates all 50 MP3 voice prompts for the DFPlayer Mini MicroSD card.
Outputs to: sdcard_mp3/MP3/0001.mp3 through sdcard_mp3/MP3/0050.mp3

Supported Modes:
1. bilingual       : English + Hindi (e.g. "Caution, stairs down. सावधान, नीचे सीढ़ियां।")
2. indian_english : Clear Indian English accent (e.g. "Caution, stairs going down ahead")
3. hindi          : Pure Hindi (e.g. "सावधान, आगे नीचे सीढ़ियां हैं")

Default Voice: hi-IN-SwaraNeural (Warm, clear Indian neural voice for bilingual/Hindi)
Alternative Voice: en-IN-NeerjaExpressiveNeural (Indian English accent)
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "data" / "classes_config.json"
OUTPUT_DIR = BASE_DIR / "sdcard_mp3" / "MP3"

def load_classes():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

async def generate_with_edge_tts(classes, mode="bilingual", voice=None, rate="+0%"):
    import edge_tts

    # Select appropriate voice based on mode if not explicitly overridden
    if voice is None:
        if mode == "indian_english":
            voice = "en-IN-NeerjaExpressiveNeural"
        elif mode == "hindi":
            voice = "hi-IN-SwaraNeural"
        else: # bilingual
            voice = "hi-IN-SwaraNeural"

    print(f"[*] Generating Audio Assets...")
    print(f"[*] Mode: {mode.upper()}")
    print(f"[*] Voice: {voice} (Authentic Indian Accent)")
    print(f"[*] Speech Rate: {rate}")
    print(f"[*] Output Directory: {OUTPUT_DIR}\n")

    total = len(classes)
    for idx, item in enumerate(classes, 1):
        track_id = item["id"]
        
        # Select prompt based on mode
        if mode == "indian_english":
            text = item.get("voice_prompt_en", item["voice_prompt"])
        elif mode == "hindi":
            text = item.get("voice_prompt_hi", item["voice_prompt"])
        else: # bilingual
            text = item["voice_prompt"]

        out_file = OUTPUT_DIR / f"{track_id}.mp3"
        print(f"[{idx:02d}/{total}] {track_id}.mp3 -> \"{text}\"")
        
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(str(out_file))

    print(f"\n[+] Successfully generated all {total} audio files with {voice}!")

def main():
    parser = argparse.ArgumentParser(description="Generate Drishti Voice Prompts in Indian Accent / Bilingual")
    parser.add_argument(
        "--mode", 
        choices=["bilingual", "indian_english", "hindi"], 
        default="bilingual",
        help="Voice mode: bilingual (English+Hindi, recommended), indian_english, or hindi"
    )
    parser.add_argument(
        "--voice", 
        type=str, 
        default=None,
        help="Custom voice (e.g., hi-IN-SwaraNeural, hi-IN-MadhurNeural, en-IN-NeerjaExpressiveNeural, en-IN-PrabhatNeural)"
    )
    parser.add_argument(
        "--rate", 
        type=str, 
        default="+0%",
        help="Speech rate adjustment (e.g. '+5%%' or '-5%%')"
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    classes = load_classes()
    print(f"[+] Loaded {len(classes)} classes from {CONFIG_PATH}")

    try:
        import edge_tts
        asyncio.run(generate_with_edge_tts(classes, mode=args.mode, voice=args.voice, rate=args.rate))
    except ImportError:
        print("[-] edge-tts is required. Run: pip install edge-tts")
        sys.exit(1)

if __name__ == "__main__":
    main()
