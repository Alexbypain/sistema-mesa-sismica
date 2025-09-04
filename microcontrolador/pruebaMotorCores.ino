//esta version aprovecha el otro core del esp32 para la lectura del encoder
#include "FastAccelStepper.h"
#include <AS5600.h>

#define STEP_PIN 26
#define DIR_PIN 25

FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;

AS5600 encoder;
float currentAngle = 0;
float lastAngle = 0;
float absolutePosition = 0;

short stepsPerRev= 6400;
short laps = 0;

TaskHandle_t encoderTaskHandle;

void setup() {
  Serial.begin(115200);
  engine.init();
  Wire.begin();
  Wire.setClock(400000);

  // Crear la tarea para el encoder en core 0
  xTaskCreatePinnedToCore(readEncoderTask,"EncoderTask",4096,NULL,1,&encoderTaskHandle,0);

  stepper = engine.stepperConnectToPin(STEP_PIN);
  if (stepper) {
    stepper->setDirectionPin(DIR_PIN);
    stepper->setSpeedInHz(7680000);
    stepper->setAcceleration(3000000);
  }
}

void loop() {
  static bool dir = true;

  if (stepper && !stepper->isRunning()) {
    if (dir) {
      stepper->move(stepsPerRev);
    } else {
      stepper->move(-stepsPerRev);
      laps++;
      stepper->setSpeedInHz(7680000 + (10000000L * laps));
    }
    dir = !dir;
  }
}

void readEncoderTask(void *parameter) {
  for (;;) {
    float angle = encoder.rawAngle() * AS5600_RAW_TO_DEGREES; // 0–4095 → 0–360°
    if (lastAngle > 300 && angle < 60) {
      laps++;
    } else if (lastAngle < 60 && angle > 300) {
      laps--;
    }
    absolutePosition = laps * 360L + angle;

    // Puedes mandar la posición absoluta en lugar de solo el ángulo
    Serial.println(angle);

    lastAngle = angle;
    vTaskDelay(pdMS_TO_TICKS(5));  // cada 5 ms
  }
}
