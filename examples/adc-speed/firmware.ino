#define NUM_SAMPLES 100000
#define FASTADC

#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))

void setup() {
  Serial.begin(115200);
  
  #ifdef FASTADC
  sbi(ADCSRA, ADPS2);
  cbi(ADCSRA, ADPS1);
  cbi(ADCSRA, ADPS0);
  #endif
}

void loop() {
  unsigned long t = micros();
  for (unsigned long int i = NUM_SAMPLES; i; i--) {
    analogRead(A0);
  }
  
  Serial.println((micros() - t) / NUM_SAMPLES);
  
}
