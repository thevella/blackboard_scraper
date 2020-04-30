import requests
from bs4 import BeautifulSoup
import lxml.html
from io import open as iopen

import os

#class for scraping iLectures from echo360.
class ILectureUnit():
    def __init__(self, link, name):
        self.link = link
        self.name = name
        self.session = requests.Session()

    #scrapes iLectures from a particular rss feed
    #path: path of the root unit directory
    @staticmethod
    def scrape_ilectures(url, path):
        session = requests.Session()
        request = session.get(url)
        soup = BeautifulSoup(request.text, "html.parser")
        alist = []
        blist = []
        dir = 'iLectures'
        unit_name = soup.title.string
        for link in soup.find_all('pubdate'):
            strin = link.string[:-6]
            alist.append(strin)
        for link in soup.find_all('enclosure'):
            blist.append(link.get('url'))
        ii = 0
        for jj in alist:
            ILectureUnit.fetch_video(blist[ii], dir, unit_name, jj, path)
            ii = ii + 1

    #downloads a single iLecture video
    #file_url: the url of the video
    #directory: the directory to save to
    #unit_name: the name of the unit
    #file_name: the name of the video
    #path: root directory to save in
    @staticmethod
    def fetch_video(file_url, directory, unit_name, file_name, path):
        session = requests.Session()
        #file_name = string.replace(file_name, ':', '-')
        file_name = file_name.replace(':', '-')
        if '.' in file_name:
            format = '.' + file_name.split('.')[1]
        else:
            format = ' '
        while len(format) > 7:
            format = '.' + file_name.split('.')[1]
        while len(directory) > 50:
            directory = directory[:-1]
        #directory = string.replace(directory, ':', '-')
        directory = directory.replace(':', '-')

        #unit_name = string.replace(unit_name, ':', '-')
        unit_name = unit_name.replace(':', '-')

        thepath = path + '/' + unit_name + '/' + directory + '/'
        while len(thepath + file_name) > 256:
            file_name = file_name[:-9] + format
        if not os.path.isdir(thepath):
            os.makedirs(thepath)
        if not os.path.exists(path + file_name):
            print(file_url)
            i = session.get(file_url)
            if i.status_code == requests.codes.ok:
                with iopen(thepath + file_name + '.m4v', 'wb') as file:
                    file.write(i.content)
            else:
                return False
