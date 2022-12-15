from typing import Union

from action_logs.profile_log import ProfileLog
from common.profiles import ProfilesFromCache
from common.telegram_bot import Bot
from common.utils import Utils
from config.config import RISA_HELPER_BOT
from telegram import ParseMode, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update
from telegram_bots.risa_helper_bot.main import BotGlobals
from telegram_bots.risa_helper_bot.plugins.download_manager import DownloadManager


class EditProfile(BotGlobals):
    def create_profile(self, update: Update, context: CallbackContext) -> None:
        try:
            profile_name = context.args[0]
            profile_name = Utils().convert_case_to_snakecase(text=profile_name)
            profile_name = f"new_profile_{profile_name}"
        except IndexError:
            update.message.reply_text("Error: Missing Argument")
            return

        action_log = ProfileLog()
        action_log.open_action(
            profile_name=profile_name,
            service="create_profile",
            command="create",
            value=profile_name,
        )
        super().STORED_PROFILE_NAME = profile_name
        update.message.reply_text(
            f"Created profile '{profile_name}' \n\n" f"\t\t\t\t> /edit_{profile_name}"
        )

    @staticmethod
    def list(update: Update, context: CallbackContext):
        try:
            folder = context.args[0]
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")
        update.message.reply_text(f"Edit Profile > Listing '{folder}'")

        if folder == "new":
            profiles = ProfileLog().get_new_profiles()
            profile_names = list(profiles)
        else:
            profiles = ProfilesFromCache().get_profiles_by_type(folder)
            profile_names = [profile.profile_name for profile in profiles]
        edit_command_list = [f"/edit_{profile_name} " for profile_name in profile_names]
        update.message.reply_text("\n".join(edit_command_list))

    @staticmethod
    def edit_profile(update: Update, context: CallbackContext) -> None:
        reply_grid = [
            ["/list celebs", "/list creators"],
            ["/list kenosha", "/list known"],
            ["/list leaks", "/list new"],
        ]
        reply_markup = ReplyKeyboardMarkup(reply_grid, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text("CREATE/EDIT PROFILE", reply_markup=reply_markup)

    def edit(self, update: Update, context: CallbackContext):
        try:
            # profile_name = context.args[0]
            profile_name = update.message.text.replace("/edit_", "").replace(
                f"@{RISA_HELPER_BOT}", ""
            )
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")
        super().STORED_PROFILE_NAME = profile_name
        update.message.reply_text(
            f"Edit Profile > Edit '{super().STORED_PROFILE_NAME}' \n"
            f"\t\t ex: /add facebook bob.smith14"
        )
        if super().STORED_ADD_COMMAND:
            self.add(update, context)
            update.message.reply_text(super().STORED_ADD_COMMAND)
            super().STORED_ADD_COMMAND = None

    def add(self, update: Update, context: CallbackContext):
        if super().STORED_ADD_COMMAND:
            command_split = super().STORED_ADD_COMMAND.split(" ")
            context.args = []
            context.args.append(command_split[1])
            context.args.append(command_split[2])
            super().STORED_COMMAND = None
        try:
            service = context.args[0]
            value = context.args[1]
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")

        if not super().STORED_PROFILE_NAME:
            super().STORED_COMMAND = update.message.text
            update.message.reply_text("Error: Missing profile_name. Select a profile first")
            return self.edit_profile(update, context)

        action_log = ProfileLog()
        if not action_log.open_action(
            profile_name=super().STORED_PROFILE_NAME, service=service, command="add", value=value
        ):
            raise Exception("Failed to open action.")

        update.message.reply_text(
            f"Opened -> {super().STORED_PROFILE_NAME}: {service}: {value} \n\n"
            f"{self.get_open_actions_as_text()}",
            parse_mode=ParseMode.HTML,
        )


class SelectProfile(BotGlobals):
    @staticmethod
    def select_profile(update: Update, context: CallbackContext) -> None:
        reply_grid = [
            ["/select_list celebs", "/select_list creators"],
            ["/select_list kenosha", "/select_list known"],
            ["/select_list leaks", "/select_list new"],
        ]
        reply_markup = ReplyKeyboardMarkup(reply_grid, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text("Select Folder", reply_markup=reply_markup)

    @staticmethod
    def select_list(update: Update, context: CallbackContext):
        try:
            folder = context.args[0]
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")
        update.message.reply_text(f"Select Profile > Listing '{folder}'")

        if folder == "new":
            profiles = ProfileLog().get_new_profiles()
            profile_names = list(profiles)
        else:
            profiles = ProfilesFromCache().get_profiles_by_type(folder)
            profile_names = [profile.profile_name for profile in profiles]
        edit_command_list = [f"/select_{profile_name} " for profile_name in profile_names]
        update.message.reply_text("\n".join(edit_command_list))

    def select(self, update: Update, context: CallbackContext):
        try:
            # profile_name = context.args[0]
            profile_name = update.message.text.replace("/select_", "").replace(
                f"@{RISA_HELPER_BOT}", ""
            )
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")

        BotGlobals.STORED_PROFILE_NAME = profile_name
        # update.message.reply_text(f"STORED_PROFILE_NAME: {BotGlobals.STORED_PROFILE_NAME} \n"
        #                           f"STORED_MEDIA_DATA: {BotGlobals.STORED_MEDIA_DATA} \n",
        #                           parse_mode=ParseMode.HTML)

        if BotGlobals.STORED_PROFILE_NAME and BotGlobals.STORED_MEDIA_DATA:
            DownloadManager().add_media_to_download_log(update, context)

        return ProfileManager().profile(update, context)


class ViewProfile:
    @staticmethod
    def view_profile(update: Update, context: CallbackContext) -> None:
        reply_grid = [
            ["/view_list celebs", "/view_list creators"],
            ["/view_list kenosha", "/view_list known"],
            ["/view_list leaks", "/view_list new"],
        ]
        reply_markup = ReplyKeyboardMarkup(reply_grid, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text("CREATE/EDIT PROFILE", reply_markup=reply_markup)

    @staticmethod
    def view_list(update: Update, context: CallbackContext):
        try:
            folder = context.args[0]
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")
        update.message.reply_text(f"View Profile > Listing '{folder}'")

        if folder == "new":
            profiles = ProfileLog().get_new_profiles()
            profile_names = list(profiles)
        else:
            profiles = ProfilesFromCache().get_profiles_by_type(folder)
            profile_names = [profile.profile_name for profile in profiles]
        edit_command_list = [f"/view_{profile_name} " for profile_name in profile_names]
        update.message.reply_text("\n".join(edit_command_list))

    def view(self, update: Update, context: CallbackContext):
        try:
            # profile_name = context.args[0]
            profile_name = update.message.text.replace("/view_", "").replace(
                f"@{RISA_HELPER_BOT}", ""
            )
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")

        super().STORED_PROFILE_NAME = profile_name

        text = self.get_profile_cache_as_text(profile_name=profile_name)

        update.message.reply_text(f"{text}", parse_mode=ParseMode.HTML)

    @staticmethod
    def get_profile_cache_as_text(profile_name: str) -> str:
        def expand(key: str, value_obj: Union[list, str], pre=""):
            if not isinstance(value_obj, list):
                return f"{pre} {key}: {value_obj}"
            expand_text_lines = [f"{pre} {key}:"]
            for value_itm in value_obj:
                expand_text_lines.append(f"{pre}\t\t\t\t - {value_itm}")
            return "\n".join(expand_text_lines)

        profile = ProfilesFromCache().get_profile(profile_name=profile_name)

        header = f"<b><u>CACHED - {profile['name_or_folder']}</u></b>\n'"

        data: dict = profile.data
        name = data.pop("name", "None")
        alias = data.pop("alias", "None")
        location = data.pop("location", "None")
        usernames = data.pop("usernames", "None")

        data_text_lines = []
        for k, v in profile.data.items():
            data_text_lines.append(expand(key=k, value_obj=v, pre="\t\t\t\t"))
        data_text = "\n".join(data_text_lines)

        action_log_profile = ProfileLog().get_actions_for_profile(profile_name=profile_name)
        action_log_lines = []
        for action_id, action_dict in action_log_profile.items():
            action_log_lines.append(f"\t\t\t\t{action_id}:")
            action_log_lines.append(
                f"\t\t\t\t\t\t\t\t{action_dict['service']}: {action_dict['value']}"
            )

        action_log_text = "\n".join(action_log_lines)

        text_lines = [
            header,
            expand(key="name", value_obj=name),
            expand(key="alias", value_obj=alias),
            expand(key="location", value_obj=location),
            expand(key="usernames", value_obj=usernames),
            f"data: \n{data_text}",
            f"action_log: \n{action_log_text}" if len(action_log_profile) > 0 else "",
        ]

        return "\n".join(text_lines)


class ProfileManager(Bot, ViewProfile, EditProfile, SelectProfile):
    def add_handlers(self, updater: Updater):
        updater.dispatcher.add_handler(CommandHandler("profile", self.profile))
        updater.dispatcher.add_handler(CommandHandler("profiles", self.profile))
        updater.dispatcher.add_handler(CommandHandler("p", self.profile))
        updater.dispatcher.add_handler(CommandHandler("edit_profile", self.edit_profile))
        updater.dispatcher.add_handler(CommandHandler("create_profile", self.create_profile))
        updater.dispatcher.add_handler(CommandHandler("view_profile", self.view_profile))
        updater.dispatcher.add_handler(CommandHandler("select_profile", self.select_profile))
        updater.dispatcher.add_handler(CommandHandler("clear", self.clear))
        updater.dispatcher.add_handler(CommandHandler("list", self.list))
        updater.dispatcher.add_handler(CommandHandler("view_list", self.view_list))
        updater.dispatcher.add_handler(CommandHandler("select_list", self.select_list))
        updater.dispatcher.add_handler(
            MessageHandler(Filters.regex(r"^(/edit_[\d\D]+)$"), self.edit)
        )
        updater.dispatcher.add_handler(
            MessageHandler(Filters.regex(r"^(/view_[\d\D]+)$"), self.view)
        )
        updater.dispatcher.add_handler(
            MessageHandler(Filters.regex(r"^(/select_[\d\D]+)$"), self.select)
        )
        updater.dispatcher.add_handler(CommandHandler("add", self.add))
        updater.dispatcher.add_handler(
            MessageHandler(Filters.regex(r"^(/close_[\d\D]+)$"), self.close)
        )
        updater.dispatcher.add_handler(CommandHandler("actions", self.actions))

    @staticmethod
    def profile(update: Update, context: CallbackContext):
        reply_grid = [
            ["/create_profile", "/edit_profile"],
            ["/view_profile", "/select_profile"],
            ["/actions"],
            ["/dl"],
        ]
        reply_markup = ReplyKeyboardMarkup(reply_grid, one_time_keyboard=True, resize_keyboard=True)
        clear_text = "\t\t\t\t /clear \n"
        profile = BotGlobals.STORED_PROFILE_NAME
        stored_profile_text = (
            f"{'STORED: ' if not profile else ''}<b><u>{profile}</u></b>\n"
            f"{clear_text if profile else '' }"
        )
        menu_text = "Choose new command:"
        context.bot.send_message(
            text=f"{stored_profile_text}\n{menu_text}",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            chat_id=update.message.chat_id,
        )
        # update.message.reply_text(f"{stored_profile_text}\n{menu_text}", reply_markup=reply_markup,
        #                           parse_mode=ParseMode.HTML, allow_sending_without_reply=True)

    def actions(self, update: Update, context: CallbackContext):
        text = self.get_open_actions_as_text()
        update.message.reply_text(text=text, parse_mode=ParseMode.HTML)

    @staticmethod
    def get_open_actions_as_text() -> str:
        action_log = ProfileLog()
        open_actions_by_profile = action_log.by_profile_name()

        header = f"<b><u>Profile Actions - ({len(open_actions_by_profile)})</u></b>'"

        text_lines = [header]
        for profile_name, profile_actions in open_actions_by_profile.items():
            text_lines.append(f"{profile_name}:")
            for key, value in profile_actions.items():
                service = value["service"]
                value = value["value"]
                text_lines.append(f"\t\t\t\t{service}: {value}")
                text_lines.append(
                    f"\t\t\t\t\t\t> /{key.replace('open_', 'close_').replace(f'@{RISA_HELPER_BOT}', '')}"
                )

        return "\n".join(text_lines)

    def close(self, update: Update, context: CallbackContext):
        try:
            open_key_name = update.message.text.replace("/close_", "open_").replace(
                f"@{RISA_HELPER_BOT}", ""
            )
        except IndexError:
            return update.message.reply_text("Error: Missing Argument")
        action_log = ProfileLog()
        action_log.close_action(open_key_name=open_key_name)
        update.message.reply_text(
            f"Closed: '{open_key_name}' \n\n" f"{self.get_open_actions_as_text()}",
            parse_mode=ParseMode.HTML,
        )

    def clear(self, update: Update, context: CallbackContext):
        BotGlobals.STORED_PROFILE_NAME = None
        return self.profile(update, context)
