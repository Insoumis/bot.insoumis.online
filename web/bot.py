# coding=utf-8
import re
import os
import json
import logging as log
from flask import Flask, send_from_directory, request
from github import Github

from lib.github import GITHUB_API_KEY


# CONFIG ######################################################################

THIS_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
GITHUB_REPO = "jlm2017/jlm-video-subtitles"

labels_columns = [                    # [fr, en, de]
    ("Process: [0] Awaiting subtitles", [398411, 387590, 654910]),
    ("Process: [1] Writing in progress", [398412, 387592, 654907]),
    ("Process: [2] Ready for review (1)", [398414, 654829, 654913]),
    ("Process: [4] Ready for review (2)", [398416, 387597, 654916]),
    ("Process: [6] Approved", [398417, 390130, 654919]),
]

# FLASK APP ###################################################################

app = Flask('RobotInsoumis', root_path=THIS_DIRECTORY)


# UTILS #######################################################################

log.basicConfig(filename=os.path.join(app.root_path, 'bot.log'),
                level=log.INFO)


# ROUTES ######################################################################

@app.route('/')
def home():
    return u"Can't stenchon the mélenchon! Robot Résistance!"


@app.route('/labellize', methods=['POST'])
def labellize():
    """
    A github webhook to receive a project_card event.
    When a project card has been moved, update its associated issue's labels.
    :return:
    """
    # https://developer.github.com/v3/activity/events/types/#projectcardevent
    payload = request.get_json()
    log.debug(u"Received payload:\n%s" % json.dumps(payload, indent=2))

    if payload['action'] == 'moved':
        card_id = payload['project_card']['id']
        column_id = payload['project_card']['column_id']
        content_url = payload['project_card']['content_url']
        m = re.search("([0-9]+)$", content_url)
        if not m:
            log.error(u"No issue id in content url '%s' for card %d.",
                      (content_url, card_id))
            return ''
        issue_number = int(m.group(1))

        log.info(u"Moved card %d (issue #%d) to column %d."
                 % (card_id, issue_number, column_id))

        gh = Github(GITHUB_API_KEY)
        repo = gh.get_repo(GITHUB_REPO)
        issue = repo.get_issue(issue_number)

        issue_labels = [label.name for label in issue.labels]

        labels_to_add = []
        labels_to_remove = []
        for _label, _column_ids in labels_columns:
            if column_id in _column_ids and _label not in issue_labels:
                labels_to_add.append(_label)
            if column_id not in _column_ids and _label in issue_labels:
                labels_to_remove.append(_label)

        for label in labels_to_remove:
            log.info("Added '%s' to issue #%d" % (label, issue_number))
            issue.remove_from_labels(label)
        for label in labels_to_add:
            log.info("Removed '%s' from issue #%d" % (label, issue_number))
            issue.add_to_labels(label)

    return ''


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )


# MAIN ########################################################################

if __name__ == "__main__":
    app.run(debug=True)  # This is not used in the production env anyways
