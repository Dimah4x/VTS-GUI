import tkinter as tk
from tkinter import ttk, messagebox
from node_manager import NodeManager
from chirpstack_client import ChirpStackClient
from end_node import EndNode  # Importing EndNode class
import grpc  # Import grpc for handling exceptions
import threading
from command_dict import COMMANDS
import paho.mqtt.client as mqtt
import json



class App:
    def __init__(self, master, devices, chirpstack_client, app_id, tenant_id):
        self.master = master
        self.master.title("Main Application")
        self.node_manager = NodeManager()
        self.node_manager.load_nodes_from_chirpstack(devices)
        self.selected_node = None
        self.chirpstack_client = chirpstack_client
        self.app_id = app_id  # Store App ID from configuration
        self.tenant_id = tenant_id  # Store Tenant ID from configuration
        self.device_profiles = self.fetch_device_profiles()
        # self.start_periodic_refresh(interval_ms=60000)  # Refresh every 60 seconds
        self.create_widgets()
        # Set up MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect("192.168.1.131", 1883, 60)
        self.mqtt_client.loop_start()

    def fetch_device_profiles(self):
        try:
            profiles = self.chirpstack_client.get_device_profiles(self.tenant_id)
            return [(profile.id, profile.name) for profile in profiles]
        except grpc.RpcError as e:
            messagebox.showerror("Error", f"Failed to fetch device profiles: {e.details()}")
            return []

    def create_widgets(self):
        tk.Label(self.master, text="Select Connected Device:").pack(pady=10)
        self.device_var = tk.StringVar()
        self.device_dropdown = ttk.Combobox(self.master, textvariable=self.device_var)
        self.device_dropdown['values'] = [str(node) for node in self.node_manager.get_all_nodes()]
        self.device_dropdown.pack(pady=10)

        self.device_dropdown.bind("<<ComboboxSelected>>", self.update_selected_node)
        # self.device_dropdown.bind("<<ComboboxSelected>>", lambda event: self.update_selected_node(event))
        # self.select_button = ttk.Button(self.master, text="Select Device", command=self.select_device)
        # self.select_button.pack(pady=10)  # Added update_selected_node method to combobox binding, seems redundant

        # self.refresh_button = ttk.Button(self.master, text="Refresh Status", command=self.update_device_status)
        # self.refresh_button.pack(pady=10)

        self.remove_button = ttk.Button(self.master, text="Remove Node", command=self.remove_selected_node)
        self.remove_button.pack(pady=10)

        self.add_button = ttk.Button(self.master, text="Add Node", command=self.open_add_node_dialog)
        self.add_button.pack(pady=10)

        self.eui_label = tk.Label(self.master, text="Device EUI: ")
        self.eui_label.pack(pady=10)

        self.status_request_button = ttk.Button(self.master, text="Status Request", command=self.send_status_request)
        self.status_request_button.pack(pady=10)
        self.reset_request_button = ttk.Button(self.master, text="Reset Request", command=self.send_reset_request)
        self.reset_request_button.pack(pady=10)
        self.data_collection_button = ttk.Button(self.master, text="Data Collection Trigger",
                                                 command=self.send_data_collection_request)
        self.data_collection_button.pack(pady=10)

        # Disable buttons initially
        self.status_request_button.config(state=tk.DISABLED)
        self.reset_request_button.config(state=tk.DISABLED)
        self.data_collection_button.config(state=tk.DISABLED)

        self.device_status_panel = tk.Frame(self.master)
        self.device_status_panel.pack(fill='both', expand=True)

        self.device_list = tk.Listbox(self.device_status_panel)
        self.device_list.pack(fill='both', expand=True)

    def enable_command_buttons(self):
        self.status_request_button.config(state=tk.NORMAL)
        self.reset_request_button.config(state=tk.NORMAL)
        self.data_collection_button.config(state=tk.NORMAL)

    def disable_command_buttons(self):
        self.status_request_button.config(state=tk.DISABLED)
        self.reset_request_button.config(state=tk.DISABLED)
        self.data_collection_button.config(state=tk.DISABLED)

    def update_selected_node(self, event):
        selected_device_name = self.device_var.get()
        self.selected_node = next(
            (node for node in self.node_manager.get_all_nodes() if str(node) == selected_device_name), None)
        if self.selected_node:
            self.eui_label.config(text=f"Device EUI: {self.selected_node.dev_eui}")
            # self.update_device_status()  # Automatically refresh status when a device is selected
            self.enable_command_buttons()
        else:
            self.eui_label.config(text="Device EUI: Not available")
            self.disable_command_buttons()  # Disable command buttons if no valid selection

    def select_device(self):
        if self.selected_node:
            print(f"Currently selected node: {self.selected_node.name} (EUI: {self.selected_node.dev_eui})")
        else:
            messagebox.showwarning("Selection Error", "Please select a valid device from the list.")

    def remove_selected_node(self):
        if self.selected_node:
            confirm = messagebox.askyesno("Confirm Removal",
                                          f"Are you sure you want to remove the node {self.selected_node.name}?")
            if confirm:
                try:
                    self.chirpstack_client.remove_device(self.selected_node.dev_eui)
                    self.node_manager.remove_node(self.selected_node.dev_eui)
                    self.device_dropdown['values'] = [str(node) for node in self.node_manager.get_all_nodes()]
                    self.selected_node = None
                    self.device_var.set('')
                    self.eui_label.config(text="Device EUI: Not available")
                    messagebox.showinfo("Node Removed", "The node has been removed successfully.")
                except grpc.RpcError as e:
                    error_details = e.details() if e.details() else "Unknown error"
                    messagebox.showerror("Removal Error", f"Failed to remove node from server: {error_details}")
        else:
            messagebox.showwarning("Removal Error", "Please select a valid device to remove.")

    def open_add_node_dialog(self):
        self.add_node_window = tk.Toplevel(self.master)
        self.add_node_window.title("Add Node")

        tk.Label(self.add_node_window, text="Device EUI:").grid(row=0, column=0, pady=5, padx=5)
        self.dev_eui_entry = tk.Entry(self.add_node_window)
        self.dev_eui_entry.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(self.add_node_window, text="Name:").grid(row=1, column=0, pady=5, padx=5)
        self.name_entry = tk.Entry(self.add_node_window)
        self.name_entry.grid(row=1, column=1, pady=5, padx=5)

        tk.Label(self.add_node_window, text="Description (Optional):").grid(row=2, column=0, pady=5, padx=5)
        self.description_entry = tk.Entry(self.add_node_window)
        self.description_entry.grid(row=2, column=1, pady=5, padx=5)

        tk.Label(self.add_node_window, text="Device Profile:").grid(row=3, column=0, pady=5, padx=5)
        self.device_profile_var = tk.StringVar()
        self.device_profile_dropdown = ttk.Combobox(self.add_node_window, textvariable=self.device_profile_var)
        self.device_profile_dropdown['values'] = [name for _, name in self.device_profiles]
        self.device_profile_dropdown.grid(row=3, column=1, pady=5, padx=5)

        tk.Label(self.add_node_window, text="NwkKey:").grid(row=4, column=0, pady=5, padx=5)
        self.nwk_key_entry = tk.Entry(self.add_node_window)
        self.nwk_key_entry.grid(row=4, column=1, pady=5, padx=5)

        ttk.Button(self.add_node_window, text="Add Node", command=self.add_node).grid(row=5, column=0, columnspan=2,
                                                                                      pady=10)

    def add_node(self):
        dev_eui = self.dev_eui_entry.get()
        name = self.name_entry.get()
        description = self.description_entry.get()
        selected_profile_name = self.device_profile_var.get()
        device_profile_id = next((id for id, name in self.device_profiles if name == selected_profile_name), None)
        nwk_key = self.nwk_key_entry.get()

        if not dev_eui or not name or not device_profile_id or not nwk_key:
            messagebox.showerror("Error", "Device EUI, Name, Device Profile ID, and NwkKey are required.")
            return

        try:
            self.chirpstack_client.add_device(dev_eui, name, device_profile_id, self.app_id, nwk_key, description)
            messagebox.showinfo("Success", "Node added successfully!")
            self.node_manager.add_node(EndNode(dev_eui, name))
            self.device_dropdown['values'] = [str(node) for node in self.node_manager.get_all_nodes()]
            self.add_node_window.destroy()
        except grpc.RpcError as e:
            error_details = e.details() if e.details() else "Unknown error"
            messagebox.showerror("Error", f"Failed to add node: {error_details}")

    # def display_device_status(self, device):
    #     self.device_list.delete(0, tk.END)
    #     status_info = self.chirpstack_client.get_device_status(device.dev_eui)
    #     is_online = status_info.get('is_online', False)
    #     last_seen = status_info.get('last_seen', 'Unknown')
    #
    #     print(f"Device {device.dev_eui} status info: {status_info}")
    #
    #     metrics = {}
    #     if is_online:
    #         metrics_resp = self.chirpstack_client.get_device_link_metrics(device.dev_eui)
    #         print(f"Device {device.dev_eui} metrics: {metrics_resp}")
    #         if metrics_resp:
    #             metrics['rssi'] = metrics_resp.get('gw_rssi', 'N/A')
    #             metrics['snr'] = metrics_resp.get('gw_snr', 'N/A')
    #             metrics['errors'] = metrics_resp.get('errors', 'N/A')
    #             metrics['rx_packets'] = metrics_resp.get('rx_packets', 'N/A')
    #
    #     status = f"{device.name}: {'Online' if is_online else 'Offline'}, Last seen: {last_seen}"
    #     if is_online:
    #         status += f", RSSI: {metrics.get('rssi', 'N/A')}, SNR: {metrics.get('snr', 'N/A')}"
    #     print(f"Displaying status: {status}")
    #     self.device_list.insert(tk.END, status)
    #
    # def alert_user(self, message):
    #     messagebox.showwarning("Alert", message)
    #
    # def update_device_status(self):
    #     if not self.selected_node:
    #         return  # Do not proceed if no device is selected
    #
    #     def fetch_and_update():
    #         try:
    #             device = self.selected_node
    #             self.display_device_status(device)
    #         except grpc.RpcError as e:
    #             self.alert_user(f"Failed to update device status: {e.details()}")
    #
    #     threading.Thread(target=fetch_and_update).start()

    # def start_periodic_refresh(self, interval_ms=60000):
    #     """Starts periodic refresh of device status every `interval_ms` milliseconds."""
    #
    #     def refresh():
    #         if self.selected_node:
    #             self.update_device_status()
    #         self.master.after(interval_ms, refresh)
    #
    #     # Start the refresh loop
    #     refresh()

    def send_status_request(self):
        if not self.selected_node:
            messagebox.showwarning("No Device Selected", "Please select a device first.")
            return
        data = COMMANDS["STATUS_REQUEST"]  # Status Request
        success, message = self.chirpstack_client.enqueue_downlink(self.selected_node.dev_eui, data)
        messagebox.showinfo("Downlink Status", message)

    def send_reset_request(self):
        if not self.selected_node:
            messagebox.showwarning("No Device Selected", "Please select a device first.")
            return
        data = COMMANDS["RESET_REQUEST"]  # Reset Request
        success, message = self.chirpstack_client.enqueue_downlink(self.selected_node.dev_eui, data)
        messagebox.showinfo("Downlink Status", message)

    def send_data_collection_request(self):
        if not self.selected_node:
            messagebox.showwarning("No Device Selected", "Please select a device first.")
            return
        data = COMMANDS["DATA_COLLECTION_REQUEST"]  # Data Collection Trigger (LIDAR Reading)
        success, message = self.chirpstack_client.enqueue_downlink(self.selected_node.dev_eui, data)
        messagebox.showinfo("Downlink Status", message)

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        # Subscribe to the relevant topics
        client.subscribe("application/+/device/+/event/up")
        client.subscribe("application/+/device/+/event/join")
        client.subscribe("application/+/device/+/event/status")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        event_type = topic.split('/')[-1]

        if event_type == "up":
            self.handle_uplink(data)
        elif event_type == "join":
            self.handle_join(data)
        elif event_type == "status":
            self.handle_status(data)

    def handle_uplink(self, data):
        device_name = data['deviceInfo'].get('deviceName', 'Unknown device')
        event_time = data.get('time', 'Unknown time')
        message = data.get('object', {}).get('message', 'No message')
        rssi = data['rxInfo'][0]['rssi'] if 'rxInfo' in data and len(data['rxInfo']) > 0 else 'N/A'
        snr = data['rxInfo'][0]['snr'] if 'rxInfo' in data and len(data['rxInfo']) > 0 else 'N/A'

        event_info = f"Uplink - Device: {device_name}, Time: {event_time}, RSSI: {rssi}, SNR: {snr}, Message: {message}"
        self.master.after(0, lambda: self.add_event_to_listbox(event_info))

    def handle_join(self, data):
        device_name = data['deviceInfo'].get('deviceName', 'Unknown device')
        dev_eui = data['deviceInfo'].get('devEui', 'Unknown DevEUI')

        event_info = f"Join - Device: {device_name}, DevEUI: {dev_eui}"
        self.master.after(0, lambda: self.add_event_to_listbox(event_info))

    def handle_status(self, data):
        device_name = data['deviceInfo'].get('deviceName', 'Unknown device')
        margin = data.get('margin', 'N/A')
        battery = data.get('batteryLevel', 'N/A')
        external_power = data.get('externalPowerSource', False)
        last_seen = data.get('lastSeenAt', 'N/A')

        event_info = f"Status - Device: {device_name}, Margin: {margin}, Battery: {battery}, External Power: {external_power}, Last Seen: {last_seen}"
        self.master.after(0, lambda: self.add_event_to_listbox(event_info))

    def add_event_to_listbox(self, event_info):
        self.device_list.insert(tk.END, event_info)

    def show_alert(self, title, message):
        self.master.after(0, lambda: messagebox.showwarning(title, message))
