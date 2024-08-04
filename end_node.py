class EndNode:
    def __init__(self, dev_eui, name, device_type):
        self.dev_eui = dev_eui
        self.name = name
        self.device_type = device_type

    def __str__(self):
        return self.name