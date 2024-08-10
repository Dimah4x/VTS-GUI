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
from datetime import datetime

DEVICE_TYPES = [
    "LiDAR unit",
    "LiDAR Simulated Unit",
    "Sound Unit",
    "Wearable Alert Unit",
    "Blank Unit"
]

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
        self.start_periodic_refresh()  # Refresh every 30 seconds
        self.create_widgets()
        # Set up MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect("192.168.1.131", 1883, 60)
        self.mqtt_client.loop_start()
        self.log_file = "events_log.txt"
        self.start_logging()

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def fetch_device_profiles(self):
        try:
            profiles = self.chirpstack_client.get_device_profiles(self.tenant_id)
            return [(profile.id, profile.name) for profile in profiles]
        except grpc.RpcError as e:
            messagebox.showerror("Error", f"Failed to fetch device profiles: {e.details()}")
            return []

    def start_periodic_refresh(self, interval_ms=10000):
        """Starts periodic refresh of device data every `interval_ms` milliseconds."""
        self.refresh_timer = self.master.after(interval_ms, self.refresh_device_status)

    def refresh_device_status(self):
        if self.selected_node:
            self.update_selected_node(self)
        self.start_periodic_refresh()  # Restart the timer after refreshing

    def create_widgets(self):
        # Layout Configuration
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_rowconfigure(2, weight=3)
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_columnconfigure(2, weight=1)

        # Widgets Configuration
        tk.Label(self.master, text="Select Node").grid(row=0, column=0, pady=10)
        self.device_var = tk.StringVar()
        self.device_dropdown = ttk.Combobox(self.master, textvariable=self.device_var)
        self.device_dropdown['values'] = [str(node) for node in self.node_manager.get_all_nodes()]
        self.device_dropdown.grid(row=0, column=1, pady=10, columnspan=2, sticky="ew")

        self.device_dropdown.bind("<<ComboboxSelected>>", self.update_selected_node)

        # Node Data
        node_data_frame = tk.Frame(self.master)
        node_data_frame.grid(row=1, column=0, padx=10, pady=10, sticky="n")

        tk.Label(node_data_frame, text="Node Data", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2)

        self.name_label = tk.Label(node_data_frame, text="Name: ")
        self.name_label.grid(row=1, column=0, sticky="w")

        self.eui_label = tk.Label(node_data_frame, text="Dev EUI: ")
        self.eui_label.grid(row=2, column=0, sticky="w")

        self.device_type_label = tk.Label(node_data_frame, text="Unit Type: ")
        self.device_type_label.grid(row=3, column=0, sticky="w")

        self.rssi_label = tk.Label(node_data_frame, text="RSSI: ")
        self.rssi_label.grid(row=4, column=0, sticky="w")

        self.snr_label = tk.Label(node_data_frame, text="SNR: ")
        self.snr_label.grid(row=5, column=0, sticky="w")

        self.online_label = tk.Label(node_data_frame, text="Online: ")
        self.online_label.grid(row=6, column=0, sticky="w")

        self.last_seen_label = tk.Label(node_data_frame, text="Last Seen at: ")
        self.last_seen_label.grid(row=7, column=0, sticky="w")

        # Buttons
        button_frame = tk.Frame(self.master)
        button_frame.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="n")

        self.status_request_button = ttk.Button(button_frame, text="Status Request", command=self.send_status_request)
        self.status_request_button.grid(row=0, column=0, padx=5, pady=5)

        self.reset_request_button = ttk.Button(button_frame, text="Reset Request", command=self.send_reset_request)
        self.reset_request_button.grid(row=0, column=1, padx=5, pady=5)

        self.data_collection_button = ttk.Button(button_frame, text="Data Collection",
                                                 command=self.send_data_collection_request)
        self.data_collection_button.grid(row=0, column=2, padx=5, pady=5)

        self.add_button = ttk.Button(button_frame, text="Add Node", command=self.open_add_node_dialog)
        self.add_button.grid(row=1, column=0, padx=5, pady=5)

        self.remove_button = ttk.Button(button_frame, text="Remove Node", command=self.remove_selected_node)
        self.remove_button.grid(row=1, column=1, padx=5, pady=5)

        # Alerts Listbox
        alert_frame = tk.Frame(self.master)
        alert_frame.grid(row=1, column=3, rowspan=4, padx=10, pady=10)

        tk.Label(alert_frame, text="Alerts").pack()
        self.alert_listbox = tk.Listbox(alert_frame, width=30, height=20)
        self.alert_listbox.pack(expand=True)

        # Log Listbox
        log_frame = tk.Frame(self.master)
        log_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

        tk.Label(log_frame, text="Log", font=("Arial", 12, "bold")).pack()
        self.log_listbox = tk.Listbox(log_frame, width=100, height=10)
        self.log_listbox.pack(fill="both", expand=True)

        # Disable buttons initially
        self.disable_command_buttons()

    def update_combobox(self):
        self.device_dropdown['values'] = [str(node) for node in self.node_manager.get_all_nodes()]

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
            self.name_label.config(text=f"Name: {self.selected_node.name}")
            self.eui_label.config(text=f"Dev EUI: {self.selected_node.dev_eui}")
            self.device_type_label.config(text=f"Unit Type: {self.selected_node.device_type}")
            status_info = self.chirpstack_client.get_device_status(self.selected_node.dev_eui, self.app_id)
            # metrics_info = self.chirpstack_client.get_device_link_metrics(self.selected_node.dev_eui)
            # self.rssi_label.config(text=f"RSSI: {metrics_info.get('rssi', 'N/A')}")
            # self.snr_label.config(text=f"SNR: {metrics_info.get('snr', 'N/A')}")
            self.online_label.config(text=f"Online: {status_info.get('is_online', 'N/A')}")
            self.last_seen_label.config(text=f"Last Seen at: {status_info.get('last_seen', 'N/A')}")
            self.enable_command_buttons()
        else:
            self.name_label.config(text="Name: ")
            self.eui_label.config(text="Dev EUI: ")
            self.device_type_label.config(text="Unit Type: ")
            self.rssi_label.config(text="RSSI: ")
            self.snr_label.config(text="SNR: ")
            self.online_label.config(text="Online: ")
            self.last_seen_label.config(text="Last Seen at: ")
            self.disable_command_buttons()

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
                    dev_eui = self.selected_node.dev_eui
                    name = self.selected_node.name
                    device_type = self.selected_node.device_type
                    self.selected_node = None
                    self.device_var.set('')
                    self.eui_label.config(text="Device EUI: Not available")
                    self.device_type_label.config(text="Device Type: Not available")
                    messagebox.showinfo("Node Removed", "The node has been removed successfully.")

                    # Log the node removal
                    timestamp = self.get_time()
                    event_info = f"{timestamp} Node successfully removed, dev eui - {dev_eui}, name - {name}, Node type - {device_type}"
                    self.update_combobox()
                    self.add_event_to_listbox(event_info)
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

        tk.Label(self.add_node_window, text="Device Type:").grid(row=2, column=0, pady=5, padx=5)
        self.device_type_var = tk.StringVar()
        self.device_type_dropdown = ttk.Combobox(self.add_node_window, textvariable=self.device_type_var)
        self.device_type_dropdown['values'] = DEVICE_TYPES
        self.device_type_dropdown.grid(row=2, column=1, pady=5, padx=5)

        tk.Label(self.add_node_window, text="Device Profile:").grid(row=3, column=0, pady=5, padx=5)
        self.device_profile_var = tk.StringVar()
        self.device_profile_dropdown = ttk.Combobox(self.add_node_window, textvariable=self.device_profile_var)
        self.device_profile_dropdown['values'] = [name for _, name in self.device_profiles]
        self.device_profile_dropdown.grid(row=3, column=1, pady=5, padx=5)

        tk.Label(self.add_node_window, text="NwkKey:").grid(row=4, column=0, pady=5, padx=5)
        self.nwk_key_entry = tk.Entry(self.add_node_window)
        self.nwk_key_entry.grid(row=4, column=1, pady=5, padx=5)

        ttk.Button(self.add_node_window, text="Add Node", command=self.add_node).grid(row=5, column=0, columnspan=2, pady=10)

    def add_node(self):
        dev_eui = self.dev_eui_entry.get()
        name = self.name_entry.get()
        device_type = self.device_type_var.get()
        selected_profile_name = self.device_profile_var.get()
        device_profile_id = next((id for id, name in self.device_profiles if name == selected_profile_name), None)
        nwk_key = self.nwk_key_entry.get()

        if not dev_eui or not name or not device_profile_id or not nwk_key or not device_type:
            messagebox.showerror("Error", "Device EUI, Name, Device Type, Device Profile ID, and NwkKey are required.")
            return

        try:
            self.chirpstack_client.add_device(dev_eui, name, device_profile_id, self.app_id, nwk_key, device_type)
            messagebox.showinfo("Success", "Node added successfully!")
            self.node_manager.add_node(EndNode(dev_eui, name, device_type))
            self.device_dropdown['values'] = [str(node) for node in self.node_manager.get_all_nodes()]
            self.add_node_window.destroy()

            # Log the node addition
            self.update_combobox()
            timestamp = self.get_time()
            event_info = f"{timestamp} Node successfully added, dev eui - {dev_eui}, name - {name}, Node type - {device_type}"
            self.add_event_to_listbox(event_info)
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

    def get_time(self):
        return datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

    def start_logging(self):
        with open(self.log_file, "a") as f:
            start_time = self.get_time()
            f.write(f"Application started at: {start_time}\n")

    def log_event(self, event_info):
        with open(self.log_file, "a") as f:
            f.write(event_info + "\n")

    def on_closing(self):
        with open(self.log_file, "a") as f:
            close_time = self.get_time()
            f.write(f"Application closed at: {close_time}\n")
            # f.write("Listbox content:\n")
            # for event in self.device_list.get(0, tk.END):
            #     f.write(event + "\n")
        self.master.destroy()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("application/+/device/+/event/up")
        client.subscribe("application/+/device/+/event/join")
        client.subscribe("application/+/device/+/event/status")
        client.subscribe("application/+/device/+/event/ack")
        client.subscribe("application/+/device/+/event/txack")
        client.subscribe("application/+/device/+/event/log")

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
        elif event_type == "ack":
            self.handle_ack(data)
        elif event_type == "txack":
            self.handle_txack(data)
        elif event_type == "log":
            self.handle_log(data)

    def handle_uplink(self, data):
        device_name = data['deviceInfo'].get('deviceName', 'Unknown device')
        message = data.get('object', {}).get('message', 'No message')
        rssi = data['rxInfo'][0]['rssi'] if 'rxInfo' in data and len(data['rxInfo']) > 0 else 'N/A'
        snr = data['rxInfo'][0]['snr'] if 'rxInfo' in data and len(data['rxInfo']) > 0 else 'N/A'
        self.rssi_label.config(text=f"RSSI: {rssi}")
        self.snr_label.config(text=f"SNR: {snr}")

        if "Alert" in message:
            alert_info = f"Alert triggered by device {device_name} - {message}"
            self.master.after(0, lambda: self.add_alert_to_listbox(alert_info))

            # Send 0xFF to Sound Unit and Wearable Alert Unit devices
            for node in self.node_manager.get_all_nodes():
                if node.device_type in ["Sound Unit", "Wearable Alert Unit", "LiDAR unit"]:
                    self.chirpstack_client.enqueue_downlink(node.dev_eui, bytes([0xFF]))
                    timestamp = self.get_time()
                    event_info = f"{timestamp} - Downlink sent to device {node.name} - {node.dev_eui}, [0xFF] - Alert Response"
                    self.master.after(0, lambda: self.add_event_to_listbox(event_info))

        elif "Status" in message:
            status_info = f"Status message from device {device_name} - {message}"
            self.master.after(0, lambda: self.add_alert_to_listbox(status_info))
        elif "Data" in message:
            data_info = f"Data message from device {device_name} - {message}"
            self.master.after(0, lambda: self.add_alert_to_listbox(data_info))
        elif "Reset" in message:
            reset_info = f"Reset message from device {device_name} - {message}"
            self.master.after(0, lambda: self.add_alert_to_listbox(reset_info))

        timestamp = self.get_time()
        event_info = f"{timestamp} - Uplink - Device: {device_name}, RSSI: {rssi}, SNR: {snr}, Message: {message}"
        self.master.after(0, lambda: self.add_event_to_listbox(event_info))

    def handle_join(self, data):
        device_name = data['deviceInfo'].get('deviceName', 'Unknown device')
        dev_eui = data['deviceInfo'].get('devEui', 'Unknown DevEUI')

        timestamp = self.get_time()
        event_info = f"{timestamp} - Join - Device: {device_name}, DevEUI: {dev_eui}"
        self.master.after(0, lambda: self.add_event_to_listbox(event_info))

    def handle_status(self, data):
        device_name = data['deviceInfo'].get('deviceName', 'Unknown device')
        margin = data.get('margin', 'N/A')
        battery = data.get('batteryLevel', 'N/A')
        external_power = data.get('externalPowerSource', False)
        last_seen = data.get('lastSeenAt', 'N/A')

        timestamp = self.get_time()
        event_info = f"{timestamp} - Status - Device: {device_name}, Margin: {margin}, Battery: {battery}, External Power: {external_power}, Last Seen: {last_seen}"
        self.master.after(0, lambda: self.add_event_to_listbox(event_info))

    def handle_ack(self, data):
        device_name = data['deviceInfo'].get('deviceName', 'Unknown device')
        acknowledged = data.get('acknowledged', False)

        timestamp = self.get_time()
        event_info = f"{timestamp} - ACK - Device: {device_name}, Acknowledged: {acknowledged}"
        self.master.after(0, lambda: self.add_event_to_listbox(event_info))

    def handle_txack(self, data):
        device_name = data['deviceInfo'].get('deviceName', 'Unknown device')

        timestamp = self.get_time()
        event_info = f"{timestamp} - TXACK - Device: {device_name}"
        self.master.after(0, lambda: self.add_event_to_listbox(event_info))

    def handle_log(self, data):
        device_name = data['deviceInfo'].get('deviceName', 'Unknown device')
        log_message = data.get('message', 'No message')
        level = data.get('level', 'Unknown level')

        timestamp = self.get_time()
        event_info = f"{timestamp} - Log - Device: {device_name}, Level: {level}, Message: {log_message}"
        self.master.after(0, lambda: self.add_event_to_listbox(event_info))

    def send_status_request(self):
        if not self.selected_node:
            messagebox.showwarning("No Device Selected", "Please select a device first.")
            return
        data = COMMANDS["STATUS_REQUEST"]  # Status Request
        success, message = self.chirpstack_client.enqueue_downlink(self.selected_node.dev_eui, data)
        if success:
            self.log_and_display_downlink(self.selected_node.name, self.selected_node.dev_eui, data, "Status Request")
        messagebox.showinfo("Downlink Status", message)

    def send_reset_request(self):
        if not self.selected_node:
            messagebox.showwarning("No Device Selected", "Please select a device first.")
            return
        data = COMMANDS["RESET_REQUEST"]  # Reset Request
        success, message = self.chirpstack_client.enqueue_downlink(self.selected_node.dev_eui, data)
        if success:
            self.log_and_display_downlink(self.selected_node.name, self.selected_node.dev_eui, data, "Reset Request")
        messagebox.showinfo("Downlink Status", message)

    def send_data_collection_request(self):
        if not self.selected_node:
            messagebox.showwarning("No Device Selected", "Please select a device first.")
            return
        data = COMMANDS["DATA_COLLECTION_REQUEST"]  # Data Collection Trigger (LIDAR Reading)
        success, message = self.chirpstack_client.enqueue_downlink(self.selected_node.dev_eui, data)
        if success:
            self.log_and_display_downlink(self.selected_node.name, self.selected_node.dev_eui, data,
                                          "Data Collection Request")
        messagebox.showinfo("Downlink Status", message)

    def log_and_display_downlink(self, device_name, dev_eui, bytes_data, command):
        timestamp = self.get_time()
        event_info = f"{timestamp} - Downlink sent to device {device_name} - {dev_eui}, {bytes_data} - {command}"
        self.add_event_to_listbox(event_info)

    def add_event_to_listbox(self, event_info):
        self.log_listbox.insert(tk.END, event_info)
        self.log_event(event_info)

    def add_alert_to_listbox(self, alert):
        self.alert_listbox.insert(tk.END, alert)
        self.log_event(alert)

    def show_alert(self, title, message):
        self.master.after(0, lambda: messagebox.showwarning(title, message))
