from __future__ import annotations

from typing import Any, Dict, List, Optional

import datetime
import re
from abc import abstractmethod

from bs4 import ResultSet, Tag

from risa.common.utils import Utils
from risa.scrapers.scrapers import Scraper, ScraperCheckpoint


class ChanScraperProfile:
    def __init__(self) -> None:
        self._use_wget = False
        self.site_name = "Site Name"
        self.site_url = "Site URL"
        self.board_url_scheme = "{SITE_URL}/{BOARD_ID}"
        self.thread_url_scheme = "{SITE_URL}/{BOARD_ID}/res/{THREAD_ID}.html"
        self.post_url_scheme = "{SITE_URL}/{BOARD_ID}/res/{THREAD_ID}.html#{POST_ID}"
        self.search_image_hash_scheme = "{SITE_URL}/_/search/image/{IMAGE_HASH}/"

    # HELEPRS ####################################################################
    @staticmethod
    def _get_str_from_tag(tag: Any) -> str:
        if not tag:
            return ""
        return tag if isinstance(tag, str) else tag.text.strip()

    @staticmethod
    def url_generator(scheme: str, **kwargs) -> str:
        for k, v in kwargs.items():
            replace_str = "{" + f"{k.upper()}" + "}"
            scheme = scheme.replace(replace_str, v)
        return scheme

    def generate_board_url(self, site_url: str, board_id: str) -> str:
        return self.url_generator(
            scheme=self.board_url_scheme, site_url=site_url, board_id=board_id
        )

    def generate_thread_url(self, site_url: str, board_id: str, thread_id: str) -> str:
        return self.url_generator(
            scheme=self.thread_url_scheme, site_url=site_url, board_id=board_id, thread_id=thread_id
        )

    def generate_post_url(self, site_url: str, board_id: str, thread_id: str, post_id: str) -> str:
        return self.url_generator(
            scheme=self.post_url_scheme,
            site_url=site_url,
            board_id=board_id,
            thread_id=thread_id,
            post_id=post_id,
        )

    def generate_search_image_hash(self, site_url: str, image_hash: str) -> str:
        return self.url_generator(
            scheme=self.search_image_hash_scheme, site_url=site_url, image_hash=image_hash
        )

    # SCRAPER ####################################################################

    # BOARD ######################################################################
    @staticmethod
    def board_id_tag(page_tag: Tag) -> Tag:
        return page_tag.find("XXXXXXX", class_="XXXXXXX")

    def board_id_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)

    @staticmethod
    def board_name_tag(page_tag: Tag) -> Tag:
        return page_tag.find("XXXXXXX", class_="XXXXXXX")

    def board_name_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)

    # THREADS ######################################################################
    @staticmethod
    def thread_tags(page_tag: Tag) -> ResultSet:
        return page_tag.find_all("XXXXXXX", class_="XXXXXXX")

    # THREAD ######################################################################
    @staticmethod
    def op_post_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("XXXXXXX", class_="XXXXXXX")

    @staticmethod
    def post_tags(thread_tag: Tag) -> ResultSet:
        return thread_tag.find_all("XXXXXXX", class_="XXXXXXX")

    @staticmethod
    def thread_id_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("XXXXXXX", class_="XXXXXXX")

    def thread_id_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)

    @staticmethod
    def thread_url_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("XXXXXXX", class_="XXXXXXX")

    def thread_url_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)

    @staticmethod
    def thread_name_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("XXXXXXX", class_="XXXXXXX")

    def thread_name_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)

    @staticmethod
    def thread_name_fallback_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("XXXXXXX", class_="XXXXXXX")

    def thread_name_fallback_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)

    # POST ######################################################################
    @staticmethod
    def post_id_tag(post_tag: Tag) -> Tag:
        return post_tag.find("XXXXXXX", class_="XXXXXXX")

    def post_id_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)

    @staticmethod
    def post_url_tag(post_tag: Tag) -> Tag:
        return post_tag.find("XXXXXXX", class_="XXXXXXX")

    def post_url_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)

    @staticmethod
    def post_subject_tag(post_tag: Tag) -> Tag:
        return post_tag.find("XXXXXXX", class_="XXXXXXX")

    def post_subject_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)

    @staticmethod
    def post_author_tag(post_tag: Tag) -> Tag:
        return post_tag.find("XXXXXXX", class_="XXXXXXX")

    def post_author_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)

    @staticmethod
    def post_datetime_tag(post_tag: Tag) -> Tag:
        return post_tag.find("XXXXXXX", class_="XXXXXXX")

    @staticmethod
    def parse_datetime_scheme() -> str:
        return "%m/%d/%Y (%a) %H:%M:%S"

    @staticmethod
    def post_backlinks_tag(post_tag: Tag) -> Tag:
        return post_tag.find("XXXXXXX", class_="XXXXXXX")

    @staticmethod
    def post_backlink_tags(backlinks_tag: Tag) -> ResultSet:
        return backlinks_tag.find_all("XXXXXXX", class_="XXXXXXX")

    @staticmethod
    def post_backlink_str(backlink_tag: Tag) -> str:
        return backlink_tag.text

    @staticmethod
    def post_files_tag(post_tag: Tag) -> Tag:
        return post_tag.find("XXXXXXX", class_="XXXXXXX")

    @staticmethod
    def post_file_tags(files_tag: Tag) -> ResultSet:
        return files_tag.find_all("XXXXXXX", class_="XXXXXXX")

    @staticmethod
    def post_file_filename(file_tag: Tag) -> str:
        return file_tag["download"]

    def post_file_url(self, file_tag: Tag) -> str:
        return f"{self.site_url or ''}{file_tag['href']}"

    @staticmethod
    def post_body_tag(post_tag: Tag) -> Tag:
        return post_tag.find("XXXXXXX", class_="XXXXXXX")

    def post_body_str(self, tag: Tag) -> str:
        return self._get_str_from_tag(tag=tag)


