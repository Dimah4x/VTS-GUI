import tkinter as tk
from tkinter import ttk, messagebox
from node_manager import NodeManager

class App:
    def __init__(self, master, devices):
        self.master = master
        self.master.title("Main Application")
        self.node_manager = NodeManager()
        self.node_manager.load_nodes_from_chirpstack(devices)
        self.selected_node = None
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.master, text="Select Connected Device:").pack(pady=10)
        self.device_var = tk.StringVar()
        self.device_dropdown = ttk.Combobox(self.master, textvariable=self.device_var)
        self.device_dropdown['values'] = [str(node) for node in self.node_manager.get_all_nodes()]
        self.device_dropdown.pack(pady=10)

        self.device_dropdown.bind("<<ComboboxSelected>>", self.update_selected_node)

        self.select_button = ttk.Button(self.master, text="Select Device", command=self.select_device)
        self.select_button.pack(pady=10)

        # Label to display the Device EUI of the selected node
        self.eui_label = tk.Label(self.master, text="Device EUI: ")
        self.eui_label.pack(pady=10)

    def update_selected_node(self, event):
        selected_device_name = self.device_var.get()
        self.selected_node = next((node for node in self.node_manager.get_all_nodes() if str(node) == selected_device_name), None)
        if self.selected_node:
            self.eui_label.config(text=f"Device EUI: {self.selected_node.dev_eui}")
        else:
            self.eui_label.config(text="Device EUI: Not available")

    def select_device(self):
        if self.selected_node:
            print(f"Currently selected node: {self.selected_node.name} (EUI: {self.selected_node.dev_eui})")
            # Further actions with the selected node can be implemented here
        else:
            messagebox.showwarning("Selection Error", "Please select a valid device from the list.")
