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
        self.session = self.open_session()

    def set_basic_auth(self, user, password):
        self.session.auth = (user, password)

    def open_session(self):
        session = requests.Session()
        headers = {'user_agent': self.USER_AGENT}
        session.headers.update(headers)
        return session

    def run(self):
        self.select_mode()

    def select_mode(self, modes, default_mode='top_menu'):
        mode = self.params.get('mode', default_mode)
        selected_mode = modes.get(mode)
        selected_mode()

    def login(self, login_url, query, mode='post'):

        if mode == 'get' or mode == 'g':
            self.session.get(login_url,  params=query)
        elif mode == 'post' or mode == 'p':
            self.session.post(login_url,  data=query)
        else:
            raise ValueError('Unexpected mode')

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
