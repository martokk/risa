from typing import Dict

import re

from action_logs.download_log import DownloadLog
from common.telegram_bot import Bot
from config.config import RISA_HELPER_BOT
from downloaders.anonfile import AnonFileGetDownload
from telegram import Message, ParseMode, ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater
from telegram_bots.risa_helper_bot.main import BotGlobals

"""
matches is entire URL
^(http[a-zA-Z0-9\s_\\.\-\(\):\/]+)$


matches only extention. ie. (.doc) or .(DOCX)
(\.[\d\D]{3,4})$

matches isURL and hasExtention
^(http[a-zA-Z0-9\s_\\.\-\(\):\/]+)(\.[\d\D]{3,4})$

"""


class DMLog:
    @staticmethod
    def dl_profile(update: Update, context: CallbackContext):
        try:
            profile_name = update.message.text.replace("/dl_", "").replace(
                f"@{RISA_HELPER_BOT}", ""
            )
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")

        log = DownloadLog()
        profile_log = log.get_actions_for_profile(profile_name=profile_name)

        try:
            first_media_key = list(profile_log.keys())[0]
        except IndexError:
            return update.message.reply_text(
                log.get_open_actions_as_text(), parse_mode=ParseMode.HTML
            )

        first_media_object = profile_log[first_media_key]
        media_type = first_media_object["media_data"]["media_type"]
        file_id = first_media_object["media_data"]["file_id"]

        update.message.reply_text(
            f"<b><u>{profile_name} - ({len(profile_log)})</u></b>", parse_mode=ParseMode.HTML
        )

        text = (
            f"{profile_name} \n"
            f"/{first_media_key.replace('open_', 'dl_close_').replace(f'@{RISA_HELPER_BOT}', '')}"
        )

        if media_type == "photo":
            update.message.reply_photo(caption=text, filename=file_id, photo=file_id)
        elif media_type == "video":
            update.message.reply_video(caption=text, filename=file_id, video=file_id)
        elif media_type == "document":
            update.message.reply_document(caption=text, filename=file_id, document=file_id)
        elif media_type == "link":
            update.message.reply_text(text=f"{text}\n\n{file_id}")

    @staticmethod
    def dlall_profile(update: Update, context: CallbackContext):
        try:
            profile_name = update.message.text.replace("/dlall_", "").replace(
                f"@{RISA_HELPER_BOT}", ""
            )
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")

        log = DownloadLog()
        profile_log = log.get_actions_for_profile(profile_name=profile_name)

        update.message.reply_text(
            f"<b><u>{profile_name} - ({len(profile_log)})</u></b>", parse_mode=ParseMode.HTML
        )

        open_keys_to_close = []
        for action_key, action_data in profile_log.items():
            media_type = action_data["media_data"]["media_type"]
            file_id = action_data["media_data"]["file_id"]
            text = profile_name
            open_keys_to_close.append(action_key)

            if media_type == "photo":
                update.message.reply_photo(caption=text, filename=file_id, photo=file_id)
            elif media_type == "video":
                update.message.reply_video(caption=text, filename=file_id, video=file_id)

        for key in open_keys_to_close:
            log.close_action(open_key_name=key)

        update.message.reply_text(
            f"Opened & Closed ({open_keys_to_close.__len__()}) download actions.'"
            f"Download media now or it will be lost forever!",
            parse_mode=ParseMode.HTML,
        )

        update.message.reply_text(log.get_open_actions_as_text(), parse_mode=ParseMode.HTML)

    @staticmethod
    def dl_close(update: Update, context: CallbackContext):
        try:
            open_key_name = update.message.text.replace("/dl_close_", "open_").replace(
                f"@{RISA_HELPER_BOT}", ""
            )
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")
        log = DownloadLog()
        open_actions = log.get_open()
        profile_name = open_actions[open_key_name]["profile_name"]
        log.close_action(open_key_name=open_key_name)

        BotGlobals.STORED_PROFILE_NAME = None

        update.message.reply_text(
            f"Closed: '{open_key_name}' \n" f"next: /dl_{profile_name}", parse_mode=ParseMode.HTML
        )

    @staticmethod
    def get_stored_profile_name(update: Update, context: CallbackContext):
        if BotGlobals.STORED_PROFILE_NAME:
            return BotGlobals.STORED_PROFILE_NAME

        reply_grid = [
            ["/select_profile"],
        ]
        reply_markup = ReplyKeyboardMarkup(reply_grid, one_time_keyboard=True, resize_keyboard=True)

        update.message.reply_text(
            "Missing Stored Profile. Click button.", reply_markup=reply_markup
        )
        #
        # return update.message.reply_text("/select_profile")
        # return ProfileManager().select_profile(update=update, context=context)

    def add_media_to_download_log(self, update: Update, context: CallbackContext) -> bool:
        stored_profile_name = self.get_stored_profile_name(update, context)
        stored_media_data = BotGlobals.STORED_MEDIA_DATA
        if stored_profile_name is None or stored_media_data is None:
            return False

        download_log = DownloadLog()
        if key := download_log.open_action(
            profile_name=stored_profile_name, media_data=stored_media_data
        ):
            update.message.reply_text(
                f"<u>Logged Media: ({stored_profile_name})</u> \n"
                f"key: {key} \n"
                f"profile_name: {stored_profile_name} \n"
                f"media_type: {stored_media_data['media_type']} \n"
                f"file_id: {stored_media_data['file_id']} \n\n"
                f"cancel: /{key.replace('open_', 'dl_close_').replace(f'@{RISA_HELPER_BOT}', '')}",
                reply_to_message_id=stored_media_data["message_id"],
                parse_mode=ParseMode.HTML,
            )
            BotGlobals.STORED_MEDIA_DATA = None
            return True
        return False


