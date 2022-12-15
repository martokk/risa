import datetime

from action_logs.action_log import ActionLog
from common import constants


class ProfileLog(ActionLog):
    def __init__(self) -> None:
        super().__init__(file_path=constants.PROFILE_LOG_FILE)

    def open_action(self, profile_name: str, service: str, command: str, value: str) -> bool:
        data = {
            self._get_open_key_name(profile_name=profile_name): {
                "timestamp": datetime.datetime.now(),
                "profile_name": profile_name,
                "service": service,
                "command": command,
                "value": value,
            }
        }
        return self.append_data_to_log(data=data)

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
                text_lines.append(f"\t\t\t\t\t\t> /{key.replace('open_', 'close_')}")

        return "\n".join(text_lines)


if __name__ == "__main__":
    action_log = ProfileLog()
    by_profile = action_log.by_profile_name()
    print(by_profile)
    print(by_profile)
