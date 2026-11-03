/*
 * =========================================================================
 * DRISHTI: Assistive Vision AI Smart Stick
 * Firmware for Seeed Studio XIAO ESP32-S3 + Grove Vision AI Module V2
 * =========================================================================
 *
 * HOW IT WORKS:
 *   1. Grove Vision AI Module V2 runs the Drishti FOMO model on its NPU
 *      and streams JSON detection results over UART at 921,600 baud.
 *   2. XIAO ESP32-S3 receives and parses those JSON packets (non-blocking).
 *   3. On each valid detection, the Audio Manager selects the correct MP3
 *      track and sends the command to DFPlayer Mini.
 *   4. DFPlayer Mini plays the /MP3/xxxx.mp3 file from the SD card.
 *   5. Audio is output to earphones via the 3.5mm audio jack on DFPlayer.
 *
 * =========================================================================
 * WIRING CONNECTIONS
 * =========================================================================
 *
 * [A] Grove Vision AI Module V2  <-->  XIAO ESP32-S3
 *     XIAO plugs directly into the dual 7-pin socket on Grove Vision AI V2.
 *     Align so BOTH USB-C ports face the SAME direction. Zero external wires.
 *
 *     Socket UART (for live inference streaming):
 *       XIAO D7 (GPIO 44) = UART1 RX  <-- Vision AI TX
 *       XIAO D6 (GPIO 43) = UART1 TX  --> Vision AI RX
 *
 *     Socket I2C (for device info / control):
 *       XIAO D4 (GPIO 5)  = SDA  <-> Vision AI SDA
 *       XIAO D5 (GPIO 6)  = SCL  <-> Vision AI SCL
 *
 * [B] DFPlayer Mini  <-->  XIAO ESP32-S3 (exposed header pins)
 *       XIAO 5V          --> DFPlayer VCC (Pin 1)
 *       XIAO GND         --> DFPlayer GND (Pin 7 or Pin 10)
 *       XIAO D1 (GPIO 2) --> 1kΩ Resistor --> DFPlayer RX (Pin 2)
 *       XIAO D2 (GPIO 3) <-- DFPlayer TX (Pin 3)
 *       XIAO D3 (GPIO 4) <-- DFPlayer BUSY (Pin 16)
 *
 * [C] 3.5mm Earphone Jack  <-->  DFPlayer Mini
 *       DFPlayer DAC_R (Pin 4)  --> Earphone Right (Tip)
 *       DFPlayer DAC_L (Pin 5)  --> Earphone Left  (Ring)
 *       DFPlayer GND   (Pin 7 or Pin 10) --> Earphone Ground (Sleeve)
 *       (Note: Pin 9 is IO1 and Pin 11 is IO2. DAC outputs are strictly Pin 4 & Pin 5!)
 *
 * [D] SD Card (inside DFPlayer Mini slot)
 *       Format: FAT32
 *       Folder: /MP3/
 *       Files:  0001.mp3 (Stairs), 0006.mp3 (Pole), 0008.mp3 (Door),
 *               0013.mp3 (Person), 0018.mp3 (Motorcycle), 0019.mp3 (Car),
 *               0023.mp3 (Chair), 0026.mp3 (Table)
 * =========================================================================
 */

#include <Arduino.h>
#include <Wire.h>
#include "config.h"
#include "dfplayer_driver.h"
#include "vision_ai_parser.h"
#include "audio_manager.h"
#include "Seeed_Arduino_SSCMA.h"

// ---- Hardware Serial Instances ----
HardwareSerial VisionSerial(1);  // UART1: Grove Vision AI V2 socket (D7/D6)
HardwareSerial DFSerial(2);      // UART2: DFPlayer Mini (D1/D2)

// ---- Global Objects ----
DFPlayerDriver dfplayer;
VisionAIParser visionParser;
AudioManager   audioManager;
SSCMA          AI;

static bool sscmaOnline = false;  // true once I2C handshake with Vision AI succeeds

