#include <Arduino.h>
#include <Wire.h>
#include "config.h"
#include "dfplayer_driver.h"
#include "vision_ai_parser.h"
#include "audio_manager.h"
#include "Seeed_Arduino_SSCMA.h"

// Hardware Serial instances
HardwareSerial VisionSerial(1); // UART1: Socket link to Himax WiseEye2 (D7/D6)
HardwareSerial DFSerial(2);     // UART2: DFPlayer Mini (D1/D2)

DFPlayerDriver dfplayer;
VisionAIParser visionParser;
AudioManager   audioManager;
SSCMA          AI;

static bool sscmaOnline = false;

void setup() {
  DEBUG_SERIAL.begin(115200);
  unsigned long start = millis();
  while (!DEBUG_SERIAL && (millis() - start < 1500)) {
    delay(10);
  }
  delay(200);

  DEBUG_PRINTLN("[System] Booting Drishti Vision Bridge...");

  #ifdef PIN_STATUS_LED
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LED_STATE_OFF);
  #endif

  // Initialize DFPlayer Mini
  dfplayer.begin(&DFSerial, PIN_DFPLAYER_RX, PIN_DFPLAYER_TX, PIN_DFPLAYER_BUSY);
  audioManager.begin(&dfplayer);

  // Probe Grove Vision AI V2 on socket I2C
  Wire.begin(5, 6);
  Wire.setClock(100000);

  for (int attempt = 1; attempt <= 3; attempt++) {
    if (AI.begin(&Wire)) {
      DEBUG_PRINTF("[VisionAI] Connected. ID: %s, Name: %s\n", AI.ID(), AI.name());
      sscmaOnline = true;
      break;
    }
    delay(500);
  }

  if (!sscmaOnline) {
    DEBUG_PRINTLN("[VisionAI] I2C handshake skipped; falling back to direct UART.");
  }

  // Initialize UART stream parser at 921600 baud
  visionParser.begin(&VisionSerial, PIN_VISION_RX, PIN_VISION_TX);
  delay(150);

  // Start continuous inference stream on Himax NPU
  VisionSerial.println("AT+INVOKE=-1,0,1");

  DEBUG_PRINTLN("[System] Drishti online. Listening for detections...");
}

void loop() {
  Detection det;
  static unsigned long lastPacketMs = millis();

  // Read and parse incoming SSCMA JSON frame
  if (visionParser.update(det)) {
    lastPacketMs = millis();
    DEBUG_PRINTF("[Detected] %s (ID %04d) | Conf: %d%% | Box: [%d,%d %dx%d]\n",
                 VisionAIParser::getClassNameById(det.classId),
                 det.classId,
                 det.confidence,
                 det.x, det.y, det.w, det.h);

    audioManager.processDetection(det);
  }

  // Watchdog: re-invoke stream if inactive for over 4.5 seconds
  if (millis() - lastPacketMs >= 4500) {
    lastPacketMs = millis();
    VisionSerial.println("AT+INVOKE=-1,0,1");
  }

  // Periodic heartbeat
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat >= 5000) {
    lastHeartbeat = millis();
    DEBUG_PRINTLN("[Heartbeat] Vision AI streaming active.");
  }

  // Serial Monitor Interactive Test Console
  if (DEBUG_SERIAL.available()) {
    String input = DEBUG_SERIAL.readStringUntil('\n');
    input.trim();

    if (input.startsWith("vol ") || input.startsWith("VOL ")) {
      int vol = input.substring(4).toInt();
      if (vol >= 0 && vol <= 30) {
        dfplayer.setVolume((uint8_t)vol);
        DEBUG_PRINTF("[Console] Volume set to %d\n", vol);
      }
    } else if (input.length() > 0) {
      int testId = input.toInt();
      if (testId > 0 && testId <= CATALOG_RESERVE_CLASSES) {
        audioManager.forcePlay((uint16_t)testId);
      }
    }
  }

  #if ENABLE_HAPTIC_SAFETY
    static unsigned long lastHaptic = 0;
    if (millis() - lastHaptic >= HAPTIC_POLL_INTERVAL_MS) {
      lastHaptic = millis();
      digitalWrite(PIN_ULTRASONIC_TRIG, LOW);
      delayMicroseconds(2);
      digitalWrite(PIN_ULTRASONIC_TRIG, HIGH);
      delayMicroseconds(10);
      digitalWrite(PIN_ULTRASONIC_TRIG, LOW);
      long echo = pulseIn(PIN_ULTRASONIC_ECHO, HIGH, 20000);
      if (echo > 0) {
        long distCm = (long)(echo * 0.0343 / 2.0);
        digitalWrite(PIN_VIBRATION_MOTOR,
                     (distCm > 2 && distCm <= HAPTIC_TRIGGER_DIST_CM) ? HIGH : LOW);
      } else {
        digitalWrite(PIN_VIBRATION_MOTOR, LOW);
      }
    }
  #endif

  delay(4);
}
