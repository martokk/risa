from typing import Any, Dict, List

import bs4
from bs4 import ResultSet, Tag

from risa.scrapers.chan_scraper import (
    ChanBoardScraper,
    ChanScraperProfile,
    ChanSearchScraper,
    ChanThreadScraper,
)
from risa.scrapers.scrapers import Scraper


class ArchivedMoeScraperProfile(ChanScraperProfile):
    def __init__(self) -> None:
        super().__init__()
        self._use_wget = True
        self.site_name = "Archived.Moe"
        self.site_url = "https://www.archived.moe"
        self.board_url_scheme = "{SITE_URL}/{BOARD_ID}"
        self.thread_url_scheme = "{SITE_URL}/{BOARD_ID}/thread/{THREAD_ID}.html"
        self.post_url_scheme = "{SITE_URL}/{BOARD_ID}/thread/{THREAD_ID}/#{POST_ID}"
        self.search_image_hash_scheme = "{SITE_URL}/_/search/image/{IMAGE_HASH}/"

    # BOARD ######################################################################
    @staticmethod
    def board_id_tag(page_tag: Tag) -> Tag:
        # return page_tag.find("article")
        return page_tag.find("button", class_="btn-toggle-post")

    def board_id_str(self, tag: Tag):
        return tag.attrs["data-board"]

    @staticmethod
    def board_name_tag(page_tag: Tag) -> Tag:
        return page_tag.find("title")

    def board_name_str(self, tag: Tag) -> str:
        text = tag.text.replace("-", "»")
        try:
            text = text.split("»")[1].strip()
        except IndexError:
            pass
        return None if not text else text

    # THREADS ######################################################################
    @staticmethod
    def thread_tags(page_tag: Tag) -> ResultSet:
        return page_tag.find_all("article", class_="post")

    # THREAD ######################################################################
    @staticmethod
    def op_post_tag(thread_tag: Tag) -> Tag:
        return thread_tag

    @staticmethod
    def post_tags(thread_tag: Tag) -> ResultSet:
        return thread_tag.find_all("article", "post")

    @staticmethod
    def thread_id_tag(thread_tag: Tag) -> Tag:
        return thread_tag

    def thread_id_str(self, tag: Tag) -> str:
        return tag.attrs["id"]

    @staticmethod
    def thread_url_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("span", class_="time_wrap").find_next_sibling()

    def thread_url_str(self, tag: Tag) -> str:
        return tag.attrs["href"]

    @staticmethod
    def thread_name_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("h2", class_="post_title")

    @staticmethod
    def thread_name_fallback_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("div", class_="text")

    # POST ######################################################################
    @staticmethod
    def post_id_tag(post_tag: Tag) -> Tag:
        try:
            return post_tag.attrs["id"]
        except KeyError:
            pass

    @staticmethod
    def post_url_tag(post_tag: Tag) -> Tag:
        return post_tag.find("span", class_="time_wrap").find_next_sibling()

    def post_url_str(self, tag: Tag) -> str:
        return f"{tag.attrs['href']}"

    @staticmethod
    def post_subject_tag(post_tag: Tag) -> Tag:
        return post_tag.find("span", class_="subject")

    @staticmethod
    def post_author_tag(post_tag: Tag) -> Tag:
        return post_tag.find("h2", class_="post_title")

    @staticmethod
    def post_datetime_tag(post_tag: Tag) -> Tag:
        return post_tag.find("time")

    @staticmethod
    def parse_datetime_scheme() -> str:
        """Sat 30 Apr 2022 03:53:52"""
        return "%a %d %b %Y %H:%M:%S"

    @staticmethod
    def post_backlinks_tag(post_tag: Tag) -> Tag:
        return post_tag.find("div", class_="backlink_list")

    @staticmethod
    def post_backlink_tags(backlinks_tag: Tag) -> ResultSet:
        return backlinks_tag.find_all("a")

    @staticmethod
    def post_backlink_str(backlink_tag: Tag) -> str:
        return backlink_tag.text.replace(">>", "")

    @staticmethod
    def post_files_tag(post_tag: Tag) -> Tag:
        return post_tag.find("div", class_="post_file")

    @staticmethod
    def post_file_tags(files_tag: Tag) -> ResultSet:
        return files_tag.find_all("a", class_="post_file_filename")

    @staticmethod
    def post_file_filename(file_tag: Tag) -> str:
        return file_tag.text.strip()

    def post_file_url(self, file_tag: Tag) -> str:
        return file_tag.attrs["href"].replace(
            "archived.moe/b/redirect/", "thebarchive.com/b/full_image/"
        )

    @staticmethod
    def post_body_tag(post_tag: Tag) -> Tag:
        return post_tag.find("div", class_="text")


