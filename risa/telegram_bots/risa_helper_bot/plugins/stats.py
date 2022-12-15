from common.telegram_bot import Bot
from stats.stats import Stats, StatsTelegram
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater

from config.config import RISA_HELPER_BOT


class StatsManager(Bot):
    def add_handlers(self, updater: Updater):
        updater.dispatcher.add_handler(CommandHandler("stats", self.stats))
        updater.dispatcher.add_handler(CommandHandler("s", self.stats))
        updater.dispatcher.add_handler(
            MessageHandler(Filters.regex(r"^(/stat_[\d\D]+)$"), self.stat)
        )

    @staticmethod
    def stats(update: Update, context: CallbackContext):
        update.message.reply_text(text=StatsTelegram().summary_text)

    @staticmethod
    def stat(update: Update, context: CallbackContext):
        try:
            id_name = update.message.text.replace("/stat_", "").replace(f"@{RISA_HELPER_BOT}", "")
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")
        view_details_text = Stats().get_view_details_text(id_name=id_name)
        update.message.reply_text(text=view_details_text, parse_mode=ParseMode.HTML)
