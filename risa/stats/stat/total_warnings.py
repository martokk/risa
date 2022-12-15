from typing import Any, Dict, List, Union

from risa.common.profiles import ProfilesFromCache
from risa.stats.stat.stat import Stat


class TotalCachedWarnings(Stat):
    def __init__(self) -> None:
        """Stat configuration and init"""
        name = "Total Cached Warnings"
        id_name = "total_warnings"
        super().__init__(name=name, id_name=id_name)

    @staticmethod
    def get_data() -> Dict[str, Dict[str, List]]:
        """Returns a LIST of cached profile_names"""
        profiles = ProfilesFromCache()
        return {
            profile.profile_name: profile.validation["warnings"]
            for profile in profiles
            if profile.validation["warnings"]
        }

    @staticmethod
    def get_summary_from_data(data: Any) -> Dict[str, Union[str, float, int]]:
        """Returns a dict of stat and value from self._data"""
        return {
            "stat": "Total Cached Warnings",
            "value": data.__len__(),
        }

    @staticmethod
    def get_view_details_text(stat_name: str, data: Dict) -> str:
        lines = []
        for profile_name, list_warnings in data.items():
            lines += [f"{profile_name}:"]
            for warning in list_warnings:
                lines += [f"\t\t- {warning}:"]
            lines += [" "]

        text = "\n".join(lines)
        return f"{stat_name}\n\n{text}"
