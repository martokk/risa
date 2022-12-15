import re

from risa.scrapers.chan_scraper import ChanScraperABC
from risa.scrapers.sites.anonib import AnonIbBoardScraper, AnonIbThreadScraper
from risa.scrapers.sites.anonvault import AnonVaultBoardScraper, AnonVaultThreadScraper


class ScraperRouter:
    def get_scraper(self, url: str) -> ChanScraperABC:
        scraper = None
        if "anonib.al" in url:
            scraper = self.get_anonib_scraper(url=url)
        if "anonib.al" in url:
            scraper = self.get_anonib_scraper(url=url)
        if "anonib.com" in url:
            scraper = self.get_anonib_scraper(url=url)
        if "anonvault.xyz" in url:
            scraper = self.get_anonvault_scraper(url=url)
        if not scraper:
            raise NotImplementedError(f"Could not find a scraper for url. {url=}")

        return scraper

    @staticmethod
    def get_anonib_scraper(url: str) -> ChanScraperABC:
        if re.search("/res/", url):
            return AnonIbThreadScraper()
        else:
            return AnonIbBoardScraper()

    @staticmethod
    def get_anonvault_scraper(url: str) -> ChanScraperABC:
        if re.search("/res/", url):
            return AnonVaultThreadScraper()
        else:
            return AnonVaultBoardScraper()
