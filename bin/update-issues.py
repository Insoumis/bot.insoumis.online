#!/usr/bin/env python
# coding=utf-8


# IMPORTS #####################################################################

import os
import re
import sys
import logging
import argparse

from github import Github, Requester
from oauth2client.tools import argparser as youtube_argparser

THIS_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIRECTORY, '..')))

from lib.github import GITHUB_API_KEY
from lib.common import get_downloaded_captions_and_videos, remove_country_code

# CONFIG ######################################################################

logging.basicConfig(format='%(message)s')
log = logging.getLogger('Issue updater')

APPROVAL_COLUMNS = {
    'fr': 398417,
    'en': 390130,
    'de': 654919,
}

# The GitHub Projects API is still in development
# - https://developer.github.com/v3/projects
# - It's not supported by the python lib yet
# - We need to provide a special "Accept" header
# So, we hack in our own support ; it's dirty but it works.
# Be warned : it may break at any moment -_-
GITHUB_ACCEPT = "application/vnd.github.inertia-preview+json"
rq = Requester.Requester(
    GITHUB_API_KEY, None, "https://api.github.com", 10, None, None,
    'PyGithub/Python', 30, False
)


# MAIN ########################################################################

if __name__ == "__main__":

    argparser = argparse.ArgumentParser(
        parents=[youtube_argparser], add_help=False,
        description="""
        Updates the issues's card by moving them to the last column if
        the related caption has been published and subsequently downloaded.
        """,
        epilog="""
        © WTFPL 2017 - YOU ARE FREE TO DO WHAT THE FORK YOU WANT
        """
    )

    argparser.add_argument(
        "--repository", default="jlm2017/jlm-video-subtitles",
        metavar="OWNER/REPO",
        help="""
        Github repository in which to curate issues.
        Defaults to 'jlm2017/jlm-video-subtitles'.
        """
    )

    argparser.add_argument(
        "--directory", dest="data_directory",
        default="../jlm-video-subtitles/subtitles",
        help="""
        The directory where the captions files are.
        This is either an absolute path (when starting with /),
        or relative to the directory where this python script is : '%s'.
        """ % THIS_DIRECTORY
    )

    argparser.add_argument(
        "--extension", dest="extension", default="vtt",
        choices=['vtt', 'srt', 'sbv'],
        help="""
        File extension in which the captions are stored.
        Available formats : srt for SubRip, sbv for SubViewer, vtt for WebVTT.
        The default is vtt.
        """
    )

    argparser.add_argument(
        "-?", "-h", "--help", dest="help", action="store_true",
        help="Display this documentation and exit."
    )

    args = argparser.parse_args()

    if args.help:
        argparser.print_help()
        argparser.exit(0)

    if args.data_directory.startswith('/'):
        captions_directory = args.data_directory
    else:
        captions_directory = os.path.abspath(os.path.join(
            THIS_DIRECTORY, args.data_directory
        ))
    if not os.path.isdir(captions_directory):
        log.error("No directory at '%s'. Tweak --directory ?"
                  % captions_directory)
        exit(1)

    caption_extension = args.extension

    # BUSINESS ################################################################

    captions, videos = get_downloaded_captions_and_videos(captions_directory)

    # from pprint import pprint
    # pprint([caption.language for caption in captions])
    # pprint([video.title for video in videos])

    if 0 == len(captions):
        sys.exit(0)

    gh = Github(GITHUB_API_KEY)
    repo = gh.get_repo(args.repository)
    issues = [issue for issue in repo.get_issues()]  # memoize it

    # There's no easy way of getting a Card an issue is associated with.
    # But there's a way of getting the Issue number of a specific Card.
    # We have to get all the Cards from all the Columns, and then find ours.
    # This is such a hack... But hey, when life gives you lemons ; REROLL!
    cards = []  # array of dict {id: ?, issue_number: ?}
    columns = [  # all columns but the last one
        398411, 398412, 398414, 398416,  # fr
        387590, 387592, 654829, 387597,  # en
        654910, 654907, 654913, 654916,  # de
    ]
    for column_id in columns:
        headers, data = rq.requestJsonAndCheck(
            "GET",
            "/projects/columns/%d/cards" % column_id,
            None,
            {"Accept": GITHUB_ACCEPT}
        )
        for card_data in data:
            m = re.search("([0-9]+)$", card_data['content_url'])
            if not m:
                log.warn("Card #%d has un-parsable content url '%s'."
                         % (card_data['id'], card_data['content_url']))
                continue
            issue_number = int(m.group(1))
            cards.append({
                'id': card_data['id'],
                'issue_number': issue_number,
            })
    # END HACK ################################################################

    for video, caption in zip(videos, captions):

        language = remove_country_code(caption.language)
        issue_title = "[subtitles] [%s] %s" % (language, video.title)

        for issue in issues:
            if issue.title == issue_title:
                print("Grab card id for issue %d (#%d)..."
                      % (issue.id, issue.number))
                # Hack continued... :p
                card_id = None
                for card in cards:
                    if card['issue_number'] == issue_number:
                        card_id = card['id']
                        break
                if not card_id:
                    log.warn("Issue #%d has no card we could find."
                             % issue_number)
                    continue
                if language not in APPROVAL_COLUMNS:
                    log.warn("Issue #%d is not in a supported language: %s."
                             % (issue_number, language))
                    break
                column_id = APPROVAL_COLUMNS[language]
                print("Move card %d to column %d..."
                      % (card_id, column_id))
                # Hack forever...
                headers, data = rq.requestJsonAndCheck(
                    verb="POST",
                    url="/projects/columns/cards/%d/moves" % card_id,
                    input={
                        'position': 'top',
                        'column_id': column_id
                    },
                    headers={"Accept": GITHUB_ACCEPT}
                )
                break
