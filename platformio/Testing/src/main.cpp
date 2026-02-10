#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  delay(1000);

  if (psramFound()) {
    Serial.println("✅ PSRAM FOUND");
    Serial.printf("PSRAM size: %d bytes\n", ESP.getPsramSize());
  } else {
    Serial.println("❌ PSRAM NOT FOUND");
  }
}

void loop() {}
