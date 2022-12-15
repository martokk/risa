from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import re
import subprocess
from abc import ABC, abstractmethod

import bs4
import requests


class Scraper(ABC):
    def __init__(self, use_wget=False) -> None:
        self._page_tag: Optional[bs4.Tag] = None
        self._url: Optional[str] = None
        self._use_wget = use_wget
        self.base_url = None

    def get_soup_from_url(self, url: str) -> bs4.BeautifulSoup:
        html = self._get_page_html(url=url)
        self._page_tag = bs4.BeautifulSoup(html, "html.parser")
        self.base_url = self._get_base_url()
        return self._page_tag

    def _get_page_html(self, url: str) -> Union[bytes, str]:
        if self._use_wget:
            cmd = f'wget -S -O - --user-agent="" {url}'
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
            )
            html, std_err = process.communicate()
            print(std_err)
        else:
            html = requests.get(url).content
        return html

    def as_dict(self) -> Dict:
        return {"base_url": self.base_url}

    def scrape_url(self, url: str) -> Dict:
        self._url = url
        self._page_tag = self.get_soup_from_url(url=url)
        return self.scrape(page_tag=self._page_tag)

    @abstractmethod
    def scrape(self, page_tag: bs4.Tag) -> Dict:
        return self.as_dict()

    def _get_base_url(self) -> str:
        return re.search("^(http[s]?://[a-zA-Z0-9\s_.\-()?=%]+\.[\w]{2,4})", self._url).group()

    @property
    def url(self) -> str:
        return self._url


class ScraperCheckpoint(ABC):
    def __init__(self) -> None:
        self.checkpoint = None

    @abstractmethod
    def _get_checkpoint(self) -> str:
        """Returns a checkpoint id for later use. Returns as a string."""
        return ""

    @abstractmethod
    def get_new_since_checkpoint(self, checkpoint: str) -> List[Any]:
        """Returns list of dew Objects since the checkpoint."""
        return []


# CHAN SCRAPERS #################################################
