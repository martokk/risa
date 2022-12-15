from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, Union

import datetime
import re
from abc import ABC, abstractmethod, abstractstaticmethod

import bs4
from bs4 import ResultSet, Tag

from risa.common.utils import Utils
from risa.scrapers.scrapers import Scraper, ScraperCheckpoint


class OLD_ChanBoardScraper(OLD_ChanScraper):
    def __init__(self) -> None:
        super().__init__()
        self.threads = []
        self.threads_ids = []

    def as_dict(self) -> Dict:
        return {**super().as_dict(), **{"threads": [thread.as_dict() for thread in self.threads]}}

    def scrape(self, tag: bs4.Tag) -> Dict:
        thread_divs = tag.find_all("div", class_="opCell")
        self.threads = self._get_threads(thread_divs=thread_divs)
        self.threads_ids = self._get_threads_ids()
        self.checkpoint = self._get_checkpoint()
        return self.as_dict()

    def _get_threads(self, thread_divs: bs4.ResultSet) -> List[ChanThreadScraper]:
        threads = []
        for op_cell in thread_divs:
            thread = ChanThreadScraper(board_details=self._board_details)
            thread.scrape(tag=op_cell)
            threads.append(thread)
        return threads

    def _get_threads_ids(self) -> List[str]:
        return [thread.thread_id for thread in self.threads]

    @staticmethod
    def _sort_threads_list(
        threads_list: List[Type[ChanThreadScraper]],
    ) -> List[Type[ChanThreadScraper]]:
        return sorted(threads_list, key=lambda thread: int(thread.thread_id), reverse=False)

    def _get_checkpoint(self) -> str:
        return str(max(int(thread_id) for thread_id in self.threads_ids))

    def get_new_since_checkpoint(self, checkpoint: str) -> List[Any]:
        """Returns list of dew Objects since the checkpoint."""
        new_threads = [thread for thread in self.threads if int(thread.thread_id) > int(checkpoint)]
        return self._sort_threads_list(threads_list=new_threads)


class OLD_ChanThreadScraper(OLD_ChanScraper):
    def __init__(self, board_details: Optional[Dict] = None) -> None:
        super().__init__(board_details=board_details)
        self.thread_url = None
        self.thread_id = None
        self.thread_name = None
        self.posts = []
        self.posts_ids = []
        self._post_scraper = "ChanPostScraper"

    def as_dict(self) -> Dict:
        return {
            **super().as_dict(),
            **{
                "thread_url": self.thread_url,
                "thread_id": self.thread_id,
                "thread_name": self.thread_name,
                "posts": [post.as_dict() for post in self.posts],
            },
        }

    def scrape(self, tag: bs4.Tag) -> Dict:
        self.thread_id = self._get_thread_id(op_cell=tag)
        self.thread_name = self._get_thread_name(op_cell=tag)
        self.thread_url = self._get_thread_url(board_url=self.board_url, thread_id=self.thread_id)
        self.posts: List[ChanPostScraper] = self._get_posts(op_cell=tag)
        self.posts_ids: List[str] = self._get_posts_ids()
        self.checkpoint = self._get_checkpoint()
        return self.as_dict()

    @property
    def post_id(self) -> str:
        return self.posts[0].post_id or ""

    @property
    def subject(self) -> str:
        return self.posts[0].subject or ""

    @property
    def message(self) -> str:
        return self.posts[0].message or ""

    @property
    def uploads(self) -> List:
        return self.posts[0].uploads or []

    @staticmethod
    def _get_thread_id(op_cell: bs4.Tag) -> str:
        tag = op_cell.find("a", class_="linkQuote")
        return "" if not tag else tag.text.strip()

    @staticmethod
    def _get_thread_name(op_cell: bs4.Tag) -> str:
        tag = op_cell.find("span", class_="labelSubject")
        if not tag:
            tag = op_cell.find("div", class_="divMessage")
        return "" if not tag else tag.text.strip()

    @staticmethod
    def _get_thread_url(board_url: str, thread_id: str) -> str:
        return f"{board_url}/res/{thread_id}.html"

    def _get_posts(self, op_cell: bs4.Tag) -> List[ChanPostScraper]:
        op_post = self._post_scraper(
            board_thread_data=self.as_dict(), post_tag=op_cell.find("div", "innerOP")
        )

        post_tags = op_cell.find_all("div", "postCell")
        posts = [op_post]
        for post_tag in post_tags:
            post = self._post_scraper(board_thread_data=self.as_dict(), post_tag=post_tag)
            posts.append(post)

        return posts

    def _get_posts_ids(self) -> List[str]:
        return [post.post_id for post in self.posts]

    def _get_checkpoint(self) -> str:
        return str(max(int(post_id) for post_id in self.posts_ids))

    def get_new_since_checkpoint(self, checkpoint: str) -> List[Any]:
        """Returns list of dew Objects since the checkpoint."""
        new_posts = [post for post in self.posts if int(post.post_id) > int(checkpoint)]
        return self._sort_posts_list(posts_list=new_posts)

    @staticmethod
    def _sort_posts_list(
        posts_list: List[Type[ChanThreadScraper]],
    ) -> List[Type[ChanThreadScraper]]:
        return sorted(posts_list, key=lambda post: int(post.post_id), reverse=False)


