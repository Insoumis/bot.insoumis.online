#!/usr/bin/env python
# coding=utf-8


# IMPORTS #####################################################################

import os
import re
import sys
import logging
import argparse

from github import Github
from oauth2client.tools import argparser as youtube_argparser

THIS_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIRECTORY, '..')))

from lib.github import GITHUB_API_KEY
from lib.common import get_downloaded_captions_and_videos, remove_country_code


# CONFIG ######################################################################

logging.basicConfig(format='%(message)s')
log = logging.getLogger('Suffix Commit')


# MAIN ########################################################################

if __name__ == "__main__":

    argparser = argparse.ArgumentParser(
        parents=[youtube_argparser], add_help=False,
        description="""
        Returns the #numbers of the issues related to the captions files that
        were added or modified. This is appended to the commit message.
        Example of string returned to stdout : ' Closes #229. Closes #184.'
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
    if 0 == len(captions):
        exit(0)

    gh = Github(GITHUB_API_KEY)
    repo = gh.get_repo(args.repository)
    issues = [issue for issue in repo.get_issues()]  # memoize it

    output_lines = []
    for video, caption in zip(videos, captions):

        # We're not relying only on issue title anymore as it may have changed.
        # We also rely on the video id that we parse from the issue content.
        language = remove_country_code(caption.language)
        issue_title_prefix = "[subtitles] [%s]" % language
        r = re.compile(r"https://www\.youtube\.com/watch\?v=([a-zA-Z0-9._-]+)")

        for issue in issues:
            matches = r.search(issue.body)
            if matches is not None \
                    and matches.group(1) == video.yid \
                    and issue.title.startswith(issue_title_prefix):
                output_lines.append(" Closes #%d." % issue.number)
                break

    if output_lines:
        print(''.join(output_lines))
