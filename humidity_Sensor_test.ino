#include <dht.h>

#define DHT_PIN 2     // use a regular digital pin
dht DHT;

void setup() {
  Serial.begin(9600);
  delay(2000);                // let the sensor power up
  Serial.println("DHT11 only");
}

void loop() {
  int chk = DHT.read11(DHT_PIN);     // <-- DHT11 ONLY

  Serial.print("Status: ");
  switch (chk) {
    case 0:  Serial.print("OK"); break;
    case -1: Serial.print("Checksum error"); break;
    case -2: Serial.print("Timeout error"); break;
    default: Serial.print("Unknown"); break;
  }

  Serial.print("  |  RH=");
  Serial.print(DHT.humidity, 1);
  Serial.print("%  T=");
  Serial.print(DHT.temperature, 1);
  Serial.println(" C");

  delay(2500);   // >= 2s between reads
}
