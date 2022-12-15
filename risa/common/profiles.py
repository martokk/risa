from typing import Dict, List, Optional, Union

import datetime
from pathlib import Path

from risa.common import constants
from risa.common.utils import Utils
from risa.config import config
from risa.services.expander import Expander


class Profile:
    def __init__(self) -> None:
        self.profile_yaml_path = None
        self.profile_path = None
        self.data = None
        self.profile_name = None
        self.profile_type = None
        self.validation = None

    @property
    def name(self) -> str:
        return self.data.get("name")

    @property
    def folder_name(self) -> str:
        return self.profile_path.name

    @property
    def name_or_folder(self) -> str:
        return self.name or self.folder_name

    def __repr__(self) -> str:
        return f"{self.name_or_folder} ({self.profile_type})"

    def __str__(self) -> str:
        return f"{self.name_or_folder} ({self.profile_type})"

    def as_dict(self) -> Dict:
        return {
            "profile_yaml_path": str(self.profile_yaml_path),
            "profile_path": str(self.profile_path),
            "data": self.data,
            "profile_name": self.profile_name,
            "profile_type": self.profile_type,
            "validation": {
                "errors": self.validation.get("errors")
                if isinstance(self.validation, dict)
                else self.validation.errors,
                "warnings": self.validation.get("warnings")
                if isinstance(self.validation, dict)
                else self.validation.warnings,
            },
        }


class ProfileFromYaml(Profile):
    def __init__(self, profile_yaml_path: Union[str, Path], profile_type: str):
        super().__init__()
        self.profile_yaml_path = (
            profile_yaml_path if isinstance(profile_yaml_path, Path) else Path(profile_yaml_path)
        )
        self.profile_path = self.profile_yaml_path.parent
        self.data = self.get_data()
        self.profile_name = self.get_profile_name(
            file_path=self.profile_yaml_path, data_name=self.data.get("name")
        )
        self.profile_type = profile_type
        self.validation = ValidateProfile(self)

    def get_data(self) -> Dict:
        data = Utils.import_yaml(file_path=str(self.profile_yaml_path))
        return {k: v for k, v in data.items() if v is not None}

    def get_profile_name(self, file_path: Path, data_name: str) -> str:
        if data_name is None:
            data_name = self.profile_path.name

        data_name = Utils.strip_special_characters(text=data_name)

        return Utils.convert_case_to_snakecase(text=data_name)


class ProfileFromCache(Profile):
    def __init__(self, profile_cache: dict):
        super().__init__()
        self.profile_yaml_path = profile_cache.get("profile_yaml_path")
        self.profile_path = profile_cache.get("profile_path")
        self.data = profile_cache.get("data")
        self.profile_name = profile_cache.get("profile_name")
        self.profile_type = profile_cache.get("profile_type")
        self.validation = profile_cache.get("validation")


class ValidateProfile:
    def __init__(self, profile: Profile) -> None:
        self.errors = []
        self.warnings = []
        self.validate(profile=profile)

    def validate(self, profile: Profile) -> None:
        self.is_missing(field="name", profile_data=profile.data, append_to=self.errors)
        self.is_missing(field="usernames", profile_data=profile.data, append_to=self.errors)
        self.is_found(field="socials", profile_data=profile.data, append_to=self.warnings)
        self.is_found(field="todo", profile_data=profile.data, append_to=self.warnings)
        self.attribute_value_contains(
            value="http", profile_data=profile.data, append_to=self.warnings
        )

    @staticmethod
    def is_missing(field: str, profile_data: dict, append_to: List) -> None:
        if profile_data.get(field) is None:
            append_to.append(f"Missing '{field}'")

    @staticmethod
    def is_found(field: str, profile_data: dict, append_to: List) -> None:
        if profile_data.get(field) is not None:
            append_to.append(f"Data found in field '{field}'")

    @staticmethod
    def attribute_value_contains(value: str, profile_data: dict, append_to: List) -> None:
        if any(value in str(v) for k, v in profile_data.items()):
            append_to.append(f"Value '{value}' found in profile attributes.")

    @property
    def total_issues(self) -> int:
        return self.errors.__len__() + self.warnings.__len__()

    @property
    def found_issues(self) -> int:
        return self.total_issues > 0

    @property
    def found_errors(self) -> int:
        return self.errors.__len__() > 0

    @property
    def found_warnings(self) -> int:
        return self.warnings.__len__() > 0


