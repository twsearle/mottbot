import os
import logging
import logging.handlers

import discord

import mott.responses as responses

discord.utils.setup_logging()

logger_discord = logging.getLogger("discord")
logger_discord.setLevel(logging.INFO)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# logger_discord.addHandler(handler)


async def send_message(message, request_text, is_private):
    response_handler = responses.get_handler(str(message.guild))
    user_role_ids = [r.id for r in message.author.roles]
    response = response_handler.handle_response(user_role_ids, request_text)
    await message.author.send(response) if is_private else await message.channel.send(
        response
    )


def run_discord_bot():
    TOKEN = os.getenv("DISCORD_BOT_SECRET_TOKEN")
    APP_COMMAND = "!motrader "
    FLAG_PRIVATE = "?"

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        logger_discord.info(f" {client.user} is now running")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if not message.content.startswith(APP_COMMAND):
            return

        username = str(message.author)
        user_command = message.content.removeprefix(APP_COMMAND).lstrip()
        is_private = True if user_command.startswith(FLAG_PRIVATE) else False
        user_message = str(user_command.removeprefix(FLAG_PRIVATE)).lstrip()
        channel = str(message.channel)
        guild = str(message.guild)

        logger_discord.info(f' {guild}#{channel} {username}: "{user_message}"')

        await send_message(message, user_message, is_private=is_private)

    client.run(TOKEN, log_handler=None)
