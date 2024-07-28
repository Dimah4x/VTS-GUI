import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import grpc
from chirpstack_client import ChirpStackClient

CONFIG_FILE = 'config.json'


class ConfigDialog:
    def __init__(self, master):
        self.master = master
        self.master.title("Initial Configuration")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.server_address = tk.StringVar()
        self.server_port = tk.StringVar()
        self.api_token = tk.StringVar()
        self.app_id = tk.StringVar()
        self.tenant_id = tk.StringVar()
        self.config_complete = False
        self.devices = []

        self.load_configuration()
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.master, text="ChirpStack Server Address:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        ttk.Entry(self.master, textvariable=self.server_address).grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(self.master, text="Server Port:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        ttk.Entry(self.master, textvariable=self.server_port).grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(self.master, text="API Token:").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        ttk.Entry(self.master, textvariable=self.api_token, show="*").grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(self.master, text="App ID:").grid(row=3, column=0, padx=10, pady=5, sticky='w')
        ttk.Entry(self.master, textvariable=self.app_id).grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(self.master, text="Tenant ID (Optional):").grid(row=4, column=0, padx=10, pady=5, sticky='w')
        ttk.Entry(self.master, textvariable=self.tenant_id).grid(row=4, column=1, padx=10, pady=5)

        ttk.Button(self.master, text="Connect", command=self.connect).grid(row=5, column=0, columnspan=2, pady=10)

    def load_configuration(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                config = json.load(file)
                self.server_address.set(config.get('server_address', ''))
                self.server_port.set(config.get('server_port', ''))
                self.api_token.set(config.get('api_token', ''))
                self.app_id.set(config.get('app_id', ''))
                self.tenant_id.set(config.get('tenant_id', ''))

    def connect(self):
        if not self.server_address.get() or not self.server_port.get() or not self.api_token.get() or not self.app_id.get():
            messagebox.showerror("Error", "Please fill in all required fields.")
            return

        try:
            port = int(self.server_port.get())
            if not (0 <= port <= 65535):
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid port number (0-65535).")
            return

        self.sync_devices()

    def sync_devices(self):
        client = ChirpStackClient(f"{self.server_address.get()}:{self.server_port.get()}", self.api_token.get())
        try:
            devices = client.list_devices(self.app_id.get())
            self.devices = devices
            messagebox.showinfo("Success", f"Successfully synchronized {len(devices)} devices.")
            self.config_complete = True
            self.save_configuration()
            self.master.destroy()
        except grpc.RpcError as e:
            messagebox.showerror("Synchronization Error", f"Failed to sync devices: {e.details()}")

    def save_configuration(self):
        config = {
            'server_address': self.server_address.get(),
            'server_port': self.server_port.get(),
            'api_token': self.api_token.get(),
            'app_id': self.app_id.get(),
            'tenant_id': self.tenant_id.get(),
        }
        with open(CONFIG_FILE, 'w') as file:
            json.dump(config, file)

    def on_close(self):
        if not self.config_complete:
            if messagebox.askokcancel("Quit", "Do you want to quit without saving the configuration?"):
                self.master.destroy()
                self.master.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigDialog(master=root)
    root.mainloop()
