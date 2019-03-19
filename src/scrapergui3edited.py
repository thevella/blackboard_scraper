#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import *
import tkinter
import tkinter.messagebox
import _thread
import webbrowser
from tkinter.filedialog import askdirectory
from bs4 import BeautifulSoup
import os
import requests
import urllib.request, urllib.error, urllib.parse
import datetime
import base64
import string
import getpass
import multiprocessing
import functools
from io import open as iopen
from urllib.parse import urlsplit
import platform

from selenium import webdriver
#import seleniumrequests as webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
import re

#for finding hiddenfields
import lxml.html

#import pdb; pdb.set_trace()

if "Darwin" in platform.system():
        os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

# ------------------------------------------------------------------------------#
# ............................................................................  #
# ................................  scrapergui................................  #
# @author: Jason Giancono............................  #
#..more info at jasongi.com/blackboard-scraper
# todo: ....documentation
# ................better Echo360 scraper
# ................clean up rapyd junk
# ................option to cancel downlaod
# ................option to select individual files
# ................better looking GUI (probably not going to happen)
# ................work for all blackboard not just Curtin
# ................make a setup file
# ------------------------------------------------------------------------------#

#blackBoardBaseURL = "lms.curtin.edu.au"
blackBoardBaseURL = 'uoit.blackboard.com'
valid_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'

#sanitizes the filenames for windows (and hopefully other OS' too!)
def sanitize(filename):
    filename = filename.strip()
    filename = filename.replace(":", "--").replace("/", "-")

    filename = ''.join(c for c in filename if c in valid_chars)
    try:
        while ((filename[len(filename)-1] == ' ') or (filename[len(filename)-1] == '.')):
            filename = filename[:-1]
        while (filename.count("  ") != 0):
            filename = filename.replace("  ", " ")
    except IndexError:
        if len(filename) < 1:
            return 'file_' + filename
        else:
            return filename.strip()
    return filename.strip()

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

