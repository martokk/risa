from common.telegram_bot import Bot
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater


class FeedManager(Bot):
    def add_handlers(self, updater: Updater):
        updater.dispatcher.add_handler(CommandHandler("feed_manager", self.feed_manager))
        updater.dispatcher.add_handler(CommandHandler("feed", self.feed_manager))
        updater.dispatcher.add_handler(CommandHandler("f", self.feed_manager))

    def feed_manager(self, update: Update, context: CallbackContext):
        self.not_implemented(update=update, context=context)
