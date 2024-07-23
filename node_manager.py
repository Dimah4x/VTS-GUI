import json
from end_node import EndNode

class NodeManager:
    def __init__(self, filename="nodes.json"):
        self.filename = filename
        self.nodes = self.load_nodes()

    def load_nodes(self):
        try:
            with open(self.filename, 'r') as file:
                data = json.load(file)
                return [EndNode(**node) for node in data]
        except FileNotFoundError:
            return []

    def save_nodes(self):
        with open(self.filename, 'w') as file:
            json.dump([node.to_dict() for node in self.nodes], file)

    def add_node(self, node):
        self.nodes.append(node)
        self.save_nodes()

    def remove_node(self, dev_eui):
        self.nodes = [node for node in self.nodes if node.dev_eui != dev_eui]
        self.save_nodes()

    def get_node_by_eui(self, dev_eui):
        for node in self.nodes:
            if node.dev_eui == dev_eui:
                return node
        return None
