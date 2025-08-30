import random
import time

class Plugin:
    def __init__(self, core_api, settings=None):
        self.api = core_api
        self.settings = settings if settings is not None else {}
        self.last_update = 0
        self._load_settings()

    def _load_settings(self):
        self.pin = self.settings.get("pin")
        self.type = self.settings.get("type", "pwm")
        self.interval = self.settings.get("update_interval_ms", 500) / 1000.0
        self.min_val = self.settings.get("min_value", 0)
        self.max_val = self.settings.get("max_value", 255)

    def update(self):
        """Logika backendowa, wywoływana w każdej pętli."""
        if self.pin is None or (time.time() - self.last_update) < self.interval:
            return

        value = random.randint(self.min_val, self.max_val)

        if self.type == "pwm":
            self.api.set_pwm_value(self.pin, value)
        elif self.type == "digital":
            self.api.set_digital_state(self.pin, bool(value))
        elif self.type == "servo":
            self.api.set_servo_angle(self.pin, value)
        
        self.last_update = time.time()