class ChanScraperABC(ChanScraperProfile, Scraper):
    def __init__(self) -> None:
        super().__init__()
        self._validate_scraper_profile()
        self.site_id = None
        self.board_id = None
        self.board_name = None
        self.board_url = None
        self.threads = []
        self.checkpoint = None

    def site_data_as_dict(self) -> Dict:
        return {
            "site_name": self.site_name,
            "site_id": self.site_id,
            "site_url": self.site_url,
        }

    def board_data_as_dict(self) -> Dict:
        return {
            "board_name": self.board_name,
            "board_id": self.board_id,
            "board_url": self.board_url,
        }

    def thread_data_as_dict(self, thread_tag: Tag) -> Dict:
        return {
            "thread_name": self._get_thread_name(thread_tag=thread_tag),
            "thread_id": self._get_thread_id(thread_tag=thread_tag),
            "thread_url": self._get_thread_url(thread_tag=thread_tag),
        }

    def as_dict(self) -> Dict:
        return {
            "site": self.site_data_as_dict(),
            "board": self.board_data_as_dict(),
        }

    @property
    def sorted_threads(self) -> List[Dict]:
        return sorted(
            self.threads, key=lambda thread: int(thread["thread"]["thread_id"]), reverse=False
        )

    def scrape(self, page_tag: Tag) -> Dict:
        self.site_id = self.generate_site_id()
        self.board_id = self._get_board_id()
        self.board_name = self._get_board_name()
        self.board_url = self._get_board_url()
        self.threads = self._get_threads()
        self.checkpoint = self._get_checkpoint()
        return self.as_dict()

    def _validate_scraper_profile(self) -> None:
        if self.site_url != self._get_base_url():
            raise AssertionError(
                "site_url from scrape_url() is different that ChanScraperProfile().site_name"
            )

    def generate_site_id(self, site_name=None) -> str:
        return Utils.convert_case_to_snakecase(text=site_name or self.site_name)

    def _get_board_id(self, page_tag: Tag = None) -> str:
        return self.board_id_str(tag=self.board_id_tag(page_tag=page_tag or self._page_tag))

    def _get_board_name(self, page_tag: Tag = None) -> str:
        return self.board_name_str(tag=self.board_name_tag(page_tag=page_tag or self._page_tag))

    def _get_board_url(self, url: str = None) -> str:
        return re.search(
            "^(http[s]?://[a-zA-Z0-9\s_.\-()?=%]+\.[\w]{2,4}/[\w]{1,5})", url or self._url
        ).group()

    def _get_threads(self, page_tag: Tag = None) -> List:
        thread_tags = self.thread_tags(page_tag=page_tag or self._page_tag)
        return [self._get_thread(thread_tag=thread_tag) for thread_tag in thread_tags]

    def _get_thread(self, thread_tag: Tag) -> Dict:
        op_post_tag = self.op_post_tag(thread_tag=thread_tag)
        op_post = self._get_post(post_tag=op_post_tag)

        posts = [op_post]
        post_tags = self.post_tags(thread_tag=thread_tag)
        posts.extend(self._get_post(post_tag=post_tag) for post_tag in post_tags)

        return {
            "site": self.site_data_as_dict(),
            "board": self.board_data_as_dict(),
            "thread": self.thread_data_as_dict(thread_tag=thread_tag),
            "posts": posts,
        }

    def _get_thread_id(self, thread_tag: Tag) -> str:
        return self.thread_id_str(tag=self.thread_id_tag(thread_tag=thread_tag))

    def _get_thread_name(self, thread_tag: Tag) -> str:
        return self.thread_name_str(
            tag=self.thread_name_tag(thread_tag=thread_tag)
        ) or self.thread_name_fallback_str(tag=self.thread_name_fallback_tag(thread_tag=thread_tag))

    def _get_thread_url(self, thread_tag: Tag) -> str:
        return self.thread_url_str(tag=self.thread_url_tag(thread_tag=thread_tag))

    def _get_post(self, post_tag: Tag) -> Dict:
        subject = self._get_post_subject(post_tag=post_tag)
        body = self._get_post_body(post_tag=post_tag)
        message = self._get_message(subject=subject, body=body)
        return {
            "post_id": self._get_post_id(post_tag=post_tag),
            "post_url": self._get_post_url(post_tag=post_tag),
            "subject": subject,
            "author": self._get_post_author(post_tag=post_tag),
            "datetime": self._get_post_datetime(post_tag=post_tag),
            "backlinks": self._get_post_backlinks(post_tag=post_tag),
            "files": self._get_post_files(post_tag=post_tag),
            "body": body,
            "message": message,
        }

    @staticmethod
    def _get_message(subject: str, body: str) -> str:
        if not subject:
            return body
        if not body:
            return subject
        if subject == body:
            return body
        return f"{subject}\n{body}"

    def _get_post_id(self, post_tag: Tag) -> str:
        return self.post_id_str(tag=self.post_id_tag(post_tag=post_tag))

    def _get_post_url(self, post_tag: Tag) -> str:
        return self.post_url_str(tag=self.post_url_tag(post_tag=post_tag))

    def _get_post_subject(self, post_tag: Tag) -> str:
        return self.post_subject_str(tag=self.post_subject_tag(post_tag=post_tag))

    def _get_post_author(self, post_tag: Tag) -> str:
        return self.post_author_str(tag=self.post_author_tag(post_tag=post_tag))

    def _get_post_datetime(self, post_tag: Tag) -> Optional[datetime.datetime]:
        tag = self.post_datetime_tag(post_tag=post_tag)
        if not tag:
            return None
        if isinstance(tag, datetime.datetime):
            return tag
        try:
            strdate = tag.text.strip()  # '12/03/2021 (Fri) 21:24:55'
            dt = datetime.datetime.strptime(strdate, self.parse_datetime_scheme())
        except AttributeError:
            dt = datetime.datetime.strptime(str(tag), self.parse_datetime_scheme())
        return dt

    def _get_post_backlinks(
        self, post_tag: Tag
    ) -> List[str]:  # TODO: Doesn't work. Maybe javascript?
        backlinks_tag = self.post_backlinks_tag(post_tag=post_tag)
        if not backlinks_tag:
            return []
        backlink_tags = self.post_backlink_tags(backlinks_tag=backlinks_tag)
        return [self.post_backlink_str(backlink_tag=backlink_tag) for backlink_tag in backlink_tags]

    def _get_post_files(self, post_tag: Tag) -> List[Dict[str, str]]:
        files_tag = self.post_files_tag(post_tag=post_tag)
        if not files_tag:
            return []
        file_tags = self.post_file_tags(files_tag=files_tag)
        return [
            {
                "filename": self.post_file_filename(file_tag=file_tag),
                "url": self.post_file_url(file_tag=file_tag),
            }
            for file_tag in file_tags
        ]

    def _get_post_body(self, post_tag: Tag) -> str:
        return self.post_body_str(tag=self.post_body_tag(post_tag=post_tag))

    @abstractmethod
    def _get_checkpoint(self) -> str:
        return "XXXXXXX"

    @abstractmethod
    def get_new_since_checkpoint(self, checkpoint: str) -> List[Any]:
        """Returns list of dew Objects since the checkpoint."""
        return ["XXXXXXXXXXXXXXXXXXXXXXXXXXXX"]


