//mueve el motor automaticamente no recive comandos 
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

short stepsPerRev= 6400; //200 * 8 = 3200
short laps = 0;

unsigned long lastSend = 0;
const unsigned long sendInterval = 5; // 0.1s

unsigned long startTimeMarca;


void setup() {
  Serial.begin(921600);
  engine.init();
  Wire.begin();                // SDA=21, SCL=22 por defecto en ESP32
  Wire.setClock(400000);       // I2C a 400 kHz para lecturas rápidas

  // Adjuntar el stepper
  stepper = engine.stepperConnectToPin(STEP_PIN);
  if (stepper) {
    stepper->setDirectionPin(DIR_PIN);
    stepper->setSpeedInHz(7680000);      // Velocidad inicial en pasos/segundo
    stepper->setAcceleration(3000000);   // Aceleración en pasos/seg²
  }
}

void loop() {
  static bool dir = true;
  if (millis() - lastSend >= sendInterval) {
    currentAngle = encoder.rawAngle() * AS5600_RAW_TO_DEGREES; // 0–4095 -> 0–360°
    if (lastAngle > 300 && currentAngle < 60) {
      laps++;
    } else if (lastAngle < 60 && currentAngle > 300) {
      laps--;
    } 
    absolutePosition = laps * 360L + currentAngle;
    //Serial.println(absolutePosition);
    Serial.println(currentAngle);
    lastAngle = currentAngle;
    lastSend = millis();
  }

  if (stepper && !stepper->isRunning()) {
    if (dir) {
      stepper->move(stepsPerRev);  // adelante
    } else {
      stepper->move(-stepsPerRev); // atrás
      laps++;
      stepper->setSpeedInHz(7680000 + (10000000L * laps));
      //Serial.println(7680000 + (10000000L * laps));
    }
    dir = !dir;
  }
}
