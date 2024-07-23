class EndNode:
    def __init__(self, dev_eui, app_id, name):
        self.dev_eui = dev_eui
        self.app_id = app_id
        self.name = name

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            'dev_eui': self.dev_eui,
            'app_id': self.app_id,
            'name': self.name
        }
