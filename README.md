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

## 📖 Usage Examples

### CLI
```bash
# List available keymaps
python keymapuino-cli.py list

# Flash a new keymap
python keymapuino-cli.py flash mykeymap.json
```

### GUI
Launch the GUI:
```bash
python keymapuino-gui.py
```
Use the interface to browse, edit, and flash keymaps.

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
