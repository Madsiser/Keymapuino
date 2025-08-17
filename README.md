# 🔑 Keymapuino

**Keymapuino** is an open-source project combining Arduino firmware, a command-line interface (CLI), and a graphical user interface (GUI) to simplify the creation and management of keyboard keymaps. Using an Arduino board, it reads input pin voltages and maps them to keyboard events on your computer.

---

## ✨ Features

* 🛠 **Arduino Firmware** – Runs on Arduino Uno and compatible boards.
* 💻 **Command-Line Interface (CLI)** – Lightweight terminal control; communicates with Arduino over serial.
* 🎨 **Graphical User Interface (GUI)** – User-friendly interface to configure keymaps and manage the CLI.
* 🔄 **Cross-Platform Build Scripts** – Supports Windows (`build.bat`) and Linux/macOS (`build.sh`).

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

* `arduino-uno.ino` – main firmware file for Arduino Uno.
* CLI and GUI communicate with Arduino via serial.

---

## 🛠 Build & Run

After installing dependencies, run the build script:

* **Windows:**

```powershell
build.bat
```

* **Linux/macOS:**

```bash
./build.sh
```

The `release/Keymapuino/` folder will contain:

```
release/Keymapuino/
├── bin/
│   └── keymapuino-cli(.exe)
└── keymapuino-gui(.exe / no .exe on Linux/macOS)
```

* On Linux/macOS, make executables runnable:

```bash
chmod +x keymapuino-cli keymapuino-gui
```

**Run CLI / GUI:**

* **Windows**

```powershell
.\release\Keymapuino\bin\keymapuino-cli.exe --config config.json
.\release\Keymapuino\keymapuino-gui.exe
```

* **Linux/macOS**

```bash
./release/Keymapuino/bin/keymapuino-cli --config config.json
./release/Keymapuino/keymapuino-gui
```

---

## ⚠️ Note for Windows 11 Users

Windows may warn about running an **unsigned .exe file**.
For security, it’s recommended to build the project from source.

---

## 💾 CLI Usage

**Configuration (`config.json`):**

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

* `port` – Arduino serial port (e.g., `COM3` on Windows, `/dev/ttyUSB0` on Linux).
* `key_mapping` – maps Arduino pins to keyboard keys:

  * **Digital pin** → `{ "key": "a" }`
  * **Analog pin** → list of objects with `"key"`, `"threshold"`, and optional `"hold_time_ms"`.

**Run CLI (Python source):**

```bash
python keymapuino-cli.py --config config.json --log 2 --port COM3
```

**Arguments:**

* `--config` → path to JSON config (default: `config.json`)
* `--log` → log level (1=minimal, 4=debug)
* `--port` → optionally override port from config

---

## 🖥 GUI Usage

**Run GUI (Python source):**

```bash
python keymapuino-gui.py
```

**Features:**

* Auto-detect or refresh Arduino ports
* Add/remove digital/analog pin mappings
* Save/load configuration files (`.conf`)
* Start/stop CLI backend
* View live logs

**Example workflow:**

1. Open GUI.
2. Select Arduino port.
3. Add pins and assign keys.
4. Save configuration.
5. Click **Start Program** – CLI runs automatically.
6. Check program status (green = running).
7. View logs for debugging.
8. Stop program using the button or close GUI.

---

## 🏗 Build Scripts

* **Windows:**

```bash
build.bat
```

* **Linux/macOS:**

```bash
./build.sh
```

**Requirements:** Python 3.x, Arduino IDE or PlatformIO (if extra libraries used).

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

**Coding style:** Follow PEP8 for Python.

---

## 📜 License

Licensed under the [MIT License](LICENSE).

---
