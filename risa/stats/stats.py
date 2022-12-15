from typing import Any, Callable, Dict, List

from risa.stats.stat.stat import Stat
from risa.stats.stat.total_errors import TotalCachedErrors
from risa.stats.stat.total_profiles import TotalCachedProfilesStat
from risa.stats.stat.total_warnings import TotalCachedWarnings


class Stats:
    def __init__(self) -> None:
        self._stats = [
            TotalCachedProfilesStat,
            TotalCachedErrors,
            TotalCachedWarnings,
        ]
        self._data = self.get_data_from_stats(stats=self._stats)

    @staticmethod
    def get_data_from_stats(stats: List[Callable]) -> Dict[str, Dict[str, Any]]:
        data = {}
        for _stat in stats:
            stat: Stat = _stat()
            data[stat.id_name] = {
                "id_name": stat.id_name,
                "stat": stat.stat,
                "value": stat.value,
                "callable": _stat,
            }
        return data

    @property
    def summary_text(self) -> str:
        return self.get_summary_text(data=self._data)

    @staticmethod
    def get_summary_text(data: Any) -> str:
        """Display full details as text"""
        header = "Summary of All Stats: \n"
        lines = [f"{summary['stat']}: {summary['value']}" for id_name, summary in data.items()]
        return "\n".join([header, *lines])

    def get_view_details_text(self, id_name) -> str:
        text = "None"
        for _id_name, _summary in self._data.items():
            if _id_name == id_name:
                stat: Stat = _summary["callable"]()
                text = stat.view_details_text_for_telegram

        return text


class StatsCLI:
    pass


class StatsTelegram(Stats):
    @staticmethod
    def get_data_from_stats(stats: List[Callable]) -> Dict[str, Dict[str, Any]]:
        data = Stats.get_data_from_stats(stats=stats)
        for id_name, stat_summary in data.items():
            data[id_name]["telegram_command"] = f"/stat_{id_name}"
        return data

    @staticmethod
    def get_summary_text(data: Any) -> str:
        """Display full details as text"""
        header = "Summary of All Stats: \n"
        lines = [
            f"{summary['stat']}: {summary['value']} \n\t\t\t\t {summary['telegram_command']} \n"
            for id_name, summary in data.items()
        ]
        return "\n".join([header, *lines])


if __name__ == "__main__":
    print(Stats().summary_text)