#class for scraping blackboard units, simply initialise and call startScrape
class BlackboardUnit():
    def __init__(self, uid, name, session, sessionr):
        self.uid = uid
        self.name = name
        self.session = session
        self.sessionr = sessionr
        self.visitList = []

    #downloads a single document - does some checks on the filename to make sure it is legit
    #file url: the url of the file
    #folder name: the subfolder which the file will be downloaded to
    #path: the root path where the unit folder will be
    def fetch_document(self, file_url, folder_name, path, listedName):
        #while len(folder_name.split("/")[-1]) > 50:
        #    folder_name = folder_name[:-1]
        #while len(self.name) > 50:
        #    self.name = self.name[:-1]
        #folder_name = string.replace(folder_name, ':', ' ')
        #self.name = string.replace(self.name, ':', ' ')
        #folder_name = folder_name.replace(":", "--")
        #self.name = self.name.replace(":", "--").replace("/", "-")

        #folder_name = sanitize(folder_name)
        self.name = sanitize(self.name)
        if len(re.findall(r'http[s\:]+\/\/', file_url)) > 1:
            file_url = file_url.replace("https://" + blackBoardBaseURL + "/", "")
        urlResponse = self.session.get(file_url, allow_redirects=False)

        if urlResponse.status_code == 302:
            urlpath = urlResponse.headers['location'].replace("https://" + blackBoardBaseURL + "/", "")
            #print(urlpath)
            if urlpath[0] == '/':
                urlpath = "https://" + blackBoardBaseURL + urlpath

            #print("1")
        else:
            urlpath = urlResponse.url
            #print("0")
        thepath=""
        if len(folder_name) > 0:
            thepath = path + '/' + self.name + '/' + folder_name + '/'
        else:
            thepath = path + '/' + self.name + '/'

        name = urlsplit(urlpath)[2].split('/')
        name = name[len(name)-1]
        #name = urllib.parse.unquote(name).decode('utf8')
        name = urllib.parse.unquote(name)
        while ((len(name) > 240)):
            if "." in name:
                filename = name.split('.')
                ext = filename[len(filename)-1]
                prefix = ''
                for x in filename[:-1]:
                    prefix = prefix + x
                name = prefix[:-1] + '.' + ext
            else:
                name = name[:-1]

        if "." in name:
            filename = name.split('.')
            ext = filename[len(filename)-1]

        name = sanitize(name)
        listedName = sanitize(listedName)
        if name != 'defaultTab' and '.html' not in name:
            if not os.path.isdir(thepath):
                os.makedirs(thepath)

            #if (not os.path.exists(thepath + name)):
            if (not os.path.exists(thepath + listedName + '.' + ext)):
                print(urlpath)
                urlResponse = self.session.get(urlpath)
                if urlResponse.status_code == requests.codes.ok:
                    #print("5")
                    #with iopen(thepath + name, 'wb') as file:
                    with iopen(thepath + listedName + '.' + ext, 'wb') as file:
                        file.write(urlResponse.content)
                else:
                    #print(urlResponse.status_code)
                    return False

    #scrapes a page (and all pages on the page)
    #content_id: the content ID number for the page
    #folder_name: the 'name' of the page - this is what the folder will be called when saving documents from this page
    #visitlist: list of previously visited links - to avoid going around in circles
    #path: root path to save all files from the unit
    def recursiveScrape(self, content_id, folder_name, path):
        url = \
            'https://' + blackBoardBaseURL + '/webapps/blackboard/content/listContent.jsp?course_id=_' \
            + self.uid + '_1&content_id=_' + content_id + '_1&mode=reset'

        #request = self.session.get(url)
        request = self.sessionr.get(url)
        sleep(3)
        #soup = BeautifulSoup(request.text, "html.parser")
        soup = BeautifulSoup(self.sessionr.page_source, "html.parser")


        if soup.find("div", {"id":"containerdiv"}).find_all('li') is None:
            print("7")

        ## For attachments
        for htmlLink in soup.find("div", {"id":"containerdiv"}).find_all('li'):
            #print(htmlLink.get('id'))
            if htmlLink.get('id') is None or htmlLink is None or htmlLink.span is None:

                continue

            if 'contentListItem' in htmlLink.get('id'):

                htmlLinkTitle = htmlLink.div.h3.a
                #print(htmlLinkTitle)
                ###############################################
                if not (htmlLink.find_all("ul", {"class":"attachments clearfix"}) == []):

                    for linkAttach in htmlLink.find("ul", {"class":"attachments clearfix"}).find_all("a"):
                        #print(linkAttach)
                        link2 = linkAttach.get('href')

                        if link2 is None or linkAttach is None:
                            print("9")
                            continue

                        passName = None

                        if linkAttach.span is None:
                            if linkAttach.text is None:
                                print("10")
                                continue
                            else:
                                passName = linkAttach.text
                        else:
                            passName = linkAttach.span.string

                        if passName is None:
                            continue

                        if '.pdf' in passName  or '.doc' in passName or 'ppt' in passName or '.mw' in passName or '.vi' in passName or '.mp4' in passName:
                            passName = passName[:passName.rfind(".")]

                        if '.pdf' in link2  or '.doc' in link2 or 'ppt' in link2 or 'xid' in link2 or '.mw' in link2 or '.vi' in link2 or '.mp4' in link2:
                            #print("we are here")
                            #link = string.replace(link, 'https://' + blackBoardBaseURL + '/', '')
                            link2 = link2.replace('https://' + blackBoardBaseURL + '/', '')

                            #link = string.replace(link, '' + blackBoardBaseURL + '/', '')
                            link2 = link2.replace('' + blackBoardBaseURL + '/', '')

                            name = linkAttach.text
                            if '1 slide per page' in name or '4 slides per page' in name:
                                name = urlsplit(link2)[2].split('/')[-1] + '.pdf'
                            try:
                                #print(htmlLink.div.h3.text)
                                self.fetch_document('https://' + blackBoardBaseURL + '/' + link2, folder_name + "/" + sanitize(htmlLink.div.h3.text), path, sanitize(passName))
                            except:
                                print("Error: %s -  %s" % (sys.exc_info()[0], str(sys.exc_info()[1])))

        ## For files
        for htmlLink in soup.find("div", {"id":"containerdiv"}).find_all('li'):
            #print(htmlLink.get('id'))
            if htmlLink.get('id') is None or htmlLink is None or htmlLink.span is None:
                #print("18")
                #print(htmlLink.get('id'))
                #print(htmlLink)
                #print(htmlLink.span)
                continue

            if 'contentListItem' in htmlLink.get('id'):

                htmlLinkTitle = htmlLink.div.h3.a
                #print(htmlLinkTitle)
                ###############################################

                ################################################
                if htmlLinkTitle is None or htmlLink.span is None:
                    #print("16")
                    #print(htmlLinkTitle)
                    #print(htmlLink.span)
                    continue

                #print("19")
                link = htmlLinkTitle.get('href')
                if link is None:
                    print("17")
                    continue

                ############################################
                link2 = htmlLinkTitle.get('href')

                if not(link2 is None or htmlLink is None):
                    #print("20")
                    passName = ""
                    """
                    if htmlLinkTitle.span is None:
                        if htmlLinkTitle.text is None:
                            #print("12")
                            continue
                        else:
                            passName = htmlLinkTitle.text
                    else:
                        passName = htmlLinkTitle.span.string
                    """
                    if htmlLink.div.h3.text is None:
                        print("22")
                        continue
                    else:
                        passName = htmlLink.div.h3.text

                    if passName is None:
                        continue

                    if '.pdf' in passName  or '.doc' in passName or 'ppt' in passName or '.mw' in passName or '.vi' in passName or '.mp4' in passName:
                        passName = passName[:passName.rfind(".")]

                    if '.pdf' in link2  or '.doc' in link2 or 'ppt' in link2 or 'xid' in link2 or '.mw' in link2 or '.vi' in link2 or '.mp4' in link2:
                        #print("here now")
                        #link = string.replace(link, 'https://' + blackBoardBaseURL + '/', '')
                        link2 = link2.replace('https://' + blackBoardBaseURL + '/', '')

                        #link = string.replace(link, '' + blackBoardBaseURL + '/', '')
                        link2 = link2.replace('' + blackBoardBaseURL + '/', '')

                        name = htmlLink.text
                        if '1 slide per page' in name or '4 slides per page' in name:
                            name = urlsplit(link2)[2].split('/')[-1] + '.pdf'
                        try:
                            print("")
                            print(sanitize(passName))
                            self.fetch_document('https://' + blackBoardBaseURL + '/' + link2, folder_name, path, sanitize(passName))
                        except:
                            print("Error: %s -  %s" % (sys.exc_info()[0], str(sys.exc_info()[1])))

        ## For folders
        for htmlLink in soup.find("div", {"id":"containerdiv"}).find_all('li'):
            #print(htmlLink.get('id'))
            if htmlLink.get('id') is None or htmlLink is None or htmlLink.span is None:
                continue

            if 'contentListItem' in htmlLink.get('id'):

                htmlLinkTitle = htmlLink.div.h3.a
                #print(htmlLinkTitle)
                ###############################################

                ################################################
                if htmlLinkTitle is None or htmlLinkTitle.span is None:
                    continue

                link = htmlLinkTitle.get('href')
                if link is None:
                    continue

                ############################################



                #########################################

                if link.startswith('https://' + blackBoardBaseURL + '/webapps/blackboard/content/listContent.jsp?') or link.startswith('/webapps/blackboard/content/listContent.jsp?'):
                    #print("This is the end")
                    link = link.replace('https://' + blackBoardBaseURL + '/webapps/blackboard/content/listContent.jsp?course_id=_'
                                   + self.uid + '_1&content_id=_', '')
                    link = link.replace('/webapps/blackboard/content/listContent.jsp?course_id=_'
                                   + self.uid + '_1&content_id=_', '')
                    link = link.replace('_1&mode=reset', '')
                    link = link.replace('_1', '')
                    try:
                        if link not in self.visitList:
                            self.visitList.append(link)
                            #visitlist = self.recursiveScrape(link, htmlLink.span.string, visitlist, path)
                            self.recursiveScrape(link, folder_name + '/' + sanitize(htmlLinkTitle.span.string), path)
                    except:
                        print("Error: %s -  %s" % (sys.exc_info()[0], str(sys.exc_info()[1])))





        '''
        for htmlLink in soup.find_all('a'):
            link = htmlLink.get('href')
            if link is None:
                continue

            if link.startswith('https://' + blackBoardBaseURL + '/webapps/blackboard/content/listContent.jsp?') or link.startswith('/webapps/blackboard/content/listContent.jsp?'):
                link = link.replace('https://' + blackBoardBaseURL + '/webapps/blackboard/content/listContent.jsp?course_id=_'
                               + self.uid + '_1&content_id=_', '')
                link = link.replace('/webapps/blackboard/content/listContent.jsp?course_id=_'
                               + self.uid + '_1&content_id=_', '')
                link = link.replace('_1&mode=reset', '')
                link = link.replace('_1', '')
                try:
                    if link not in visitlist:
                        visitlist.append(link)
                        #visitlist = self.recursiveScrape(link, htmlLink.span.string, visitlist, path)
                        visitlist = self.recursiveScrape(link, folder_name + '/' + sanitize(htmlLink.span.string), visitlist, path)
                except:
                    print("Error: %s -  %s" % (sys.exc_info()[0], str(sys.exc_info()[1])))
        '''
        return 0

    #starts scraping the unit, path is where it will save the files to
    def startScrape(self, path):
        #lock.acquire()
        self.visitList = []
        print("\n\n" + self.name + ' has Started\n\n')
        #request = self.session.get('https://' + blackBoardBaseURL + '/webapps/blackboard/execute/launcher?type=Course&id=_' + self.uid + '_1')
        self.sessionr.get('https://' + blackBoardBaseURL + '/webapps/blackboard/execute/launcher?type=Course&id=_' + self.uid + '_1')
        sleep(3)

        #soup = BeautifulSoup(request.text, "html.parser")
        soup = BeautifulSoup(self.sessionr.page_source, "html.parser")

        if soup.find("ul", {"id":"courseMenuPalette_contents"}).find_all('a') is None:
            print("5")
        for htmlLink in soup.find("ul", {"id":"courseMenuPalette_contents"}).find_all('a'):

            link = htmlLink.get('href')

            if link is None:
                continue

            passName = ""

            if htmlLink.span is None:
                if htmlLink.text is None:
                    continue
                else:
                    passName = htmlLink.text
            else:
                passName = htmlLink.span.string

            if passName is None:
                continue

            if '.pdf' in passName  or '.doc' in passName or 'ppt' in passName or '.mw' in passName or '.vi' in passName or '.mp4' in passName:
                passName = passName[:passName.rfind(".")]

            if '.pdf' in link  or '.doc' in link or 'ppt' in link or 'xid' in link or '.mw' in link or '.vi' in link or '.mp4' in link:
                link.replace('https://' + blackBoardBaseURL + '', '')
                link.replace('' + blackBoardBaseURL + '', '')
                name = htmlLink.text.replace(' ', '')
                if '1slideperpage' in name or '4slideperpage' in name:
                    name = urlsplit(w)[2].split('/')[-1] + '.pdf'  # tempfix for a particular computing unit
                try:

                    self.fetch_document('https://' + blackBoardBaseURL + '/' + link, '', path, sanitize(passName))
                except:
                    print("Error: %s -  %s" % (sys.exc_info()[0], str(sys.exc_info()[1])))

            elif link.startswith('https://' + blackBoardBaseURL + '/webapps/blackboard/content/listContent.jsp?') or link.startswith('/webapps/blackboard/content/listContent.jsp?'):
                link = link.replace('https://' + blackBoardBaseURL + '/webapps/blackboard/content/listContent.jsp?course_id=_'
                               + self.uid + '_1&content_id=_', '')
                link = link.replace('/webapps/blackboard/content/listContent.jsp?course_id=_'
                               + self.uid + '_1&content_id=_', '')
                link = link.replace('_1&mode=reset', '')
                try:
                    if link not in self.visitList:
                        self.visitList.append(link)
                        self.recursiveScrape(link, sanitize(htmlLink.span.string), path)
                except:
                    print("Error: %s -  %s" % (sys.exc_info()[0], str(sys.exc_info()[1])))
        print("\n" + self.name + ' has finished')
        #lock.release()

