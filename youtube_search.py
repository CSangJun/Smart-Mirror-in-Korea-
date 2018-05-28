#!/usr/bin/python

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import sys
import json
import urllib
import urllib.request
# if sys.version_info[0] == 2:
#     import urllib
#     urlopen = urllib.urlopen
# else:
#     import urllib.request
#     urlopen = urllib.request.urlopen


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
  freebase_response = json.loads(urllib.request.urlopen(freebase_url).read())


  # if len(freebase_response["result"]) == 0:
  #   exit("No matching terms were found in Freebase.")

  # Display the list of matching Freebase topics.
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

  # Call the search.list method to retrieve results associated with the
  # specified Freebase topic.
  search_response = youtube.search().list(
    topicId=mid,
    type=options.indent,
    part="id,snippet",
    maxResults=options.limit
  ).execute()

  # Print the title and ID of each matching resource.
  for search_result in search_response.get("items", []):
    if search_result["id"]["kind"] == "youtube#video":
      print("%s (%s)" % (search_result["snippet"]["title"],
        search_result["id"]["videoId"]))
    elif search_result["id"]["kind"] == "youtube#channel":
      print("%s (%s)" % (search_result["snippet"]["title"],
        search_result["id"]["channelId"]))
    elif search_result["id"]["kind"] == "youtube#playlist":
      print("%s (%s)" % (search_result["snippet"]["title"],
        search_result["id"]["playlistId"]))


if __name__ == "__main__":
  print("검색을 하세요.")
  query = input()
  argparser.add_argument("--query", help="kgsearch search term", default="Taylor Swift")
  argparser.add_argument("--limit", help="Max YouTube results",
    default=10)
  argparser.add_argument("--indent",
    help="YouTube result type: video, playlist, or channel", default="True")
  args = argparser.parse_args()

  mid = get_topic_id(args)
  try:
    youtube_search(mid, args)
  except HttpError as e:
    print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))