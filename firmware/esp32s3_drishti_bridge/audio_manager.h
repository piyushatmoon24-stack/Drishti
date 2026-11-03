#ifndef AUDIO_MANAGER_H
#define AUDIO_MANAGER_H

#include <Arduino.h>
#include "config.h"
#include "dfplayer_driver.h"
#include "vision_ai_parser.h"

class AudioManager {
private:
  DFPlayerDriver* _player;
  unsigned long   _lastGlobalAnnounce;
  unsigned long   _lastClassAnnounce[CATALOG_RESERVE_CLASSES + 1];
  uint16_t        _lastAnnouncedClass;

  unsigned long getClassCooldown(uint8_t priority) {
    if (priority == 1) return HAZARD_CLASS_COOLDOWN;
    if (priority == 2) return DEFAULT_CLASS_COOLDOWN;
    return DEFAULT_CLASS_COOLDOWN + 1000;
  }

public:
  AudioManager() : _player(nullptr), _lastGlobalAnnounce(0), _lastAnnouncedClass(0) {
    for (int i = 0; i <= CATALOG_RESERVE_CLASSES; i++) {
      _lastClassAnnounce[i] = 0;
    }
  }

  void begin(DFPlayerDriver* player) {
    _player = player;
  }

  void processDetection(const Detection& det) {
    if (!_player || det.classId == 0 || det.classId > CATALOG_RESERVE_CLASSES) {
      return;
    }

    unsigned long now = millis();

    // Check if player is busy
    if (_player->isBusy()) {
      if (det.priority > 1) {
        return;
      }
      _player->stop();
      delay(40);
    }

    // Minimum global interval between any two speech alerts
    unsigned long elapsed = now - _lastGlobalAnnounce;
    if (elapsed < GLOBAL_ANNOUNCE_COOLDOWN) {
      if (det.priority > 1 || elapsed < 600) {
        return;
      }
    }

    // Per-class cooldown to suppress repetitive chatter
    unsigned long cooldown = getClassCooldown(det.priority);
    if ((now - _lastClassAnnounce[det.classId]) < cooldown) {
      return;
    }

    DEBUG_PRINTF("[Audio] Triggering class %04d (%s) | Conf: %d%%\n",
                 det.classId, VisionAIParser::getClassNameById(det.classId), det.confidence);

    _player->playMp3Folder(det.classId);

    _lastGlobalAnnounce = now;
    _lastClassAnnounce[det.classId] = now;
    _lastAnnouncedClass = det.classId;

    #ifdef PIN_STATUS_LED
      digitalWrite(PIN_STATUS_LED, LED_STATE_ON);
      delay(15);
      digitalWrite(PIN_STATUS_LED, LED_STATE_OFF);
    #endif
  }

  void forcePlay(uint16_t classId, uint8_t confidence = 95) {
    if (!_player) return;

    Detection simDet;
    simDet.classId = classId;
    simDet.confidence = confidence;
    simDet.x = 0; simDet.y = 0;
    simDet.w = 50; simDet.h = 50;
    simDet.priority = VisionAIParser::getPriority(classId);

    if (_player->isBusy()) _player->stop();
    delay(30);

    DEBUG_PRINTF("[Audio] Manual play class %04d (%s)\n",
                 classId, VisionAIParser::getClassNameById(classId));
    _player->playMp3Folder(classId);

    _lastGlobalAnnounce = millis();
    _lastClassAnnounce[classId] = millis();
  }
};

#endif // AUDIO_MANAGER_H
