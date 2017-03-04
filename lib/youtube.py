#!/usr/bin/env python
# coding=utf-8

# Tested with python 2.7 only.

# How to get a Google API Key and OAuth2 credentials:
# 1) Go to https://console.developers.google.com
# 2) Create a project, eg. "JLM Video Captions"
# 3) Set the YouTube data API to "ON"
# 4) Create a public access key
# 5) Copy it to config/api-key.txt
# 6) Create an OAuth2 Client Id
# 7) Copy config/client-secrets.json.dist to config/client-secrets.json
# 8) Fill client_id and client_secret with your OAuth2 credentials


###############################################################################

import os
import re
import datetime
import dateutil.parser
import locale
import isodate
import strict_rfc3339
import httplib2

from colorama import init
from termcolor import colored, cprint

from apiclient.discovery import build_from_document
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

from requests import get
from slugify import slugify


###############################################################################

init()  # use Colorama to make Termcolor work on all platforms


###############################################################################

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client-secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'config', 'client-secrets.json'
))

# Grabbed from https://www.googleapis.com/discovery/v1/apis/youtube/v3/rest
DISCOVERY_DOCUMENT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'config', 'youtube-v3-api-captions.json'
))

# Credentials created by the authentication process
OAUTH_CREDENTIALS = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'config', 'credentials-oauth2.json'
))

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
YOUTUBE_RW_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Message to display if the CLIENT_SECRETS_FILE is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
ERROR: Please configure OAuth 2.0.

To download the captions you will need to populate the client_secrets.json file
found at:
   %s
with information from the APIs Console
https://console.developers.google.com

You can use config/client-secrets.json.dist as a template, but you'll need to
fill client_id and client_secret with your own OAuth2 credentials that you can
get from Google's API Console linked above.

For more information about the client-secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % CLIENT_SECRETS_FILE


###############################################################################

YOUTUBE_API_KEY_FILE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'config', 'client-key.txt'
))

MISSING_API_KEY_FILE = """
ERROR : Google API key missing.

How to get a Google API Key and OAuth2 credentials:
  1) Go to https://console.developers.google.com
  2) Create a project, eg. "JLM Video Captions"
  3) Set the YouTube data API to "ON"
  4) Create a public access key
  5) Copy it to %s
""" % YOUTUBE_API_KEY_FILE

YOUTUBE_API_KEY = ""
try:
    with open(YOUTUBE_API_KEY_FILE) as api_key_file:
        YOUTUBE_API_KEY = api_key_file.read().strip()
except IOError:
    cprint(MISSING_API_KEY_FILE, "red")
    exit(1)


# YOUTUBE API SETUP ###########################################################

def get_authenticated_service(_args):
    """
    Authorize the request and store the authorization credentials.
    """
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_RW_SSL_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage(OAUTH_CREDENTIALS)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, _args)

    with open(DISCOVERY_DOCUMENT, "r") as f:
        doc = f.read()
        return build_from_document(
            doc, http=credentials.authorize(httplib2.Http())
        )


# YOUTUBE API REQUESTS ########################################################

def get_latest_videos_of_channel(channel_id, cap=10, since_minutes_ago=120):
    assert cap < 51  # 50 is the highest authorized value in 2017
    t = datetime.datetime.now() - datetime.timedelta(minutes=since_minutes_ago)
    t = strict_rfc3339.timestamp_to_rfc3339_utcoffset(int(t.strftime("%s")))
    url = 'https://www.googleapis.com/youtube/v3/search'
    parameters = {
        'key': YOUTUBE_API_KEY,
        'channelId': channel_id,
        'type': 'video',
        'part': 'snippet',
        'order': 'date',
        'publishedAfter': t,  # RFC 3339 with trailing Z, or it will not work
        'maxResults': '%d' % cap,
    }

    response = get(url, params=parameters)

    if not response.ok:
        cprint("Request to Youtube API failed with response :", "red")
        print(response.text)
        exit(1)

    return response.json()


def get_videos_of_channel(channel_id, page=None, cap=50):
    assert cap < 51  # 50 is the highest authorized value in 2017
    url = 'https://www.googleapis.com/youtube/v3/search'
    parameters = {
        'key': YOUTUBE_API_KEY,
        'channelId': channel_id,
        'type': 'video',
        'part': 'snippet',
        'order': 'date',
        'maxResults': '%d' % cap,
    }

    if page is not None:
        parameters['pageToken'] = page

    response = get(url, params=parameters)

    if not response.ok:
        cprint("Request to Youtube API failed with response :", "red")
        print(response.text)
        exit(1)

    return response.json()


