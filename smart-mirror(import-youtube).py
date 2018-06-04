# -*- coding:utf-8 -*-
# smartmirror.py
# requirements
# requests, feedparser, traceback, Pillow

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
from tkinter import *
import locale
import threading
import time
import requests
import json
import traceback
import feedparser
import sys
from pyowm import OWM
import os
import urllib
import urllib.request
import pafy
import vlc

from tkinter import ttk
from tkinter.filedialog import askopenfilename

from PIL import Image, ImageTk
from contextlib import contextmanager

import pathlib
import time
import platform

LOCALE_LOCK = threading.Lock()

DEVELOPER_KEY = "AIzaSyBfxBMi3ytFSrcBxbKw8CaerNOM8uxsTZo"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

ui_locale = ''  # e.g. 'fr_FR' fro French, '' as default
time_format = 12  # 12 or 24
date_format = "%b %d, %Y"  # check python doc for strftime() for options
news_country_code = 'us'
weather_api_token = '<TOKEN>'  # create account at https://darksky.net/dev/
weather_lang = 'en'  # see https://darksky.net/dev/docs/forecast for full list of language parameters values
weather_unit = 'us'  # see https://darksky.net/dev/docs/forecast for full list of unit parameters values
lat = None  # Set this if IP location lookup does not work for you (must be a string)
lon = None  # Set this if IP location lookup does not work for you (must be a string)
loccity = None  # Set this if IP location City Name
locregion = None  # Set this if IP location Region Name
xlarge_text_size = 94
large_text_size = 48
medium_text_size = 28
small_text_size = 18


@contextmanager
def setlocale(name):  # thread proof function to work with locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)


# maps open weather icons to
# icon reading is not impacted by the 'lang' parameter
icon_lookup = {
    '01d': "assets/Sun.png",  # clear sky day
    '01n': "assets/Sun.png",
    '02d': "assets/Cloud.png",  # cloudy day
    '02n': "assets/Cloud.png",
    '03d': "assets/Sun.png",
    '04d': "assets/Cloud.png",
    '10d': "assets/Rain.png",  # rain day
    '10n': "assets/Rain.png",
    '09d': "assets/Rain.png",  # rain day
    '09n': "assets/Rain.png",
    '13d': "assets/Snow.png",  # snow day
    '13n': "assets/Snow.png",
    '03n': "assets/Snow.png",  # sleet day
    '04n': "assets/PartlyMoon.png",  # scattered clouds night
    '11n': "assets/Storm.png",  # thunderstorm
}


class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initialize day of week
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)
        # initialize date label
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p')  # hour in 12h format
            else:
                time2 = time.strftime('%H:%M')  # hour in 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.config(text=date2)
            # calls itself every 200 milliseconds
            # to update the time display as needed
            # could use >200 ms, but display gets jerky
            self.timeLbl.after(200, self.tick)


