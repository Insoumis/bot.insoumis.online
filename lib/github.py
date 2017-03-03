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