def get_videos(video_ids):
    url = 'https://www.googleapis.com/youtube/v3/videos'
    parameters = {
        'key': YOUTUBE_API_KEY,
        'id': ','.join(video_ids),
        'part': 'snippet,contentDetails',
        'maxResults': '50',
    }

    response = get(url, params=parameters)

    if not response.ok:
        cprint("Request to Youtube API failed with response :", "red")
        print(response.text)

    return response.json()


def get_captions_for_video(video_id):
    url = 'https://www.googleapis.com/youtube/v3/captions'
    parameters = {
        'key': YOUTUBE_API_KEY,
        'videoId': video_id,
        'part': 'snippet',
    }

    response = get(url, params=parameters)

    if not response.ok:
        cprint("Request to Youtube API failed with response :", "red")
        cprint(response.text, "red")

    return response.json()


def upload_caption(_youtube, _id, _file):
    return _youtube.captions().update(
        part="id",
        body=dict(
            id=_id
        ),
        media_body=_file,
        media_mime_type='test/vtt'
    ).execute()


def get_caption(_youtube, caption_id, caption_extension):
    return _youtube.captions().download(
        id=caption_id,
        tfmt=caption_extension
    ).execute().decode('utf-8')


###############################################################################

def parse_videos_from_json(_json):
    _videos = []
    for video_data in _json['items']:
        _id = video_data['id']
        if type(_id) is dict:
            _id = _id['videoId']
        _duration = None
        if 'contentDetails' in video_data:
            _duration = video_data['contentDetails']['duration']
        _videos.append(Video(
            yid=_id,
            title=video_data['snippet']['title'],
            date=video_data['snippet']['publishedAt'],
            duration=_duration
        ))
    return _videos


def get_caption_file_by_id(_id, _dir, _ext):
    for dirpath, dirnames, filenames in os.walk(_dir):
        for name in filenames:
            if name.endswith(_ext):
                _caption = Caption.from_file(os.path.join(dirpath, name))
                _caption.filename = name
                if _caption.id == _id:
                    return _caption
    raise Exception("Found no caption for id %s" % _id)


# MODEL #######################################################################

class Video:

    def __init__(self, yid, title, date, duration=None):
        """
        :param yid: Youtube Id
        :param title: Unicode
        :param date: RFC 3339
        :param duration: ISO 8601 (PT prefix)
        """
        self.yid = yid
        self.title = title
        self.date = dateutil.parser.parse(date)
        if duration is not None:
            self.duration = isodate.parse_duration(duration)
        else:
            self.duration = None

    def __str__(self):
        return "%s - %s" % (self.yid, self.title)

    @property
    def slug(self):
        return slugify(self.title)

    @property
    def day_fr(self):
        locale.setlocale(locale.LC_TIME, "fr_FR.utf8")
        day = self.date.strftime("%A %d %B %Y")
        locale.resetlocale(locale.LC_TIME)
        return day.capitalize().decode('utf-8')

    @property
    def day_en(self):
        locale.setlocale(locale.LC_TIME, "en_US.utf8")
        day = self.date.strftime("%A, %d %B %Y")
        locale.resetlocale(locale.LC_TIME)
        return day.decode('utf-8')

    @property
    def day_de(self):
        locale.setlocale(locale.LC_TIME, "de_DE.utf8")
        day = self.date.strftime("%A %d %B %Y")
        locale.resetlocale(locale.LC_TIME)
        return day.decode('utf-8')


class Caption:

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def from_file(filepath):
        metas = {}
        regex = re.compile("(\w+): +(.+)")
        with open(filepath, "r") as open_file:
            line = open_file.readline()
            while line and line.strip():  # stop at the first blank line
                line = open_file.readline()  # also, skip "WebVTT"
                matches = re.match(regex, line)
                if matches:
                    metas[matches.group(1).strip()] = matches.group(2).strip()

        return Caption(
            filepath=filepath,
            id=metas['Caption'],
            video_id=metas['Video'],
            language=metas['Language'],
            modified_at=dateutil.parser.parse(metas['LastUpdated'])
        )

    @property
    def id(self):
        if not hasattr(self, 'id'):
            raise Exception("Caption without ID.")
        return self.id
