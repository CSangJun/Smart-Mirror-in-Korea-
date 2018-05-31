#!/usr/bin/python

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import sys
import json
import urllib
import urllib.request
import pafy
import vlc
import sys
if sys.version_info[0] < 3:
    import Tkinter as Tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename
else:
    import tkinter as Tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename

import os
import pathlib
from threading import Thread, Event
import time
import platform


# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "AIzaSyBfxBMi3ytFSrcBxbKw8CaerNOM8uxsTZo"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
#FREEBASE_SEARCH_URL = "https://kgsearch.googleapis.com/v1/entities:search?%s"

# def get_topic_id(options):
#   # Retrieve a list of Freebase topics associated with the provided query term.
#   freebase_params = dict(query=options.query, limit=options.limit, indent=options.indent, key=DEVELOPER_KEY)
#   print(freebase_params)
#   freebase_url = FREEBASE_SEARCH_URL % urllib.parse.urlencode(freebase_params)
#   print(freebase_url)
#   freebase_response = json.loads(urllib.request.urlopen(freebase_url).read())
#   print(freebase_response)
#
#
#   if len(freebase_response["itemListElement"]) == 0:
#      exit("No matching terms were found in Freebase.")
#
#   # 매칭된 리스트를 보여준다.
#   mids = []
#   index = 1
#   print("The following topics were found:")
#   for result in freebase_response["itemListElement"]:
#     mids.append(result["result"]['@id'])#result.get(key,default)
#     print("  %2d. %s" % (index, (result.get("result")).get("name")))
#     index += 1
#
#   # Display a prompt for the user to select a topic and return the topic ID
#   # of the selected topic.
#   mid = None
#   while mid is None:
#     index = input("Enter a topic number to find related YouTube %ss: " %
#       options.indent)
#     try:
#       mid = mids[int(index) - 1]
#     except ValueError:
#       pass
#   return mid


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

#Frame을 상속받는 Player 클래스 선언.
class Player(Tk.Frame):
    """The main windwo has to deal with events.
    """
    #root를 parent로 하는 Frame만들기.
    def __init__(self, parent, youtube_url, title="tk_vlc"):
        Tk.Frame.__init__(self, parent)

        self.parent = parent
        self.parent.title(title)

        self.youtube_url = youtube_url
        self.player = None
        self.videopanel = ttk.Frame(self.parent)
        self.canvas = Tk.Canvas(self.videopanel).pack(fill=Tk.BOTH,expand=1)
        self.videopanel.pack(fill=Tk.BOTH,expand=1)

        ctrlpanel = ttk.Frame(self.parent)
        pause = ttk.Button(ctrlpanel, text="Pause", command=self.OnPause)
        #play = ttk.Button(ctrlpanel, text="Play", command=self.OnPlay)
        stop = ttk.Button(ctrlpanel, text="Stop", command=self.OnStop)
        volume = ttk.Button(ctrlpanel, text="Volume", command=self.OnSetVolume)
        pause.pack(side=Tk.LEFT)
        #play.pack(side=Tk.LEFT)
        stop.pack(side=Tk.LEFT)
        volume.pack(side=Tk.LEFT)
        self.volume_var = Tk.IntVar()
        self.volslider = Tk.Scale(ctrlpanel, variable=self.volume_var, command=self.volume_sel, from_=0, to=100, orient=Tk.HORIZONTAL, length=100)
        self.volslider.pack(side=Tk.LEFT)
        ctrlpanel.pack(side=Tk.BOTTOM)

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
    #attribute가 있는지 확인하고 있으면 있는 것을 그대로, 없으면 rootf를 만들어서 저장.
    if not hasattr(Tk_get_root, "root"):
        Tk_get_root.root = Tk.Tk()
    return Tk_get_root.root

def _quit():
    print("_quit: bye")
    root = Tk_get_root()
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    os._exit(1)

if __name__ == "__main__":
    root = Tk_get_root()
    root.protocol("WM_DELETE_WINDOW", _quit)
    youtube_url = ""
    print("검색을 하세요.")
    query = input()
    argparser.add_argument("--query", help="kgsearch search term", default=query)
    argparser.add_argument("--limit", help="Max YouTube results", default=10)
    argparser.add_argument("--indent",help="YouTube result type: video, playlist, or channel", default="True")
    args = argparser.parse_args()

    #mid = get_topic_id(args)
    try:
        #youtube_url = youtube_search(mid, args)
        youtube_url = youtube_search(args)
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

    player = Player(root, youtube_url, title="YouTube Display")
    # show the player window centred and run the application
    root.mainloop()