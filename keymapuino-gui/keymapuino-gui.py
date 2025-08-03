import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import json
import subprocess
import threading
import os
import signal

class ConfigGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Keymapuino")
        self.config = {"port": "/dev/ttyUSB0", "key_mapping": {}}
        self.proc = None
        self.log_path = "temp_log.txt"

        self.create_widgets()

    def create_widgets(self):
        port_frame = ttk.LabelFrame(self.root, text="Port Settings")
        port_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(port_frame, text="Port:").pack(side="left", padx=5)
        self.port_entry = ttk.Entry(port_frame)
        self.port_entry.insert(0, "/dev/ttyUSB0")
        self.port_entry.pack(side="left", fill="x", expand=True)

        pin_frame = ttk.LabelFrame(self.root, text="Pin Mapping")
        pin_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.pin_listbox = tk.Listbox(pin_frame, height=10)
        self.pin_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(pin_frame)
        btn_frame.pack(side="right", fill="y")

        ttk.Button(btn_frame, text="Add Digital Pin", command=self.add_digital_pin).pack(pady=2)
        ttk.Button(btn_frame, text="Add Analog Pin", command=self.add_analog_pin).pack(pady=2)
        ttk.Button(btn_frame, text="Remove Pin", command=self.remove_pin).pack(pady=2)

        file_frame = ttk.Frame(self.root)
        file_frame.pack(pady=5)

        ttk.Button(file_frame, text="Save to .conf File", command=self.save_to_file).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Load .conf File", command=self.load_from_file).pack(side="left", padx=5)
        self.run_button = ttk.Button(file_frame, text="Start Program", command=self.run_program)
        self.run_button.pack(side="left", padx=5)
        self.stop_button = ttk.Button(file_frame, text="Stop Program", command=self.stop_program)
        self.stop_button.pack(side="left", padx=5)
        self.stop_button.pack_forget()

        status_frame = ttk.Frame(self.root)
        status_frame.pack(pady=5)

        ttk.Label(status_frame, text="Program Status:").pack(side="left", padx=5)
        self.status_icon = tk.Label(status_frame, width=2, background="grey", relief="sunken")
        self.status_icon.pack(side="left")

        ttk.Button(status_frame, text="View Logs", command=self.show_log_window).pack(side="left", padx=10)

    def add_digital_pin(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Digital Pin")

        tk.Label(dialog, text="Digital Pin Number:").pack()
        pin_entry = tk.Entry(dialog)
        pin_entry.pack()

        tk.Label(dialog, text="Assigned Key:").pack()
        key_entry = tk.Entry(dialog)
        key_entry.pack()

        def submit():
            pin = pin_entry.get()
            key = key_entry.get()
            if pin and key:
                self.config["key_mapping"][pin] = {"key": key}
                self.pin_listbox.insert("end", f"Digital {pin} → {key}")
                dialog.destroy()

        tk.Button(dialog, text="OK", command=submit).pack(pady=5)

    def add_analog_pin(self):
        pin = simpledialog.askstring("Add Analog Pin", "Analog Pin Number (e.g. A0):")
        if not pin:
            return

        thresholds = []
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Thresholds for {pin}")

        entries = []
        def add_entry():
            frame = ttk.Frame(dialog)
            frame.pack(padx=5, pady=2)
            key = ttk.Entry(frame, width=5)
            low = ttk.Entry(frame, width=5)
            high = ttk.Entry(frame, width=5)
            hold = ttk.Entry(frame, width=5)
            key.pack(side="left", padx=2)
            low.pack(side="left", padx=2)
            high.pack(side="left", padx=2)
            hold.pack(side="left", padx=2)
            entries.append((key, low, high, hold))

        for _ in range(2):
            add_entry()

        ttk.Button(dialog, text="Add Another Threshold", command=add_entry).pack(pady=5)

        def submit():
            for key, low, high, hold in entries:
                try:
                    k = key.get()
                    l = int(low.get())
                    h = int(high.get())
                    t = int(hold.get())
                    if 0 <= l <= 1023 and 0 <= h <= 1023 and l <= h:
                        thresholds.append({"key": k, "threshold": [l, h], "hold_time_ms": t})
                except:
                    continue
            if thresholds:
                self.config["key_mapping"][pin] = thresholds
                self.pin_listbox.insert("end", f"Analog {pin} → {len(thresholds)} thresholds")
            dialog.destroy()

        ttk.Button(dialog, text="OK", command=submit).pack(pady=5)

    def remove_pin(self):
        selected = self.pin_listbox.curselection()
        if not selected:
            return
        index = selected[0]
        pin = list(self.config["key_mapping"].keys())[index]
        del self.config["key_mapping"][pin]
        self.pin_listbox.delete(index)

    def save_to_file(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".conf", filetypes=[("Config files", "*.conf")])
        if filepath:
            self.config["port"] = self.port_entry.get()
            with open(filepath, "w") as f:
                json.dump(self.config, f, indent=2)

    def load_from_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Config files", "*.conf")])
        if filepath:
            with open(filepath, "r") as f:
                self.config = json.load(f)
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, self.config.get("port", ""))
            self.pin_listbox.delete(0, "end")
            for pin, val in self.config.get("key_mapping", {}).items():
                if isinstance(val, list):
                    self.pin_listbox.insert("end", f"Analog {pin} → {len(val)} thresholds")
                else:
                    self.pin_listbox.insert("end", f"Digital {pin} → {val['key']}")

    def run_program(self):
        self.config["port"] = self.port_entry.get()
        config_path = "temp_config.json"
        with open(config_path, "w") as f:
            json.dump(self.config, f, indent=2)

        with open(self.log_path, "w") as f:
            f.write("")

        try:
            cmd = ["bin/keymapuino-cli.exe", "--config", config_path, "--log", "2"]
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            self.update_status("starting")
            self.run_button.pack_forget()
            self.stop_button.pack(side="left", padx=5)
            threading.Thread(target=self.monitor_process, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start the program:\n{e}")
            self.update_status("error")

    def stop_program(self):
        if self.proc and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGINT)
            self.proc.wait()
        self.update_status("finished")
        self.stop_button.pack_forget()
        self.run_button.pack(side="left", padx=5)

    def monitor_process(self):
        try:
            for line in self.proc.stdout:
                with open(self.log_path, "a") as f:
                    f.write(line)
                if "STARTING" in line:
                    self.update_status("starting")
                elif "RUN" in line:
                    self.update_status("running")

            self.proc.wait()
            if self.proc.returncode == 0:
                self.update_status("finished")
            else:
                stderr = self.proc.stderr.read()
                if stderr:
                    with open(self.log_path, "a") as f:
                        f.write("\n[ERROR]\n" + stderr)
                    self.update_status("error")
                else:
                    self.update_status("error")
        except Exception:
            self.update_status("error")
        finally:
            self.stop_button.pack_forget()
            self.run_button.pack(side="left", padx=5)

    def update_status(self, state):
        color_map = {
            "starting": "yellow",
            "running": "green",
            "error": "red",
            "finished": "blue"
        }
        color = color_map.get(state, "grey")
        self.status_icon.configure(background=color)

    def show_log_window(self):
        if not os.path.exists(self.log_path):
            messagebox.showerror("Error", "Log file not found.")
            return
        win = tk.Toplevel(self.root)
        win.title("Program Logs")
        win.geometry("700x400")
        txt = tk.Text(win, wrap="word", state="normal")
        txt.pack(fill="both", expand=True)
        with open(self.log_path, "r") as f:
            txt.insert("1.0", f.read())
        txt.configure(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigGeneratorApp(root)
    root.mainloop()
