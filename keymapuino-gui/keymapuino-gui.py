import sys
import os

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, get_base_path())

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import subprocess
import threading
import signal
import serial.tools.list_ports

class AnalogPinDialog(tk.Toplevel):
    def __init__(self, parent, pin_name, initial_data=None):
        super().__init__(parent)
        self.title(f"Analog Pin Editor: {pin_name}")
        self.transient(parent)
        self.grab_set()
        
        self.pin_name = pin_name
        self.result = initial_data if initial_data is not None else []
        
        self.create_widgets()
        self._refresh_listbox()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        list_frame = ttk.LabelFrame(main_frame, text="Thresholds")
        list_frame.pack(fill="both", expand=True)
        self.threshold_listbox = tk.Listbox(list_frame, height=8)
        self.threshold_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        ttk.Button(list_frame, text="Remove Selected", command=self._remove_threshold).pack(side="right", anchor="n", padx=5, pady=5)

        add_frame = ttk.LabelFrame(main_frame, text="Add New Threshold")
        add_frame.pack(fill="x", pady=10)

        ttk.Label(add_frame, text="Key:").grid(row=0, column=0, padx=5, pady=5)
        self.key_entry = ttk.Entry(add_frame, width=8)
        self.key_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="Low:").grid(row=0, column=2, padx=5, pady=5)
        self.low_entry = ttk.Entry(add_frame, width=8)
        self.low_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(add_frame, text="High:").grid(row=0, column=4, padx=5, pady=5)
        self.high_entry = ttk.Entry(add_frame, width=8)
        self.high_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(add_frame, text="Hold(ms):").grid(row=0, column=6, padx=5, pady=5)
        self.hold_entry = ttk.Entry(add_frame, width=8)
        self.hold_entry.grid(row=0, column=7, padx=5, pady=5)

        ttk.Button(add_frame, text="Add", command=self._add_threshold).grid(row=0, column=8, padx=10, pady=5)
        
        ttk.Button(main_frame, text="Save", command=self.on_save).pack(side="right", padx=5)
        ttk.Button(main_frame, text="Cancel", command=self.destroy).pack(side="right")

    def _refresh_listbox(self):
        self.threshold_listbox.delete(0, "end")
        for item in self.result:
            self.threshold_listbox.insert("end", f"Key: {item['key']}, Range: {item['threshold'][0]}-{item['threshold'][1]}, Hold: {item['hold_time_ms']}ms")

    def _add_threshold(self):
        try:
            key = self.key_entry.get()
            low = int(self.low_entry.get())
            high = int(self.high_entry.get())
            hold = int(self.hold_entry.get())
            if not key or low > high or low < 0 or high > 1023:
                raise ValueError
            new_threshold = {"key": key, "threshold": [low, high], "hold_time_ms": hold}
            self.result.append(new_threshold)
            self._refresh_listbox()
            self.key_entry.delete(0, "end")
            self.low_entry.delete(0, "end")
            self.high_entry.delete(0, "end")
            self.hold_entry.delete(0, "end")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid data.", parent=self)
    
    def _remove_threshold(self):
        selection = self.threshold_listbox.curselection()
        if not selection: return
        self.result.pop(selection[0])
        self._refresh_listbox()
    
    def on_save(self):
        self.destroy()

