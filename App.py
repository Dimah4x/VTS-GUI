import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from end_node import EndNode
from node_manager import NodeManager
from chirpstack_client import ChirpStackClient


server = "192.168.0.1:8080"
api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjaGlycHN0YWNrIiwiaXNzIjoiY2hpcnBzdGFjayIsInN1YiI6ImFiNjA3ZTE3LTQyMGUtNDkxNy1hZjE1LTFjMGJiZTM0ZDk3NiIsInR5cCI6ImtleSJ9.n3Ac1S-1zMLpjjbhtnbSQuHjTcKD3EIHmevJXMb4hmQ"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("VTS GUI")

        self.node_manager = NodeManager()
        self.chirpstack_client = ChirpStackClient(server=server, api_token=api_token)

        self.setup_gui()
        self.load_nodes()

    def setup_gui(self):
        self.node_label = ttk.Label(self.root, text="Select Node")
        self.node_label.pack(pady=5)
        self.node_var = tk.StringVar()
        self.node_dropdown = ttk.Combobox(self.root, textvariable=self.node_var)
        self.node_dropdown.pack(pady=5)

        self.request_status_button = ttk.Button(self.root, text="Request Status", command=self.request_status)
        self.request_status_button.pack(pady=5)

        self.reset_button = ttk.Button(self.root, text="Reset", command=self.reset)
        self.reset_button.pack(pady=5)

        self.register_node_button = ttk.Button(self.root, text="Register End Node",
                                               command=self.open_register_node_window)
        self.register_node_button.pack(pady=5)

        self.remove_node_button = ttk.Button(self.root, text="Remove Node", command=self.remove_node)
        self.remove_node_button.pack(pady=5)

        self.list_nodes_button = ttk.Button(self.root, text="List Paired Nodes", command=self.list_paired_nodes)
        self.list_nodes_button.pack(pady=5)

        self.downlink_button = ttk.Button(self.root, text="Send Downlink", command=self.send_downlink)
        self.downlink_button.pack(pady=5)

        self.alerts_label = ttk.Label(self.root, text="Alerts")
        self.alerts_label.pack(pady=5)
        self.alerts_listbox = tk.Listbox(self.root)
        self.alerts_listbox.pack(pady=5)

        self.app_id_label = ttk.Label(self.root, text="Select App ID")
        self.app_id_label.pack(pady=5)
        self.app_id_entry = ttk.Entry(self.root)
        self.app_id_entry.pack(pady=5)

        self.alerts_log_label = ttk.Label(self.root, text="Alerts Log")
        self.alerts_log_label.pack(pady=5)

        self.active_nodes_label = ttk.Label(self.root, text="Active Nodes/Registered Nodes On/Off List")
        self.active_nodes_label.pack(pady=5)

    def load_nodes(self):
        self.node_dropdown['values'] = [str(node) for node in self.node_manager.nodes]

    def request_status(self):
        messagebox.showinfo("Request Status", "Request Status pressed")

    def reset(self):
        messagebox.showinfo("Reset", "Reset pressed")

    def open_register_node_window(self):
        register_window = Toplevel(self.root)
        register_window.title("Register End Node")

        ttk.Label(register_window, text="Device EUI").pack(pady=5)
        dev_eui_entry = ttk.Entry(register_window)
        dev_eui_entry.pack(pady=5)

        ttk.Label(register_window, text="App ID").pack(pady=5)
        app_id_entry = ttk.Entry(register_window)
        app_id_entry.pack(pady=5)

        ttk.Label(register_window, text="Node Name").pack(pady=5)
        node_name_entry = ttk.Entry(register_window)
        node_name_entry.pack(pady=5)

        def register_node():
            dev_eui = dev_eui_entry.get()
            app_id = app_id_entry.get()
            node_name = node_name_entry.get()

            if not dev_eui or not app_id or not node_name:
                messagebox.showerror("Error", "All fields are required")
                return

            tenant_id = "your-tenant-id"

            try:
                device_profile_id = self.chirpstack_client.create_device_profile(tenant_id, node_name)
                application_id = self.chirpstack_client.create_application(tenant_id, app_id)
                self.chirpstack_client.create_device(application_id, device_profile_id, dev_eui, node_name)

                new_node = EndNode(dev_eui, app_id, node_name)
                self.node_manager.add_node(new_node)
                self.load_nodes()
                messagebox.showinfo("Register End Node", "End Node registered")
                register_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        register_button = ttk.Button(register_window, text="Register", command=register_node)
        register_button.pack(pady=20)

    def remove_node(self):
        dev_eui = self.node_var.get()
        if not dev_eui:
            messagebox.showerror("Error", "Please select a node")
            return

        self.chirpstack_client.delete_device(dev_eui)
        self.node_manager.remove_node(dev_eui)
        self.load_nodes()
        messagebox.showinfo("Remove Node", "End Node removed")

    def list_paired_nodes(self):
        try:
            application_id = self.app_id_entry.get()
            if not application_id:
                messagebox.showerror("Error", "Please enter App ID")
                return
            devices = self.chirpstack_client.list_devices(application_id)
            paired_nodes = "\n".join([device.name for device in devices])
            messagebox.showinfo("Paired Nodes", paired_nodes if paired_nodes else "No paired nodes found")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def send_downlink(self):
        dev_eui = self.node_var.get()
        if not dev_eui:
            messagebox.showerror("Error", "Please select a node")
            return
        try:
            downlink_id = self.chirpstack_client.send_downlink(dev_eui, bytes([0x01, 0x02, 0x03]), 10)
            messagebox.showinfo("Downlink Sent", f"Downlink ID: {downlink_id}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def async_request_alerts(self):
        messagebox.showinfo("Async Request for Alerts", "Async Request for Alerts triggered")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
