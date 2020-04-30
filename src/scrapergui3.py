#!/usr/bin/python3
# -*- coding: utf-8 -*-

from tkinter import *
import tkinter
import tkinter.messagebox
import _thread
import webbrowser
from tkinter.filedialog import askdirectory

import os

import datetime

import getpass
import multiprocessing
import functools

from platform import system as systemName

from ILectureUnit import ILectureUnit
from BlackboardUnit import BlackboardUnit
from BlackboardSession import BlackboardSession

#import pdb; pdb.set_trace()

if "Darwin" in systemName():
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