class HandleMediaDownloads:
    def handle_media(self, update: Update, context: CallbackContext):
        media_data = self.get_media_data_from_message(message=update.message)
        BotGlobals.STORED_MEDIA_DATA = media_data
        DMLog().add_media_to_download_log(update, context)

    @staticmethod
    def handle_link(update: Update, context: CallbackContext):
        try:
            url = update.message.text
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")

        media_data = {"file_id": url, "media_type": "link", "message_id": update.message.message_id}
        BotGlobals.STORED_MEDIA_DATA = media_data
        DMLog().add_media_to_download_log(update, context)

    def handle_media_url_by_type(self, update: Update, context: CallbackContext, media_type: str):
        try:
            url = update.message.text
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")

        if media_type == "photo":
            message = update.message.reply_photo(photo=url)
            file_id = message.photo[0].file_id
            media_type = "photo"
        elif media_type == "video":
            url = url.replace(" ", "%20")
            message = update.message.reply_video(video=url)
            file_id = message.video.file_id
            media_type = "video"
        else:
            message = update.message.reply_document(document=url)
            file_id = message.document.file_id
            media_type = "document"

        update.message.reply_text(f"media_type: {media_type} \n" f"file_id: {file_id}")

        media_data = self.get_media_data_from_message(message=message)
        BotGlobals.STORED_MEDIA_DATA = media_data

        DMLog().add_media_to_download_log(update, context)

    def handle_photo_url(self, update: Update, context: CallbackContext):
        return self.handle_media_url_by_type(update=update, context=context, media_type="photo")

    def handle_video_url(self, update: Update, context: CallbackContext):
        return self.handle_media_url_by_type(update=update, context=context, media_type="video")

    def handle_document_url(self, update: Update, context: CallbackContext):
        return self.handle_media_url_by_type(update=update, context=context, media_type="document")

    def handle_anonfiles(self, update, context):
        try:
            url = update.message.text
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")

        url = AnonFileGetDownload().get_direct_url_from_url(url=url)
        update.message.text = url

        return self.handle_video_url(update, context)

    @staticmethod
    def handled_by_3rd_party_bot(update: Update, context: CallbackContext):
        update.message.reply_text(
            "Media handled by Group bot. Resend downloaded media back to group to log."
        )

    @staticmethod
    def get_media_data_from_message(message: Message) -> Dict:
        for media in BotGlobals.MEDIA_TYPES:
            if media_obj := message.__getattribute__(media):
                file_id = media_obj[0].file_id if media == "photo" else media_obj.file_id
                return {"file_id": file_id, "media_type": media, "message_id": message.message_id}


