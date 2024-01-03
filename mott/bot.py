"""
mo.trader tracker bot
---------------------

I am a Star Citizen mo.trader helper bot. I am holding the line until CIG give us a decent banking app for in-game money.

Once you create an account in a channel I will begin watching all images posted in that channel. If they can be interpreted as screenshots of an mo.trader transaction, I will save the value and sender to the account database. This data can be queried by those with sufficient permissions.
"""

import os
import logging
import logging.handlers
from pathlib import Path

import discord
from discord.ext import commands
import asyncio

from mott.exceptions import MottException, CommandError
import mott.accounts as accounts
from mott.ocr import OCR, uri_validator

module_doc = __doc__


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
async def pay(ctx, auec_value: int):
    """- pay into the account for this channel"""
    message = ctx.message

    guild = message.guild
    guild_bank = accounts.get_bank(guild.id)

    sender_name = message.author.display_name
    account_name = message.channel.name

    guild_bank.pay_to(sender_name, account_name, auec_value)

    info_message = (
        f"{guild} {sender_name}: responding to `pay` request,"
        f" {sender_name} is paying {auec_value} to {account_name}"
    )
    logger_discord.info(info_message)

    response = f"{sender_name} paid {account_name} {auec_value}aUEC"
    await ctx.send(response)


@commands.command()
async def withdraw(ctx, auec_value: int):
    """- withdraw from the account for this channel"""
    message = ctx.message

    guild = message.guild
    guild_bank = accounts.get_bank(guild.id)

    sender_name = message.author.display_name
    account_name = message.channel.name

    guild_bank.withdraw_from(sender_name, account_name, auec_value)

    info_message = (
        f"{guild} {sender_name}: responding to `withdraw` request,"
        f" {sender_name} is withdrawing {auec_value} from {account_name}"
    )
    logger_discord.info(info_message)

    response = f"{sender_name} withdrew {auec_value}aUEC from {account_name}"
    await ctx.send(response)


@commands.group(name="account")
async def _account(ctx):
    """- account management commands"""
    if ctx.invoked_subcommand is None:
        await ctx.send("Invalid account command passed.")


@commands.command()
async def create(
    ctx,
    account_channel: discord.TextChannel = commands.parameter(
        description="The discord text channel to watch for motrader receipts"
    ),
    owning_role: discord.Role = commands.parameter(
        description="The discord role required to manage the account"
    ),
):
    """- create a motrader-tracker account to track a discord channel with admin restrictions locked to a role"""
    message = ctx.message

    guild = message.guild
    guild_bank = accounts.get_bank(guild.id)

    sender_name = message.author.display_name
    user_role_ids = [str(r) for r in message.author.roles]
    account_name = account_channel.name

    guild_bank.create(account_name, owning_role.id)
    response = f"account: {account_name} created for {owning_role.name}"

    info_message = (
        f"{guild} {sender_name}: responding to `account create` "
        f"request, creating account and adding {account_name} "
        f"channel to watchlist"
    )
    logger_discord.info(info_message)
    await ctx.send(response)


@commands.command(name="all")
async def _all(
    ctx,
    account_channel: discord.TextChannel = commands.parameter(
        description="discord text channel that is being watched for receipts"
    ),
):
    """- print all transactions as comma-separated-values for an account"""
    message = ctx.message

    guild = message.guild
    guild_bank = accounts.get_bank(guild.id)

    sender_name = message.author.display_name
    account_name = account_channel.name
    user_role_ids = [str(r) for r in message.author.roles]

    all_transactions = guild_bank.all(account_name)
    response = f"### Account Transactions: {account_name}\n"
    response += f"time,author,value\n"
    for transaction in all_transactions:
        display_name = ctx.bot.fetch_user(transaction["id"]).display_name
        response += f'<t:{int(transaction["timestamp"]):d}>,"{display_name}",{int(transaction["value"]):d}\n'

    info_message = (
        f"{guild} {sender_name}: responding to `account all` "
        f"request, displaying all transactions for {account_name} channel"
    )
    logger_discord.info(info_message)
    await ctx.send(response)


