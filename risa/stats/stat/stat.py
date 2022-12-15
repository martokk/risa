from typing import Any, Dict, Union

from abc import ABC, abstractmethod


class Stat(ABC):
    def __init__(self, name: str, id_name: str) -> None:
        self.name = name
        self.id_name = id_name
        self._data = self.get_data()
        self._summary = self.get_summary_from_data(data=self._data)

    @staticmethod
    @abstractmethod
    def get_data() -> Any:
        return "return data"

    @staticmethod
    @abstractmethod
    def get_summary_from_data(data: Any) -> Dict[str, Union[str, float, int]]:
        return {
            "stat": "stat",
            "value": "value",
        }

    @property
    def stat(self) -> str:
        return self._summary["stat"]

    @property
    def value(self) -> str:
        return self._summary["value"]

    @property
    def view_details_text(self) -> str:
        return self.get_view_details_text(stat_name=self.name, data=self._data)

    @property
    def view_details_text_for_telegram(self) -> str:
        return self.get_view_details_text_for_telegram(stat_name=self.name, data=self._data)

    @property
    def view_details_text_for_cli(self) -> str:
        return self.get_view_details_text_for_cli(stat_name=self.name, data=self._data)

    @staticmethod
    @abstractmethod
    def get_view_details_text(stat_name: str, data: Any) -> str:
        """Display full details as text"""
        text = "\n".join(list(data))
        return f"{stat_name}\n\n{text}"

    def get_view_details_text_for_cli(self, stat_name: str, data: Any) -> str:
        """Display full details as text (formatted for CLI)"""
        return self.view_details_text

    def get_view_details_text_for_telegram(self, stat_name: str, data: Any) -> str:
        """Display full details as text (formatted for Telegram)"""
        return self.view_details_text
