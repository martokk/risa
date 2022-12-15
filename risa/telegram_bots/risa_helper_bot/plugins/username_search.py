from common.telegram_bot import Bot
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater


class UsernameSearch(Bot):
    def add_handlers(self, updater: Updater):
        updater.dispatcher.add_handler(CommandHandler("user", self.username_search))
        updater.dispatcher.add_handler(CommandHandler("username", self.username_search))
        updater.dispatcher.add_handler(CommandHandler("u", self.username_search))

    def username_search(self, update: Update, context: CallbackContext):
        self.not_implemented(update=update, context=context)
