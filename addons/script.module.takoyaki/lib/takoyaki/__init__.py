# codec: utf-8

import sys
import urllib
import urlparse

import requests


class Takoyaki(object):

    __base__url = sys.argv[0]
    __handle__ = int(sys.argv[1])

    def __init__(self):
        self.params = self.parse_parameter()

    def run(self):
        self.select_mode()

    @classmethod
    def urljoin(cls, base, *urls):
        jointed_url = base
        for url in urls:
            jointed_url = urlparse.urljoin(jointed_url,url)
        return

    @classmethod
    def build_url(cls, query):
        return sys.argv[0] + '?' + urllib.urlencode(query)

    @classmethod
    def parse_parameter(cls):
        params = urlparse.parse_qs(sys.argv[2][1:])
        return {key: value[0] for key, value in params.items()}

    @classmethod
    def download_html(cls, url):
        headers = {'user-agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        return requests.get(url, headers=headers).text
