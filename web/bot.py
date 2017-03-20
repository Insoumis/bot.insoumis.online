# coding=utf-8

# Basically a listener for events sent by github (and maybe youtube, later on).

import re
import os
import sys
import json
import hmac
import yaml
import random
import datetime
import logging
from hashlib import sha1
from flask import Flask, send_from_directory, request, abort, url_for
from jinja2 import Environment, FileSystemLoader
from github import Github
from subprocess import check_output, CalledProcessError

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from lib.github import GITHUB_API_KEY, LANGUAGES


# PATH RELATIVITY #############################################################
THIS_DIRECTORY = os.path.abspath(os.path.dirname(__file__))


def get_path(relative_path):
    return os.path.abspath(os.path.join(THIS_DIRECTORY, relative_path))


# LOGGING #####################################################################

log = logging.getLogger("Bot")
log.setLevel(logging.INFO)
log.addHandler(logging.FileHandler(get_path('bot.log')))


# CONFIG ######################################################################

GITHUB_REPO = "jlm2017/jlm-video-subtitles"
LABELS_COLUMNS = [              # [fr, en, de, zh]
    (u"⚙ [0] Awaiting subtitles", [398411, 387590, 654910, 654911]),
    (u"⚙ [1] Writing in progress", [398412, 387592, 654907, 654908]),
    (u"⚙ [2] First review", [398414, 654829, 654913, 654914]),
    (u"⚙ [3] Second review", [398416, 387597, 654916, 654917]),
    (u"⚙ [4] Approved", [398417, 390130, 654919, 654920]),
]

# There's no YAML support in Flask (yet) so we make our own.
with open(get_path('config.yml')) as f:
    config = yaml.load(f)


# FLASK APP ###################################################################

app = Flask('RobotInsoumis', root_path=THIS_DIRECTORY)
app.debug = os.environ.get('DEBUG') == 'true'


# SECRET ######################################################################

GITHUB_SECRET_FILE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'config', 'github-webhook-secret.txt'
))

MISSING_GITHUB_SECRET_FILE = """
ERROR : Github webhook secret missing.

How to get a Github webhook secret:
  1) Set up a webhook
  2) Choose a secret
  3) Copy it to %s
""" % GITHUB_SECRET_FILE

GITHUB_SECRET = ""
try:
    with open(GITHUB_SECRET_FILE) as secret_file:
        GITHUB_SECRET = secret_file.read().strip()
except IOError:
    log.error(MISSING_GITHUB_SECRET_FILE)
    exit(1)


# SETUP JINJA2 TEMPLATE ENGINE ################################################

def markdown_filter(value, nl2br=False, p=True):
    """
    nl2br: set to True to replace line breaks with <br> tags
    p: set to False to remove the enclosing <p></p> tags
    """
    from markdown import markdown
    from markdown.extensions.nl2br import Nl2BrExtension
    from markdown.extensions.abbr import AbbrExtension
    extensions = [AbbrExtension()]
    if nl2br is True:
        extensions.append(Nl2BrExtension())
    markdowned = markdown(value, output_format='html5', extensions=extensions)
    if p is False:
        markdowned = markdowned.replace(r"<p>", "").replace(r"</p>", "")
    return markdowned


def shuffle_filter(seq):
    """
    This shuffles the sequence it is applied to.
    'tis a failure of jinja2 to not provide a shuffle filter by default.
    """
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq


tpl_engine = Environment(
    loader=FileSystemLoader([get_path('view')]),
    trim_blocks=True,
    lstrip_blocks=True,
)

tpl_engine.globals.update(
    url_for=url_for,
)

tpl_engine.filters['md'] = markdown_filter
tpl_engine.filters['markdown'] = markdown_filter
tpl_engine.filters['shuffle'] = shuffle_filter

tpl_global_vars = {
    'config': config,
    'request': request,
    # 'version': version,
    'now': datetime.datetime.now(),
}


# HELPERS #####################################################################

def render_view(view, context=None):
    """
    A simple helper to render [view] template with [context] vars.
    It automagically adds the global template vars defined above, too.
    It returns a string, usually the HTML contents to display.

    We're not using flask's render_template because we want more flexibility.
    """
    if context is None:
        context = {}
    return tpl_engine.get_template(view).render(
        dict(tpl_global_vars.items() + context.items())
    )


# ROUTES ######################################################################

@app.route('/')
def home():
    return render_view("home.html.jinja2")


