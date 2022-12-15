from typing import Any, Dict, List, Union

import datetime
import glob
import os
import subprocess
from abc import abstractmethod
from pathlib import Path

from common.constants import IMAGE_METADATA_FILE, RISA_PROFILES_PATH, WIP_FOLDERNAME
from common.utils import Utils
from scrapers.sites.archived_moe import ArchivedMoeSearchScraper


class ImportExportYaml:
    @abstractmethod
    def __init__(self) -> None:
        self._data = {}

    def _load_yaml(self) -> None:
        self._data = Utils().import_yaml(file_path=IMAGE_METADATA_FILE) or {}

    def _export_yaml(self) -> None:
        return Utils().export_yaml(file_path=IMAGE_METADATA_FILE, data=self._data)

    def _load(self, image_hash: str):
        if not image_hash:
            raise ValueError("image_hash can not be None.")
        if not self._data:
            self._load_yaml()
        return self._data.get(image_hash)

    def get(self, key: str, image_hash: str):
        if not image_hash:
            raise ValueError("image_hash can not be None.")
        return self._data.get(image_hash, {}).get(key)

    def update(self, data: dict, image_hash: str):
        if not image_hash:
            raise ValueError("image_hash can not be None.")
        self._data[image_hash] = self._data.get(image_hash, {})
        return self._data[image_hash].update(data)

    def save(self) -> None:
        return self._export_yaml()


class ImageFolderCrawler(ImportExportYaml):
    def __init__(self) -> None:
        pass

    def crawl_folder(self, folder_path: Union[Path, str], recursive=False):
        folder_paths = [x[0] for x in os.walk(str(folder_path))]

        if not recursive:
            folder_paths = [folder_paths[0]]

        for folder_path in folder_paths:

            folder_path = Path(folder_path)
            if not folder_path.is_dir():
                raise TypeError("folder_path is not a folder")
            image_paths = self._get_image_paths_from_folder(
                folder_path=folder_path, recursive=False
            )

            crawl_data = {}
            for image_path in image_paths:
                image_data = self.process_image(image_path=image_path)
                crawl_data[str(image_path)] = image_data.as_dict()

            images_metadata_file = folder_path / "images_metadata.yaml"
            if crawl_data:
                Utils().export_yaml(file_path=str(images_metadata_file), data=crawl_data)

    @staticmethod
    def _get_image_paths_from_folder(folder_path: Path, recursive=False) -> List:
        if not folder_path.is_dir():
            raise TypeError("folder_path is not a folder")
        exts = ["png", "jpg", "jpeg", "gif"]
        files = []
        [files.extend(glob.glob(f"{folder_path}/*.{ext}", recursive=recursive)) for ext in exts]
        return files

    @staticmethod
    def process_image(image_path: Path):
        image_path = Path(image_path)
        if image_path.is_dir():
            raise TypeError("image_path is not a file.")
        image = ImageMetaData(file_path=image_path)
        image.process_image()
        return image


class ImageMetaData(ImportExportYaml):
    def __init__(self, file_path: Union[str, Path]) -> None:
        self._data = {}
        self.file_path = Path(file_path)
        self.image_hash = None

    def as_dict(self) -> Dict:
        return {
            "file_path": str(self.file_path),
            "file_name": str(self.file_name),
            "folder_name": str(self.file_path.parent),
            "image_hash": self.image_hash,
            "md5": self.md5sum,
            "search_results": self.search_results,
        }

    @property
    def folder_name(self) -> Path:
        return self.file_path.parent

    @property
    def search_results(self) -> Path:
        return self.get(image_hash=self.image_hash, key="search_results")

    @property
    def file_name(self) -> str:
        return self.file_path.name

    @property
    def md5sum(self) -> str:
        return self.get(image_hash=self.image_hash, key="md5sum")

    def process_image(self, dry_run=False) -> dict:
        self.image_hash = self.get_image_hash(file_path=self.file_path)
        self._load(image_hash=self.image_hash)

        if not self.get(image_hash=self.image_hash, key="md5sum"):
            self.update(
                image_hash=self.image_hash,
                data={"md5sum": self.get_md5sum(file_path=self.file_path)},
            )

        self._search()

        if not dry_run:
            self.save()
        return self.as_dict()

    @staticmethod
    def get_image_hash(file_path: Union[str, Path]) -> str:
        command = f'md5sum "{Path(file_path)}"' + " | awk '{print $1}' | xxd -r -p | base64"
        return subprocess.check_output(command, shell=True).strip().decode()

    @staticmethod
    def get_md5sum(file_path: Union[str, Path]) -> str:
        command = f'md5sum "{Path(file_path)}"' + " | awk '{print $1}'"
        return subprocess.check_output(command, shell=True).strip().decode()

    def _search(self) -> None:
        existing_data = self._load(image_hash=self.image_hash)

        if not existing_data.get("archivedmoe"):
            results = ArchivedMoeResults(image_hash=self.image_hash).results
            self.update(
                image_hash=self.image_hash, data={"search_results": {"archivedmoe": results}}
            )


class RevImgSearchResults:
    def __init__(self, image_hash: str) -> None:
        self.image_hash = image_hash
        self.results = self._get_results()

    @abstractmethod
    def _get_results(self) -> List[Dict[str, Any]]:
        return [
            {
                "filename": "XXXXXXXXXXXXXXXXXXX.jpg",
                "url": "https://www.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.jpg",
                "post_id": "XXXXXXXXXXXXXXXXXXX",
                "post_url": "https://XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "datetime": datetime.datetime(2022, 4, 29, 21, 9, 35),
                "subject": "XXXXXXXXXXXXXXXXXXX",
                "body": "XXXXXXXXXXXXXXXXXXX",
            }
        ]


class ArchivedMoeResults(RevImgSearchResults):
    def __init__(self, image_hash) -> None:
        super().__init__(image_hash=image_hash)

    def _get_results(self) -> List[Dict[str, Any]]:
        scraper = ArchivedMoeSearchScraper()
        scraper.search_image_hash(image_hash=self.image_hash)
        return scraper.files


if __name__ == "__main__":
    folder_path = RISA_PROFILES_PATH / "kenosha" / WIP_FOLDERNAME
    ImageFolderCrawler().crawl_folder(folder_path=folder_path, recursive=True)
