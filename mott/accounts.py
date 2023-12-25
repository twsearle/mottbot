from mott.exceptions import MottException


class AccountDoesNotExistError(MottException):
    def __init__(self, account_name, message=""):
        if message == "":
            self.message = f"Account: {account_name} does not exist."
        else:
            self.message = message
        self.account_name = account_name
        super().__init__(self.message)


class AccountAlreadyExistsError(MottException):
    def __init__(self, account_name, message=""):
        if message == "":
            self.message = f"Account: {account_name} already exists. Perhaps you intended to `delete` or `reset`?"
        else:
            self.message = message
        self.account_name = account_name
        super().__init__(self.message)


class Accounts:
    def __init__(self, database_name):
        self.name_ = database_name
        self.conn_ = {}
        self.accounts_table_ = []

    def create(self, account_name, role_id):
        if self.conn_.get(account_name, None) != None:
            raise AccountAlreadyExistsError(account_name)
        self.accounts_table_.append(
            {"account name": account_name, "owning role": role_id}
        )
        self.conn_[account_name] = [{"id": 0, "source": "Account Setup", "value": 0}]

    def delete(self, account_name):
        if self.conn_.get(account_name, None) == None:
            raise AccountDoesNotExistError(account_name)
        del self.conn_[account_name]

    def reset(self, account_name):
        if self.conn_.get(account_name, None) == None:
            raise AccountDoesNotExistError(account_name)

        role = self.owning_role(account_name)
        self.delete(account_name)
        self.create(account_name, role)

    def owning_role(self, account_name):
        for account_info in self.accounts_table_:
            if account_info["account name"] == account_name:
                return account_info["owning role"]

        raise MottException(f"owning role for account: {account_name} not found")
        return None

    def balance(self, account_name) -> float:
        if self.conn_.get(account_name, None) == None:
            raise AccountDoesNotExistError(account_name)
        total = 0
        for line in self.conn_[account_name]:
            total += line["value"]
        return total

    def pay_to(self, sender_name, account_name, value):
        if self.conn_.get(account_name, None) == None:
            raise AccountDoesNotExistError(account_name)
        rowid = len(self.conn_[account_name])
        self.conn_[account_name].append(
            {"id": rowid, "source": sender_name, "value": value}
        )

    def withdraw_from(self, account_name, value):
        if self.conn_.get(account_name, None) == None:
            raise AccountDoesNotExistError(account_name)
        rowid = len(self.conn_[account_name])
        self.conn_[account_name].append(
            {"id": rowid, "source": "  --- ", "value": -value}
        )

    def last_transaction(self, account_name):
        if not self.conn_.get(account_name, None):
            raise AccountDoesNotExistError(account_name)
        last = self.conn_[account_name][-1]
        return last

    def summary(self, account_name):
        if not self.conn_.get(account_name, None):
            raise AccountDoesNotExistError(account_name)
        source_contributions = {}
        withdrawls = 0
        for line in self.conn_[account_name][1:]:
            if line["id"] == 0:
                continue
            if line["value"] < 0:
                withdrawls += abs(line["value"])
            else:
                if source_contributions.get(line["source"]):
                    source_contributions[line["source"]] += line["value"]
                else:
                    source_contributions[line["source"]] = line["value"]
        return source_contributions, withdrawls

    def permitted(self, account_name, role_ids):
        for account_info in self.accounts_table_:
            if (
                account_info["account name"] == account_name
                and account_info["owning role"] in role_ids
            ):
                return True
        return False
