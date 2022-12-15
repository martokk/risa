from common import constants
from common.utils import Utils


class Feed:
    def __init__(self, feed_path: str = None) -> None:
        self._feed_path = feed_path or constants.FEED_FILE
        self.feed_data = {}

    def update(self) -> None:
        self._update_feed()

    def _update_feed(self) -> None:
        print(f"Updating Feed ({self._feed_path})...")

        # Check users for missing usernames on services

        # Check users services for updates to serice posts (ie. new images or posts).

        # Check watchers for new updates (New 4chan post, new AnonIb, SocialMediaGirls, etc).

    def display(self) -> None:
        self._import_feed_yaml()
        self._display_feed()

    def _import_feed_yaml(self) -> None:
        self.feed_data = Utils().import_yaml(file_path=self._feed_path)

    def _display_feed(self) -> None:
        print(f"Displaying Feed ({self._feed_path})...")
        for result, data in self.feed_data.items():
            print(data)
