from typing import Dict, List

import datetime
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from risa.common.constants import LOG_FILE
from risa.common.subscriptions import Subscriptions
from risa.scrapers.router import ScraperRouter

# Configure Loguru Logger
logger.add(LOG_FILE, level="TRACE", rotation="50 MB")


class SubscriptionWatcher:
    @property
    def name(self) -> str:
        return self.__class__.__name__

    def check_app_for_updates(self, app: str, context: CallbackContext) -> None:
        print(f"{datetime.datetime.now()} - {self.name} - Checking board for updates...")
        subscriptions = Subscriptions(app)

        for url_key, sub in subscriptions.get_subscriptions().items():
            self.check_subscription_for_updates(app=app, sub=sub, context=context)

    def check_subscription_for_updates(self, app: str, sub: Dict, context: CallbackContext) -> None:
        url = sub["url"]

        last_checkpoint = sub.get("checkpoint", -1)
        limit = 3 if last_checkpoint == -1 else None

        # Check if url is broken (404)
        try:
            request = Request(sub["url"])
            f = urlopen(request)
            status_code = f.code
            f.close()

            if status_code == 404:
                raise URLError("404 Not Found")
        except (HTTPError, URLError) as e:
            print(f"{datetime.datetime.now()} - {self.name} - {e}: {sub['url']}")
            return

        scraper = ScraperRouter().get_scraper(url=url)
        scraper.scrape_url(url=url)

        if new_posts := scraper.get_new_since_checkpoint(checkpoint=last_checkpoint):
            if limit:
                new_posts = new_posts[-limit:]
            for post in new_posts:
                self.send_message_new_post(context=context, post=post, chat_ids=sub["chat_ids"])
                time.sleep(0.5)

            subscriptions = Subscriptions(app)
            subscriptions.update_checkpoint(url_key=sub["url_key"], checkpoint=scraper.checkpoint)
            subscriptions.save()
        return

    def send_message_new_post(self, context: CallbackContext, chat_ids: List, post: Dict) -> None:
        message = ""

        if post["body"] and post["subject"] and post["body"] != post["subject"]:
            message += f"<u><b>{post['subject']}</b></u> \n" if post["subject"] else ""
        else:
            message += "<u><b>No Subject:</b></u> \n" if post["subject"] else ""
        message += f"{post['body']} \n\n" if post["body"] else ""

        if post["files"]:
            message += f"<u><b>Uploads: {len(post['files'])}</b></u> \n"

        text = (
            f"{message}\n-----------------------------------\n"
            f"<i>{post['board']['board_url']}</i>\n"
            f"<i>{post['post_url']}</i>\n"
        )
        # f"<i>{post['board']['board_name']}</i>\n" \
        # f"<i>{post['thread']['thread_name']}</i>\n"

        # Define Inline Buttons
        button_board_name = InlineKeyboardButton(
            text=post["board"]["board_name"],
            callback_data=f"open_link {post['board']['board_url']}",
        )

        button_thread_name = InlineKeyboardButton(
            text=post["thread"]["thread_name"],
            callback_data=f"open_link {post['post_url']}",
        )

        button_subscribe_to_thread = InlineKeyboardButton(
            text="subscribe to thread",
            callback_data=f"subscribe_to_thread {post['thread']['thread_url']}",
        )

        for chat_id in chat_ids:
            buttons = [
                [
                    button_board_name,
                    button_thread_name,
                ],
                [button_subscribe_to_thread] if self.name == "RisaBoardsBot" else [],
            ]

            divider_text = "█████████████████"
            parse_mode = ParseMode.HTML
            reply_markup = InlineKeyboardMarkup(buttons)

            try:
                divider = context.bot.send_message(
                    chat_id=chat_id,
                    text=divider_text,
                    parse_mode=parse_mode,
                )
                message = context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
            except BadRequest as e:
                error_message = (
                    f"{datetime.datetime.now()} - {self.name} - BadRequestError: {e.message} \n"
                    f"\t{chat_id=} {text=} {parse_mode=} {reply_markup=}"
                )

                logger.error(error_message)
                message = context.bot.send_message(
                    chat_id=chat_id,
                    text=error_message,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )

            if post["files"]:

                for _upload in post["files"]:

                    # Check if image url is broken (404), replace with default if it is
                    try:
                        request = Request(_upload["url"])
                        response = urlopen(request)
                        status_code = response.code
                        response.close()
                    except (HTTPError, URLError):
                        status_code = 404

                    if status_code != 404:
                        photo = _upload["url"]
                    else:
                        print(f"Image url is not found ({status_code=}): {_upload['url']}")
                        photo = "https://anonib.al/.static/logo.png"

                    # Check filesize below 5MB (telegram limit for photo)
                    response = urlopen(_upload["url"])
                    meta = response.info()
                    size_bytes = int(meta.get("Content-Length"))

                    # Prepare photo/document as Message
                    caption = ""
                    caption += f"<i>{post['subject']}</i>\n"
                    caption += f"<i>{post['thread']['thread_url']}</i>\n"
                    caption += f"{_upload['filename']}\n"
                    caption = caption[:199]

                    reply_to_message_id = message.message_id

                    try:
                        if size_bytes > 5000000:
                            context.bot.send_document(
                                chat_id=chat_id,
                                document=photo,
                                caption=caption,
                                reply_to_message_id=reply_to_message_id,
                                parse_mode=parse_mode,
                            )
                        else:
                            context.bot.send_photo(
                                chat_id=chat_id,
                                photo=photo,
                                caption=caption,
                                reply_to_message_id=reply_to_message_id,
                                parse_mode=parse_mode,
                            )
                    except BadRequest as e:
                        error_message = (
                            f"{datetime.datetime.now()} - {self.name} - "
                            f"BadRequestError: {e.message} \n"
                            f"\t{chat_id=} {photo=} {caption=} {len(caption)=} "
                            f"{reply_to_message_id=} {parse_mode=}"
                        )

                        logger.error(error_message)
                        message = context.bot.send_message(
                            chat_id=chat_id,
                            text=error_message,
                            parse_mode=parse_mode,
                            reply_markup=reply_markup,
                        )