class OLD_ChanPostScraper("ChanScraperProfile"):
    def __init__(self, post_tag: Tag, board_thread_data: Dict = None) -> None:
        board_thread_data = board_thread_data or {}
        self.base_url = board_thread_data.get("base_url") or None
        self.board_id = board_thread_data.get("board_id")
        self.board_name = board_thread_data.get("board_name")
        self.board_url = board_thread_data.get("board_url")
        self.thread_url = board_thread_data.get("thread_url")
        self.thread_id = board_thread_data.get("thread_id")
        self.thread_name = board_thread_data.get("thread_name")

        self.post_id = None
        self.subject = None
        self.name = None
        self.created = None
        self.backlinks = None
        self.uploads = None
        self.message = None

        self._post_tag = post_tag

        if self._post_tag:
            self._scrape_post_tag(post_tag=self._post_tag)

    def as_dict(self) -> Dict:
        return {
            "base_url": self.base_url,
            "board_id": self.board_id,
            "board_name": self.board_name,
            "board_url": self.board_url,
            "thread_url": self.thread_url,
            "thread_id": self.thread_id,
            "thread_name": self.thread_name,
            "post_id": self.post_id,
            "subject": self.subject,
            "name": self.name,
            "created": self.created,
            "backlinks": self.backlinks,
            "uploads": self.uploads,
            "message": self.message,
        }

    def _scrape_post_tag(self, post_tag: Tag):
        self.post_id = self._get_post_id(post_tag=post_tag)
        self.subject = self._get_post_subject(post_tag=post_tag)
        self.name = self._get_post_name(post_tag=post_tag)
        self.created = self._get_post_created(post_tag=post_tag)
        self.backlinks = self._get_post_backlinks(post_tag=post_tag)
        self.uploads = self._get_post_uploads(post_tag=post_tag, base_url=self.base_url)
        self.message = self._get_post_message(post_tag=post_tag)

        self.thread_id = self.thread_url or self._get_thread_id(post_tag=post_tag)
        self.thread_url = self.thread_url or self._get_thread_url(post_tag=post_tag)

        return self

    @staticmethod
    def _get_str_from_tag(tag: Any) -> str:
        if not tag:
            return ""
        return tag if isinstance(tag, str) else tag.text.strip()

    def _get_post_id(self, post_tag: Tag) -> str:
        tag = self.post_id_tag(tag=post_tag)
        return self._get_str_from_tag(tag=tag)

    def _get_post_subject(self, post_tag: Tag) -> str:
        tag = self.post_subject_tag(tag=post_tag)
        return self._get_str_from_tag(tag=tag)

    def _get_post_name(self, post_tag: Tag) -> str:
        tag = self.post_name_tag(tag=post_tag)
        return self._get_str_from_tag(tag=tag)

    def _get_post_created(self, post_tag: Tag) -> Optional[datetime.datetime]:
        tag = self.post_created_tag(tag=post_tag)
        if not tag:
            return None
        if isinstance(tag, datetime.datetime):
            return tag

        try:
            strdate = tag.text.strip()  # '12/03/2021 (Fri) 21:24:55'
            dt = datetime.datetime.strptime(strdate, self.parse_datetime_scheme())
        except AttributeError:
            dt = datetime.datetime.strptime(tag, self.parse_datetime_scheme())
        return dt

    def _get_post_backlinks(
        self, post_tag: Tag
    ) -> List[str]:  # TODO: Doesn't work. Maybe javascript?
        tag = self.post_backlinks_tag(tag=post_tag)
        if not tag:
            return []
        links_a = tag.find_all("a")
        return [a.text for a in links_a]

    def _get_post_uploads(
        self, post_tag: Tag, base_url: Optional[str] = None
    ) -> List[Dict[str, str]]:
        tag = self.post_uploads_tag(tag=post_tag)
        if not tag:
            return []
        links_a = self.post_upload_a_tags(tag=tag)
        return [
            {
                "filename": self.post_upload_filename(a=a),
                "url": self.post_upload_url(a=a, base_url=base_url),
            }
            for a in links_a
        ]

    def _get_post_message(self, post_tag: Tag) -> str:
        tag = self.post_message_tag(tag=post_tag)
        return self._get_str_from_tag(tag=tag)

    def _get_thread_id(self, post_tag: Tag) -> str:
        return self.post_thread_id(tag=post_tag)

    def _get_thread_url(self, post_tag: Tag) -> str:
        return self.post_thread_url(tag=post_tag)