#class for managing a blackboard session. Also holds lists of iLectures and units available to your session.
class BlackboardSession():
    def __init__(self, user, password):
        self.session = requests.Session()

        self.options = Options()
        self.options.headless = True
        self.sessionr = webdriver.Chrome(options=self.options)


        self.unitList = []
        self.iLectureList = []

        if (blackBoardBaseURL.find("uoit") != -1):
            self.password = password
        else:
            self.password = base64.b64encode(password)
        self.username = user

        if (blackBoardBaseURL.find("uoit") != -1):
            self.url = 'https://login.uoit.ca/cas/login?service=https%3A%2F%2Fuoit.blackboard.com%2Fwebapps%2Fbb-auth-provider-cas-BBLEARN%2Fexecute%2FcasLogin%3Fcmd%3Dlogin%26authProviderId%3D_123_1%26redirectUrl%3Dhttps%253A%252F%252Fuoit.blackboard.com%252Fwebapps%252Fblackboard%252Fcontent%252FlistContent.jsp%26globalLogoutEnabled%3Dtrue'
        else:
            self.url = 'https://' + blackBoardBaseURL + '/webapps/login/'

        if (blackBoardBaseURL.find("uoit") != -1):
            loginTemp = self.session.get(self.url)
            loginTemp_html = lxml.html.fromstring(loginTemp.text)
            loginTemp_hiddenInputs = loginTemp_html.xpath(r'//form//input[@type="hidden"]')
            self.payload = {x.attrib["name"] : x.attrib["value"] for x in loginTemp_hiddenInputs}
            self.payload['username'] = self.username
            self.payload['password'] = self.password
            self.payload['submit']   = 'LOGIN'

        else:
            self.payload = {
                'login'     : 'Login',
                'action'    : 'login',
                'user_id'   : self.username,
                'encoded_pw': self.password,
                }


        #req = \
        self.sessionr.get(self.url)
        sleep(.5)
        self.sessionr.find_element_by_id("username").send_keys(self.username)
        self.sessionr.find_element_by_id("password").send_keys(self.password)
        self.sessionr.find_element_by_name("submit").click()

        #print(self.session.current_url)
        self.session.post(self.url, data=self.payload, allow_redirects = True)
        #print req.text
        self.getUnitList()
        self.getILectureList()

    #gets all available units for current logged in user
    def getUnitList(self):
        #response = self.session.urlopen('https://' + blackBoardBaseURL + '/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_3_1')

        self.sessionr.get('https://' + blackBoardBaseURL + '/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_3_1')
        sleep(3)
        #soup = BeautifulSoup(response.text, "html.parser")
        soup = BeautifulSoup(self.sessionr.page_source, "html.parser")
        #rint(soup)
        for htmlLink in soup.find_all('a'):
            link = htmlLink.get('href')

            if (link is None):
                continue

            #print(htmlLink)


            if link.startswith(' /webapps/blackboard/execute/launcher?type=Course'):
                link = \
                    link.replace(' /webapps/blackboard/execute/launcher?type=Course&id=_'
                              , '')
                link = link.replace('_1&url=', '')
                #self.unitList.append(BlackboardUnit(link, htmlLink.string.replace('/',''), self.session, self.sessionr))
                self.unitList.append(BlackboardUnit(link, htmlLink.string.replace('/',''), self.session, self.sessionr))

    #gets all available iLectures for current logged in user
    def getILectureList(self):
        try:
            for unit in self.unitList:
                #request = \
                #    self.session.get('https://' + blackBoardBaseURL + '/webapps/blackboard/execute/launcher?type=Course&id=_'
                #           + unit.uid + '_1')

                self.sessionr.get('https://' + blackBoardBaseURL + '/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_3_1')
                sleep(3)

                #soup = BeautifulSoup(request.text, "html.parser")
                soup = BeautifulSoup(self.sessionr.page_source, "html.parser")

                if soup.find_all('a') is None:
                    continue

                for link in soup.find_all('a'):
                    if link.get('href') is None:
                        continue

                    if 'Echo' in link.get('href'):
                        self.iLectureList.append(ILectureUnit(link.get('href'),
                                        soup.find(id='courseMenu_link'
                                        ).get('title')[9:].replace('/','')))
        except:
            print("Error: %s -  %s" % (sys.exc_info()[0], str(sys.exc_info()[1])))


