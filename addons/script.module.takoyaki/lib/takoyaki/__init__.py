# codec: utf-8

import sys
import urllib
import urlparse
import pickle
import requests


class Takoyaki(object):

    USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

    __base__url = sys.argv[0]
    __handle__ = int(sys.argv[1])

    def __init__(self):
        self.params = self.parse_parameter()

    def run(self):
        self.select_mode()

    @classmethod
    def write_cookie(cls, session, cookie_file_name='cookie.dump'):
        with open('cookie_file_name', 'wb') as fp:
            pickle.dump(session.cookies, fp)

    @classmethod
    def read_cookie(cls, session, cookie_file_name='cookie.dump'):
        with open(cookie_file_name, 'rb') as fp:
            cookie = pickle.load(fp)
            session.cookies.update(cookie)

    @classmethod
    def login(cls, login_url, query):
        session = requests.Session()
        response = session.post(login_url, data=query)
        return session, response

    @classmethod
    def urljoin(cls, base, *urls):
        jointed_url = base
        for url in urls:
            jointed_url = urlparse.urljoin(jointed_url,url)
        return jointed_url

    @classmethod
    def build_url(cls, query):
        return sys.argv[0] + '?' + urllib.urlencode(query)

    @classmethod
    def parse_parameter(cls):
        params = urlparse.parse_qs(sys.argv[2][1:])
        return {key: value[0] for key, value in params.items()}

    def download_html(self, url, cookie=None):
        headers = {'user-agent': self.USER_AGENT}
        return requests.get(url, headers=headers).text
