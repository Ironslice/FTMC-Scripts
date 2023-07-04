/*Example sketch to control a stepper motor with A4988 stepper motor driver and Arduino without a library. More info: https://www.makerguides.com */
#include <AccelStepper.h>
// Define stepper motor connections and steps per revolution:
#define TriggerPin 7
#define dirPin 5
#define stepPin 4
#define PosPin 3
#define PwrPin 2
#define motorInterfaceType 1
AccelStepper myStepper(motorInterfaceType, stepPin, dirPin);
long homing= -500;
void setup() {

  // Declare pins as output:
  Serial.begin(9600);
  Serial.setTimeout(500);
  pinMode(TriggerPin, OUTPUT);
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  pinMode(PwrPin, OUTPUT);
  pinMode(PosPin, INPUT);
  digitalWrite(PwrPin, HIGH);

  
  
   myStepper.setMaxSpeed(1000);
  myStepper.setAcceleration(1000);
}

void loop() {
  while (Serial.available() == 0) {}
  String teststr = Serial.readString();  //read until timeout
  teststr.trim();                        // remove any \r \n whitespace at the end of the String

  if (teststr == "t") {
    digitalWrite(TriggerPin, HIGH);
    delay(10);
    Serial.write("td");
    

  }
  else if (teststr == "o") {
    digitalWrite(TriggerPin, LOW);
    delay(10);
    Serial.write("od");
  }
  else if (teststr == "m") {
  while (digitalRead(PosPin)) {
  myStepper.moveTo(homing);
  homing = homing - 500;
  myStepper.runToPosition();
  delay(5);
  }
  myStepper.setCurrentPosition(0);
 // myStepper.stop();
  delay(10);
  Serial.write("md");
  }
  
  else if (teststr == "b") {
        myStepper.moveTo(5000);
        myStepper.runToPosition();
  
  delay(10);
  Serial.write("bd");
  }
 delay(100);
  }
