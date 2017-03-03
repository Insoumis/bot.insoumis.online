#!/usr/bin/env bash

# A simple script to install the dependencies.

if cat /etc/*release | grep ^NAME | grep Ubuntu ; then
    sudo apt install git python python-pip virtualenv
elif cat /etc/*release | grep ^NAME | grep Debian ; then
    sudo aptitude install git python python-pip virtualenv
fi  # ... add your OS here

virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

# If "InsecurePlatformWarning: A true SSLContext object is not available."
# pip install requests[security]

echo -e "Done."