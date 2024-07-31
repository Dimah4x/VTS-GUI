# node_manager.py

from end_node import EndNode

class NodeManager:
    def __init__(self):
        self.nodes = {}

    def add_node(self, node):
        self.nodes[node.dev_eui] = node

    def remove_node(self, dev_eui):
        if dev_eui in self.nodes:
            del self.nodes[dev_eui]

    def get_node(self, dev_eui):
        return self.nodes.get(dev_eui)

    def get_all_nodes(self):
        return list(self.nodes.values())

    def load_nodes_from_chirpstack(self, devices):
        self.nodes.clear()
        for device in devices:
            # Assuming 'device' is an object with 'dev_eui' and 'name' attributes
            node = EndNode(dev_eui=device.dev_eui, name=device.name)
            self.add_node(node)
