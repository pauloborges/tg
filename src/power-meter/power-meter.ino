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


/* Pinos onde a tensão e corrente serão amostradas */
#define VOLTAGE_PIN A0
#define CURRENT_PIN A1

unsigned short int NUM_SAMPLES;
float PHASE_CORRECTION;

float DIGITAL_TO_ANALOG, V_CALIB, I_CALIB;
float V_RMS_RATIO, I_RMS_RATIO, P_RMS_RATIO;

int raw_voltage, last_raw_voltage;
int raw_current, last_raw_current;

float fixed_voltage, last_fixed_voltage;

float voltage, last_voltage;
float current, last_current;

double sum_rms_voltage, rms_voltage;
double sum_rms_current, rms_current;

double sum_real_power, real_power;


/*****************************************************************************
 * ********************************* SERIAL **********************************
 *****************************************************************************/
void serialEventRun(void) {
    if (Serial.available()) {
        // TODO
    }
} 


/*****************************************************************************
 * ********************************** SETUP **********************************
 *****************************************************************************/
void setup() {
    Serial.begin(115200);
    analogReadResolution(12);
    // FIXME: deixar ADC mais rápido.

    /*
     * Etapa de calibragem.
     *
     * FIXME: fazer isso vir do HOST via Serial.
     * FIXME: documentar.
     */
    NUM_SAMPLES = 5000;
    PHASE_CORRECTION = 1.0;

    /*
     * Calcula o "quantum" do ADC. O ADC mapeia [0, 3.3] V num intervalo
     * [0, 4095]. Então cada passo desse intervalo equivale a
     * 3.3 V / 4095 ~ 0.806 mV.
     */
    DIGITAL_TO_ANALOG = 3.3 / 4095;

    // 110 Vrms / 1.45 V
    V_CALIB = 107.285;
    I_CALIB = 1.0;

    V_RMS_RATIO = (DIGITAL_TO_ANALOG * V_CALIB) / NUM_SAMPLES;
    I_RMS_RATIO = (DIGITAL_TO_ANALOG * I_CALIB) / NUM_SAMPLES;
    P_RMS_RATIO = (DIGITAL_TO_ANALOG * V_CALIB * I_CALIB) / NUM_SAMPLES;
}


/*****************************************************************************
 * ********************************** LOOP ***********************************
 *****************************************************************************/
void loop() {
    /*
     * Inicializa as variáveis para um novo ciclo.
     */
    raw_voltage = analogRead(VOLTAGE_PIN);
    // raw_current = analogRead(CURRENT_PIN);
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
        // last_raw_current = raw_current;

        raw_voltage = analogRead(VOLTAGE_PIN);
        // raw_current = analogRead(CURRENT_PIN);

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
        ///// APAGAR
        fixed_voltage = raw_voltage;

        /*
         * Remove o offset de ambas as amostras através de um HPF.
         */
        last_voltage = voltage;
        voltage = 0.996 * (last_voltage + fixed_voltage - last_fixed_voltage);
        // last_current = current;
        // current = 0.996 * (last_current + raw_current - last_raw_current);

        /*
         * Adiciona o quadrado da tensão e o quadrado da corrente nos
         * respectivos acumuladores para, posteriormente, calcular os valores
         * RMS.
         */
        sum_rms_voltage += voltage * voltage;
        // sum_rms_current += current * current;

        /*
         * Adiciona o produto da tensão pela corrente no acumulador de potência
         * real para, posteriormente, calcular a potência real.
         */
        // sum_real_power += voltage * current;
    }

    /*
     * Calcula a tensão e corrente RMS, fazendo a conversão
     */
    rms_voltage = sqrt(V_RMS_RATIO * sum_rms_voltage);
    // rms_current = sqrt(I_RMS_RATIO * sum_rms_current);

    /*
     * Calcula a potência real.
     */
    // real_power = P_RMS_RATIO * sum_real_power;

    /*
     * Transmite as informações via Serial através de um protocolo *textual*.
     *
     * O pacote do protocolo é:
     *
     * [TENSÃO_RMS]#[CORRENTE_RMS]#[POTÊNCIA_REAL]\n
     */
    Serial.print(rms_voltage);
    Serial.print('#');
    Serial.print(rms_current);
    Serial.print('#');
    Serial.println(real_power);
}
