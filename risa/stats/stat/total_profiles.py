from typing import Any, Dict, List, Union

from risa.common.profiles import ProfilesFromCache
from risa.stats.stat.stat import Stat


class TotalCachedProfilesStat(Stat):
    def __init__(self) -> None:
        """Stat configuration and init"""
        name = "Total Cached Profiles"
        id_name = "total_profiles"
        super().__init__(name=name, id_name=id_name)

    @staticmethod
    def get_data() -> List[str]:
        """Returns a LIST of cached profile_names"""
        profiles = ProfilesFromCache()
        return profiles.get_list_of_profile_names()

    @staticmethod
    def get_summary_from_data(data: Any) -> Dict[str, Union[str, float, int]]:
        """Returns a dict of stat and value from self._data"""
        return {
            "stat": "Total Cached Profiles",
            "value": data.__len__(),
        }

    @staticmethod
    def get_view_details_text(stat_name: str, data: Any) -> str:
        text = "\n".join(list(data))
        return f"{stat_name}\n\n{text}"
