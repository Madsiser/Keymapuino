import json
import time
import serial
import argparse
import signal
import sys
from pynput.keyboard import Controller

class KeymapuinoCLI:
    def __init__(self, config_path, log_level, port_override=None):
        self.config_path = config_path
        self.log_level = log_level
        self.port_override = port_override

        self.keyboard = Controller()
        self.running = True
        self.max_hold_time = 0.1
        self.key_states = {}

        self.load_config()
        self.setup_serial()

        signal.signal(signal.SIGINT, self.handle_sigint)

    def log(self, message, level=1):
        if self.log_level >= level:
            print(message, flush=True)

    def load_config(self):
        with open(self.config_path) as config_file:
            config = json.load(config_file)

        self.port = self.port_override if self.port_override else config['port']
        self.key_mapping = config['key_mapping']

        for pin, mapping in self.key_mapping.items():
            if isinstance(mapping, dict):
                key = mapping['key']
                self.key_states[key] = {'pressed': False, 'hold_time': 0}
            elif isinstance(mapping, list):
                for entry in mapping:
                    key = entry['key']
                    self.key_states[key] = {'pressed': False, 'hold_time': 0}

    def setup_serial(self):
        self.ser = serial.Serial(self.port, 9600, timeout=1)

    def handle_sigint(self, signum, frame):
        self.log("\n[INFO] Otrzymano SIGINT. Kończenie działania...", level=1)
        self.running = False

    def send_and_confirm(self, cmd):
        for attempt in range(3):
            self.ser.write((cmd + '\n').encode())
            self.log(f"Sent: {cmd} (attempt {attempt + 1})", level=4)
            start_time = time.time()
            while time.time() - start_time < 2:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8').strip()
                    self.log(f"Received: {response}", level=4)
                    if response == 'OK':
                        return True
                    elif response == 'ERR':
                        self.log("Received ERR – retrying...", level=4)
                        break
            time.sleep(0.1)
        self.log(f"Error: no confirmation for command '{cmd}'", level=1)
        return False

    def send_mode_commands(self):
        self.log("Sending configuration to Arduino...", level=1)
        if not self.send_and_confirm("clear"):
            self.log("Failed to clear Arduino configuration.", level=1)

        for pin, mapping in self.key_mapping.items():
            if isinstance(mapping, dict):
                cmd = f"mode digital {pin}"
            elif isinstance(mapping, list):
                cmd = f"mode analog {pin}"
            else:
                self.log(f"Unknown configuration for pin {pin}", level=1)
                continue
            self.send_and_confirm(cmd)

        self.log("Configuration sent.", level=1)
        self.log("RUN", level=2)

    def main_loop(self):
        self.log("STARTING", level=2)
        self.send_mode_commands()

        while self.running:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8').strip()
                self.log(f"Received from Arduino: {line}", level=4)

                if ':' in line:
                    pin, value = line.split(':')
                    value = int(value)
                    self.log(f"Analog {pin} = {value}", level=3)

                    if pin in self.key_mapping and isinstance(self.key_mapping[pin], list):
                        for mapping in self.key_mapping[pin]:
                            key = mapping['key']
                            t_min, t_max = mapping['threshold']
                            hold_required = mapping.get('hold_time_ms', 0) / 1000.0

                            in_range = t_min <= value <= t_max

                            if in_range:
                                if not self.key_states[key]['pressed']:
                                    if 'range_enter_time' not in self.key_states[key]:
                                        self.key_states[key]['range_enter_time'] = time.time()
                                    elif time.time() - self.key_states[key]['range_enter_time'] >= hold_required:
                                        self.keyboard.press(key)
                                        self.key_states[key]['pressed'] = True
                                        self.key_states[key]['hold_time'] = time.time()
                                        self.log(f"Pressed key: {key}", level=1)
                                else:
                                    self.key_states[key]['hold_time'] = time.time()
                            else:
                                if self.key_states[key]['pressed']:
                                    self.keyboard.release(key)
                                    self.key_states[key]['pressed'] = False
                                    self.log(f"Released key: {key}", level=1)
                                self.key_states[key].pop('range_enter_time', None)
                else:
                    pin = line
                    if pin in self.key_mapping and isinstance(self.key_mapping[pin], dict):
                        key = self.key_mapping[pin]['key']
                        if not self.key_states[key]['pressed']:
                            self.keyboard.press(key)
                            self.key_states[key]['pressed'] = True
                            self.key_states[key]['hold_time'] = time.time()
                            self.log(f"Pressed key: {key}", level=1)
                        else:
                            self.key_states[key]['hold_time'] = time.time()
            else:
                for key, state in self.key_states.items():
                    if state['pressed']:
                        hold_time = time.time() - state['hold_time']
                        self.log(f"Hold time for {key}: {hold_time:.3f}", level=3)
                        if hold_time > self.max_hold_time:
                            self.keyboard.release(key)
                            self.key_states[key]['pressed'] = False
                            self.log(f"Released key: {key}", level=1)

        self.cleanup()

    def cleanup(self):
        self.log("Cleaning up...", level=2)
        self.send_and_confirm("clear")
        self.ser.close()
        self.log("Serial port closed. Exiting.", level=1)
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serial keyboard controller")
    parser.add_argument('--config', type=str, default='config.json', help='Path to the JSON configuration file')
    parser.add_argument('--log', type=int, choices=[1, 2, 3, 4], default=1, help='Logging level (1-4)')
    parser.add_argument('--port', type=str, help='Serial port (e.g. COM3, /dev/ttyUSB0)')
    args = parser.parse_args()

    app = KeymapuinoCLI(args.config, args.log, args.port)
    app.main_loop()
