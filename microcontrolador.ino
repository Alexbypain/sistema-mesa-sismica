#include <Wire.h>
#include <AS5600.h>
#include "FastAccelStepper.h"

#define DIR_PIN   25
#define STEP_PIN  26

FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;

AS5600 encoder;
float currentAngle = 0;
float lastAngle = 0;
float absolutePosition = 0;
int laps=0;

unsigned long lastSend = 0;
const unsigned long sendInterval = 100; // 0.1s

void setup() {
  Serial.begin(115200);
  Wire.begin();
  engine.init();
  stepper = engine.stepperConnectToPin(STEP_PIN);
  if (stepper) {
    stepper->setDirectionPin(DIR_PIN);
    stepper->setSpeedInHz(1000);      // Velocidad máxima (Hz = pasos/seg)
    stepper->setAcceleration(500);    // Aceleración en pasos/s^2
  }
}

void loop() {
  if (millis() - lastSend >= sendInterval) {
    currentAngle = encoder.rawAngle() * AS5600_RAW_TO_DEGREES; // 0–4095 -> 0–360°
    if (lastAngle > 300 && currentAngle < 60) {
      laps++;
    } else if (lastAngle < 60 && currentAngle > 300) {
      laps--;
    } 
    absolutePosition = laps * 360L + currentAngle;
    Serial.println(absolutePosition);
    lastAngle = currentAngle;
    lastSend = millis();
  }

  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    long steps = cmd.toInt();
    if (stepper) {
      stepper->move(steps);
    }
  }
}
