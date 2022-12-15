from bs4 import ResultSet, Tag

from risa.scrapers.chan_scraper import ChanBoardScraper, ChanScraperProfile, ChanThreadScraper


class AnonIbScraperProfile(ChanScraperProfile):
    def __init__(self) -> None:
        super().__init__()
        self._use_wget = False
        self.site_name = "AnonIB"
        self.site_url = "http://www.anonib.al"
        self.board_url_scheme = "{SITE_URL}/{BOARD_ID}"
        self.thread_url_scheme = "{SITE_URL}/{BOARD_ID}/res/{THREAD_ID}.html"
        self.post_url_scheme = "{SITE_URL}/{BOARD_ID}/res/{THREAD_ID}.html#{POST_ID}"

    # BOARD ######################################################################
    @staticmethod
    def board_id_tag(page_tag: Tag) -> Tag:
        return page_tag.find("p", id="labelName")

    def board_id_str(self, tag: Tag):
        return super().board_id_str(tag=tag).split("/")[1]

    @staticmethod
    def board_name_tag(page_tag: Tag) -> Tag:
        return page_tag.find("p", id="labelName")

    # THREADS ######################################################################
    @staticmethod
    def thread_tags(page_tag: Tag) -> ResultSet:
        return page_tag.find_all("div", class_="opCell")

    # THREAD ######################################################################
    @staticmethod
    def op_post_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("div", "innerOP")

    @staticmethod
    def post_tags(thread_tag: Tag) -> ResultSet:
        return thread_tag.find_all("div", "postCell")

    @staticmethod
    def thread_id_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("a", class_="linkQuote")

    @staticmethod
    def thread_url_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("input", class_="deletionCheckBox")

    def thread_url_str(self, tag: Tag) -> str:
        split = tag.attrs["name"].split("-")  # wi-6511-6717
        return self.generate_thread_url(
            site_url=self.site_url, board_id=split[0], thread_id=split[1]
        )

    @staticmethod
    def thread_name_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("span", class_="labelSubject")

    @staticmethod
    def thread_name_fallback_tag(thread_tag: Tag) -> Tag:
        return thread_tag.find("div", class_="divMessage")

    # POST ######################################################################
    @staticmethod
    def post_id_tag(post_tag: Tag) -> Tag:
        return post_tag.find("a", class_="linkQuote")

    @staticmethod
    def post_url_tag(post_tag: Tag) -> Tag:
        return post_tag.find("input", class_="deletionCheckBox")

    def post_url_str(self, tag: Tag) -> str:
        split = tag.attrs["name"].split("-")  # wi-6511-6717
        try:
            post_id = split[2]
        except IndexError:
            post_id = split[1]
        return self.generate_post_url(
            site_url=self.site_url, board_id=split[0], thread_id=split[1], post_id=post_id
        )

    @staticmethod
    def post_subject_tag(post_tag: Tag) -> Tag:
        return post_tag.find("span", class_="labelSubject")

    @staticmethod
    def post_author_tag(post_tag: Tag) -> Tag:
        return post_tag.find("a", class_="linkName")

    @staticmethod
    def post_datetime_tag(post_tag: Tag) -> Tag:
        return post_tag.find("span", class_="labelCreated")

    @staticmethod
    def post_backlinks_tag(post_tag: Tag) -> Tag:
        return post_tag.find("span", class_="panelBacklinks")

    @staticmethod
    def post_backlink_tags(backlinks_tag: Tag) -> ResultSet:
        return backlinks_tag.find_all("a")

    @staticmethod
    def post_files_tag(post_tag: Tag) -> Tag:
        return post_tag.find("div", class_="panelUploads")

    @staticmethod
    def post_file_tags(files_tag: Tag) -> ResultSet:
        return files_tag.find_all("a", class_="originalNameLink")

    @staticmethod
    def post_body_tag(post_tag: Tag) -> Tag:
        return post_tag.find("div", class_="divMessage")


class AnonIbBoardScraper(AnonIbScraperProfile, ChanBoardScraper):
    pass


class AnonIbThreadScraper(AnonIbScraperProfile, ChanThreadScraper):
    pass


# Examples ##################################################
def example_scrape_thread() -> None:
    thread_url = "https://anonib.al/wi/res/1559.html"

    thread = AnonIbThreadScraper()
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
    board_url = "https://anonib.al/wi"

    scraper = AnonIbBoardScraper()
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