class ChanBoardScraper(ScraperCheckpoint, ChanScraperABC):
    def as_dict(self) -> Dict:
        return {**super().as_dict(), "threads": self.threads}

    def _get_checkpoint(self) -> str:
        if not self.threads:
            return None
        return str(max(int(thread["thread"]["thread_id"]) for thread in self.threads))

    def get_new_since_checkpoint(self, checkpoint: str) -> List[Any]:
        data = []
        for thread in self.sorted_threads:
            if int(thread["thread"]["thread_id"]) > int(checkpoint):
                post = thread["posts"][0]
                if int(post["post_id"]) > int(checkpoint):
                    data.append(
                        {
                            "site": self.site_data_as_dict(),
                            "board": self.board_data_as_dict(),
                            "thread": thread["thread"],
                            **post,
                        }
                    )
        return data


class ChanThreadScraper(ScraperCheckpoint, ChanScraperABC):
    def as_dict(self) -> Dict:
        return {**super().as_dict(), "thread": self.thread["thread"], "posts": self.thread["posts"]}

    @property
    def thread(self) -> Dict:
        return self.threads[0]

    @property
    def thread_id(self) -> str:
        return self.thread["thread"]["thread_id"]

    @property
    def thread_url(self) -> str:
        return self.thread["thread"]["thread_url"]

    @property
    def thread_name(self) -> str:
        return self.thread["thread"]["thread_name"]

    @property
    def posts(self) -> List:
        return self.thread["posts"]

    @property
    def thread_posts(self) -> List:
        return self.thread["posts"]

    def _get_checkpoint(self) -> str:
        return str(max(int(post["post_id"]) for post in self.posts))

    def get_new_since_checkpoint(self, checkpoint: str) -> List[Any]:
        return [
            {
                "site": self.site_data_as_dict(),
                "board": self.board_data_as_dict(),
                "thread": self.thread["thread"],
                **post,
            }
            for post in self.posts
            if int(post["post_id"]) > int(checkpoint)
        ]


