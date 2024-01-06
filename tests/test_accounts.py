import logging
from logging import StreamHandler

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

import pytest
import tinydb
import tinydb.storages
import mott.accounts as acc


@pytest.fixture
def test_accounts():
    db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)
    return acc.Accounts(db)


msg_id, account_name, role_id = 0, "Chris Roberts", "CEO"


class TestAccounts:
    def test_accounts_init(self, test_accounts):
        pass

    def test_accounts_create(self, test_accounts):
        returnstr = test_accounts.create(account_name, role_id)
        with pytest.raises(acc.AccountAlreadyExistsError):
            test_accounts.create(account_name, role_id)

    def permitted(self, test_accounts):
        returnstr = test_accounts.create(account_name, role_id)
        assert test_accounts.permitted(account_name, ["CEO"])
        assert not test_accounts.permitted(account_name, ["pleb"])

    def test_accounts_delete(self, test_accounts):
        returnstr = test_accounts.create(account_name, role_id)
        returnstr = test_accounts.delete(account_name)
        with pytest.raises(acc.AccountDoesNotExistError):
            test_accounts.delete(account_name)

    def test_accounts_reset(self, test_accounts):
        with pytest.raises(acc.AccountDoesNotExistError):
            test_accounts.reset(account_name)
        returnstr = test_accounts.create(account_name, role_id)
        test_accounts.reset(account_name)
        test_accounts.delete(account_name)

    def test_accounts_pay_to(self, test_accounts):
        with pytest.raises(acc.AccountDoesNotExistError):
            test_accounts.pay_to(msg_id, "BoneW", account_name, 1e7)
        returnstr = test_accounts.create(account_name, role_id)
        test_accounts.pay_to(msg_id, "BoneW", account_name, 1e7)
        balance = test_accounts.balance(account_name)
        test_accounts.delete(account_name)
        assert balance == 1e7

    def test_accounts_withdraw_from(self, test_accounts):
        with pytest.raises(acc.AccountDoesNotExistError):
            test_accounts.withdraw_from(msg_id, "SalteMike", account_name, 1e9)
        returnstr = test_accounts.create(account_name, role_id)
        test_accounts.withdraw_from(msg_id, "SalteMike", account_name, 1e9)
        balance = test_accounts.balance(account_name)
        test_accounts.delete(account_name)
        assert balance == -1e9

    def test_accounts_balance(self, test_accounts):
        with pytest.raises(acc.AccountDoesNotExistError):
            test_accounts.balance(account_name)
        returnstr = test_accounts.create(account_name, role_id)
        balance = test_accounts.balance(account_name)
        assert balance == 0
        test_accounts.pay_to(0, "BoneW", account_name, 1e7)
        test_accounts.withdraw_from(1, "SalteMike", account_name, 5e6)
        balance = test_accounts.balance(account_name)
        test_accounts.delete(account_name)
        assert balance == 5e6

    def test_accounts_last_transaction(self, test_accounts):
        with pytest.raises(acc.AccountDoesNotExistError):
            last = test_accounts.last_transaction(account_name)
        returnstr = test_accounts.create(account_name, role_id)
        with pytest.raises(acc.AccountEmptyError):
            last = test_accounts.last_transaction(account_name)
        test_accounts.pay_to(msg_id, "BoneW", account_name, 1e7)
        last = test_accounts.last_transaction(account_name)
        test_accounts.delete(account_name)
        assert last["message_id"] == msg_id
        assert last["user_id"] == "BoneW"
        assert last["value"] == 1e7
        assert last["ocr-verified"] == False

    def test_accounts_remove_transactions(self, test_accounts):
        with pytest.raises(acc.AccountDoesNotExistError):
            transactions = test_accounts.remove_transactions(account_name, msg_id)
        returnstr = test_accounts.create(account_name, role_id)
        with pytest.raises(acc.AccountError):
            transactions = test_accounts.remove_transactions(account_name, msg_id)
        test_accounts.pay_to(msg_id, "BoneW", account_name, 1e7)
        test_accounts.pay_to(msg_id, "BoneW", account_name, 1e7)
        transactions = test_accounts.remove_transactions(account_name, msg_id)
        test_accounts.delete(account_name)
        for transaction in transactions:
            assert transaction["message_id"] == msg_id
            assert transaction["user_id"] == "BoneW"
            assert transaction["value"] == 1e7
            assert transaction["ocr-verified"] == False

    def test_accounts_summary(self, test_accounts):
        with pytest.raises(acc.AccountDoesNotExistError):
            source_contributions = test_accounts.summary(account_name)
        returnstr = test_accounts.create(account_name, role_id)
        test_accounts.pay_to(0, "BoneW", account_name, 1e7)
        test_accounts.pay_to(1, "BoneW", account_name, 1e7)
        test_accounts.pay_to(2, "greyL", account_name, 1e6)
        test_accounts.pay_to(4, "greyMalding", account_name, 2e3)
        test_accounts.withdraw_from(5, "SalteMike", account_name, 1e3)
        source_contributions, withdrawls = test_accounts.summary(account_name)
        test_accounts.delete(account_name)
        assert source_contributions["BoneW"] == 2e7
        assert source_contributions["greyL"] == 1e6
        assert source_contributions["greyMalding"] == 2e3
        assert withdrawls == 1e3

    def test_accounts_account_names(self, test_accounts):
        _ = test_accounts.create(account_name, role_id)
        account_names = test_accounts.account_names()
        assert account_name in account_names
