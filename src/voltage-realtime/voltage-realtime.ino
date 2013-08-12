/**
 *
 */

#define VOLTAGE_PIN A0

int curr_voltage = 0;

void setup() {
    Serial.begin(115200);
}

void loop() {
    curr_voltage = analogRead(VOLTAGE_PIN);
    Serial.println(curr_voltage);
}
