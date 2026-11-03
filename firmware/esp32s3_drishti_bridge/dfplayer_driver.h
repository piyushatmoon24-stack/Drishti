#ifndef DFPLAYER_DRIVER_H
#define DFPLAYER_DRIVER_H

#include <Arduino.h>
#include "config.h"

class DFPlayerDriver {
private:
  HardwareSerial* _serial;
  int _busyPin;
  uint8_t _currentVolume;
  bool _ready;

  void sendCommand(uint8_t cmd, uint8_t feedback, uint16_t param) {
    if (!_serial || !_ready) return;

    uint8_t paramH = (uint8_t)(param >> 8);
    uint8_t paramL = (uint8_t)(param & 0xFF);

    uint16_t sum = 0xFF + 0x06 + cmd + feedback + paramH + paramL;
    uint16_t checksum = (uint16_t)(0 - sum);

    uint8_t packet[10] = {
      0x7E,
      0xFF,
      0x06,
      cmd,
      feedback,
      paramH,
      paramL,
      (uint8_t)(checksum >> 8),
      (uint8_t)(checksum & 0xFF),
      0xEF
    };

    _serial->write(packet, 10);
    _serial->flush();
    delay(30);
  }

public:
  DFPlayerDriver() : _serial(nullptr), _busyPin(-1), _currentVolume(DEFAULT_VOLUME), _ready(false) {}

  void begin(HardwareSerial* serialPort, int rxPin, int txPin, int busyPin = -1) {
    _serial = serialPort;
    _busyPin = busyPin;

    if (_busyPin >= 0) {
      pinMode(_busyPin, INPUT_PULLUP);
    }

    _serial->begin(DFPLAYER_BAUDRATE, SERIAL_8N1, rxPin, txPin);
    _ready = true;

    delay(1200); // Allow DFPlayer onboard DSP and SD card to mount

    sendCommand(0x0C, 0x00, 0x0000); // Reset
    delay(400);

    sendCommand(0x09, 0x00, 0x0002); // Select SD Card source
    delay(150);

    setVolume(_currentVolume);
  }

  void setVolume(uint8_t volume) {
    if (volume > 30) volume = 30;
    _currentVolume = volume;
    sendCommand(0x06, 0x00, volume);
  }

  void playMp3Folder(uint16_t trackNumber) {
    if (trackNumber == 0 || trackNumber > 9999) return;
    sendCommand(0x12, 0x00, trackNumber); // Play /MP3/xxxx.mp3
  }

  void stop() {
    sendCommand(0x16, 0x00, 0x0000);
  }

  bool isBusy() {
    if (_busyPin >= 0) {
      return (digitalRead(_busyPin) == LOW);
    }
    return false;
  }

  bool isReady() { 
    return _ready; 
  }
};

#endif // DFPLAYER_DRIVER_H
