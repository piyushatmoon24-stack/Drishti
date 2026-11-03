#ifndef DRISHTI_CONFIG_H
#define DRISHTI_CONFIG_H

#include <Arduino.h>

// Vision AI UART (Socket link to Himax WiseEye2)
#define PIN_VISION_RX           44  // XIAO D7 (GPIO 44)
#define PIN_VISION_TX           43  // XIAO D6 (GPIO 43)
#define VISION_BAUDRATE         921600

// DFPlayer Mini UART & Control
#define PIN_DFPLAYER_TX         2   // XIAO D1 (GPIO 2) -> 1k Resistor -> DFPlayer RX
#define PIN_DFPLAYER_RX         3   // XIAO D2 (GPIO 3) <- DFPlayer TX
#define PIN_DFPLAYER_BUSY       -1  // Set -1 to use non-blocking software cooldowns
#define DFPLAYER_BAUDRATE       9600
#define DEFAULT_VOLUME          24  // Playback volume (0-30)

// Onboard User Indicator
#define PIN_STATUS_LED          21  // Active-LOW yellow LED
#define LED_STATE_ON            LOW
#define LED_STATE_OFF           HIGH

// Detection and Audio Throttle Settings
#define ACTIVE_CLASSES          8   // Current deployed 8-class model
#define CATALOG_RESERVE_CLASSES 50  // Reserved ID ceiling for future catalog expansion
#define MIN_CONFIDENCE_THRESHOLD 35  // Minimum detection score percentage

#define GLOBAL_ANNOUNCE_COOLDOWN 1200 // Minimum gap (ms) between any two speech alerts
#define HAZARD_CLASS_COOLDOWN    1500 // Cooldown (ms) for Priority 1 life hazards
#define DEFAULT_CLASS_COOLDOWN   3500 // Cooldown (ms) for Priority 2/3 obstacles

// Optional Reflex Layer (Disabled by default)
#define ENABLE_HAPTIC_SAFETY    false
#define PIN_ULTRASONIC_TRIG     7
#define PIN_ULTRASONIC_ECHO     8
#define PIN_VIBRATION_MOTOR     9
#define HAPTIC_TRIGGER_DIST_CM  80
#define HAPTIC_POLL_INTERVAL_MS 100

// Diagnostics Output
#define ENABLE_DEBUG            true
#define DEBUG_SERIAL            Serial

#if ENABLE_DEBUG
  #define DEBUG_PRINT(x)    DEBUG_SERIAL.print(x)
  #define DEBUG_PRINTLN(x)  DEBUG_SERIAL.println(x)
  #define DEBUG_PRINTF(...) DEBUG_SERIAL.printf(__VA_ARGS__)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
  #define DEBUG_PRINTF(...)
#endif

#endif // DRISHTI_CONFIG_H
