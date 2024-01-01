import logging
from logging import StreamHandler

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

import pytest
import tinydb
import tinydb.storages
import mott.responses as responses
from mott.accounts import Accounts
from mott.responses import Responses


@pytest.fixture
def test_responses():
    db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)
    return Responses(Accounts(db))


sender_account_roles_args = ["Chris-Roberts", "MO-trader-receipts", ["CEO"]]


@pytest.fixture
def test_responses_created(test_responses):
    test_responses.handle_response(*sender_account_roles_args, "account-create CEO")
    return test_responses


@pytest.fixture
def test_responses_filled(test_responses_created):
    test_responses_created.handle_response(*sender_account_roles_args, "pay 10000")
    test_responses_created.handle_response(
        "BoneW", sender_account_roles_args[1], ["CEO"], "pay 1000"
    )
    test_responses_created.handle_response(*sender_account_roles_args, "withdraw 100")
    return test_responses_created


class TestResponses:
    def test_responses_init(self, test_responses):
        pass

    def test_responses_handle_help(self, test_responses):
        assert test_responses.handle_response(*sender_account_roles_args, "help")

    def test_responses_create_account(self, test_responses):
        assert test_responses.handle_response(
            *sender_account_roles_args, "account-create CEO"
        )

    def test_responses_watched_channels(self, test_responses_created):
        assert sender_account_roles_args[1] in test_responses_created.watched_channels()

    def test_responses_pay(self, test_responses_created):
        assert test_responses_created.handle_response(
            *sender_account_roles_args, "pay 10000 with no failure on exception"
        )
        returned_response = test_responses_created.handle_response(
            *sender_account_roles_args, "pay 10000"
        )
        assert (
            f"{sender_account_roles_args[0]} paid {sender_account_roles_args[1]} 10000AUEC"
            in returned_response
        )

    def test_responses_withdraw(self, test_responses_created):
        assert test_responses_created.handle_response(
            *sender_account_roles_args, "withdraw 10000 with no failure on exception"
        )
        returned_response = test_responses_created.handle_response(
            *sender_account_roles_args, "withdraw 10000"
        )
        assert "10000AUEC withdrawn" in returned_response

    def test_responses_account_delete(self, test_responses_created):
        returned_response = test_responses_created.handle_response(
            *sender_account_roles_args, f"account-delete {sender_account_roles_args[1]}"
        )
        assert f"account: {sender_account_roles_args[1]} deleted" in returned_response

    def test_responses_account_reset(self, test_responses_created):
        returned_response = test_responses_created.handle_response(
            *sender_account_roles_args, f"account-reset {sender_account_roles_args[1]}"
        )
        assert f"account: {sender_account_roles_args[1]} reset" in returned_response

    def test_responses_account_balance(self, test_responses_created):
        returned_response = test_responses_created.handle_response(
            *sender_account_roles_args,
            f"account-balance {sender_account_roles_args[1]}",
        )
        assert f"{sender_account_roles_args[1]} balance: 0" in returned_response

    def test_responses_last(self, test_responses_created):
        assert test_responses_created.handle_response(
            *sender_account_roles_args, f"last {sender_account_roles_args[1]}"
        )

    def test_responses_account_summary(self, test_responses_filled):
        returned_response = test_responses_filled.handle_response(
            *sender_account_roles_args,
            f"account-summary {sender_account_roles_args[1]}",
        )
        assert f'"{sender_account_roles_args[0]}" paid: 10000AUEC' in returned_response
        assert f'"BoneW" paid: 1000AUEC' in returned_response
        assert f"withdrawn: 100AUEC" in returned_response
        assert f"balance: 10900AUEC" in returned_response

    def test_responses_all(self, test_responses_filled):
        returned_response = test_responses_filled.handle_response(
            *sender_account_roles_args, f"account-all {sender_account_roles_args[1]}"
        )
        assert f'"{sender_account_roles_args[0]}",10000' in returned_response
        assert f'"BoneW",1000' in returned_response
        assert f'"{sender_account_roles_args[0]}",-100' in returned_response
