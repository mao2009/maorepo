# coding: utf-8

from bs4 import BeautifulSoup

import xbmcgui
import xbmcplugin

from takoyaki import Takoyaki


class DotInstall(Takoyaki):

    BASE_URL = 'https://dotinstall.com/'
    LOGIN_URL = 'https://dotinstall.com/login.php'

    def select_mode(self):
        modes = {
            'top_menu': self.top_menu,
            'lessons': self.lessons,
            'lesson': self.lesson,
            'select_source': self.select_source
        }
        super(DotInstall, self).select_mode(modes)

    def login(self):
        url = 'https://dotinstall.com/login'
        html = self.download_html(url)
        soup = BeautifulSoup(html)
        token = soup.find('input', class_='one_time_token').get('value').encode('utf-8')
        query = {
            'mail': self.username,
            'password': self.password,
            'one_time_token': token
        }
        super(DotInstall, self).login(self.LOGIN_URL, query, mode='post')

    def lessons(self):
        url = self.url_join(self.BASE_URL, 'lessons')
        html = self.download_html(url)
        bs = BeautifulSoup(html)
        elements = bs.find_all(class_='span8')
        num = int(self.params.get('element_num'))
        element = elements[num]
        lessons = element.find_all('a')

        img_url = self.params.get('img_url')
        for lesson in lessons:
            link = self.url_join(self.BASE_URL, lesson.get('href'))
            title = lesson.text
            li = xbmcgui.ListItem(title, iconImage=img_url)
            query = {'mode': 'lesson', 'link': link, 'img_url': img_url}
            url = self.build_url(query)
            xbmcplugin.addDirectoryItem(handle=self.__handle__, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(self.__handle__)

    def lesson(self):
        url = self.params.get('link')
        html = self.download_html(url)
        bs = BeautifulSoup(html)
        lessons = bs.find(id='lessons_list').find_all('a')
        img_url = self.params.get('img_url')
        for lesson in lessons:
            link = self.url_join(self.BASE_URL, lesson.get('href'))
            title = lesson.text
            li = xbmcgui.ListItem(title, iconImage=img_url)
            query = {'mode': 'select_source', 'link': link, 'img_url': img_url}
            url = self.build_url(query)
            xbmcplugin.addDirectoryItem(handle=self.__handle__, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(self.__handle__)

    def select_source(self):
        if self.is_login:
            self.login()

        url = self.params.get('link')
        html = self.download_html(url)
        bs = BeautifulSoup(html)
        sources = bs.find_all('source')
        img_url = self.params.get('img_url')
        for source in sources:
            link = self.url_join(self.BASE_URL, source.get('src'))
            title = source.get('data-res') + 'P ' + source.get('type')
            li = xbmcgui.ListItem(title, iconImage=img_url)
            query = {'mode': 'play_video', 'link': link, 'img_url': img_url}
            url = self.build_url(query)
            xbmcplugin.addDirectoryItem(handle=self.__handle__, url=link, listitem=li)
        xbmcplugin.endOfDirectory(self.__handle__)

    def top_menu(self):

        url = self.url_join(self.BASE_URL, 'lessons')
        html = self.download_html(url)
        bs = BeautifulSoup(html)

        elements = bs.find_all(class_='span8')

        for element_num, element in enumerate(elements):
            image_element = element.find('img')
            if image_element is None:
                continue
            title_element = element.div.div
            if title_element is None:
                continue
            img_url = image_element.get('src')
            title = title_element.text.encode('utf-8').replace('\n', '')
            img_url = self.url_join(self.BASE_URL, img_url)
            li = xbmcgui.ListItem(title, iconImage=img_url)
            query = {'mode': 'lessons', 'img_url': img_url, 'element_num': element_num}
            url = self.build_url(query)
            xbmcplugin.addDirectoryItem(handle=self.__handle__, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(self.__handle__)


def main():
    dotinstall = DotInstall()
    dotinstall.run()


main()

