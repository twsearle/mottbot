import pytest

import mott.accounts as acc


@pytest.fixture
def test_accounts():
    return acc.Accounts("test")


class TestAccounts:
    def test_accounts_init(self, test_accounts):
        pass

    def test_accounts_create(self, test_accounts):
        account_name, role_id = "Chris Roberts", "CEO"
        returnstr = test_accounts.create(account_name, role_id)
        with pytest.raises(acc.AccountAlreadyExistsError):
            test_accounts.create(account_name, role_id)

    def permitted(self, test_accounts):
        account_name, role_id = "Chris Roberts", "CEO"
        returnstr = test_accounts.create(account_name, role_id)
        assert test_accounts(account_name, ["CEO"])
        assert not test_accounts(account_name, ["pleb"])

    def test_accounts_delete(self, test_accounts):
        account_name, role_id = "Chris Roberts", "CEO"
        returnstr = test_accounts.create(account_name, role_id)
        returnstr = test_accounts.delete(account_name)
        with pytest.raises(acc.AccountDoesNotExistError):
            test_accounts.delete(account_name)

    def test_accounts_reset(self, test_accounts):
        account_name, role_id = "Chris Roberts", "CEO"
        with pytest.raises(acc.AccountDoesNotExistError):
            test_accounts.reset(account_name)
        returnstr = test_accounts.create(account_name, role_id)
        test_accounts.reset(account_name)
        test_accounts.delete(account_name)

    def test_accounts_pay_to(self, test_accounts):
        account_name, role_id = "Chris Roberts", "CEO"
        with pytest.raises(acc.AccountDoesNotExistError):
            test_accounts.pay_to("BoneW", account_name, 1e7)
        returnstr = test_accounts.create(account_name, role_id)
        test_accounts.pay_to("BoneW", account_name, 1e7)
        balance = test_accounts.balance(account_name)
        test_accounts.delete(account_name)
        assert balance == 1e7

    def test_accounts_withdraw_from(self, test_accounts):
        account_name, role_id = "Chris Roberts", "CEO"
        with pytest.raises(acc.AccountDoesNotExistError):
            test_accounts.withdraw_from(account_name, 1e9)
        returnstr = test_accounts.create(account_name, role_id)
        test_accounts.withdraw_from(account_name, 1e9)
        balance = test_accounts.balance(account_name)
        test_accounts.delete(account_name)
        assert balance == -1e9

    def test_accounts_balance(self, test_accounts):
        account_name, role_id = "Chris Roberts", "CEO"
        with pytest.raises(acc.AccountDoesNotExistError):
            test_accounts.balance(account_name)
        returnstr = test_accounts.create(account_name, role_id)
        balance = test_accounts.balance(account_name)
        assert balance == 0
        test_accounts.pay_to("BoneW", account_name, 1e7)
        test_accounts.withdraw_from(account_name, 5e6)
        balance = test_accounts.balance(account_name)
        test_accounts.delete(account_name)
        assert balance == 5e6

    def test_accounts_last_transaction(self, test_accounts):
        account_name, role_id = "Chris Roberts", "CEO"
        with pytest.raises(acc.AccountDoesNotExistError):
            last = test_accounts.last_transaction(account_name)
        returnstr = test_accounts.create(account_name, role_id)
        last = test_accounts.last_transaction(account_name)
        assert last["id"] == 0
        assert last["value"] == 0
        test_accounts.pay_to("BoneW", account_name, 1e7)
        last = test_accounts.last_transaction(account_name)
        test_accounts.delete(account_name)
        assert last["id"] == 1
        assert last["source"] == "BoneW"
        assert last["value"] == 1e7

    def test_accounts_summary(self, test_accounts):
        account_name, role_id = "Chris Roberts", "CEO"
        with pytest.raises(acc.AccountDoesNotExistError):
            source_contributions = test_accounts.summary(account_name)
        returnstr = test_accounts.create(account_name, role_id)
        test_accounts.pay_to("BoneW", account_name, 1e7)
        test_accounts.pay_to("greyL", account_name, 1e6)
        test_accounts.pay_to("greyMalding", account_name, 2e3)
        test_accounts.withdraw_from(account_name, 1e3)
        source_contributions, withdrawls = test_accounts.summary(account_name)
        test_accounts.delete(account_name)
        assert source_contributions["BoneW"] == 1e7
        assert source_contributions["greyL"] == 1e6
        assert source_contributions["greyMalding"] == 2e3
        assert withdrawls == 1e3
