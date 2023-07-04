/*Example sketch to control a stepper motor with A4988 stepper motor driver and Arduino without a library. More info: https://www.makerguides.com */
// Define stepper motor connections and steps per revolution:
#define TriggerPin 7
#define dirPin 5
#define stepPin 4
#define PosPin 3
#define PwrPin 2
#define Mspeed 400
#define MoveB 9000

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
    digitalWrite(dirPin, LOW);
    while (digitalRead(PosPin) == HIGH) {
      for (int i = 0; i < 50; i++) { 
      digitalWrite(stepPin, HIGH);
      delayMicroseconds(Mspeed);
      digitalWrite(stepPin, LOW);
      delayMicroseconds(Mspeed);
  }}
  delay(10);
  Serial.write("md");
  }
  else if (teststr == "b") {
    digitalWrite(dirPin, HIGH);
    for (int i = 0; i < MoveB; i++) {
      digitalWrite(stepPin, HIGH);
      delayMicroseconds(Mspeed);
      digitalWrite(stepPin, LOW);
      delayMicroseconds(Mspeed);
  }
  delay(10);
  Serial.write("bd");
  }

 delay(100);
  }
