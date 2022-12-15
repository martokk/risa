import requests
from bs4 import BeautifulSoup
# from anonfile import AnonFile

class AnonFileGetDownload:
    # @staticmethod
    # def get_direct_url_from_url(url: str):
    #     """
    #     uses 'anonfile' package from: https://github.com/nstrydom2/anonfile-api
    #     pip install anonfile
    #
    #     url = "https://anonfiles.com/V3m1f7Zcx0/PIPER_BLUSH_NAKED_BATH_PORN_VIDEO_mp4"
    #     """
    #     # Get download link for anonfile package
    #     anonfile_download_url = AnonFile().preview(url).ddl.geturl()  # (doesn't handle spaces correcyly?)
    #
    #     # HACK: hotfix corrects spaces not getting encoded in filename.
    #     url_split = anonfile_download_url.split("/")
    #     url_split[-1] = urllib.parse.quote(url_split[-1])
    #     download_url = '/'.join(url_split)
    #
    #     return download_url

    @staticmethod
    def get_direct_url_from_url(url: str):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        url = soup.find("a", id='download-url')['href']
        url.replace(" ", "%20")
        return url
