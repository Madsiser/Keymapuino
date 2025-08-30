#include <Arduino.h>
#include <Servo.h>

#define PWM_MAX_VALUE 255
#define SERVO_MAX_ANGLE 180

#define PIN_MODE_UNCONFIGURED 0
#define PIN_MODE_OUTPUT 1
#define PIN_MODE_INPUT 2
#define PIN_MODE_PULLUP 3
#define PIN_MODE_SERVO 4

const int NUM_PINS = 20;
int pinModes[NUM_PINS];

const int MAX_AMOUNT_SERVOS = 8;
Servo servoObjects[MAX_AMOUNT_SERVOS];
int servoPins[MAX_AMOUNT_SERVOS];
int numServos = 0;

const int MAX_PINS_MONITORED = 20;
int digitalReadPins[MAX_PINS_MONITORED];
int numDigitalReadPins = 0;
int analogReadPins[MAX_PINS_MONITORED];
int numAnalogReadPins = 0;

void setup() {
  Serial.begin(9600);
  clearAll();
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }

  for (int i = 0; i < numDigitalReadPins; i++) {
    int pin = digitalReadPins[i];
    if (digitalRead(pin) == LOW) {
      sendPinCode(pin);
      delay(5);
    }
  }

  for (int i = 0; i < numAnalogReadPins; i++) {
    int pin = analogReadPins[i];
    int value = analogRead(pin);
    sendAnalogValue(pin, value);
  }

  delay(20);
}

void processCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  char type = cmd.charAt(0);
  if (type == 'D' || type == 'P' || type == 'S') {
    int firstComma = cmd.indexOf(',');
    int secondComma = cmd.indexOf(',', firstComma + 1);

    if (firstComma == -1 || secondComma == -1) { sendError("Malformed command"); return; }

    int pin = cmd.substring(firstComma + 1, secondComma).toInt();
    int value = cmd.substring(secondComma + 1).toInt();

    if (pin < 0 || pin >= NUM_PINS) { sendError("Invalid pin"); return; }

    if (type == 'D') {
      if (pinModes[pin] != PIN_MODE_OUTPUT) { sendError("Pin not configured as OUTPUT"); return; }
      digitalWrite(pin, value == 1 ? HIGH : LOW);
    } else if (type == 'P') {
      if (pinModes[pin] != PIN_MODE_OUTPUT) { sendError("Pin not configured as OUTPUT"); return; }
      analogWrite(pin, constrain(value, 0, PWM_MAX_VALUE));
    } else if (type == 'S') {
      if (pinModes[pin] != PIN_MODE_SERVO) { sendError("Pin not configured as SERVO"); return; }
      for (int i = 0; i < numServos; i++) {
        if (servoPins[i] == pin) {
          servoObjects[i].write(constrain(value, 0, SERVO_MAX_ANGLE));
          break;
        }
      }
    }
    return;
  }

  cmd.toLowerCase();
  
  if (cmd.startsWith("pin ")) {
    String params = cmd.substring(4);
    int spaceIndex = params.indexOf(' ');
    if (spaceIndex == -1) { sendError("Malformed pin command"); return; }

    int pin = parsePin(params.substring(0, spaceIndex));
    String action = params.substring(spaceIndex + 1);

    if (pin < 0 || pin >= NUM_PINS) { sendError("Invalid pin number"); return; }

    if (action.startsWith("mode ")) {
      String modeStr = action.substring(5);
      if (modeStr == "output") {
        pinMode(pin, OUTPUT);
        pinModes[pin] = PIN_MODE_OUTPUT;
        sendOK();
      } else if (modeStr == "input") {
        pinMode(pin, INPUT);
        pinModes[pin] = PIN_MODE_INPUT;
        sendOK();
      } else if (modeStr == "pullup") {
        pinMode(pin, INPUT_PULLUP);
        pinModes[pin] = PIN_MODE_PULLUP;
        sendOK();
      } else if (modeStr == "servo") {
        if (pinModes[pin] != PIN_MODE_UNCONFIGURED) { sendError("Pin already in use"); return; }
        if (numServos >= MAX_AMOUNT_SERVOS) { sendError("Max servos reached"); return; }
        servoPins[numServos] = pin;
        servoObjects[numServos].attach(pin);
        pinModes[pin] = PIN_MODE_SERVO;
        numServos++;
        sendOK();
      } else if (modeStr == "unconfigured") {
        if (pinModes[pin] == PIN_MODE_SERVO) {
          for (int i = 0; i < numServos; i++) {
            if (servoPins[i] == pin) {
              servoObjects[i].detach();
              for (int j = i; j < numServos - 1; j++) {
                servoObjects[j] = servoObjects[j + 1];
                servoPins[j] = servoPins[j + 1];
              }
              numServos--;
              break;
            }
          }
        }
        pinModes[pin] = PIN_MODE_UNCONFIGURED;
        sendOK();
      } else {
        sendError("Invalid pin mode");
      }
    } else if (action.startsWith("read ")) {
      if (pinModes[pin] != PIN_MODE_INPUT && pinModes[pin] != PIN_MODE_PULLUP) {
        sendError("Pin not configured for input");
        return;
      }
      String readType = action.substring(5);
      if (readType == "digital") {
        addToList(digitalReadPins, numDigitalReadPins, pin);
      } else if (readType == "analog") {
        addToList(analogReadPins, numAnalogReadPins, pin);
      } else if (readType == "stop") {
        removeFromList(digitalReadPins, numDigitalReadPins, pin);
        removeFromList(analogReadPins, numAnalogReadPins, pin);
      }
      sendOK();
    }
  } else if (cmd == "clear") {
    clearAll();
    sendOK();
  }
}