class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.temperature = ''
        self.forecast = ''
        self.location = ''
        self.currently = ''
        self.icon = ''
        self.degreeFrm = Frame(self, bg="black")
        self.degreeFrm.pack(side=TOP, anchor=W)
        self.temperatureLbl = Label(self.degreeFrm, font=('Helvetica', xlarge_text_size), fg="white", bg="black")
        self.temperatureLbl.pack(side=LEFT, anchor=N)
        self.iconLbl = Label(self.degreeFrm, bg="black")
        self.iconLbl.pack(side=LEFT, anchor=N, padx=20)
        self.currentlyLbl = Label(self, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.currentlyLbl.pack(side=TOP, anchor=W)
        self.forecastLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.forecastLbl.pack(side=TOP, anchor=W)
        self.locationLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.locationLbl.pack(side=TOP, anchor=W)
        self.get_weather()

    def get_weather(self):
        try:
            global lat
            global lon

            weather_api_token = '5e4e45f4e6c9b6a651f7130ab2f192ca'
            owm = OWM(weather_api_token, language='ko')

            # get location
            if (lat is None and lon is None):
                global loccity
                global locregion
                url = 'https://maps.googleapis.com/maps/api/geocode/json'
                params = {'sensor': 'false', 'address': 'Yonam University, 가좌동 진주시 경상남도'}
                r = requests.get(url, params=params)
                results = r.json()['results']
                location = results[0]['geometry']['location']

                lat = location['lat']
                lon = location['lng']

                loccity = results[0]['address_components'][2]['long_name']
                locregion = results[0]['address_components'][3]['long_name']

            obs = owm.weather_at_coords(lat, lon)

            w = obs.get_weather()

            location2 = "%s, %s" % (loccity, locregion)
            temperature2 = w.get_temperature(unit='celsius')['temp']
            weather_icon_name = w.get_weather_icon_name()

            print(weather_icon_name)

            icon2 = None

            if weather_icon_name in icon_lookup:
                icon2 = icon_lookup[weather_icon_name]


            if icon2 is not None:
                # __init에서 지정한 self.icon 값과 icon2 값이 같은지 비교하고,
                # 다르면 self.icon 값에 icon2값을 대입, self.icon값은 이미지 경로와
                # 이미지 이름이 있는 String 값이 저장된다.
                if self.icon != icon2:
                    self.icon = icon2
                    image = Image.open("assets/Newspaper.png")
                    image = image.resize((50, 50), Image.ANTIALIAS)

                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)
                    self.iconLbl.config(image=photo)

                    self.iconLbl.image = photo

            else:
                # remove image
                self.iconLbl.config(image='')

            # if self.currently != currently2:
            #    self.currently = currently2

            #    self.currentlyLbl.config(text=currently2)

            # if self.forecast != forecast2:
            #    self.forecast = forecast2

            #    self.forecastLbl.config(text=forecast2)
            if self.temperature != temperature2:
                self.temperature = temperature2
                self.temperatureLbl.config(text=temperature2)

            if self.location != location2:
                if location2 == ", ":
                    self.location = "Cannot Pinpoint Location"
                    self.locationLbl.config(text="Cannot Pinpoint Location")
                else:
                    self.location = location2
                    self.locationLbl.config(text=location2)
        except Exception as e:
            traceback.print_exc()
            print("Error: %s. Cannot get weather." % e)

        self.after(600000, self.get_weather)

    @staticmethod
    def convert_kelvin_to_fahrenheit(kelvin_temp):
        return 1.8 * (kelvin_temp - 273) + 32


class News(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.config(bg='black')
        self.title = 'News'  # 'News' is more internationally generic
        self.newsLbl = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.newsLbl.pack(side=TOP, anchor=W)
        self.headlinesContainer = Frame(self, bg="black")
        self.headlinesContainer.pack(side=TOP)
        self.get_headlines()

    def get_headlines(self):
        try:
            # remove all children
            for widget in self.headlinesContainer.winfo_children():
                widget.destroy()
            if news_country_code == None:
                headlines_url = "https://news.google.com/news?ned=us&output=rss"
            else:
                headlines_url = "https://news.google.com/news?ned=%s&output=rss" % news_country_code

            feed = feedparser.parse(headlines_url)

            for post in feed.entries[0:5]:
                headline = NewsHeadline(self.headlinesContainer, post.title)
                headline.pack(side=TOP, anchor=W)
        except Exception as e:
            traceback.print_exc()
            print("Error: %s. Cannot get news." % e)

        self.after(600000, self.get_headlines)


class NewsHeadline(Frame):
    def __init__(self, parent, event_name=""):
        Frame.__init__(self, parent, bg='black')

        image = Image.open("assets/Newspaper.png")
        image = image.resize((25, 25), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.iconLbl = Label(self, bg='black', image=photo)
        self.iconLbl.image = photo
        self.iconLbl.pack(side=LEFT, anchor=N)

        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white",
                                  bg="black")
        self.eventNameLbl.pack(side=LEFT, anchor=N)


class Calendar(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.title = 'Calendar Events'
        self.calendarLbl = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.calendarLbl.pack(side=TOP, anchor=E)
        self.calendarEventContainer = Frame(self, bg='black')
        self.calendarEventContainer.pack(side=TOP, anchor=E)
        self.get_events()

    def get_events(self):
        # TODO: implement this method
        # reference https://developers.google.com/google-apps/calendar/quickstart/python

        # remove all children
        for widget in self.calendarEventContainer.winfo_children():
            widget.destroy()

        calendar_event = CalendarEvent(self.calendarEventContainer)
        calendar_event.pack(side=TOP, anchor=E)
        pass


class CalendarEvent(Frame):
    def __init__(self, parent, event_name="Event 1"):
        Frame.__init__(self, parent, bg='black')
        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white",
                                  bg="black")
        self.eventNameLbl.pack(side=TOP, anchor=E)


class FullscreenWindow:

    def __init__(self, root):
        self.tk = root
        self.tk.configure(background='black')
        self.topFrame = Frame(self.tk, background='black')
        self.bottomFrame = Frame(self.tk, background='black')
        self.topFrame.pack(side=TOP, fill=BOTH, expand=YES)
        self.bottomFrame.pack(side=BOTTOM, fill=BOTH, expand=YES)
        self.state = False
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=100, pady=60)
        # weather
        self.weather = Weather(self.topFrame)
        self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)
        # news
        self.news = News(self.bottomFrame)
        self.news.pack(side=LEFT, anchor=S, padx=100, pady=60)
        # calender - removing for now
        # self.calender = Calendar(self.bottomFrame)
        # self.calender.pack(side = RIGHT, anchor=S, padx=100, pady=60)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"