class ChanSearchScraper(ChanBoardScraper):
    def __init__(self) -> None:
        super().__init__()
        self.files = []
        self.results = []

    def board_id_str(self, tag: Tag):
        return "_"

    def as_dict(self) -> Dict:
        return {**super().as_dict(), "files": self.files, "results": self.results}

    @property
    def total_results(self) -> int:
        return self.results.__len__()

    @property
    def total_files(self) -> int:
        return self.files.__len__()

    def search(self, **kwargs) -> Dict:
        return self.scrape_url(**kwargs)

    def search_image_hash(self, image_hash: str) -> Dict:
        return self.scrape_url(image_hash=image_hash)

    def scrape_url(self, image_hash: str, url: str = None) -> Dict:
        if image_hash:
            url = self.generate_search_image_hash(site_url=self.site_url, image_hash=image_hash)

        if not url:
            raise ValueError("Could not determain 'url'. 'url' can not be None.")
        data = super().scrape_url(url=url)
        self.parse_data(data=data)
        return self.as_dict()

    def parse_data(self, data: dict):
        files = []
        for thread in data["threads"]:
            post = thread["posts"][0]
            for file in post["files"]:
                files.append(
                    {
                        "filename": file["filename"],
                        "url": file["url"],
                        "post_id": post["post_id"],
                        "post_url": post["post_url"],
                        "datetime": post["datetime"],
                        "subject": post["subject"],
                        "body": post["body"],
                    }
                )
        self.files = files
        self.results = self.threads
