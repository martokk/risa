import datetime
from typing import Union

from action_logs.action_log import ActionLog
from common import constants
from telegram_bots.risa_helper_bot.main import BotGlobals


class DownloadLog(ActionLog):
    def __init__(self) -> None:
        super().__init__(file_path=constants.DOWNLOAD_LOG_FILE)

    def open_action(self, profile_name: str, media_data: dict) -> Union[bool, str]:
        open_key_name = self._get_open_key_name()
        data = {
            open_key_name: {
                'timestamp': datetime.datetime.now(),
                'profile_name': profile_name,
                'media_data': media_data,
            }
        }
        if self.append_data_to_log(data=data):
            return open_key_name
        return False

    @staticmethod
    def get_open_actions_as_text() -> str:
        action_log = DownloadLog()
        open_actions_by_profile = action_log.by_profile_name()

        header = f"<b><u>Profile Download Actions - ({len(open_actions_by_profile)})</u></b>'"

        text_lines = [header]
        for profile_name, actions in open_actions_by_profile.items():
            text_lines.append(f"{profile_name}:")
            for media_type in BotGlobals.MEDIA_TYPES:
                media_type_actions = \
                    [data for key, data in actions.items() if data['media_data']['media_type'] == media_type]
                len_media_type_actions = len(media_type_actions)
                if len_media_type_actions > 0:
                    text_lines.append(f"\t\t\t\t{media_type}: {len_media_type_actions}")

            text_lines.append(f"\t\t\t\t /dl_{profile_name}")
            text_lines.append(f"\t\t\t\t /dlall_{profile_name}")

        return '\n'.join(text_lines)
