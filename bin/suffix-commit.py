#!/usr/bin/env python
# coding=utf-8

# IMPORTS #####################################################################

import os
import re
import sys
import logging
import argparse

from github import Github
from subprocess import check_output
from oauth2client.tools import argparser as youtube_argparser

THIS_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIRECTORY, '..')))

from lib.youtube import get_authenticated_service, Caption, get_videos, \
    parse_videos_from_json
from lib.github import GITHUB_API_KEY

# CONFIG ######################################################################

logging.basicConfig(format='%(message)s')
log = logging.getLogger('Issue #numbers retriever')


# MAIN ########################################################################

if __name__ == "__main__":

    argparser = argparse.ArgumentParser(
        parents=[youtube_argparser], add_help=False,
        description="""
        Returns the #numbers of the issues related to the captions files that
        were added or modified. This is used in the commit message.
        Example of string returned to stdout : 'Closes #229\\nCloses #184'
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
        "--directory", dest="data_directory", default="../jlm-video-subtitles/subtitles",
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

    # youtube = get_authenticated_service(args)

    # print("Looking through files added to '%s'..." % captions_directory)

    files_raw = check_output(
        ["git add -n ."], shell=True, cwd=captions_directory
    )

    git_added_paths = re.findall("^add '(.+)'$", files_raw, flags=re.MULTILINE)

    # from pprint import pprint
    # pprint(git_added_paths)

    if 0 == len(git_added_paths):
        exit(0)

    output_lines = []  # eg: "Closes #229\nCloses #184"

    captions = []
    for git_caption_path in git_added_paths:
        m = re.search("([0-9]+)/([^/]+)$", git_caption_path)
        if not m:
            log.error("WTF %s" % git_caption_path)
            exit(1)
        caption_year, caption_filename = m.group(1, 2)
        caption_path = os.path.join(
            captions_directory, caption_year, caption_filename
        )
        captions.append(Caption.from_file(caption_path))

    videos = get_videos([caption.video_id for caption in captions])
    videos = parse_videos_from_json(videos)

    gh = Github(GITHUB_API_KEY)
    repo = gh.get_repo(args.repository)
    issues = [issue for issue in repo.get_issues()]  # no laziness !

    for video, caption in zip(videos, captions):
        language = caption.language
        issue_title = "[subtitles] [%s] %s" % (language, video.title)

        found = False
        for issue in issues:
            if issue.title == issue_title:
                found = issue.number
                break
        if found:
            output_lines.append("Closes #%d" % found)

    if output_lines:
        print("\n".join(output_lines))






