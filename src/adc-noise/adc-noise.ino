/*
	Esse firmware envia para o host leituras periódicas do
	ADC para verificar o ruído inserido no processo de
	conversão.

	Deve-se colocar um divisor de tensão R/R entre o pino de 5 V
	e o GND. O ponto do meio deve ir no pino A0.
*/

#define ADC_PIN A0

int curr_voltage = 0;

void setup() {
    Serial.begin(115200);
}

void loop() {
    curr_voltage = analogRead(ADC_PIN);    
    Serial.println(curr_voltage);         
}
