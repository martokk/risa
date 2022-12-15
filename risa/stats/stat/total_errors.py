from typing import Any, Dict, List, Union

from risa.common.profiles import ProfilesFromCache
from risa.stats.stat.stat import Stat


class TotalCachedErrors(Stat):
    def __init__(self) -> None:
        """Stat configuration and init"""
        name = "Total Cached Errors"
        id_name = "total_errors"
        super().__init__(name=name, id_name=id_name)

    @staticmethod
    def get_data() -> Dict[str, Dict[str, List]]:
        """Returns a LIST of cached profile_names"""
        profiles = ProfilesFromCache()
        return {
            profile.profile_name: profile.validation["errors"]
            for profile in profiles
            if profile.validation["errors"]
        }

    @staticmethod
    def get_summary_from_data(data: Any) -> Dict[str, Union[str, float, int]]:
        """Returns a dict of stat and value from self._data"""
        return {
            "stat": "Total Cached Errors",
            "value": data.__len__(),
        }

    @staticmethod
    def get_view_details_text(stat_name: str, data: Dict) -> str:
        lines = []
        for profile_name, list_errors in data.items():
            lines += [f"{profile_name}:"]
            for error in list_errors:
                lines += [f"\t\t- {error}:"]
            lines += [" "]

        text = "\n".join(lines)
        return f"{stat_name}\n\n{text}"
