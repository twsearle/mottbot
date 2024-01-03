from discord.ext.commands import CommandError


class MottException(CommandError):
    def __init__(self, message="Unknown error."):
        self.message = message
        super().__init__(self.message)
