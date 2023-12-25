import functools
import logging

logger_discord = logging.getLogger("discord")

from mott.exceptions import MottException
from mott.accounts import Accounts


@functools.cache
def get_handler(name):
    return Responses(Accounts(name))


class Responses:
    def __init__(self, accounts):
        self.accounts_ = accounts

    def handle_response(self, user_role_ids, message_text) -> str:
        sender_name = str(message.author)
        message_split = message_text.lower().split()
        try:
            if message_split[0] == "help":
                return self.handle_help()

            if message_split[0] == "pay":
                if len(message_split) != 3:
                    raise MottException(
                        "Sorry, I couldn't understand your request. Please check the help and try again"
                    )
                return self.handle_pay(sender_name, message_split[1], message_split[2])

            if message_split[0] == "withdraw":
                if len(message_split) != 3:
                    raise MottException(
                        "Sorry, I couldn't understand your request. Please check the help and try again"
                    )
                return self.handle_withdraw(message_split[1], message_split[2])

            if message_split[0] == "account":
                if len(message_split) < 3 or len(message_split) > 4:
                    raise MottException(
                        "Sorry, I couldn't understand your request. Please check the help and try again"
                    )
                if message_split[1] == "create" and len(message_split) < 4:
                    raise MottException(
                        "Please specify the role permissions to create account"
                    )
                return self.handle_account(user_role_ids, *message_split[1:])
        except MottException as e:
            return e.message

    @staticmethod
    def handle_help() -> str:
        logging.info("responding to `help` request")
        description = (
            "I am a Star Citizen mo.trader helper bot. I am holding the line until CIG give us a decent banking app for in-game money. Talk to me with `!motrader <command>`. If you expect a private response start your command with `?`\n\n"
            "### basic commands: \n\n"
            "`help`\n\t print this help message \n\n"
            "`pay <accountname> <value>` \n\t add motrader transaction from you to `<accountname>` of `<value>` AUEC.\n\n"
            "`withdraw <accountname> <value>` \n\t add motrader transaction deducting `<value>` AUEC from `<accountname>` (only available to account owner).\n\n"
            "### account management commands: \n\n"
            "`account create <accountname>` \n\t create account named `<accountname>`.\n\n"
            "`account delete <accountname>` \n\t create account named `<accountname>`.\n\n"
            "`account balance <accountname>` \n\t display current AUEC balance of `<accountname>`. \n\n"
            "`account reset <accountname>` \n\t reset AUEC transaction records for `<accountname>` (only available to account owner). \n\n"
            "`account summary <accountname>` \n\t print summary of AUEC transaction records for `<accountname>` by user (only available to account owner).\n\n"
            "`account last <accountname>` \n\t print last transaction record for `<accountname>` (only available to account owner).\n\n"
        )
        return description

    def handle_pay(self, sender_name, account_name, value) -> str:
        logging.info("responding to `pay` request")
        for substr in value.split("."):
            if not substr.isdecimal():
                return f"Sorry, I couldn't understand your request. The payment value '{value}' is not a number."

        self.accounts_.pay_to(sender_name, account_name, float(value))
        return f"{sender_name} paid {account_name} {value}AUEC"

    def handle_withdraw(self, account_name, value) -> str:
        logging.info("responding to `withdraw` request")
        for substr in value.split("."):
            if not substr.isdecimal():
                return f"Sorry, I couldn't understand your request. The withdrawl value '{value}' is not a number."

        self.accounts_.withdraw_from(account_name, float(value))
        return f"{account_name} {value}AUEC withdrawn"

    def handle_account(self, user_role_ids, command, account_name, role=None) -> str:
        logging.info("responding to `account` request")
        try:
            if command == "create":
                self.accounts_.create(account_name, role)
                return f"account: {account_name} created for {role}"
            elif not self.accounts_.permitted(account_name, user_role_ids):
                raise MottException(
                    "Sorry, you must be {role} to have permissions to manage account: {account_name}"
                )

            if command == "delete":
                self.accounts_.delete(account_name)
                return f"account: {account_name} deleted"
            elif command == "reset":
                self.accounts_.reset(account_name)
                return f"account: {account_name} reset"
            elif command == "balance":
                balance = self.accounts_.balance(account_name)
                return f"{account_name} balance: {balance}"
            elif command == "last":
                transaction = self.accounts_.last_transaction(account_name)
                if transaction["value"] < 0:
                    return f'id: {transaction["id"]} withdrawl: {abs(transaction["value"])}AUEC'
                return f'id: {transaction["id"]} source: "{transaction["source"]}" value: {transaction["value"]}AUEC'
            elif command == "summary":
                summary_msg = f"### Account Summary: {account_name}"
                source_contributions = self.accounts_.summary(account_name)
                for contributor, value in source_contributions.items():
                    summary_msg += f'source: "{contributor}" value: {value}AUEC'
                summary_msg += self.accounts_.balance(account_name)
                return summary_msg
            else:
                return f"Sorry, I couldn't understand your request. The subcommand '{command}' was not recognised."
        except MottException as e:
            return e.message
