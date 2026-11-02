Seeed Grove Vision AI Module V2 (Himax WiseEye2)
------------------------------------------------

Flashing instruction:
1. Connect your board
2. Install the flashing script dependencies:

    pip install -r xmodem/requirements.txt

3. Find the serial port number or path
4. Flash firmware and model file (replace YOUR_BOARD_SERIAL PORT with the proper port number/path)

    python3 xmodem/xmodem_send.py --port=YOUR_BOARD_SERIAL --baudrate=921600 --protocol=xmodem --file=firmware.img --model="model_vela.tflite 0x200000 0x00000"

For more details on how to use this firmware, see the tutorial:
https://docs.edgeimpulse.com/docs/edge-ai-hardware/mcu-+-ai-accelerators/himax-seeed-grove-vision-ai-module-v2-wise-eye-2

(c) Copyright 2024 Edge Impulse Inc., all rights reserved.
