from typing import List

from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram_bots.risa_helper_bot.plugins.download_manager import DownloadManager
from telegram_bots.risa_helper_bot.plugins.feed_manager import FeedManager
from telegram_bots.risa_helper_bot.plugins.profile_manager import ProfileManager
from telegram_bots.risa_helper_bot.plugins.stats import StatsManager
from telegram_bots.risa_helper_bot.plugins.username_search import UsernameSearch

from config.config import RISA_HELPER_BOT_TOKEN


def main() -> None:
    updater = Updater(token=RISA_HELPER_BOT_TOKEN, use_context=True)

    # Create Command Handlers
    updater.dispatcher.add_handler(CommandHandler("start", RisaHelperBot().help))
    updater.dispatcher.add_handler(CommandHandler("help", RisaHelperBot().help))
    updater.dispatcher.add_handler(CommandHandler("commands", RisaHelperBot().help))
    ProfileManager().add_handlers(updater=updater)
    DownloadManager().add_handlers(updater=updater)
    UsernameSearch().add_handlers(updater=updater)
    FeedManager().add_handlers(updater=updater)
    StatsManager().add_handlers(updater=updater)

    # Filters out unknown commands & messages
    updater.dispatcher.add_handler(MessageHandler(Filters.command, RisaHelperBot().unknown))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, RisaHelperBot().unknown_text))

    updater.start_polling()


class RisaHelperBot:
    @staticmethod
    def help(update: Update, context: CallbackContext):
        update.message.reply_text(
            """
        Commands :-
            /profile - Profile Manager
            /actions - Open Actions (Action Log)
            /downloads - Open Download Actions (Download Log)
            /stats - Displays summary of all stats.
            
        Send Media to bot --> creates action in Download Log.
        """
        )

    @staticmethod
    def unknown(update: Update, context: CallbackContext):
        update.message.reply_text(
            f"InvalidCommandError: '{update.message.text}' is not a valid command"
        )

    @staticmethod
    def unknown_text(update: Update, context: CallbackContext):
        update.message.reply_text(f"UnknownTextError: '{update.message.text}'")


if __name__ == "__main__":
    main()


class BotGlobals:
    STORED_PROFILE_NAME = None
    STORED_ADD_COMMAND = None
    STORED_MEDIA_DATA = None
    MEDIA_TYPES: List[str] = ["photo", "video", "animation", "document"]
