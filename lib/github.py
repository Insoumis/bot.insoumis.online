# coding=utf-8
import os

from colorama import init
from termcolor import colored, cprint


###############################################################################

init()  # use Colorama to make Termcolor work on all platforms


###############################################################################

GITHUB_API_KEY_FILE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'config', 'github-key.txt'
))

MISSING_GITHUB_API_KEY_FILE = """
ERROR : Github API key missing.

How to get a Github API Key:
  1) Go to https://github.com/settings/tokens
  2) Create a new key
  3) Copy it to %s
""" % GITHUB_API_KEY_FILE

GITHUB_API_KEY = ""
try:
    with open(GITHUB_API_KEY_FILE) as api_key_file:
        GITHUB_API_KEY = api_key_file.read().strip()
except IOError:
    cprint(MISSING_GITHUB_API_KEY_FILE, "red")
    exit(1)


###############################################################################

LANGUAGES = [
    {
        'short': 'fr',
        'label': u'⚑ Français',
        'column': '398411',
        'issue': u"""
## {video.title}

&nbsp;          | Info
--------------- | ---------------
**Date**        | {video.day_fr}
**Durée**       | {video.duration} :clock7:
**Langue**      | Français :fr:
**Vidéo**       | [Voir dans YouTube :arrow_upper_right:](https://www.youtube.com/watch?v={video.yid})
**Sous-titres** | [Éditer dans YouTube :arrow_upper_right:](https://www.youtube.com/timedtext_editor?v={video.yid}&tab=captions&bl=vmp&action_mde_edit_form=1&lang=fr&ui=hd)
"""
    }
    ,
    {
        'short': 'en',
        'label': u'⚑ English',
        'column': '387590',
        'issue': u"""
## {video.title}

&nbsp;        | Info
------------- | -------------
**Date**      | {video.day_en}
**Duration**  | {video.duration} :clock7:
**Language**  | English :gb:
**Video**     | [See it on YouTube :arrow_upper_right:](https://www.youtube.com/watch?v={video.yid})
**Subtitles** | [Edit them in YouTube :arrow_upper_right:](https://www.youtube.com/timedtext_editor?v={video.yid}&tab=captions&bl=vmp&action_mde_edit_form=1&lang=en&ui=hd)
"""
    }
    #             ,
    #             {
    #                 'short': 'de',
    #                 'label': 'Language: German',
    #                 'column': '654910',
    #                 'issue': u"""
    # Titel | {video.title}
    # ----- | -----
    # Dauer | {video.duration}
    # Sprache | German
    # Verweise | [VIDEO](https://www.youtube.com/watch?v={video.yid}) - [EDITOR](https://www.youtube.com/timedtext_editor?v={video.yid}&tab=captions&bl=vmp&action_mde_edit_form=1&lang=en&ui=hd)
    # """
    #             }
]

