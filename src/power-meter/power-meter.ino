/**
 * Copyright (c) 2013 Paulo Sérgio Borges de Oliveira Filho
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 * the Software, and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
 * FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
 * COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
 * IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

/**
 * Esse sketch calcula o consumo energético e envia as informações
 * via Serial.
 *
 * As informações computadas são:
 * - Tensão RMS
 * - Corrente RMS
 * - Potência Real
 * - Potência Aparente
 *
 * A potência reativa, aparente e fator de potência podem ser derivados das
 * informações listadas acima e, portanto, não são calculados aqui.
 */

/*****************************************************************************
 ********************************** PLATFORM *********************************
 *****************************************************************************/
#define ARDUINO_PLATFORM AVR

#if ARDUINO_PLATFORM == AVR
#define ADC_MAX_VALUE 1023
#else
#define ADC_MAX_VALUE 4095
#endif


/*****************************************************************************
 ************************************ ADC ************************************
 *****************************************************************************/
#define VOLTAGE_PIN A0
#define CURRENT_PIN A1

#define VOLTAGE_SAMPLING 0
#define CURRENT_SAMPLING 0

#define PI              3.14159265359
#define FREQ_60HZ       2 * PI * 60
#define PHASE_ZERO      0
#define OFFSET_HALF_ADC (ADC_MAX_VALUE / 2)

#if VOLTAGE_SAMPLING == 1
#define READ_VOLTAGE(elapsed) analogRead(VOLTAGE_PIN)
#else
#define V_AMPLI (ADC_MAX_VALUE / 2)
#define READ_VOLTAGE(elapsed) \
    fakeAnalogRead(FREQ_60HZ, PHASE_ZERO, V_AMPLI, OFFSET_HALF_ADC, elapsed)
#endif

#if CURRENT_SAMPLING == 1
#define READ_CURRENT(elapsed) analogRead(CURRENT_PIN)
#else
#define I_AMPLI (ADC_MAX_VALUE / 10)
#define I_PHASE 5.0
#define READ_CURRENT(elapsed) \
    fakeAnalogRead(FREQ_60HZ, I_PHASE, I_AMPLI, OFFSET_HALF_ADC, elapsed)
#endif

#define NUM_SAMPLES 1000
#define PHASE_CORRECTION 1.0

#define V_CALIB 1.0 //107.285     /* 110 VRMS / 1.45 V */
#define I_CALIB 1.0

/*
 * Calcula o "quantum" do ADC. O ADC mapeia [0, 3.3] V num intervalo
 * [0, 1023|4095] (depende do uC). Então cada passo desse intervalo equivale
 * a 3.3 V / ADC_MAX_VALUE.
 */
#define DIGITAL_TO_ANALOG 3.3 / ADC_MAX_VALUE

float V_RATIO = (DIGITAL_TO_ANALOG * V_CALIB) / NUM_SAMPLES;
float I_RATIO = (DIGITAL_TO_ANALOG * I_CALIB) / NUM_SAMPLES;
float P_RATIO = (DIGITAL_TO_ANALOG * V_CALIB * I_CALIB) / NUM_SAMPLES;


/*****************************************************************************
 ********************************* VARIABLES *********************************
 *****************************************************************************/
int raw_voltage, last_raw_voltage;
int raw_current, last_raw_current;

float fixed_voltage, last_fixed_voltage;

float voltage, last_voltage;
float current, last_current;

double sum_rms_voltage, rms_voltage;
double sum_rms_current, rms_current;

double sum_real_power, real_power;

#define MICRO_TO_SECOND 1000000.0
#define REFRESH_ELAPSED_TIME()                                              \
    do {                                                                    \
        float old = seconds_counter;                                        \
        seconds_counter = (((double) micros()) / MICRO_TO_SECOND);          \
        if (seconds_counter < 0.0)                                          \
            ; /*FIXME*/                                                     \
    } while(0)

double seconds_counter = 0.0;


/*****************************************************************************
 *********************************** SERIAL **********************************
 *****************************************************************************/
