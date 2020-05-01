from shared import blackBoardBaseURL

from bs4 import BeautifulSoup
import lxml.html

import requests
from selenium import webdriver
#import seleniumrequests as webdriver
from selenium.webdriver.firefox.options import Options
from time import sleep


from base64 import b64encode

from BlackboardUnit import BlackboardUnit
from ILectureUnit import ILectureUnit

#class for managing a blackboard session. Also holds lists of iLectures and units available to your session.
class BlackboardSession():
    def __init__(self, user, password):
        self.session = requests.Session()

        self.options = Options()
        self.options.headless = False
        profile = webdriver.FirefoxProfile("/home/mitchell/.mozilla/firefox/pl0ce26f.seleniumNoDownloads")
        self.sessionr = webdriver.Firefox(options=self.options, firefox_profile=profile)


        self.unitList = []
        self.links = []
        self.iLectureList = []

        if (blackBoardBaseURL.find("uoit") != -1):
            self.password = password
        else:
            self.password = b64encode(password)

        self.username = user

        self.url = 'https://' + blackBoardBaseURL + '/webapps/login/'

        if (blackBoardBaseURL.find("uoit") != -1):
            loginTemp = self.session.get(self.url)
            #print(loginTemp.content)
            sleep(5)

            loginTemp_html = lxml.html.fromstring(loginTemp.text)
            loginTemp_hiddenInputs = loginTemp_html.xpath(r'//form//input[@type="hidden"]')

            #self.payload = {x.attrib["name"] : x.attrib["value"] if 'value' in x.attrib else '':'' for x in loginTemp_hiddenInputs}

            self.payload = {}

            for x in loginTemp_hiddenInputs:
                if 'value' in x.attrib:
                    self.payload[x.attrib['name']] = x.attrib['value']


            self.payload['UserName'] = 'oncampus.local\\' + self.username
            self.payload['Password'] = self.password
            #self.payload['submit']   = 'LOGIN'

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
        self.sessionr.find_element_by_id("userNameInput").send_keys(self.username)
        self.sessionr.find_element_by_id("passwordInput").send_keys(self.password)
        self.sessionr.find_element_by_id("submitButton").click()

        """
        headers = {
            "User-Agent" : self.sessionr.execute_script("return navigator.userAgent;")
        }
        print(headers)
        self.session.headers.update(headers)
        """
        #for cookie in self.sessionr.get_cookies():
        #    self.session.cookies.update({cookie['name']:cookie['value']})

        #print(self.session.current_url)
        r = self.session.get(self.url, allow_redirects=True)

        self.session.post(r.url, data=self.payload, allow_redirects=True)

        r = self.session.get('https://' + blackBoardBaseURL)


        sleep(1)
        print(r.content)

        #print req.text
        self.getUnitList()
        self.getILectureList()

    #gets all available units for current logged in user
    def getUnitList(self):
        #response = self.session.urlopen('https://' + blackBoardBaseURL + '/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_3_1')

        self.sessionr.get('https://' + blackBoardBaseURL + '/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_3_1')
        sleep(7)
        #soup = BeautifulSoup(response.text, "html.parser")
        soup = BeautifulSoup(self.sessionr.page_source, "html.parser")
        #rint(soup)
        for htmlLink in soup.find_all('a'):
            link = htmlLink.get('href')

            if (link is None):
                continue

            #print(htmlLink)


            if link.startswith('/webapps/blackboard/execute/launcher?type=Course'):
                link = \
                    link.replace('/webapps/blackboard/execute/launcher?type=Course&id=_'
                              , '')
                link = link.replace('_1&url=', '')
                #self.unitList.append(BlackboardUnit(link, htmlLink.string.replace('/',''), self.session, self.sessionr))
                if link not in self.links:
                    self.unitList.append(BlackboardUnit(link, htmlLink.string.replace('/',''), self.session, self.sessionr))
                    self.links.append(link)

    #gets all available iLectures for current logged in user
    def getILectureList(self):
        try:
            return
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

    def returnSessions(self):
        return [self.session, self.sessionr]
