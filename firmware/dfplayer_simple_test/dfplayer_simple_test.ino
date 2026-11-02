/*
 * =========================================================
 * DRISHTI: DFPlayer Mini Direct Diagnostic Test
 * Board: Seeed Studio XIAO ESP32-S3
 * =========================================================
 *
 * This standalone test verifies the hardware connection between
 * the XIAO ESP32-S3 and the DFPlayer Mini module.
 *
 * WIRING:
 *   XIAO 5V   --> DFPlayer Pin 1 (VCC)
 *   XIAO GND  --> DFPlayer Pin 7 or 10 (GND)
 *   XIAO D1   --> DFPlayer Pin 2 (RX)  <-- Direct wire (no resistor needed for 3.3V ESP32)
 *   XIAO D2   --> DFPlayer Pin 3 (TX)
 *   Earphones --> DFPlayer Pin 4 (DAC_R) & Pin 5 (DAC_L), GND to Pin 7/10
 *
 * WHAT TO EXPECT:
 *   - Every 4 seconds, the XIAO onboard LED will blink.
 *   - The DFPlayer's red LED should turn ON for 1-2 seconds.
 *   - Audio will play through the earphones.
 * =========================================================
 */

#include <Arduino.h>

// UART2 instance on ESP32-S3: RX = GPIO 3 (D2), TX = GPIO 2 (D1)
HardwareSerial DFSerial(2);

void sendDFCommand(uint8_t cmd, uint8_t feedback, uint16_t param) {
  uint8_t paramH = (uint8_t)(param >> 8);
  uint8_t paramL = (uint8_t)(param & 0xFF);
  uint16_t sum = 0xFF + 0x06 + cmd + feedback + paramH + paramL;
  uint16_t checksum = (uint16_t)(0 - sum);

  uint8_t packet[10] = {
    0x7E,                        // Start byte
    0xFF,                        // Version
    0x06,                        // Data length
    cmd,                         // Command
    feedback,                    // Feedback (0 = No)
    paramH,                      // Parameter High
    paramL,                      // Parameter Low
    (uint8_t)(checksum >> 8),    // Checksum High
    (uint8_t)(checksum & 0xFF),  // Checksum Low
    0xEF                         // End byte
  };

  DFSerial.write(packet, 10);
  DFSerial.flush();
  delay(40);
}

void setup() {
  Serial.begin(115200);
  pinMode(21, OUTPUT); // XIAO Onboard Yellow LED (Active LOW)
  digitalWrite(21, HIGH);

  delay(2000);
  Serial.println("\n========================================");
  Serial.println("  DFPLAYER MINI DIRECT HARDWARE TEST    ");
  Serial.println("========================================");

  // Start UART2 at 9600 baud: RX on GPIO 3 (D2), TX on GPIO 2 (D1)
  DFSerial.begin(9600, SERIAL_8N1, 3, 2);
  delay(1500);

  // Set Volume to 28 / 30
  Serial.println("[Init] Setting volume to 28/30...");
  sendDFCommand(0x06, 0x00, 28);
  delay(200);
  Serial.println("[Ready] Starting continuous playback loop...");
}

void loop() {
  // Flash onboard LED to show command transmission
  digitalWrite(21, LOW);
  delay(100);
  digitalWrite(21, HIGH);

  Serial.println("\n>>> [Sending Command] Playing Track 13 (Person)...");
  
  // 1. Try Command 0x12 (Folder /MP3/)
  sendDFCommand(0x12, 0x00, 13);
  delay(100);

  // 2. Try Command 0x03 (Universal direct track index for clone chips)
  sendDFCommand(0x03, 0x00, 13);

  Serial.println(">>> Commands sent! Watch DFPlayer red LED.");

  // Wait 4 seconds before next attempt
  delay(4000);
}
