import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import grpc
from chirpstack_api import api

# Configuration
server = "localhost:8080"
api_token = "YOUR_API_TOKEN_HERE"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("VTS GUI")

        # Node Selection Dropdown
        self.node_label = ttk.Label(root, text="Select Node")
        self.node_label.pack(pady=5)
        self.node_var = tk.StringVar()
        self.node_dropdown = ttk.Combobox(root, textvariable=self.node_var)
        self.node_dropdown['values'] = ('Node 1', 'Node 2', 'Node 3')
        self.node_dropdown.pack(pady=5)

        # Buttons
        self.request_status_button = ttk.Button(root, text="Request Status", command=self.request_status)
        self.request_status_button.pack(pady=5)

        self.reset_button = ttk.Button(root, text="Reset", command=self.reset)
        self.reset_button.pack(pady=5)

        self.register_node_button = ttk.Button(root, text="Register End Node", command=self.register_node)
        self.register_node_button.pack(pady=5)

        self.remove_node_button = ttk.Button(root, text="Remove Node", command=self.remove_node)
        self.remove_node_button.pack(pady=5)

        self.downlink_button = ttk.Button(root, text="Send Downlink", command=self.send_downlink)
        self.downlink_button.pack(pady=5)

        # Alerts List
        self.alerts_label = ttk.Label(root, text="Alerts")
        self.alerts_label.pack(pady=5)
        self.alerts_listbox = tk.Listbox(root)
        self.alerts_listbox.pack(pady=5)

        # App ID Entry
        self.app_id_label = ttk.Label(root, text="Select App ID")
        self.app_id_label.pack(pady=5)
        self.app_id_entry = ttk.Entry(root)
        self.app_id_entry.pack(pady=5)

        # Alerts Log Label
        self.alerts_log_label = ttk.Label(root, text="Alerts Log")
        self.alerts_log_label.pack(pady=5)

        # Active Nodes Label
        self.active_nodes_label = ttk.Label(root, text="Active Nodes/Registered Nodes On/Off List")
        self.active_nodes_label.pack(pady=5)

    def request_status(self):
        messagebox.showinfo("Request Status", "Request Status pressed")

    def reset(self):
        messagebox.showinfo("Reset", "Reset pressed")

    def register_node(self):
        messagebox.showinfo("Register End Node", "Register End Node pressed")

    def remove_node(self):
        messagebox.showinfo("Remove Node", "Remove Node pressed")

    def send_downlink(self):
        dev_eui = self.node_var.get()
        if not dev_eui:
            messagebox.showerror("Error", "Please select a node")
            return

        try:
            # Connect without using TLS.
            channel = grpc.insecure_channel(server)

            # Device-queue API client.
            client = api.DeviceServiceStub(channel)

            # Define the API key meta-data.
            auth_token = [("authorization", "Bearer %s" % api_token)]

            # Construct request.
            req = api.EnqueueDeviceQueueItemRequest()
            req.queue_item.confirmed = False
            req.queue_item.data = bytes([0x01, 0x02, 0x03])
            req.queue_item.dev_eui = dev_eui
            req.queue_item.f_port = 10

            resp = client.Enqueue(req, metadata=auth_token)

            # Print the downlink id
            messagebox.showinfo("Downlink Sent", f"Downlink ID: {resp.id}")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def async_request_alerts(self):
        messagebox.showinfo("Async Request for Alerts", "Async Request for Alerts triggered")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
