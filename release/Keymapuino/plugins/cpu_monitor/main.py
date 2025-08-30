# Plik: keymapuino-cli/plugins/cpu_monitor/main.py

from plugin_api import BasePlugin # Importujemy klasę bazową
import psutil

LED_PIN = 13

class Plugin(BasePlugin):
    """
    Plugin, który monitoruje użycie CPU i steruje diodą LED.
    """
    def __init__(self, core_api):
        super().__init__(core_api)
        self.led_is_on = False
        print("Plugin CPU Monitor zainicjalizowany.")

    def update(self):
        # Pobierz aktualne użycie CPU
        cpu_usage = psutil.cpu_percent()

        if cpu_usage > 50 and not self.led_is_on:
            # Użycie > 50%, włącz diodę
            print("CPU > 50%. Włączam LED.")
            self.api.send_to_arduino(f"D,{LED_PIN},1")
            self.led_is_on = True
        elif cpu_usage <= 50 and self.led_is_on:
            # Użycie <= 50%, wyłącz diodę
            print("CPU <= 50%. Wyłączam LED.")
            self.api.send_to_arduino(f"D,{LED_PIN},0")
            self.led_is_on = False