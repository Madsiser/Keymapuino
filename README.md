# Keymapuino

**Keymapuino** is an open-source project that combines Arduino firmware, a command-line interface, and a graphical user interface to make working with keyboard keymaps simple and accessible. It enables you to flash, configure, and manage keymaps on supported Arduino boards with ease.

---

## ✨ Features

- 🛠 **Arduino Firmware** – Runs on Arduino Uno and compatible boards.  
- 💻 **Command-Line Interface (CLI)** – Lightweight control from the terminal.  
- 🎨 **Graphical User Interface (GUI)** – User-friendly desktop tool for managing keymaps.  
- 🔄 **Cross-Platform Build Scripts** – Supports Windows (`build.bat`) and Linux/macOS (`build.sh`).  
- ⚡ **Automated Releases** – GitHub Actions workflow included.  

---

## 📂 Project Structure

```
Keymapuino/
├── keymapuino-arduino/   # Arduino firmware (arduino-uno.ino)
├── keymapuino-cli/       # CLI tool (Python)
├── keymapuino-gui/       # GUI tool (Python)
├── build.bat             # Windows build script
├── build.sh              # Linux/macOS build script
├── LICENSE
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Keymapuino.git
cd Keymapuino
```

### 2. Arduino Firmware
- Open **`keymapuino-arduino/arduino-uno.ino`** in the [Arduino IDE](https://www.arduino.cc/en/software).  
- Select your board and port.  
- Upload the sketch to your Arduino.  

### 3. CLI Tool
The CLI is written in Python. To install dependencies:
```bash
cd keymapuino-cli
pip install -r requirements.txt   # (create this file if needed)
python keymapuino-cli.py --help
```

### 4. GUI Tool
The GUI is also Python-based:
```bash
cd keymapuino-gui
pip install -r requirements.txt   # (create this file if needed)
python keymapuino-gui.py
```
---

## 📖 Usage – Keymapuino CLI

The CLI communicates with the Arduino over serial and maps input pins to keyboard events on your computer.
Configuration is defined in a JSON file (`config.json`).

### Example `config.json`

```json
{
  "port": "COM3",
  "key_mapping": {
    "2": { "key": "a" },
    "3": { "key": "b" },
    "A0": [
      { "key": "x", "threshold": [0, 500] },
      { "key": "y", "threshold": [501, 1023], "hold_time_ms": 300 }
    ]
  }
}
```

* `port` – serial port of the Arduino (e.g. `COM3` on Windows or `/dev/ttyUSB0` on Linux).
* `key_mapping` – mapping of Arduino pins to keyboard keys.

  * **Digital pin** (single key): `{ "key": "a" }`
  * **Analog pin** (ranges): list of objects with `"key"`, `"threshold"`, and optional `"hold_time_ms"`.

---

### Run CLI

```bash
python keymapuino-cli.py --config config.json --log 2 --port COM3
```

#### Arguments:

* `--config` → Path to JSON config file (default: `config.json`)
* `--log` → Logging verbosity (1 = minimal, 4 = debug)
* `--port` → Override serial port (optional, otherwise read from config)

---

### Example session

```bash
$ python keymapuino-cli.py --config config.json --log 2
Sending configuration to Arduino...
Configuration sent.
RUN
Pressed key: a
Released key: a
Pressed key: y
Released key: y
```

---

## 🖥 Usage – Keymapuino GUI

The GUI provides a graphical interface to configure key mappings and manage the CLI process easily.

### Launch GUI

```bash
python keymapuino-gui.py
```

### Features

* **Port selection** – Choose from detected serial ports, or refresh the list.
* **Pin mapping** – Add/remove digital or analog pin mappings via dialogs.
* **Save/Load configs** – Save your mappings to a `.conf` file or load an existing one.
* **Start/Stop program** – Launches the CLI backend automatically with your config.
* **Log viewer** – See live logs of the CLI inside the GUI.

### Example workflow

1. Open GUI with `python keymapuino-gui.py`.
2. Select Arduino port from dropdown.
3. Add pins (digital or analog) and assign keys.
4. Save config to file.
5. Click **Start Program** – the CLI runs in background.
6. Observe **Program Status** indicator (green = running).
7. Open **View Logs** to debug.
8. Stop with **Stop Program** button or close the GUI.

---

---

## 🏗 Build Scripts
- On Windows:
  ```bash
  build.bat
  ```
- On Linux/macOS:
  ```bash
  ./build.sh
  ```

---

## 🤝 Contributing
Contributions are welcome!  
1. Fork the repo  
2. Create a feature branch (`git checkout -b feature/my-feature`)  
3. Commit your changes (`git commit -m "Add my feature"`)  
4. Push to the branch (`git push origin feature/my-feature`)  
5. Open a Pull Request  

---

## 📜 License
This project is licensed under the terms of the [MIT License](LICENSE).
