# end_node.py

class EndNode:
    def __init__(self, dev_eui, name):
        self.dev_eui = dev_eui
        self.name = name

    def __str__(self):
        return f"{self.name} (EUI: {self.dev_eui})"
