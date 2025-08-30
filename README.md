# 🔑 Keymapuino v2.0.1

**Keymapuino** is an open-source system for creating and managing keymaps and I/O control on Arduino, featuring a convenient CLI, advanced GUI, and plugin support. It enables dynamic pin configuration, keyboard handling, servos, LEDs, and other devices—without reflashing the firmware.

---

## ✨ Main Features

* 🛠 **Arduino Firmware** – dynamic pin handling, servos, PWM, digital/analog inputs.
* 💻 **CLI (Command-Line Interface)** – control and key mapping via terminal, serial communication.
* 🎨 **GUI** – graphical configuration of keymaps, plugins, and ports.
* 🧩 **Plugins** – logic extensions, e.g. automatic servo control, macro support.
* 🔄 **Build scripts** – support for Windows (`build.bat`) and Linux/macOS (`build.sh`).

---

## 📂 Project Structure

```
Keymapuino/
├── keymapuino-arduino/   # Arduino firmware (arduino-uno.ino)
├── keymapuino-cli/       # CLI (Python)
├── keymapuino-gui/       # GUI (Python)
├── plugins/              # Plugins (each in a separate folder)
├── build.bat             # Windows build
├── build.sh              # Linux/macOS build
├── LICENSE
└── README.md
```

* `arduino-uno.ino` – main firmware for Arduino Uno.
* CLI and GUI communicate with Arduino via serial.
* Plugins: each plugin is a folder with `main.py` and optional `ui.json` (GUI definition).

---

## 🛠 Installation & Running

After installing dependencies, run the build script:

* **Windows:**
    ```powershell
    build.bat
    ```
* **Linux/macOS:**
    ```bash
    ./build.sh
    ```

In the `release/Keymapuino/` folder you will find:

```
release/Keymapuino/
├── bin/
│   └── keymapuino-cli(.exe)
└── keymapuino-gui(.exe / no .exe on Linux/macOS)
```

On Linux/macOS, grant execute permissions:
```bash
chmod +x keymapuino-cli keymapuino-gui
```

**Running CLI / GUI:**

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

The system may warn about running unsigned `.exe` files.
For safety, building the project from source is recommended.

---

## 💾 CLI Configuration (`config.json`)

Example:
```json
{
  "port": "/dev/ttyUSB0",
  "key_mapping": {
    "2": { "key": "a" },
    "3": { "key": "b" },
    "A0": [
      { "key": "x", "threshold": [0, 500] },
      { "key": "y", "threshold": [501, 1023], "hold_time_ms": 300 }
    ]
  },
  "plugins": [
    {
      "name": "servo_sweeper",
      "settings": { "pin": 9, "step_delay_ms": 50, "step_size": 2 }
    }
  ]
}
```

* `port` – Arduino serial port (`COM3` on Windows, `/dev/ttyUSB0` on Linux).
* `key_mapping` – pin-to-key mapping:
  * **Digital pin** → `{ "key": "a" }`
  * **Analog pin** → list of objects with `"key"`, `"threshold"`, optionally `"hold_time_ms"`
* `plugins` – list of active plugins and their settings.

**Run CLI (Python):**
```bash
python keymapuino-cli.py --config config.json --log 2 --port /dev/ttyUSB0
```

Arguments:
* `--config` → path to config file (default: `config.json`)
* `--log` → log level (1=minimal, 4=debug)
* `--port` → overrides port from config

---

## 🖥 GUI Usage

**Run GUI (Python):**
```bash
python keymapuino-gui.py
```

**Features:**
* Automatic Arduino port detection
* Add/remove digital/analog pin mappings
* Edit and configure plugins (e.g. `servo_sweeper`)
* Save/load configuration (`.json`)
* Start/stop CLI backend
* Live log viewer

**Sample workflow:**
1. Open GUI.
2. Select Arduino port.
3. Add pins and assign keys.
4. Add/edit plugins.
5. Save configuration.
6. Click **Start Program** – CLI launches automatically.
7. Check program status (green = running).
8. View logs for debugging.
9. Stop program or close GUI.

---

## 🧩 Plugins

Each plugin is a folder in `plugins/` with `main.py` (logic) and optional `ui.json` (GUI definition).

Example plugin: **servo_sweeper**
* Automatically sweeps a servo back and forth on a selected pin.
* Configuration: pin, step delay, step size.

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

**Requirements:** Python 3.x, Arduino IDE or PlatformIO (if using extra libraries).

---

## 🤝 Contributing

1. Fork the repository
2. Create a branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

**Coding style:** PEP8 for Python.

---

## 📜 License

Project is licensed under MIT. See [LICENSE](LICENSE)
