#ifndef DFPLAYER_DRIVER_H
#define DFPLAYER_DRIVER_H

#include <Arduino.h>
#include "config.h"

// ============================================================
// DFPlayer Mini Driver
// Communicates via UART at 9600 baud using the YX5200 protocol.
// Hardware wiring:
//   XIAO D1 (GPIO 2) --> 1kΩ Resistor --> DFPlayer RX (Pin 2)
//   XIAO D2 (GPIO 3) <-- DFPlayer TX (Pin 3)
//   XIAO D3 (GPIO 4) <-- DFPlayer BUSY (Pin 16) [LOW=playing, HIGH=idle]
//   XIAO 5V          --> DFPlayer VCC (Pin 1)
//   XIAO GND         --> DFPlayer GND (Pin 7 or Pin 10)
//
// SD Card folder structure for /MP3/ folder:
//   /MP3/0001.mp3  -> Stairs
//   /MP3/0006.mp3  -> Pole
//   /MP3/0008.mp3  -> Door
//   /MP3/0013.mp3  -> Person
//   /MP3/0018.mp3  -> Motorcycle
//   /MP3/0019.mp3  -> Car
//   /MP3/0023.mp3  -> Chair
//   /MP3/0026.mp3  -> Table
//
// Earphone (3.5mm audio jack) connects to DFPlayer:
//   DFPlayer DAC_R (Pin 4)  -> Right channel tip
//   DFPlayer DAC_L (Pin 5)  -> Left channel ring
//   DFPlayer GND   (Pin 7 or Pin 10) -> Sleeve / Ground
//   (Caution: Pin 9 is IO1 and Pin 11 is IO2. DAC outputs are Pin 4 & Pin 5!)
// ============================================================

class DFPlayerDriver {
private:
  HardwareSerial* _serial;
  int _busyPin;
  uint8_t _currentVolume;
  bool _ready;

  // Sends a raw 10-byte YX5200 protocol packet to DFPlayer Mini.
  // No blocking delay inside — caller is responsible for spacing.
  void sendCommand(uint8_t cmd, uint8_t feedback, uint16_t param) {
    if (!_serial || !_ready) return;

    uint8_t paramH = (uint8_t)(param >> 8);
    uint8_t paramL = (uint8_t)(param & 0xFF);

    // Checksum covers: Version + Length + Cmd + Feedback + ParamH + ParamL
    uint16_t sum = 0xFF + 0x06 + cmd + feedback + paramH + paramL;
    uint16_t checksum = (uint16_t)(0 - sum);

    uint8_t packet[10] = {
      0x7E,                        // Start byte
      0xFF,                        // Version
      0x06,                        // Data length (always 6)
      cmd,                         // Command
      feedback,                    // ACK requested (0 = no, 1 = yes)
      paramH,                      // Parameter high byte
      paramL,                      // Parameter low byte
      (uint8_t)(checksum >> 8),    // Checksum high byte
      (uint8_t)(checksum & 0xFF),  // Checksum low byte
      0xEF                         // End byte
    };

    _serial->write(packet, 10);
    _serial->flush();
    // Minimum 30ms inter-command gap: YX5200 chip needs time to process each command
    delay(30);
  }

public:
  DFPlayerDriver() : _serial(nullptr), _busyPin(-1), _currentVolume(DEFAULT_VOLUME), _ready(false) {}

  // Call begin() in setup() AFTER Serial.begin() for USB debug output.
  void begin(HardwareSerial* serialPort, int rxPin, int txPin, int busyPin = -1) {
    _serial  = serialPort;
    _busyPin = busyPin;

    // Configure BUSY pin with internal pull-up:
    // DFPlayer BUSY is active-LOW (LOW = playing, HIGH = idle).
    // INPUT_PULLUP ensures pin reads HIGH (idle) safely when DFPlayer is not connected.
    if (_busyPin >= 0) {
      pinMode(_busyPin, INPUT_PULLUP);
    }

    // Start UART to DFPlayer FIRST, then wait for power-on
    _serial->begin(DFPLAYER_BAUDRATE, SERIAL_8N1, rxPin, txPin);
    _ready = true;

    // DFPlayer Mini requires ~2.0s power-on stabilization to mount the SD card.
    // NOTE: Software reset (0x0C) is intentionally NOT sent here because clone chips
    // (GD3200B, MH2024K, JL AC20BP) crash/freeze their UART receiver upon receiving 0x0C.
    delay(2000);

    // Set default volume (level 24 / 30)
    setVolume(_currentVolume);
    delay(100);

    DEBUG_PRINTLN("[DFPlayer] Initialized cleanly without 0x0C reset crash.");
  }

  // Set playback volume (0 = mute, 30 = maximum)
  void setVolume(uint8_t volume) {
    if (volume > 30) volume = 30;
    _currentVolume = volume;
    sendCommand(0x06, 0x00, volume); // CMD 0x06 = Set volume
    DEBUG_PRINTF("[DFPlayer] Volume set to %d/30\n", volume);
  }

  // Play a track from the /MP3/ folder on the SD card.
  // trackNumber 1 -> /MP3/0001.mp3, 13 -> /MP3/0013.mp3, etc.
  void playMp3Folder(uint16_t trackNumber) {
    if (trackNumber == 0 || trackNumber > 9999) {
      DEBUG_PRINTF("[DFPlayer] Invalid track number: %d\n", trackNumber);
      return;
    }
    DEBUG_PRINTF("[DFPlayer] Playing /MP3/%04d.mp3\n", trackNumber);
    sendCommand(0x12, 0x00, trackNumber); // CMD 0x12 = Play track in /MP3/ folder
  }

  // Universal track playback (CMD 0x03: compatible with clone chips that ignore 0x12)
  void playTrack(uint16_t trackNumber) {
    if (trackNumber == 0 || trackNumber > 9999) return;
    DEBUG_PRINTF("[DFPlayer] Playing root track %d (CMD 0x03)\n", trackNumber);
    sendCommand(0x03, 0x00, trackNumber);
  }

  // Stop current playback immediately
  void stop() {
    sendCommand(0x16, 0x00, 0x0000); // CMD 0x16 = Stop
  }

  // Returns true if DFPlayer is currently playing audio.
  // BUSY pin: LOW = playing, HIGH = idle.
  // If BUSY pin not connected, always returns false (non-blocking mode).
  bool isBusy() {
    if (_busyPin >= 0) {
      return (digitalRead(_busyPin) == LOW);
    }
    return false;
  }

  bool isReady() { return _ready; }
};

#endif // DFPLAYER_DRIVER_H
