# codec: utf-8

import os
import sys
import urllib
import urlparse
import pickle
import requests

import xbmc
import xbmcaddon


class Takoyaki(object):

    USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

    __base__url = sys.argv[0]
    __handle__ = int(sys.argv[1])
    __addon__ = xbmcaddon.Addon()
    __addon_id__ = __addon__.getAddonInfo('id')

    def __init__(self):

        self.__addon_user_data__ = xbmc.translatePath(self.path_join('special://userdata/addon_data', self.__addon_id__))
        self.params = self.parse_parameter()
        self.is_login = self.__addon__.getSetting('login')
        if self.is_login:
            self.password = self.__addon__.getSetting('password')
            self.username = self.__addon__.getSetting('username')
        self.cookies = self.read_cookie()
        self.session = self.open_session()

    def set_basic_auth(self, user, password):
        self.session.auth = (user, password)

    def open_session(self):
        session = requests.Session()
        session.cookies.update(self.cookies)
        headers = {'user_agent': self.USER_AGENT}
        session.headers.update(headers)
        return session

    def run(self):
        self.select_mode()

    def select_mode(self, modes, default_mode='top_menu'):
        mode = self.params.get('mode', default_mode)
        selected_mode = modes.get(mode)
        selected_mode()

    def write_cookie(self, cookie, cookie_file_name='cookie.dump'):
        cookie_file_path = self.path_join(self.__addon_user_data__, cookie_file_name)
        with open(cookie_file_path, 'wb') as fp:
            pickle.dump(cookie, fp)

    def read_cookie(self, cookie_file_name='cookie.dump'):
        cookie_file_path = self.path_join(self.__addon_user_data__, cookie_file_name)
        if os.path.exists(cookie_file_path):
            with open(cookie_file_path, 'rb') as fp:
                cookie = pickle.load(fp)
            return cookie
        else:
            return {}

    def login(self, login_url, query, mode='post'):

        if mode == 'get' or mode == 'g':
            cookies = self.session.get(login_url,  params=query).cookies
        elif mode == 'post' or mode == 'p':
            cookies = self.session.post(login_url,  data=query).cookies
        else:
            raise ValueError('Unexpected mode')
        self.session.cookies.update(cookies)
        self.write_cookie(cookie=cookies)

    @classmethod
    def path_join(cls, path, *paths):
        return os.path.join(path, *paths).replace('\\', '/')

    @classmethod
    def url_join(cls, base, *urls):
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

    def download_html(self, url, mode='get', query={}):

        if mode == 'get' or mode == 'g':
            return self.session.get(url, params=query).text
        elif mode == 'post' or mode == 'p':
            return self.session.post(url, data=query).text

        raise ValueError('Unexpected mode')