// =========================================================================
void setup() {
  // ---- 1. USB Serial (for Arduino IDE Serial Monitor diagnostics) ----
  DEBUG_SERIAL.begin(115200);
  // Wait up to 1.5s for Serial Monitor to attach (USB CDC on ESP32-S3)
  unsigned long t0 = millis();
  while (!DEBUG_SERIAL && (millis() - t0 < 1500)) delay(10);
  delay(300);

  DEBUG_PRINTLN("\n========================================================");
  DEBUG_PRINTLN("  DRISHTI: Assistive Vision AI (XIAO ESP32-S3 Edition) ");
  DEBUG_PRINTLN("========================================================");

  // ---- 2. Status LED ----
  #ifdef PIN_STATUS_LED
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LED_STATE_OFF);
  #endif

  // ---- 3. DFPlayer Mini ----
  DEBUG_PRINTLN("[Init] Starting DFPlayer Mini...");
  dfplayer.begin(&DFSerial, PIN_DFPLAYER_RX, PIN_DFPLAYER_TX, PIN_DFPLAYER_BUSY);
  // Volume is set inside begin() after DFPlayer boots
  DEBUG_PRINTLN("[Init] DFPlayer ready.");

  // ---- 4. Audio Manager ----
  audioManager.begin(&dfplayer);

  // ---- 5. Grove Vision AI V2: I2C handshake for device info ----
  DEBUG_PRINTLN("[Init] Connecting to Grove Vision AI V2 via I2C socket...");
  Wire.begin(5, 6); // SDA = GPIO 5 (D4), SCL = GPIO 6 (D5)
  Wire.setClock(100000); // 100 kHz (reliable over friction-contact socket)

  for (int attempt = 1; attempt <= 3; attempt++) {
    DEBUG_PRINTF("[Init]   Attempt %d/3...\n", attempt);
    if (AI.begin(&Wire)) {
      DEBUG_PRINTF("[Init] Vision AI connected! Device: %s | Model: %s\n",
                   AI.ID(), AI.name());
      sscmaOnline = true;
      break;
    }
    delay(600);
  }
  if (!sscmaOnline) {
    DEBUG_PRINTLN("[Init] I2C probe failed (no device at 0x62).");
    DEBUG_PRINTLN("       Check: XIAO seated firmly, USB-C ports same direction.");
    DEBUG_PRINTLN("       Will still use UART stream if camera sends data.");
  }

  // ---- 6. Vision UART Stream ----
  // Grove Vision AI V2 streams SSCMA JSON inference results over UART at 921,600 baud.
  // This is the PRIMARY detection channel — non-blocking, runs every loop().
  visionParser.begin(&VisionSerial, PIN_VISION_RX, PIN_VISION_TX);

  // Send AT+INVOKE=-1,0,1 to start continuous inference mode.
  // -1 = loop forever | 0 = all frames | 1 = stream results only (no image data)
  // Note: AT+MODEL=1 is NOT sent — camera already auto-loads model 1 at startup.
  delay(200);
  VisionSerial.println("AT+INVOKE=-1,0,1");
  DEBUG_PRINTLN("[Init] Continuous inference started on Grove Vision AI V2.");

  DEBUG_PRINTLN("[Ready] Drishti is active. Listening for objects...");
  DEBUG_PRINTLN("[Test]  Type a class number in Serial Monitor to test audio:");
  DEBUG_PRINTLN("        1=Stairs  6=Pole  8=Door  13=Person");
  DEBUG_PRINTLN("        18=Moto   19=Car  23=Chair 26=Table");
  DEBUG_PRINTLN("        Or type: vol 20  (to set volume 0-30)\n");
}

// =========================================================================
void loop() {
  // ---- A. Read Vision AI UART Stream ----
  // visionParser.update() reads incoming SSCMA JSON packets from the camera.
  // Returns true + fills `det` when a confident detection is parsed.
  Detection det;
  static unsigned long lastPacketMs = millis();

  if (visionParser.update(det)) {
    lastPacketMs = millis();

    // Log the detection
    DEBUG_PRINTF("[DETECTED] %s (class %04d) | Conf: %d%% | Priority: %d | Box: [%d,%d %dx%d]\n",
                 VisionAIParser::getClassNameById(det.classId),
                 det.classId,
                 det.confidence,
                 det.priority,
                 det.x, det.y, det.w, det.h);

    // Route to Audio Manager (applies cooldown rules, then plays MP3)
    audioManager.processDetection(det);
  }

  // ---- B. Stream Watchdog ----
  // If no UART packets for >4 seconds, resend AT+INVOKE in case camera reset
  if (millis() - lastPacketMs >= 4000) {
    lastPacketMs = millis();
    DEBUG_PRINTLN("[Watchdog] No UART data — resending AT+INVOKE=-1,0,1");
    VisionSerial.println("AT+INVOKE=-1,0,1");
  }

  // ---- C. Heartbeat (every 5 seconds) ----
  static unsigned long lastBeat = 0;
  if (millis() - lastBeat >= 5000) {
    lastBeat = millis();
    DEBUG_PRINTLN("[Heartbeat] Vision AI streaming | Waiting for objects in FOV...");
  }

  // ---- D. Serial Monitor Test Console ----
  // Type a class number (e.g. 13) to simulate a detection and test audio.
  // Type "vol 25" to change volume on the fly.
  if (DEBUG_SERIAL.available()) {
    String input = DEBUG_SERIAL.readStringUntil('\n');
    input.trim();
    if (input.length() == 0) return;

    if (input.startsWith("vol ") || input.startsWith("VOL ")) {
      int vol = input.substring(4).toInt();
      if (vol >= 0 && vol <= 30) {
        dfplayer.setVolume((uint8_t)vol);
        DEBUG_PRINTF("[Console] Volume changed to %d\n", vol);
      } else {
        DEBUG_PRINTLN("[Console] Volume must be 0-30. Example: vol 25");
      }
    } else {
      int testId = input.toInt();
      if (testId >= 1 && testId <= TOTAL_CLASSES) {
        DEBUG_PRINTF("[Console] Testing class %04d (%s)...\n",
                     testId, VisionAIParser::getClassNameById((uint16_t)testId));
        audioManager.forcePlay((uint16_t)testId);
      } else {
        DEBUG_PRINTLN("[Console] Enter a valid class (1-50) or 'vol 0-30'.");
        DEBUG_PRINTLN("          Active classes: 1 6 8 13 18 19 23 26");
      }
    }
  }

  // ---- E. Optional: Ultrasonic + Haptic Reflex Layer ----
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

  delay(4); // Yield to ESP32 RTOS / keep loop tight for UART parsing
}
