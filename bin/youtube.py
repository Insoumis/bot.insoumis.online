#!/usr/bin/env python
# coding=utf-8

# The purpose of the script is to download all the subtitles files from Youtube
# Tested with python 2.7 only.

# I. Gather your tools.
#
# See setup.sh

# II. Pay a visit to the landlord of the forest, on your way there.
#
# How to get a Google API Key and OAuth2 credentials:
# 1) Go to https://console.developers.google.com
# 2) Create a project, eg. "JLM Video Captions"
# 3) Set the YouTube data API to "ON"
# 4) Create a public access key
# 5) Copy it to config/api-key.txt
# 6) Create an OAuth2 Client Id
# 7) Copy config/client-secrets.json.dist to config/client-secrets.json
# 8) Fill client_id and client_secret with your OAuth2 credentials

# III. Check the forest from afar
#
# bin/youtube.py --help

# IV. Do your gathering round
#
# bin/youtube.py

###############################################################################

import os
import re
import sys
import datetime
import dateutil.parser
import locale
import isodate
import strict_rfc3339
import argparse
import httplib2

from oauth2client.tools import argparser as youtube_argparser

from requests import get
from pprint import pprint
from colorama import init
from termcolor import colored, cprint
from slugify import slugify
from github import Github, Requester

THIS_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIRECTORY, '..')))

