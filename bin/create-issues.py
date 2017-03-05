#!/usr/bin/env python
# coding=utf-8

# Create issues for each newly published video.
# Tested with python 2.7 only.

###############################################################################

import argparse
import sys

import os
from pprint import pprint
from colorama import init
from github import Github, Requester
from oauth2client.tools import argparser as youtube_argparser
from termcolor import colored, cprint

THIS_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIRECTORY, '..')))

from lib.youtube import get_authenticated_service, get_videos, \
    parse_videos_from_json, get_latest_videos_of_channel

from lib.github import GITHUB_API_KEY

# use Colorama to make Termcolor work on all platforms
init()

THIS_DIRECTORY = os.path.abspath(os.path.dirname(__file__))


###############################################################################

def _s(int_or_list):
    if type(int_or_list) is list:
        int_or_list = len(int_or_list)
    return '' if int_or_list == 1 else 's'


###############################################################################


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(
        parents=[youtube_argparser], add_help=False,
        description="""
        Create issues on github for each new video of specified channel.
        """,
        epilog="""
        © WTFPL 2017 - YOU ARE FREE TO DO WHAT THE FORK YOU WANT
        """
    )

    argparser.add_argument(
        "--repository", default="jlm2017/jlm-video-subtitles",
        metavar="OWNER/REPO",
        help="""
        Github repository in which to create issues.
        Defaults to 'jlm2017/jlm-video-subtitles'.
        """
    )

    argparser.add_argument(
        "--channel", default="UCk-_PEY3iC6DIGJKuoEe9bw",
        metavar="CHANNEL_ID",
        help="""
        Identifier of the YouTube channel publishing the videos for which the
        captions are to be downloaded.
        The default channel is the channel of "JEAN-LUC MÉLENCHON", which is
        the candidate of the "Insoumis".
        This option is ignored if you provide the --videos option.
        """
    )

    argparser.add_argument(
        "--videos",
        nargs="+",
        metavar="VIDEO_ID",
        help="""
        Identifier⋅s of the YouTube video⋅s for which to create issues.
        When you provide this option, the --channel option is ignored.
        You cannot provide more than 50 video ids to this parameter.
        """
    )

    argparser.add_argument(
        "-?", "-h", "--help", dest="help", action="store_true",
        help="Display this documentation and exit."
    )

    args = argparser.parse_args()

    if args.help:
        # Doing this instead of leaving the default behavior, to support -? too
        argparser.print_help()
        argparser.exit(0)

    cprint("Authenticating with YouTube...", "yellow")

    youtube = get_authenticated_service(args)

    languages = [
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

    print("Collecting issues of repository %s..."
          % colored(args.repository, "yellow"))

    gh = Github(GITHUB_API_KEY)
    repo = gh.get_repo(args.repository)

    # The Projects API is still in development
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

    # Useful to get the IDs of the Projects
    # headers, data = rq.requestJsonAndCheck(
    #     "GET",
    #     "/repos/%s/projects" % args.repository,
    #     None,
    #     {"Accept": GITHUB_ACCEPT}
    # )
    # pprint(data)

    # Useful to get the IDs of the Columns
    # headers, data = rq.requestJsonAndCheck(
    #     "GET",
    #     "/projects/%s/columns" % '206437',
    #     None,
    #     {"Accept": GITHUB_ACCEPT}
    # )
    # pprint(data)

    # List cards of a Column
    # headers, data = rq.requestJsonAndCheck(
    #     "GET",
    #     "/projects/columns/%s/cards" % '398411',
    #     None,
    #     {"Accept": GITHUB_ACCEPT}
    # )
    # pprint(data)

    issues = [issue for issue in repo.get_issues()]  # no laziness !

    labels = {}
    for language in languages:
        labels[language['short']] = repo.get_label(
            language['label'].encode('utf-8')
        )
    label_start = repo.get_label('Process: [0] Awaiting subtitles')

    if args.videos:
        print(
            colored("Selecting video%s " % _s(args.videos), "yellow") +
            colored(', '.join(args.videos), "magenta") +
            colored("...", "yellow")
        )
        ids = args.videos
    else:
        print("Collecting latest videos of channel %s..."
              % colored(args.channel, "yellow"))
        jsonResponse = get_latest_videos_of_channel(args.channel)
        videos = parse_videos_from_json(jsonResponse)
        ids = [video.yid for video in videos]

    jsonResponse = get_videos(ids)
    videos = parse_videos_from_json(jsonResponse)

    for video in videos:
        for language in languages:
            issue_title = "[subtitles] [%s] %s" % \
                          (language['short'], video.title)

            print("Looking for issue %s..."
                  % colored(issue_title, "yellow"))

            found = False
            for issue in issues:
                if issue.title == issue_title:
                    found = True
                    break
            if found:
                print("  Found existing issue. Skipping...")
            else:
                print("  Issue not found. Creating it now...")
                issue_body = language['issue'].format(video=video)
                issue = repo.create_issue(
                    issue_title,
                    body=issue_body,
                    labels=[labels[language['short']], label_start]
                )
                # Ok, this is a total hack that may break at any point,
                # because the Cards API is a dev-preview only.
                print("  Creating a card for it as well...")
                headers, data = rq.requestJsonAndCheck(
                    verb="POST",
                    url="/projects/columns/%s/cards" % language['column'],
                    input={
                        'content_id': issue.id,
                        'content_type': 'Issue'
                    },
                    headers={"Accept": GITHUB_ACCEPT}
                )

    if 0 == len(videos):
        print("No recent videos were found.")

    cprint("Done!", "green")