class PluginConfigDialog(tk.Toplevel):
    def __init__(self, parent, ui_definition, initial_settings=None):
        super().__init__(parent)
        self.title(ui_definition.get("window_title", "Configure Plugin"))
        self.transient(parent)
        self.result = None
        self.widgets = {}
        self.data_model = ui_definition.get("data_model", {})
        if initial_settings:
            import copy
            self.data_model = copy.deepcopy(initial_settings)
        main_frame = ttk.Frame(self)
        main_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)
        self.render_layout(main_frame, ui_definition.get("layout", {}))
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right")
        self.grab_set()

    def render_layout(self, parent, layout_def):
        if "grid" in layout_def:
            all_columns = [d.get("grid", {}).get("column", 0) for r in layout_def["grid"] for d in r["widgets"]]
            num_columns = max(all_columns) + 1 if all_columns else 1
            parent.columnconfigure(tuple(range(num_columns)), weight=1)
            for row_def in layout_def["grid"]:
                for widget_def in row_def["widgets"]:
                    self.create_widget(parent, widget_def, row_def["row"])

    def create_widget(self, parent, widget_def, row_index):
        widget_type = widget_def["type"]
        name = widget_def.get("name")
        widget = None
        if widget_type == "notebook":
            widget = ttk.Notebook(parent)
            for tab_def in widget_def.get("tabs", []):
                tab_frame = ttk.Frame(widget, padding=10)
                widget.add(tab_frame, text=tab_def.get("title", "Tab"))
                self.render_layout(tab_frame, tab_def.get("layout", {}))
        elif widget_type == "label":
            widget = ttk.Label(parent, text=widget_def.get("text", ""))
        elif widget_type == "entry":
            var = tk.StringVar()
            widget = ttk.Entry(parent, textvariable=var, width=widget_def.get("width"))
            bind_key = widget_def.get("bind_to")
            if bind_key:
                var.set(self.data_model.get(bind_key, widget_def.get("default", "")))
                var.trace_add("write", lambda *args, v=var, k=bind_key: self.update_data_model(k, v.get(), widget_def.get("var_type")))
        if widget:
            grid_opts = widget_def.get("grid", {})
            grid_opts.setdefault("row", row_index)
            grid_opts.setdefault("padx", 2); grid_opts.setdefault("pady", 2)
            widget.grid(**grid_opts)
            if name: self.widgets[name] = widget
    
    def on_ok(self):
        self.result = self.data_model
        self.destroy()
    
    def update_data_model(self, key, value, var_type=None):
        if var_type == "integer":
            try: value = int(value) if value else 0
            except (ValueError, TypeError): value = self.data_model.get(key, 0)
        self.data_model[key] = value

