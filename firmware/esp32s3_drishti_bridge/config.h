#ifndef DRISHTI_CONFIG_H
#define DRISHTI_CONFIG_H

#include <Arduino.h>

// ==========================================
// 1. PIN DEFINITIONS FOR SEEED STUDIO XIAO ESP32-S3
// ==========================================
//
// The Seeed Studio XIAO ESP32S3 mounts DIRECTLY onto the Grove Vision AI V2 socket!
// When mounted on the socket:
// - Zero wires required between Grove Vision AI V2 and XIAO ESP32-S3!
// - I2C Bus: XIAO D4 (SDA / GPIO 5) & D5 (SCL / GPIO 6)
// - Socket UART Bus: XIAO D7 (RX / GPIO 44) & D6 (TX / GPIO 43)
//   (Direct hardware link through the socket to Himax WiseEye2 HX6538 UART!)
// - Power and ground pass through the socket automatically.
#define PIN_VISION_RX       44  // XIAO D7 (GPIO 44) <- Himax WiseEye2 TX
#define PIN_VISION_TX       43  // XIAO D6 (GPIO 43) -> Himax WiseEye2 RX
#define VISION_BAUDRATE     921600

// DFPlayer Mini connects to exposed XIAO header pins:
// - D1 (GPIO 2) -> 1K Resistor -> DFPlayer RX (Pin 2)
// - D2 (GPIO 3) <- DFPlayer TX (Pin 3)
// - BUSY pin check disabled (-1) so disconnected or floating pins never block audio alerts
#define PIN_DFPLAYER_TX     2   // XIAO D1 (GPIO 2) -> 1K Resistor -> DFPlayer RX
#define PIN_DFPLAYER_RX     3   // XIAO D2 (GPIO 3) <- DFPlayer TX
#define PIN_DFPLAYER_BUSY   -1  // -1 = Disabled (non-blocking, immune to clone chip quirks)
#define DFPLAYER_BAUDRATE   9600

// Status LED (XIAO ESP32S3 built-in user LED is GPIO 21)
// NOTE: XIAO ESP32-S3 onboard LED is active-LOW (LOW = ON, HIGH = OFF)
#define PIN_STATUS_LED      21  // XIAO Onboard Yellow LED
#define LED_STATE_ON        LOW
#define LED_STATE_OFF       HIGH

// ==========================================
// 3. ULTRASONIC & HAPTIC BYPASS SAFETY LAYER (OPTIONAL)
// ==========================================
// Non-blocking close-range reflex layer: buzzes handle vibration motor
// when an obstacle enters critical zone (<80cm), bypassing vision AI inference latency.
#define ENABLE_HAPTIC_SAFETY       false // Set true when HC-SR04 & motor are wired
#define PIN_ULTRASONIC_TRIG        7     // XIAO D8 (GPIO 7) -> HC-SR04 TRIG
#define PIN_ULTRASONIC_ECHO        8     // XIAO D9 (GPIO 8) <- HC-SR04 ECHO (via voltage divider!)
#define PIN_VIBRATION_MOTOR        9     // XIAO D10 (GPIO 9) -> NPN/MOSFET Gate for Vibration Motor
#define HAPTIC_TRIGGER_DIST_CM     80    // Vibration threshold distance in cm
#define HAPTIC_POLL_INTERVAL_MS    100   // Non-blocking distance check every 100ms

// ==========================================
// 2. DETECTION & FILTERING PARAMETERS
// ==========================================

// Minimum detection confidence to trigger voice (0-100%)
// Calibrated for the balanced 128x128 FOMO MobileNetV2 0.35 model (35% threshold captures doors and persons with 0% cross-class confusion)
#define MIN_CONFIDENCE_THRESHOLD  35

// Number of supported classes
#define TOTAL_CLASSES             50

// Minimum time (ms) between ANY consecutive voice announcements
// 2000ms ensures the current audio track finishes completely before another command is sent
#define GLOBAL_ANNOUNCE_COOLDOWN  2000

// Default cooldown (ms) for the same class
#define DEFAULT_CLASS_COOLDOWN    3500

// High hazard cooldown (ms) for critical safety items (Stairs down, potholes, red light)
#define HAZARD_CLASS_COOLDOWN     2000

// DFPlayer Default Volume (0 - 30)
#define DEFAULT_VOLUME            24

// Debug output to USB Serial
#define DEBUG_SERIAL              Serial
#define ENABLE_DEBUG              true

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
