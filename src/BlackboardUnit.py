from shared import sanitize, blackBoardBaseURL

from bs4 import BeautifulSoup
from io import open as iopen
from urllib.parse import urlsplit
import urllib.parse

import requests

#urllib.request, urllib.error

import re, pdfkit, os, sys

from time import sleep


#class for scraping blackboard units, simply initialise and call startScrape
class BlackboardUnit():
    def __init__(self, uid, name, session, sessionr):
        self.uid = uid
        self.name = name
        self.session = session
        self.sessionr = sessionr
        self.visitList = []
        self.cssHeader=""
        with open("header.css", "r") as cssFile:
            for x in cssFile.readlines():
                self.cssHeader+=x

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

        #soupTemp = BeautifulSoup(self.sessionr.page_source,features="lxml")

        ## for pdfs

        for htmlLink in soup.find("div", {"id":"containerdiv"}).find_all('li'):
            if htmlLink.get('id') is None or htmlLink is None:
                continue

            if 'contentListItem' in htmlLink.get('id'):
                if htmlLink.text != htmlLink.div.h3.text:
                    tempT = self.cssHeader + htmlLink.prettify( formatter="html" )
                    #tempT = htmlLink.prettify( formatter="html" )
                    options = {
                    'quiet': ''
                    }
                    #pdfkit.from_string(temp, "temp_" + str(number) + ".pdf", options=options)
                    tempT = pdfkit.from_string(tempT, False, options=options)

                    #temp =""
                    #with open("temp_" + str(number) + ".pdf", "rb") as byteObject:
                    #    temp = byteObject.read()
                    tempPath = path + '/' + self.name + '/'

                    if len(folder_name) > 0:
                        tempPath += folder_name + '/'

                    if not os.path.isdir(tempPath):
                        os.makedirs(tempPath)

                    if not (os.path.isfile(tempPath + sanitize(htmlLink.div.h3.text) + ".pdf")):
                        with open(tempPath + sanitize(htmlLink.div.h3.text) + ".pdf", "wb") as file:
                            file.write(tempT)
                            file.flush()



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
