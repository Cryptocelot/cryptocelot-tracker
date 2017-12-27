class Definition():
    """Store instructions for determining an attribute while parsing records."""

    def __init__(self, key=None, value=None, transform=None):
        self.key = key
        self.value = value
        self.transform = transform
