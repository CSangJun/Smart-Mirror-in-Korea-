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
FREEBASE_SEARCH_URL = "https://kgsearch.googleapis.com/v1/entities:search?%s"

def get_topic_id(options):
  # Retrieve a list of Freebase topics associated with the provided query term.
  freebase_params = dict(query=options.query, limit=options.limit, indent=options.indent, key=DEVELOPER_KEY)
  freebase_url = FREEBASE_SEARCH_URL % urllib.parse.urlencode(freebase_params)
  print(freebase_url)
  freebase_response = json.loads(urllib.request.urlopen(freebase_url).read())


  if len(freebase_response["itemListElement"]) == 0:
     exit("No matching terms were found in Freebase.")

  # 매칭된 리스트를 보여준다.
  mids = []
  index = 1
  print("The following topics were found:")
  for result in freebase_response["itemListElement"]:
    mids.append(result["result"]['@id'])#result.get(key,default)
    print("  %2d. %s" % (index, (result.get("result")).get("name")))
    index += 1

  # Display a prompt for the user to select a topic and return the topic ID
  # of the selected topic.
  mid = None
  while mid is None:
    index = input("Enter a topic number to find related YouTube %ss: " %
      options.indent)
    try:
      mid = mids[int(index) - 1]
    except ValueError:
      pass
  return mid


def youtube_search(mid, options):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
  developerKey=DEVELOPER_KEY)

  youtube_video_url = "https://www.youtube.com/watch?v={0}"
  youtube_playlist_url = "https://www.youtube.com/playlist?list={0}"

  # Call the search.list method to retrieve results associated with the
  # specified Freebase topic.
  search_response = youtube.search().list(
    topicId=mid,
    type=options.indent,
    part="id,snippet",
    maxResults=options.limit
  ).execute()

  print("Debug Test print search_response")
  print(search_response)

  videos = [] #if type is video,.
  playlists = [] #if type is playlist.
  channels = [] #if type is channel.

  # Print the title and ID of each matching resource.
  for search_result in search_response.get("items", []):
    if search_result["id"]["kind"] == "youtube#video":
      print("video")
      videos.append('%s' % (search_result['id']['videoId'])) # video input
    elif search_result["id"]["kind"] == "youtube#channel":
      print("channel")
      playlists.append('%s' % (search_result['id']['channelId']))
    elif search_result["id"]["kind"] == "youtube#playlist":
      print("playlist")
      playlists.append('%s' % (search_result['id']['playlistId']))

  url = ""

  if videos:
    url = youtube_video_url.format(videos[0])
  elif playlists:
    url = youtube_playlist_url.format(playlists[0])

  for i in videos:
    print(i)

  video = pafy.new(url)
  best = video.getbest()
  playurl = best.url
  print(playurl)

  vlc_instance = vlc.Instance()
  player = vlc_instance.media_player_new()
  Media = vlc_instance.media_new(playurl)
  Media.get_mrl()
  player.set_media(Media)
  player.play()

#Frame을 상속받는 Player 클래스 선언.
class Player(Tk.Frame):
    """The main windwo has to deal with events.
    """
    #root를 parent로 하는 Frame만들기.
    def __init__(self, parent, title="tk_vlc", playurl=""):
        Tk.Frame.__init__(self, parent)

        self.parent = parent
        self.parent.title(title)

        self.player = None
        self.videopanel = ttk.Frame(self.parent)
        self.canvas = Tk.Canvas(self.videopanel).pack(fill=Tk.BOTH,expand=1)
        self.videopanel.pack(fill=Tk.BOTH,expand=1)

        ctrlpanel = ttk.Frame(self.parent)
        pause = ttk.Button(ctrlpanel, text="Pause", command=self.OnPause)
        play = ttk.Button(ctrlpanel, text="Play", command=self.OnPlay)
        stop = ttk.Button(ctrlpanel, text="Stop", command=self.OnStop)
        volume = ttk.Button(ctrlpanel, text="Volume", command=self.OnSetVolume)
        pause.pack(side=Tk.LEFT)
        play.pack(side=Tk.LEFT)
        stop.pack(side=Tk.LEFT)
        volume.pack(side=Tk.LEFT)
        self.volume_var = Tk.IntVar()
        self.volslider = Tk.Scale(ctrlpanel, variable=self.volume_var, command=self.volume_sel, from_=0, to=100, orient=Tk.HORIZONTAL, length=100)
        self.volslider.pack(side=Tk.LEFT)
        ctrlpanel.pack(side=Tk.BOTTOM)

        # VLC player controls
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()

        # self.timer = ttkTimer(self.OnTimer, 1.0)
        # self.timer.start()
        # self.parent.update()

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
    playurl = ""
    print("검색을 하세요.")
    query = input()
    argparser.add_argument("--query", help="kgsearch search term", default="Taylor Swift")
    argparser.add_argument("--limit", help="Max YouTube results", default=10)
    argparser.add_argument("--indent",help="YouTube result type: video, playlist, or channel", default="True")
    args = argparser.parse_args()
    print(args)
    mid = get_topic_id(args)
    try:
        youtube_search(mid, args)
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

    player = Player(root, title="YouTube Display")
    # show the player window centred and run the application
    root.mainloop()