#start the GUI
def load(RootObj):
    x = 10
    y = 10
    Root = Tk()
    App = loading(Root)
    App.pack(expand='yes', fill='both')
    Root.geometry('200x100+' + str(x + 300) + '+' + str(y + 150))
    Root.title('Loading')
    Root.after(100, functools.partial(update, Root, App))
    Root.mainloop()

def update(Root, App):
    App.progress()
    Root.after(100, functools.partial(update, Root, App))

#GUI stuff
class scrapergui(Frame):

    def __init__(self, Master=None, **kw):
        kw['height'] = 110
        kw['width'] = 110
        self.blackboard_session = None
        self.path = '.'
        Frame.__init__(*(self, Master), **kw)
        self.__RootObj = Frame
        self.__Frame2 = Frame(self)
        self.__Frame2.pack(side='top', padx=5, pady=0)
        self.__Label3 = Label(self.__Frame2, text='Directory')
        self.__Label3.pack(side='left', padx=5, pady=0)

        self.__Entry3 = Entry(self.__Frame2, width=50)
        self.__Entry3.pack(side='left', padx=5, pady=0)
        self.__Button3 = Button(self.__Frame2, text='browse', width=10)
        self.__Button3.pack(side='left', padx=5, pady=0)
        self.__Button3.bind('<ButtonRelease-1>',
                            self.__on_Button3_ButRel_1)
        self.__Frame5 = Frame(self)
        self.__Frame5.pack(side='top', padx=5, pady=5)
        self.__Frame3 = Frame(self)
        self.__Frame3.pack(side='top', padx=5, pady=0)
        self.__Frame1 = Frame(self)
        self.__Frame1.pack(side='top', padx=5, pady=5)


        self.__LFrame = Frame(self, padx=5, pady=0)
        self.__LFrame.pack(side='left', padx=5, pady=0)
        self.__RFrame = Frame(self, padx=5, pady=0)
        self.__RFrame.pack(side='left', padx=5, pady=0)
        self.__Frame4 = Frame(self.__LFrame, padx=5, pady=5)
        self.__Frame4.pack(side='top', padx=5, pady=5)
        self.__Label9 = Label(self.__Frame4, text='Blackboard Materials'
                              )
        self.__Label9.pack(side='top', padx=5, pady=0)
        self.__Listbox1 = Listbox(self.__Frame4, width=40,
                                  selectmode=EXTENDED)
        self.__Listbox1.pack(side='top', padx=5, pady=5)
        self.__Button1 = Button(self.__Frame4, text='Scrape', width=20)
        self.__Button1.pack(side='bottom')
        self.__Label1 = Label(self.__Frame5, text='login')
        self.__Label1.pack(side='top', padx=5, pady=0)
        self.__Entry1 = Entry(self.__Frame5)
        self.__Entry1.pack(side='top', padx=5, pady=0)
        self.__Label2 = Label(self.__Frame3, text='pass')
        self.__Label2.pack(side='top', padx=5, pady=0)
        self.__Entry2 = Entry(self.__Frame3, show='*')
        self.__Entry2.pack(side='top', padx=5, pady=0)
        self.__Entry2.bind('<KeyRelease-Return>',
                           self.__on_Button2_ButRel_1)
        self.__Button2 = Button(self.__Frame1, text='Login', width=20)
        self.__Button2.pack(side='top', padx=5, pady=5)
        self.__Button2.bind('<ButtonRelease-1>',
                            self.__on_Button2_ButRel_1)
        self.__Button1.bind('<ButtonRelease-1>',
                            self.__on_Button1_ButRel_1)
        self.__Entry3.insert(0, '.')
        self.__Frame7 = Frame(self.__RFrame)
        self.__Frame7.pack(side='top', padx=5, pady=5)
        self.__Label8 = Label(self.__Frame7, text='iLectures')
        self.__Label8.pack(side='top', padx=5, pady=0)
        self.__Listbox2 = Listbox(self.__Frame7, width=40)
        self.__Listbox2.pack(side='top', padx=5, pady=5)
        self.__Button5 = Button(self.__Frame7, text='goto url',
                                width=20)
        self.__Button5.pack(side='top', padx=5, pady=5)
        self.__Button5.bind('<ButtonRelease-1>',
                            self.__on_Button5_ButRel_1)
        self.__Frame6 = Frame(self.__RFrame)
        self.__Frame6.pack(side='top', padx=5, pady=5)
        self.__Frame10 = Frame(self.__Frame6)
        self.__Frame10.pack(side='top', padx=5, pady=0)
        self.__Frame11 = Frame(self.__Frame6)
        self.__Frame11.pack(side='top', padx=5, pady=0)
        self.__Label4 = Label(self.__Frame10, text='Paste iLecture Video RSS URL Here')
        self.__Label4.pack(side='left', padx=5, pady=0)
        self.__Entry4 = Entry(self.__Frame11)
        self.__Entry4.pack(side='left', padx=5, pady=0)
        self.__Button4 = Button(self.__Frame11, text='scrape', width=10)
        self.__Button4.pack(side='left', padx=5, pady=0)
        self.__Button4.bind('<ButtonRelease-1>',
                            self.__on_Button4_ButRel_1)
        self.__Frame9 = Frame(self.__LFrame)
        self.__Frame9.pack(side='top', padx=5, pady=45)
        self.__Frame8 = Frame(self.__RFrame)
        self.__Frame8.pack(side='top', padx=5, pady=15)


    #open lms to get the rss link
    def __on_Button5_ButRel_1(self, Event=None):
        for lecs in map(int, self.__Listbox2.curselection()):
            url = self.blackboard_session.iLectureList[lecs].link
            webbrowser.open('https://' + blackBoardBaseURL + '' + url, new=1,
                            autoraise=True)

    #scrape ilectures
    def __on_Button4_ButRel_1(self, Event=None):
        self.path = self.__Entry3.get()
        _thread.start_new_thread(ILectureUnit.scrape_ilectures, (self.__Entry4.get(), self.path))

    #login and get unit list
    def __on_Button2_ButRel_1(self, Event=None):
        self.blackboard_session = BlackboardSession(self.__Entry1.get(), self.__Entry2.get())
        self.__Listbox1.delete(0, END)
        self.__Listbox2.delete(0, END)
        for ii in self.blackboard_session.unitList:
            self.__Listbox1.insert(END, ii.name)
        for ii in self.blackboard_session.iLectureList:
            self.__Listbox2.insert(END, ii.name)

    #GUI browse button
    def __on_Button3_ButRel_1(self, Event=None):
        filename = askdirectory()
        self.__Entry3.delete(0, END)
        self.__Entry3.insert(0, filename)

    #scrape units selected
    def __on_Button1_ButRel_1(self, Event=None):
        self.path = self.__Entry3.get()
        #lock = _thread.allocate_lock()
        for unit in map(int, self.__Listbox1.curselection()):
            #while lock.locked():
            #    sleep(1)
            bbunit = self.blackboard_session.unitList[unit]
            bbunit.startScrape(self.path)
            #_thread.start_new_thread(bbunit.startScrape, (self.path, lock,))




# Adjust sys.path so we can find other modules of this project
import sys
if '.' not in sys.path:
    sys.path.append('.')

# Put lines to import other modules of this project here
#init the program
if __name__ == '__main__':
    Root = Tk()
    App = scrapergui(Root)
    App.pack(expand='yes', fill='both')
    Root.geometry('600x600+10+10')
    Root.title('Blackboard/iLecture Scraper - By Jason Giancono')
    Root.mainloop()
