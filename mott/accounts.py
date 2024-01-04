import time
import functools
import os
from datetime import datetime
import logging
import tinydb
from mott.exceptions import MottException

logger_discord = logging.getLogger("discord")


@functools.cache
def get_bank(bank_id):
    database_dir = os.getenv("DISCORD_BOT_DB_DIR")
    db_file_path = f"{database_dir}/{str(bank_id).replace(' ', '_')}_db.json"
    logger_discord.info(
        f"get handler for db: {db_file_path} already exists? {os.path.isfile(db_file_path)}"
    )
    db = tinydb.TinyDB(db_file_path)
    return Accounts(db)


class AccountError(MottException):
    def __init__(self, account_name, message=""):
        if message == "":
            self.message = f"Account: {account_name} error"
        else:
            self.message = message
        self.account_name = account_name
        super().__init__(self.message)


class AccountEmptyError(AccountError):
    def __init__(self, account_name, message=""):
        if message == "":
            self.message = f"Account: {account_name} has no transactions."
        else:
            self.message = message
        self.account_name = account_name
        super().__init__(self.message)


class AccountDoesNotExistError(AccountError):
    def __init__(self, account_name, message=""):
        if message == "":
            self.message = f"Account: {account_name} does not exist."
        else:
            self.message = message
        self.account_name = account_name
        super().__init__(self.message)


class AccountAlreadyExistsError(AccountError):
    def __init__(self, account_name, message=""):
        if message == "":
            self.message = f"Account: {account_name} already exists. Perhaps you intended to `delete` or `reset`?"
        else:
            self.message = message
        self.account_name = account_name
        super().__init__(self.message)


class Accounts:
    def __init__(self, db):
        self.db = db
        self.accounts_table = self.db.table("accounts")

    def create(self, account_name, role_id):
        query = tinydb.Query()
        if self.accounts_table.contains(query.account == account_name):
            raise AccountAlreadyExistsError(account_name)
        self.accounts_table.insert(
            {"account": account_name, "owners": str(role_id).replace("@", "")}
        )
        table = self.db.table(f"{account_name}_transactions")

    def delete(self, account_name):
        query = tinydb.Query()
        if not self.accounts_table.contains(query.account == account_name):
            raise AccountDoesNotExistError(account_name)
        self.db.drop_table(f"{account_name}_transactions")
        self.accounts_table.remove(tinydb.Query()["account"] == account_name)

    def owning_role(self, account_name):
        query = tinydb.Query()
        account_info = self.accounts_table.get(query.account == account_name)
        if account_info["account"] == account_name:
            return account_info["owners"]
        raise MottException(f"owning role for account: {account_name} not found")
        return None

    def reset(self, account_name):
        query = tinydb.Query()
        if not self.accounts_table.contains(query.account == account_name):
            raise AccountDoesNotExistError(account_name)
        role = self.owning_role(account_name)
        self.delete(account_name)
        self.create(account_name, role)

    def balance(self, account_name) -> float:
        query = tinydb.Query()
        if not self.accounts_table.contains(query.account == account_name):
            raise AccountDoesNotExistError(account_name)
        total = 0
        logger_discord.info(f"balance known accounts: {self.db.tables()}")
        transactions_db = self.db.table(f"{account_name}_transactions")
        for doc in transactions_db:
            total += doc["value"]
        return total

    def pay_to(self, message_id, sender_name, account_name, value, verified=False):
        query = tinydb.Query()
        if not self.accounts_table.contains(query.account == account_name):
            raise AccountDoesNotExistError(account_name)
        d = datetime.now()
        unixtime = int(time.mktime(d.timetuple()))
        transactions_db = self.db.table(f"{account_name}_transactions")
        transactions_db.insert(
            {
                "message_id": message_id,
                "timestamp": unixtime,
                "user_id": sender_name,
                "value": value,
                "ocr-verified": verified,
            }
        )

    def withdraw_from(self, message_id, payee_name, account_name, value):
        query = tinydb.Query()
        if not self.accounts_table.contains(query.account == account_name):
            raise AccountDoesNotExistError(account_name)
        d = datetime.now()
        unixtime = int(time.mktime(d.timetuple()))
        transactions_db = self.db.table(f"{account_name}_transactions")
        transactions_db.insert(
            {
                "message_id": message_id,
                "timestamp": unixtime,
                "user_id": payee_name,
                "value": -value,
                "ocr-verified": False,
            }
        )

    def last_transaction(self, account_name):
        query = tinydb.Query()
        if not self.accounts_table.contains(query.account == account_name):
            raise AccountDoesNotExistError(account_name)
        transactions_db = self.db.table(f"{account_name}_transactions")
        if len(transactions_db) < 1:
            raise AccountEmptyError(account_name)
        el = transactions_db.all()[-1]
        return transactions_db.get(doc_id=el.doc_id)

    def summary(self, account_name):
        query = tinydb.Query()
        if not self.accounts_table.contains(query.account == account_name):
            raise AccountDoesNotExistError(account_name)
        source_contributions = {}
        withdrawls = 0
        transactions_db = self.db.table(f"{account_name}_transactions")
        transaction_query = tinydb.Query()
        for line in transactions_db:
            if line["value"] < 0:
                withdrawls += abs(line["value"])
            else:
                if source_contributions.get(line["user_id"]):
                    source_contributions[line["user_id"]] += line["value"]
                else:
                    source_contributions[line["user_id"]] = line["value"]
        return source_contributions, withdrawls

    def all(self, account_name):
        query = tinydb.Query()
        if not self.accounts_table.contains(query.account == account_name):
            raise AccountDoesNotExistError(account_name)
        transactions_db = self.db.table(f"{account_name}_transactions")
        if len(transactions_db) < 1:
            raise AccountEmptyError(account_name)
        return transactions_db.all()

    def permitted(self, account_name, role_ids):
        role_ids_san = [str(r).replace("@", "") for r in role_ids]
        logger_discord.info(
            f"permissions check: {role_ids_san} sufficient for {account_name}?"
        )
        for account_info in self.accounts_table:
            logger_discord.info(
                f"permissions check: {account_info['account']} {account_info['owners']}"
            )
            if (
                account_info["account"] == account_name
                and account_info["owners"] in role_ids_san
            ):
                return True
        return False

    def account_names(self):
        return [doc["account"] for doc in self.accounts_table]
