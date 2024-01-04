import logging
from logging import StreamHandler

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

import asyncio

import unittest
import pytest
import pytest_asyncio

import mott.bot
from discord.ext.commands import CheckFailure, UserInputError, CommandError


@pytest.fixture
def mocked_bot(mocker):
    async def fetch_user(user_id):
        user = mocker.Mock()
        if user_id == 0:
            user.display_name = "Chris Roberts"
        else:
            user.display_name = "BoneW"
        return user

    m_bot = mocker.Mock()

    m_bot.fetch_user = fetch_user
    return m_bot


@pytest.fixture
def mocked_message(mocker):
    message = mocker.Mock()
    message.id = 0
    message.guild.name = "greyLegatus"
    message.guild.id = "greyLegatus"
    message.author.id = 0
    message.author.display_name = "Chris Roberts"
    message.author.roles = [
        "CEO",
    ]
    message.channel.name = "receipts"
    message.channel.id = 0
    return message


class TestBot:
    @pytest.mark.asyncio
    async def test_pay(self, mocker, mocked_message):
        mocked_ctx = mocker.patch(
            "mott.bot.commands.Context", new_callable=mocker.PropertyMock
        )
        mocked_ctx.message = mocked_message
        test_response = "Chris Roberts paid receipts 1aUEC"
        auec_value = 1
        # mock the async send method by setting its future
        future = asyncio.Future()
        future.set_result(test_response)
        mocked_ctx.send.return_value = future

        mocked_account = mocker.Mock()
        mocked_bank = mocker.patch("mott.bot.accounts.get_bank")
        mocked_bank.return_value = mocked_account

        await mott.bot.pay(mocked_ctx, auec_value)

        mocked_account.pay_to.assert_called_with(
            mocked_ctx.message.id,
            mocked_ctx.message.author.id,
            mocked_ctx.message.channel.id,
            auec_value,
        )
        mocked_ctx.send.assert_called_with(test_response)

    @pytest.mark.asyncio
    async def test_withdraw(self, mocker, mocked_message):
        mocked_ctx = mocker.patch(
            "mott.bot.commands.Context", new_callable=mocker.PropertyMock
        )
        mocked_ctx.message = mocked_message
        auec_value = 2
        test_response = "Chris Roberts withdrew 2aUEC from receipts"
        # mock the async send method by setting its future
        future = asyncio.Future()
        future.set_result(test_response)
        mocked_ctx.send.return_value = future

        mocked_account = mocker.Mock()
        mocked_bank = mocker.patch("mott.bot.accounts.get_bank")
        mocked_bank.return_value = mocked_account

        await mott.bot.withdraw(mocked_ctx, auec_value)

        mocked_account.withdraw_from.assert_called_with(
            mocked_ctx.message.id,
            mocked_ctx.message.author.id,
            mocked_ctx.message.channel.id,
            auec_value,
        )
        mocked_ctx.send.assert_called_with(test_response)

    @pytest.mark.asyncio
    async def test_last(self, mocker, mocked_message, mocked_bot):
        mocked_ctx = mocker.patch(
            "mott.bot.commands.Context", new_callable=mocker.PropertyMock
        )
        mocked_ctx.bot = mocked_bot
        mocked_ctx.message = mocked_message
        test_response = '<t:0> User: "BoneW" value: 578308 aUEC ocr-verified: False'
        # mock the async send method by setting its future
        future = asyncio.Future()
        future.set_result(test_response)
        mocked_ctx.send.return_value = future

        mocked_account = mocker.Mock()
        mocked_bank = mocker.patch("mott.bot.accounts.get_bank")
        mocked_bank.return_value = mocked_account
        mocked_account.last_transaction.return_value = {
            "timestamp": 0,
            "id": 1,
            "value": 578308,
            "ocr-verified": False,
        }

        await mott.bot.last_transaction(mocked_ctx)

        mocked_account.last_transaction.assert_called_with(
            mocked_ctx.message.channel.id
        )
        mocked_ctx.send.assert_called_with(test_response)

    @pytest.mark.asyncio
    async def test_account_create(self, mocker, mocked_message, mocked_bot):
        mocked_ctx = mocker.patch(
            "mott.bot.commands.Context", new_callable=mocker.PropertyMock
        )
        mocked_ctx.bot = mocked_bot
        mocked_ctx.message = mocked_message
        mocked_role = mocker.Mock()
        mocked_role.id = 0
        mocked_role.name = "CEO"
        test_response = "account: receipts created for CEO"

        # mock the async send method by setting its future
        future = asyncio.Future()
        future.set_result(test_response)
        mocked_ctx.send.return_value = future

        mocked_account = mocker.Mock()
        mocked_bank = mocker.patch("mott.bot.accounts.get_bank")
        mocked_bank.return_value = mocked_account

        await mott.bot.create(
            mocked_ctx,
            mocked_ctx.message.channel,
            mocked_role,
        )
        mocked_account.create.assert_called_with(
            mocked_ctx.message.channel.id,
            mocked_role.id,
        )
        mocked_ctx.send.assert_called_with(test_response)

    @pytest.mark.asyncio
    async def test_account_all(self, mocker, mocked_message, mocked_bot):
        mocked_ctx = mocker.patch(
            "mott.bot.commands.Context", new_callable=mocker.PropertyMock
        )
        mocked_ctx.bot = mocked_bot
        mocked_ctx.message = mocked_message
        test_response = """### Account Transactions: receipts
time,author,value,ocr-verified
<t:0>,"Chris Roberts",18082308,True
<t:0>,"BoneW",578308,False
"""

        # mock the async send method by setting its future
        future = asyncio.Future()
        future.set_result(test_response)
        mocked_ctx.send.return_value = future

        mocked_account = mocker.Mock()
        mocked_account.all.return_value = [
            {"timestamp": 0, "id": 0, "value": 18082308, "ocr-verified": True},
            {"timestamp": 0, "id": 1, "value": 578308, "ocr-verified": False},
        ]
        mocked_bank = mocker.patch("mott.bot.accounts.get_bank")
        mocked_bank.return_value = mocked_account

        await mott.bot._all(mocked_ctx, mocked_message.channel)
        mocked_account.all.assert_called_with(mocked_ctx.message.channel.id)
        mocked_ctx.send.assert_called_with(test_response)

    @pytest.mark.asyncio
    async def test_account_delete(self, mocker, mocked_message):
        mocked_ctx = mocker.patch(
            "mott.bot.commands.Context", new_callable=mocker.PropertyMock
        )
        mocked_ctx.message = mocked_message
        test_response = "account: receipts deleted"

        # mock the async send method by setting its future
        future = asyncio.Future()
        future.set_result(test_response)
        mocked_ctx.send.return_value = future

        mocked_account = mocker.Mock()
        mocked_bank = mocker.patch("mott.bot.accounts.get_bank")
        mocked_bank.return_value = mocked_account

        await mott.bot.delete(mocked_ctx, mocked_message.channel)
        mocked_ctx.send.assert_called_with(test_response)
        mocked_account.delete.assert_called_with(mocked_message.channel.id)

    @pytest.mark.asyncio
    async def test_account_reset(self, mocker, mocked_message):
        mocked_ctx = mocker.patch(
            "mott.bot.commands.Context", new_callable=mocker.PropertyMock
        )
        mocked_ctx.message = mocked_message
        test_response = "account: receipts reset"

        # mock the async send method by setting its future
        future = asyncio.Future()
        future.set_result(test_response)
        mocked_ctx.send.return_value = future

        mocked_account = mocker.Mock()
        mocked_bank = mocker.patch("mott.bot.accounts.get_bank")
        mocked_bank.return_value = mocked_account

        await mott.bot.reset(mocked_ctx, mocked_message.channel)
        mocked_ctx.send.assert_called_with(test_response)
        mocked_account.reset.assert_called_with(mocked_message.channel.id)

    @pytest.mark.asyncio
    async def test_account_balance(self, mocker, mocked_message):
        mocked_ctx = mocker.patch(
            "mott.bot.commands.Context", new_callable=mocker.PropertyMock
        )
        mocked_ctx.message = mocked_message
        test_response = "receipts balance: 1aUEC"

        # mock the async send method by setting its future
        future = asyncio.Future()
        future.set_result(test_response)
        mocked_ctx.send.return_value = future

        mocked_account = mocker.Mock()
        mocked_account.balance.return_value = 1
        mocked_bank = mocker.patch("mott.bot.accounts.get_bank")
        mocked_bank.return_value = mocked_account

        await mott.bot.balance(mocked_ctx, mocked_message.channel)
        mocked_ctx.send.assert_called_with(test_response)
        mocked_account.balance.assert_called_with(mocked_message.channel.id)

    @pytest.mark.asyncio
    async def test_account_summary(self, mocker, mocked_message, mocked_bot):
        mocked_ctx = mocker.patch(
            "mott.bot.commands.Context", new_callable=mocker.PropertyMock
        )
        mocked_ctx.bot = mocked_bot
        mocked_ctx.message = mocked_message
        test_response = (
            f'### Account Summary: receipts\n"Chris Roberts" paid: 18082308aUEC'
            f'\n"BoneW" paid: 578308aUEC\nwithdrawn: 0aUEC\nbalance: 18660616aUEC\n'
        )
        # mock the async send method by setting its future
        future = asyncio.Future()
        future.set_result(test_response)
        mocked_ctx.send.return_value = future

        mocked_account = mocker.Mock()
        mocked_account.summary.return_value = {
            0: 18082308,
            1: 578308,
        }, 0
        mocked_account.balance.return_value = 18660616
        mocked_bank = mocker.patch("mott.bot.accounts.get_bank")
        mocked_bank.return_value = mocked_account

        await mott.bot.summary(mocked_ctx, mocked_message.channel)
        mocked_ctx.send.assert_called_with(test_response)
        mocked_account.summary.assert_called_with(mocked_message.channel.id)
        mocked_account.balance.assert_called_with(mocked_message.channel.id)
