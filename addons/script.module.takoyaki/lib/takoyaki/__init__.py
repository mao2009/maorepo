# codec: utf-8

import os
import sys
import urllib
import urlparse
import pickle
import requests

import xbmcaddon


class Takoyaki(object):

    USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

    __base__url = sys.argv[0]
    __handle__ = int(sys.argv[1])
    __addon__ = xbmcaddon.Addon()
    __addon_id__ = __addon__.getAddonInfo('id')
    __addon_user_data_ = os.path.join('special://userdata/addon_data', __addon_id__)

    def __init__(self):
        self.params = self.parse_parameter()

    def run(self):
        self.select_mode()

    def select_mode(self, func, default_mode='top_menu'):
        mode = self.params.get('mode', default_mode)
        modes = func()
        selected_mode = modes.get(mode)
        return selected_mode

    def write_cookie(self, cookie, cookie_file_name='cookie.dump'):
        cookie_file_path = os.path.join(self.__user_data_path__, cookie_file_name)
        with open(cookie_file_path, 'wb') as fp:
            pickle.dump(cookie, fp)

    def read_cookie(self, cookie_file_name='cookie.dump'):
        cookie_file_path = os.path.join(self.__user_data_path__, cookie_file_name)
        with open(cookie_file_path, 'rb') as fp:
            cookie = pickle.load(fp)
        return cookie

    def login(self, login_url, query, mode='post', session=None, headers={}):
        if session is None:
            headers['user_agent'] = self.USER_AGENT
            if mode == 'get' or mode == 'g':
                cookies = requests.get(login_url, params=query, headers=headers).cookies

            elif mode == 'post' or mode == 'p':
                cookies = requests.post(login_url, data=query, headers=headers).cookies
            else:
                raise ValueError('Unexpected mode')
        else:
            if mode == 'get' or mode == 'g':
                cookies = session.get(login_url, headers=headers, params=query).cookies
            elif mode == 'post' or mode == 'p':
                cookies = session.post(login_url, headers=headers, data=query).cookies
            else:
                raise ValueError('Unexpected mode')
        self.write_cookie(cookie=cookies)


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
