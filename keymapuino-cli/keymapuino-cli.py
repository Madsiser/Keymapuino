import sys
import os

def get_base_path():
    if getattr(sys, 'frozen', False):
        executable_path = os.path.dirname(sys.executable)
        return os.path.abspath(os.path.join(executable_path, ".."))
    else:
        return os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, get_base_path())

import json
import time
import serial
import argparse
import signal
import importlib
from pynput.keyboard import Controller

class CoreAPI:
    """Uproszczone API dla pluginów - tylko wysyłanie danych i logowanie."""
    def __init__(self, controller, log_function, plugin_name="Core"):
        self.controller = controller
        self._log = log_function
        self._plugin_name = plugin_name

    def set_digital_state(self, pin, state):
        cmd = f"D,{pin},{1 if state else 0}"
        self.controller.send_command_no_wait(cmd)

    def set_pwm_value(self, pin, value):
        value = max(0, min(255, int(value)))
        cmd = f"P,{pin},{value}"
        self.controller.send_command_no_wait(cmd)

    def set_servo_angle(self, pin, angle):
        angle = max(0, min(180, int(angle)))
        cmd = f"S,{pin},{angle}"
        self.controller.send_command_no_wait(cmd)
        
    def log(self, message, level='info'):
        level_map = {'debug': 4, 'info': 2, 'warning': 1, 'error': 1}
        numeric_level = level_map.get(level.lower(), 2)
        self._log(f"[Plugin: {self._plugin_name}] {message}", level=numeric_level)

class ArduinoController:
    # ... (bez zmian)
    def __init__(self, port, baud_rate=9600, timeout=1, log_func=print):
        try: self.ser = serial.Serial(port, baud_rate, timeout=timeout)
        except serial.SerialException as e: print(f"[ERROR] Could not open serial port '{port}': {e}"); sys.exit(1)
        self.log = log_func; time.sleep(2)
    def _send_and_wait(self, command, timeout=2.0):
        self.ser.write(f"{command}\n".encode('utf-8')); self.log(f"Sent: {command}", level=4); start_time = time.time()
        while time.time() - start_time < timeout:
            if self.ser.in_waiting > 0:
                response = self.ser.readline().decode('utf-8').strip(); self.log(f"Received: {response}", level=4)
                if response == 'OK': return True, "OK"
                if response.startswith('ERROR:'): return False, response
        return False, "Timeout"
    def configure_pin(self, pin, mode): return self._send_and_wait(f"pin {pin} mode {mode}")
    def start_reading(self, pin, read_type): return self._send_and_wait(f"pin {pin} read {read_type}")
    def send_command_no_wait(self, command): self.ser.write(f"{command}\n".encode('utf-8')); self.log(f"Sent (no-wait): {command}", level=4)
    def clear_all(self): return self._send_and_wait("clear")
    def read_line(self):
        if self.ser.in_waiting > 0: return self.ser.readline().decode('utf-8').strip()
        return None
    def close(self):
        if self.ser and self.ser.is_open: self.ser.close()

