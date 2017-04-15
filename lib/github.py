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

GITHUB_REPO = "jlm2017/jlm-video-subtitles"

LABELS_COLUMNS = [              # [fr, en, de, pt, zh]
    (u"⚙ [0] Awaiting subtitles", [910796, 387590, 654910, 654905, 654911]),
    (u"⚙ [1] Writing in progress", [398412, 387592, 654907, 654906, 654908]),
    (u"⚙ [2] First review", [398414, 654829, 654913, 654912, 654914]),
    (u"⚙ [3] Second review", [398416, 387597, 654916, 654915, 654917]),
    (u"⚙ [4] Approved", [398417, 390130, 654919, 654918, 654920]),
]

LANGUAGES = [
    {
        'short': 'fr',
        'label': u'⚑ Français',
        'column': '910796',
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
    ,
    {
        'short': 'de',
        'label': u'⚑ Deutsche',
        'column': '654910',
        'issue': u"""
## {video.title}

&nbsp;         | Info
-------------- | -------------
**Datum**      | {video.day_en}
**Dauer**      | {video.duration} :clock7:
**Sprache**    | Deutsche :de:
**Video**      | [See it on YouTube :arrow_upper_right:](https://www.youtube.com/watch?v={video.yid})
**Untertitel** | [Edit them in YouTube :arrow_upper_right:](https://www.youtube.com/timedtext_editor?v={video.yid}&tab=captions&bl=vmp&action_mde_edit_form=1&lang=de&ui=hd)
"""
    }
    ,
    {
        'short': 'pt',
        'label': u'⚑ Português',
        'column': '654905',
        'issue': u"""
## {video.title}

&nbsp;         | Info
-------------- | -------------
**Datum**      | {video.day_en}
**Dauer**      | {video.duration} :clock7:
**Sprache**    | Português :pt:
**Video**      | [See it on YouTube :arrow_upper_right:](https://www.youtube.com/watch?v={video.yid})
**Untertitel** | [Edit them in YouTube :arrow_upper_right:](https://www.youtube.com/timedtext_editor?v={video.yid}&tab=captions&bl=vmp&action_mde_edit_form=1&lang=pt&ui=hd)
"""
    }
    ,
    {
        'short': 'zh',
        'label': u'⚑ Chinese',  # 中国, but github labels sorting sucks
        'column': '654911',
        'issue': u"""
## {video.title}

&nbsp;        | Info
------------- | -------------
**Date**      | {video.day_en}
**Duration**  | {video.duration} :clock7:
**Language**  | 中国 :cn:
**Video**     | [See it on YouTube :arrow_upper_right:](https://www.youtube.com/watch?v={video.yid})
**Subtitles** | [Edit them in YouTube :arrow_upper_right:](https://www.youtube.com/timedtext_editor?v={video.yid}&tab=captions&bl=vmp&action_mde_edit_form=1&lang=zh&ui=hd)
"""
    }
]

