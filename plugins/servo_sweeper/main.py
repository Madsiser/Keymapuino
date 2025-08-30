import time

class Plugin:
    def __init__(self, core_api, settings):
        """
        Inicjalizuje plugin, wczytując jego ustawienia i stan początkowy.
        """
        self.api = core_api
        self.settings = settings if settings is not None else {}
        
        # Wczytaj konfigurację z pliku JSON z bezpiecznymi wartościami domyślnymi
        self.pin = self.settings.get("pin")
        self.step_delay_sec = self.settings.get("step_delay_ms", 50) / 1000.0  # Konwertuj na sekundy
        self.step_size = self.settings.get("step_size", 2)
        
        # Zmienne stanu do śledzenia ruchu serwa
        self.current_angle = 0
        self.direction = 1  # 1 oznacza ruch w stronę 180, -1 w stronę 0
        self.last_update_time = 0
        
        if self.pin is not None:
            self.api.log(f"Servo Sweeper initialized on pin {self.pin}.", level='info')
        else:
            self.api.log("Servo Sweeper loaded, but no pin is configured.", level='warning')

    def get_pins_to_setup(self):
        """
        Informuje rdzeń aplikacji, że ten plugin wymaga, aby pin był skonfigurowany
        jako wyjście typu 'servo'.
        """
        if self.pin is not None:
            return {
                self.pin: {'mode': 'servo'}
            }
        return {}

    def update(self):
        """
        Główna metoda logiki, wywoływana cyklicznie przez keymapuino-cli.
        """
        # Jeśli pin nie jest skonfigurowany, nic nie rób
        if self.pin is None:
            return
            
        # Sprawdź, czy minął już czas na kolejny ruch
        if (time.time() - self.last_update_time) < self.step_delay_sec:
            return
            
        # Oblicz następną pozycję
        self.current_angle += self.step_size * self.direction
        
        # Sprawdź granice i zmień kierunek, jeśli to konieczne
        if self.current_angle >= 180:
            self.current_angle = 180
            self.direction = -1  # Zmień kierunek na powrót
        elif self.current_angle <= 0:
            self.current_angle = 0
            self.direction = 1   # Zmień kierunek na ruch w przód
            
        # Wyślij komendę do Arduino
        self.api.set_servo_angle(self.pin, self.current_angle)
        
        # Zapisz czas ostatniej aktualizacji
        self.last_update_time = time.time()
        
        self.api.log(f"Set servo on pin {self.pin} to {self.current_angle} degrees.", level='debug')
