import os
import logging
import logging.handlers
from pathlib import Path

import discord
from discord.ext import commands
import asyncio

from mott.exceptions import MottException
import mott.responses as responses
from mott.ocr import OCR, uri_validator


discord.utils.setup_logging(level=logging.INFO, root=False)

logger_discord = logging.getLogger("discord")

# logger_discord.setLevel(logging.INFO)
# log_dir = Path(os.getenv("DISCORD_BOT_DB_DIR", "."))
#
##handler = logging.handlers.RotatingFileHandler(
##    filename=log_dir / "mott_discord.log",
##    encoding="utf-8",
##    maxBytes=8 * 1024 * 1024,  # 8 MiB
##    backupCount=4,
##)
# dt_fmt = "%Y-%m-%d %H:%M:%S"
# formatter = logging.Formatter(
#    "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
# )
##handler.setFormatter(formatter)
##logger_discord.addHandler(handler)
# logger_discord.addHandler(logging.StreamHandler().setFormatter(formatter))


@commands.command()
async def motrader(ctx, *args):
    user_message = " ".join(args)

    message = ctx.message
    guild = str(message.guild)
    response_handler = responses.get_handler(guild)
    sender_name = str(message.author.display_name)
    account_name = str(message.channel.name)
    user_role_ids = [str(r) for r in message.author.roles]
    response = response_handler.handle_response(
        sender_name, account_name, user_role_ids, user_message
    )

    info_message = f' {guild}#{account_name} {sender_name}: "{user_message}"'
    logger_discord.info(info_message)
    await ctx.send(response)


async def send_message(response_handler, message, request_text, is_private):
    sender_name = str(message.author.display_name)
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

    discordbot = commands.Bot(command_prefix="!", intents=intents)

    discordbot.add_command(motrader)

    @discordbot.listen("on_message")
    async def on_message(message):
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
                try:
                    if attachment_is_image(attachment):
                        logger_discord.info(
                            f" {guild}#{channel} {username}: Reading image at {attachment.url}"
                        )
                        ocr_reader = await OCR.create(attachment.proxy_url)
                        auec_amount = await ocr_reader.image_to_auec()
                        user_message = f"pay {auec_amount}"
                        await send_message(
                            response_handler,
                            message,
                            user_message,
                            is_private=is_private,
                        )
                except MottException as e:
                    logger_discord.info("Exception during image text recognition")
                    response_message = (
                        f"Sorry, I couldn't read the aUEC from that screenshot."
                        f" Either check the examples above or try a different screenshot or enter the payment manually with `{APP_COMMAND} pay`."
                    )
                    await message.channel.send(response_message)
            return

    discordbot.run(TOKEN, log_handler=None)
