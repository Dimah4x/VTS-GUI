import tkinter as tk
from tkinter import ttk

class App:
    def __init__(self, master, devices):
        self.master = master
        self.master.title("Main Application")
        self.devices = devices
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.master, text="Select Connected Device:").pack(pady=10)

        # Dropdown list for devices
        self.device_var = tk.StringVar()
        self.device_dropdown = ttk.Combobox(self.master, textvariable=self.device_var)
        self.device_dropdown['values'] = [device.name for device in self.devices]  # Assuming each device has a 'name' attribute
        self.device_dropdown.pack(pady=10)

        # Button to perform an action with the selected device
        self.select_button = ttk.Button(self.master, text="Select Device", command=self.select_device)
        self.select_button.pack(pady=10)

    def select_device(self):
        selected_device = self.device_var.get()
        if selected_device:
            print(f"Selected Device: {selected_device}")
            # Further actions can be implemented here based on the selected device
        else:
            tk.messagebox.showwarning("Selection Error", "Please select a device from the list.")