class KeymapuinoCLI:
    def __init__(self, config_path, log_level=2, port=None):
        self.config_path = config_path
        self.log_level = log_level
        self.port_override = port
        self.running = True
        
        self.key_states = {}
        self.max_hold_time = 0.1

        self.load_config()
        
        self.keyboard = Controller()
        self.controller = ArduinoController(self.port, log_func=self.log)
        self.plugins = self._load_plugins()
        
        signal.signal(signal.SIGINT, self.handle_sigint)

    def log(self, message, level=1):
        if self.log_level >= level: print(message, flush=True)

    def load_config(self):
        try:
            with open(self.config_path) as config_file: config = json.load(config_file)
            self.port = self.port_override if self.port_override else config['port']
            self.key_mapping = config.get('key_mapping', {})
            self.plugin_configs = config.get('plugins', [])
            
            for mapping in self.key_mapping.values():
                if isinstance(mapping, dict):
                    self.key_states[mapping['key']] = {'pressed': False, 'hold_time': 0}
                elif isinstance(mapping, list):
                    for entry in mapping: self.key_states[entry['key']] = {'pressed': False, 'hold_time': 0}
        except FileNotFoundError: print(f"[ERROR] Config file not found at: {self.config_path}"); sys.exit(1)
        except json.JSONDecodeError: print(f"[ERROR] Could not parse config file: {self.config_path}"); sys.exit(1)

    def _load_plugins(self):
        plugins = []
        plugin_dir = os.path.join(get_base_path(), "plugins")
        if not os.path.isdir(plugin_dir): return plugins
        for config in self.plugin_configs:
            name = config.get("name")
            settings = config.get("settings", {})
            if not name: continue
            try:
                plugin_api = CoreAPI(self.controller, self.log, plugin_name=name)
                module = importlib.import_module(f"plugins.{name}.main")
                plugin_instance = module.Plugin(plugin_api, settings)
                plugins.append(plugin_instance)
                self.log(f"Plugin '{name}' loaded.", level=2)
            except Exception as e:
                self.log(f"Error loading plugin '{name}': {e}", level=1)
        return plugins

    def handle_sigint(self, signum, frame):
        self.log("\n[INFO] Shutting down...", level=1); self.running = False

    def setup_arduino(self):
        self.log("Sending configuration to Arduino...", level=1)
        self.controller.clear_all()

        for pin, mapping in self.key_mapping.items():
            is_analog = isinstance(mapping, list)
            mode = "input" if is_analog else "pullup"
            self.controller.configure_pin(pin, mode)
            read_type = "analog" if is_analog else "digital"
            self.controller.start_reading(pin, read_type)

        for plugin in self.plugins:
            if hasattr(plugin, 'settings'):
                pin = plugin.settings.get("pin"); pin_type = plugin.settings.get("type")
                if pin is None or pin_type is None: continue
                if pin_type in ["digital", "pwm"]: mode_to_set = "output"
                elif pin_type == "servo": mode_to_set = "servo"
                else: continue
                self.controller.configure_pin(pin, mode_to_set)
        self.log("Configuration sent successfully.", level=1)

    def main_loop(self):
        self.log("STARTING", level=2)
        self.setup_arduino()
        while self.running:
            for plugin in self.plugins: plugin.update()
            line = self.controller.read_line()
            if line and line.upper() != 'OK' and not line.startswith('ERROR:'):
                self.log(f"Received from Arduino: {line}", level=4)
                if ':' in line:
                    pin, value_str = line.split(':', 1)
                    try: self.handle_analog_input(pin, int(value_str))
                    except ValueError: self.log(f"Could not parse analog value: {line}", level=2)
                else:
                    self.handle_digital_input(line)
            self.check_and_release_keys()
            time.sleep(0.001)
        self.cleanup()
    
    def handle_analog_input(self, pin, value):
        self.log(f"Analog {pin} = {value}", level=3)
        if pin in self.key_mapping:
            for mapping in self.key_mapping[pin]:
                key = mapping['key']; t_min, t_max = mapping['threshold']
                hold_required = mapping.get('hold_time_ms', 0) / 1000.0
                in_range = t_min <= value <= t_max
                state = self.key_states[key]
                if in_range:
                    if not state['pressed']:
                        if 'range_enter_time' not in state: state['range_enter_time'] = time.time()
                        elif time.time() - state['range_enter_time'] >= hold_required:
                            self.keyboard.press(key); state['pressed'] = True
                            self.log(f"Pressed key: {key}", level=1)
                else:
                    if state['pressed']: self.keyboard.release(key); state['pressed'] = False; self.log(f"Released key: {key}", level=1)
                    state.pop('range_enter_time', None)

    def handle_digital_input(self, pin):
        if pin in self.key_mapping:
            key = self.key_mapping[pin]['key']; state = self.key_states[key]
            state['hold_time'] = time.time()
            if not state['pressed']:
                self.keyboard.press(key); state['pressed'] = True
                self.log(f"Pressed key: {key}", level=1)

    def check_and_release_keys(self):
        for key, state in self.key_states.items():
            if state['pressed']:
                is_digital = any(isinstance(m, dict) and m['key'] == key for m in self.key_mapping.values())
                if is_digital:
                    if (time.time() - state['hold_time']) > self.max_hold_time:
                        self.keyboard.release(key); state['pressed'] = False
                        self.log(f"Auto-released key: {key}", level=1)

    def cleanup(self):
        self.log("Cleaning up...", level=2)
        if hasattr(self, 'controller'): self.controller.clear_all(); self.controller.close()
        self.log("Serial port closed. Exiting.", level=1); sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serial keyboard controller")
    parser.add_argument('--config', type=str, default='config.json', help='Path to JSON config')
    parser.add_argument('--log', type=int, choices=[1, 2, 3, 4], default=2, help='Logging level')
    parser.add_argument('--port', type=str, help='Serial port')
    args = parser.parse_args()
    config_path = args.config if os.path.isabs(args.config) else os.path.join(get_base_path(), args.config)
    app = KeymapuinoCLI(config_path, args.log, args.port)
    app.main_loop()