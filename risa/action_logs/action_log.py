from typing import Dict

import datetime
from abc import abstractmethod
from pathlib import Path

import yaml
from common.utils import Utils
from yaml.representer import RepresenterError


class ActionLog:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def append_data_to_log(self, data: dict) -> bool:
        with open(self.file_path, "a") as file:
            try:
                yaml.safe_dump(data, stream=file, default_flow_style=False)
            except RepresenterError as e:
                raise RepresenterError(e)
        return True

    def import_data_from_yaml(self) -> dict:
        return Utils().import_yaml(file_path=str(self.file_path))

    @abstractmethod
    def open_action(self, *args, **kwargs) -> bool:
        data = {"open_key": {"data_key1": "data_value1"}}
        return self.append_data_to_log(data=data)

    def close_action(self, open_key_name: str) -> bool:
        open_actions = self.get_filtered_by_status(status="open")
        if not open_actions.get(open_key_name):
            print("already closed")
            return True
        data = {
            self._get_close_key_name(open_key_name=open_key_name): {
                "timestamp": datetime.datetime.now(),
                "open_key_name": open_key_name,
            }
        }
        return self.append_data_to_log(data=data)

    @staticmethod
    def _get_open_key_name(*args, **kwargs) -> str:
        return f"open_{Utils().datetime_filename()}"

    @staticmethod
    def _get_close_key_name(open_key_name: str) -> str:
        return open_key_name.replace("open_", "close_")

    def get_filtered_by_status(self, status: str = "all") -> Dict:
        imported_yaml_data = self.import_data_from_yaml()

        # Import 'open_' actions in yaml file
        actions = {key: value for key, value in imported_yaml_data.items() if "open_" in key}

        # Add status to action
        for key, value in actions.items():
            closed_key_name = self._get_close_key_name(open_key_name=key)
            actions[key]["_status"] = (
                "closed" if imported_yaml_data.get(closed_key_name) else "open"
            )

        # Filter by 'status' argument
        if status != "all":
            actions = {
                key: value
                for key, value in actions.items()
                if value["_status"].lower() == status.lower()
            }

        return actions

    def get_actions(self, status="all") -> Dict:
        return self.get_filtered_by_status(status=status)

    def get_all(self) -> Dict:
        return self.get_filtered_by_status(status="all")

    def get_open(self) -> Dict:
        return self.get_filtered_by_status(status="open")

    @staticmethod
    @abstractmethod
    def get_open_actions_as_text() -> str:
        pass

    def get_closed(self) -> Dict:
        return self.get_filtered_by_status(status="closed")

    def by_profile_name(self) -> Dict:
        open_actions = self.get_open()

        actions_by_profile = {}
        for key, value in open_actions.items():
            actions_by_profile[value["profile_name"]] = actions_by_profile.get(
                value["profile_name"], {}
            )
            actions_by_profile[value["profile_name"]][key] = value

        return actions_by_profile

    def get_new_profiles(self) -> Dict:
        return {k: v for k, v in self.by_profile_name().items() if "new_profile_" in k}

    def get_actions_for_profile(self, profile_name: str) -> Dict:
        actions_by_profile = self.by_profile_name()
        return actions_by_profile.get(profile_name, {})
