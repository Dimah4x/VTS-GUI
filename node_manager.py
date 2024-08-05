# node_manager.py

from end_node import EndNode

class NodeManager:
    def __init__(self):
        self.nodes = []

    def load_nodes_from_chirpstack(self, devices):
        self.nodes = []  # Ensure nodes is a list
        for device in devices:
            device_type = self.get_device_type(device)  # Fetch the device type
            node = EndNode(dev_eui=device.dev_eui, name=device.name, device_type=device_type)
            self.nodes.append(node)

    def get_device_type(self, device):
        # Fetch the device type from the device description or other metadata
        # Here we assume that the description field contains the device type
        return getattr(device, 'description', 'Blank Unit')  # Default to 'Blank Unit' if description is missing

    def get_all_nodes(self):
        return self.nodes

    def add_node(self, node):
        self.nodes.append(node)

    def remove_node(self, dev_eui):
        self.nodes = [node for node in self.nodes if node.dev_eui != dev_eui]