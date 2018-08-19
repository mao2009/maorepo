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

    def select_mode(self, func, default_mode='top_menu'):
        mode = self.params.get('mode', default_mode)
        modes = func()
        selected_mode = modes.get(mode)
        return selected_mode

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

    def download_html(self, url, mode='get', session=None, headers={}, query={}, cookies={}):
        if session is None:
            headers['user_agent'] = self.USER_AGENT
            if mode == 'get' or mode == 'g':
                return requests.get(url, headers=headers, params=query, cookies=cookies).text
            elif mode == 'post' or mode == 'p':
                return requests.post(url, headers=headers, data=query, cookies=cookies).text
        else:
            if mode == 'get' or mode == 'g':
                return session.get(url, headers=headers, params=query, cookies=cookies).text
            elif mode == 'post' or mode == 'p':
                return session.post(url, headers=headers, data=query, cookies=cookies).text

        raise ValueError('Unexpected mode')
