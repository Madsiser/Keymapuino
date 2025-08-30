# plugins/key_presser/ui_logic.py
import tkinter as tk
from tkinter import messagebox

class UILogic:
    def __init__(self, initial_settings=None):
        """
        Inicjalizuje model danych dla okna konfiguracji.
        """
        import copy
        # Używamy deepcopy, aby edycja nie wpływała na główną konfigurację, dopóki nie klikniemy OK.
        self.data_model = copy.deepcopy(initial_settings) if initial_settings is not None else {
            "mappings": {},
            "max_hold_time_ms": 100,
            "current_analog_pin": "",
            "analog_key_entry": "",
            "analog_low_entry": 0,
            "analog_high_entry": 0,
            "analog_hold_entry": 0
        }

    # --- Metody Akcji, które są wywoływane przez renderer GUI ---
    
    def action_add_digital_mapping(self, dialog_instance):
        """
        Logika dla przycisku 'Add / Update' w zakładce Digital.
        Otrzymuje instancję okna dialogowego, aby mieć dostęp do jego widżetów.
        """
        widgets = dialog_instance.widgets
        pin = widgets["digital_pin_entry"].get()
        key = widgets["digital_key_entry"].get()
        if not (pin and key): return
        
        mappings = self.data_model.setdefault("mappings", {})
        mappings[pin] = {"key": key}
        
        dialog_instance.refresh_bindings() # Mówi dialogowi, aby odświeżył widok
        widgets["digital_pin_entry"].delete(0, "end")
        widgets["digital_key_entry"].delete(0, "end")

    def action_remove_digital_mapping(self, dialog_instance):
        widgets = dialog_instance.widgets
        listbox = widgets["digital_listbox"]
        selection = listbox.curselection()
        if not selection: return
        
        item_text = listbox.get(selection[0])
        pin_to_remove = item_text.split(" -> ")[0]
        
        mappings = self.data_model.get("mappings", {})
        if pin_to_remove in mappings:
            del mappings[pin_to_remove]
            
        dialog_instance.refresh_bindings()

    def action_add_analog_threshold(self, dialog_instance):
        current_pin = self.data_model.get("current_analog_pin", "").strip()
        if not current_pin:
            messagebox.showerror("Error", "Please enter an Analog Pin first (e.g., A0).", parent=dialog_instance)
            return
        
        try:
            key = self.data_model["analog_key_entry"]
            low = int(self.data_model["analog_low_entry"])
            high = int(self.data_model["analog_high_entry"])
            hold = int(self.data_model["analog_hold_entry"])
            if not key or low > high: raise ValueError()
        except (KeyError, ValueError):
            messagebox.showerror("Error", "Please fill all threshold fields with valid data.", parent=dialog_instance)
            return
        
        mappings = self.data_model.setdefault("mappings", {})
        threshold_list = mappings.setdefault(current_pin, [])
        new_threshold = {"key": key, "threshold": [low, high], "hold_time_ms": hold}
        threshold_list.append(new_threshold)
        
        dialog_instance.refresh_bindings()

    def action_remove_analog_threshold(self, dialog_instance):
        current_pin = self.data_model.get("current_analog_pin", "").strip()
        if not current_pin: return
        
        listbox = dialog_instance.widgets.get("analog_threshold_list")
        if not listbox: return
        
        selection = listbox.curselection()
        if not selection: return
        
        index_to_remove = selection[0]
        mappings = self.data_model.get("mappings", {})
        if current_pin in mappings and len(mappings[current_pin]) > index_to_remove:
            mappings[current_pin].pop(index_to_remove)
            if not mappings[current_pin]:
                del mappings[current_pin]
        
        dialog_instance.refresh_bindings()