@commands.command()
async def delete(
    ctx,
    account_channel: discord.TextChannel = commands.parameter(
        description="discord text channel that is being watched for receipts"
    ),
):
    """- delete an account"""
    message = ctx.message

    guild = message.guild
    guild_bank = accounts.get_bank(guild.id)

    sender_name = message.author.display_name
    account_name = account_channel.name

    guild_bank.delete(account_name)
    response = f"account: {account_name} deleted"

    info_message = (
        f"{guild} {sender_name}: responding to `account delete`"
        " request: deleting {account_name}"
    )
    logger_discord.info(info_message)
    await ctx.send(response)


@commands.command()
async def reset(
    ctx,
    account_channel: discord.TextChannel = commands.parameter(
        description="discord text channel that is being watched for receipts"
    ),
):
    """- reset an account"""
    message = ctx.message

    guild = message.guild
    guild_bank = accounts.get_bank(guild.id)

    sender_name = message.author.display_name
    account_name = account_channel.name

    guild_bank.reset(account_name)
    response = f"account: {account_name} reset"

    info_message = (
        f"{guild} {sender_name}: responding to `account reset`"
        f" request, resetting {account_name}"
    )
    logger_discord.info(info_message)
    await ctx.send(response)


@commands.command()
async def balance(
    ctx,
    account_channel: discord.TextChannel = commands.parameter(
        description="discord text channel that is being watched for receipts"
    ),
):
    """- print the current balance of an account"""
    message = ctx.message

    guild = message.guild
    guild_bank = accounts.get_bank(guild.id)

    sender_name = str(message.author.display_name)
    account_name = account_channel.name
    balance = guild_bank.balance(account_name)
    response = f"{account_name} balance: {balance}aUEC"

    info_message = (
        f"{guild} {sender_name}: responding to `account balance`"
        f" request, balance for {account_name} is {balance}"
    )
    logger_discord.info(info_message)
    await ctx.send(response)


@commands.command()
async def summary(
    ctx,
    account_channel: discord.TextChannel = commands.parameter(
        description="discord text channel that is being watched for receipts"
    ),
):
    """- print a summary of contributions and withdrawls from an account"""
    message = ctx.message

    guild = message.guild
    guild_bank = accounts.get_bank(guild.id)

    sender_name = str(message.author.display_name)
    account_name = account_channel.name
    source_contributions, withdrawls = guild_bank.summary(account_name)

    response = f"### Account Summary: {account_name}\n"
    for contributor_id, value in source_contributions.items():
        contributor = ctx.bot.fetch_user(contributor_id).display_name
        response += f'"{contributor}" paid: {int(value):d}aUEC\n'
    response += f"withdrawn: {int(withdrawls):d}aUEC\n"
    response += f"balance: {int(guild_bank.balance(account_name)):d}aUEC\n"

    info_message = (
        f"{guild} {sender_name}: responding to `account summary`"
        f" request for {account_name}"
    )
    logger_discord.info(info_message)
    await ctx.send(response)


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

    intents = discord.Intents.default()
    intents.message_content = True

    discordbot = commands.Bot(
        command_prefix=APP_COMMAND, intents=intents, description=module_doc
    )

    discordbot.add_command(pay)
    discordbot.add_command(withdraw)

    discordbot.add_command(_account)
    _account.add_command(create)
    _account.add_command(delete)
    _account.add_command(reset)
    _account.add_command(balance)
    _account.add_command(summary)
    _account.add_command(_all)

    @discordbot.listen("on_message")
    async def on_message(message):
        username = message.author.display_name
        guild = message.guild
        guild_bank = accounts.get_bank(guild.id)
        channel = message.channel.name
        is_private = False

        if (
            # channel in watched_channels()
            len(message.attachments)
            > 0
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
                        guild_bank.pay(auec_amount)
                except CommandError as e:
                    logger_discord.info("Exception during image text recognition")
                    response_message = (
                        f"Sorry, I couldn't read the aUEC from that screenshot."
                        f" Please check the examples above and try a different "
                        f"screenshot. Make sure you use a screenshot and not a "
                        f"photograph of the screen (I can't read images of PC monitors sorry)."
                        f" Alternatively, enter the payment manually with `{APP_COMMAND} pay`."
                    )
                    await message.channel.send(response_message)
            return

    discordbot.run(TOKEN, log_handler=None)