def youtube_search(options): #첫 번째 파라미터인 mid 잠시 주석처리.
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
  developerKey=DEVELOPER_KEY)

  youtube_video_url = "https://www.youtube.com/watch?v={0}"
  youtube_playlist_url = "https://www.youtube.com/playlist?list={0}"
  youtub_channel_url = "https://www.youtube.com/channel/{0}"

  # Call the search.list method to retrieve results associated with the
  # specified Freebase topic.
  search_response = youtube.search().list(
    #topicId=mid,
    #type=options.indent,
    q = options.query,
    part="id,snippet",
    maxResults=options.limit
  ).execute()

  videos = [] #if type is video,.
  playlists = [] #if type is playlist.
  channels = [] #if type is channel.

  # Print the title and ID of each matching resource.
  for search_result in search_response.get("items", []):
    if search_result["id"]["kind"] == "youtube#video":
      videos.append('%s' % (search_result['id']['videoId'])) # video input
    elif search_result["id"]["kind"] == "youtube#channel":
      playlists.append('%s' % (search_result['id']['channelId']))
    elif search_result["id"]["kind"] == "youtube#playlist":
      playlists.append('%s' % (search_result['id']['playlistId']))

  url = ""

  if videos:
    url = youtube_video_url.format(videos[0])
  elif playlists:
    url = youtube_playlist_url.format(playlists[0])
  elif channels:
    url = youtub_channel_url.format(channels[0])

  video = pafy.new(url)
  best = video.getbest()
  playurl = best.url

  return playurl

