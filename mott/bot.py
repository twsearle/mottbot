import os
import logging
import logging.handlers
from pathlib import Path

import discord

from mott.exceptions import MottException
import mott.responses as responses
from mott.ocr import OCR, uri_validator

discord.utils.setup_logging()

logger_discord = logging.getLogger("discord")
logger_discord.setLevel(logging.INFO)
log_dir = Path(os.getenv("DISCORD_BOT_DB_DIR", "."))

handler = logging.handlers.RotatingFileHandler(
    filename=log_dir / "mott_discord.log",
    encoding="utf-8",
    maxBytes=1024 * 1024,  # 1 MiB
    backupCount=5,
)


async def send_message(response_handler, message, request_text, is_private):
    sender_name = str(message.author)
    account_name = str(message.channel.name)
    user_role_ids = [str(r) for r in message.author.roles]
    response = response_handler.handle_response(
        sender_name, account_name, user_role_ids, request_text
    )
    await message.author.send(response) if is_private else await message.channel.send(
        response
    )


def attachment_is_image(attachment):
    if not uri_validator(attachment.url):
        raise MottException(f"Could not read attachment URL")
    logger_discord.info(f"attachment type: {attachment.content_type}")
    if "image" in str(attachment.content_type):
        return True
    logger_discord.info(f"invalid image url: {attachment.url}")
    return False


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

        username = str(message.author)
        guild = str(message.guild)
        channel = str(message.channel.name)
        is_private = False
        response_handler = responses.get_handler(guild)

        if (
            channel in response_handler.watched_channels()
            and len(message.attachments) > 0
        ):
            logger_discord.info(
                f" {guild}#{channel} {username}: Reading images from {channel}"
            )
            for attachment in message.attachments:
                if attachment_is_image(attachment):
                    logger_discord.info(
                        f" {guild}#{channel} {username}: Reading image at {attachment.url}"
                    )
                    auec_amount = OCR(attachment.proxy_url).image_to_auec()
                    user_message = f"pay {auec_amount}"
                    await send_message(
                        response_handler, message, user_message, is_private=is_private
                    )
            return

        elif not message.content.startswith(APP_COMMAND):
            return

        else:
            user_command = message.content.removeprefix(APP_COMMAND).lstrip()
            is_private = True if user_command.startswith(FLAG_PRIVATE) else False
            user_message = str(user_command.removeprefix(FLAG_PRIVATE)).lstrip()

            logger_discord.info(f' {guild}#{channel} {username}: "{user_message}"')

            await send_message(
                response_handler, message, user_message, is_private=is_private
            )

    client.run(TOKEN, log_handler=None)
