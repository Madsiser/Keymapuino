#include <Arduino.h>

const int maxPins = 20;

int digitalPins[maxPins];
int numDigitalPins = 0;

int analogPins[maxPins];
int numAnalogPins = 0;

String inputCommand = "";

void setup() {
  Serial.begin(9600);

  // Piny cyfrowe 2–12
  for (int pin = 2; pin <= 12; pin++) {
    pinMode(pin, INPUT_PULLUP);
  }

  // Piny analogowe A0–A5 (czyli 14–19)
  for (int i = 0; i <= 5; i++) {
    int pin = A0 + i;
    pinMode(pin, INPUT_PULLUP);
  }

  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
}

void loop() {
  handleSerialInput();

  // Cyfrowe wejścia (przyciski)
  for (int i = 0; i < numDigitalPins; i++) {
    int pin = digitalPins[i];
    pinMode(pin, INPUT_PULLUP);
    if (digitalRead(pin) == LOW) {
      sendPinCode(pin);
      delay(5); // debounce
    }
  }

  // Analogowe wejścia
  for (int i = 0; i < numAnalogPins; i++) {
    int pin = analogPins[i];
    int value = analogRead(pin);
    sendAnalogValue(pin, value);
  }

  delay(50);
}

// Odczytywanie komend z komputera
void handleSerialInput() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      processCommand(inputCommand);
      inputCommand = "";
    } else {
      inputCommand += c;
    }
  }
}

// Obsługa komend
void processCommand(String cmd) {
  cmd.trim();
  cmd.toLowerCase();

  if (cmd.startsWith("mode ")) {
    cmd = cmd.substring(5);
    int spaceIndex = cmd.indexOf(' ');
    if (spaceIndex == -1) return;

    String type = cmd.substring(0, spaceIndex);
    String pinStr = cmd.substring(spaceIndex + 1);
    int pin = parsePin(pinStr);

    if (pin == -1) return;

    if (type == "digital") {
      addToList(digitalPins, numDigitalPins, pin);
      sendOK();
    } else if (type == "analog") {
      addToList(analogPins, numAnalogPins, pin);
      sendOK();
    }
  } else if (cmd.startsWith("stop ")) {
    String pinStr = cmd.substring(5);
    int pin = parsePin(pinStr);
    if (pin == -1) return;

    removeFromList(digitalPins, numDigitalPins, pin);
    removeFromList(analogPins, numAnalogPins, pin);
    sendOK();
  } else if (cmd == "clear") {
    numDigitalPins = 0;
    numAnalogPins = 0;
    digitalWrite(13, LOW);
    sendOK();
  }
}

// Parsowanie "A0" → A0
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
    if (list[i] == value) return; // już jest
  }
  if (count < maxPins) {
    list[count++] = value;
    digitalWrite(13, HIGH);
  }
}

void removeFromList(int list[], int &count, int value) {
  for (int i = 0; i < count; i++) {
    if (list[i] == value) {
      for (int j = i; j < count - 1; j++) {
        list[j] = list[j + 1];
      }
      count--;
      if (count == 0) digitalWrite(13, LOW);
      return;
    }
  }
}

void sendOK(){
  Serial.println("OK");
}