class DownloadManager(DMLog, HandleMediaDownloads, Bot, BotGlobals):
    def add_handlers(self, updater: Updater):
        updater.dispatcher.add_handler(CommandHandler("downloader", self.downloader))
        updater.dispatcher.add_handler(CommandHandler("downloads", self.downloader))
        updater.dispatcher.add_handler(CommandHandler("download", self.downloader))
        updater.dispatcher.add_handler(CommandHandler("dl", self.downloader))
        updater.dispatcher.add_handler(
            MessageHandler(
                Filters.regex(r"^(http[a-zA-Z0-9\s_\\.\-\(\):\/\?\=\%]+)$"), self.router_url
            )
        )
        updater.dispatcher.add_handler(
            MessageHandler(Filters.photo | Filters.video | Filters.document, self.handle_media)
        )
        updater.dispatcher.add_handler(
            MessageHandler(Filters.regex(r"^(/dl_close[\d\D]+)$"), self.dl_close)
        )
        updater.dispatcher.add_handler(
            MessageHandler(Filters.regex(r"^(/dl_[\d\D]+)$"), self.dl_profile)
        )
        updater.dispatcher.add_handler(
            MessageHandler(Filters.regex(r"^(/dlall_[\d\D]+)$"), self.dlall_profile)
        )

    @staticmethod
    def router_url(update: Update, context: CallbackContext):
        """Routes url to method."""
        try:
            url = update.message.text
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")

        # Route by sites
        handle_as_link = ["gofile.io", "onlyfans.com"]
        for site in handle_as_link:
            if site in url:
                return HandleMediaDownloads().handle_link(update, context)

        # Route by sites using 3rd party bots to download in group.
        handled_by_3rd_party = ["tiktok.com", "instagram.com", "youtube.com"]
        for site in handled_by_3rd_party:
            if site in url:
                return HandleMediaDownloads().handled_by_3rd_party_bot(update, context)

        if re.search(pattern="^(https://(www\.)?anonfiles.com/.{10}/*(.+)*)$", string=url):
            HandleMediaDownloads().handle_anonfiles(update, context)

        # Route by media type
        search = re.search(pattern="(\.[\d\D]{3,4})$", string=url)
        if search:
            ext = search.group().lower()
            if ext in [
                ".mp4",
                ".gif",
                ".3gp",
                ".avi",
                ".dash",
                ".flv",
                ".m4v",
                ".mkv",
                ".mov",
                ".mpeg",
                ".mpg",
                ".ts",
                ".webm",
                ".wmv",
            ]:
                return HandleMediaDownloads().handle_video_url(update, context)

            if ext in [".jpg", ".jpeg", ".tiff", ".png", ".webp", ".raw", ".bmp", ".svg"]:
                return HandleMediaDownloads().handle_photo_url(update, context)

            if ext in [".zip", ".rar", ".mp3", ".001", ".7z", ".tgz", ".tar"]:
                return HandleMediaDownloads().handle_document_url(update, context)

        # Route fallback
        update.message.reply_text(text="Unknown URL Type. Falling back to media_type='link'.")
        return HandleMediaDownloads().handle_link(update, context)

    def downloader(self, update: Update, context: CallbackContext) -> None:
        self.download_actions(update=update, context=context)

    @staticmethod
    def download_actions(update: Update, context: CallbackContext) -> None:
        text = DownloadLog().get_open_actions_as_text()
        update.message.reply_text(text=text, parse_mode=ParseMode.HTML)
