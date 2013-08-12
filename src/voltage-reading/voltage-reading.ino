/**
 *
 */

#define VOLTAGE_PIN A0
#define LED_PIN     13

int curr_voltage = 0;

void setup() {
    Serial.begin(115200);
    pinMode(LED_PIN, OUTPUT);
}

void loop() {
    curr_voltage = analogRead(VOLTAGE_PIN);    
    Serial.println(curr_voltage);         
}