class ProfilesList(List[Profile]):
    def get_profiles_by_type(self, profile_type: str) -> List[Profile]:
        return [profile for profile in self if profile_type in profile.profile_type]

    def get_list_of_profile_names(self) -> List[str]:
        return [profile.profile_name for profile in self]

    def get_by_attribute(self, attribute: str) -> Dict[str, List[str]]:
        rtn = {}
        for profile in self:
            attribute_data = profile.data.get(attribute)
            if attribute_data is None:
                continue
            if isinstance(attribute_data, str):
                attribute_data = [attribute_data]

            attribute_data = Expander(service=attribute).expand(attribute_data)
            rtn[profile.profile_name] = attribute_data
        return rtn

    def as_dict(self, profile_type: Optional[str] = None) -> Dict:
        profiles = self.get_profiles_by_type(profile_type=profile_type) if profile_type else self
        rtn = {profile.profile_name: profile.as_dict() for profile in profiles}
        return rtn

    def get_profile(self, profile_name: str):
        for profile in self:
            if profile.profile_name == profile_name:
                return profile
        return None


class ProfilesFromCache(ProfilesList):
    def __init__(self) -> None:
        super().__init__()
        self.last_updated = None
        self._get_init_profiles()

    def _get_init_profiles(self) -> None:
        cache = Utils.import_yaml(file_path=constants.CACHE_PROFILES_FILE)
        self.last_updated = cache.pop("last_updated")
        self.extend(
            [ProfileFromCache(profile_cache=profile_cache) for _, profile_cache in cache.items()]
        )


class ProfilesFromActionLog(ProfilesList):
    def __init__(self) -> None:
        super().__init__()
        self.last_updated = None
        self._get_init_profiles()

    def _get_init_profiles(self) -> None:
        self.last_updated = datetime.datetime.now()

        cache = Utils.import_yaml(file_path=constants.CACHE_PROFILES_FILE)
        self.extend(
            [ProfileFromCache(profile_cache=profile_cache) for _, profile_cache in cache.items()]
        )


class ProfilesFromYaml(ProfilesList):
    def __init__(self) -> None:
        super().__init__()
        self._get_init_profiles()
        self.export_to_cache()

    def _get_init_profiles(self, folder_names: list = config.RISA_FOLDERS) -> None:
        folder_names = [folder_names] if isinstance(folder_names, str) else folder_names
        for folder_name in folder_names:
            folder_path = constants.RISA_PROFILES_PATH / folder_name
            self.extend(
                self.load_profiles_from_folder_path(
                    folder_path=folder_path, folder_name=folder_name
                )
            )

    @staticmethod
    def load_profiles_from_folder_path(folder_path: Path, folder_name: str) -> List:
        list_profiles = list(folder_path.parent.glob(f"{folder_name}/*/user.yaml"))
        profiles = [
            ProfileFromYaml(profile_yaml_path=profile_path, profile_type=folder_name)
            for profile_path in list_profiles
        ]

        list_wip_profiles = list(
            folder_path.parent.glob(f"{folder_name}/{constants.WIP_FOLDERNAME}/*/user.yaml")
        )
        wip_profiles = [
            ProfileFromYaml(profile_yaml_path=profile_path, profile_type=f"{folder_name}__wip__")
            for profile_path in list_wip_profiles
        ]
        profiles.extend(wip_profiles)

        list_no_nudes_profiles = list(
            folder_path.parent.glob(f"{folder_name}/{constants.NO_NUDES_FOLDERNAME}/*/user.yaml")
        )
        no_nudes_profiles = [
            ProfileFromYaml(
                profile_yaml_path=profile_path, profile_type=f"{folder_name}__no_nudes__"
            )
            for profile_path in list_no_nudes_profiles
        ]
        profiles.extend(no_nudes_profiles)

        list_unknown_profiles = list(
            folder_path.parent.glob(f"{folder_name}/{constants.UNKNOWN_FOLDERNAME}/*/user.yaml")
        )
        unknown_profiles = [
            ProfileFromYaml(
                profile_yaml_path=profile_path, profile_type=f"{folder_name}__unknown__"
            )
            for profile_path in list_unknown_profiles
        ]
        profiles.extend(unknown_profiles)

        return profiles

    def export_to_cache(self) -> None:
        data = self.as_dict()
        data["last_updated"] = datetime.datetime.now()
        Utils().export_yaml(file_path=constants.CACHE_PROFILES_FILE, data=data)

        archive_filename = f"_archive_profiles_{Utils().datetime_filename()}.yaml"
        Utils().export_yaml(file_path=constants.CACHE_PATH / archive_filename, data=data)


class Profiles(ProfilesFromYaml):
    pass


if __name__ == "__main__":
    _profiles = Profiles()
