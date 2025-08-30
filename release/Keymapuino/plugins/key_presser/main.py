import random
import time

class Plugin:
    def __init__(self, core_api, settings):
        self.api = core_api # To jest teraz uproszczone API
        self.settings = settings
        self.pin = self.settings.get("pin")
        self.type = self.settings.get("type", "pwm")
        self.interval = self.settings.get("update_interval_ms", 500) / 1000.0
        self.last_update = 0
        self.api.log("RandomOutput plugin initialized.", level='info')

    def update(self):
        if self.pin is None or (time.time() - self.last_update) < self.interval:
            return

        # Prosta logika: wyślij losową wartość do skonfigurowanego pinu
        if self.type == "pwm":
            value = random.randint(0, 255)
            self.api.set_pwm_value(self.pin, value)
            self.api.log(f"Sent PWM value {value} to pin {self.pin}", level='debug')
        elif self.type == "digital":
            state = random.choice([True, False])
            self.api.set_digital_state(self.pin, state)
            self.api.log(f"Sent digital state {state} to pin {self.pin}", level='debug')

        self.last_update = time.time()
