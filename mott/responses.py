import os
import functools
import logging

logger_discord = logging.getLogger("discord")

import tinydb
import tinydb.storages
from mott.exceptions import MottException
from mott.accounts import Accounts


@functools.cache
def get_handler(name):
    database_dir = os.getenv("DISCORD_BOT_DB_DIR")
    db_file_path = f"{database_dir}/{name.replace(' ', '_')}_db.json"
    logger_discord.info(
        f"get handler for db: {db_file_path} already exists? {os.path.isfile(db_file_path)}"
    )
    db = tinydb.TinyDB(db_file_path)
    return Responses(Accounts(db))


class Responses:
    def __init__(self, accounts):
        self.accounts_ = accounts

    def watched_channels(self):
        return self.accounts_.account_names()

    def handle_response(
        self, sender_name, account_name, user_role_ids, message_text
    ) -> str:
        message_split = message_text.split()
        command = message_split[0]
        try:
            if command == "help":
                return self.handle_help()
            elif len(message_split) < 2:
                raise MottException(
                    "Sorry, I couldn't understand your request. Please check the help and try again"
                )

            if command == "account-create":
                role_id = message_split[1]
                self.accounts_.create(account_name, role_id)
                logger_discord.info(
                    f" creating account and {account_name} channel to watchlist: {self.watched_channels()}"
                )
                return f"account: {account_name} created for {role_id}"
            elif not self.accounts_.permitted(account_name, user_role_ids):
                raise MottException(
                    f"Sorry, you either do not have permissions or the account: {account_name} does not yet exist in watchlist: {self.watched_channels()}"
                )

            if command == "pay":
                if len(message_split) != 2:
                    raise MottException(
                        "Sorry, I couldn't understand your request. Please check the help and try again"
                    )
                return self.handle_pay(sender_name, account_name, message_split[1])

            if command == "withdraw":
                if len(message_split) != 2:
                    raise MottException(
                        "Sorry, I couldn't understand your request. Please check the help and try again"
                    )
                return self.handle_withdraw(sender_name, account_name, message_split[1])

            if command == "account-delete":
                specified_account = message_split[1]
                self.accounts_.delete(specified_account)
                logger_discord.info(
                    f"deleting account: removing {account_name} channel from watchlist: {self.watched_channels()}"
                )
                return f"account: {specified_account} deleted"

            elif command == "account-reset":
                specified_account = message_split[1]
                self.accounts_.reset(specified_account)
                logger_discord.info(
                    f"resetting account removing and re-adding {account_name} channel from watchlist: {self.watched_channels()}"
                )
                return f"account: {specified_account} reset"

            elif command == "account-balance":
                specified_account = message_split[1]
                balance = self.accounts_.balance(specified_account)
                return f"{specified_account} balance: {balance}"

            elif command == "last":
                specified_account = message_split[1]
                transaction = self.accounts_.last_transaction(specified_account)
                return f'<t:{int(transaction["timestamp"]):d}> id: "{transaction["id"]}" value: {int(transaction["value"]):d}AUEC'

            elif command == "account-summary":
                specified_account = message_split[1]
                summary_msg = f"### Account Summary: {specified_account}\n"
                source_contributions, withdrawls = self.accounts_.summary(
                    specified_account
                )
                for contributor, value in source_contributions.items():
                    summary_msg += f'"{contributor}" paid: {int(value):d}AUEC\n'
                summary_msg += f"withdrawn: {int(withdrawls):d}AUEC\n"
                summary_msg += (
                    f"balance: {int(self.accounts_.balance(specified_account)):d}AUEC\n"
                )
                return summary_msg

            elif command == "account-all":
                specified_account = message_split[1]
                all_transactions = self.accounts_.all(specified_account)
                all_msg = f"### Account Transactions: {specified_account}\n"
                all_msg += f"time,author,value\n"
                for transaction in all_transactions:
                    all_msg += f'<t:{int(transaction["timestamp"]):d}>,"{transaction["id"]}",{int(transaction["value"]):d}\n'
                return all_msg

            else:
                return f"Sorry, I couldn't understand your request. The subcommand '{command}' was not recognised."

        except MottException as e:
            return e.message

    @staticmethod
    def handle_help() -> str:
        logging.info("responding to `help` request")
        description = (
            "I am a Star Citizen mo.trader helper bot. I am holding the line until CIG give us a decent banking app for in-game money. Talk to me with `!motrader <command>`. If you expect a private response start your command with `?`\n\n"
            "Once you create an account in a channel I will begin watching all images posted in that channel. If they can be interpreted as screenshots of an mo.trader transaction, I will save the value and sender to the account database. This data can be queried by those with sufficient permissions below. \n\n"
            "### basic commands: \n\n"
            "`help`\n\t print this help message \n\n"
            "`account-create <accountname> <rolename>` \n\t create account that watches channel `<accountname>` can only be edited/viewed by those with `<rolename>`.\n\n"
            "### restricted commands (only available to users with owning role): \n\n"
            "`pay <accountname> <value>` \n\t add motrader transaction from you to `<accountname>` of `<value>` AUEC.\n\n"
            "`withdraw <value>` \n\t add motrader transaction deducting `<value>` AUEC from `<accountname>` corresponding to current channel.\n\n"
            "`account-delete <accountname>` \n\t create account named `<accountname>`.\n\n"
            "`account-balance <accountname>` \n\t display current AUEC balance of `<accountname>`. \n\n"
            "`account-reset <accountname>` \n\t reset AUEC transaction records for `<accountname>`. \n\n"
            "`account-summary <accountname>` \n\t print summary of AUEC transaction records for `<accountname>` by user.\n\n"
            "`account-all <accountname>` \n\t print all AUEC transaction records for `<accountname>`.\n\n"
            "`last <accountname>` \n\t print last transaction record for `<accountname>`.\n\n"
        )
        return description

    def handle_pay(self, sender_name, account_name, value) -> str:
        logging.info(
            "responding to `pay` request: {sender_name} is paying {value} to {account_name}"
        )
        for substr in value.split("."):
            if not substr.isdecimal():
                return f"Sorry, I couldn't understand your request. The payment value '{value}' is not a number."

        self.accounts_.pay_to(sender_name, account_name, float(value))
        return f"{sender_name} paid {account_name} {value}AUEC"

    def handle_withdraw(self, payee_name, account_name, value) -> str:
        logging.info(
            "responding to `withdraw` request: {payee_name} is withdrawing {value} from {account_name}"
        )
        for substr in value.split("."):
            if not substr.isdecimal():
                return f"Sorry, I couldn't understand your request. The withdrawl value '{value}' is not a number."

        self.accounts_.withdraw_from(payee_name, account_name, float(value))
        return f"{account_name} {value}AUEC withdrawn"
