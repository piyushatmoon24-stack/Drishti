#ifndef AUDIO_MANAGER_H
#define AUDIO_MANAGER_H

#include <Arduino.h>
#include "config.h"
#include "dfplayer_driver.h"
#include "vision_ai_parser.h"

// ============================================================
// AudioManager: Throttles and routes detections to DFPlayer.
//
// Rules (in order):
//  1. If DFPlayer is busy playing: only Priority-1 hazard interrupts.
//  2. Global cooldown: minimum gap between any two audio alerts.
//  3. Per-class cooldown: suppress repeated announcements of same object.
//  4. If all checks pass: play the mapped MP3 track.
// ============================================================

class AudioManager {
private:
  DFPlayerDriver*   _player;
  unsigned long     _lastGlobalAnnounce;
  unsigned long     _lastClassAnnounce[TOTAL_CLASSES + 1];
  uint16_t          _lastAnnouncedClass;

  // Returns cooldown duration (ms) based on hazard priority
  unsigned long getClassCooldown(uint8_t priority) {
    if (priority == 1) return HAZARD_CLASS_COOLDOWN;   // 1500ms for critical hazards
    if (priority == 2) return DEFAULT_CLASS_COOLDOWN;  // 3500ms for navigation obstacles
    return DEFAULT_CLASS_COOLDOWN + 1000;              // 4500ms for stationary furniture
  }

public:
  AudioManager() : _player(nullptr), _lastGlobalAnnounce(0), _lastAnnouncedClass(0) {
    for (int i = 0; i <= TOTAL_CLASSES; i++) {
      _lastClassAnnounce[i] = 0;
    }
  }

  void begin(DFPlayerDriver* player) {
    _player = player;
  }

  // Main entry point: called whenever vision parser reports a detection.
  // Applies throttle rules then triggers DFPlayer audio if allowed.
  void processDetection(const Detection& det) {
    if (!_player) return;

    // Bounds check: classId must be valid
    if (det.classId == 0 || det.classId > TOTAL_CLASSES) return;

    unsigned long now = millis();

    // ---- Rule 1: DFPlayer busy check (if busy pin is connected and enabled) ----
    if (_player->isBusy()) {
      return; // Audio is currently playing — wait until done
    }

    // ---- Rule 2: Global minimum gap between any two alerts (Strict 2.0s pause) ----
    // Guarantees no repetitive commands reach the DFPlayer while audio is playing
    unsigned long globalGap = now - _lastGlobalAnnounce;
    if (globalGap < GLOBAL_ANNOUNCE_COOLDOWN) {
      return;
    }

    // ---- Rule 3: Per-class cooldown (suppress same object spam) ----
    unsigned long cooldown = getClassCooldown(det.priority);
    if ((now - _lastClassAnnounce[det.classId]) < cooldown) {
      return;
    }

    // ---- All checks passed: play audio ----
    DEBUG_PRINTF("[Audio] Playing class %04d '%s' | Conf: %d%% | Pri: %d\n",
                 det.classId,
                 VisionAIParser::getClassNameById(det.classId),
                 det.confidence,
                 det.priority);

    _player->playMp3Folder(det.classId);

    _lastGlobalAnnounce          = now;
    _lastClassAnnounce[det.classId] = now;
    _lastAnnouncedClass          = det.classId;

    // Pulse the onboard LED on every audio alert (Active-LOW: LOW=ON)
    #ifdef PIN_STATUS_LED
      digitalWrite(PIN_STATUS_LED, LED_STATE_ON);
      delay(15);
      digitalWrite(PIN_STATUS_LED, LED_STATE_OFF);
    #endif
  }

  // Force-play a track immediately (for test console), bypassing all cooldowns
  void forcePlay(uint16_t classId, uint8_t confidence = 95) {
    if (!_player) return;
    Detection simDet;
    simDet.classId    = classId;
    simDet.confidence = confidence;
    simDet.x = 0; simDet.y = 0;
    simDet.w = 50; simDet.h = 50;
    simDet.priority = VisionAIParser::getPriority(classId);

    if (_player->isBusy()) _player->stop();
    delay(40);
    DEBUG_PRINTF("[Audio] Force-playing class %04d '%s'\n",
                 classId, VisionAIParser::getClassNameById(classId));
    _player->playMp3Folder(classId);
    _lastGlobalAnnounce          = millis();
    _lastClassAnnounce[classId]  = millis();
  }
};

#endif // AUDIO_MANAGER_H