void clearAll() {
  for (int i = 0; i < numServos; i++) {
    servoObjects[i].detach();
  }
  numServos = 0;
  
  numDigitalReadPins = 0;
  numAnalogReadPins = 0;

  for (int i = 0; i < NUM_PINS; i++) {
    pinModes[i] = PIN_MODE_UNCONFIGURED;
  }
  
  pinMode(LED_BUILTIN, OUTPUT);
  pinModes[LED_BUILTIN] = PIN_MODE_OUTPUT;
  digitalWrite(LED_BUILTIN, LOW);
}

int parsePin(String pinStr) {
    pinStr.trim();
    pinStr.toUpperCase();
    if (pinStr.startsWith("A")) {
        int n = pinStr.substring(1).toInt();
        if (n >= 0 && n <= 5) return A0 + n;
    } else {
        return pinStr.toInt();
    }
    return -1;
}

void sendPinCode(int pin) {
    if (pin >= A0 && pin <= A5) {
        Serial.print("A");
        Serial.println(pin - A0);
    } else {
        Serial.println(pin);
    }
}

void sendAnalogValue(int pin, int value) {
    if (pin >= A0 && pin <= A5) {
        Serial.print("A");
        Serial.print(pin - A0);
        Serial.print(":");
        Serial.println(value);
    }
}

void addToList(int list[], int &count, int value) {
    for (int i = 0; i < count; i++) {
        if (list[i] == value) return;
    }
    if (count < MAX_PINS_MONITORED) {
        list[count++] = value;
        digitalWrite(LED_BUILTIN, HIGH);
    }
}

void removeFromList(int list[], int &count, int value) {
    for (int i = 0; i < count; i++) {
        if (list[i] == value) {
            for (int j = i; j < count - 1; j++) {
                list[j] = list[j + 1];
            }
            count--;
            if (numDigitalReadPins == 0 && numAnalogReadPins == 0 && numServos == 0) {
                digitalWrite(LED_BUILTIN, LOW);
            }
            return;
        }
    }
}

void sendOK(){ Serial.println("OK"); }
void sendError(String err){ Serial.print("ERROR: "); Serial.println(err); }