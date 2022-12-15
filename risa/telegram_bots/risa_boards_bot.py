from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater

from risa.common.telegram_bot import TelegramBot
from risa.config.config import (
    RISA_BOARDS_BOT,
    RISA_BOARDS_BOT_REPEATING_INTERVAL,
    RISA_BOARDS_BOT_TOKEN,
    RISA_FEEDS_BOT,
)
from risa.telegram_bots.plugins.subscription_manager import SubscriptionManager
from risa.telegram_bots.plugins.subscription_watcher import SubscriptionWatcher


class RisaBoardsBot(TelegramBot, SubscriptionManager, SubscriptionWatcher):
    def init(self, updater: Updater) -> Updater:
        updater.dispatcher.add_handler(CommandHandler("subscribe", self.subscribe))
        updater.dispatcher.add_handler(CommandHandler("s", self.subscribe))
        updater.dispatcher.add_handler(CommandHandler("list", self.list))
        updater.dispatcher.add_handler(CommandHandler("l", self.list))
        updater.dispatcher.add_handler(
            MessageHandler(Filters.regex(r"^(/remove_[\d\D]+)$"), self.remove)
        )
        updater.dispatcher.add_handler(
            MessageHandler(Filters.regex(r"^(/r_[\d\D]+)$"), self.remove)
        )
        updater.job_queue.run_repeating(
            self.repeating_check_boards_for_updates,
            first=1,
            interval=RISA_BOARDS_BOT_REPEATING_INTERVAL,
        )
        return updater

    def query_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query.data
        update.callback_query.answer()

        if "subscribe_to_thread" in query:
            url = query.split(" ")[1]
            app = RISA_FEEDS_BOT
            sub = self.add_subscription(app=app, url=url, chat_ids=[])
            update.effective_message.reply_text(
                f"Sucessfuly added new feed subscription. {app=} {sub=} "
            )

    @staticmethod
    def help(update: Update, context: CallbackContext):
        update.message.reply_text(
            """
        Commands :-
            /l, /list - list all subscriptions
            /s, /subscribe <URL> - Subscribe to a board url
            /r_<>, /remove_example_com_wi - Remove a subscription

        """
        )

    def subscribe(self, update: Update, context: CallbackContext):
        if not (args := self.get_args(update=update, context=context)):
            return
        sub = self.add_subscription(
            app=RISA_BOARDS_BOT, url=args[0], chat_ids=[update.message.chat_id]
        )
        update.message.reply_text(
            text=f"Sucessfuly added new subscription. Will get 3 latest posts... \n{args=}"
        )
        self.check_subscription_for_updates(app=RISA_BOARDS_BOT, sub=sub, context=context)

    def list(self, update: Update, context: CallbackContext):
        update.message.reply_text(text=self.get_subscriptions_as_text(app=RISA_BOARDS_BOT))

    def remove(self, update: Update, context: CallbackContext):
        if not (args := self.get_args_from_message(update=update, context=context)):
            return
        url_key = args[0]
        self.remove_subscription(app=RISA_BOARDS_BOT, url_key=url_key)
        update.message.reply_text(text=f"Sucessfuly removed Subscription: {url_key=}")

    def repeating_check_boards_for_updates(self, context: CallbackContext):
        return self.check_app_for_updates(app=RISA_BOARDS_BOT, context=context)


if __name__ == "__main__":
    RisaBoardsBot(token=RISA_BOARDS_BOT_TOKEN)
