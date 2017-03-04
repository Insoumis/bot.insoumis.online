import os
import re
import sys
import logging

from subprocess import check_output

THIS_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIRECTORY, '..')))

from lib.youtube import Caption, get_videos, parse_videos_from_json

logging.basicConfig(format='%(message)s')
log = logging.getLogger('Common')


def get_downloaded_captions_and_videos(captions_directory):

    files_raw = check_output(
        ["git add -n ."], shell=True, cwd=captions_directory
    )
    git_added_paths = re.findall("^add '(.+)'$", files_raw, flags=re.MULTILINE)

    if 0 == len(git_added_paths):
        return [], []

    captions = []
    for git_caption_path in git_added_paths:
        # path may be arbitrarily prefixed but it'll always end by
        # year subdir and filename, so we extract that.
        m = re.search("([0-9]+)/([^/]+)$", git_caption_path)
        if not m:
            log.error("Bad path '%s'." % git_caption_path)
            sys.exit(1)
        caption_year, caption_filename = m.group(1, 2)
        caption_path = os.path.join(
            captions_directory, caption_year, caption_filename
        )
        captions.append(Caption.from_file(caption_path))

    videos = get_videos([caption.video_id for caption in captions])
    videos = parse_videos_from_json(videos)

    return captions, videos
