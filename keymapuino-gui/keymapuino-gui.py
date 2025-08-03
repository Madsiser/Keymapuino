import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import json
import subprocess
import threading
import os
import signal
import sys
import serial.tools.list_ports
import ctypes
import platform
import tkinter.messagebox as messagebox


class KeymapuinoGUI:
    def __init__(self, root):
        self.version = "v1.0.1"
        
        self.root = root
        self.root.title("Keymapuino")
        self.config = {"port": "/dev/ttyUSB0", "key_mapping": {}}
        self.proc = None
        
        BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
        binary_name = "keymapuino-cli.exe" if sys.platform == "win32" else "keymapuino-cli"
        self.path = os.path.join(BASE_DIR, "bin", binary_name)
        
        self.log_path = os.path.join(BASE_DIR, "temp_log.txt")
        self.config_path = os.path.join(BASE_DIR, "config.json")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_widgets()

    def create_widgets(self):
        port_frame = ttk.LabelFrame(self.root, text="Port Settings")
        port_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(port_frame, text="Port:").pack(side="left", padx=5)
        # self.port_entry = ttk.Entry(port_frame)
        # self.port_entry.insert(0, "/dev/ttyUSB0")
        # self.port_entry.pack(side="left", fill="x", expand=True)
        self.port_combo = ttk.Combobox(port_frame, values=self.get_serial_ports(), state="normal")
        self.port_combo.pack(side="left", fill="x", expand=True, padx=5)
        self.port_combo.set("/dev/ttyUSB0")
        ttk.Button(port_frame, text="Refresh", command=self.refresh_ports).pack(side="left", padx=5)


        pin_frame = ttk.LabelFrame(self.root, text="Pin Mapping")
        pin_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.pin_listbox = tk.Listbox(pin_frame, height=10)
        self.pin_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.pin_listbox.bind("<<ListboxSelect>>", self.show_pin_details)

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

        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        version_label = ttk.Label(
            footer_frame,
            text=f"{self.version}",
            anchor="e",
            font=("TkDefaultFont", 8, "italic"),
            foreground="gray"
        )
        version_label.pack(side="left")
        version_label2 = ttk.Label(
            footer_frame,
            text=f"© 2025 Madsiser",
            anchor="e",
            font=("TkDefaultFont", 8, "italic"),
            foreground="gray"
        )
        version_label2.pack(side="right")
    
    def get_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]

    def refresh_ports(self):
        ports = self.get_serial_ports()
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])


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
                self.pin_listbox.insert("end", f"Digital {pin} -> {key}")
                dialog.destroy()

        tk.Button(dialog, text="OK", command=submit).pack(pady=5)

    def add_analog_pin(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Analog Pin")

        thresholds = []

        # Pin entry row
        pin_frame = ttk.Frame(dialog)
        pin_frame.pack(pady=5, padx=10, fill="x")

        ttk.Label(pin_frame, text="Analog Pin (e.g. A0):").pack(side="left")
        pin_entry = ttk.Entry(pin_frame, width=10)
        pin_entry.pack(side="left", padx=5)

        # Thresholds group
        container = ttk.LabelFrame(dialog, text="Thresholds")
        container.pack(padx=10, pady=10, fill="both", expand=True)

        entry_area = ttk.Frame(container)
        entry_area.pack(fill="both", expand=True)

        entry_widgets = []

        def add_entry():
            frame = ttk.Frame(entry_area)
            frame.pack(pady=2, padx=5, fill="x")

            key_var = tk.StringVar()
            low_var = tk.StringVar()
            high_var = tk.StringVar()
            hold_var = tk.StringVar()

            ttk.Label(frame, text="Key:").pack(side="left")
            key = ttk.Entry(frame, width=5, textvariable=key_var)
            key.pack(side="left", padx=2)

            ttk.Label(frame, text="Low:").pack(side="left")
            low = ttk.Entry(frame, width=5, textvariable=low_var)
            low.pack(side="left", padx=2)

            ttk.Label(frame, text="High:").pack(side="left")
            high = ttk.Entry(frame, width=5, textvariable=high_var)
            high.pack(side="left", padx=2)

            ttk.Label(frame, text="Hold(ms):").pack(side="left")
            hold = ttk.Entry(frame, width=6, textvariable=hold_var)
            hold.pack(side="left", padx=2)

            def delete_entry():
                entry_widgets.remove((key_var, low_var, high_var, hold_var, frame))
                frame.destroy()

            ttk.Button(frame, text="Delete", command=delete_entry).pack(side="right", padx=5)

            entry_widgets.append((key_var, low_var, high_var, hold_var, frame))

        # Add threshold button
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=10)

        ttk.Button(btn_frame, text="Add Threshold", command=add_entry).pack(side="right", pady=5)

        # Submit button
        def submit():
            pin = pin_entry.get().strip()
            if not pin:
                messagebox.showerror("Input Error", "Please enter the analog pin number.")
                return

            thresholds.clear()
            for key_var, low_var, high_var, hold_var, _ in entry_widgets:
                try:
                    k = key_var.get().strip()
                    l = int(low_var.get())
                    h = int(high_var.get())
                    t = int(hold_var.get())
                    if k and 0 <= l <= 1023 and 0 <= h <= 1023 and l <= h:
                        thresholds.append({"key": k, "threshold": [l, h], "hold_time_ms": t})
                except ValueError:
                    continue

            if thresholds:
                self.config["key_mapping"][pin] = thresholds
                self.pin_listbox.insert("end", f"Analog {pin} -> {len(thresholds)} thresholds")
            dialog.destroy()

        bottom_frame = ttk.Frame(dialog)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(bottom_frame, text="OK", command=submit).pack(side="right")



    def show_pin_details(self, event):
        selection = self.pin_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        pin = list(self.config["key_mapping"].keys())[index]
        value = self.config["key_mapping"][pin]

        detail_win = tk.Toplevel(self.root)
        detail_win.title(f"Pin {pin} Details")
        txt = tk.Text(detail_win, wrap="word")
        txt.pack(fill="both", expand=True)
        if isinstance(value, list):
            for item in value:
                txt.insert("end", f"Key: {item['key']}, Threshold: {item['threshold']}, Hold Time: {item['hold_time_ms']} ms\n")
        else:
            txt.insert("end", f"Key: {value['key']}\n")
        txt.config(state="disabled")

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
            # self.config["port"] = self.port_entry.get()
            self.config["port"] = self.port_combo.get()
            with open(filepath, "w") as f:
                json.dump(self.config, f, indent=2)

    def load_from_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Config files", "*.conf")])
        if filepath:
            with open(filepath, "r") as f:
                self.config = json.load(f)
            # self.port_entry.delete(0, "end")
            # self.port_entry.insert(0, self.config.get("port", ""))
            self.port_combo.set(self.config.get("port", ""))
            self.pin_listbox.delete(0, "end")
            for pin, val in self.config.get("key_mapping", {}).items():
                if isinstance(val, list):
                    self.pin_listbox.insert("end", f"Analog {pin} -> {len(val)} thresholds")
                else:
                    self.pin_listbox.insert("end", f"Digital {pin} -> {val['key']}")

    def run_program(self):
        # self.config["port"] = self.port_entry.get()
        self.config["port"] = self.port_combo.get()
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

        with open(self.log_path, "w") as f:
            f.write("")

        try:
            cmd = [self.path, "--config", self.config_path, "--log", "2"]

            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=creationflags
            )

            self.update_status("starting")
            self.run_button.pack_forget()
            self.stop_button.pack(side="left", padx=5)
            threading.Thread(target=self.monitor_process, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start the program:\n{e}")
            self.update_status("error")

    def stop_program(self):
        if self.proc and self.proc.poll() is None:
            if sys.platform == "win32":
                self.proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
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

        log_window = tk.Toplevel(self.root)
        log_window.title("Live Log Viewer")
        log_window.geometry("700x400")

        txt = tk.Text(log_window, wrap="word", state="disabled")
        txt.pack(fill="both", expand=True)

        last_pos = [0]

        def follow_log():
            try:
                with open(self.log_path, "r") as f:
                    f.seek(last_pos[0])
                    new_lines = f.readlines()
                    last_pos[0] = f.tell()

                    if new_lines:
                        txt.config(state="normal")
                        for line in new_lines:
                            txt.insert("end", line)
                        txt.yview_moveto(1.0)
                        txt.config(state="disabled")
            except Exception as e:
                print(f"Log read error: {e}")

            # Repeat after 1s
            if log_window.winfo_exists():
                log_window.after(1000, follow_log)

        follow_log()

    
    def on_closing(self):
        if self.proc and self.proc.poll() is None:
            if messagebox.askyesno("Exit", "The program is still running.\nDo you want to stop it and exit the application?"):
                self.stop_program()
            else:
                return
        self.root.destroy()

def is_admin():
    if os.name == 'nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0


if __name__ == "__main__":
    if not is_admin():
        if os.name == 'nt':
            # Windows: re-run with elevated privileges
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f'"{script}" {params}', None, 1
                )
            except Exception as e:
                messagebox.showerror("Administrator Required", f"Failed to request administrator privileges.\n\n{e}")
            sys.exit()
        else:
            # Unix/Linux/macOS: show error
            # messagebox.showerror(
            #     "Administrator Required",
            #     "This application must be run with root privileges."
            # )
            # sys.exit()
            pass

    root = tk.Tk()
    app = KeymapuinoGUI(root)
    root.mainloop()

