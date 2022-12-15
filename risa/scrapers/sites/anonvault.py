from bs4 import ResultSet, Tag

from risa.scrapers.chan_scraper import ChanBoardScraper, ChanScraperProfile, ChanThreadScraper


class AnonVaultScraperProfile(ChanScraperProfile):
    def __init__(self) -> None:
        super().__init__()
        self._use_wget = True
        self.site_name = "AnonVault"
        self.site_url = "https://www.anonvault.org"
        self.board_url_scheme = "{SITE_URL}/{BOARD_ID}"
        self.thread_url_scheme = "{SITE_URL}/{BOARD_ID}/res/{THREAD_ID}.html"
        self.post_url_scheme = "{SITE_URL}/{BOARD_ID}/res/{THREAD_ID}.html#{POST_ID}"

    # BOARD ######################################################################
    @staticmethod
    def board_id_tag(page_tag: Tag) -> Tag:
        return page_tag.find("div", class_="thread")

    def board_id_str(self, tag: Tag):
        return tag.attrs["data-board"]

    @staticmethod
    def board_name_tag(page_tag: Tag) -> Tag:
        return page_tag.find("header").find("h1")

    # THREADS ######################################################################
    @staticmethod
    def thread_tags(page_tag: Tag) -> ResultSet:
        return page_tag.find_all("div", class_="thread")

    # THREAD ######################################################################
    @staticmethod
    def op_post_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("div", "post op")

    @staticmethod
    def post_tags(thread_tag: Tag) -> ResultSet:
        return thread_tag.find_all("div", "post reply")

    @staticmethod
    def thread_id_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find_all("a", class_="post_no")[1]

    @staticmethod
    def thread_url_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("a", class_="post_no")

    def thread_url_str(self, tag: Tag) -> str:
        return f"{self.site_url}{tag.attrs['href'].split('#')[0]}"

    @staticmethod
    def thread_name_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("span", class_="subject")

    @staticmethod
    def thread_name_fallback_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("div", class_="body")

    # POST ######################################################################
    @staticmethod
    def post_id_tag(post_tag: Tag) -> Tag:
        return post_tag.find_all("a", class_="post_no")[1]

    @staticmethod
    def post_url_tag(post_tag: Tag) -> Tag:
        return post_tag.find("a", class_="post_no")

    def post_url_str(self, tag: Tag) -> str:
        return f"{self.site_url}{tag.attrs['href']}"

    @staticmethod
    def post_subject_tag(post_tag: Tag) -> Tag:
        return post_tag.find("span", class_="subject")

    @staticmethod
    def post_author_tag(post_tag: Tag) -> Tag:
        return post_tag.find("span", class_="name")

    @staticmethod
    def post_datetime_tag(post_tag: Tag) -> Tag:
        return post_tag.find("time")

    @staticmethod
    def parse_datetime_scheme() -> str:
        return "%m/%d/%y (%a) %H:%M:%S"

    @staticmethod
    def post_backlinks_tag(post_tag: Tag) -> Tag:
        return post_tag.find("span", class_="mentioned")

    @staticmethod
    def post_backlink_tags(backlinks_tag: Tag) -> ResultSet:
        return backlinks_tag.find_all("a")

    @staticmethod
    def post_files_tag(post_tag: Tag) -> Tag:
        return post_tag.find("div", class_="files")

    @staticmethod
    def post_file_tags(files_tag: Tag) -> ResultSet:
        return files_tag.find_all("p", class_="fileinfo")

    @staticmethod
    def post_file_filename(file_tag: Tag) -> str:
        tag = file_tag.find("a")
        return tag.text.strip()

    def post_file_url(self, file_tag: Tag) -> str:
        tag = file_tag.find("a")
        return f"{self.site_url or ''}{tag['href']}"

    @staticmethod
    def post_body_tag(post_tag: Tag) -> Tag:
        return post_tag.find("div", class_="body")


class AnonVaultBoardScraper(AnonVaultScraperProfile, ChanBoardScraper):
    pass


class AnonVaultThreadScraper(AnonVaultScraperProfile, ChanThreadScraper):
    pass


# Examples ##################################################
def example_scrape_thread() -> None:
    thread_url = "https://anonvault.xyz/wisc/res/41.html"

    thread = AnonVaultThreadScraper()
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


def example_scrape_board() -> None:
    board_url = "https://anonvault.xyz/wisc"

    scraper = AnonVaultBoardScraper()
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
    # example_scrape_thread()
    example_scrape_board()
    # example_checkpoint()
