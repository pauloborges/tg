/**
 *  Esse sketch lê a tensão e corrente dos pinos A0 e A1 e as envia via
 *  serial.
 */

#define VOLTAGE_PIN A0
#define CURRENT_PIN A1

#define PHASE_STEP 0.05
float PHASE_CORRECTION = 1.0;
int NUM_SAMPLES = 100;

int raw_voltage, last_raw_voltage;
int raw_current, last_raw_current;

float fixed_voltage, last_fixed_voltage;

float voltage, last_voltage;
float current, last_current;

int i;

void serialEventRun(void) {
    if (Serial.available()) serialEvent();
} 

void serialEvent() {
    int available = Serial.available();
    if (available < 2)
        return;

    char c = Serial.read();
    if (c == 'P') {
        c = Serial.read();

        if (available > 2 && Serial.peek() == '\n')
            Serial.read();

        if (c == '+')
            PHASE_CORRECTION += PHASE_STEP;
        else if (c == '-')
            PHASE_CORRECTION -= PHASE_STEP;

        Serial.print('P');
        Serial.println(PHASE_CORRECTION);
    }
}

void setup() {
    Serial.begin(115200);
    analogReadResolution(12);

    raw_voltage = analogRead(VOLTAGE_PIN);
    raw_current = analogRead(CURRENT_PIN);

    voltage = fixed_voltage = 0.0;
    current = 0.0;
}

void loop() {
    for (int i = NUM_SAMPLES; i > 0; i--) {
        /*
         * Faz a amostra da tensão e corrente.
         *
         * Esse sinal é um inteiro pertencente ao intervalo [0, 4048].
         */
        last_raw_voltage = raw_voltage;
        last_raw_current = raw_current;

        raw_voltage = analogRead(VOLTAGE_PIN);
        raw_current = analogRead(CURRENT_PIN);

        /*
         * Corrige a fase do sinal da tensão.
         *
         * Como as amostras são retiradas em série, existe uma diferença de fase
         * entre ambas.
         *
         * Esse cálculo faz uma correção (que não é perfeita), através da predição
         * do valor da tensão no momento em que a corrente foi amostrada
         * (a corrente foi amostrada momentos depois da tensão).
         *
         * Essa previsão extrapola a diferença entre a tensão atual e a última
         * tensão amostrada por um fator de correção.
         *
         * Segue um exemplo: os pontos denominados 'v' são amostras de tensão e os
         * pontos denominados 'c' são amostras de corrente.
         *
         * |
         * |        v          -
         * |      v c  -       | PHASE_CORRECTION * diff
         * |   c       | diff  |
         * | v         -       -
         * |______________________
         *   ^    ^ ^
         *   0    1 2
         *
         * A amostra de corrente no momento 2 foi convertida depois da amostra de
         * tensão do momento 1. Utilizá-las como se tivessem sido obtidas no mesmo
         * instante irá causar erros. Então a diferença entre as duas últimas
         * amostras de tensão é calculada e extrapolada por um fator de correção
         * de fase para encontrar um valor de tensão que foi "convertido"
         * simultaneamente com a amostra de corrente.
         */
        last_fixed_voltage = fixed_voltage;
        fixed_voltage = last_raw_voltage + PHASE_CORRECTION
                        * (raw_voltage - last_raw_voltage);

        /*
         * Remove o offset de ambos os sinais através de um HPF.
         * ...
         */
        last_voltage = voltage;
        voltage = 0.996 * (last_voltage + fixed_voltage - last_fixed_voltage);
        last_current = current;
        current = 0.996 * (last_current + raw_current - last_raw_current);

        /*
         * Transmite as informações para serial.
         */
        Serial.print(voltage);
        Serial.print('#');
        Serial.println(current);
    }
}
