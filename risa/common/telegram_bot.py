from typing import List

import re
from abc import ABC, abstractmethod

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)


class Bot:
    @abstractmethod
    def add_handlers(self, updater: Updater) -> None:
        pass

    @staticmethod
    def not_implemented(update: Update, context: CallbackContext):
        update.message.reply_text(f"{update.message.text}: Not Implemented")


class TelegramBot(ABC):
    def __init__(self, token: str) -> None:
        updater = Updater(
            token=token,
            use_context=True,
        )

        # Create Command Handlers
        updater.dispatcher.add_handler(CommandHandler("start", self.help))
        updater.dispatcher.add_handler(CommandHandler("help", self.help))
        updater.dispatcher.add_handler(CommandHandler("commands", self.help))
        updater.dispatcher.add_handler(CallbackQueryHandler(self.query_handler))

        updater = self.init(updater=updater)

        # Filters out unknown commands & messages
        updater.dispatcher.add_handler(
            MessageHandler(Filters.command, self.send_msg_unknown_command)
        )
        updater.dispatcher.add_handler(MessageHandler(Filters.text, self.send_msg_unknown_text))

        updater.start_polling()
        updater.idle()

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def init(self, updater: Updater) -> Updater:
        return updater

    @staticmethod
    @abstractmethod
    def help(update: Update, context: CallbackContext):
        update.message.reply_text(
            """
        Commands :-
            /help - shows available commands
        """
        )

    @abstractmethod
    def query_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query.data
        update.callback_query.answer()

        if "subscribe" in query:
            print(query)

    @staticmethod
    def send_msg_unknown_command(update: Update, context: CallbackContext):
        update.message.reply_text(
            f"InvalidCommandError: '{update.message.text}' is not a valid command"
        )

    @staticmethod
    def send_msg_unknown_text(update: Update, context: CallbackContext):
        update.message.reply_text(f"UnknownTextError: '{update.message.text}'")

    @staticmethod
    def get_args(update: Update, context: CallbackContext) -> List[str]:
        if not context.args:
            update.message.reply_text("Error: Missing Argument")
        return context.args

    @staticmethod
    def get_args_from_message(update: Update, context: CallbackContext) -> List[str]:
        args = (
            re.search("(?<=[A-Za-z0-9]_)(.+(?=@.+bot)|.+)", update.message.text).group().split("_")
        )
        if not args:
            update.message.reply_text("Error: Missing Argument")
        return args