void serialEventRun(void) {
    if (Serial.available()) {
        // TODO
    }
} 


/*****************************************************************************
 ****************************** FAKE ANALOG READ *****************************
 *****************************************************************************/
int fakeAnalogRead(double freq, double phase, double ampl, double offset,
                                                            double elapsed) {
    return (int) (ampl * sin(freq * elapsed) + offset);
}

/*****************************************************************************
 ************************************ SETUP **********************************
 *****************************************************************************/
void setup() {
    #if ARDUINO_PLATFORM == DUE
    analogReadResolution(12);
    #endif

    Serial.begin(115200);
    // FIXME: deixar ADC mais rápido.
}


/*****************************************************************************
 ************************************ LOOP ***********************************
 *****************************************************************************/
void loop() {
    /*
     * Inicializa as variáveis para um novo ciclo.
     */

    REFRESH_ELAPSED_TIME();
    raw_voltage = READ_VOLTAGE(0);
    raw_current = READ_CURRENT(0);

    voltage = fixed_voltage = 0.0;
    current = 0.0;

    sum_rms_voltage = 0.0;
    sum_rms_current = 0.0;
    sum_real_power = 0.0;

    rms_voltage = 0.0;
    rms_current = 0.0;
    real_power = 0.0;

    for (unsigned short int i = NUM_SAMPLES; i > 0; i--) {
        /*
         * Faz a amostra da tensão e corrente.
         *
         * Esse sinal é um inteiro pertencente ao intervalo [0, 4048].
         */
        last_raw_voltage = raw_voltage;
        last_raw_current = raw_current;

        REFRESH_ELAPSED_TIME();
        raw_voltage = READ_VOLTAGE(seconds_counter);
        raw_current = READ_CURRENT(seconds_counter);

        /*
         * Corrige a fase do sinal da tensão.
         *
         * Como as amostras são retiradas em série, existe uma diferença de
         * fase entre ambas.
         *
         * Esse cálculo faz uma correção (que não é perfeita), através da
         * predição do valor da tensão no momento em que a corrente foi
         * amostrada (um ponto futuro em relação à amostra de tensão).
         *
         * Essa previsão extrapola a diferença entre a tensão atual e a última
         * tensão amostrada por um fator de correção.
         */
        last_fixed_voltage = fixed_voltage;
        fixed_voltage = last_raw_voltage + PHASE_CORRECTION
                        * (raw_voltage - last_raw_voltage);

        /*
         * Remove o offset de ambas as amostras através de um HPF.
         */
        last_voltage = voltage;
        voltage = 0.996 * (last_voltage + fixed_voltage - last_fixed_voltage);
        last_current = current;
        current = 0.996 * (last_current + raw_current - last_raw_current);

        Serial.print(voltage);
        Serial.print('#');
        Serial.println(current);

        /*
         * Adiciona o quadrado da tensão e o quadrado da corrente nos
         * respectivos acumuladores para, posteriormente, calcular os valores
         * RMS.
         */
        sum_rms_voltage += voltage * voltage;
        sum_rms_current += current * current;

        /*
         * Adiciona o produto da tensão pela corrente no acumulador de potência
         * real para, posteriormente, calcular a potência real.
         */
        sum_real_power += voltage * current;
    }

    /*
     * Calcula a tensão e corrente RMS, fazendo a conversão
     */
    rms_voltage = sqrt(V_RATIO * sum_rms_voltage);
    rms_current = sqrt(I_RATIO * sum_rms_current);

    /*
     * Calcula a potência real.
     */
    real_power = P_RATIO * sum_real_power;

    /*
     * Transmite as informações via Serial através de um protocolo *textual*.
     *
     * O pacote do protocolo é:
     *
     * [TENSÃO_RMS]#[CORRENTE_RMS]#[POTÊNCIA_REAL]\n
     */
    // Serial.print(rms_voltage);
    // Serial.print('#');
    // Serial.print(rms_current);
    // Serial.print('#');
    // Serial.println(real_power);
}