@app.route('/labellize', methods=['POST'])
def labellize():
    """
    A github webhook to receive a project_card event.
    When a project card has been moved, update its associated issue's labels.
    :return:
    """
    # https://developer.github.com/v3/activity/events/types/#projectcardevent
    payload = request.get_json(silent=True)
    if not payload:
        log.error(u"Invalid payload:\n%s" % request.get_data())
        abort(400)
    log.debug(u"Received payload:\n%s" % json.dumps(payload, indent=2))

    provided_digest = request.headers.get('X-Hub-Signature', default='')
    h = hmac.new(GITHUB_SECRET, msg=request.get_data(), digestmod=sha1)
    expected_digest = "sha1=%s" % h.hexdigest()
    # if not hmac.compare_digest(provided_digest, expected_digest):
    # hmac.compare_digest is not available for python 2.7.3
    # and I'm too lazy/scared to mess with my server.
    # It's okay if someone uses time attacks to guess our secret.
    if provided_digest != expected_digest:
        log.error(u"Hub signature digest mismatch: %s != %s"
                  % (provided_digest, expected_digest))
        abort(403)

    if payload['action'] == 'moved':
        card_id = payload['project_card']['id']
        column_id = payload['project_card']['column_id']
        content_url = payload['project_card']['content_url']
        m = re.search("([0-9]+)$", content_url)
        if not m:
            # It's probably not an issue card, but a standalone card.
            log.warn(u"No issue id in content url '%s' for card %d.",
                     (content_url, card_id))
            return ''
        issue_number = int(m.group(1))

        blacklist = [1]
        if issue_number in blacklist:
            return ''

        log.info(u"Moved card %d (issue #%d) to column %d."
                 % (card_id, issue_number, column_id))

        gh = Github(GITHUB_API_KEY)
        repo = gh.get_repo(GITHUB_REPO)
        issue = repo.get_issue(issue_number)

        issue_labels = [label.name for label in issue.labels]

        labels_to_add = []
        labels_to_remove = []
        for label, column_ids in LABELS_COLUMNS:
            if column_id in column_ids and label not in issue_labels:
                labels_to_add.append(label)
            if column_id not in column_ids and label in issue_labels:
                labels_to_remove.append(label)

        for label in labels_to_remove:
            log.info(u"Added '%s' to issue #%d" % (label, issue_number))
            issue.remove_from_labels(label.encode('utf-8'))
        for label in labels_to_add:
            log.info(u"Removed '%s' from issue #%d" % (label, issue_number))
            issue.add_to_labels(label.encode('utf-8'))

    return ''


# This is never triggered. :(
# @app.route('/webhook/youtube', methods=['POST'])
# def webhook_youtube():
#     """
#     A youtube webhook receiving an Atom feed whenever a new video has been
#     published.
#     It creates an issue for each configured language on github.
#     https://developers.google.com/youtube/v3/guides/push_notifications
#     """
#
#     payload = request.get_data()
#     log.info(u"Received youtube payload:\n%s" % payload)
#
#     import feedparser
#     try:
#         d = feedparser.parse(payload)
#         video_id = d['entries'][0]['yt_videoid']
#         log.info("Video %s was published or updated." % video_id)
#         published = d['entries'][0]['published_parsed']
#         updated = d['entries'][0]['updated_parsed']
#         if published == updated:
#             log.info("Video %s was PUBLISHED." % video_id)
#         else:
#             log.info("Video %s was UPDATED." % video_id)
#
#     except Exception as e:
#         log.error(e.message)
#         log.error(e)

    # if not payload:
    #     log.error(u"Invalid youtube payload:\n%s" % request.get_data())
    #     abort(400)


@app.route('/captions/create/<language>/<video>')
def create_issue(language, video):
    """
    Create a new issue for the video with youtube id <video>.
    Language may be fr or en or zh, see LANGUAGES in lib.github.py.
    """
    if not re.match("^[a-zA-Z-]{2,5}$", language):
        msg = "Malformed language '%s'." % language
        log.error(msg)
        abort(400, description=msg)
    if not re.match("^[a-zA-Z0-9._-]{5,}$", video):
        msg = "Malformed video id '%s'." % video
        log.error(msg)
        abort(400, description=msg)

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    try:
        out_raw = check_output(
            [
                "bin/create-issues.sh --languages %s --videos %s"
                % (language, video),
            ],
            shell=True, cwd=root_dir
        )
        log.info("Created '%s' issue for video '%s'." % (language, video))
    except CalledProcessError as e:
        out_raw = "%s" % e.output

    return "<pre>%s</pre>" % out_raw


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )


# RUNNER FOR DEVELOPMENT ######################################################

if __name__ == "__main__":
    # We add the YAML config file to the list of files to watch for automatic
    # reload of the development server.
    extra_files = [get_path('config.yml')]
    app.run(debug=True, extra_files=extra_files)
