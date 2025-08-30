# Plik np. keymapuino-cli/plugin_api.py

class BasePlugin:
    """Klasa bazowa dla wszystkich pluginów."""
    def __init__(self, core_api):
        """
        Inicjalizacja pluginu.
        :param core_api: Obiekt dający dostęp do funkcji programu, np. wysyłania do Arduino.
        """
        self.api = core_api

    def update(self):
        """
        Metoda wywoływana cyklicznie przez główną pętlę programu.
        Tutaj plugin zbiera swoje dane i decyduje o akcjach.
        """
        pass # Każdy plugin implementuje swoją logikę

class CoreAPI:
    """Obiekt przekazywany do pluginów, aby mogły komunikować się z resztą programu."""
    def __init__(self, arduino_serial):
        self._arduino = arduino_serial

    def send_to_arduino(self, command):
        """Wysyła komendę do Arduino."""
        if self._arduino and self._arduino.is_open:
            self._arduino.write(f"{command}\n".encode('utf-8'))