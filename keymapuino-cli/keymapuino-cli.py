import json
import time
import serial
import argparse
from pynput.keyboard import Controller

parser = argparse.ArgumentParser(description="Serial keyboard controller")
parser.add_argument('--config', type=str, default='config.json', help='Path to the JSON configuration file')
parser.add_argument('--log', type=int, choices=[1, 2, 3, 4], default=1, help='Logging level (1-3)')
parser.add_argument('--port', type=str, help='Serial port (e.g. COM3, /dev/ttyUSB0)')
args = parser.parse_args()

LOG_LEVEL = args.log

def log(message, level=1):
    if LOG_LEVEL >= level:
        print(message)

with open(args.config) as config_file:
    config = json.load(config_file)

port = args.port if args.port else config['port']
key_mapping = config['key_mapping']
max_hold_time = 0.1

keyboard = Controller()
ser = serial.Serial(port, 9600, timeout=1)

key_states = {}

for pin, mapping in key_mapping.items():
    if isinstance(mapping, dict):
        key = mapping['key']
        key_states[key] = {'pressed': False, 'hold_time': 0}
    elif isinstance(mapping, list):
        for entry in mapping:
            key = entry['key']
            key_states[key] = {'pressed': False, 'hold_time': 0}

def send_and_confirm(cmd):
    for attempt in range(3):
        ser.write((cmd + '\n').encode())
        log(f"Sent: {cmd} (attempt {attempt + 1})", level=4)
        start_time = time.time()
        while time.time() - start_time < 2:
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                log(f"Received: {response}", level=4)
                if response == 'OK':
                    return True
                elif response == 'ERR':
                    log("Received ERR – retrying...", level=4)
                    break
        time.sleep(0.1)
    log(f"Error: no confirmation for command '{cmd}'", level=1)
    return False

def send_mode_commands():
    log("Sending configuration to Arduino...", level=1)
    if not send_and_confirm("clear"):
        log("Failed to clear Arduino configuration.", level=1)

    for pin, mapping in key_mapping.items():
        if isinstance(mapping, dict):
            cmd = f"mode digital {pin}"
        elif isinstance(mapping, list):
            cmd = f"mode analog {pin}"
        else:
            log(f"Unknown configuration for pin {pin}", level=1)
            continue
        send_and_confirm(cmd)

    log("Configuration sent.", level=1)
    log("RUN", level=2)

log("STARTING", level=2)

send_mode_commands()

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            log(f"Received from Arduino: {line}", level=4)

            if ':' in line:
                pin, value = line.split(':')
                value = int(value)
                log(f"Analog {pin} = {value}", level=3)

                if pin in key_mapping and isinstance(key_mapping[pin], list):
                    for mapping in key_mapping[pin]:
                        key = mapping['key']
                        t_min, t_max = mapping['threshold']
                        hold_required = mapping.get('hold_time_ms', 0) / 1000.0

                        in_range = t_min <= value <= t_max

                        if in_range:
                            if not key_states[key]['pressed']:
                                if 'range_enter_time' not in key_states[key]:
                                    key_states[key]['range_enter_time'] = time.time()
                                elif time.time() - key_states[key]['range_enter_time'] >= hold_required:
                                    keyboard.press(key)
                                    key_states[key]['pressed'] = True
                                    key_states[key]['hold_time'] = time.time()
                                    log(f"Pressed key: {key}", level=1)
                            else:
                                key_states[key]['hold_time'] = time.time()
                        else:
                            if key_states[key]['pressed']:
                                keyboard.release(key)
                                key_states[key]['pressed'] = False
                                log(f"Released key: {key}", level=1)
                            key_states[key].pop('range_enter_time', None)

            else:
                pin = line
                if pin in key_mapping and isinstance(key_mapping[pin], dict):
                    key = key_mapping[pin]['key']
                    if not key_states[key]['pressed']:
                        keyboard.press(key)
                        key_states[key]['pressed'] = True
                        key_states[key]['hold_time'] = time.time()
                        log(f"Pressed key: {key}", level=1)
                    else:
                        key_states[key]['hold_time'] = time.time()
        else:
            for key, state in key_states.items():
                if state['pressed']:
                    hold_time = time.time() - state['hold_time']
                    log(f"Hold time for {key}: {hold_time:.3f}", level=3)
                    if hold_time > max_hold_time:
                        keyboard.release(key)
                        key_states[key]['pressed'] = False
                        log(f"Released key: {key}", level=1)

except KeyboardInterrupt:
    log("Program terminated by user.", level=1)
finally:
    send_and_confirm("clear")
    ser.close()