class Player(Frame):
    """The main windwo has to deal with events.
    """
    #root를 parent로 하는 Frame만들기.
    def __init__(self, parent, youtube_url, title="tk_vlc"):
        Frame.__init__(self, parent)
        self.parent = parent

        self.youtube_url = youtube_url
        self.player = None
        self.videopanel = ttk.Frame(self.parent)
        self.canvas = Canvas(self.videopanel).pack(fill=BOTH,expand=1)
        self.videopanel.pack(fill=None, expand=1)

        ctrlpanel = ttk.Frame(self.parent)
        pause = ttk.Button(ctrlpanel, text="Pause", command=self.OnPause)
        #play = ttk.Button(ctrlpanel, text="Play", command=self.OnPlay)
        stop = ttk.Button(ctrlpanel, text="Stop", command=self.OnStop)
        volume = ttk.Button(ctrlpanel, text="Volume", command=self.OnSetVolume)
        pause.pack(side=LEFT)
        #play.pack(side=Tk.LEFT)
        stop.pack(side=LEFT)
        volume.pack(side=LEFT)
        self.volume_var = IntVar()
        self.volslider = Scale(ctrlpanel, variable=self.volume_var, command=self.volume_sel, from_=0, to=100, orient=HORIZONTAL, length=100)
        self.volslider.pack(side=LEFT)
        ctrlpanel.pack(side=BOTTOM)

        # VLC player controls
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()
        print("1")
        self.OnPlay()
        # self.timer = ttkTimer(self.OnTimer, 1.0)
        # self.timer.start()
        # self.parent.update()

    def OnPlay(self):
        """Toggle the status to Play/Pause.
        If no file is loaded, open the dialog window.
        """
        # check if there is a file to play, otherwise open a
        # Tk.FileDialog to select a file
        print("1-1")


        self.Media = self.Instance.media_new(self.youtube_url)
        self.player.set_media(self.Media)

        # set the window id where to render VLC's video output
        if platform.system() == 'Windows':
            print("1-3")
            self.player.set_hwnd(self.GetHandle())
        else:
            print("1-4")
            self.player.set_xwindow(self.GetHandle())  # this line messes up windows
        # FIXME: this should be made cross-platform

        # Try to launch the media, if this fails display an error message
        if self.player.play() == -1:
            print("1-6")
            self.errorDialog("Unable to play.")

    def GetHandle(self):
        return self.videopanel.winfo_id()

    def OnPause(self):
        """Pause the player.
        """
        self.player.pause()

    def OnStop(self):
        """Stop the player.
        """
        self.player.stop()
        # reset the time slider

    def volume_sel(self, evt):
        if self.player == None:
            return
        volume = self.volume_var.get()
        if volume > 100:
            volume = 100
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

    def OnToggleVolume(self, evt):
        """Mute/Unmute according to the audio button.
        """
        is_mute = self.player.audio_get_mute()

        self.player.audio_set_mute(not is_mute)
        # update the volume slider;
        # since vlc volume range is in [0, 200],
        # and our volume slider has range [0, 100], just divide by 2.
        self.volume_var.set(self.player.audio_get_volume())

    def OnSetVolume(self):
        """Set the volume according to the volume sider.
        """
        volume = self.volume_var.get()
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if volume > 100:
            volume = 100
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

    def errorDialog(self, errormessage):
        """Display a simple error dialog.
        """
        Tk.tkMessageBox.showerror(self, 'Error', errormessage)

def Tk_get_root():
    #Tk의 root 만들어주는 함수.
    #attribute가 있는지 확인하고 있으면 있는 것을 그대로, 없으면 rootf를 만들어서 저장.
    if not hasattr(Tk_get_root, "root"):
        Tk_get_root.root = Tk()
    return Tk_get_root.root

#창을 닫을 시 발생하는 이벤트에 대한 이벤트 핸들러의 역할.
def _quit():
    print("_quit: bye")
    root = Tk_get_root()
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    os._exit(1)

def display_youtube():
    youtube_url = ""
    print("Search Youtube Key word : ")
    query = input()

    argparser.add_argument("--query", help="kgsearch search term", default=query)
    argparser.add_argument("--limit", help="Max YouTube results", default=10)
    argparser.add_argument("--indent", help="YouTube result type: video, playlist, or channel", default="True")
    args = argparser.parse_args()

    try:
        youtube_url = youtube_search(args)
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

    # root.mainloop()

    player = Player(root, youtube_url, title="YouTube Display")

if __name__ == '__main__':
    #FullscreenWindow에서 기본 화면 설정을 한다.
    #Fullscreen 객체가 형성되면 참조값이 w변수에 저장.
    root = Tk_get_root()
    FullscreenWindow(root)
    #FullscreenWindow 객체가 생성되면서 속성으로 tk를 생성하는데 그 값을 root에 넣는다.
    root.protocol("WM_DELETE_WINDOW", _quit)

    #root.mainloop()

    # youtube_url = ""
    # print("Search Youtube Key word : ")
    # query = input()
    #
    # argparser.add_argument("--query", help="kgsearch search term", default=query)
    # argparser.add_argument("--limit", help="Max YouTube results", default=10)
    # argparser.add_argument("--indent", help="YouTube result type: video, playlist, or channel", default="True")
    # args = argparser.parse_args()
    #
    # try:
    #     youtube_url = youtube_search(args)
    # except HttpError as e:
    #     print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
    #
    # #root.mainloop()
    #
    # player = Player(root, youtube_url, title="YouTube Display")

    t1 = threading.Thread(target=display_youtube)
    t1.start()

    root.mainloop()