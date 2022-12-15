from typing import Dict

import re
import time
from pathlib import Path

import yaml


class Utils:
    @staticmethod
    def import_yaml(file_path: str) -> dict:
        with open(file=file_path, mode="r") as file:
            return yaml.safe_load(file)

    @staticmethod
    def export_yaml(file_path: str, data: Dict, mode="w") -> None:
        with open(file=file_path, mode=mode) as file:
            yaml.safe_dump(data, stream=file, default_flow_style=False)

    @staticmethod
    def get_directory_files_folders(folder_path: Path):
        root_directory = Path(folder_path) if isinstance(folder_path, str) else folder_path
        files = []
        folders = []
        for path_object in root_directory.glob("**/*"):
            if path_object.is_file():
                files.append(path_object)
            elif path_object.is_dir():
                folders.append(path_object)
        return files, folders

    @staticmethod
    def convert_case_to_snakecase(text: str) -> str:
        try:
            return text.replace(" ", "_").lower()
        except AttributeError:
            pass

    @staticmethod
    def datetime_filename() -> str:
        return time.strftime("%y%m%d%H%M%S")

    @staticmethod
    def strip_special_characters(text: str) -> str:
        return re.sub("[^A-Za-z0-9\s]+", "", text)


class ViewMixIn:
    @staticmethod
    def print_horizontal_line() -> None:
        print("".ljust(50, "-"))
