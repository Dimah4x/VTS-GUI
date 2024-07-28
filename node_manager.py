class NodeManager:
    def __init__(self):
        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def remove_node(self, dev_eui):
        self.nodes = [node for node in self.nodes if node.dev_eui != dev_eui]

    def get_nodes(self):
        return self.nodes