class ArchivedMoeBoardScraper(ArchivedMoeScraperProfile, ChanBoardScraper):
    pass


class ArchivedMoeThreadScraper(ArchivedMoeScraperProfile, ChanThreadScraper):
    pass


class ArchivedMoeSearchScraper(ArchivedMoeScraperProfile, ChanSearchScraper):
    def board_id_str(self, tag: Tag):
        return "_"


# Examples ##################################################
def example_scrape_thread(thread_url) -> None:
    thread = ArchivedMoeThreadScraper()
    data = thread.scrape_url(url=thread_url)

    # Print Site Attributes
    for k, v in data["site"].items():
        print(f"{k}: {v}")

    # Print Board Attributes
    for k, v in data["board"].items():
        print(f"{k}: {v}")

    _pre = "\t"
    # Print Thread Attributes
    for k, v in data["thread"]["thread"].items():
        print(f"{_pre}{k}: {v}")

        # Print Thread Postss
        for post in data["posts"]:
            print(
                f"{_pre} --> {post.get('post_id')} {post.get('datetime')}: "
                f"{post.get('name')} - {len(post['files']) if post['files'] else ' '} "
                f"{post.get('message')}".replace("\n", " \\n ")
            )


def example_scrape_board(board_url) -> None:
    scraper = ArchivedMoeBoardScraper()
    data = scraper.scrape_url(url=board_url)

    _pre = "\t"
    # Print Site Attributes
    for k, v in data["site"].items():
        print(f"{k}: {v}")

    # Print Board Attributes
    for k, v in data["board"].items():
        print(f"{k}: {v}")

    for thread in data["threads"]:
        # Print Thread Attributes
        for k, v in thread["thread"].items():
            print(f"{_pre}{k}: {v}")

        # Print Thread Posts
        for post in thread["posts"]:
            print(
                f"{_pre} --> {post.get('post_id')} {post.get('datetime')}: "
                f"{post.get('name')} - {len(post['files']) if post['files'] else ' '} "
                f"{post.get('message')}".replace("\n", " \\n ")
            )


def example_scrape_image_hash() -> None:
    image_hash = "jIANnBQZ7ExMVJoN9pgfnw=="

    scraper = ArchivedMoeSearchScraper()
    data = scraper.search_image_hash(image_hash=image_hash)
    results = scraper.results

    _pre = "\t"
    # Print Site Attributes
    for k, v in data["site"].items():
        print(f"{k}: {v}")

    # Print Board Attributes
    for k, v in data["board"].items():
        print(f"{k}: {v}")

    for thread in data["threads"]:
        # Print Thread Attributes
        for k, v in thread["thread"].items():
            print(f"{_pre}{k}: {v}")

        # Print Thread Posts
        for post in thread["posts"]:
            print(
                f"{_pre} --> {post.get('post_id')} {post.get('datetime')}: "
                f"{post.get('name')} - {len(post['files']) if post['files'] else ' '} "
                f"{post.get('message')}".replace("\n", " \\n ")
            )


# def example_checkpoint() -> None:
#     url = 'http://www.anonib.al/wi'
#
#     # last_checkpoint = sub.get('checkpoint')
#
#     scraper = AnonIbBoardScraper()
#     scraper.scrape_url(url=url)
#     temp_last_checkpoint = '6850'
#
#     new_threads_ids = [thread.thread_id for thread in scraper.get_new_since_checkpoint(last_checkpoint=temp_last_checkpoint)]
#     print([new_threads_ids])
#     print()


if __name__ == "__main__":
    # example_scrape_thread("https://archived.moe/b/thread/877224365")
    # example_scrape_board("https://archived.moe/b")
    example_scrape_image_hash()
    # example_checkpoint()