class KeymapuinoGUI:
    def __init__(self, root):
        self.version = "v5.0.1"
        self.root = root
        self.root.title("Keymapuino")
        self.proc = None
        self.config = {"port": "", "key_mapping": {}, "plugins": []}
        self.available_plugins = {}
        BASE_DIR = get_base_path()
        binary_name = "keymapuino-cli.exe" if sys.platform == "win32" else "keymapuino-cli"
        self.path = os.path.join(BASE_DIR, "bin", binary_name)
        self.log_path = os.path.join(BASE_DIR, "temp_log.txt")
        self.config_path = os.path.join(BASE_DIR, "config.json")
        self.plugins_dir = os.path.join(BASE_DIR, "plugins")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._scan_for_plugins()
        self.create_widgets()

    def _scan_for_plugins(self):
        if not os.path.isdir(self.plugins_dir): return
        for name in os.listdir(self.plugins_dir):
            if os.path.exists(os.path.join(self.plugins_dir, name, "ui.json")):
                self.available_plugins[name] = os.path.join(self.plugins_dir, name, "ui.json")

    def create_widgets(self):
        port_frame = ttk.LabelFrame(self.root, text="Port Settings")
        port_frame.pack(fill="x", padx=10, pady=5)
        self.port_combo = ttk.Combobox(port_frame, values=self.get_serial_ports(), state="normal")
        self.port_combo.pack(side="left", fill="x", expand=True, padx=5)
        self.port_combo.set(" ")
        ttk.Button(port_frame, text="Refresh", command=self.refresh_ports).pack(side="left", padx=5)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        keymap_tab = ttk.Frame(self.notebook, padding=5)
        plugins_tab = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(keymap_tab, text="Key Mapping")
        self.notebook.add(plugins_tab, text="Plugins (Output)")
        
        self.keymap_listbox = tk.Listbox(keymap_tab, height=10)
        self.keymap_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        keymap_btn_frame = ttk.Frame(keymap_tab)
        keymap_btn_frame.pack(side="right", fill="y")
        ttk.Button(keymap_btn_frame, text="Add Digital Pin", command=self.add_digital_pin).pack(pady=2, fill="x")
        ttk.Button(keymap_btn_frame, text="Add Analog Pin", command=self.add_analog_pin).pack(pady=2, fill="x")
        ttk.Button(keymap_btn_frame, text="Remove Pin", command=self.remove_pin).pack(pady=2, fill="x")

        self.plugin_listbox = tk.Listbox(plugins_tab, height=10)
        self.plugin_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        plugin_btn_frame = ttk.Frame(plugins_tab)
        plugin_btn_frame.pack(side="right", fill="y")
        ttk.Button(plugin_btn_frame, text="Add Plugin", command=self.add_plugin).pack(pady=2, fill="x")
        ttk.Button(plugin_btn_frame, text="Edit Plugin", command=self.edit_plugin).pack(pady=2, fill="x")
        ttk.Button(plugin_btn_frame, text="Remove Plugin", command=self.remove_plugin).pack(pady=2, fill="x")

        file_frame = ttk.Frame(self.root)
        file_frame.pack(pady=5)
        ttk.Button(file_frame, text="Save Config", command=self.save_to_file).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Load Config", command=self.load_from_file).pack(side="left", padx=5)
        self.run_button = ttk.Button(file_frame, text="Start Program", command=self.run_program)
        self.run_button.pack(side="left", padx=5)
        self.stop_button = ttk.Button(file_frame, text="Stop Program", command=self.stop_program)
        self.stop_button.pack_forget()
        
        status_frame = ttk.Frame(self.root)
        status_frame.pack(pady=5)
        ttk.Label(status_frame, text="Program Status:").pack(side="left", padx=5)
        self.status_icon = tk.Label(status_frame, width=2, background="grey", relief="sunken")
        self.status_icon.pack(side="left")
        ttk.Button(status_frame, text="View Logs", command=self.show_log_window).pack(side="left", padx=10)

        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(side="bottom", fill="x", padx=10, pady=5)
        ttk.Label(footer_frame, text=f"{self.version} © 2025 Madsiser", anchor="e", font=("TkDefaultFont", 8, "italic"), foreground="gray").pack(side="right")

    def get_serial_ports(self): return [p.device for p in serial.tools.list_ports.comports()]
    
    def refresh_ports(self):
        ports = self.get_serial_ports()
        self.port_combo['values'] = ports
        if ports: self.port_combo.set(ports[0])

    def _refresh_listboxes(self):
        self.keymap_listbox.delete(0, "end")
        for pin, val in self.config.get("key_mapping", {}).items():
            if isinstance(val, list):
                self.keymap_listbox.insert("end", f"Analog {pin} -> {len(val)} thresholds")
            else:
                self.keymap_listbox.insert("end", f"Digital {pin} -> {val['key']}")
        
        self.plugin_listbox.delete(0, "end")
        for i, instance_config in enumerate(self.config.get("plugins", [])):
            name = instance_config["name"]
            summary = f"({i}) {name}"
            settings = instance_config.get("settings", {})
            if "pin" in settings: summary += f" on Pin {settings['pin']}"
            self.plugin_listbox.insert("end", summary)

    def add_digital_pin(self):
        pin = simpledialog.askstring("Input", "Digital Pin Number:", parent=self.root)
        if not pin: return
        key = simpledialog.askstring("Input", f"Key for Pin {pin}:", parent=self.root)
        if not key: return
        self.config["key_mapping"][pin] = {"key": key}
        self._refresh_listboxes()

    def add_analog_pin(self):
        pin = simpledialog.askstring("Input", "Analog Pin (e.g., A0):", parent=self.root)
        if not pin: return
        initial_data = self.config["key_mapping"].get(pin, [])
        dialog = AnalogPinDialog(self.root, pin, initial_data)
        self.root.wait_window(dialog)
        if dialog.result:
            self.config["key_mapping"][pin] = dialog.result
        elif pin in self.config["key_mapping"] and not dialog.result:
            del self.config["key_mapping"][pin]
        self._refresh_listboxes()

    def remove_pin(self):
        selection = self.keymap_listbox.curselection()
        if not selection: return
        item_text = self.keymap_listbox.get(selection[0])
        pin_to_remove = item_text.split(" -> ")[0].replace("Digital ", "").replace("Analog ", "")
        if pin_to_remove in self.config["key_mapping"]:
            del self.config["key_mapping"][pin_to_remove]
        self._refresh_listboxes()

    def add_plugin(self):
        if not self.available_plugins:
            messagebox.showinfo("No Plugins", "No plugins with a 'ui.json' file found.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Plugin")
        dialog.transient(self.root); dialog.grab_set()
        ttk.Label(dialog, text="Select a plugin to add:").pack(padx=20, pady=10)
        selected_plugin_name = tk.StringVar()
        plugin_names = list(self.available_plugins.keys())
        combo = ttk.Combobox(dialog, textvariable=selected_plugin_name, values=plugin_names, state="readonly")
        combo.pack(padx=20, pady=5)
        if plugin_names: combo.current(0)
        def on_add():
            chosen_name = selected_plugin_name.get()
            dialog.destroy()
            if not chosen_name: return
            ui_path = self.available_plugins[chosen_name]
            with open(ui_path, 'r') as f: ui_definition = json.load(f)
            config_dialog = PluginConfigDialog(self.root, ui_definition)
            self.root.wait_window(config_dialog)
            if config_dialog.result is not None:
                self.config["plugins"].append({"name": chosen_name, "settings": config_dialog.result})
                self._refresh_listboxes()
        ttk.Button(dialog, text="Add", command=on_add).pack(pady=10)

    def edit_plugin(self):
        selection = self.plugin_listbox.curselection()
        if not selection: return
        index = selection[0]
        instance_config = self.config["plugins"][index]
        name = instance_config["name"]
        settings = instance_config.get("settings", {})
        ui_path = self.available_plugins.get(name)
        if not ui_path:
            messagebox.showerror("Error", f"UI definition for '{name}' not found!")
            return
        with open(ui_path, 'r') as f: ui_definition = json.load(f)
        config_dialog = PluginConfigDialog(self.root, ui_definition, initial_settings=settings)
        self.root.wait_window(config_dialog)
        if config_dialog.result is not None:
            self.config["plugins"][index]["settings"] = config_dialog.result
            self._refresh_listboxes()

    def remove_plugin(self):
        selection = self.plugin_listbox.curselection()
        if not selection: return
        if messagebox.askyesno("Confirm", "Remove this plugin instance?"):
            self.config["plugins"].pop(selection[0])
            self._refresh_listboxes()

    def save_to_file(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Config", "*.json")])
        if not filepath: return
        self.config["port"] = self.port_combo.get()
        with open(filepath, "w") as f: json.dump(self.config, f, indent=2)
        messagebox.showinfo("Success", "Configuration saved.")

    def load_from_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Config", "*.json")])
        if not filepath: return
        with open(filepath, "r") as f: self.config = json.load(f)
        self.port_combo.set(self.config.get("port", ""))
        self._refresh_listboxes()

    def run_program(self):
        self.config["port"] = self.port_combo.get()
        with open(self.config_path, "w") as f: json.dump(self.config, f, indent=2)
        with open(self.log_path, "w") as f: f.write("")
        try:
            cmd = [self.path, "--config", self.config_path, "--log", "2"]
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, creationflags=creationflags)
            self.update_status("starting")
            self.run_button.pack_forget()
            self.stop_button.pack(side="left", padx=5)
            threading.Thread(target=self.monitor_process, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start the program:\n{e}")
            self.update_status("error")

    def stop_program(self):
        if self.proc and self.proc.poll() is None:
            if sys.platform == "win32": self.proc.send_signal(signal.CTRL_BREAK_EVENT)
            else: self.proc.send_signal(signal.SIGINT)
            self.proc.wait()
        self.update_status("finished")
        if self.root.winfo_exists():
            self.stop_button.pack_forget()
            self.run_button.pack(side="left", padx=5)

    def monitor_process(self):
        try:
            for line in self.proc.stdout:
                with open(self.log_path, "a") as f: f.write(line)
                if "STARTING" in line: self.update_status("starting")
                elif "Configuration sent successfully" in line: self.update_status("running")
            self.proc.wait()
            stderr = self.proc.stderr.read()
            if self.proc.returncode != 0 and stderr:
                with open(self.log_path, "a") as f: f.write("\n[ERROR]\n" + stderr)
                self.update_status("error")
            else:
                self.update_status("finished")
        except Exception:
            self.update_status("error")
        finally:
            if self.root.winfo_exists():
                self.stop_button.pack_forget()
                self.run_button.pack(side="left", padx=5)

    def update_status(self, state):
        color_map = {"starting": "yellow", "running": "green", "error": "red", "finished": "blue"}
        self.status_icon.configure(background=color_map.get(state, "grey"))

    def show_log_window(self):
        if not os.path.exists(self.log_path): return
        log_window = tk.Toplevel(self.root)
        log_window.title("Live Log Viewer")
        txt = tk.Text(log_window, wrap="word", state="disabled")
        txt.pack(fill="both", expand=True)
        last_pos = [0]
        def follow_log():
            try:
                with open(self.log_path, "r") as f:
                    f.seek(last_pos[0])
                    if new_lines := f.readlines():
                        txt.config(state="normal")
                        txt.insert("end", "".join(new_lines))
                        txt.yview_moveto(1.0)
                        txt.config(state="disabled")
                    last_pos[0] = f.tell()
            finally:
                if log_window.winfo_exists(): log_window.after(1000, follow_log)
        follow_log()

    def on_closing(self):
        if self.proc and self.proc.poll() is None:
            if messagebox.askyesno("Exit", "The program is running. Stop it and exit?"): self.stop_program()
            else: return
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = KeymapuinoGUI(root)
    root.mainloop()