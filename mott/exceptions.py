class MottException(Exception):
    def __init__(self, message="Unknown error."):
        self.message = message
        super().__init__(self.message)