from lib.youtube import get_authenticated_service, get_videos, \
    parse_videos_from_json, get_videos_of_channel, get_captions_for_video, \
    get_caption_file_by_id, upload_caption

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
        A simple script to download all the published captions of all the
        videos of a channel from YouTube.
        It will ignore captions made with ASR (Automatic Speech Recognition).
        You need to set up `client-key.txt` and `client-secrets.json`
        in order to authenticate successfully with YouTube.
        """,
        epilog="""
        © WTFPL 2017 - YOU ARE FREE TO DO WHAT THE FORK YOU WANT
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
        Identifier⋅s of the YouTube video⋅s for which the captions are to be
        downloaded. When you provide this option, the script will only back up
        the captions of the specified video⋅s, and not of all the other videos
        of the channel, like it would normally do.
        Very useful to make a quick backup of only one or more video⋅s.
        You cannot provide more than 50 video ids to this parameter.
        Remember: YouTube's API has quotas, and using this option is the best
        way to not blow them.
        """
    )

    argparser.add_argument(
        "--captions",
        nargs="+",
        metavar="CAPTION_ID",
        help="""
        Identifier(s) of the YouTube caption(s) to upload to youtube.
        This option is only useful for the upload action.
        """
    )

    argparser.add_argument(
        "--extension", dest="extension", default="vtt",
        choices=['vtt', 'srt', 'sbv'],
        help="""
        File extension in which the captions will be downloaded.
        Available formats : srt for SubRip, sbv for SubViewer, vtt for WebVTT.
        The default is vtt.
        """
    )

    argparser.add_argument(
        "--directory", dest="data_directory", default="../subtitles",
        help="""
        The directory where the captions are or where you want them to be.
        This is either an absolute path (when starting with /),
        or relative to the directory where this python script is : '%s'.
        """ % THIS_DIRECTORY
    )

    argparser.add_argument(
        "--action", dest="action", default="help",
        choices=['help', 'download', 'upload'],
        help="""
        help : Show this help and exit.
        download : Download the caption file⋅s from youtube.\n
        upload : Upload specified caption file⋅s to youtube.\n
        """
    )

    argparser.add_argument(
        "-?", "-h", "--help", dest="help", action="store_true",
        help="Display this documentation and exit."
    )

    args = argparser.parse_args()

    if args.help or args.action == 'help':
        argparser.print_help()
        argparser.exit(0)

    if args.data_directory.startswith('/'):
        captions_directory = args.data_directory
    else:
        captions_directory = os.path.abspath(os.path.join(
            THIS_DIRECTORY, args.data_directory
        ))

    caption_extension = args.extension

    cprint("Authenticating with YouTube...", "yellow")

    youtube = get_authenticated_service(args)

    # ACTION = UPLOAD #########################################################

    if args.action == 'upload':

        # Logic
        # -----
        # check last publication date
        # fixme
        # if not different from stored
        # fixme
        # then actually upload
        if not args.captions:
            cprint("For the upload action,\n"
                   "You must provide caption(s) YouTube id(s) "
                   "in the --captions option.", "red")
            exit(1)

        caption_id = args.captions[0]

        caption = get_caption_file_by_id(caption_id, captions_directory, caption_extension)

        print("Uploading changes to caption %s"
              % colored(caption.filename, "yellow"))

        # googleapiclient.errors.HttpError: HttpError 403
        # when requesting
        # https://www.googleapis.com/upload/youtube/v3/captions?uploadType=multipart&alt=json&part=id
        # returned
        #   The permissions associated with the request are not sufficient
        #   to update the caption track.
        #   The request might not be properly authorized.
        #
        # fixme
        #
        # T_T

        upload_caption(youtube, caption.id, caption.filepath)

        cprint("Done!", "green")
        exit(0)

    # ACTION = DOWNLOAD #######################################################

    videos = []
    if args.videos:
        print(
            colored("Selecting video%s " % _s(args.videos), "yellow") +
            colored(', '.join(args.videos), "magenta") +
            colored("...", "yellow")
        )
        jsonResponse = get_videos(args.videos)
        if jsonResponse['pageInfo']['totalResults'] != len(args.videos):
            if len(args.videos) == 1:
                cprint("""
                Video %s probably do not exist.
                """ % args.videos[0], "red")
            else:
                cprint("""
                We could only retrieve %d out of the %d videos you provided.
                Either they don't exist, or you provided too many, because
                we do not support pagination here yet. Ask for it?
                """ % (
                    jsonResponse['pageInfo']['totalResults'], len(args.videos)
                ), "red")
            exit(1)
        videos.extend(parse_videos_from_json(jsonResponse))
    else:
        print(
            colored("Collecting videos of channel ", "yellow") +
            colored(args.channel, "magenta") +
            colored("...", "yellow")
        )

        jsonResponse = get_videos_of_channel(args.channel)
        videos.extend(parse_videos_from_json(jsonResponse))
        while 'nextPageToken' in jsonResponse:
            jsonResponse = get_videos_of_channel(
                args.channel, page=jsonResponse['nextPageToken']
            )
            videos.extend(parse_videos_from_json(jsonResponse))

    print("Found %s video%s." % (
        colored(str(len(videos)), "yellow"), _s(videos)
    ))

    cprint("Downloading captions from YouTube...", "yellow")

    captions_count = 0

    for video in videos:
        print("Retrieving captions for %s" % colored(video.title, "yellow"))
        jsonResponse = get_captions_for_video(video.yid)

        for caption_data in jsonResponse['items']:
            caption_kind = caption_data['snippet']['trackKind']
            if caption_kind != 'standard':
                print("  Ignored caption of kind %s." % caption_kind)
                continue
            if caption_data['snippet']['isDraft']:
                print("  Ignored caption draft.")
                continue

            caption_id = caption_data['id']
            caption_lang = caption_data['snippet']['language']
            caption_contents = youtube.captions().download(
                id=caption_id,
                tfmt=caption_extension
            ).execute().decode('utf-8')

            # YouTube writes comments on the first three lines of the VTT file:
            # WEBVTT
            # Kind: captions
            # Language: fr
            #
            # So we're going to append our metadata to these comments.
            if caption_extension == 'vtt':
                caption_lines = caption_contents.split("\n")
                caption_contents_header = caption_lines[0:3]
                caption_contents_rest = caption_lines[3:]
                caption_contents_header.append(
                    "LastUpdated: %s" % caption_data['snippet']['lastUpdated']
                )
                caption_contents_header.append("Caption: %s" % caption_id)
                caption_contents_header.append("Video: %s" % video.yid)
                caption_contents = "\n".join(caption_contents_header) + "\n" \
                                   + "\n".join(caption_contents_rest)

            caption_filename = "%s.%s.%s.%s.%s" % (
                video.date.strftime("%Y-%m-%d"), video.slug,
                caption_lang, caption_id, caption_extension
            )

            caption_year = video.date.strftime("%Y")
            caption_path = os.path.join(
                captions_directory, caption_year, caption_filename
            )

            if not os.path.exists(os.path.dirname(caption_path)):
                os.makedirs(os.path.dirname(caption_path))
            with open(caption_path, mode="w") as caption_file:
                caption_file.write(caption_contents.encode('utf-8'))

            captions_count += 1
            print("  Retrieved %s" % colored(caption_filename, "blue"))

    print("Downloaded a grand total of %s caption%s." % (
        colored(captions_count, "yellow"), _s(captions_count)
    ))

    cprint("Done!", "green")
    exit(0)
